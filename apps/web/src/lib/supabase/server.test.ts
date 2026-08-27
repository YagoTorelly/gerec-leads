import { beforeEach, describe, expect, it, vi } from "vitest";

const { cookiesMock } = vi.hoisted(() => ({ cookiesMock: vi.fn() }));

vi.mock("next/headers", () => ({
  cookies: cookiesMock,
}));

import { ACCESS_TOKEN_COOKIE, createServerSupabaseClient } from "./server";

describe("createServerSupabaseClient", () => {
  beforeEach(() => {
    cookiesMock.mockReset();
    vi.restoreAllMocks();
  });

  it("nao consulta o auth quando o cookie de acesso nao existe", async () => {
    cookiesMock.mockResolvedValue({
      get: vi.fn().mockReturnValue(undefined),
    });
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    const client = await createServerSupabaseClient({
      runtime: { url: "http://127.0.0.1:54321", publishableKey: "public-key" },
    });

    expect(client.auth.getAccessToken()).toBeNull();
    await expect(client.auth.getUser()).resolves.toBeNull();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("busca o usuario autenticado e o perfil correspondente", async () => {
    cookiesMock.mockResolvedValue({
      get: vi
        .fn()
        .mockImplementation((name: string) =>
          name === ACCESS_TOKEN_COOKIE ? { value: "token-123" } : undefined,
        ),
    });
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ id: "user-1", email: "admin@wtg.com" }), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify([
            {
              user_id: "user-1",
              full_name: "Administrador WTG",
              email: "admin@wtg.com",
              role: "admin",
            },
          ]),
          { status: 200 },
        ),
      );
    vi.stubGlobal("fetch", fetchMock);

    const client = await createServerSupabaseClient({
      runtime: { url: "http://127.0.0.1:54321", publishableKey: "public-key" },
    });

    await expect(client.auth.getUser()).resolves.toEqual({
      id: "user-1",
      email: "admin@wtg.com",
    });
    await expect(client.profiles.getByUserId("user-1")).resolves.toEqual({
      user_id: "user-1",
      full_name: "Administrador WTG",
      email: "admin@wtg.com",
      role: "admin",
    });

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      "http://127.0.0.1:54321/auth/v1/user",
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: "Bearer token-123",
          apikey: "public-key",
        }),
      }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      "http://127.0.0.1:54321/rest/v1/profiles?user_id=eq.user-1&select=user_id,full_name,email,role&limit=1",
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: "Bearer token-123",
          apikey: "public-key",
        }),
      }),
    );
  });
});
