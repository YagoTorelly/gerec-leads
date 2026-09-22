import { redirect } from "next/navigation";
import type { ManagedUser } from "../../lib/api/types";

import { AdminDashboard } from "../../components/admin-dashboard";
import { AppShell } from "../../components/app-shell";
import { LeadListControls } from "../../components/lead-list-controls";
import { SellerDashboard } from "../../components/seller-dashboard";
import { NewLeadsNotificationModal } from "../../components/new-leads-notification-modal";
import { ManualLeadForm } from "../../components/manual-lead-form";
import { getManagedUsers } from "../../lib/api/client";
import { getSessionContext } from "../../lib/auth/session";
import {
  dashboardListFilters,
  getDashboardData,
  isAdminDashboard,
  pageNumber,
  type DashboardSearchParams,
} from "../../lib/dashboard/queries";
import { getNewLeadNotifications } from "../../lib/notifications/queries";

export const dynamic = "force-dynamic";

export default async function DashboardPage({
  searchParams,
}: {
  searchParams: Promise<DashboardSearchParams>;
}) {
  const session = await getSessionContext();
  if (session.status !== "authenticated") redirect("/login");

  const params = await searchParams;
  const page = pageNumber(typeof params.page === "string" ? params.page : "1");
  const filters = dashboardListFilters(params);
  let dashboard: Awaited<ReturnType<typeof getDashboardData>> | null = null;
  try {
    dashboard = await getDashboardData(session.sessionToken, page, filters);
  } catch {
    // A tela não expõe detalhes internos da falha da API.
  }

  if (dashboard === null) {
    return (
      <AppShell profile={session.profile} activePath="/dashboard" heading="Visão geral">
        <section className="dashboard-panel unavailable-state" aria-live="polite">
          <p className="eyebrow">Dados indisponíveis</p>
          <h2>Não foi possível carregar a visão geral.</h2>
          <p className="dashboard-copy">Tente atualizar a página em alguns instantes.</p>
        </section>
      </AppShell>
    );
  }

  let transferTargets: ManagedUser[] = [];
  const isAdmin = isAdminDashboard(dashboard);
  let newLeadsSnapshot: Awaited<ReturnType<typeof getNewLeadNotifications>> | null = null;
  if (isAdmin) {
    try {
      transferTargets = (await getManagedUsers(session.sessionToken, 1, 200)).items;
    } catch {
      // The dashboard remains readable if the optional transfer target list is unavailable.
    }
  } else {
    try {
      newLeadsSnapshot = await getNewLeadNotifications(session.sessionToken);
    } catch {
      // Falha opcional de notificação não pode impedir o uso do dashboard do vendedor.
    }
  }

  return (
    <AppShell profile={session.profile} activePath="/dashboard" heading="Visão geral">
      {isAdminDashboard(dashboard) ? (
        <>
          <LeadListControls role="admin" sellers={transferTargets} current={filters} />
          <ManualLeadForm latestCampaignDefaults={null} />
          <AdminDashboard dashboard={dashboard} transferTargets={transferTargets} />
        </>
      ) : (
        <>
          <LeadListControls role="seller" sellers={[]} current={filters} />
          <SellerDashboard dashboard={dashboard} />
        </>
      )}
      {!isAdminDashboard(dashboard) && newLeadsSnapshot && newLeadsSnapshot.items.length > 0 ? (
        <NewLeadsNotificationModal snapshot={newLeadsSnapshot} />
      ) : null}
    </AppShell>
  );
}
