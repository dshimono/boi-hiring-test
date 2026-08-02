"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { storeToken, verifyMagicLink } from "../../auth";
import { VerifyStatus } from "./VerifyStatus";

export default function VerifyClient() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = searchParams.get("token");
    if (!token) {
      setError("This link is missing its token.");
      return;
    }
    verifyMagicLink(token)
      .then(({ access_token }) => {
        storeToken(access_token);
        router.replace("/");
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Something went wrong."));
  }, [searchParams, router]);

  if (error) return <VerifyStatus state="error" message={error} />;
  return <VerifyStatus state="loading" />;
}
