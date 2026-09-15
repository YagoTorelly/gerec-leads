import { redirect } from "next/navigation";

import { AppShell } from "../../components/app-shell";
import { ReportsDashboard } from "../../components/reports-dashboard";
import { getSessionContext } from "../../lib/auth/session";
import {
  getLeadDistributionReport,
  isReportPeriod,
  reportPeriod,
  type ReportSearchParams,
} from "../../lib/reports/queries";

export const dynamic = "force-dynamic";

export default async function ReportsPage({ searchParams }: { searchParams: Promise<ReportSearchParams> }) {
  const session = await getSessionContext();
  if (session.status !== "authenticated" || session.profile.role !== "admin") redirect("/dashboard");

  const period = reportPeriod(await searchParams);
  let report = null;
  let error: string | null = null;
  if (isReportPeriod(period)) {
    try {
      report = await getLeadDistributionReport(session.sessionToken, period);
    } catch {
      error = "Não foi possível carregar os relatórios. Tente novamente.";
    }
  } else {
    error = period.error;
  }

  return (
    <AppShell profile={session.profile} activePath="/relatorios" eyebrow="Leitura gerencial" heading="Relatórios">
      <ReportsDashboard
        report={report}
        period={period.key}
        error={error}
        from={isReportPeriod(period) ? undefined : period.from}
        to={isReportPeriod(period) ? undefined : period.to}
        interval={isReportPeriod(period) ? { from: period.fromAt, to: period.toAt } : undefined}
      />
    </AppShell>
  );
}
