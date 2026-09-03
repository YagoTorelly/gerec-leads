"use server";

import { randomUUID } from "node:crypto";

import { ApiRequestError, transferLeadOwnership } from "../api/client";
import { getSessionContext } from "../auth/session";

import type { TransferActionState } from "./transfer-state";

export type { TransferActionState } from "./transfer-state";

export async function transferLeadOwnershipAction(
  _previous: TransferActionState,
  formData: FormData,
): Promise<TransferActionState> {
  const leadId = String(formData.get("leadId") ?? "").trim();
  const sellerId = String(formData.get("sellerId") ?? "").trim();
  const reason = String(formData.get("reason") ?? "").trim();
  if (!leadId || !sellerId || reason.length < 1) {
    return { status: "error", message: "Selecione um vendedor e informe o motivo." };
  }
  try {
    const session = await getSessionContext();
    if (session.status !== "authenticated" || session.profile.role !== "admin") {
      return { status: "error", message: "Sessão expirada ou sem permissão." };
    }
    await transferLeadOwnership(leadId, sellerId, reason, randomUUID(), session.sessionToken);
    return { status: "success", message: "Propriedade transferida." };
  } catch (error) {
    return {
      status: "error",
      message:
        error instanceof ApiRequestError
          ? error.message
          : "Não foi possível transferir a propriedade.",
    };
  }
}
