import type { OperationalLead, SellerAvailability, SellerQueue } from "../lib/api/types";
import { formatDateTime } from "../lib/dashboard/format";

function availabilityLabel(availability: SellerAvailability): string {
  return availability === "paused" ? "Pausado pelo administrador" : "Disponível para novas atribuições";
}

export function SellerQueueTable({
  queue,
  leads,
}: {
  queue: SellerQueue;
  leads: OperationalLead[];
}) {
  return (
    <section className="table-card seller-queue-card" aria-labelledby="seller-queue-title">
      <div className="table-head">
        <div>
          <p className="eyebrow">Minha distribuição</p>
          <h2 id="seller-queue-title">Minha fila</h2>
        </div>
        <dl className="queue-table-summary">
          <div>
            <dt>Minha posição</dt>
            <dd>
              {queue.position === null ? "Posição não informada" : `Posição ${queue.position}`}
            </dd>
          </div>
          <div>
            <dt>Disponibilidade</dt>
            <dd>
              <span className={`status-badge status-badge--${queue.availability === "paused" ? "paused" : "active"}`}>
                {availabilityLabel(queue.availability)}
              </span>
            </dd>
          </div>
          <div>
            <dt>Saldo</dt>
            <dd>Saldo de pulos: {queue.skipBalance}</dd>
          </div>
        </dl>
      </div>
      {leads.length === 0 ? (
        <p className="empty">Nenhum lead atribuído a você.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Lead</th>
              <th>Atribuído em</th>
              <th>Última atualização</th>
            </tr>
          </thead>
          <tbody>
            {leads.map((lead) => (
              <tr key={lead.id}>
                <td>
                  <strong>{lead.contactName}</strong>
                </td>
                <td>{formatDateTime(lead.assignedAt)}</td>
                <td>{formatDateTime(lead.lastUpdatedAt)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
