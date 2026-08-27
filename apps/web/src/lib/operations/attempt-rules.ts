export const FEEDBACK_INTERVAL_HOURS = 24;

export function toSaoPauloDateKey(date: Date) {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "America/Sao_Paulo",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(date);
}

export function isBusinessDate(date: Date, holidays: string[] = []) {
  const weekday = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/Sao_Paulo",
    weekday: "short",
  }).format(date);
  return weekday !== "Sat" && weekday !== "Sun" && !holidays.includes(toSaoPauloDateKey(date));
}

export function nextFeedbackDueAt(attemptAt: Date) {
  return new Date(attemptAt.getTime() + FEEDBACK_INTERVAL_HOURS * 60 * 60 * 1000);
}

export function validateAttempt(input: {
  comment: string;
  attemptCount: number;
}) {
  const comment = input.comment.trim();
  if (comment.length < 6) throw new Error("O comentário deve ter pelo menos 6 caracteres.");
}
