import { apiFetch } from "../api/client";
import type { ApiDashboard } from "../api/types";
import { SESSION_COOKIE } from "../auth/session";

export async function getDashboardData(sessionToken: string, page = 1): Promise<ApiDashboard> {
  return apiFetch<ApiDashboard>(`/api/dashboard?page=${page}&limit=50`, {
    cache: "no-store",
    headers: { Cookie: `${SESSION_COOKIE}=${sessionToken}` },
  });
}
