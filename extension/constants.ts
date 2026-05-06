/** Dev API — đặt qua chrome.storage.local key apiBaseUrl nếu cần. */
export const DEFAULT_API_BASE = "http://localhost:8000";

/** Alarm SW — retry `pullUserSettingsToSync` sau login offline (Epic 5.2). */
export const VP_SETTINGS_PULL_RETRY_ALARM = "vp-settings-pull-retry";

export type PopupStatus = "Ready" | "Dubbing..." | "Capturing..." | "Error";

export const LANG_OPTIONS: { code: string; label: string }[] = [
  { code: "vi", label: "Tiếng Việt" },
  { code: "en", label: "English" },
  { code: "es", label: "Español" },
  { code: "fr", label: "Français" },
  { code: "de", label: "Deutsch" },
  { code: "ja", label: "日本語" },
  { code: "ko", label: "한국어" },
  { code: "zh-CN", label: "中文" },
  { code: "pt", label: "Português" },
  { code: "it", label: "Italiano" },
];
