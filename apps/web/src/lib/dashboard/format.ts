export type SlaState = "overdue" | "today" | "scheduled" | "none";

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

export function formatDateTime(value: string | null | undefined) {
  if (!value) return "";
  return dateTimeFormatter.format(new Date(value));
}

export function getSaoPauloDateKey(value: Date) {
  return dateKeyFormatter.format(value);
}

export function getSlaState(value: string | null | undefined, now = new Date()): SlaState {
  if (!value) return "none";
  const dueDate = new Date(value);
  if (dueDate.getTime() < now.getTime()) return "overdue";
  if (getSaoPauloDateKey(dueDate) === getSaoPauloDateKey(now)) return "today";
  return "scheduled";
}
