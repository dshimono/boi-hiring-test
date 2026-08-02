import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.API_URL ?? "http://localhost:8000";
// Railway's edge proxy doesn't forward the public hostname to the container, so
// request.url resolves to the container's internal bind address. Build redirects
// from the known public origin instead.
const WEBSITE_URL = process.env.NEXT_PUBLIC_WEBSITE_URL ?? "http://localhost:3000";
const TOKEN_COOKIE = "access_token";
const DEFAULT_MAX_AGE = 60 * 60 * 24;

function expirySeconds(accessToken: string): number {
  try {
    const payload = JSON.parse(Buffer.from(accessToken.split(".")[1], "base64url").toString("utf-8"));
    if (typeof payload.exp !== "number") return DEFAULT_MAX_AGE;
    return Math.max(payload.exp - Math.floor(Date.now() / 1000), 0);
  } catch {
    return DEFAULT_MAX_AGE;
  }
}

export async function GET(request: NextRequest): Promise<NextResponse> {
  const token = request.nextUrl.searchParams.get("token");
  if (!token) {
    return NextResponse.redirect(new URL("/auth/verify/error?reason=missing", WEBSITE_URL));
  }

  const res = await fetch(`${API_URL}/api/v1/auth/verify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token }),
  });

  if (!res.ok) {
    return NextResponse.redirect(new URL("/auth/verify/error", WEBSITE_URL));
  }

  const { access_token: accessToken } = (await res.json()) as { access_token: string };
  const response = NextResponse.redirect(new URL("/", WEBSITE_URL));
  response.cookies.set(TOKEN_COOKIE, accessToken, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: expirySeconds(accessToken),
  });
  return response;
}
