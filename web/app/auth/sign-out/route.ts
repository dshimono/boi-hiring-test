import { NextResponse } from "next/server";

// Railway's edge proxy doesn't forward the public hostname to the container, so
// request.url resolves to the container's internal bind address. Build redirects
// from the known public origin instead.
const WEBSITE_URL = process.env.NEXT_PUBLIC_WEBSITE_URL ?? "http://localhost:3000";

export async function POST(): Promise<NextResponse> {
  const response = NextResponse.redirect(new URL("/sign-in", WEBSITE_URL));
  response.cookies.set("access_token", "", { path: "/", maxAge: 0 });
  return response;
}
