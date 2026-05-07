import { transcribeThenSynthesize, refreshCreditMinutes } from "../lib/apiPipeline";

declare global {
  interface Window {
    dubAudioEl?: HTMLAudioElement;
  }
}

function getVideo(): HTMLVideoElement | null {
  return document.querySelector("video");
}

async function ensureTabAudioStream(): Promise<MediaStream> {
  const res = (await chrome.runtime.sendMessage({
    type: "GET_TAB_AUDIO_STREAM_ID",
  })) as { ok: boolean; streamId?: string; error?: string };

  if (!res.ok || !res.streamId) {
    throw new Error(res.error ?? "tabCapture denied");
  }

  const constraints = {
    audio: {
      mandatory: {
        chromeMediaSource: "tab",
        chromeMediaSourceId: res.streamId,
      },
    },
    video: false,
  };

  return navigator.mediaDevices.getUserMedia(constraints as MediaStreamConstraints);
}

async function recordTabAudio(ms: number): Promise<Blob> {
  const stream = await ensureTabAudioStream();
  const chunks: BlobPart[] = [];
  const mr = new MediaRecorder(stream, { mimeType: "audio/webm;codecs=opus" });
  return await new Promise((resolve, reject) => {
    mr.ondataavailable = (e) => {
      if (e.data.size) chunks.push(e.data);
    };
    mr.onerror = () => {
      stream.getTracks().forEach((t) => t.stop());
      reject(new Error("MediaRecorder failed"));
    };
    mr.onstop = () => {
      stream.getTracks().forEach((t) => t.stop());
      resolve(new Blob(chunks, { type: "audio/webm" }));
    };
    mr.start(3000);
    window.setTimeout(() => {
      try {
        mr.stop();
      } catch {
        reject(new Error("stop failed"));
      }
    }, ms);
  });
}

function duckOriginalVideoOnElement(active: boolean, v: HTMLVideoElement | null) {
  if (!v) return;
  if (active) {
    if (v.dataset.dubPrevVolume === undefined) {
      v.dataset.dubPrevVolume = String(v.volume);
    }
    v.volume = Math.min(v.volume, 0.2);
  } else if (v.dataset.dubPrevVolume !== undefined) {
    v.volume = Number(v.dataset.dubPrevVolume);
    delete v.dataset.dubPrevVolume;
  }
}

function duckOriginalVideo(active: boolean) {
  duckOriginalVideoOnElement(active, getVideo());
}

/** Gỡ listener đồng bộ dub ↔ video (Epic 5.4 — tránh orphan trên element cũ). */
let dubSyncCleanups: Array<() => void> = [];

function clearDubVideoSyncListeners(): void {
  for (const c of dubSyncCleanups) {
    try {
      c();
    } catch {
      /* ignore */
    }
  }
  dubSyncCleanups = [];
}

function stopDubAudioElement(): void {
  const prev = window.dubAudioEl;
  if (prev) {
    prev.pause();
    prev.removeAttribute("src");
    prev.load();
  }
  window.dubAudioEl = undefined;
}

function teardownDubForSpaNavigation(previousVideoEl: HTMLVideoElement | null): void {
  clearDubVideoSyncListeners();
  duckOriginalVideoOnElement(false, previousVideoEl);
  stopDubAudioElement();
}

function playDubBase64(audioBase64: string, mimeType: string) {
  clearDubVideoSyncListeners();
  stopDubAudioElement();

  const url = `data:${mimeType};base64,${audioBase64}`;
  const audio = new Audio(url);
  window.dubAudioEl = audio;
  const v = getVideo();
  if (v) {
    const sync = () => {
      if (!audio.paused && !v.paused) {
        const drift = Math.abs(audio.currentTime - v.currentTime);
        if (drift > 0.15) {
          audio.currentTime = v.currentTime;
        }
      }
    };
    const onPlay = () => void audio.play().catch(() => undefined);
    const onPause = () => audio.pause();
    const onSeeking = () => {
      audio.currentTime = v.currentTime;
    };
    v.addEventListener("play", onPlay);
    v.addEventListener("pause", onPause);
    v.addEventListener("seeking", onSeeking);
    v.addEventListener("timeupdate", sync);
    audio.addEventListener("timeupdate", sync);
    dubSyncCleanups.push(() => {
      v.removeEventListener("play", onPlay);
      v.removeEventListener("pause", onPause);
      v.removeEventListener("seeking", onSeeking);
      v.removeEventListener("timeupdate", sync);
      audio.removeEventListener("timeupdate", sync);
    });
  }
  void audio.play().catch(() => undefined);
}

async function isDubEnabledForThisTab(): Promise<boolean> {
  let tabId: number | undefined;
  try {
    const tabRes = (await chrome.runtime.sendMessage({ type: "GET_TAB_ID" })) as { tabId?: number };
    tabId = tabRes.tabId;
  } catch {
    // Service worker terminated — fall back to global dubMode
    const sync = await chrome.storage.sync.get("dubMode");
    return sync.dubMode === true;
  }
  if (tabId === undefined) return false;

  const local = await chrome.storage.local.get(["perTabDubOverrides"]);
  const overrides = (local.perTabDubOverrides ?? {}) as Record<string, boolean>;
  const key = String(tabId);
  if (Object.prototype.hasOwnProperty.call(overrides, key)) {
    return overrides[key]!;
  }

  const sync = await chrome.storage.sync.get("dubMode");
  return sync.dubMode === true;
}

