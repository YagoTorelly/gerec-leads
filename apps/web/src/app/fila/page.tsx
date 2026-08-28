import { redirect } from "next/navigation";
import { AppShell } from "../../components/app-shell";
import { Pagination } from "../../components/pagination";
import { ResourceTable } from "../../components/resource-table";
import { getSessionContext } from "../../lib/auth/session";
import { getDashboardData, pageNumber } from "../../lib/dashboard/queries";

export const dynamic = "force-dynamic";
export default async function QueuePage({
  searchParams,
}: {
  searchParams: Promise<{ page?: string }>;
}) {
  const session = await getSessionContext();
  if (session.status !== "authenticated") redirect("/login");
  const page = pageNumber((await searchParams).page ?? "1");
  const data = await getDashboardData(session.sessionToken, page);
  return (
    <AppShell
      profile={session.profile}
      activePath="/fila"
      eyebrow="Fila comercial"
      heading="Fila de leads"
    >
      <ResourceTable title="Fila" items={data.queue.items} />
      <Pagination href="/fila" page={data.queue} />
    </AppShell>
  );
}
