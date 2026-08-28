import { redirect } from "next/navigation";
import { AppShell } from "../../components/app-shell";
import { ResourceTable } from "../../components/resource-table";
import { getSessionContext } from "../../lib/auth/session";
import { getDashboardData } from "../../lib/dashboard/queries";

export const dynamic = "force-dynamic";
export default async function QueuePage() {
  const session = await getSessionContext();
  if (session.status !== "authenticated") redirect("/login");
  const data = await getDashboardData(session.sessionToken);
  return <AppShell profile={session.profile} activePath="/fila" eyebrow="Fila comercial" heading="Fila de leads"><ResourceTable title="Fila" items={data.queue.items} /></AppShell>;
}
