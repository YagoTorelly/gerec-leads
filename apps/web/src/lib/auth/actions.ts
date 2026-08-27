"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { ACCESS_TOKEN_COOKIE, REFRESH_TOKEN_COOKIE } from "./session";
import { supabaseAuthRequest } from "../supabase/rest";

export type LoginState = {
  error?: string;
};

type PasswordGrantResponse = {
  access_token: string;
  refresh_token: string;
  expires_in: number;
};

const cookieOptions = {
  httpOnly: true,
  sameSite: "lax" as const,
  secure: process.env.NODE_ENV === "production",
  path: "/",
};

export async function loginAction(_state: LoginState, formData: FormData): Promise<LoginState> {
  const email = String(formData.get("email") ?? "").trim();
  const password = String(formData.get("password") ?? "");

  if (!email || !password) {
    return { error: "Informe e-mail e senha para entrar." };
  }

  try {
    const session = await supabaseAuthRequest<PasswordGrantResponse>(
      "/auth/v1/token?grant_type=password",
      {
        method: "POST",
        body: JSON.stringify({ email, password }),
      },
    );
    const cookieStore = await cookies();
    cookieStore.set(ACCESS_TOKEN_COOKIE, session.access_token, {
      ...cookieOptions,
      maxAge: session.expires_in,
    });
    cookieStore.set(REFRESH_TOKEN_COOKIE, session.refresh_token, {
      ...cookieOptions,
      maxAge: 60 * 60 * 24 * 30,
    });
  } catch (error) {
    return {
      error:
        error instanceof Error
          ? error.message
          : "Nao foi possivel autenticar com o Supabase local.",
    };
  }

  redirect("/dashboard");
}

export async function signOutAction() {
  const cookieStore = await cookies();
  cookieStore.delete(ACCESS_TOKEN_COOKIE);
  cookieStore.delete(REFRESH_TOKEN_COOKIE);
  redirect("/login");
}
