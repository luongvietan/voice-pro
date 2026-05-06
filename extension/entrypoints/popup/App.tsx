import { useCallback, useEffect, useState } from "react";

import { LANG_OPTIONS } from "../../constants";
import { signInWithGoogle, signOut } from "../../lib/auth";
import { pullUserSettingsToSync, schedulePushUserSettings } from "../../lib/settingsSync";

type TabDubMode = "default" | "on" | "off";

async function confirmFreeTierDubEnable(): Promise<boolean> {
  const s = await chrome.storage.local.get(["accessToken", "creditMinutes", "userHasPaidPlan"]);
  if (typeof s.accessToken !== "string" || !s.accessToken) {
    window.alert("Đăng nhập để dùng dubbing và trừ phút credit.");
    return false;
  }
  if (s.userHasPaidPlan === true) return true;
  const m = s.creditMinutes;
  // P12: creditMinutes undefined means storage not yet synced — block and ask user to reopen
  if (typeof m !== "number") {
    window.alert("Chưa đồng bộ thông tin credit. Đóng và mở lại popup để thử lại.");
    return false;
  }
  // P7: AC 4.2 requires notification when blocking at 0 minutes
  if (m <= 0) {
    window.alert("Hết phút credit. Nâng cấp hoặc chờ reset miễn phí đầu tháng.");
    return false;
  }
  if (m <= 2) {
    return window.confirm(
      `Còn ${m} phút — Upgrade để tiếp tục thoải mái. Bật Dub anyway?`,
    );
  }
  return true;
}

