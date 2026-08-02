import type { NextRequest } from "next/server";

export async function GET(_req: NextRequest, { params }: { params: { path: string[] } }) {
  const apiUrl = process.env.API_URL ?? "http://localhost:8000";
  const upstream = await fetch(`${apiUrl}/static/ads/${params.path.map(encodeURIComponent).join("/")}`, {
    cache: "no-store",
  });

  if (!upstream.ok || !upstream.body) {
    return new Response(null, { status: upstream.status });
  }

  return new Response(upstream.body, {
    status: upstream.status,
    headers: {
      "content-type": upstream.headers.get("content-type") ?? "application/octet-stream",
      "cache-control": "public, max-age=3600",
    },
  });
}
