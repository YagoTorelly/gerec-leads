"use server";

import { randomUUID } from "node:crypto";
import { revalidatePath } from "next/cache";

import { apiFetch } from "../api/client";
import { getSessionContext, SESSION_COOKIE } from "../auth/session";

export async function registerContactAttemptAction(formData: FormData) {
  const session = await getSessionContext();
  if (session.status !== "authenticated") throw new Error("Sessão expirada. Entre novamente.");
  const leadId = String(formData.get("leadId") ?? "").trim();
  const comment = String(formData.get("comment") ?? "").trim();
  if (!leadId || comment.length < 6) throw new Error("Informe um comentário válido de ao menos 6 caracteres.");
  await apiFetch(`/api/leads/${encodeURIComponent(leadId)}/attempts`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Cookie: `${SESSION_COOKIE}=${session.sessionToken}` },
    body: JSON.stringify({ comment, idempotency_key: randomUUID() }),
  });
  revalidatePath("/dashboard"); revalidatePath("/fila"); revalidatePath("/historico");
}
