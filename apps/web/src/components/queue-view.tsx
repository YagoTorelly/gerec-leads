import type { DashboardData, SessionProfile } from "../lib/dashboard/types";
import { formatDateTime } from "../lib/dashboard/format";
import { LeadOperationsTable } from "./dashboards";

export function QueueView({
  data,
  profile,
}: {
  data: DashboardData;
  profile: SessionProfile;
}) {
  return (
    <>
      <div className="notice">
        {data.warning ??
          (profile.role === "admin"
            ? "Fila completa com elegibilidade, créditos e SLA por vendedor."
            : "Sua posição na fila e seus prazos de atendimento em tempo real.")}
      </div>
      <section className="panel-card">
        <div className="panel-head">
          <div>
            <p className="eyebrow">Ordem operacional</p>
            <h2>{profile.role === "admin" ? "Fila de distribuição" : "Minha posição atual"}</h2>
          </div>
          <span className={`data-badge ${data.source}`}>
            {data.source === "supabase" ? "Dados ao vivo" : "Modo demonstração"}
          </span>
        </div>
        <table>
          <thead>
            <tr>
              <th>Posição</th>
              <th>Vendedor</th>
              <th>Status</th>
              <th>Leads ativos</th>
              <th>Atrasados</th>
              <th>Próximo prazo</th>
              <th>Créditos</th>
            </tr>
          </thead>
          <tbody>
            {data.queue.map((entry) => (
              <tr key={entry.sellerId}>
                <td>#{entry.position}</td>
                <td>
                  <strong>{entry.sellerName}</strong>
                  <small>{entry.email}</small>
                </td>
                <td>
                  <span className={`queue-state ${entry.isPaused ? "paused" : "ready"}`}>
                    {entry.isPaused ? "Pausado" : "Elegível"}
                  </span>
                </td>
                <td>{entry.activeLeads}</td>
                <td>{entry.overdueLeads}</td>
                <td>{entry.nextDueAt ? formatDateTime(entry.nextDueAt) : "Sem SLA aberto"}</td>
                <td>{entry.skipBalance}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <LeadOperationsTable
        data={data}
        title={profile.role === "admin" ? "Leads que impactam a fila" : "Leads que impactam sua fila"}
      />
    </>
  );
}
