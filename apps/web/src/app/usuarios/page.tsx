import { redirect } from "next/navigation";

import { AppShell } from "../../components/app-shell";
import { Pagination } from "../../components/pagination";
import { UserManagement } from "../../components/user-management";
import { getManagedUsers } from "../../lib/api/client";
import { getSessionContext } from "../../lib/auth/session";
import { pageNumber } from "../../lib/dashboard/queries";

export const dynamic = "force-dynamic";

export default async function UsersPage({
  searchParams,
}: {
  searchParams: Promise<{ page?: string }>;
}) {
  const session = await getSessionContext();
  if (session.status !== "authenticated" || session.profile.role !== "admin") redirect("/dashboard");

  const page = pageNumber((await searchParams).page ?? "1");
  const users = await getManagedUsers(session.sessionToken, page);

  return (
    <AppShell profile={session.profile} activePath="/usuarios" eyebrow="Administração" heading="Usuários">
      <UserManagement key={`users-page-${users.page}`} users={users.items} page={users.page} />
      <Pagination href="/usuarios" page={users} />
    </AppShell>
  );
}
