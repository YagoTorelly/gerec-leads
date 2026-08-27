import { redirect } from "next/navigation";

import { AppShell } from "../../components/app-shell";
import { UserManagement } from "../../components/user-management";
import { getSessionContext } from "../../lib/auth/get-session-context";
import { getDashboardData } from "../../lib/dashboard/queries";

export const dynamic = "force-dynamic";

export default async function UsersPage({
  searchParams,
}: {
  searchParams: Promise<{ notice?: string }>;
}) {
  const session = await getSessionContext({ onMissingSession: () => redirect("/login") });
  if (session.profile.role !== "admin") {
    redirect("/dashboard");
  }

  const data = await getDashboardData(session.profile, session.accessToken);
  const resolvedSearchParams = await searchParams;
  const notice = resolvedSearchParams.notice ? decodeURIComponent(resolvedSearchParams.notice) : undefined;

  return (
    <AppShell
      profile={session.profile}
      activePath="/usuarios"
      eyebrow="Administração local"
      heading="Usuários e posições da fila"
    >
      <UserManagement data={data} notice={notice} />
    </AppShell>
  );
}
