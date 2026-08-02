import Link from "next/link";
import AuthForm from "../AuthForm";

export const metadata = { title: "Sign in – Board of Innovation" };

export default function SignInPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[var(--surface-page)] px-6 text-[var(--text-primary)]">
      <div className="w-full max-w-sm">
        <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--text-muted)]">
          Board of Innovation
        </p>
        <h1 className="mt-3 text-3xl font-semibold leading-[1.1] tracking-tight">Sign in</h1>
        <p className="mt-2 text-sm leading-relaxed text-[var(--text-secondary)]">
          Enter your email and we&apos;ll send you a link to sign in — no password needed.
        </p>

        <div className="mt-8">
          <AuthForm mode="sign-in" />
        </div>

        <p className="mt-6 text-center text-sm text-[var(--text-secondary)]">
          Don&apos;t have an account?{" "}
          <Link href="/sign-up" className="font-medium text-[var(--series-google)] hover:underline">
            Sign up
          </Link>
        </p>
      </div>
    </main>
  );
}
