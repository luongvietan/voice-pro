import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { loginEmail } from "./api";

const S = {
  page: {
    minHeight: "100vh",
    display: "flex",
    flexDirection: "column" as const,
    background: "#f8faf7",
    fontFamily: "'Inter',Helvetica,Arial,sans-serif",
    fontFeatureSettings: '"calt"',
    color: "#0e0f0c",
    WebkitFontSmoothing: "antialiased" as const,
  } as React.CSSProperties,
  center: {
    flex: 1,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "40px 16px",
  } as React.CSSProperties,
  card: {
    background: "#ffffff",
    borderRadius: 30,
    padding: "48px 40px",
    width: "100%",
    maxWidth: 420,
    boxShadow: "rgba(14,15,12,0.12) 0px 0px 0px 1px",
  } as React.CSSProperties,
  logo: {
    fontSize: 22,
    fontWeight: 900,
    textDecoration: "none",
    color: "#0e0f0c",
    display: "block",
    marginBottom: 32,
  } as React.CSSProperties,
  heading: {
    fontSize: 32,
    fontWeight: 900,
    lineHeight: 0.9,
    letterSpacing: "-1px",
    marginBottom: 8,
    fontFeatureSettings: '"calt"',
  } as React.CSSProperties,
  subtext: {
    fontSize: 15,
    fontWeight: 400,
    color: "#454745",
    marginBottom: 36,
    lineHeight: 1.55,
  } as React.CSSProperties,
  fieldGroup: {
    marginBottom: 20,
  } as React.CSSProperties,
  label: {
    display: "block",
    fontSize: 14,
    fontWeight: 600,
    marginBottom: 8,
    color: "#0e0f0c",
  } as React.CSSProperties,
  input: {
    display: "block",
    width: "100%",
    padding: "12px 16px",
    fontSize: 15,
    fontWeight: 400,
    fontFamily: "'Inter',Helvetica,Arial,sans-serif",
    border: "1px solid rgba(14,15,12,0.2)",
    borderRadius: 12,
    outline: "none",
    background: "#ffffff",
    color: "#0e0f0c",
    boxSizing: "border-box" as const,
    transition: "border-color 0.15s ease, box-shadow 0.15s ease",
  } as React.CSSProperties,
  inputFocus: {
    borderColor: "#9fe870",
    boxShadow: "0 0 0 3px rgba(159,232,112,0.3)",
  } as React.CSSProperties,
  btnPrimary: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    width: "100%",
    background: "#9fe870",
    color: "#163300",
    border: "none",
    borderRadius: 9999,
    padding: "13px 24px",
    fontSize: 16,
    fontWeight: 600,
    cursor: "pointer",
    transition: "transform 0.15s ease",
    fontFamily: "'Inter',Helvetica,Arial,sans-serif",
    marginTop: 8,
  } as React.CSSProperties,
  errorBox: {
    background: "rgba(208,50,56,0.08)",
    color: "#d03238",
    borderRadius: 12,
    padding: "12px 14px",
    fontSize: 14,
    fontWeight: 600,
    marginTop: 16,
    lineHeight: 1.4,
  } as React.CSSProperties,
  footer: {
    marginTop: 28,
    display: "flex",
    flexDirection: "column" as const,
    gap: 8,
  } as React.CSSProperties,
  link: {
    color: "#054d28",
    textDecoration: "none",
    fontWeight: 600,
    fontSize: 14,
  } as React.CSSProperties,
};

function FocusInput(props: React.InputHTMLAttributes<HTMLInputElement>) {
  const [focused, setFocused] = useState(false);
  return (
    <input
      {...props}
      style={{ ...S.input, ...(focused ? S.inputFocus : {}) }}
      onFocus={() => setFocused(true)}
      onBlur={() => setFocused(false)}
    />
  );
}

export default function LoginPage() {
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [btnHover, setBtnHover] = useState(false);

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    void loginEmail(email, password)
      .then(() => nav("/"))
      .catch((err: unknown) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setBusy(false));
  }

  return (
    <div style={S.page}>
      <div style={S.center}>
        <div style={S.card}>
          <Link to="/" style={S.logo}>
            Voice<span style={{ color: "#9fe870" }}>Pro</span>
          </Link>

          <h1 style={S.heading}>Đăng nhập</h1>
          <p style={S.subtext}>Chào mừng trở lại. Nhập thông tin tài khoản của bạn.</p>

          <form onSubmit={onSubmit}>
            <div style={S.fieldGroup}>
              <label style={S.label} htmlFor="email">Email</label>
              <FocusInput
                id="email"
                type="email"
                required
                value={email}
                autoComplete="email"
                placeholder="you@example.com"
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div style={S.fieldGroup}>
              <label style={S.label} htmlFor="password">Mật khẩu</label>
              <FocusInput
                id="password"
                type="password"
                required
                value={password}
                autoComplete="current-password"
                placeholder="••••••••"
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>

            <button
              type="submit"
              disabled={busy}
              style={{
                ...S.btnPrimary,
                transform: btnHover && !busy ? "scale(1.02)" : "scale(1)",
                opacity: busy ? 0.7 : 1,
                cursor: busy ? "wait" : "pointer",
              }}
              onMouseEnter={() => setBtnHover(true)}
              onMouseLeave={() => setBtnHover(false)}
            >
              {busy ? "Đang đăng nhập..." : "Đăng nhập"}
            </button>
          </form>

          {error ? (
            <div style={S.errorBox} role="alert">
              {error}
            </div>
          ) : null}

          <div style={S.footer}>
            <Link to="/register" style={S.link}>
              Chưa có tài khoản? Đăng ký ngay →
            </Link>
            <Link to="/" style={{ ...S.link, color: "#868685", fontWeight: 400 }}>
              ← Về trang chủ
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
