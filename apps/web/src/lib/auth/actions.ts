"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { apiRequest } from "../api/client";
import { SESSION_COOKIE } from "./session";

export type LoginState = { error?: string };
const cookieOptions = {
  httpOnly: true,
  sameSite: "lax" as const,
  secure: process.env.NODE_ENV === "production",
  path: "/",
};

function apiSessionCookie(setCookie: string | null): { token: string; maxAge: number } | null {
  const token = setCookie?.match(/gerec_session=([^;]+)/)?.[1];
  const maxAge = Number(setCookie?.match(/max-age=(\d+)/i)?.[1]);
  return token && Number.isSafeInteger(maxAge) && maxAge > 0 ? { token, maxAge } : null;
}

export async function loginAction(_state: LoginState, formData: FormData): Promise<LoginState> {
  const email = String(formData.get("email") ?? "").trim();
  const password = String(formData.get("password") ?? "");
  if (!email || !password) return { error: "Informe e-mail e senha para entrar." };
  try {
    const response = await apiRequest("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const session = apiSessionCookie(response.headers.get("set-cookie"));
    if (!session) throw new Error("A API não retornou uma sessão válida.");
    (await cookies()).set(SESSION_COOKIE, session.token, {
      ...cookieOptions,
      maxAge: session.maxAge,
    });
  } catch (error) {
    return { error: error instanceof Error ? error.message : "Não foi possível autenticar." };
  }
  redirect("/dashboard");
}

export async function signOutAction() {
  const cookieStore = await cookies();
  const token = cookieStore.get(SESSION_COOKIE)?.value;
  try {
    if (token)
      await apiRequest("/auth/logout", {
        method: "POST",
        headers: { Cookie: `${SESSION_COOKIE}=${token}` },
      });
  } finally {
    cookieStore.delete(SESSION_COOKIE);
  }
  redirect("/login");
}
