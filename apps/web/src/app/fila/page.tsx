import { redirect } from "next/navigation";
import type { ManagedUser } from "../../lib/api/types";

import { AppShell } from "../../components/app-shell";
import { LeadListControls } from "../../components/lead-list-controls";
import { LeadTable } from "../../components/lead-table";
import { Pagination } from "../../components/pagination";
import { QueueTable } from "../../components/queue-table";
import { SellerQueueTable } from "../../components/seller-queue-table";
import { getSessionContext } from "../../lib/auth/session";
import {
  dashboardListFilters,
  getDashboardData,
  isAdminDashboard,
  pageNumber,
  type DashboardSearchParams,
} from "../../lib/dashboard/queries";
import { getManagedUsers } from "../../lib/api/client";

export const dynamic = "force-dynamic";

export default async function QueuePage({
  searchParams,
}: {
  searchParams: Promise<DashboardSearchParams>;
}) {
  const params = await searchParams;
  const session = await getSessionContext();
  if (session.status !== "authenticated") redirect("/login");
  const page = pageNumber(typeof params.page === "string" ? params.page : "1");
  const filters = dashboardListFilters(params);
  const data = await getDashboardData(session.sessionToken, page, filters);
  if (!isAdminDashboard(data)) {
    return (
      <AppShell
        profile={session.profile}
        activePath="/fila"
        eyebrow="Minha distribuição"
        heading="Minha fila"
      >
        <LeadListControls role="seller" sellers={[]} current={filters} />
        <SellerQueueTable queue={data.queue} leads={data.leads.items} />
        <Pagination href="/fila" page={data.leads} searchParams={params} />
      </AppShell>
    );
  }

  let transferTargets: ManagedUser[] = [];
  try {
    transferTargets = (await getManagedUsers(session.sessionToken, 1, 200)).items;
  } catch {
    // Keep the read-only queue available if target loading fails.
  }

  return (
    <AppShell
      profile={session.profile}
      activePath="/fila"
      eyebrow="Fila comercial"
      heading="Fila de leads"
    >
      <QueueTable queue={data.queue} />
      <LeadListControls role="admin" sellers={transferTargets} current={filters} />
      <LeadTable leads={data.leads.items} role="admin" transferTargets={transferTargets} />
      <Pagination href="/fila" page={data.leads} searchParams={params} />
    </AppShell>
  );
}
