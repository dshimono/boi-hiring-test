import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest): Promise<NextResponse> {
  const response = NextResponse.redirect(new URL("/sign-in", request.url));
  response.cookies.set("access_token", "", { path: "/", maxAge: 0 });
  return response;
}
