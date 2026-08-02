import Link from "next/link";
import AuthForm from "../AuthForm";

export const metadata = { title: "Sign up – Board of Innovation" };

export default function SignUpPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[var(--surface-page)] px-6 text-[var(--text-primary)]">
      <div className="w-full max-w-sm">
        <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--text-muted)]">
          Board of Innovation
        </p>
        <h1 className="mt-3 text-3xl font-semibold leading-[1.1] tracking-tight">
          Create your account
        </h1>
        <p className="mt-2 text-sm leading-relaxed text-[var(--text-secondary)]">
          No password to set. We&apos;ll email you a link — click it and you&apos;re in.
        </p>

        <div className="mt-8">
          <AuthForm mode="sign-up" />
        </div>

        <p className="mt-6 text-center text-sm text-[var(--text-secondary)]">
          Already have an account?{" "}
          <Link href="/sign-in" className="font-medium text-[var(--series-google)] hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </main>
  );
}
