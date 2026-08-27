import { cookies } from "next/headers";

import { supabaseAuthRequest, supabaseRestSelect } from "../supabase/rest";
import type { SessionProfile } from "../dashboard/types";

export const ACCESS_TOKEN_COOKIE = "wtg_access_token";
export const REFRESH_TOKEN_COOKIE = "wtg_refresh_token";

type SupabaseUser = {
  id: string;
  email?: string;
};

type ProfileRecord = {
  user_id: string;
  full_name: string;
  email: string;
  role: SessionProfile["role"];
};

export type SessionContext =
  | { status: "authenticated"; accessToken: string; profile: SessionProfile }
  | { status: "missing"; message: string }
  | { status: "unavailable"; message: string };

export async function getSessionContext(): Promise<SessionContext> {
  const cookieStore = await cookies();
  const accessToken = cookieStore.get(ACCESS_TOKEN_COOKIE)?.value;
  if (!accessToken) {
    return { status: "missing", message: "Entre com uma conta local para acessar o dashboard." };
  }

  try {
    const user = await supabaseAuthRequest<SupabaseUser>("/auth/v1/user", {
      method: "GET",
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    const profiles = await supabaseRestSelect<ProfileRecord>(
      `profiles?user_id=eq.${user.id}&select=user_id,full_name,email,role&limit=1`,
      accessToken,
    );
    const profile = profiles[0];
    if (!profile) {
      return { status: "unavailable", message: "Usuario autenticado sem perfil ativo no sistema." };
    }

    return {
      status: "authenticated",
      accessToken,
      profile: {
        userId: profile.user_id,
        fullName: profile.full_name,
        email: profile.email,
        role: profile.role,
      },
    };
  } catch (error) {
    return {
      status: "unavailable",
      message: error instanceof Error ? error.message : "Supabase local indisponivel.",
    };
  }
}
