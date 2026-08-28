import { afterEach, describe, expect, it, vi } from "vitest";

import { apiFetch } from "./client";

describe("apiFetch", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
  });

  it("chama a API Python pela URL pública e inclui cookies", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "https://api.wtg.example/");
    const request = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify({ status: "ok" }), { status: 200 }));
    vi.stubGlobal("fetch", request);

    await expect(apiFetch<{ status: string }>("/health")).resolves.toEqual({ status: "ok" });
    expect(request).toHaveBeenCalledWith(
      "https://api.wtg.example/health",
      expect.objectContaining({ credentials: "include" }),
    );
  });

  it("preserva status e mensagem de validação da API", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "https://api.wtg.example");
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          new Response(JSON.stringify({ detail: "Lead inválido" }), { status: 422 }),
        ),
    );

    await expect(apiFetch("/api/leads/inválido/attempts")).rejects.toMatchObject({
      status: 422,
      message: "Lead inválido",
    });
  });

  it.each([
    [401, "Sessão expirada. Entre novamente."],
    [403, "Você não tem permissão para esta ação."],
  ])("traduz HTTP %i sem expor corpo da API", async (status, message) => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "https://api.wtg.example");
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(null, { status })));

    await expect(apiFetch("/api/dashboard")).rejects.toMatchObject({ status, message });
  });
});
