import { Link } from "react-router-dom";
import { useState } from "react";

import {
  createBillingPortalSession,
  createCheckoutSession,
  getStoredAccessToken,
  logoutDashboard,
} from "./api";

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
    <main style={{ fontFamily: "system-ui", padding: 24 }}>
      <h1>Voice-Pro Dashboard</h1>
      <p>SPA — Epic 3 email đăng nhập / đăng ký.</p>
      {token ? (
        <p style={{ color: "green" }}>Đã đăng nhập (access token trong session).</p>
      ) : (
        <p>Chưa đăng nhập.</p>
      )}
      {billingError ? (
        <p style={{ color: "crimson", marginTop: 8 }} role="alert">
          {billingError}
        </p>
      ) : null}
      <nav style={{ display: "flex", gap: 16, marginTop: 16, flexWrap: "wrap", alignItems: "center" }}>
        <Link to="/login">Đăng nhập</Link>
        <Link to="/register">Đăng ký</Link>
        {token ? (
          <>
            <button type="button" disabled={billingBusy} onClick={() => void openCheckout()}>
              Upgrade (Stripe Checkout)
            </button>
            <button type="button" disabled={billingBusy} onClick={() => void openPortal()}>
              Quản lý gói (Stripe Portal)
            </button>
            <button
              type="button"
              onClick={() => {
                void logoutDashboard().then(() => window.location.reload());
              }}
            >
              Đăng xuất
            </button>
          </>
        ) : null}
      </nav>
      <p style={{ marginTop: 24, fontSize: 13, color: "#555" }}>
        Sau khi thanh toán, trạng thái gói được đồng bộ qua webhook Stripe (backend); không tin client-only.
      </p>
    </main>
  );
}
