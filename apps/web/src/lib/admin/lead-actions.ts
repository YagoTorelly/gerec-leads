"use server";
import { revalidatePath } from "next/cache";
import { getSessionContext } from "../auth/get-session-context";
import { supabaseAdminRestPatch } from "../supabase/admin";

export async function archiveLeadAction(formData: FormData) {
  const session = await getSessionContext();
  if (session.profile.role !== "admin") throw new Error("Apenas administradores podem remover leads.");
  const leadId = Number(formData.get("leadId"));
  if (!Number.isInteger(leadId) || leadId <= 0) throw new Error("Lead inválido.");
  await supabaseAdminRestPatch(`leads?id=eq.${leadId}`, { assignment_status: "archived", archived_at: new Date().toISOString(), current_assignee_id: null, updated_at: new Date().toISOString() });
  revalidatePath("/dashboard"); revalidatePath("/fila"); revalidatePath("/historico");
}
