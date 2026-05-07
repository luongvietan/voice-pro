import { useCallback, useEffect, useRef, useState } from "react";

import { LANG_OPTIONS } from "../../constants";
import { signInWithGoogle, signOut } from "../../lib/auth";
import { pullUserSettingsToSync, schedulePushUserSettings } from "../../lib/settingsSync";

type TabDubMode = "default" | "on" | "off";

type GatePrompt =
  | null
  | { kind: "login"; message: string }
  | { kind: "sync"; message: string }
  | { kind: "exhausted"; message: string }
  | { kind: "lowCredit"; minutes: number };

/* ── Design tokens ── */
const T = {
  black: "#0e0f0c",
  green: "#9fe870",
  darkGreen: "#163300",
  mint: "#e2f6d5",
  warmDark: "#454745",
  gray: "#868685",
  danger: "#d03238",
  dangerBg: "rgba(208,50,56,0.09)",
  ring: "rgba(14,15,12,0.12) 0px 0px 0px 1px",
  font: "'Inter',Helvetica,Arial,sans-serif",
};

/* ── Shared micro-styles ── */
const base: React.CSSProperties = {
  fontFamily: T.font,
  fontFeatureSettings: '"calt"',
  WebkitFontSmoothing: "antialiased",
} as React.CSSProperties;

function BtnGreen({
  children,
  disabled,
  onClick,
  style,
}: {
  children: React.ReactNode;
  disabled?: boolean;
  onClick?: () => void;
  style?: React.CSSProperties;
}) {
  const [hover, setHover] = useState(false);
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        ...base,
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        gap: 6,
        background: disabled ? "rgba(159,232,112,0.4)" : T.green,
        color: T.darkGreen,
        border: "none",
        borderRadius: 9999,
        padding: "8px 16px",
        fontSize: 13,
        fontWeight: 600,
        cursor: disabled ? "not-allowed" : "pointer",
        transform: hover && !disabled ? "scale(1.05)" : "scale(1)",
        transition: "transform 0.15s ease",
        ...style,
      }}
    >
      {children}
    </button>
  );
}

function BtnGhost({
  children,
  disabled,
  onClick,
  style,
}: {
  children: React.ReactNode;
  disabled?: boolean;
  onClick?: () => void;
  style?: React.CSSProperties;
}) {
  const [hover, setHover] = useState(false);
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        ...base,
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        background: "rgba(22,51,0,0.07)",
        color: T.black,
        border: "none",
        borderRadius: 9999,
        padding: "7px 14px",
        fontSize: 12,
        fontWeight: 600,
        cursor: disabled ? "not-allowed" : "pointer",
        transform: hover && !disabled ? "scale(1.05)" : "scale(1)",
        transition: "transform 0.15s ease",
        ...style,
      }}
    >
      {children}
    </button>
  );
}

/* ── Status dot ── */
function StatusDot({ status }: { status: string }) {
  const isError = status === "Error";
  const isProcessing =
    status !== "Ready" && status !== "Error" && status !== "Idle";
  const color = isError ? T.danger : isProcessing ? "#ffd11a" : T.green;
  return (
    <span
      style={{
        display: "inline-block",
        width: 7,
        height: 7,
        borderRadius: "50%",
        background: color,
        boxShadow: `0 0 0 2px ${color}33`,
        flexShrink: 0,
      }}
    />
  );
}

/* ── Toggle switch ── */
function Toggle({
  checked,
  onChange,
  label,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  label: string;
}) {
  return (
    <label
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        cursor: "pointer",
        userSelect: "none",
      }}
    >
      <span style={{ fontSize: 13, fontWeight: 600, color: T.black }}>{label}</span>
      <span
        onClick={() => onChange(!checked)}
        style={{
          display: "inline-flex",
          width: 38,
          height: 22,
          borderRadius: 9999,
          background: checked ? T.green : "rgba(14,15,12,0.15)",
          position: "relative",
          transition: "background 0.2s ease",
          flexShrink: 0,
          cursor: "pointer",
        }}
      >
        <span
          style={{
            position: "absolute",
            top: 3,
            left: checked ? 19 : 3,
            width: 16,
            height: 16,
            borderRadius: "50%",
            background: checked ? T.darkGreen : "#ffffff",
            boxShadow: "0 1px 3px rgba(0,0,0,0.2)",
            transition: "left 0.2s ease, background 0.2s ease",
          }}
        />
      </span>
    </label>
  );
}

