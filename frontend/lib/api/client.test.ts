import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiFetch } from "@/lib/api/client";

const authMock = vi.hoisted(() => {
  const clearSession = vi.fn();
  const getState = vi.fn(() => ({
    accessToken: "token-123" as string | null,
    clearSession,
  }));
  return { getState, clearSession };
});

vi.mock("@/lib/store/auth", () => ({
  useAuthStore: {
    getState: authMock.getState,
  },
}));

describe("apiFetch", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("injects authorization and propagates request identifiers", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => ({ ok: true }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await apiFetch<{ ok: boolean }>("/api/v1/ping");

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const init = fetchMock.mock.calls[0]?.[1] as RequestInit | undefined;
    expect(init).toBeDefined();
    const headers = init?.headers as Headers;
    expect(headers.get("Authorization")).toBe("Bearer token-123");
    expect(headers.get("X-Request-Id")).toBeTruthy();
  });

  it("throws ApiError with backend detail messaging", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 422,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => ({ detail: "Invalid payload" }),
      }),
    );

    try {
      await apiFetch("/api/v1/contracts");
      throw new Error("expected ApiError");
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError);
      if (error instanceof ApiError) {
        expect(error.message).toBe("Invalid payload");
        expect(error.status).toBe(422);
      }
    }
  });

  it("clears session on 401 and surfaces session-expired messaging", async () => {
    authMock.clearSession.mockClear();

    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => ({ detail: "Invalid access token" }),
      }),
    );

    try {
      await apiFetch("/api/v1/contracts");
      throw new Error("expected ApiError");
    } catch (error) {
      expect(authMock.clearSession).toHaveBeenCalled();
      expect(error).toBeInstanceOf(ApiError);
      if (error instanceof ApiError) {
        expect(error.message).toBe("Session expired, please log in again");
        expect(error.status).toBe(401);
      }
    } finally {
      consoleSpy.mockRestore();
    }
  });

  it("does not clear session when login fails with skipAuth 401", async () => {
    authMock.clearSession.mockClear();

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => ({ detail: "Incorrect email or password" }),
      }),
    );

    try {
      await apiFetch("/api/v1/auth/login", {
        method: "POST",
        body: {},
        skipAuth: true,
      });
      throw new Error("expected ApiError");
    } catch (error) {
      expect(authMock.clearSession).not.toHaveBeenCalled();
      expect(error).toBeInstanceOf(ApiError);
      if (error instanceof ApiError) {
        expect(error.message).toBe("Incorrect email or password");
      }
    }
  });
});
