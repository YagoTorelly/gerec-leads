import type { LeadDistributionReport } from "../lib/api/types";
import { formatCommercialStatus } from "../lib/dashboard/format";
import type { ReportPeriodKey } from "../lib/reports/queries";

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

export function ReportsDashboard({ report, period }: { report: LeadDistributionReport; period: ReportPeriodKey }) {
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
        <label>De<input name="from" type="date" /></label>
        <label>Até<input name="to" type="date" /></label>
        <button className="table-action" type="submit">Atualizar relatório</button>
      </form>
      <section className="report-card" aria-labelledby="report-by-situation">
        <h2 id="report-by-situation">Por situação</h2>
        <DistributionBars label="Distribuição por situação" items={report.bySituation.map((item) => ({ name: formatCommercialStatus(item.commercialStatus), count: item.count }))} />
      </section>
      <section className="report-card" aria-labelledby="report-by-seller">
        <h2 id="report-by-seller">Por vendedor</h2>
        <DistributionBars label="Distribuição por vendedor" items={report.bySeller.map((item) => ({ name: item.sellerName, count: item.count }))} />
      </section>
    </section>
  );
}
