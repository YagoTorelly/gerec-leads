import { apiFetch } from "../api/client";
import type { AdminDashboard, ApiDashboard } from "../api/types";
import { SESSION_COOKIE } from "../auth/session";

export function pageNumber(value: string | undefined): number {
  const page = Number(value);
  if (!Number.isFinite(page) || !Number.isInteger(page) || page < 1) {
    throw new Error("Página inválida.");
  }
  return page;
}

export async function getDashboardData(sessionToken: string, page = 1): Promise<ApiDashboard> {
  return apiFetch<ApiDashboard>(`/api/dashboard?page=${page}&limit=50`, {
    cache: "no-store",
    headers: { Cookie: `${SESSION_COOKIE}=${sessionToken}` },
  });
}

/** A API define o papel; a web apenas escolhe a composição de apresentação. */
export function isAdminDashboard(dashboard: unknown): dashboard is AdminDashboard {
  return (
    typeof dashboard === "object" &&
    dashboard !== null &&
    "user" in dashboard &&
    typeof dashboard.user === "object" &&
    dashboard.user !== null &&
    "role" in dashboard.user &&
    dashboard.user.role === "admin"
  );
}
