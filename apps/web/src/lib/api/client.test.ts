import { afterEach, describe, expect, it, vi } from "vitest";

import {
  apiFetch,
  createManagedUser,
  getManagedUsers,
  getLeadTreatments,
  resetManagedUserPassword,
  setManagedUserAvailability,
  submitLeadTreatment,
} from "./client";

describe("cliente HTTP operacional", () => {
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

  it("não devolve detalhes arbitrários de validação", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "https://api.wtg.example");
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(new Response(JSON.stringify({ detail: "Lead inválido" }), { status: 422 })),
    );

    await expect(apiFetch("/api/leads/inválido/attempts")).rejects.toMatchObject({
      status: 422,
      message: "Revise os dados informados e tente novamente.",
    });
  });

  it.each([
    [401, "Sessão expirada. Entre novamente."],
    [403, "Você não tem permissão para esta ação."],
    [409, "A operação conflita com o estado atual. Atualize os dados e tente novamente."],
    [422, "Revise os dados informados e tente novamente."],
  ])("traduz HTTP %i para erro legível", async (status, message) => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "https://api.wtg.example");
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(null, { status })));

    await expect(apiFetch("/api/dashboard")).rejects.toMatchObject({ status, message });
  });

  it.each([
    [401, "Unauthorized", "Sessão expirada. Entre novamente."],
    [403, "Forbidden", "Você não tem permissão para esta ação."],
    [409, "Email already registered", "A operação conflita com o estado atual. Atualize os dados e tente novamente."],
    [422, "Invalid object id", "Revise os dados informados e tente novamente."],
  ])("não expõe detalhe técnico HTTP %i", async (status, detail, message) => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "https://api.wtg.example");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail }), { status })),
    );

    await expect(apiFetch("/api/dashboard")).rejects.toMatchObject({ status, message });
  });

  it.each([
    [409, "queue changed concurrently", "A operação conflita com o estado atual. Atualize os dados e tente novamente."],
    [409, "retry user creation", "A operação conflita com o estado atual. Atualize os dados e tente novamente."],
    [422, "password is required", "Revise os dados informados e tente novamente."],
    [422, "paused must be a boolean", "Revise os dados informados e tente novamente."],
    [422, "MONGODB_URI=mongodb://internal-secret", "Revise os dados informados e tente novamente."],
  ])("nunca expõe detalhe operacional ou segredo HTTP %i", async (status, detail, message) => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "https://api.wtg.example");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail }), { status })),
    );

    await expect(apiFetch("/api/dashboard")).rejects.toMatchObject({ status, message });
  });

  it("normaliza a listagem persistida de usuários para o contrato público", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "https://api.wtg.example");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            items: [
              {
                id: "seller-1",
                fullName: "Sandra",
                emailNormalized: "sandracristina@wtgseguros.com.br",
                role: "seller",
                active: true,
                paused: false,
                passwordHash: "never-expose",
                tokenHash: "never-expose",
              },
            ],
            page: 1,
            pageSize: 50,
            total: 1,
          }),
          { status: 200 },
        ),
      ),
    );

    await expect(getManagedUsers("sessao")).resolves.toEqual({
      items: [
        {
          id: "seller-1",
          fullName: "Sandra",
          email: "sandracristina@wtgseguros.com.br",
          role: "seller",
          active: true,
          paused: false,
        },
      ],
      page: 1,
      pageSize: 50,
      total: 1,
    });
  });

  it("serializa criação de usuário e não devolve a senha", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "https://api.wtg.example");
    const request = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          id: "seller-1",
          fullName: "Nova Vendedora",
          email: "nova@wtgseguros.com.br",
          role: "seller",
          active: true,
          paused: false,
        }),
        { status: 201 },
      ),
    );
    vi.stubGlobal("fetch", request);

    const user = await createManagedUser(
      {
        fullName: "Nova Vendedora",
        email: "nova@wtgseguros.com.br",
        role: "seller",
        password: "senha inicial",
      },
      "sessao",
    );

    expect(user).toEqual({
      id: "seller-1",
      fullName: "Nova Vendedora",
      email: "nova@wtgseguros.com.br",
      role: "seller",
      active: true,
      paused: false,
    });
    expect(user).not.toHaveProperty("password");
    expect(request).toHaveBeenCalledWith(
      "https://api.wtg.example/api/admin/users",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          fullName: "Nova Vendedora",
          email: "nova@wtgseguros.com.br",
          role: "seller",
          password: "senha inicial",
        }),
        headers: expect.objectContaining({
          "Content-Type": "application/json",
          Cookie: "gerec_session=sessao",
        }),
      }),
    );
  });

  it("envia disponibilidade e redefinição de senha sem expor a senha na resposta", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "https://api.wtg.example");
    const response = {
      id: "seller-1",
      fullName: "Nova Vendedora",
      email: "nova@wtgseguros.com.br",
      role: "seller" as const,
      active: true,
      paused: true,
    };
    const request = vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify(response), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(response), { status: 200 }));
    vi.stubGlobal("fetch", request);

    await expect(setManagedUserAvailability("seller-1", true, "sessao")).resolves.toEqual(response);
    await expect(resetManagedUserPassword("seller-1", "nova senha", "sessao")).resolves.toEqual(
      response,
    );
    expect(request).toHaveBeenNthCalledWith(
      1,
      "https://api.wtg.example/api/admin/users/seller-1/availability",
      expect.objectContaining({ body: JSON.stringify({ paused: true }) }),
    );
    expect(request).toHaveBeenNthCalledWith(
      2,
      "https://api.wtg.example/api/admin/users/seller-1/password",
      expect.objectContaining({ body: JSON.stringify({ password: "nova senha" }) }),
    );
  });

  it("serializa tratativa e consulta histórico sem decidir o estado no navegador", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "https://api.wtg.example");
    const request = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            leadId: "lead-1",
            treatmentId: "treatment-1",
            status: "ok",
            commercialStatus: "negotiation",
            isDisqualified: false,
            commentCount: 2,
          }),
          { status: 201 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ items: [], page: 1, pageSize: 50, total: 0 }), {
          status: 200,
        }),
      );
    vi.stubGlobal("fetch", request);

    await expect(
      submitLeadTreatment(
        "lead-1",
        {
          comment: "Cliente pediu uma nova cotação.",
          commercialStatus: "negotiation",
          isDisqualified: false,
          idempotencyKey: "treatment-1",
        },
        "sessao",
      ),
    ).resolves.toMatchObject({ commentCount: 2, commercialStatus: "negotiation" });
    await expect(getLeadTreatments("lead-1", "sessao")).resolves.toEqual({
      items: [],
      page: 1,
      pageSize: 50,
      total: 0,
    });
    expect(request).toHaveBeenNthCalledWith(
      1,
      "https://api.wtg.example/api/leads/lead-1/treatments",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          comment: "Cliente pediu uma nova cotação.",
          commercialStatus: "negotiation",
          isDisqualified: false,
          idempotencyKey: "treatment-1",
        }),
      }),
    );
    expect(request).toHaveBeenNthCalledWith(
      2,
      "https://api.wtg.example/api/leads/lead-1/treatments?page=1&limit=50",
      expect.objectContaining({ headers: expect.objectContaining({ Cookie: "gerec_session=sessao" }) }),
    );
  });
});
