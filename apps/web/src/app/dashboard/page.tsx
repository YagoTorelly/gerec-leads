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
      <ResourceTable
        title="Leads"
        items={data.leads.items}
        allowAttempts={session.profile.role === "seller"}
      />
      <Pagination href="/dashboard" page={data.leads} />
    </AppShell>
  );
}
