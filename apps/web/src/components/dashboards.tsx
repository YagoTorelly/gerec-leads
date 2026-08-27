import type { DashboardData, SessionProfile } from "../lib/dashboard/types";
import { formatDateTime } from "../lib/dashboard/format";
import { registerContactAttemptAction } from "../lib/operations/actions";
import { simulateLeadsAction } from "../lib/admin/simulation-actions";
import { ConfirmArchiveButton } from "./confirm-archive-button";
import { AttemptModal } from "./attempt-modal";

function Metric({ label, value, tone = "" }: { label: string; value: number; tone?: string }) {
  return (
    <div className={`metric ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function Notice({ data, fallback }: { data: DashboardData; fallback: string }) {
  return <div className="notice">{data.warning ?? fallback}</div>;
}

export function LeadOperationsTable({ data, title, canRegister = false, canRemove = false }: { data: DashboardData; title: string; canRegister?: boolean; canRemove?: boolean }) {
  return (
    <section className="table-card">
      <div className="table-head">
        <div>
          <p className="eyebrow">Operação comercial</p>
          <h2>{title}</h2>
        </div>
        <span className={`data-badge ${data.source}`}>
          {data.source === "supabase" ? "Dados ao vivo" : "Modo demonstração"}
        </span>
      </div>
      <table>
        <thead>
          <tr>
            <th>Lead / contato</th>
            <th>Empresa</th>
            <th>Vendedor</th>
            <th>Próximo prazo</th>
            <th>Status</th>
            <th>Tentativas</th>
            {canRemove && !canRegister ? <th>Ação</th> : null}
            {canRegister ? <th>Ação</th> : null}
          </tr>
        </thead>
        <tbody>
          {data.leads.map((lead) => (
            <tr key={lead.id}>
              <td>
                <strong>{lead.contactName}</strong>
                <small>
                  {lead.phone} · {lead.email}
                </small>
              </td>
              <td>
                {lead.companyName}
                <small>{lead.campaignName}</small>
              </td>
              <td>{lead.sellerName}</td>
              <td>
                <span className={`sla ${lead.stage}`}>
                  {lead.stage === "overdue"
                    ? "Atrasado"
                    : lead.stage === "today"
                      ? "Vence hoje"
                      : lead.feedbackDueAt
                        ? formatDateTime(lead.feedbackDueAt)
                        : "Sem prazo"}
                </span>
                <small>{lead.feedbackDueAt ? formatDateTime(lead.feedbackDueAt) : "Sem SLA"}</small>
              </td>
              <td>
                <span className={`pill commercial-status ${lead.commercialStatus}`}>
                  {lead.commercialStatus === "negotiation" ? "Negociação" : lead.commercialStatus === "won" ? "Ganho" : lead.commercialStatus === "disqualified" ? "Desqualificado" : "Indefinido"}
                </span>
                <span className={`pill commercial-status ${lead.commercialStatus}`}>
                  {lead.conversionStatus === "won"
                    ? "Ganho"
                    : lead.qualificationStatus === "disqualified"
                      ? "Desqualificado"
                      : lead.qualificationStatus === "qualified"
                        ? "Qualificado"
                        : "Em andamento"}
                </span>
              </td>
              <td>{lead.attemptsCount}</td>
              {canRegister || canRemove ? <td>
                {canRemove ? <ConfirmArchiveButton leadId={lead.id} contactName={lead.contactName} /> : <AttemptModal leadId={lead.id} contactName={lead.contactName} attempts={lead.attemptsCount} status={lead.commercialStatus} />}
                {canRemove ? null : lead.attemptsCount >= 5 ? (
                  <span className="muted">Limite atingido</span>
                ) : (
                  <form className="attempt-form" action={registerContactAttemptAction}>
                    <input type="hidden" name="leadId" value={lead.id} />
                    <input name="comment" required minLength={6} placeholder="Comentário" aria-label={`Comentário para ${lead.contactName}`} />
                    <button type="submit">Registrar</button>
                  </form>
                )}
              </td> : null}
            </tr>
          ))}
        </tbody>
      </table>
      {data.leads.length === 0 ? (
        <div className="empty">Nenhum lead disponível para este perfil.</div>
      ) : null}
    </section>
  );
}

export function QueuePanel({ data, profile }: { data: DashboardData; profile: SessionProfile }) {
  return (
    <section className="panel-card">
      <div className="panel-head">
        <div>
          <p className="eyebrow">Fila global</p>
          <h2>{profile.role === "admin" ? "Estado dos vendedores" : "Minha posição na fila"}</h2>
        </div>
        <a className="inline-link" href="/fila">
          Abrir fila
        </a>
      </div>
      <div className="queue-grid">
        {data.queue.map((entry) => (
          <article className="queue-item" key={entry.sellerId}>
            <div className="queue-item-head">
              <span className="queue-position">#{entry.position}</span>
              <span className={`queue-state ${entry.isPaused ? "paused" : "ready"}`}>
                {entry.isPaused ? "Pausado" : "Elegível"}
              </span>
            </div>
            <strong>{entry.sellerName}</strong>
            <small>{entry.email}</small>
            <dl>
              <div>
                <dt>Leads ativos</dt>
                <dd>{entry.activeLeads}</dd>
              </div>
              <div>
                <dt>Atrasados</dt>
                <dd>{entry.overdueLeads}</dd>
              </div>
              <div>
                <dt>Créditos</dt>
                <dd>{entry.skipBalance}</dd>
              </div>
            </dl>
          </article>
        ))}
      </div>
    </section>
  );
}

export function HistoryPanel({ data }: { data: DashboardData }) {
  return (
    <section className="panel-card">
      <div className="panel-head">
        <div>
          <p className="eyebrow">Atividade recente</p>
          <h2>Últimos movimentos</h2>
        </div>
        <a className="inline-link" href="/historico">
          Abrir histórico
        </a>
      </div>
      <div className="history-list">
        {data.history.slice(0, 4).map((event) => (
          <article className="history-item" key={event.id}>
            <div>
              <strong>{event.label}</strong>
              <small>
                {event.contactName} · {event.companyName}
              </small>
            </div>
            <div className="history-meta">
              <span>{event.sellerName}</span>
              <small>{formatDateTime(event.happenedAt)}</small>
            </div>
          </article>
        ))}
      </div>
      {data.history.length === 0 ? (
        <div className="empty compact">Nenhuma atividade registrada ainda.</div>
      ) : null}
    </section>
  );
}

export function AdminDashboard({
  data,
  profile,
}: {
  data: DashboardData;
  profile: SessionProfile;
}) {
  return (
    <>
      <Notice data={data} fallback="Ambiente local sincronizado. Horários em America/Sao_Paulo." />
      <form className="simulation-bar" action={simulateLeadsAction}>
        <div><strong>Simular entrada de leads</strong><small>Testa a distribuição pulando vendedores pausados ou bloqueados.</small></div>
        <input name="quantity" type="number" min="1" max="10" defaultValue="1" aria-label="Quantidade de leads" />
        <button type="submit">Simular leads</button>
      </form>
      <section className="metrics">
        <Metric label="Total de leads" value={data.summary.total} />
        <Metric label="Em distribuição" value={data.summary.queued} />
        <Metric label="Feedbacks hoje" value={data.summary.feedbacksToday} tone="amber" />
        <Metric label="Atrasados" value={data.summary.overdue} tone="red" />
        <Metric label="Negócios ganhos" value={data.summary.won} tone="green" />
      </section>
      <div className="panel-stack">
        <QueuePanel data={data} profile={profile} />
        <HistoryPanel data={data} />
      </div>
      <LeadOperationsTable data={data} title="Leads em acompanhamento" canRemove />
    </>
  );
}

export function SellerDashboard({
  data,
  profile,
}: {
  data: DashboardData;
  profile: SessionProfile;
}) {
  return (
    <>
      <Notice
        data={data}
        fallback={`Carteira de ${profile.fullName} · Horários em America/Sao_Paulo.`}
      />
      <section className="metrics">
        <Metric label="Minha carteira" value={data.summary.total} />
        <Metric label="Feedbacks hoje" value={data.summary.feedbacksToday} tone="amber" />
        <Metric label="Atrasados" value={data.summary.overdue} tone="red" />
        <Metric label="Tentativas" value={data.summary.attempts} />
        <Metric label="Ganhos" value={data.summary.won} tone="green" />
      </section>
      <div className="panel-stack">
        <QueuePanel data={data} profile={profile} />
        <HistoryPanel data={data} />
      </div>
      <LeadOperationsTable data={data} title="Meus leads em acompanhamento" canRegister />
    </>
  );
}
