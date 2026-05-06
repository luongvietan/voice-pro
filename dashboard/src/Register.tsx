import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { registerEmail } from "./api";

export default function RegisterPage() {
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    void registerEmail(email, password)
      .then(() => nav("/"))
      .catch((err: unknown) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setBusy(false));
  }

  return (
    <main style={{ fontFamily: "system-ui", maxWidth: 360, margin: "48px auto", padding: 16 }}>
      <h1 style={{ fontSize: 20 }}>Đăng ký</h1>
      <p style={{ fontSize: 13, color: "#555" }}>Tối thiểu 8 ký tự, có chữ hoa và số.</p>
      <form onSubmit={onSubmit}>
        <label style={{ display: "block", marginBottom: 8 }}>
          Email
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            style={{ display: "block", width: "100%", marginTop: 4 }}
          />
        </label>
        <label style={{ display: "block", marginBottom: 12 }}>
          Mật khẩu
          <input
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{ display: "block", width: "100%", marginTop: 4 }}
          />
        </label>
        <button type="submit" disabled={busy} style={{ padding: "8px 16px" }}>
          {busy ? "..." : "Đăng ký"}
        </button>
      </form>
      {error ? (
        <pre style={{ color: "#b00020", fontSize: 12, whiteSpace: "pre-wrap" }}>{error}</pre>
      ) : null}
      <p style={{ marginTop: 16 }}>
        <Link to="/login">Đã có tài khoản? Đăng nhập</Link>
      </p>
      <p style={{ marginTop: 8 }}>
        <Link to="/">← Về trang chủ</Link>
      </p>
    </main>
  );
}
