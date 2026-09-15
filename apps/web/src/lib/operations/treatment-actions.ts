"use server";

import { randomUUID } from "node:crypto";
import { revalidatePath } from "next/cache";

import { ApiRequestError, getLeadTreatments, submitLeadTreatment } from "../api/client";
import type { CommercialStatus, Treatment } from "../api/types";
import { getSessionContext } from "../auth/session";
import type { TreatmentActionState } from "./treatment-state";

export type { TreatmentActionState } from "./treatment-state";

type TreatmentHistoryResult =
  | { status: "success"; items: Treatment[] }
  | { status: "error"; message: string; items: Treatment[] };

function commercialStatus(value: FormDataEntryValue | null): CommercialStatus | null {
  return value === "undefined" || value === "negotiation" || value === "potential" || value === "won"
    ? value
    : null;
}

function actionError(error: unknown): string {
  if (error instanceof ApiRequestError) return error.message;
  return "Não foi possível concluir a tratativa. Tente novamente.";
}

export async function submitLeadTreatmentAction(
  _previous: TreatmentActionState,
  formData: FormData,
): Promise<TreatmentActionState> {
  const leadId = String(formData.get("leadId") ?? "").trim();
  const comment = String(formData.get("comment") ?? "").trim();
  const status = commercialStatus(formData.get("commercialStatus"));
  const isDisqualified = formData.get("isDisqualified") === "on";

  if (!leadId || !status || comment.length < 6) {
    return {
      status: "error",
      message: "Escreva um comentário com ao menos 6 caracteres.",
      submission: null,
    };
  }

  const session = await getSessionContext();
  if (session.status !== "authenticated") {
    return { status: "error", message: "Sessão expirada. Entre novamente.", submission: null };
  }

  try {
    const submission = await submitLeadTreatment(
      leadId,
      {
        comment,
        commercialStatus: status,
        isDisqualified,
        idempotencyKey: String(formData.get("idempotencyKey") ?? "").trim() || randomUUID(),
      },
      session.sessionToken,
    );
    revalidatePath("/dashboard");
    revalidatePath("/historico");
    return { status: "success", message: "Tratativa registrada.", submission };
  } catch (error) {
    return { status: "error", message: actionError(error), submission: null };
  }
}

export async function loadLeadTreatmentHistoryAction(
  leadId: string,
): Promise<TreatmentHistoryResult> {
  const session = await getSessionContext();
  if (session.status !== "authenticated") {
    return { status: "error", message: "Sessão expirada. Entre novamente.", items: [] };
  }

  try {
    const history = await getLeadTreatments(leadId, session.sessionToken);
    return { status: "success", items: history.items };
  } catch (error) {
    return { status: "error", message: actionError(error), items: [] };
  }
}
