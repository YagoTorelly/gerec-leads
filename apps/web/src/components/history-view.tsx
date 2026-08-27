import type { DashboardData } from "../lib/dashboard/types";
import { formatDateTime } from "../lib/dashboard/format";

export function HistoryView({ data }: { data: DashboardData }) {
  return (
    <>
      <div className="notice">
        {data.warning ?? "Linha do tempo dos contatos, feedbacks, qualificações e negócios ganhos."}
      </div>
      <section className="panel-card">
        <div className="panel-head">
          <div>
            <p className="eyebrow">Rastro operacional</p>
            <h2>Histórico completo</h2>
          </div>
          <span className={`data-badge ${data.source}`}>
            {data.source === "supabase" ? "Dados ao vivo" : "Modo demonstração"}
          </span>
        </div>
        <table>
          <thead>
            <tr>
              <th>Evento</th>
              <th>Lead</th>
              <th>Responsável</th>
              <th>Comentário</th>
              <th>Quando</th>
            </tr>
          </thead>
          <tbody>
            {data.history.map((event) => (
              <tr key={event.id}>
                <td>
                  <strong>{event.label}</strong>
                  <small>{event.eventType}</small>
                </td>
                <td>
                  <strong>{event.contactName}</strong>
                  <small>{event.companyName}</small>
                </td>
                <td>{event.sellerName}</td>
                <td>{event.comment}</td>
                <td>{formatDateTime(event.happenedAt)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {data.history.length === 0 ? <div className="empty">Nenhum evento disponível para este perfil.</div> : null}
      </section>
    </>
  );
}
