import { beforeEach, describe, expect, it, vi } from "vitest";

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
  return { ApiRequestError, transferLeadOwnership: vi.fn() };
});

import { getSessionContext } from "../auth/session";
import { transferLeadOwnership } from "../api/client";
import { initialTransferActionState, transferLeadOwnershipAction } from "./transfer-actions";

function formData(values: Record<string, string>): FormData {
  const form = new FormData();
  Object.entries(values).forEach(([key, value]) => form.set(key, value));
  return form;
}

describe("ação de transferência de propriedade", () => {
  beforeEach(() => vi.clearAllMocks());

  it("converte falha inesperada ao carregar sessão em erro do formulário", async () => {
    vi.mocked(getSessionContext).mockRejectedValue(new Error("API indisponível"));

    await expect(
      transferLeadOwnershipAction(
        initialTransferActionState,
        formData({ leadId: "lead-1", sellerId: "seller-2", reason: "Cobertura" }),
      ),
    ).resolves.toEqual({
      status: "error",
      message: "Não foi possível transferir a propriedade.",
    });
  });

  it("envia confirmação explícita ao backend", async () => {
    vi.mocked(getSessionContext).mockResolvedValue({
      status: "authenticated",
      sessionToken: "sessao",
      profile: {
        id: "admin-1",
        userId: "admin-1",
        fullName: "Yago",
        email: "yago@example.com",
        role: "admin",
      },
    });
    vi.mocked(transferLeadOwnership).mockResolvedValue({
      leadId: "lead-1",
      sellerId: "seller-2",
      status: "assigned",
    });

    const result = await transferLeadOwnershipAction(
      initialTransferActionState,
      formData({ leadId: "lead-1", sellerId: "seller-2", reason: "Cobertura" }),
    );

    expect(result.status).toBe("success");
    expect(transferLeadOwnership).toHaveBeenCalledWith(
      "lead-1",
      "seller-2",
      "Cobertura",
      expect.any(String),
      "sessao",
    );
  });
});
