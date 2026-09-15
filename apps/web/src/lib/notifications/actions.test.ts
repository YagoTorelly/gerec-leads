import { beforeEach, describe, expect, it, vi } from "vitest";

const { acknowledgeRequest, getSessionContext, revalidatePath } = vi.hoisted(() => ({
  acknowledgeRequest: vi.fn(),
  getSessionContext: vi.fn(),
  revalidatePath: vi.fn(),
}));

vi.mock("next/cache", () => ({ revalidatePath }));
vi.mock("../api/client", () => {
  class ApiRequestError extends Error {
    constructor(
      message: string,
      readonly status: number,
    ) {
      super(message);
    }
  }
  return { acknowledgeNewLeadNotifications: acknowledgeRequest, ApiRequestError };
});
vi.mock("../auth/session", () => ({ getSessionContext }));

import { acknowledgeNewLeadsAction } from "./actions";

const snapshot = {
  items: [],
  watermark: "2026-09-15T12:01:00.000Z",
  acknowledgementToken: "token-assinado",
  watermarkSequence: 8,
};

describe("ação de confirmação de novos leads", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("encaminha o recibo emitido pela API somente para a sessão do vendedor", async () => {
    getSessionContext.mockResolvedValue({
      status: "authenticated",
      sessionToken: "sessao-segura",
      profile: { id: "seller-1", userId: "seller-1", fullName: "Sandra", email: "sandra@example.test", role: "seller" },
    });
    acknowledgeRequest.mockResolvedValue({ watermark: snapshot.watermark });

    await expect(acknowledgeNewLeadsAction(snapshot)).resolves.toEqual({
      ok: true,
      message: "Novos leads confirmados.",
    });
    expect(acknowledgeRequest).toHaveBeenCalledWith(snapshot, "sessao-segura");
    expect(revalidatePath).toHaveBeenCalledWith("/dashboard");
  });

  it("não envia confirmação quando a sessão não é de vendedor", async () => {
    getSessionContext.mockResolvedValue({
      status: "authenticated",
      sessionToken: "sessao-admin",
      profile: { id: "admin-1", userId: "admin-1", fullName: "Yago", email: "yago@example.test", role: "admin" },
    });

    await expect(acknowledgeNewLeadsAction(snapshot)).resolves.toEqual({
      ok: false,
      message: "Sessão expirada ou sem permissão.",
    });
    expect(acknowledgeRequest).not.toHaveBeenCalled();
  });

  it("converte indisponibilidade da sessão em erro seguro da janela", async () => {
    getSessionContext.mockRejectedValue(new Error("falha interna"));

    await expect(acknowledgeNewLeadsAction(snapshot)).resolves.toEqual({
      ok: false,
      message: "Não foi possível confirmar os novos leads.",
    });
    expect(acknowledgeRequest).not.toHaveBeenCalled();
  });
});
