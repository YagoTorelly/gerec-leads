import { redirect } from "next/navigation";
import { AppShell } from "../../components/app-shell";
import { AdminControls } from "../../components/admin-controls";
import { Pagination } from "../../components/pagination";
import { ResourceTable } from "../../components/resource-table";
import { getSessionContext } from "../../lib/auth/session";
import { getDashboardData, pageNumber } from "../../lib/dashboard/queries";

export const dynamic = "force-dynamic";
export default async function DashboardPage({
  searchParams,
}: {
  searchParams: Promise<{ page?: string }>;
}) {
  const session = await getSessionContext();
  if (session.status !== "authenticated") redirect("/login");
  const page = pageNumber((await searchParams).page ?? "1");
  const data = await getDashboardData(session.sessionToken, page);
  return (
    <AppShell profile={session.profile} activePath="/dashboard" heading="Visão geral">
      {session.profile.role === "admin" ? <AdminControls /> : null}
      <section className="metrics" aria-label="Resumo operacional">
        <div className="metric green"><span>Total de leads</span><strong>{data.leads.total}</strong></div>
        <div className="metric"><span>Leads exibidos</span><strong>{data.leads.items.length}</strong></div>
        <div className="metric amber"><span>Posições na fila</span><strong>{data.queue.total}</strong></div>
        <div className="metric"><span>Atribuições</span><strong>{data.history.total}</strong></div>
        <div className="metric"><span>Próximo vendedor</span><strong className="metric-text">{String(data.queue.items[0]?.sellerName ?? data.queue.items[0]?.sellerId ?? "—")}</strong></div>
      </section>
      <div className="panel-stack">
        <section className="panel-card"><div className="panel-head"><div><p className="eyebrow">Distribuição</p><h2>Fila comercial</h2></div><a className="inline-link" href="/fila">Ver fila</a></div><div className="queue-grid">{data.queue.items.map((item, index) => <div className="queue-item" key={String(item.id ?? index)}><div className="queue-item-head"><span className="queue-position">#{String(item.position ?? index + 1)}</span><span className={`queue-state ${item.paused ? "paused" : "ready"}`}>{item.paused ? "Pausado" : "Ativo"}</span></div><strong>{String(item.sellerName ?? item.sellerEmail ?? item.sellerId ?? "Vendedor")}</strong><small>{item.paused ? "Fora da distribuição" : "Recebe novos leads"}</small></div>)}</div></section>
        <section className="panel-card"><div className="panel-head"><div><p className="eyebrow">Atividade</p><h2>Últimas atribuições</h2></div><a className="inline-link" href="/historico">Ver histórico</a></div>{data.history.items.slice(0, 5).map((item, index) => <div className="history-item" key={String(item.id ?? index)}><div><strong>Lead {String(item.leadId ?? "")}</strong><small>Vendedor: {String(item.sellerName ?? item.sellerId ?? "—")}</small></div><div className="history-meta"><span>{String(item.type ?? "Normal")}</span><small>{String(item.startedAt ?? "")}</small></div></div>)}</section>
      </div>
      <ResourceTable
        title="Leads"
        items={data.leads.items}
        allowAttempts={session.profile.role === "seller"}
      />
      <Pagination href="/dashboard" page={data.leads} />
    </AppShell>
  );
}
