"use server";
import { revalidatePath } from "next/cache";
import { getSessionContext } from "../auth/get-session-context";
import { simulateLeads } from "./simulator";
export async function simulateLeadsAction(formData: FormData) {
  const session = await getSessionContext();
  if (session.profile.role !== "admin") throw new Error("Apenas administradores podem simular leads.");
  await simulateLeads(Number(formData.get("quantity") ?? 1));
  revalidatePath("/dashboard"); revalidatePath("/fila"); revalidatePath("/historico");
}
