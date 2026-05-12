import { NextResponse } from "next/server";
import { getPublicApiBaseUrl } from "@/lib/env";

export async function POST(request: Request) {
  const body: unknown = await request.json().catch(() => null);
  if (body == null) {
    return NextResponse.json({ detail: "Invalid JSON body" }, { status: 400 });
  }
  const base = getPublicApiBaseUrl();
  const upstream = await fetch(`${base}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  const data: unknown = await upstream.json().catch(() => ({}));
  if (!upstream.ok) {
    return NextResponse.json(data, { status: upstream.status });
  }

  let refresh: string | null = null;
  if (typeof data === "object" && data !== null) {
    const d = data as Record<string, unknown>;
    const nested = d.tokens;
    if (
      typeof nested === "object" &&
      nested !== null &&
      typeof (nested as { refresh_token?: unknown }).refresh_token === "string"
    ) {
      refresh = (nested as { refresh_token: string }).refresh_token;
    } else if (typeof d.refresh_token === "string") {
      refresh = d.refresh_token;
    }
  }

  const response = NextResponse.json(data, { status: upstream.status });
  if (refresh != null && refresh.length > 0) {
    response.cookies.set("la_refresh", refresh, {
      httpOnly: true,
      sameSite: "lax",
      path: "/",
      maxAge: 60 * 60 * 24 * 30,
    });
  }
  return response;
}
