import type { AdminQueue, QueueEntry } from "../lib/api/types";

function availabilityLabel(availability: QueueEntry["availability"]): string {
  return {
    active: "Ativo",
    paused: "Pausado",
  }[availability];
}

function availabilityReason(item: QueueEntry): string {
  return item.reason ?? "Disponível para novas atribuições";
}

export function QueueTable({ queue }: { queue: AdminQueue }) {
  return (
    <section className="table-card queue-table-card" aria-labelledby="queue-table-title">
      <div className="table-head">
        <div>
          <p className="eyebrow">Dados ao vivo</p>
          <h2 id="queue-table-title">Fila comercial</h2>
        </div>
        <dl className="queue-table-summary">
          <div>
            <dt>Cursor atual</dt>
            <dd>{queue.cursorSellerName}</dd>
          </div>
          <div>
            <dt>Próximo elegível</dt>
            <dd>{queue.nextSellerName}</dd>
          </div>
        </dl>
      </div>
      {queue.items.length === 0 ? (
        <p className="empty">Nenhum vendedor cadastrado na fila.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Ordem atual</th>
              <th>Posição base</th>
              <th>Vendedor</th>
              <th>Disponibilidade</th>
              <th>Motivo</th>
              <th>Créditos de pulo</th>
            </tr>
          </thead>
          <tbody>
            {queue.items.map((item, index) => (
              <tr key={`${item.position}-${item.sellerName}`}>
                <td>{index + 1}</td>
                <td>{item.position}</td>
                <td>
                  <strong>{item.sellerName}</strong>
                </td>
                <td>
                  <span className={`status-badge status-badge--${item.availability}`}>
                    {availabilityLabel(item.availability)}
                  </span>
                </td>
                <td>{availabilityReason(item)}</td>
                <td>{item.skipBalance}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
