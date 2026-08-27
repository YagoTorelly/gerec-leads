import { describe, expect, it, vi } from "vitest";

import { checkSupabaseHealth, type HealthRequest } from "./check-supabase";

describe("checkSupabaseHealth", () => {
  it("informa conexão quando o Auth local responde", async () => {
    const request = vi.fn<HealthRequest>().mockResolvedValue(new Response(null, { status: 200 }));

    await expect(
      checkSupabaseHealth({ url: "http://127.0.0.1:54321", publishableKey: "public-key" }, request),
    ).resolves.toEqual({ status: "connected", message: "Supabase local conectado" });

    expect(request).toHaveBeenCalledWith(
      "http://127.0.0.1:54321/auth/v1/health",
      expect.objectContaining({
        cache: "no-store",
        headers: { apikey: "public-key" },
      }),
    );
  });

  it("não tenta conectar sem configuração pública", async () => {
    const request = vi.fn<HealthRequest>();

    await expect(
      checkSupabaseHealth({ url: undefined, publishableKey: undefined }, request),
    ).resolves.toEqual({
      status: "not_configured",
      message: "Supabase local ainda não configurado",
    });
    expect(request).not.toHaveBeenCalled();
  });

  it("degrada de forma segura quando o serviço está indisponível", async () => {
    const request = vi.fn<HealthRequest>().mockRejectedValue(new Error("connection refused"));

    await expect(
      checkSupabaseHealth({ url: "http://127.0.0.1:54321", publishableKey: "public-key" }, request),
    ).resolves.toEqual({
      status: "unavailable",
      message: "Supabase local indisponível",
    });
  });
});