let pipelineRunning = false;
/** Thời điểm pipeline **hoàn tất** (success/error) lần trước — dùng cho cooldown (Epic 8.1). */
let lastPipelineCompletedAt = 0;
/**
 * Cooldown sau khi pipeline xong trước khi chạy lại.
 * Baseline cũ: 45s kể từ **lần bắt đầu** → tần suất tối đa ~80 req/h/giả định luôn fire.
 * Chiến lược: debounce theo **completion** + 23s → gap sau chunk ngắn hơn; tần suất tối đa ~156 req/h
 * khi pipeline tức thì (vẫn < 2× baseline 80).
 */
const PIPELINE_DEBOUNCE_AFTER_COMPLETE_MS = 23_000;

/** `Set` thay `WeakSet` để có thể `delete` khi SPA đổi `<video>` (Epic 5.4). */
const attachedVideos = new Set<HTMLVideoElement>();

async function maybeRunPipeline() {
  if (!(await isDubEnabledForThisTab()) || pipelineRunning) return;
  if (Date.now() - lastPipelineCompletedAt < PIPELINE_DEBOUNCE_AFTER_COMPLETE_MS) return;
  const v = getVideo();
  if (!v) return;

  const gate = await chrome.storage.local.get(["accessToken", "creditMinutes", "userHasPaidPlan"]);
  if (typeof gate.accessToken !== "string" || !gate.accessToken) {
    await chrome.storage.local.set({
      dubStatus: "Error",
      dubErrorMessage: "Cần đăng nhập để dub (API yêu cầu JWT).",
    });
    return;
  }
  // P12: creditMinutes undefined means storage not synced yet — block gracefully
  if (gate.userHasPaidPlan !== true && typeof gate.creditMinutes !== "number") {
    await chrome.storage.local.set({
      dubStatus: "Error",
      dubErrorMessage: "Chưa đồng bộ credit — mở popup để cập nhật.",
    });
    return;
  }
  if (
    gate.userHasPaidPlan !== true &&
    typeof gate.creditMinutes === "number" &&
    gate.creditMinutes <= 0
  ) {
    await chrome.storage.local.set({
      dubStatus: "Error",
      dubErrorMessage: "Hết phút credit — nâng cấp hoặc chờ reset đầu tháng.",
    });
    return;
  }

  pipelineRunning = true;
  await chrome.storage.local.set({ dubStatus: "Dubbing..." });
  duckOriginalVideo(true);

  try {
    const blob = await recordTabAudio(12000);
    const { audioBase64 } = await transcribeThenSynthesize(blob);
    playDubBase64(audioBase64, "audio/mpeg");
    await chrome.storage.local.set({ dubStatus: "Ready", dubErrorMessage: "" });
    void refreshCreditMinutes();
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    await chrome.storage.local.set({ dubStatus: "Error", dubErrorMessage: msg });
  } finally {
    pipelineRunning = false;
    lastPipelineCompletedAt = Date.now();
  }
}

export default defineContentScript({
  matches: ["*://www.youtube.com/*", "*://youtube.com/*", "*://m.youtube.com/*"],
  main() {
    let previousVideo: HTMLVideoElement | null = null;

    const onPossibleVideoSwap = () => {
      const v = getVideo();
      if (v === previousVideo) return;
      if (previousVideo !== null) {
        attachedVideos.delete(previousVideo);
        teardownDubForSpaNavigation(previousVideo);
      }
      previousVideo = v;
      if (v) attachToVideo(v);
    };

    try {
      document.addEventListener(
        "yt-navigate-finish",
        () => {
          onPossibleVideoSwap();
        },
        true,
      );
    } catch {
      /* feature-detect: một số build không có custom event */
    }

    chrome.storage.onChanged.addListener((changes, area) => {
      if (area === "sync" && changes.dubMode?.newValue === false) {
        void isDubEnabledForThisTab().then((on) => {
          if (!on) {
            duckOriginalVideo(false);
            window.dubAudioEl?.pause();
          }
        });
      }
      if (area === "local" && changes.perTabDubOverrides) {
        void isDubEnabledForThisTab().then((on) => {
          if (!on) {
            duckOriginalVideo(false);
            window.dubAudioEl?.pause();
          }
        });
      }
    });

    chrome.runtime.onMessage.addListener((msg) => {
      if (msg?.type === "PLAY_DUB_AUDIO" && msg.audioBase64) {
        playDubBase64(msg.audioBase64, msg.mimeType ?? "audio/mpeg");
      }
    });

    const attachToVideo = (v: HTMLVideoElement) => {
      if (attachedVideos.has(v)) return;
      attachedVideos.add(v);
      v.addEventListener(
        "playing",
        () => {
          void maybeRunPipeline();
        },
        { passive: true },
      );
      v.addEventListener(
        "pause",
        () => {
          window.dubAudioEl?.pause();
        },
        { passive: true },
      );
    };

    const obs = new MutationObserver(() => {
      onPossibleVideoSwap();
    });
    obs.observe(document.documentElement, { childList: true, subtree: true });

    onPossibleVideoSwap();
  },
});
