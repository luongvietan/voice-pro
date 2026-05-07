import { Link } from "react-router-dom";
import { useState } from "react";

import {
  createBillingPortalSession,
  createCheckoutSession,
  getStoredAccessToken,
  logoutDashboard,
} from "./api";

const S = {
  page: {
    minHeight: "100vh",
    background: "#ffffff",
    fontFamily: "'Inter',Helvetica,Arial,sans-serif",
    fontFeatureSettings: '"calt"',
    color: "#0e0f0c",
    WebkitFontSmoothing: "antialiased" as const,
  } as React.CSSProperties,
  nav: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "16px 40px",
    borderBottom: "1px solid rgba(14,15,12,0.08)",
    background: "#ffffff",
    position: "sticky" as const,
    top: 0,
    zIndex: 10,
  } as React.CSSProperties,
  logo: {
    fontSize: 20,
    fontWeight: 900,
    letterSpacing: "-0.5px",
    color: "#0e0f0c",
    textDecoration: "none",
  } as React.CSSProperties,
  main: {
    maxWidth: 920,
    margin: "0 auto",
    padding: "56px 40px",
  } as React.CSSProperties,
  heading: {
    fontSize: "clamp(36px,5vw,56px)",
    fontWeight: 900,
    lineHeight: 0.9,
    letterSpacing: "-1.5px",
    margin: "0 0 12px",
    fontFeatureSettings: '"calt"',
  } as React.CSSProperties,
  subtext: {
    fontSize: 16,
    fontWeight: 400,
    color: "#454745",
    lineHeight: 1.55,
    margin: "0 0 40px",
  } as React.CSSProperties,
  badge: (logged: boolean) =>
    ({
      display: "inline-flex",
      alignItems: "center",
      gap: 6,
      padding: "6px 14px",
      borderRadius: 9999,
      fontSize: 13,
      fontWeight: 600,
      background: logged ? "#e2f6d5" : "rgba(14,15,12,0.06)",
      color: logged ? "#054d28" : "#454745",
      marginBottom: 40,
    }) as React.CSSProperties,
  card: {
    background: "#ffffff",
    borderRadius: 30,
    padding: "32px",
    boxShadow: "rgba(14,15,12,0.12) 0px 0px 0px 1px",
    marginBottom: 24,
  } as React.CSSProperties,
  cardTitle: {
    fontSize: 20,
    fontWeight: 700,
    marginBottom: 8,
    letterSpacing: "-0.3px",
  } as React.CSSProperties,
  cardDesc: {
    fontSize: 15,
    color: "#454745",
    fontWeight: 400,
    lineHeight: 1.55,
    marginBottom: 24,
  } as React.CSSProperties,
  btnPrimary: {
    display: "inline-flex",
    alignItems: "center",
    gap: 6,
    background: "#9fe870",
    color: "#163300",
    border: "none",
    borderRadius: 9999,
    padding: "10px 22px",
    fontSize: 15,
    fontWeight: 600,
    cursor: "pointer",
    transition: "transform 0.15s ease",
    textDecoration: "none",
    fontFamily: "'Inter',Helvetica,Arial,sans-serif",
  } as React.CSSProperties,
  btnSecondary: {
    display: "inline-flex",
    alignItems: "center",
    gap: 6,
    background: "rgba(22,51,0,0.08)",
    color: "#0e0f0c",
    border: "none",
    borderRadius: 9999,
    padding: "10px 22px",
    fontSize: 15,
    fontWeight: 600,
    cursor: "pointer",
    transition: "transform 0.15s ease",
    textDecoration: "none",
    fontFamily: "'Inter',Helvetica,Arial,sans-serif",
  } as React.CSSProperties,
  btnDanger: {
    display: "inline-flex",
    alignItems: "center",
    gap: 6,
    background: "rgba(208,50,56,0.1)",
    color: "#d03238",
    border: "none",
    borderRadius: 9999,
    padding: "10px 22px",
    fontSize: 15,
    fontWeight: 600,
    cursor: "pointer",
    transition: "transform 0.15s ease",
    fontFamily: "'Inter',Helvetica,Arial,sans-serif",
  } as React.CSSProperties,
  errorBox: {
    background: "rgba(208,50,56,0.08)",
    color: "#d03238",
    borderRadius: 16,
    padding: "12px 16px",
    fontSize: 14,
    fontWeight: 600,
    marginBottom: 24,
  } as React.CSSProperties,
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(260px,1fr))",
    gap: 20,
  } as React.CSSProperties,
};

