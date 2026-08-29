import { redirect } from "next/navigation";

import { AdminDashboard } from "../../components/admin-dashboard";
import { AppShell } from "../../components/app-shell";
import { SellerDashboard } from "../../components/seller-dashboard";
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
  const dashboard = await getDashboardData(session.sessionToken, page);

  return (
    <AppShell profile={session.profile} activePath="/dashboard" heading="Visão geral">
      {isAdminDashboard(dashboard) ? <AdminDashboard dashboard={dashboard} /> : <SellerDashboard dashboard={dashboard} />}
    </AppShell>
  );
}
