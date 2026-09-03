import { redirect } from "next/navigation";
import type { ManagedUser } from "../../lib/api/types";

import { AdminDashboard } from "../../components/admin-dashboard";
import { AppShell } from "../../components/app-shell";
import { SellerDashboard } from "../../components/seller-dashboard";
import { getManagedUsers } from "../../lib/api/client";
import { getSessionContext } from "../../lib/auth/session";
import { getDashboardData, isAdminDashboard, pageNumber } from "../../lib/dashboard/queries";

export const dynamic = "force-dynamic";

export default async function DashboardPage({
  searchParams,
}: {
  searchParams: Promise<{ page?: string }>;
}) {
  const session = await getSessionContext();
  if (session.status !== "authenticated") redirect("/login");

  const page = pageNumber((await searchParams).page ?? "1");
  let dashboard: Awaited<ReturnType<typeof getDashboardData>> | null = null;
  try {
    dashboard = await getDashboardData(session.sessionToken, page);
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
  if (isAdminDashboard(dashboard)) {
    try {
      transferTargets = (await getManagedUsers(session.sessionToken, 1, 200)).items;
    } catch {
      // The dashboard remains readable if the optional transfer target list is unavailable.
    }
  }

  return (
    <AppShell profile={session.profile} activePath="/dashboard" heading="Visão geral">
      {isAdminDashboard(dashboard) ? (
        <AdminDashboard dashboard={dashboard} transferTargets={transferTargets} />
      ) : (
        <SellerDashboard dashboard={dashboard} />
      )}
    </AppShell>
  );
}
