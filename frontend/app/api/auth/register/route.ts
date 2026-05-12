import { NextResponse } from "next/server";
import { getPublicApiBaseUrl } from "@/lib/env";

export async function POST(request: Request) {
  const body: unknown = await request.json().catch(() => null);
  if (body == null) {
    return NextResponse.json({ detail: "Invalid JSON body" }, { status: 400 });
  }
  const base = getPublicApiBaseUrl();
  const upstream = await fetch(`${base}/api/v1/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data: unknown = await upstream.json().catch(() => ({}));
  return NextResponse.json(data, { status: upstream.status });
}
