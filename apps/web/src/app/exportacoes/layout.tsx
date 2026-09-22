import { redirect } from "next/navigation";

import { AppShell } from "../../components/app-shell";
import { getSessionContext } from "../../lib/auth/session";

export default async function ExportationsLayout({ children }: { children: React.ReactNode }) {
  const session = await getSessionContext();
  if (session.status !== "authenticated") redirect("/login");
  if (session.profile.role !== "admin") redirect("/dashboard");

  return (
    <AppShell
      profile={session.profile}
      activePath="/exportacoes"
      eyebrow="Administração"
      heading="Exportações"
    >
      {children}
    </AppShell>
  );
}
