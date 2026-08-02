export const metadata = { title: "Sign-in link didn't work – Board of Innovation" };

const MESSAGES: Record<string, string> = {
  missing: "This link is missing its token.",
};

export default function VerifyErrorPage({
  searchParams,
}: {
  searchParams: { reason?: string };
}) {
  const message =
    MESSAGES[searchParams.reason ?? ""] ?? "This link may have expired or already been used.";

  return (
    <main className="flex min-h-screen items-center justify-center bg-[var(--surface-page)] px-6 text-[var(--text-primary)]">
      <div className="w-full max-w-sm text-center">
        <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--text-muted)]">
          Board of Innovation
        </p>
        <h1 className="mt-3 text-2xl font-semibold tracking-tight">Sign-in link didn&apos;t work</h1>
        <p className="mt-2 text-sm leading-relaxed text-[var(--text-secondary)]">{message}</p>
        <a
          href="/sign-in"
          className="mt-6 inline-block text-sm font-medium text-[var(--series-google)] hover:underline"
        >
          Back to sign in
        </a>
      </div>
    </main>
  );
}
