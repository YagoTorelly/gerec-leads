import { apiFetch } from "../api/client";
import type { AdminDashboard, ApiDashboard } from "../api/types";
import { SESSION_COOKIE } from "../auth/session";

export type DashboardSort = "situation";

export type DashboardListFilters = {
  assigneeId: string | null;
  sort: DashboardSort | null;
};

export type DashboardSearchParams = Record<string, string | string[] | undefined>;

function singleValue(value: string | string[] | undefined): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

/** Only recognized query values are forwarded to the API read model. */
export function dashboardListFilters(searchParams: DashboardSearchParams): DashboardListFilters {
  const sort = singleValue(searchParams.sort);
  return {
    assigneeId: singleValue(searchParams.assigneeId),
    sort: sort === "situation" ? sort : null,
  };
}

export function pageNumber(value: string | undefined): number {
  const page = Number(value);
  if (!Number.isFinite(page) || !Number.isInteger(page) || page < 1) {
    throw new Error("Página inválida.");
  }
  return page;
}

export async function getDashboardData(
  sessionToken: string,
  page = 1,
  filters: Partial<DashboardListFilters> = {},
): Promise<ApiDashboard> {
  const searchParams = new URLSearchParams({ page: String(page), limit: "50" });
  if (filters.assigneeId) searchParams.set("assigneeId", filters.assigneeId);
  if (filters.sort === "situation") searchParams.set("sort", filters.sort);
  return apiFetch<ApiDashboard>(`/api/dashboard?${searchParams.toString()}`, {
    cache: "no-store",
    headers: { Cookie: `${SESSION_COOKIE}=${sessionToken}` },
  });
}

/** A API define o papel; a web apenas escolhe a composição de apresentação. */
export function isAdminDashboard(dashboard: ApiDashboard): dashboard is AdminDashboard {
  return dashboard.user.role === "admin";
}
