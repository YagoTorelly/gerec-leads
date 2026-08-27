import { describe, expect, it, vi } from "vitest";

import type { ServerSupabaseClient } from "../supabase/server";
import { getSessionContext } from "./get-session-context";

function createClient(overrides?: {
  accessToken?: string | null;
  userId?: string | null;
  role?: "admin" | "seller";
}) {
  const accessToken = overrides?.accessToken !== undefined ? overrides.accessToken : "token-123";
  const userId = overrides?.userId !== undefined ? overrides.userId : "user-1";
  const role = overrides?.role ?? "seller";

  const client: ServerSupabaseClient = {
    auth: {
      getAccessToken: () => accessToken,
      getUser: vi.fn().mockResolvedValue(userId ? { id: userId, email: `${role}@wtg.com` } : null),
    },
    profiles: {
      getByUserId: vi.fn().mockResolvedValue(
        userId
          ? {
              user_id: userId,
              full_name: role === "admin" ? "Administrador WTG" : "Vendedor WTG",
              email: `${role}@wtg.com`,
              role,
            }
          : null,
      ),
    },
  };

  return client;
}

describe("getSessionContext", () => {
  it("aciona o redirecionamento quando a sessao nao existe", async () => {
    const missingSession = vi.fn<() => never>().mockImplementation(() => {
      throw new Error("redirect:/login");
    });

    await expect(
      getSessionContext({
        client: createClient({ accessToken: null, userId: null }),
        onMissingSession: missingSession,
      }),
    ).rejects.toThrow("redirect:/login");

    expect(missingSession).toHaveBeenCalledOnce();
  });

  it("retorna o contexto autenticado para admin", async () => {
    await expect(
      getSessionContext({
        client: createClient({ role: "admin" }),
      }),
    ).resolves.toEqual({
      accessToken: "token-123",
      profile: {
        userId: "user-1",
        fullName: "Administrador WTG",
        email: "admin@wtg.com",
        role: "admin",
      },
    });
  });

  it("retorna o contexto autenticado para seller", async () => {
    await expect(
      getSessionContext({
        client: createClient({ role: "seller" }),
      }),
    ).resolves.toEqual({
      accessToken: "token-123",
      profile: {
        userId: "user-1",
        fullName: "Vendedor WTG",
        email: "seller@wtg.com",
        role: "seller",
      },
    });
  });
});
