"use server";

import { revalidatePath } from "next/cache";
import { getSessionContext } from "../auth/get-session-context";
import { registerContactAttempt } from "./attempt-service";

export async function registerContactAttemptAction(formData: FormData) {
  const session = await getSessionContext();
  if (session.profile.role !== "seller") throw new Error("Somente vendedores podem registrar tentativas.");
  const leadId = Number(formData.get("leadId"));
  if (!Number.isInteger(leadId) || leadId <= 0) throw new Error("Lead inválido.");
  await registerContactAttempt({
    leadId,
    sellerId: session.profile.userId,
    comment: String(formData.get("comment") ?? ""),
    commercialStatus: String(formData.get("commercialStatus") ?? "undefined") as "undefined" | "negotiation" | "won" | "disqualified",
  });
  revalidatePath("/dashboard");
  revalidatePath("/fila");
  revalidatePath("/historico");
}
