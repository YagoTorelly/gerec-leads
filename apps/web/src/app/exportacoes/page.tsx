import { ExportationsPanel } from "../../components/exportations-panel";
import { getExportationHistory } from "../../lib/admin/exportation-queries";
import { getSessionContext } from "../../lib/auth/session";
import { pageNumber } from "../../lib/dashboard/queries";

export const dynamic = "force-dynamic";

export default async function ExportationsPage({
  searchParams,
}: {
  searchParams: Promise<{ page?: string }>;
}) {
  const session = await getSessionContext();
  if (session.status !== "authenticated" || session.profile.role !== "admin") return null;

  const page = pageNumber((await searchParams).page ?? "1");
  const retryHref = page === 1 ? "/exportacoes" : `/exportacoes?page=${page}`;
  let history = null;
  let error: string | null = null;
  try {
    history = await getExportationHistory(session.sessionToken, page);
  } catch {
    error = "Não foi possível carregar o histórico de exportações.";
  }
  return <ExportationsPanel history={history} error={error} retryHref={retryHref} />;
}
