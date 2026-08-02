import { Suspense } from "react";
import VerifyClient from "./VerifyClient";
import { VerifyStatus } from "./VerifyStatus";

export const metadata = { title: "Signing in – Board of Innovation" };

export default function VerifyPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[var(--surface-page)] px-6 text-[var(--text-primary)]">
      <Suspense fallback={<VerifyStatus state="loading" />}>
        <VerifyClient />
      </Suspense>
    </main>
  );
}
