import { ApiRequestError, apiFetch } from "../api/client";
import type { ExportationHistoryItem, Page } from "../api/types";
import { SESSION_COOKIE } from "../auth/session";

const INVALID_HISTORY = "A resposta do histórico de exportações é inválida.";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function exportationItem(value: unknown): ExportationHistoryItem {
  if (!isRecord(value)) throw new ApiRequestError(INVALID_HISTORY, 502);
  const { administratorName, createdAt, filters, leadCount, status } = value;
  if (
    typeof createdAt !== "string" ||
    Number.isNaN(new Date(createdAt).getTime()) ||
    typeof administratorName !== "string" ||
    !administratorName.trim() ||
    typeof leadCount !== "number" ||
    !Number.isInteger(leadCount) ||
    leadCount < 0 ||
    !isRecord(filters) ||
    (status !== "success" && status !== "error")
  ) {
    throw new ApiRequestError(INVALID_HISTORY, 502);
  }
  return { createdAt, administratorName: administratorName.trim(), leadCount, filters, status };
}

function exportationPage(value: unknown): Page<ExportationHistoryItem> {
  if (!isRecord(value)) throw new ApiRequestError(INVALID_HISTORY, 502);
  const { items, page, pageSize, total } = value;
  if (
    !Array.isArray(items) ||
    typeof page !== "number" ||
    !Number.isInteger(page) ||
    page < 1 ||
    typeof pageSize !== "number" ||
    !Number.isInteger(pageSize) ||
    pageSize < 1 ||
    typeof total !== "number" ||
    !Number.isInteger(total) ||
    total < 0
  ) {
    throw new ApiRequestError(INVALID_HISTORY, 502);
  }
  return { items: items.map(exportationItem), page, pageSize, total };
}

export async function getExportationHistory(
  sessionToken: string,
  page = 1,
  limit = 50,
): Promise<Page<ExportationHistoryItem>> {
  const query = new URLSearchParams({ page: String(page), limit: String(limit) });
  return exportationPage(
    await apiFetch<unknown>(`/api/admin/exportations?${query.toString()}`, {
      cache: "no-store",
      headers: { Cookie: `${SESSION_COOKIE}=${sessionToken}` },
    }),
  );
}
