export function VerifyStatus({ state, message }: { state: "loading" | "error"; message?: string }) {
  return (
    <div className="w-full max-w-sm text-center">
      <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--text-muted)]">
        Board of Innovation
      </p>
      <h1 className="mt-3 text-2xl font-semibold tracking-tight">
        {state === "loading" ? "Signing you in…" : "Sign-in link didn't work"}
      </h1>
      <p className="mt-2 text-sm leading-relaxed text-[var(--text-secondary)]">
        {state === "loading" ? "Verifying your link, just a moment." : message}
      </p>
      {state === "error" ? (
        <a
          href="/sign-in"
          className="mt-6 inline-block text-sm font-medium text-[var(--series-google)] hover:underline"
        >
          Back to sign in
        </a>
      ) : null}
    </div>
  );
}
