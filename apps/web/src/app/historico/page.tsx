import { redirect } from "next/navigation";
import { AppShell } from "../../components/app-shell";
import { ResourceTable } from "../../components/resource-table";
import { getSessionContext } from "../../lib/auth/session";
import { getDashboardData } from "../../lib/dashboard/queries";

export const dynamic = "force-dynamic";
export default async function HistoryPage() {
  const session = await getSessionContext();
  if (session.status !== "authenticated") redirect("/login");
  const data = await getDashboardData(session.sessionToken);
  return <AppShell profile={session.profile} activePath="/historico" eyebrow="Histórico auditável" heading="Histórico"><ResourceTable title="Atribuições" items={data.history.items} /></AppShell>;
}
