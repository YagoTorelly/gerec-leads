import { apiFetch } from "../api/client";
import type { LeadDistributionReport } from "../api/types";
import { SESSION_COOKIE } from "../auth/session";

export type ReportPeriodKey = "all" | "month" | "last30" | "custom";
export type ReportPeriod = { key: ReportPeriodKey; fromAt: string; toAt: string };
export type InvalidCustomReportPeriod = {
  key: "custom";
  from: string | null;
  to: string | null;
  error: string;
};
export type ReportPeriodResolution = ReportPeriod | InvalidCustomReportPeriod;
export type ReportSearchParams = Record<string, string | string[] | undefined>;

const ALL_HISTORY_FROM = "1970-01-01T00:00:00.000Z";
const SAO_PAULO_TIME_ZONE = "America/Sao_Paulo";
const dateTimeFormatter = new Intl.DateTimeFormat("en-US", {
  timeZone: SAO_PAULO_TIME_ZONE,
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
  hourCycle: "h23",
  timeZoneName: "longOffset",
});

function valueOf(value: string | string[] | undefined): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function dateParts(date: Date): Record<string, string> {
  return Object.fromEntries(
    dateTimeFormatter
      .formatToParts(date)
      .filter((part) => part.type !== "literal")
      .map((part) => [part.type, part.value]),
  );
}

function saoPauloOffsetMilliseconds(date: Date): number {
  const offset = dateParts(date).timeZoneName;
  const match = /^GMT([+-])(\d{2}):(\d{2})$/.exec(offset ?? "");
  if (!match) throw new Error("Não foi possível determinar o fuso de São Paulo.");
  const milliseconds = (Number(match[2]) * 60 + Number(match[3])) * 60 * 1000;
  return match[1] === "+" ? milliseconds : -milliseconds;
}

function saoPauloDate(value: string | null): Date | null {
  if (!value || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return null;
  const [year, month, day] = value.split("-").map(Number);
  const localMidnight = Date.UTC(year, month - 1, day);
  if (Number.isNaN(localMidnight)) return null;
  let instant = localMidnight - saoPauloOffsetMilliseconds(new Date(localMidnight));
  instant = localMidnight - saoPauloOffsetMilliseconds(new Date(instant));
  return new Date(instant);
}

function saoPauloMonthStart(now: Date): Date {
  const parts = dateParts(now);
  return saoPauloDate(`${parts.year}-${parts.month}-01`) as Date;
}

function allHistory(now: Date): ReportPeriod {
  return { key: "all", fromAt: ALL_HISTORY_FROM, toAt: now.toISOString() };
}

export function isReportPeriod(period: ReportPeriodResolution): period is ReportPeriod {
  return "fromAt" in period;
}

/** Converts São Paulo calendar controls into the explicit UTC interval required by the API. */
export function reportPeriod(searchParams: ReportSearchParams, now = new Date()): ReportPeriodResolution {
  const key = valueOf(searchParams.period);
  if (key === "last30") {
    return { key, fromAt: new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString(), toAt: now.toISOString() };
  }
  if (key === "month") {
    return { key, fromAt: saoPauloMonthStart(now).toISOString(), toAt: now.toISOString() };
  }
  if (key === "custom") {
    const fromValue = valueOf(searchParams.from);
    const toValue = valueOf(searchParams.to);
    const from = saoPauloDate(fromValue);
    const to = saoPauloDate(toValue);
    if (from && to && from < to) {
      return { key, fromAt: from.toISOString(), toAt: to.toISOString() };
    }
    return {
      key,
      from: fromValue,
      to: toValue,
      error: "Informe as duas datas de um período personalizado válido.",
    };
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
