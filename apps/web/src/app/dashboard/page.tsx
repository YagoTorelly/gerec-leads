import { redirect } from "next/navigation";
import { AppShell } from "../../components/app-shell";
import { AdminDashboard, SellerDashboard } from "../../components/dashboards";
import { getSessionContext } from "../../lib/auth/get-session-context";
import { getDashboardData } from "../../lib/dashboard/queries";
export const dynamic = "force-dynamic";
export default async function DashboardPage() {
  const session = await getSessionContext({ onMissingSession: () => redirect("/login") });
  const data = await getDashboardData(session.profile, session.accessToken);
  return (
    <AppShell
      profile={session.profile}
      activePath="/dashboard"
      eyebrow={session.profile.role === "admin" ? "Painel administrativo" : "Minha operação"}
      heading="Visão geral"
    >
      {session.profile.role === "admin" ? (
        <AdminDashboard data={data} profile={session.profile} />
      ) : (
        <SellerDashboard data={data} profile={session.profile} />
      )}
    </AppShell>
  );
}
