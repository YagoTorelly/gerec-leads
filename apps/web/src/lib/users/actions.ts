"use server";

import { revalidatePath } from "next/cache";

import {
  ApiRequestError,
  createManagedUser,
  resetManagedUserPassword,
  setManagedUserAvailability,
} from "../api/client";
import type { CreateManagedUserInput, ManagedUser } from "../api/types";
import { getSessionContext } from "../auth/session";

export type UserMutationResult =
  | { status: "success"; message: string; user: ManagedUser }
  | { status: "error"; message: string; user: null };

function actionError(error: unknown): string {
  if (error instanceof ApiRequestError) return error.message;
  return "Não foi possível concluir a ação. Tente novamente.";
}

async function sessionToken(): Promise<string | null> {
  const session = await getSessionContext();
  return session.status === "authenticated" && session.profile.role === "admin" ? session.sessionToken : null;
}

function refreshUsers(): void {
  revalidatePath("/usuarios");
  revalidatePath("/dashboard");
  revalidatePath("/fila");
}

export async function createManagedUserAction(input: CreateManagedUserInput): Promise<UserMutationResult> {
  if (!input.fullName.trim() || !input.email.trim() || !input.password.trim()) {
    return { status: "error", message: "Preencha nome, e-mail e senha para criar o usuário.", user: null };
  }
  const token = await sessionToken();
  if (!token) return { status: "error", message: "Sessão expirada. Entre novamente.", user: null };
  try {
    const user = await createManagedUser({ ...input, fullName: input.fullName.trim(), email: input.email.trim() }, token);
    refreshUsers();
    return { status: "success", message: "Usuário criado.", user };
  } catch (error) {
    return { status: "error", message: actionError(error), user: null };
  }
}

export async function setManagedUserAvailabilityAction(userId: string, paused: boolean): Promise<UserMutationResult> {
  const token = await sessionToken();
  if (!token) return { status: "error", message: "Sessão expirada. Entre novamente.", user: null };
  try {
    const user = await setManagedUserAvailability(userId, paused, token);
    refreshUsers();
    return { status: "success", message: paused ? "Vendedor pausado." : "Vendedor ativado.", user };
  } catch (error) {
    return { status: "error", message: actionError(error), user: null };
  }
}

export async function resetManagedUserPasswordAction(userId: string, password: string): Promise<UserMutationResult> {
  if (!password.trim()) return { status: "error", message: "Informe uma nova senha.", user: null };
  const token = await sessionToken();
  if (!token) return { status: "error", message: "Sessão expirada. Entre novamente.", user: null };
  try {
    const user = await resetManagedUserPassword(userId, password, token);
    refreshUsers();
    return { status: "success", message: "Senha redefinida.", user };
  } catch (error) {
    return { status: "error", message: actionError(error), user: null };
  }
}
