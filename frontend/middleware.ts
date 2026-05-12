import { NextResponse, type NextRequest } from "next/server";
import { SESSION_COOKIE_NAME } from "@/lib/session-cookie";

export function middleware(request: NextRequest) {
  const marker = request.cookies.get(SESSION_COOKIE_NAME);
  if (marker?.value == null || marker.value.length === 0) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    url.searchParams.set("from", request.nextUrl.pathname);
    return NextResponse.redirect(url);
  }
  return NextResponse.next();
}

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/contracts/:path*",
    "/approvals/:path*",
    "/playbook/:path*",
    "/audit/:path*",
  ],
};
