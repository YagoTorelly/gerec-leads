import { Pagination } from "./pagination";
import type { ExportationHistoryItem, Page } from "../lib/api/types";
import { formatDateTime } from "../lib/dashboard/format";

const FILTER_LABELS: Record<string, string> = {
  situation: "Situação",
  seller: "Responsável",
  source: "Origem",
};

function filterValue(value: unknown): string {
  if (value === null || value === undefined || value === "") return "Não informado";
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  try {
    return JSON.stringify(value);
  } catch {
    return "Não informado";
  }
}

function formatFilters(filters: Record<string, unknown>): string {
  const entries = Object.entries(filters);
  if (entries.length === 0) return "Todos os leads";
  return entries
    .map(([key, value]) => `${FILTER_LABELS[key] ?? key}: ${filterValue(value)}`)
    .join("; ");
}

function statusLabel(status: ExportationHistoryItem["status"]): string {
  return status === "success" ? "Concluída" : "Falhou";
}

export function ExportationsLoading() {
  return (
    <section className="panel-card exportations-panel" aria-live="polite" aria-busy="true">
      <div className="route-loading">
        <div className="route-loading__bar" />
        <p>Carregando histórico de exportações…</p>
      </div>
    </section>
  );
}

export function ExportationsPanel({
  history,
  error = null,
  retryHref = "/exportacoes",
}: {
  history: Page<ExportationHistoryItem> | null;
  error?: string | null;
  retryHref?: string;
}) {
  return (
    <div className="exportations-layout">
      <section className="panel-card exportations-panel" aria-labelledby="export-leads-title">
        <div className="panel-head exportations-panel__head">
          <div>
            <p className="eyebrow">Dados administrativos</p>
            <h2 id="export-leads-title">Exportar leads</h2>
            <p className="muted">
              Baixe todos os leads em Excel. O arquivo não inclui tratativas nem o histórico abaixo.
            </p>
          </div>
          <a className="table-action exportations-download" href="/exportacoes/download" download>
            Exportar leads em Excel
          </a>
        </div>
      </section>

      <section
        className={`table-card exportations-history${error ? " unavailable-state" : ""}`}
        aria-label="Histórico de exportações"
      >
        <div className="table-head">
          <div>
            <p className="eyebrow">Auditoria</p>
            <h2>Histórico de exportações</h2>
          </div>
        </div>
        {error || history === null ? (
          <div className="exportations-history__state" aria-live="polite">
            <p>{error ?? "Não foi possível carregar o histórico de exportações."}</p>
            <a className="secondary-button" href={retryHref}>
              Tentar novamente
            </a>
          </div>
        ) : history.items.length === 0 ? (
          <p className="empty">Nenhuma exportação registrada.</p>
        ) : (
          <>
            <table>
              <thead>
                <tr>
                  <th>Data e hora</th>
                  <th>Administrador responsável</th>
                  <th>Quantidade</th>
                  <th>Filtros</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {history.items.map((item, index) => (
                  <tr key={`${item.createdAt}-${item.administratorName}-${index}`}>
                    <td>{formatDateTime(item.createdAt)}</td>
                    <td>
                      <strong>{item.administratorName}</strong>
                    </td>
                    <td>{item.leadCount}</td>
                    <td>{formatFilters(item.filters)}</td>
                    <td>
                      <span className={`status-badge status-badge--export-${item.status}`}>
                        {statusLabel(item.status)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <Pagination href="/exportacoes" page={history} />
          </>
        )}
      </section>
    </div>
  );
}