export default function App() {
  const [dubMode, setDubMode] = useState(false);
  const [lang, setLang] = useState("vi");
  const [status, setStatus] = useState("Ready");
  const [errorDetail, setErrorDetail] = useState("");

  const [signedIn, setSignedIn] = useState(false);
  const [userName, setUserName] = useState("");
  const [userEmail, setUserEmail] = useState("");
  const [avatarUrl, setAvatarUrl] = useState("");
  const [creditMinutes, setCreditMinutes] = useState<number | null>(null);
  const [authBusy, setAuthBusy] = useState(false);
  const [authError, setAuthError] = useState("");

  const [tabId, setTabId] = useState<number | null>(null);
  const [tabMode, setTabMode] = useState<TabDubMode>("default");

  const loadTabOverride = useCallback(async (id: number | null) => {
    if (id === null) return;
    const local = await chrome.storage.local.get(["perTabDubOverrides"]);
    const o = (local.perTabDubOverrides ?? {}) as Record<string, boolean>;
    const key = String(id);
    if (!Object.prototype.hasOwnProperty.call(o, key)) setTabMode("default");
    else setTabMode(o[key] ? "on" : "off");
  }, []);

  useEffect(() => {
    chrome.storage.local.get(
      ["accessToken", "userDisplayName", "userEmail", "userAvatarUrl", "creditMinutes"],
      (s) => {
        if (typeof s.accessToken === "string" && s.accessToken) {
          setSignedIn(true);
          if (typeof s.userDisplayName === "string") setUserName(s.userDisplayName);
          if (typeof s.userEmail === "string") setUserEmail(s.userEmail);
          if (typeof s.userAvatarUrl === "string") setAvatarUrl(s.userAvatarUrl);
          if (typeof s.creditMinutes === "number") setCreditMinutes(s.creditMinutes);
        }
      },
    );
  }, []);

  useEffect(() => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const id = tabs[0]?.id;
      setTabId(id ?? null);
      void loadTabOverride(id ?? null);
    });
  }, [loadTabOverride]);

  useEffect(() => {
    chrome.storage.sync.get(["dubMode", "dubTargetLang"], (s) => {
      if (typeof s.dubMode === "boolean") setDubMode(s.dubMode);
      if (typeof s.dubTargetLang === "string") setLang(s.dubTargetLang);
    });
    chrome.storage.local.get(
      ["accessToken", "userDisplayName", "userEmail", "userAvatarUrl", "creditMinutes", "dubStatus", "dubErrorMessage"],
      (s) => {
        setSignedIn(typeof s.accessToken === "string" && s.accessToken.length > 0);
        if (typeof s.userDisplayName === "string") setUserName(s.userDisplayName);
        if (typeof s.userEmail === "string") setUserEmail(s.userEmail);
        if (typeof s.userAvatarUrl === "string") setAvatarUrl(s.userAvatarUrl);
        if (typeof s.creditMinutes === "number") setCreditMinutes(s.creditMinutes);
        if (typeof s.dubStatus === "string") setStatus(s.dubStatus);
        if (typeof s.dubErrorMessage === "string") setErrorDetail(s.dubErrorMessage);
      },
    );

    const handler = (
      changes: Record<string, chrome.storage.StorageChange>,
      area: string,
    ) => {
      if (area === "local") {
        if (changes.dubStatus?.newValue !== undefined) {
          setStatus(String(changes.dubStatus.newValue));
        }
        if (changes.dubErrorMessage?.newValue !== undefined) {
          setErrorDetail(String(changes.dubErrorMessage.newValue ?? ""));
        }
        if (changes.accessToken !== undefined || changes.creditMinutes !== undefined) {
          chrome.storage.local.get(["accessToken", "creditMinutes"], (s) => {
            setSignedIn(typeof s.accessToken === "string" && s.accessToken.length > 0);
            if (typeof s.creditMinutes === "number") setCreditMinutes(s.creditMinutes);
          });
        }
      }
      if (area === "local" && changes.perTabDubOverrides) {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
          const id = tabs[0]?.id ?? null;
          void loadTabOverride(id);
        });
      }
    };
    chrome.storage.onChanged.addListener(handler);
    return () => chrome.storage.onChanged.removeListener(handler);
  }, [loadTabOverride]);

  async function persistTabMode(mode: TabDubMode) {
    if (tabId === null) return;
    if (mode === "on") {
      const ok = await confirmFreeTierDubEnable();
      if (!ok) return;
    }
    const local = await chrome.storage.local.get(["perTabDubOverrides"]);
    const o = { ...((local.perTabDubOverrides ?? {}) as Record<string, boolean>) };
    const key = String(tabId);
    if (mode === "default") delete o[key];
    else o[key] = mode === "on";
    await chrome.storage.local.set({ perTabDubOverrides: o });
    setTabMode(mode);
  }

  return (
    <div style={{ padding: 12, fontFamily: "system-ui", minWidth: 280 }}>
      <h1 style={{ fontSize: 14, margin: "0 0 8px" }}>Voice-Pro Dub</h1>

      {!signedIn ? (
        <div style={{ marginBottom: 12 }}>
          <button
            type="button"
            disabled={authBusy}
            style={{ cursor: authBusy ? "wait" : "pointer", padding: "6px 10px", fontSize: 12 }}
            onClick={() => {
              setAuthError("");
              setAuthBusy(true);
              void signInWithGoogle()
                .then(async () => {
                  const { accessToken } = await chrome.storage.local.get("accessToken");
                  if (typeof accessToken === "string") {
                    await pullUserSettingsToSync(accessToken);
                  }
                  setSignedIn(true);
                  chrome.storage.local.get(["userDisplayName", "userEmail", "userAvatarUrl", "creditMinutes"], (s) => {
                    if (typeof s.userDisplayName === "string") setUserName(s.userDisplayName);
                    if (typeof s.userEmail === "string") setUserEmail(s.userEmail);
                    if (typeof s.userAvatarUrl === "string") setAvatarUrl(s.userAvatarUrl);
                    if (typeof s.creditMinutes === "number") setCreditMinutes(s.creditMinutes);
                  });
                })
                .catch((e) => setAuthError(e instanceof Error ? e.message : String(e)))
                .finally(() => setAuthBusy(false));
            }}
          >
            Sign in with Google
          </button>
          {authError ? (
            <div style={{ fontSize: 11, color: "#b00020", marginTop: 6 }}>{authError}</div>
          ) : null}
          <div style={{ fontSize: 10, color: "#888", marginTop: 6 }}>
            Cần Google OAuth Client ID (Chrome extension) trong biến môi trường build.
          </div>
        </div>
      ) : (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            marginBottom: 12,
            paddingBottom: 8,
            borderBottom: "1px solid #eee",
          }}
        >
          {avatarUrl ? (
            <img src={avatarUrl} alt="" width={32} height={32} style={{ borderRadius: "50%" }} />
          ) : (
            <div style={{ width: 32, height: 32, borderRadius: "50%", background: "#ddd" }} />
          )}
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 12, fontWeight: 600, overflow: "hidden", textOverflow: "ellipsis" }}>
              {userName || userEmail || "Đã đăng nhập"}
            </div>
            <div style={{ fontSize: 11, color: "#555" }}>
              {creditMinutes !== null ? `${creditMinutes} phút còn lại` : "—"}
            </div>
          </div>
          <button
            type="button"
            style={{ fontSize: 11, cursor: "pointer" }}
            onClick={() => {
              void signOut().then(() => setSignedIn(false));
            }}
          >
            Đăng xuất
          </button>
        </div>
      )}

      <label style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
        <input
          type="checkbox"
          checked={dubMode}
          onChange={(e) => {
            const v = e.target.checked;
            if (v) {
              void confirmFreeTierDubEnable().then((ok) => {
                if (!ok) return;
                setDubMode(true);
                void chrome.storage.sync.set({ dubMode: true });
                schedulePushUserSettings();
              });
              return;
            }
            setDubMode(false);
            void chrome.storage.sync.set({ dubMode: false });
            schedulePushUserSettings();
          }}
        />
        Dub Mode (global)
      </label>

      <label style={{ display: "block", fontSize: 12, marginBottom: 8 }}>
        Ngôn ngữ đích
        <select
          value={lang}
          onChange={(e) => {
            const v = e.target.value;
            setLang(v);
            void chrome.storage.sync.set({ dubTargetLang: v });
            schedulePushUserSettings();
          }}
          style={{ marginLeft: 8 }}
        >
          {LANG_OPTIONS.map((o) => (
            <option key={o.code} value={o.code}>
              {o.label}
            </option>
          ))}
        </select>
      </label>

      {tabId !== null ? (
        <label style={{ display: "block", fontSize: 12, marginBottom: 8 }}>
          Dub cho tab hiện tại
          <select
            value={tabMode}
            onChange={(e) => void persistTabMode(e.target.value as TabDubMode)}
            style={{ marginLeft: 8 }}
          >
            <option value="default">Theo global</option>
            <option value="on">Luôn bật</option>
            <option value="off">Luôn tắt</option>
          </select>
        </label>
      ) : null}

      <div style={{ fontSize: 11, color: "#666" }}>Status: {status}</div>
      {status === "Error" ? (
        <div style={{ marginTop: 6 }}>
          {errorDetail ? (
            <div style={{ fontSize: 11, color: "#b00020", marginBottom: 6 }}>{errorDetail}</div>
          ) : null}
          <button
            style={{ fontSize: 11, cursor: "pointer", padding: "2px 8px" }}
            onClick={() => {
              void confirmFreeTierDubEnable().then((ok) => {
                if (!ok) return;
                void chrome.storage.local.set({ dubStatus: "Ready", dubErrorMessage: "" });
                void chrome.storage.sync.set({ dubMode: true });
                setDubMode(true);
                setStatus("Ready");
                setErrorDetail("");
              });
            }}
          >
            Thử lại
          </button>
        </div>
      ) : null}
    </div>
  );
}
