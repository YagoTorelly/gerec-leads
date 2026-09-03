import type {
  SellerAvailability,
  SellerDashboard as SellerDashboardData,
  Treatment,
} from "../lib/api/types";
import {
  formatCommentCount,
  formatCommercialStatus,
  formatDateTime,
  formatDisqualificationMarker,
} from "../lib/dashboard/format";
import { LeadTable } from "./lead-table";

function availabilityLabel(availability: SellerAvailability): string {
  return availability === "paused" ? "Pausado pelo administrador" : "Disponível para novas atribuições";
}

function TreatmentPreview({ item }: { item: Treatment }) {
  return (
    <li className="activity-item">
      <div>
        <strong>{item.leadName ?? "Lead não informado"}</strong>
        <small>{item.comment}</small>
      </div>
      <div className="activity-item__meta">
        <span className={`commercial-status ${item.commercialStatus}`}>
          {formatCommercialStatus(item.commercialStatus)}
        </span>
        <small>{formatDateTime(item.createdAt)}</small>
        {item.isDisqualified ? (
          <span className="disqualification-marker">{formatDisqualificationMarker(true)}</span>
        ) : null}
      </div>
    </li>
  );
}

export function SellerDashboard({ dashboard }: { dashboard: SellerDashboardData }) {
  const queuePosition =
    typeof dashboard.queue.position === "number" && Number.isFinite(dashboard.queue.position)
      ? dashboard.queue.position
      : null;

  return (
    <>
      <section className="metric-grid metric-grid--seller" aria-label="Resumo da minha operação">
        <article className="metric-card metric-card--accent">
          <span>Meus leads</span>
          <strong>{dashboard.leads.total}</strong>
        </article>
        <article className="metric-card">
          <span>Meus comentários</span>
          <strong>{formatCommentCount(dashboard.history.total)}</strong>
        </article>
        <article className="metric-card metric-card--next">
          <span>Minha posição na fila</span>
          <strong className="metric-card__text">
            {queuePosition === null
              ? "Não informado"
              : `Posição ${queuePosition}`}
          </strong>
        </article>
      </section>

      <section
        className="dashboard-layout dashboard-layout--seller"
        aria-label="Minha atividade recente"
      >
        <section className="dashboard-panel">
          <p className="eyebrow">Minha disponibilidade</p>
          <h2>{availabilityLabel(dashboard.queue.availability)}</h2>
          <p className="dashboard-copy">Saldo de pulos: {dashboard.queue.skipBalance}</p>
        </section>
        <section className="dashboard-panel">
          <header className="dashboard-panel__header">
            <div>
              <p className="eyebrow">Minha atividade</p>
              <h2>Últimas tratativas</h2>
            </div>
          </header>
          {dashboard.history.items.length === 0 ? (
            <p className="empty-state">Você ainda não registrou tratativas.</p>
          ) : (
            <ol className="activity-list">
              {dashboard.history.items.slice(0, 5).map((item, index) => (
                <TreatmentPreview item={item} key={`${item.createdAt}-${index}`} />
              ))}
            </ol>
          )}
        </section>
      </section>

      <LeadTable leads={dashboard.leads.items} role="seller" />
    </>
  );
}
