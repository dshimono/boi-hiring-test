const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

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
