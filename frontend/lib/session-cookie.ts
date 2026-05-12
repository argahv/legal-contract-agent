export const SESSION_COOKIE_NAME = "la_session";

function sessionCookieMaxAgeSeconds(): number {
  return 60 * 60 * 24 * 7;
}

export function setSessionMarkerCookie(): void {
  if (typeof document === "undefined") return;
  const secure = globalThis.location?.protocol === "https:" ? "; Secure" : "";
  const maxAge = sessionCookieMaxAgeSeconds();
  document.cookie = `${SESSION_COOKIE_NAME}=1; Path=/; Max-Age=${maxAge}; SameSite=Lax${secure}`;
}

export function clearSessionMarkerCookie(): void {
  if (typeof document === "undefined") return;
  document.cookie = `${SESSION_COOKIE_NAME}=; Path=/; Max-Age=0`;
}
