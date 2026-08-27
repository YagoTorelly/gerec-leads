import { redirect } from "next/navigation";

import { AppShell } from "../../components/app-shell";
import { QueueView } from "../../components/queue-view";
import { getSessionContext } from "../../lib/auth/get-session-context";
import { getDashboardData } from "../../lib/dashboard/queries";

export const dynamic = "force-dynamic";

export default async function QueuePage() {
  const session = await getSessionContext({ onMissingSession: () => redirect("/login") });
  const data = await getDashboardData(session.profile, session.accessToken);

  return (
    <AppShell
      profile={session.profile}
      activePath="/fila"
      eyebrow="Fila comercial"
      heading={session.profile.role === "admin" ? "Distribuição global de leads" : "Minha posição na fila"}
    >
      <QueueView data={data} profile={session.profile} />
    </AppShell>
  );
}
