import { useAuthStore } from "@/lib/store/auth";
import type { ApiErrorBody } from "@/lib/types";
import { getPublicApiBaseUrl } from "@/lib/env";
import { clearSessionMarkerCookie } from "@/lib/session-cookie";

const SESSION_EXPIRED_USER_MESSAGE =
  "Session expired, please log in again";

/** Path only (handles absolute API URLs vs relative `/api/v1/...`). */
function getRequestPath(pathOrUrl: string): string {
  if (
    pathOrUrl.startsWith("http://") ||
    pathOrUrl.startsWith("https://")
  ) {
    try {
      return new URL(pathOrUrl).pathname;
    } catch {
      return pathOrUrl;
    }
  }
  const noQuery = pathOrUrl.split("?")[0] ?? pathOrUrl;
  return noQuery.split("#")[0] ?? noQuery;
}

/** Wrong credentials on login/register stay on the page — do not wipe session here. */
function isCredentialsAuthRequest(pathOrUrl: string): boolean {
  const path = getRequestPath(pathOrUrl);
  return (
    path === "/api/v1/auth/login" || path === "/api/v1/auth/register"
  );
}

export class ApiError extends Error {
  readonly status: number;
  readonly body: unknown;

  constructor(message: string, status: number, body: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

export function getApiBaseUrl(): string {
  return getPublicApiBaseUrl();
}

export const API_BASE_URL = getApiBaseUrl();

function createRequestId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `req_${Date.now().toString(36)}_${Math.random().toString(36).slice(2)}`;
}

function normalizeErrorMessage(status: number, parsed: unknown): string {
  if (
    typeof parsed === "object" &&
    parsed !== null &&
    "detail" in parsed &&
    typeof (parsed as ApiErrorBody).detail === "string"
  ) {
    return (parsed as ApiErrorBody).detail;
  }
  if (
    typeof parsed === "object" &&
    parsed !== null &&
    "message" in parsed &&
    typeof (parsed as { message: string }).message === "string"
  ) {
    return (parsed as { message: string }).message;
  }
  return `Request failed with status ${status}`;
}

export type ApiFetchOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
  skipAuth?: boolean;
};

export async function apiFetch<T>(
  path: string,
  options: ApiFetchOptions = {},
): Promise<T> {
  const { body, skipAuth, headers: initHeaders, ...rest } = options;
  const url = path.startsWith("http") ? path : `${API_BASE_URL}${path}`;

  const headers = new Headers(initHeaders);
  headers.set("X-Request-Id", createRequestId());

  if (body != null && !(body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  if (skipAuth !== true) {
    const token = useAuthStore.getState().accessToken;
    if (token != null && token.length > 0) {
      headers.set("Authorization", `Bearer ${token}`);
    }
  }

  const response = await fetch(url, {
    ...rest,
    headers,
    body:
      body instanceof FormData || typeof body === "string" || body == null
        ? (body as BodyInit | null | undefined)
        : JSON.stringify(body),
  });

  const contentType = response.headers.get("content-type") ?? "";
  const isJson = contentType.includes("application/json");
  let parsed: unknown = null;

  if (isJson) {
    try {
      parsed = await response.json();
    } catch {
      parsed = null;
    }
  } else if (response.ok) {
    const text = await response.text();
    parsed = text.length > 0 ? text : null;
  }

  if (
    !response.ok &&
    response.status === 401 &&
    !(skipAuth === true && isCredentialsAuthRequest(url))
  ) {
    useAuthStore.getState().clearSession();
    if (typeof window !== "undefined") {
      clearSessionMarkerCookie();
      window.location.assign("/login");
    }
    throw new ApiError(
      SESSION_EXPIRED_USER_MESSAGE,
      response.status,
      parsed,
    );
  }

  if (!response.ok) {
    throw new ApiError(
      normalizeErrorMessage(response.status, parsed),
      response.status,
      parsed,
    );
  }

  return parsed as T;
}
