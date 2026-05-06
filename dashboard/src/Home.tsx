import { Link } from "react-router-dom";

import { getStoredAccessToken, logoutDashboard } from "./api";

export default function HomePage() {
  const token = getStoredAccessToken();

  return (
    <main style={{ fontFamily: "system-ui", padding: 24 }}>
      <h1>Voice-Pro Dashboard</h1>
      <p>SPA — Epic 3 email đăng nhập / đăng ký.</p>
      {token ? (
        <p style={{ color: "green" }}>Đã đăng nhập (access token trong session).</p>
      ) : (
        <p>Chưa đăng nhập.</p>
      )}
      <nav style={{ display: "flex", gap: 16, marginTop: 16 }}>
        <Link to="/login">Đăng nhập</Link>
        <Link to="/register">Đăng ký</Link>
        {token ? (
          <button
            type="button"
            onClick={() => {
              void logoutDashboard().then(() => window.location.reload());
            }}
          >
            Đăng xuất
          </button>
        ) : null}
      </nav>
    </main>
  );
}
