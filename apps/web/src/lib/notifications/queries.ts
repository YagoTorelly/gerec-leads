import { apiFetch } from "../api/client";
import type { NewLeadNotificationSnapshot } from "../api/types";
import { SESSION_COOKIE } from "../auth/session";

/** Consulta uma janela estável; a confirmação acontece somente em uma ação separada. */
export async function getNewLeadNotifications(
  sessionToken: string,
): Promise<NewLeadNotificationSnapshot> {
  return apiFetch<NewLeadNotificationSnapshot>("/api/lead-notifications/new", {
    cache: "no-store",
    headers: { Cookie: `${SESSION_COOKIE}=${sessionToken}` },
  });
}
