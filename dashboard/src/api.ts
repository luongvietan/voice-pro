const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

async function extractErrorMessage(res: Response): Promise<string> {
  const text = await res.text().catch(() => "");
  try {
    const json = JSON.parse(text) as { detail?: unknown };
    if (typeof json.detail === "string") return json.detail;
    if (json.detail !== undefined) return JSON.stringify(json.detail);
  } catch {
    /* plain text */
  }
  return text || `HTTP ${res.status}`;
}

export function getStoredAccessToken(): string | null {
  return sessionStorage.getItem("vp_access_token");
}

export function setStoredAccessToken(token: string): void {
  sessionStorage.setItem("vp_access_token", token);
}

export function clearStoredAccessToken(): void {
  sessionStorage.removeItem("vp_access_token");
}

export async function registerEmail(email: string, password: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/v1/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error(await extractErrorMessage(res));
  const data = (await res.json()) as { access_token: string };
  setStoredAccessToken(data.access_token);
}

export async function loginEmail(email: string, password: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error(await extractErrorMessage(res));
  const data = (await res.json()) as { access_token: string };
  setStoredAccessToken(data.access_token);
}

export async function logoutDashboard(): Promise<void> {
  await fetch(`${API_BASE}/api/v1/auth/logout`, {
    method: "POST",
    credentials: "include",
  }).catch(() => undefined);
  clearStoredAccessToken();
}

export async function createCheckoutSession(): Promise<string> {
  const token = getStoredAccessToken();
  if (!token) throw new Error("Chưa đăng nhập");
  const res = await fetch(`${API_BASE}/api/v1/billing/stripe/checkout-session`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(await extractErrorMessage(res));
  const data = (await res.json()) as { url: string };
  return data.url;
}

export async function createBillingPortalSession(): Promise<string> {
  const token = getStoredAccessToken();
  if (!token) throw new Error("Chưa đăng nhập");
  const res = await fetch(`${API_BASE}/api/v1/billing/stripe/portal-session`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(await extractErrorMessage(res));
  const data = (await res.json()) as { url: string };
  return data.url;
}
