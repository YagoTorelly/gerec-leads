"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { apiRequest } from "../api/client";
import { SESSION_COOKIE } from "./session";

export type LoginState = { error?: string };
const cookieOptions = { httpOnly: true, sameSite: "lax" as const, secure: process.env.NODE_ENV === "production", path: "/" };

export async function loginAction(_state: LoginState, formData: FormData): Promise<LoginState> {
  const email = String(formData.get("email") ?? "").trim();
  const password = String(formData.get("password") ?? "");
  if (!email || !password) return { error: "Informe e-mail e senha para entrar." };
  try {
    const response = await apiRequest("/auth/login", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email, password }) });
    const token = response.headers.get("set-cookie")?.match(/gerec_session=([^;]+)/)?.[1];
    if (!token) throw new Error("A API não retornou uma sessão válida.");
    (await cookies()).set(SESSION_COOKIE, token, { ...cookieOptions, maxAge: 60 * 60 * 24 });
  } catch (error) {
    return { error: error instanceof Error ? error.message : "Não foi possível autenticar." };
  }
  redirect("/dashboard");
}

export async function signOutAction() {
  const cookieStore = await cookies();
  const token = cookieStore.get(SESSION_COOKIE)?.value;
  if (token) await apiRequest("/auth/logout", { method: "POST", headers: { Cookie: `${SESSION_COOKIE}=${token}` } });
  cookieStore.delete(SESSION_COOKIE);
  redirect("/login");
}
