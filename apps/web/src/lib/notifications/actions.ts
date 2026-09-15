"use server";

import { revalidatePath } from "next/cache";

import {
  acknowledgeNewLeadNotifications,
  ApiRequestError,
} from "../api/client";
import type { NewLeadNotificationSnapshot } from "../api/types";
import { getSessionContext } from "../auth/session";

export type NewLeadAcknowledgementResult =
  | { ok: true; message: string }
  | { ok: false; message: string };

function actionError(error: unknown): string {
  if (error instanceof ApiRequestError) return error.message;
  return "Não foi possível confirmar os novos leads.";
}

export async function acknowledgeNewLeadsAction(
  snapshot: NewLeadNotificationSnapshot,
): Promise<NewLeadAcknowledgementResult> {
  try {
    const session = await getSessionContext();
    if (session.status !== "authenticated" || session.profile.role !== "seller") {
      return { ok: false, message: "Sessão expirada ou sem permissão." };
    }
    await acknowledgeNewLeadNotifications(snapshot, session.sessionToken);
    revalidatePath("/dashboard");
    return { ok: true, message: "Novos leads confirmados." };
  } catch (error) {
    return { ok: false, message: actionError(error) };
  }
}
