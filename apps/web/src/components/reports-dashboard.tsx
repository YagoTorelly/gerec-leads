import type { LeadDistributionReport } from "../lib/api/types";
import { formatCommercialStatus } from "../lib/dashboard/format";
import type { ReportPeriodKey } from "../lib/reports/queries";

const SAO_PAULO_TIME_ZONE = "America/Sao_Paulo";

function DistributionBars({
  items,
  label,
}: {
  items: Array<{ name: string; count: number }>;
  label: string;
}) {
  if (items.length === 0) return <p className="empty-state">Nenhum dado para o período selecionado.</p>;
  const maximum = Math.max(...items.map((item) => item.count), 1);
  return (
    <ul className="report-bars" aria-label={label}>
      {items.map((item) => (
        <li key={item.name} className="report-bar">
          <span className="report-bar__label">{item.name}: {item.count}</span>
          <span className="report-bar__track" aria-hidden="true">
            <span className="report-bar__fill" style={{ width: `${(item.count / maximum) * 100}%` }} />
          </span>
        </li>
      ))}
    </ul>
  );
}

function saoPauloDateInputValue(value: string | null | undefined): string {
  if (!value) return "";
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: SAO_PAULO_TIME_ZONE,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(new Date(value));
  const fields = Object.fromEntries(
    parts.filter((part) => part.type !== "literal").map((part) => [part.type, part.value]),
  );
  return `${fields.year}-${fields.month}-${fields.day}`;
}

export function ReportsDashboard({
  report,
  period,
  error,
  from,
  to,
  interval,
}: {
  report: LeadDistributionReport | null;
  period: ReportPeriodKey;
  error?: string | null;
  from?: string | null;
  to?: string | null;
  interval?: { from: string; to: string };
}) {
  const reportPeriod = report?.period ?? interval;
  const customFrom = from ?? (period === "custom" ? saoPauloDateInputValue(reportPeriod?.from) : "");
  const customTo = to ?? (period === "custom" ? saoPauloDateInputValue(reportPeriod?.to) : "");
  const periodFrom = reportPeriod?.from ?? (customFrom ? `${customFrom}T00:00:00` : null);
  const periodTo = reportPeriod?.to ?? (customTo ? `${customTo}T00:00:00` : null);

  return (
    <section className="reports-dashboard">
      <form className="report-filters" action="/relatorios" method="get">
        <label>
          Período
          <select name="period" defaultValue={period}>
            <option value="all">Todo o histórico</option>
            <option value="month">Mês atual</option>
            <option value="last30">Últimos 30 dias</option>
            <option value="custom">Personalizado</option>
          </select>
        </label>
        <label>De<input name="from" type="date" defaultValue={customFrom} /></label>
        <label>Até<input name="to" type="date" defaultValue={customTo} /></label>
        <button className="table-action" type="submit">{error ? "Tentar novamente" : "Atualizar relatório"}</button>
      </form>
      {periodFrom && periodTo ? (
        <p className="muted">Período baseado na atribuição atual: {periodFrom} até {periodTo}.</p>
      ) : null}
      {error ? <p className="form-error" role="alert">{error}</p> : null}
      {report ? (
        <>
          <section className="report-card" aria-labelledby="report-by-situation">
            <h2 id="report-by-situation">Por situação</h2>
            <DistributionBars label="Distribuição por situação" items={report.bySituation.map((item) => ({ name: formatCommercialStatus(item.commercialStatus), count: item.count }))} />
          </section>
          <section className="report-card" aria-labelledby="report-by-seller">
            <h2 id="report-by-seller">Por vendedor</h2>
            <DistributionBars label="Distribuição por vendedor" items={report.bySeller.map((item) => ({ name: item.sellerName, count: item.count }))} />
          </section>
        </>
      ) : null}
    </section>
  );
}
