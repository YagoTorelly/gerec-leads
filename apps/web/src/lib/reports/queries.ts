import { apiFetch } from "../api/client";
import type { LeadDistributionReport } from "../api/types";
import { SESSION_COOKIE } from "../auth/session";

export type ReportPeriodKey = "all" | "month" | "last30" | "custom";
export type ReportPeriod = { key: ReportPeriodKey; fromAt: string; toAt: string };
export type ReportSearchParams = Record<string, string | string[] | undefined>;

const ALL_HISTORY_FROM = "1970-01-01T00:00:00.000Z";

function valueOf(value: string | string[] | undefined): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function utcDate(value: string | null): Date | null {
  if (!value || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return null;
  const date = new Date(`${value}T00:00:00.000Z`);
  return Number.isNaN(date.getTime()) ? null : date;
}

function allHistory(now: Date): ReportPeriod {
  return { key: "all", fromAt: ALL_HISTORY_FROM, toAt: now.toISOString() };
}

/** Converts report controls into the explicit UTC interval required by the API. */
export function reportPeriod(searchParams: ReportSearchParams, now = new Date()): ReportPeriod {
  const key = valueOf(searchParams.period);
  if (key === "last30") {
    return { key, fromAt: new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString(), toAt: now.toISOString() };
  }
  if (key === "month") {
    return { key, fromAt: new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), 1)).toISOString(), toAt: now.toISOString() };
  }
  if (key === "custom") {
    const from = utcDate(valueOf(searchParams.from));
    const to = utcDate(valueOf(searchParams.to));
    if (from && to && from < to) {
      return { key, fromAt: from.toISOString(), toAt: to.toISOString() };
    }
  }
  return allHistory(now);
}

export async function getLeadDistributionReport(
  sessionToken: string,
  period: ReportPeriod,
): Promise<LeadDistributionReport> {
  const searchParams = new URLSearchParams({ fromAt: period.fromAt, toAt: period.toAt });
  return apiFetch<LeadDistributionReport>(
    `/api/admin/reports/lead-distribution?${searchParams.toString()}`,
    { cache: "no-store", headers: { Cookie: `${SESSION_COOKIE}=${sessionToken}` } },
  );
}
