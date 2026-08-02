const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const TOKEN_COOKIE = "access_token";

type CurrentUser = {
  id: string;
  email: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
};

async function postJSON<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail ?? "Something went wrong.");
  }
  return data as T;
}

export function requestMagicLink(email: string): Promise<{ message: string }> {
  return postJSON("/api/v1/auth/magic-link", { email });
}

export function verifyMagicLink(token: string): Promise<{ access_token: string }> {
  return postJSON("/api/v1/auth/verify", { token });
}

export async function fetchCurrentUser(token: string): Promise<CurrentUser | null> {
  const res = await fetch(`${API_URL}/api/v1/users/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.ok ? res.json() : null;
}

function decodeExpiry(token: string): number | null {
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return typeof payload.exp === "number" ? payload.exp : null;
  } catch {
    return null;
  }
}

export function storeToken(token: string): void {
  const exp = decodeExpiry(token);
  const maxAge = exp ? Math.max(exp - Math.floor(Date.now() / 1000), 0) : 60 * 60 * 24;
  document.cookie = `${TOKEN_COOKIE}=${token}; path=/; max-age=${maxAge}; samesite=lax`;
}

export function getStoredToken(): string | null {
  const match = document.cookie.match(new RegExp(`(?:^|; )${TOKEN_COOKIE}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

export function clearToken(): void {
  document.cookie = `${TOKEN_COOKIE}=; path=/; max-age=0`;
}
