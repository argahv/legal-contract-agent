import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { getPublicApiBaseUrl } from "@/lib/env";

export async function POST(request: Request) {
  const jar = await cookies();
  const fromCookie = jar.get("la_refresh")?.value;
  const body: unknown = await request.json().catch(() => ({}));
  const refreshFromBody =
    typeof body === "object" &&
    body !== null &&
    "refresh_token" in body &&
    typeof (body as { refresh_token: unknown }).refresh_token === "string"
      ? (body as { refresh_token: string }).refresh_token
      : null;

  const refresh = fromCookie ?? refreshFromBody;
  if (refresh == null || refresh.length === 0) {
    return NextResponse.json({ detail: "Missing refresh token" }, { status: 401 });
  }

  const base = getPublicApiBaseUrl();
  const upstream = await fetch(`${base}/api/v1/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refresh }),
  });

  const data: unknown = await upstream.json().catch(() => ({}));
  if (!upstream.ok) {
    return NextResponse.json(data, { status: upstream.status });
  }

  const response = NextResponse.json(data, { status: upstream.status });
  if (
    typeof data === "object" &&
    data !== null &&
    "refresh_token" in data &&
    typeof (data as { refresh_token: unknown }).refresh_token === "string"
  ) {
    const nextRefresh = (data as { refresh_token: string }).refresh_token;
    response.cookies.set("la_refresh", nextRefresh, {
      httpOnly: true,
      sameSite: "lax",
      path: "/",
      maxAge: 60 * 60 * 24 * 30,
    });
  }
  return response;
}
