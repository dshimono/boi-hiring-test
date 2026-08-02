import { cookies } from "next/headers";

const API_URL = process.env.API_URL ?? "http://localhost:8000";

async function getCurrentUserEmail(token: string): Promise<string | null> {
  const res = await fetch(`${API_URL}/api/v1/users/me`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!res.ok) return null;
  const user = (await res.json()) as { email: string };
  return user.email;
}

export default async function AuthStatus() {
  const token = cookies().get("access_token")?.value;
  const email = token ? await getCurrentUserEmail(token) : null;

  if (!email) {
    return (
      <a href="/sign-in" className="text-sm font-medium text-[var(--series-google)] hover:underline">
        Sign in
      </a>
    );
  }

  return (
    <div className="flex items-center gap-3 text-sm text-[var(--text-secondary)]">
      <span>{email}</span>
      <form action="/auth/sign-out" method="post">
        <button type="submit" className="font-medium text-[var(--series-google)] hover:underline">
          Sign out
        </button>
      </form>
    </div>
  );
}
