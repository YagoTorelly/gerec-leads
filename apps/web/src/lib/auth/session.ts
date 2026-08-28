import { cookies } from "next/headers";

import { apiFetch, ApiRequestError } from "../api/client";
import type { ApiUser } from "../api/types";

export const SESSION_COOKIE = "gerec_session";
export type SessionProfile = ApiUser & { userId: string; fullName: string };
export type SessionContext =
  | { status: "authenticated"; sessionToken: string; profile: SessionProfile }
  | { status: "missing" | "unavailable"; message: string };

export async function getSessionContext(): Promise<SessionContext> {
  const token = (await cookies()).get(SESSION_COOKIE)?.value;
  if (!token) return { status: "missing", message: "Entre para acessar o sistema." };
  try {
    const user = await apiFetch<ApiUser>("/auth/me", {
      cache: "no-store",
      headers: { Cookie: `${SESSION_COOKIE}=${token}` },
    });
    return { status: "authenticated", sessionToken: token, profile: { ...user, userId: user.id, fullName: user.email } };
  } catch (error) {
    if (error instanceof ApiRequestError && error.status === 401) {
      return { status: "missing", message: "Sua sessão expirou. Entre novamente." };
    }
    return { status: "unavailable", message: error instanceof Error ? error.message : "API indisponível." };
  }
}
