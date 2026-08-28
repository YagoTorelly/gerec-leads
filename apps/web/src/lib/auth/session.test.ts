import { beforeEach, describe, expect, it, vi } from "vitest";

const { cookieStore, apiFetch } = vi.hoisted(() => ({
  cookieStore: { get: vi.fn() },
  apiFetch: vi.fn(),
}));
vi.mock("next/headers", () => ({ cookies: vi.fn(async () => cookieStore) }));
vi.mock("../api/client", () => ({
  ApiRequestError: class ApiRequestError extends Error {
    constructor(
      message: string,
      readonly status: number,
    ) {
      super(message);
    }
  },
  apiFetch,
}));

import { getSessionContext } from "./session";

describe("getSessionContext", () => {
  beforeEach(() => vi.clearAllMocks());

  it("encaminha apenas o cookie de sessão à API", async () => {
    cookieStore.get.mockReturnValue({ value: "opaque" });
    apiFetch.mockResolvedValue({ id: "u1", email: "vendedor@wtg.com", role: "seller" });

    await expect(getSessionContext()).resolves.toMatchObject({
      status: "authenticated",
      sessionToken: "opaque",
      profile: { userId: "u1" },
    });
    expect(apiFetch).toHaveBeenCalledWith(
      "/auth/me",
      expect.objectContaining({ headers: { Cookie: "gerec_session=opaque" } }),
    );
  });
});
