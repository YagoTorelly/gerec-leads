import type { AdminDashboard as AdminDashboardData, QueueEntry, Treatment } from "../lib/api/types";
import {
  formatCommercialStatus,
  formatDateTime,
  formatDisqualificationMarker,
} from "../lib/dashboard/format";

function availabilityLabel(availability: QueueEntry["availability"]): string {
  return {
    active: "Ativo",
    blocked_overdue: "Bloqueado por atraso",
    paused: "Pausado",
  }[availability];
}

function QueueCard({ item }: { item: QueueEntry }) {
  const label = availabilityLabel(item.availability);
  return (
    <li className="queue-card">
      <div className="queue-card__header">
        <span className="queue-card__position">#{item.position}</span>
        <span className={`status-badge status-badge--${item.availability}`}>{label}</span>
      </div>
      <strong>{item.sellerName}</strong>
      <small>{item.reason ?? "Disponível para novas atribuições"}</small>
    </li>
  );
}

function TreatmentPreview({ item }: { item: Treatment }) {
  return (
    <li className="activity-item">
      <div>
        <strong>{item.leadName ?? "Lead não informado"}</strong>
        <small>Vendedor responsável: {item.sellerName}</small>
      </div>
      <div className="activity-item__meta">
        <span>{formatCommercialStatus(item.commercialStatus)}</span>
        <small>{formatDateTime(item.createdAt)}</small>
        <small>{formatDisqualificationMarker(item.isDisqualified)}</small>
      </div>
    </li>
  );
}

export function AdminDashboard({ dashboard }: { dashboard: AdminDashboardData }) {
  return (
    <>
      <section className="metric-grid" aria-label="Resumo operacional administrativo">
        <article className="metric-card metric-card--accent"><span>Total de leads</span><strong>{dashboard.leads.total}</strong></article>
        <article className="metric-card"><span>Atribuições</span><strong>{dashboard.history.total}</strong></article>
        <article className="metric-card"><span>Posições na fila</span><strong>{dashboard.queue.total}</strong></article>
        <article className="metric-card metric-card--next"><span>Próximo vendedor</span><strong>{dashboard.queue.nextSellerName}</strong></article>
      </section>

      <section className="dashboard-layout" aria-label="Distribuição e atividade recente">
        <section className="dashboard-panel dashboard-panel--queue">
          <header className="dashboard-panel__header">
            <div><p className="eyebrow">Distribuição</p><h2>Fila comercial</h2></div>
            <a className="text-link" href="/fila">Ver fila completa</a>
          </header>
          <p className="queue-cursor">Próxima vez: <strong>{dashboard.queue.cursorSellerName}</strong></p>
          <ol className="queue-list" aria-label="Fila comercial completa">
            {dashboard.queue.items.map((item) => <QueueCard item={item} key={item.sellerName} />)}
          </ol>
        </section>

        <section className="dashboard-panel">
          <header className="dashboard-panel__header">
            <div><p className="eyebrow">Atividade</p><h2>Últimas tratativas</h2></div>
            <a className="text-link" href="/historico">Ver histórico</a>
          </header>
          {dashboard.history.items.length === 0 ? <p className="empty-state">Nenhuma tratativa registrada.</p> : (
            <ol className="activity-list">{dashboard.history.items.slice(0, 5).map((item, index) => <TreatmentPreview item={item} key={`${item.createdAt}-${index}`} />)}</ol>
          )}
        </section>
      </section>
    </>
  );
}
