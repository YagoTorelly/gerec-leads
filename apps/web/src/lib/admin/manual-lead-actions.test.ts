import { beforeEach, describe, expect, it, vi } from "vitest";

const cache = vi.hoisted(() => ({ revalidatePath: vi.fn() }));

vi.mock("next/cache", () => cache);
vi.mock("../auth/session", () => ({ getSessionContext: vi.fn() }));
vi.mock("../api/client", () => {
  class ApiRequestError extends Error {
    constructor(
      message: string,
      readonly status: number,
    ) {
      super(message);
    }
  }
  return { ApiRequestError, createManualLead: vi.fn() };
});

import { createManualLead } from "../api/client";
import { getSessionContext } from "../auth/session";
import { createManualLeadAction } from "./manual-lead-actions";

const input = {
  name: "Contato manual",
  email: "contato@example.com",
  phone: "+55 11 99999-1234",
  campaign: "Campanha",
  source: "Meta Ads",
};

const createdLead = {
  leadId: "lead-1",
  manualQueueLeadId: "MAN-123",
  assigneeId: "seller-1",
  assignedAt: "2026-09-22T13:00:00Z",
  commercialStatus: "undefined" as const,
  source: "manual" as const,
};

describe("ação administrativa de cadastro manual", () => {
  beforeEach(() => vi.clearAllMocks());

  it("rejeita os campos obrigatórios vazios antes de consultar a sessão", async () => {
    await expect(createManualLeadAction({ ...input, phone: "   " })).resolves.toEqual({
      ok: false,
      message: "Preencha nome, e-mail e telefone para cadastrar o lead.",
    });
    expect(getSessionContext).not.toHaveBeenCalled();
    expect(createManualLead).not.toHaveBeenCalled();
  });

  it("nega a criação para vendedor sem enviar dados à API administrativa", async () => {
    vi.mocked(getSessionContext).mockResolvedValue({
      status: "authenticated",
      sessionToken: "sessao-seller",
      profile: {
        id: "seller-1",
        userId: "seller-1",
        fullName: "Sandra",
        email: "sandra@example.com",
        role: "seller",
      },
    });

    await expect(createManualLeadAction(input)).resolves.toEqual({
      ok: false,
      message: "Você não tem permissão para cadastrar leads.",
    });
    expect(createManualLead).not.toHaveBeenCalled();
  });

  it("cria o lead com chave idempotente e revalida as visões afetadas", async () => {
    vi.mocked(getSessionContext).mockResolvedValue({
      status: "authenticated",
      sessionToken: "sessao-admin",
      profile: {
        id: "admin-1",
        userId: "admin-1",
        fullName: "Yago",
        email: "yago@example.com",
        role: "admin",
      },
    });
    vi.mocked(createManualLead).mockResolvedValue(createdLead);

    const result = await createManualLeadAction({
      ...input,
      campaign: "  Campanha  ",
      source: "   ",
    });

    expect(result).toEqual({
      ok: true,
      message: "Lead cadastrado e distribuído.",
      lead: createdLead,
    });
    expect(createManualLead).toHaveBeenCalledWith(
      { ...input, campaign: "Campanha", source: undefined },
      expect.stringMatching(/^[0-9a-f-]{36}$/),
      "sessao-admin",
    );
    expect(cache.revalidatePath.mock.calls.map(([path]) => path)).toEqual([
      "/usuarios",
      "/dashboard",
      "/fila",
      "/notificacoes",
    ]);
  });

  it("informa quando o lead fica aguardando um vendedor ativo", async () => {
    vi.mocked(getSessionContext).mockResolvedValue({
      status: "authenticated",
      sessionToken: "sessao-admin",
      profile: {
        id: "admin-1",
        userId: "admin-1",
        fullName: "Yago",
        email: "yago@example.com",
        role: "admin",
      },
    });
    vi.mocked(createManualLead).mockResolvedValue({
      ...createdLead,
      assigneeId: null,
      assignedAt: null,
    });

    await expect(createManualLeadAction(input)).resolves.toMatchObject({
      ok: true,
      message: "Lead cadastrado e aguardando um vendedor ativo.",
    });
  });

  it("converte erro da API em mensagem segura e recuperável", async () => {
    vi.mocked(getSessionContext).mockResolvedValue({
      status: "authenticated",
      sessionToken: "sessao-admin",
      profile: {
        id: "admin-1",
        userId: "admin-1",
        fullName: "Yago",
        email: "yago@example.com",
        role: "admin",
      },
    });
    vi.mocked(createManualLead).mockRejectedValue(new Error("segredo interno"));

    await expect(createManualLeadAction(input)).resolves.toEqual({
      ok: false,
      message: "Não foi possível cadastrar o lead. Tente novamente.",
    });
  });
});
