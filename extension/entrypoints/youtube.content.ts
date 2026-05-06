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

function duckOriginalVideo(active: boolean) {
  const v = getVideo();
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

function playDubBase64(audioBase64: string, mimeType: string) {
  const url = `data:${mimeType};base64,${audioBase64}`;
  const prev = window.dubAudioEl;
  if (prev) {
    prev.pause();
    prev.src = "";
  }
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
    v.addEventListener("play", () => void audio.play().catch(() => undefined));
    v.addEventListener("pause", () => audio.pause());
    v.addEventListener("seeking", () => {
      audio.currentTime = v.currentTime;
    });
    v.addEventListener("timeupdate", sync);
    audio.addEventListener("timeupdate", sync);
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
let lastPipelineAt = 0;
const PIPELINE_DEBOUNCE_MS = 45_000;

const attachedVideos = new WeakSet<HTMLVideoElement>();

async function maybeRunPipeline() {
  if (!(await isDubEnabledForThisTab()) || pipelineRunning) return;
  if (Date.now() - lastPipelineAt < PIPELINE_DEBOUNCE_MS) return;
  const v = getVideo();
  if (!v) return;

  pipelineRunning = true;
  lastPipelineAt = Date.now();
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
  }
}

export default defineContentScript({
  matches: ["*://www.youtube.com/*", "*://youtube.com/*", "*://m.youtube.com/*"],
  main() {
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
      const v = getVideo();
      if (v) {
        attachToVideo(v);
      }
    });
    obs.observe(document.documentElement, { childList: true, subtree: true });

    const existing = getVideo();
    if (existing) attachToVideo(existing);
  },
});
