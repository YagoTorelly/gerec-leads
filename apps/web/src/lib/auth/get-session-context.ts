import type { SessionProfile } from "../dashboard/types";
import { createServerSupabaseClient, type ServerSupabaseClient } from "../supabase/server";

export type AuthenticatedSession = { accessToken: string; profile: SessionProfile };

export async function getSessionContext({
  client,
  onMissingSession = () => undefined,
}: {
  client?: ServerSupabaseClient;
  onMissingSession?: () => unknown;
} = {}): Promise<AuthenticatedSession> {
  const resolvedClient = client ?? (await createServerSupabaseClient());
  const accessToken = resolvedClient.auth.getAccessToken();
  if (!accessToken) {
    onMissingSession();
    throw new Error("Sessão ausente");
  }
  let user: { id: string; email?: string } | null;
  try {
    user = await resolvedClient.auth.getUser();
  } catch (error) {
    onMissingSession();
    throw error;
  }
  if (!user) throw new Error("Sessão inválida");
  const profile = await resolvedClient.profiles.getByUserId(user.id);
  if (!profile) throw new Error("Perfil não encontrado");
  return {
    accessToken,
    profile: {
      userId: profile.user_id,
      fullName: profile.full_name,
      email: profile.email,
      role: profile.role,
    },
  };
}