function HoverBtn({
  style,
  children,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { style?: React.CSSProperties }) {
  const [hover, setHover] = useState(false);
  return (
    <button
      {...props}
      style={{ ...style, transform: hover ? "scale(1.04)" : "scale(1)" }}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
    >
      {children}
    </button>
  );
}

export default function HomePage() {
  const token = getStoredAccessToken();
  const [billingError, setBillingError] = useState<string | null>(null);
  const [billingBusy, setBillingBusy] = useState(false);

  async function openCheckout() {
    setBillingError(null);
    setBillingBusy(true);
    try {
      const url = await createCheckoutSession();
      setBillingError(null);
      window.location.assign(url);
    } catch (e) {
      setBillingError(e instanceof Error ? e.message : "Không mở được thanh toán");
    } finally {
      setBillingBusy(false);
    }
  }

  async function openPortal() {
    setBillingError(null);
    setBillingBusy(true);
    try {
      const url = await createBillingPortalSession();
      setBillingError(null);
      window.location.assign(url);
    } catch (e) {
      setBillingError(e instanceof Error ? e.message : "Không mở được cổng quản lý gói");
    } finally {
      setBillingBusy(false);
    }
  }

  return (
    <div style={S.page}>
      {/* Nav */}
      <nav style={S.nav}>
        <Link to="/" style={S.logo}>
          Voice<span style={{ color: "#9fe870" }}>Pro</span>
        </Link>
        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          {!token ? (
            <>
              <Link
                to="/login"
                style={{ ...S.btnSecondary, padding: "8px 18px", fontSize: 14 }}
              >
                Đăng nhập
              </Link>
              <Link
                to="/register"
                style={{ ...S.btnPrimary, padding: "8px 18px", fontSize: 14 }}
              >
                Đăng ký
              </Link>
            </>
          ) : (
            <HoverBtn
              type="button"
              style={S.btnDanger}
              onClick={() => {
                void logoutDashboard().then(() => window.location.reload());
              }}
            >
              Đăng xuất
            </HoverBtn>
          )}
        </div>
      </nav>

      <main style={S.main}>
        {/* Header */}
        <h1 style={S.heading}>
          Voice-Pro{" "}
          <span style={{ color: "#9fe870" }}>Dashboard</span>
        </h1>
        <p style={S.subtext}>
          Quản lý tài khoản, gói cước và cài đặt dubbing của bạn.
        </p>

        {/* Auth status badge */}
        <div style={S.badge(!!token)}>
          {token ? (
            <>
              <span style={{ fontSize: 10 }}>●</span> Đã đăng nhập
            </>
          ) : (
            <>
              <span style={{ fontSize: 10 }}>○</span> Chưa đăng nhập
            </>
          )}
        </div>

        {/* Error */}
        {billingError ? (
          <div style={S.errorBox} role="alert">
            {billingError}
          </div>
        ) : null}

        {/* Cards grid */}
        <div style={S.grid}>
          {/* Auth card */}
          {!token ? (
            <div style={S.card}>
              <div style={S.cardTitle}>Bắt đầu ngay</div>
              <p style={S.cardDesc}>
                Đăng nhập hoặc tạo tài khoản để lưu cài đặt và theo dõi credit dubbing.
              </p>
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                <Link to="/login" style={S.btnPrimary}>
                  Đăng nhập
                </Link>
                <Link to="/register" style={S.btnSecondary}>
                  Tạo tài khoản
                </Link>
              </div>
            </div>
          ) : null}

          {/* Billing card */}
          {token ? (
            <div style={S.card}>
              <div style={S.cardTitle}>Gói cước</div>
              <p style={S.cardDesc}>
                Nâng cấp lên Pro để không giới hạn phút dubbing. Quản lý gói, hóa đơn và phương thức thanh toán.
              </p>
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                <HoverBtn
                  type="button"
                  disabled={billingBusy}
                  style={{
                    ...S.btnPrimary,
                    opacity: billingBusy ? 0.6 : 1,
                    cursor: billingBusy ? "wait" : "pointer",
                  }}
                  onClick={() => void openCheckout()}
                >
                  {billingBusy ? "Đang mở..." : "⬆ Nâng cấp Pro"}
                </HoverBtn>
                <HoverBtn
                  type="button"
                  disabled={billingBusy}
                  style={{
                    ...S.btnSecondary,
                    opacity: billingBusy ? 0.6 : 1,
                    cursor: billingBusy ? "wait" : "pointer",
                  }}
                  onClick={() => void openPortal()}
                >
                  Quản lý gói
                </HoverBtn>
              </div>
            </div>
          ) : null}

          {/* Info card */}
          <div style={{ ...S.card, background: "#0e0f0c", color: "#ffffff" }}>
            <div style={{ ...S.cardTitle, color: "#9fe870" }}>30 phút miễn phí</div>
            <p style={{ ...S.cardDesc, color: "rgba(255,255,255,0.65)" }}>
              Mỗi tháng bạn nhận 30 phút credit dubbing miễn phí. Reset tự động vào đầu tháng.
            </p>
            <div
              style={{
                background: "rgba(159,232,112,0.12)",
                borderRadius: 16,
                padding: "12px 16px",
                fontSize: 13,
                color: "rgba(255,255,255,0.7)",
                fontWeight: 400,
                lineHeight: 1.55,
              }}
            >
              Sau khi thanh toán, trạng thái gói được đồng bộ qua webhook Stripe — không tin client-only.
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
