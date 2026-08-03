import { cookies } from "next/headers";
import { NextResponse, type NextRequest } from "next/server";

const API_URL = process.env.API_URL ?? "http://localhost:8000";

// Client components can't read the httpOnly access_token cookie, so this
// route runs server-side to attach it and proxy the request to the API.
// Whether a missing/invalid token is allowed through is the backend's call
// (e.g. AUTH_ENABLED=false bypasses auth entirely) — don't pre-empt it here.
export async function POST(request: NextRequest) {
  const token = cookies().get("access_token")?.value;

  const upstream = await fetch(`${API_URL}/api/v1/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: await request.text(),
    signal: request.signal,
  });

  if (!upstream.ok) {
    const body = await upstream.text();
    return new NextResponse(body, {
      status: upstream.status,
      headers: { "Content-Type": "application/json" },
    });
  }

  return new NextResponse(upstream.body, {
    status: upstream.status,
    headers: { "Content-Type": "text/event-stream", "Cache-Control": "no-cache" },
  });
}
