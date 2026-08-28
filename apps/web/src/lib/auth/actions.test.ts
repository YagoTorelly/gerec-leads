import { beforeEach, describe, expect, it, vi } from "vitest";

const { cookieStore, apiRequest, redirect } = vi.hoisted(() => ({
  cookieStore: { get: vi.fn(), set: vi.fn(), delete: vi.fn() },
  apiRequest: vi.fn(),
  redirect: vi.fn(),
}));

vi.mock("next/headers", () => ({ cookies: vi.fn(async () => cookieStore) }));
vi.mock("next/navigation", () => ({ redirect }));
vi.mock("../api/client", () => ({ apiRequest }));

import { loginAction, signOutAction } from "./actions";

describe("ações de sessão", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("propaga cookie HTTP da API e conserva o Max-Age dela", async () => {
    apiRequest.mockResolvedValue(
      new Response(null, {
        headers: { "set-cookie": "gerec_session=opaque; Max-Age=28800; Path=/; HttpOnly" },
      }),
    );
    const form = new FormData();
    form.set("email", "yago@wtg.com");
    form.set("password", "segura");

    await loginAction({}, form);

    expect(cookieStore.set).toHaveBeenCalledWith(
      "gerec_session",
      "opaque",
      expect.objectContaining({ maxAge: 28800, httpOnly: true }),
    );
    expect(redirect).toHaveBeenCalledWith("/dashboard");
  });

  it("apaga cookie e volta ao login quando logout remoto falha", async () => {
    cookieStore.get.mockReturnValue({ value: "opaque" });
    apiRequest.mockRejectedValue(new Error("indisponível"));

    await signOutAction();
    expect(cookieStore.delete).toHaveBeenCalledWith("gerec_session");
    expect(redirect).toHaveBeenCalledWith("/login");
  });
});
