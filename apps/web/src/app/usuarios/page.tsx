import { redirect } from "next/navigation";
import { AppShell } from "../../components/app-shell";
import { Pagination } from "../../components/pagination";
import { UserManagement } from "../../components/user-management";
import { apiFetch } from "../../lib/api/client";
import type { Page } from "../../lib/api/types";
import { getSessionContext, SESSION_COOKIE } from "../../lib/auth/session";
import { pageNumber } from "../../lib/dashboard/queries";

export const dynamic = "force-dynamic";
export default async function UsersPage({
  searchParams,
}: {
  searchParams: Promise<{ page?: string }>;
}) {
  const session = await getSessionContext();
  if (session.status !== "authenticated" || session.profile.role !== "admin")
    redirect("/dashboard");
  const page = pageNumber((await searchParams).page ?? "1");
  const users = await apiFetch<Page<Record<string, unknown>>>(
    `/api/admin/users?page=${page}&limit=50`,
    { cache: "no-store", headers: { Cookie: `${SESSION_COOKIE}=${session.sessionToken}` } },
  );
  return (
    <AppShell
      profile={session.profile}
      activePath="/usuarios"
      eyebrow="Administração"
      heading="Usuários"
    >
      <UserManagement users={users.items} />
      <Pagination href="/usuarios" page={users} />
    </AppShell>
  );
}
