import { redirect } from "next/navigation";

import { AppShell } from "../../components/app-shell";
import { Pagination } from "../../components/pagination";
import { ResourceTable } from "../../components/resource-table";
import { getSessionContext } from "../../lib/auth/session";
import { getDashboardData, isAdminDashboard, pageNumber } from "../../lib/dashboard/queries";

export const dynamic = "force-dynamic";

function dateLabel(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "Não informado"
    : date.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}

export default async function DashboardPage({
  searchParams,
}: {
  searchParams: Promise<{ page?: string }>;
}) {
  const session = await getSessionContext();
  if (session.status !== "authenticated") redirect("/login");

  const page = pageNumber((await searchParams).page ?? "1");
  const data = await getDashboardData(session.sessionToken, page);
  const adminDashboard = isAdminDashboard(data);

  return (
    <AppShell profile={session.profile} activePath="/dashboard" heading="Visão geral">
      <section className="metrics" aria-label="Resumo operacional">
        <div className="metric green"><span>Total de leads</span><strong>{data.leads.total}</strong></div>
        <div className="metric"><span>Leads exibidos</span><strong>{data.leads.items.length}</strong></div>
        <div className="metric amber"><span>Posições na fila</span><strong>{adminDashboard ? data.queue.total : 1}</strong></div>
        <div className="metric"><span>Tratativas</span><strong>{data.history.total}</strong></div>
        <div className="metric"><span>{adminDashboard ? "Próximo vendedor" : "Sua posição"}</span><strong className="metric-text">{adminDashboard ? data.queue.nextSellerName : String(data.queue.position ?? "Não informado")}</strong></div>
      </section>

      <div className="panel-stack">
        {adminDashboard ? (
          <section className="panel-card">
            <div className="panel-head"><div><p className="eyebrow">Distribuição</p><h2>Fila comercial</h2></div><a className="inline-link" href="/fila">Ver fila</a></div>
            <div className="queue-grid">
              {data.queue.items.map((item) => (
                <div className="queue-item" key={item.sellerName}>
                  <div className="queue-item-head"><span className="queue-position">#{item.position}</span><span className={`queue-state ${item.availability === "paused" ? "paused" : "ready"}`}>{item.availability === "paused" ? "Pausado" : item.availability === "blocked_overdue" ? "Bloqueado por atraso" : "Ativo"}</span></div>
                  <strong>{item.sellerName}</strong><small>{item.reason ?? "Recebe novos leads"}</small>
                </div>
              ))}
            </div>
          </section>
        ) : (
          <section className="panel-card"><p className="eyebrow">Sua fila</p><h2>Posição {data.queue.position ?? "não informada"}</h2><p>{data.queue.availability === "active" ? "Recebe novos leads" : "Indisponível para novas atribuições"}</p></section>
        )}
        <section className="panel-card">
          <div className="panel-head"><div><p className="eyebrow">Atividade</p><h2>Últimas tratativas</h2></div><a className="inline-link" href="/historico">Ver histórico</a></div>
          {data.history.items.slice(0, 5).map((item, index) => (
            <div className="history-item" key={`${item.createdAt}-${index}`}>
              <div><strong>{item.leadName ?? "Lead não informado"}</strong><small>Vendedor: {item.sellerName}</small></div>
              <div className="history-meta"><span>{item.commercialStatus}</span><small>{dateLabel(item.createdAt)}</small></div>
            </div>
          ))}
        </section>
      </div>
      <ResourceTable title="Leads" items={data.leads.items} allowAttempts={session.profile.role === "seller"} />
      <Pagination href="/dashboard" page={data.leads} />
    </AppShell>
  );
}
