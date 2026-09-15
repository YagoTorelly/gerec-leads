import { redirect } from "next/navigation";

import { AppShell } from "../../components/app-shell";
import { ReportsDashboard } from "../../components/reports-dashboard";
import { getSessionContext } from "../../lib/auth/session";
import { getLeadDistributionReport, reportPeriod, type ReportSearchParams } from "../../lib/reports/queries";

export const dynamic = "force-dynamic";

export default async function ReportsPage({ searchParams }: { searchParams: Promise<ReportSearchParams> }) {
  const session = await getSessionContext();
  if (session.status !== "authenticated" || session.profile.role !== "admin") redirect("/dashboard");
  const period = reportPeriod(await searchParams);
  const report = await getLeadDistributionReport(session.sessionToken, period);
  return (
    <AppShell profile={session.profile} activePath="/relatorios" eyebrow="Leitura gerencial" heading="Relatórios">
      <ReportsDashboard report={report} period={period.key} />
    </AppShell>
  );
}
