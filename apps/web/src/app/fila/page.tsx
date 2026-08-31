import { redirect } from "next/navigation";

import { AppShell } from "../../components/app-shell";
import { LeadTable } from "../../components/lead-table";
import { Pagination } from "../../components/pagination";
import { QueueTable } from "../../components/queue-table";
import { getSessionContext } from "../../lib/auth/session";
import { getDashboardData, isAdminDashboard, pageNumber } from "../../lib/dashboard/queries";

export const dynamic = "force-dynamic";

export default async function QueuePage({
  searchParams,
}: {
  searchParams: Promise<{ page?: string }>;
}) {
  const params = await searchParams;
  const session = await getSessionContext();
  if (session.status !== "authenticated") redirect("/login");
  if (session.profile.role !== "admin") redirect("/dashboard");

  const page = pageNumber(params.page ?? "1");
  const data = await getDashboardData(session.sessionToken, page);
  if (!isAdminDashboard(data)) redirect("/dashboard");

  return (
    <AppShell
      profile={session.profile}
      activePath="/fila"
      eyebrow="Fila comercial"
      heading="Fila de leads"
    >
      <QueueTable queue={data.queue} />
      <LeadTable leads={data.leads.items} role="admin" />
      <Pagination href="/fila" page={data.leads} searchParams={params} />
    </AppShell>
  );
}
