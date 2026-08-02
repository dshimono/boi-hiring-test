"use client";

import { useState, type FormEvent } from "react";
import { requestMagicLink } from "./auth";

type Mode = "sign-in" | "sign-up";

export default function AuthForm({ mode }: { mode: Mode }) {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "sent" | "error">("idle");
  const [error, setError] = useState("");

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setStatus("loading");
    setError("");
    try {
      await requestMagicLink(email);
      setStatus("sent");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
      setStatus("error");
    }
  }

  if (status === "sent") {
    return (
      <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-6 text-center">
        <p className="text-sm font-medium">Check your email</p>
        <p className="mt-2 text-sm leading-relaxed text-[var(--text-secondary)]">
          If an account exists for{" "}
          <span className="font-medium text-[var(--text-primary)]">{email}</span>, a sign-in link
          is on its way. It expires in 15 minutes.
        </p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      <label className="flex flex-col gap-1.5">
        <span className="text-xs font-medium text-[var(--text-secondary)]">Email</span>
        <input
          type="email"
          required
          autoFocus
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@company.com"
          className="rounded-lg border border-[var(--border)] bg-[var(--surface-2)] px-3 py-2.5 text-sm outline-none transition focus:border-[var(--border-strong)]"
        />
      </label>

      {error ? <p className="text-sm text-red-600 dark:text-red-400">{error}</p> : null}

      <button
        type="submit"
        disabled={status === "loading"}
        className="mt-1 rounded-lg bg-[var(--text-primary)] px-4 py-2.5 text-sm font-medium text-[var(--surface-page)] transition hover:opacity-90 disabled:opacity-50"
      >
        {status === "loading" ? "Sending…" : mode === "sign-in" ? "Send sign-in link" : "Create account"}
      </button>
    </form>
  );
}
