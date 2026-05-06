import { useEffect, useState } from "react";

import { LANG_OPTIONS } from "../../constants";

export default function App() {
  const [dubMode, setDubMode] = useState(false);
  const [lang, setLang] = useState("vi");
  const [status, setStatus] = useState("Ready");
  const [errorDetail, setErrorDetail] = useState("");

  useEffect(() => {
    // Preferences come from sync storage; ephemeral state from local
    chrome.storage.sync.get(["dubMode", "dubTargetLang"], (s) => {
      if (typeof s.dubMode === "boolean") setDubMode(s.dubMode);
      if (typeof s.dubTargetLang === "string") setLang(s.dubTargetLang);
    });
    chrome.storage.local.get(["dubStatus", "dubErrorMessage"], (s) => {
      if (typeof s.dubStatus === "string") setStatus(s.dubStatus);
      if (typeof s.dubErrorMessage === "string") setErrorDetail(s.dubErrorMessage);
    });

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
      }
    };
    chrome.storage.onChanged.addListener(handler);
    return () => chrome.storage.onChanged.removeListener(handler);
  }, []);

  return (
    <div style={{ padding: 12, fontFamily: "system-ui", minWidth: 260 }}>
      <h1 style={{ fontSize: 14, margin: "0 0 8px" }}>Voice-Pro Dub</h1>
      <label style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
        <input
          type="checkbox"
          checked={dubMode}
          onChange={(e) => {
            const v = e.target.checked;
            setDubMode(v);
            void chrome.storage.sync.set({ dubMode: v });
          }}
        />
        Dub Mode
      </label>
      <label style={{ display: "block", fontSize: 12, marginBottom: 8 }}>
        Ngôn ngữ đích
        <select
          value={lang}
          onChange={(e) => {
            const v = e.target.value;
            setLang(v);
            void chrome.storage.sync.set({ dubTargetLang: v });
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
      <div style={{ fontSize: 11, color: "#666" }}>Status: {status}</div>
      {status === "Error" ? (
        <div style={{ marginTop: 6 }}>
          {errorDetail ? (
            <div style={{ fontSize: 11, color: "#b00020", marginBottom: 6 }}>{errorDetail}</div>
          ) : null}
          <button
            style={{ fontSize: 11, cursor: "pointer", padding: "2px 8px" }}
            onClick={() => {
              void chrome.storage.local.set({ dubStatus: "Ready", dubErrorMessage: "" });
              void chrome.storage.sync.set({ dubMode: true });
              setDubMode(true);
              setStatus("Ready");
              setErrorDetail("");
            }}
          >
            Thử lại
          </button>
        </div>
      ) : null}
    </div>
  );
}