/* ── Main component ── */
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

  const [gatePrompt, setGatePrompt] = useState<GatePrompt>(null);
  const gateResolverRef = useRef<((value: boolean) => void) | null>(null);

  const resolveGate = useCallback((value: boolean) => {
    const r = gateResolverRef.current;
    gateResolverRef.current = null;
    setGatePrompt(null);
    r?.(value);
  }, []);

  useEffect(() => {
    return () => {
      const r = gateResolverRef.current;
      if (r !== null) {
        gateResolverRef.current = null;
        r(false);
      }
    };
  }, []);

  const confirmFreeTierDubEnable = useCallback(async (): Promise<boolean> => {
    if (gateResolverRef.current !== null) return false;
    const s = await chrome.storage.local.get(["accessToken", "creditMinutes", "userHasPaidPlan"]);
    if (typeof s.accessToken !== "string" || !s.accessToken) {
      return await new Promise((resolve) => {
        gateResolverRef.current = resolve;
        setGatePrompt({ kind: "login", message: "Đăng nhập để dùng dubbing và trừ phút credit." });
      });
    }
    if (s.userHasPaidPlan === true) return true;
    const m = s.creditMinutes;
    if (typeof m !== "number") {
      return await new Promise((resolve) => {
        gateResolverRef.current = resolve;
        setGatePrompt({ kind: "sync", message: "Chưa đồng bộ thông tin credit. Đóng và mở lại popup để thử lại." });
      });
    }
    if (m <= 0) {
      return await new Promise((resolve) => {
        gateResolverRef.current = resolve;
        setGatePrompt({ kind: "exhausted", message: "Hết phút credit. Nâng cấp hoặc chờ reset miễn phí đầu tháng." });
      });
    }
    if (m <= 2) {
      return await new Promise((resolve) => {
        gateResolverRef.current = resolve;
        setGatePrompt({ kind: "lowCredit", minutes: m });
      });
    }
    return true;
  }, []);

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
    const onOnline = () => {
      void chrome.runtime
        .sendMessage({ type: "VP_WAKE_SETTINGS_PULL_RETRY" })
        .catch(() => undefined);
    };
    window.addEventListener("online", onOnline);
    return () => window.removeEventListener("online", onOnline);
  }, []);

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
        if (changes.dubStatus?.newValue !== undefined) setStatus(String(changes.dubStatus.newValue));
        if (changes.dubErrorMessage?.newValue !== undefined) setErrorDetail(String(changes.dubErrorMessage.newValue ?? ""));
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

  /* ── Credit bar width ── */
  const creditPct =
    creditMinutes !== null ? Math.min(100, Math.max(0, (creditMinutes / 30) * 100)) : null;
  const creditColor =
    creditPct !== null
      ? creditPct > 50
        ? T.green
        : creditPct > 15
          ? "#ffd11a"
          : T.danger
      : T.green;

  return (
    <div
      style={{
        ...base,
        width: 300,
        minWidth: 300,
        background: "#ffffff",
        color: T.black,
        padding: 0,
        overflow: "hidden",
      }}
    >
      {/* Header bar */}
      <div
        style={{
          background: T.black,
          padding: "14px 16px 12px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <span
          style={{
            fontSize: 15,
            fontWeight: 900,
            color: "#ffffff",
            letterSpacing: "-0.3px",
          }}
        >
          Voice<span style={{ color: T.green }}>Pro</span>
        </span>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <StatusDot status={status} />
          <span style={{ fontSize: 11, color: "rgba(255,255,255,0.6)", fontWeight: 600 }}>
            {status}
          </span>
        </div>
      </div>

      <div style={{ padding: "14px 16px" }}>

        {/* Gate prompt modal */}
        {gatePrompt ? (
          <div
            role="dialog"
            aria-modal="true"
            style={{
              background: "#f8faf7",
              borderRadius: 16,
              padding: "14px",
              marginBottom: 12,
              boxShadow: T.ring,
            }}
          >
            {gatePrompt.kind === "lowCredit" ? (
              <>
                <p
                  style={{
                    margin: "0 0 10px",
                    fontSize: 13,
                    fontWeight: 600,
                    lineHeight: 1.45,
                    color: T.black,
                  }}
                >
                  Còn {gatePrompt.minutes} phút — Bật Dub tiếp?
                </p>
                <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
                  <BtnGhost onClick={() => resolveGate(false)}>Hủy</BtnGhost>
                  <BtnGreen onClick={() => resolveGate(true)}>Tiếp tục</BtnGreen>
                </div>
              </>
            ) : (
              <>
                <p
                  style={{
                    margin: "0 0 10px",
                    fontSize: 13,
                    fontWeight: 600,
                    lineHeight: 1.45,
                    color:
                      gatePrompt.kind === "exhausted"
                        ? T.danger
                        : T.black,
                  }}
                >
                  {gatePrompt.message}
                </p>
                <div style={{ display: "flex", justifyContent: "flex-end" }}>
                  <BtnGhost onClick={() => resolveGate(false)}>Đóng</BtnGhost>
                </div>
              </>
            )}
          </div>
        ) : null}

        {/* Auth section */}
        {!signedIn ? (
          <div
            style={{
              background: "#f8faf7",
              borderRadius: 16,
              padding: "14px",
              marginBottom: 12,
              boxShadow: T.ring,
            }}
          >
            <p
              style={{
                margin: "0 0 10px",
                fontSize: 13,
                fontWeight: 600,
                color: T.black,
              }}
            >
              Đăng nhập để bắt đầu dubbing
            </p>
            <BtnGreen
              disabled={authBusy}
              style={{ width: "100%" }}
              onClick={() => {
                setAuthError("");
                setAuthBusy(true);
                void signInWithGoogle()
                  .then(async () => {
                    const { accessToken } = await chrome.storage.local.get("accessToken");
                    if (typeof accessToken === "string") {
                      const pulled = await pullUserSettingsToSync(accessToken);
                      if (!pulled) {
                        await chrome.storage.local.set({
                          vpSettingsPullRetryActive: true,
                          vpSettingsPullRetryAttempts: 0,
                        });
                        void chrome.runtime
                          .sendMessage({ type: "VP_START_SETTINGS_PULL_RETRY" })
                          .catch(() => undefined);
                      }
                    }
                    setSignedIn(true);
                    chrome.storage.local.get(
                      ["userDisplayName", "userEmail", "userAvatarUrl", "creditMinutes"],
                      (s) => {
                        if (typeof s.userDisplayName === "string") setUserName(s.userDisplayName);
                        if (typeof s.userEmail === "string") setUserEmail(s.userEmail);
                        if (typeof s.userAvatarUrl === "string") setAvatarUrl(s.userAvatarUrl);
                        if (typeof s.creditMinutes === "number") setCreditMinutes(s.creditMinutes);
                      },
                    );
                  })
                  .catch((e) => setAuthError(e instanceof Error ? e.message : String(e)))
                  .finally(() => setAuthBusy(false));
              }}
            >
              {authBusy ? "Đang đăng nhập..." : "🔑 Sign in with Google"}
            </BtnGreen>
            {authError ? (
              <div
                style={{
                  marginTop: 8,
                  fontSize: 12,
                  color: T.danger,
                  fontWeight: 600,
                  background: T.dangerBg,
                  borderRadius: 8,
                  padding: "6px 10px",
                }}
              >
                {authError}
              </div>
            ) : null}
          </div>
        ) : (
          /* User info card */
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              marginBottom: 12,
              padding: "10px 12px",
              borderRadius: 16,
              background: "#f8faf7",
              boxShadow: T.ring,
            }}
          >
            {avatarUrl ? (
              <img
                src={avatarUrl}
                alt=""
                width={34}
                height={34}
                style={{ borderRadius: "50%", flexShrink: 0 }}
              />
            ) : (
              <div
                style={{
                  width: 34,
                  height: 34,
                  borderRadius: "50%",
                  background: T.mint,
                  flexShrink: 0,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 16,
                }}
              >
                🎙
              </div>
            )}
            <div style={{ flex: 1, minWidth: 0 }}>
              <div
                style={{
                  fontSize: 13,
                  fontWeight: 700,
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                  color: T.black,
                }}
              >
                {userName || userEmail || "Đã đăng nhập"}
              </div>
              {/* Credit bar */}
              {creditMinutes !== null ? (
                <div style={{ marginTop: 4 }}>
                  <div
                    style={{
                      height: 4,
                      borderRadius: 9999,
                      background: "rgba(14,15,12,0.1)",
                      overflow: "hidden",
                    }}
                  >
                    <div
                      style={{
                        height: "100%",
                        width: `${creditPct ?? 0}%`,
                        background: creditColor,
                        borderRadius: 9999,
                        transition: "width 0.4s ease",
                      }}
                    />
                  </div>
                  <div
                    style={{
                      marginTop: 3,
                      fontSize: 11,
                      color: T.gray,
                      fontWeight: 600,
                    }}
                  >
                    {creditMinutes} phút còn lại
                  </div>
                </div>
              ) : null}
            </div>
            <BtnGhost
              style={{ fontSize: 11, padding: "5px 10px", flexShrink: 0 }}
              onClick={() => void signOut().then(() => setSignedIn(false))}
            >
              Ra
            </BtnGhost>
          </div>
        )}

        {/* Controls */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 10,
            background: "#f8faf7",
            borderRadius: 16,
            padding: "12px 14px",
            marginBottom: 12,
            boxShadow: T.ring,
          }}
        >
          {/* Dub mode toggle */}
          <Toggle
            checked={dubMode}
            label="Dub Mode (toàn cục)"
            onChange={(v) => {
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

          {/* Language select */}
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <label
              htmlFor="lang-select"
              style={{ fontSize: 13, fontWeight: 600, color: T.black }}
            >
              Ngôn ngữ đích
            </label>
            <select
              id="lang-select"
              value={lang}
              onChange={(e) => {
                const v = e.target.value;
                setLang(v);
                void chrome.storage.sync.set({ dubTargetLang: v });
                schedulePushUserSettings();
              }}
              style={{
                ...base,
                fontSize: 12,
                fontWeight: 600,
                color: T.black,
                background: "#ffffff",
                border: "1px solid rgba(14,15,12,0.15)",
                borderRadius: 8,
                padding: "5px 8px",
                cursor: "pointer",
                outline: "none",
                maxWidth: 130,
              }}
            >
              {LANG_OPTIONS.map((o) => (
                <option key={o.code} value={o.code}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>

          {/* Per-tab override */}
          {tabId !== null ? (
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <label
                htmlFor="tab-mode"
                style={{ fontSize: 13, fontWeight: 600, color: T.black }}
              >
                Tab này
              </label>
              <select
                id="tab-mode"
                value={tabMode}
                onChange={(e) => void persistTabMode(e.target.value as TabDubMode)}
                style={{
                  ...base,
                  fontSize: 12,
                  fontWeight: 600,
                  color: T.black,
                  background: "#ffffff",
                  border: "1px solid rgba(14,15,12,0.15)",
                  borderRadius: 8,
                  padding: "5px 8px",
                  cursor: "pointer",
                  outline: "none",
                  maxWidth: 130,
                }}
              >
                <option value="default">Theo global</option>
                <option value="on">Luôn bật</option>
                <option value="off">Luôn tắt</option>
              </select>
            </div>
          ) : null}
        </div>

        {/* Error state */}
        {status === "Error" ? (
          <div
            style={{
              background: T.dangerBg,
              borderRadius: 12,
              padding: "10px 12px",
              marginBottom: 12,
            }}
          >
            {errorDetail ? (
              <p
                style={{
                  margin: "0 0 8px",
                  fontSize: 12,
                  color: T.danger,
                  fontWeight: 600,
                  lineHeight: 1.45,
                }}
              >
                {errorDetail}
              </p>
            ) : null}
            <BtnGhost
              style={{ fontSize: 12 }}
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
            </BtnGhost>
          </div>
        ) : null}

      </div>
    </div>
  );
}
