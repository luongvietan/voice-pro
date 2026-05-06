import { VP_SETTINGS_PULL_RETRY_ALARM } from "../constants";
import { pullUserSettingsToSync } from "../lib/settingsSync";

const SETTINGS_PULL_ALARM = VP_SETTINGS_PULL_RETRY_ALARM;
const SETTINGS_PULL_MIN_GAP_MS = 2000;
const SETTINGS_PULL_RETRY_SPACING_MS = 10_000;
const SETTINGS_PULL_MAX_ATTEMPTS = 5;

let lastSettingsPullAt = 0;

async function clearPerTabOverrideForClosedTab(tabId: number): Promise<void> {
  const { perTabDubOverrides } = await chrome.storage.local.get("perTabDubOverrides");
  if (perTabDubOverrides === undefined || perTabDubOverrides === null) return;
  if (typeof perTabDubOverrides !== "object" || Array.isArray(perTabDubOverrides)) return;
  const o = perTabDubOverrides as Record<string, boolean>;
  const key = String(tabId);
  if (!Object.prototype.hasOwnProperty.call(o, key)) return;
  const next = { ...o };
  delete next[key];
  await chrome.storage.local.set({ perTabDubOverrides: next });
}

async function clearSettingsPullRetryState(): Promise<void> {
  await chrome.alarms.clear(SETTINGS_PULL_ALARM);
  await chrome.storage.local.remove([
    "vpSettingsPullRetryActive",
    "vpSettingsPullRetryAttempts",
  ]);
}

async function runSettingsPullIfDue(): Promise<void> {
  const { accessToken, vpSettingsPullRetryActive, vpSettingsPullRetryAttempts } =
    await chrome.storage.local.get([
      "accessToken",
      "vpSettingsPullRetryActive",
      "vpSettingsPullRetryAttempts",
    ]);
  if (typeof accessToken !== "string" || !accessToken) {
    await clearSettingsPullRetryState();
    return;
  }
  if (vpSettingsPullRetryActive !== true) {
    await chrome.alarms.clear(SETTINGS_PULL_ALARM);
    return;
  }

  const now = Date.now();
  if (lastSettingsPullAt > 0 && now - lastSettingsPullAt < SETTINGS_PULL_MIN_GAP_MS) {
    await chrome.alarms.create(SETTINGS_PULL_ALARM, {
      when: lastSettingsPullAt + SETTINGS_PULL_MIN_GAP_MS,
    });
    return;
  }
  lastSettingsPullAt = now;

  const ok = await pullUserSettingsToSync(accessToken).catch(() => false);
  if (ok) {
    await clearSettingsPullRetryState();
    return;
  }

  const prev =
    typeof vpSettingsPullRetryAttempts === "number" &&
    Number.isFinite(vpSettingsPullRetryAttempts) &&
    vpSettingsPullRetryAttempts >= 0
      ? Math.floor(vpSettingsPullRetryAttempts)
      : 0;
  const nextAttempts = prev + 1;
  if (nextAttempts >= SETTINGS_PULL_MAX_ATTEMPTS) {
    await clearSettingsPullRetryState();
    return;
  }
  await chrome.storage.local.set({
    vpSettingsPullRetryAttempts: nextAttempts,
    vpSettingsPullRetryActive: true,
  });
  await chrome.alarms.create(SETTINGS_PULL_ALARM, {
    when: now + SETTINGS_PULL_RETRY_SPACING_MS,
  });
}

export default defineBackground(() => {
  chrome.tabs.onRemoved.addListener((tabId) => {
    void clearPerTabOverrideForClosedTab(tabId);
  });

  chrome.alarms.onAlarm.addListener((alarm) => {
    if (alarm.name === SETTINGS_PULL_ALARM) {
      void runSettingsPullIfDue();
    }
  });

  chrome.storage.onChanged.addListener((changes, area) => {
    if (area !== "local") return;
    if (changes.accessToken && changes.accessToken.newValue == null) {
      void clearSettingsPullRetryState();
    }
  });

  chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg?.type === "GET_TAB_ID") {
      const tabId = sender.tab?.id;
      sendResponse({ tabId });
      return true;
    }
    if (msg?.type === "GET_TAB_AUDIO_STREAM_ID") {
      const tabId = sender.tab?.id;
      if (tabId === undefined) {
        sendResponse({ ok: false, error: "No sender tab" });
        return;
      }
      chrome.tabCapture.getMediaStreamId({ targetTabId: tabId }, (streamId) => {
        if (!streamId || chrome.runtime.lastError) {
          sendResponse({
            ok: false,
            error: chrome.runtime.lastError?.message ?? "Cannot get capture stream id",
          });
          return;
        }
        sendResponse({ ok: true, streamId });
      });
      return true;
    }
    /** Epic 5.2: bắt đầu chuỗi pull `/me` khi popup đăng nhập nhưng pull lỗi (dùng `chrome.alarms`, xem constants phía trên). */
    if (msg?.type === "VP_START_SETTINGS_PULL_RETRY") {
      void chrome.storage.local
        .set({ vpSettingsPullRetryActive: true, vpSettingsPullRetryAttempts: 0 })
        .then(() =>
          chrome.alarms.create(SETTINGS_PULL_ALARM, {
            when: Date.now() + SETTINGS_PULL_RETRY_SPACING_MS,
          }),
        );
      sendResponse({ ok: true });
      return true;
    }
    /** Gọi khi popup nhận `online` — thử pull ngay nếu đang pending và đủ khoảng cách tối thiểu. */
    if (msg?.type === "VP_WAKE_SETTINGS_PULL_RETRY") {
      void chrome.storage.local.get("vpSettingsPullRetryActive").then((r) => {
        if (r.vpSettingsPullRetryActive === true) void runSettingsPullIfDue();
      });
      sendResponse({ ok: true });
      return true;
    }
    return undefined;
  });
});
