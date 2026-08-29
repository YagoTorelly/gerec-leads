import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("next/cache", () => ({ revalidatePath: vi.fn() }));
vi.mock("../auth/session", () => ({ getSessionContext: vi.fn() }));
vi.mock("../api/client", () => {
  class ApiRequestError extends Error {
    constructor(message: string, readonly status: number) {
      super(message);
    }
  }
  return { ApiRequestError, getLeadTreatments: vi.fn(), submitLeadTreatment: vi.fn() };
});

import { revalidatePath } from "next/cache";

import { ApiRequestError, submitLeadTreatment } from "../api/client";
import { getSessionContext } from "../auth/session";
import { initialTreatmentActionState, submitLeadTreatmentAction } from "./treatment-actions";

const authenticatedSession = {
  status: "authenticated" as const,
  sessionToken: "sessao-segura",
  profile: { id: "seller-1", userId: "seller-1", fullName: "Jessica", email: "jessica@wtgseguros.com.br", role: "seller" as const },
};

function formData(values: Record<string, string>): FormData {
  const form = new FormData();
  Object.entries(values).forEach(([key, value]) => form.set(key, value));
  return form;
}

describe("ação de tratativa", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getSessionContext).mockResolvedValue(authenticatedSession);
  });

  it("mantém o erro 422 legível para o formulário", async () => {
    vi.mocked(submitLeadTreatment).mockRejectedValue(new ApiRequestError("Revise os dados informados e tente novamente.", 422));

    await expect(submitLeadTreatmentAction(initialTreatmentActionState, formData({
      leadId: "lead-1",
      comment: "Contato realizado por telefone.",
      commercialStatus: "negotiation",
      idempotencyKey: "key-1",
    }))).resolves.toEqual({
      status: "error",
      message: "Revise os dados informados e tente novamente.",
      submission: null,
    });
  });

  it("envia o status atual e atualiza a consulta após sucesso", async () => {
    vi.mocked(submitLeadTreatment).mockResolvedValue({
      leadId: "lead-1",
      treatmentId: "treatment-1",
      status: "created",
      commercialStatus: "won",
      isDisqualified: true,
      commentCount: 3,
      reminderAt: null,
      dueAt: null,
    });

    const result = await submitLeadTreatmentAction(initialTreatmentActionState, formData({
      leadId: "lead-1",
      comment: "Seguro contratado e escopo confirmado.",
      commercialStatus: "won",
      isDisqualified: "on",
      idempotencyKey: "key-2",
    }));

    expect(submitLeadTreatment).toHaveBeenCalledWith("lead-1", {
      comment: "Seguro contratado e escopo confirmado.",
      commercialStatus: "won",
      isDisqualified: true,
      idempotencyKey: "key-2",
    }, "sessao-segura");
    expect(revalidatePath).toHaveBeenCalledWith("/dashboard");
    expect(result).toMatchObject({ status: "success", submission: { commentCount: 3 } });
  });
});
