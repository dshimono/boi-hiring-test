import { cookies } from "next/headers";
import { NextResponse, type NextRequest } from "next/server";

const API_URL = process.env.API_URL ?? "http://localhost:8000";

// Client components can't read the httpOnly access_token cookie, so this
// route runs server-side to attach it and proxy the request to the API.
export async function POST(request: NextRequest) {
  const token = cookies().get("access_token")?.value;
  if (!token) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }

  const upstream = await fetch(`${API_URL}/api/v1/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: await request.text(),
  });

  const body = await upstream.text();
  return new NextResponse(body, {
    status: upstream.status,
    headers: { "Content-Type": "application/json" },
  });
}
