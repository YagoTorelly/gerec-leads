import { redirect } from "next/navigation";

import { AppShell } from "../../components/app-shell";
import { HistoryView } from "../../components/history-view";
import { getSessionContext } from "../../lib/auth/get-session-context";
import { getDashboardData } from "../../lib/dashboard/queries";

export const dynamic = "force-dynamic";

export default async function HistoryPage() {
  const session = await getSessionContext({ onMissingSession: () => redirect("/login") });
  const data = await getDashboardData(session.profile, session.accessToken);

  return (
    <AppShell
      profile={session.profile}
      activePath="/historico"
      eyebrow="Histórico auditável"
      heading={session.profile.role === "admin" ? "Linha do tempo da operação" : "Linha do tempo dos meus leads"}
    >
      <HistoryView data={data} />
    </AppShell>
  );
}
