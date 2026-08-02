"use client";

import { useEffect, useState } from "react";
import { clearToken, fetchCurrentUser, getStoredToken } from "./auth";

export default function AuthStatus() {
  const [email, setEmail] = useState<string | null>(null);
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    const token = getStoredToken();
    if (!token) {
      setChecked(true);
      return;
    }
    fetchCurrentUser(token).then((user) => {
      if (!user) clearToken();
      setEmail(user?.email ?? null);
      setChecked(true);
    });
  }, []);

  if (!checked) return null;

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
      <button
        type="button"
        onClick={() => {
          clearToken();
          window.location.href = "/sign-in";
        }}
        className="font-medium text-[var(--series-google)] hover:underline"
      >
        Sign out
      </button>
    </div>
  );
}
