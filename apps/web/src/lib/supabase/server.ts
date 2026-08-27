import { cookies } from "next/headers";

import { ACCESS_TOKEN_COOKIE } from "../auth/session";
import { getPublicSupabaseRuntime, supabaseAuthRequest, supabaseRestSelect } from "./rest";

export { ACCESS_TOKEN_COOKIE } from "../auth/session";

export type ServerSupabaseClient = {
  auth: {
    getAccessToken: () => string | null;
    getUser: () => Promise<{ id: string; email?: string } | null>;
  };
  profiles: {
    getByUserId: (userId: string) => Promise<{
      user_id: string;
      full_name: string;
      email: string;
      role: "admin" | "seller";
    } | null>;
  };
};

export async function createServerSupabaseClient({
  runtime = getPublicSupabaseRuntime(),
} = {}): Promise<ServerSupabaseClient> {
  const cookieStore = await cookies();
  const accessToken = cookieStore.get(ACCESS_TOKEN_COOKIE)?.value ?? null;
  return {
    auth: {
      getAccessToken: () => accessToken,
      getUser: async () => {
        if (!accessToken || !runtime) return null;
        return supabaseAuthRequest(
          "/auth/v1/user",
          { method: "GET", headers: { Authorization: `Bearer ${accessToken}` } },
          runtime,
        );
      },
    },
    profiles: {
      getByUserId: async (userId) => {
        if (!accessToken || !runtime) return null;
        const rows = await supabaseRestSelect<{
          user_id: string;
          full_name: string;
          email: string;
          role: "admin" | "seller";
        }>(
          `profiles?user_id=eq.${encodeURIComponent(userId)}&select=user_id,full_name,email,role&limit=1`,
          accessToken,
          runtime,
        );
        return rows[0] ?? null;
      },
    },
  };
}
