import { apiFetch, getApiBaseUrl } from "./client";
import type { AuthTokens, Role, User } from "@/lib/types";

/** FastAPI `TokenPair` wire shape. */
interface TokenPairWire {
  access_token: string;
  refresh_token: string;
  token_type?: string;
}

/** FastAPI `UserRead` — no full_name on user row today. */
interface UserReadWire {
  id: string;
  email: string;
  role: string;
}

/** FastAPI `AuthBundle`: `{ user, tokens }`. */
interface AuthBundleWire {
  user: UserReadWire;
  tokens: TokenPairWire;
}

/** Legacy / flat shape some proxies might return. */
interface FlatAuthWire {
  access_token: string;
  refresh_token: string;
  token_type?: string;
  expires_in?: number;
  user: UserReadWire;
}

function mapBackendRole(r: string): Role {
  const key = r.trim().toLowerCase().replace(/-/g, "_");
  const m: Record<string, Role> = {
    super_admin: "SUPER_ADMIN",
    admin: "ADMIN",
    legal_reviewer: "LEGAL_REVIEWER",
    general_counsel: "GENERAL_COUNSEL",
  };
  return m[key] ?? "LEGAL_REVIEWER";
}

function userFromWire(u: UserReadWire, displayName?: string): User {
  const local = u.email.split("@")[0] ?? "user";
  const name =
    displayName?.trim() ||
    (u as { full_name?: string }).full_name?.trim() ||
    local;
  return {
    id: String(u.id),
    email: u.email,
    full_name: name,
    role: mapBackendRole(u.role),
    is_active: true,
    created_at: new Date().toISOString(),
  };
}

/**
 * Normalize auth JSON from FastAPI (`{ user, tokens }`) or a flat legacy shape.
 */
export function parseAuthResponse(
  data: unknown,
  opts?: { displayName?: string },
): { tokens: AuthTokens; user: User } {
  if (typeof data !== "object" || data === null) {
    throw new Error("Invalid auth response");
  }
  const o = data as Record<string, unknown>;

  let access: string;
  let refresh: string;
  let tokenType = "bearer";
  let expiresIn = 0;

  const nested = o.tokens;
  if (typeof nested === "object" && nested !== null) {
    const t = nested as TokenPairWire;
    if (typeof t.access_token !== "string" || typeof t.refresh_token !== "string") {
      throw new Error("Invalid token pair in auth response");
    }
    access = t.access_token;
    refresh = t.refresh_token;
    if (typeof t.token_type === "string") tokenType = t.token_type;
  } else if (
    typeof o.access_token === "string" &&
    typeof o.refresh_token === "string"
  ) {
    access = o.access_token;
    refresh = o.refresh_token;
    if (typeof o.token_type === "string") tokenType = o.token_type;
    if (typeof o.expires_in === "number") expiresIn = o.expires_in;
  } else {
    throw new Error("Invalid auth response: expected user + tokens or flat tokens");
  }

  const userRaw = o.user;
  if (typeof userRaw !== "object" || userRaw === null) {
    throw new Error("Missing user in auth response");
  }
  const u = userRaw as UserReadWire;
  if (u.email == null || u.role == null) {
    throw new Error("Invalid user in auth response");
  }

  const user = userFromWire(
    { id: String(u.id), email: String(u.email), role: String(u.role) },
    opts?.displayName,
  );

  return {
    tokens: {
      access_token: access,
      refresh_token: refresh,
      token_type: tokenType,
      expires_in: expiresIn,
    },
    user,
  };
}

export async function loginWithBackend(
  email: string,
  password: string,
): Promise<{ tokens: AuthTokens; user: User }> {
  const res = await apiFetch<AuthBundleWire | FlatAuthWire>(
    "/api/v1/auth/login",
    {
      method: "POST",
      body: { email, password },
      skipAuth: true,
    },
  );
  return parseAuthResponse(res);
}

/** Login via Next.js API route (sets httpOnly refresh cookie when returned). */
export async function loginViaNextRoute(
  email: string,
  password: string,
): Promise<{ tokens: AuthTokens; user: User }> {
  const res = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data: unknown = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail =
      typeof data === "object" &&
      data !== null &&
      "detail" in data &&
      typeof (data as { detail: unknown }).detail === "string"
        ? (data as { detail: string }).detail
        : "Login failed";
    throw new Error(detail);
  }
  return parseAuthResponse(data);
}

export async function registerAccount(input: {
  email: string;
  password: string;
  full_name: string;
}): Promise<{ tokens: AuthTokens; user: User }> {
  const res = await apiFetch<AuthBundleWire | FlatAuthWire>(
    "/api/v1/auth/register",
    {
      method: "POST",
      body: input,
      skipAuth: true,
    },
  );
  return parseAuthResponse(res, { displayName: input.full_name });
}

export async function fetchCurrentUser(): Promise<User> {
  const me = await apiFetch<UserReadWire>("/api/v1/auth/me", { method: "GET" });
  return userFromWire(me);
}

export async function refreshSession(
  refreshToken: string,
): Promise<AuthTokens> {
  return apiFetch<AuthTokens>("/api/v1/auth/refresh", {
    method: "POST",
    body: { refresh_token: refreshToken },
    skipAuth: true,
  });
}

export function getBackendAuthUrl(): string {
  return `${getApiBaseUrl()}/api/v1/auth`;
}
