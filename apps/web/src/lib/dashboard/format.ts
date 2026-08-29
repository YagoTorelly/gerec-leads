import type { CommercialStatus } from "../api/types";

export type SlaState = "overdue" | "today" | "scheduled" | "none";

export const NOT_INFORMED = "Não informado";

const SAO_PAULO_TIME_ZONE = "America/Sao_Paulo";

const dateTimeFormatter = new Intl.DateTimeFormat("pt-BR", {
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
  month: "2-digit",
  timeZone: SAO_PAULO_TIME_ZONE,
  year: "numeric",
});

const dateKeyFormatter = new Intl.DateTimeFormat("en-CA", {
  day: "2-digit",
  month: "2-digit",
  timeZone: SAO_PAULO_TIME_ZONE,
  year: "numeric",
});

export function formatText(value: string | null | undefined): string {
  return value?.trim() || NOT_INFORMED;
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value || Number.isNaN(new Date(value).getTime())) return NOT_INFORMED;
  return dateTimeFormatter.format(new Date(value));
}

export function formatSlaDeadline(value: string | null | undefined): string {
  return formatDateTime(value);
}

export function formatCommercialStatus(value: CommercialStatus): string {
  return {
    undefined: "Indefinido",
    negotiation: "Negociação",
    won: "Ganho",
  }[value];
}

export function formatDisqualificationMarker(isDisqualified: boolean): string {
  return isDisqualified ? "Desqualificado" : "Não desqualificado";
}

export function formatCommentCount(value: number): string {
  const count = Number.isInteger(value) && value >= 0 ? value : 0;
  return `${count} ${count === 1 ? "comentário" : "comentários"}`;
}

export function formatPhone(value: string | null | undefined): string {
  let digits = String(value ?? "").replace(/\D/g, "");
  if (digits.startsWith("55") && (digits.length === 12 || digits.length === 13)) digits = digits.slice(2);
  if (digits.length === 11) return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7)}`;
  if (digits.length === 10) return `(${digits.slice(0, 2)}) ${digits.slice(2, 6)}-${digits.slice(6)}`;
  return digits || NOT_INFORMED;
}

export function getSaoPauloDateKey(value: Date): string {
  return dateKeyFormatter.format(value);
}

export function getSlaState(value: string | null | undefined, now = new Date()): SlaState {
  if (!value || Number.isNaN(new Date(value).getTime())) return "none";
  const dueDate = new Date(value);
  if (dueDate.getTime() < now.getTime()) return "overdue";
  if (getSaoPauloDateKey(dueDate) === getSaoPauloDateKey(now)) return "today";
  return "scheduled";
}
