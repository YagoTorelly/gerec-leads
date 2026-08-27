"use server";

import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";

import { getSessionContext } from "../../auth/get-session-context";
import { saveSeller, setSellerActiveState } from "./service";

function assertAdmin(role: "admin" | "seller") {
  if (role !== "admin") {
    throw new Error("Apenas administradores podem gerenciar usuários.");
  }
}

function toBoolean(value: FormDataEntryValue | null) {
  return value === "on" || value === "true" || value === "1";
}

function encodeNotice(message: string) {
  return encodeURIComponent(message);
}

export async function saveSellerAction(formData: FormData) {
  const session = await getSessionContext();
  assertAdmin(session.profile.role);

  await saveSeller({
    userId: String(formData.get("userId") ?? "").trim() || undefined,
    fullName: String(formData.get("fullName") ?? "").trim(),
    email: String(formData.get("email") ?? "").trim(),
    position: Number(formData.get("position")),
    password: String(formData.get("password") ?? "").trim() || undefined,
    isActive: toBoolean(formData.get("isActive")),
    isPaused: toBoolean(formData.get("isPaused")),
  });

  revalidatePath("/usuarios");
  redirect(`/usuarios?notice=${encodeNotice("Vendedor salvo com sucesso.")}`);
}

export async function deactivateSellerAction(formData: FormData) {
  const session = await getSessionContext();
  assertAdmin(session.profile.role);

  await setSellerActiveState(String(formData.get("userId") ?? ""), false);
  revalidatePath("/usuarios");
  redirect(`/usuarios?notice=${encodeNotice("Vendedor desativado e retirado da fila.")}`);
}

export async function reactivateSellerAction(formData: FormData) {
  const session = await getSessionContext();
  assertAdmin(session.profile.role);

  await setSellerActiveState(String(formData.get("userId") ?? ""), true);
  revalidatePath("/usuarios");
  redirect(`/usuarios?notice=${encodeNotice("Vendedor reativado.")}`);
}
