import { cookies } from "next/headers";

import { apiRequest, ApiRequestError } from "../../../lib/api/client";
import { SESSION_COOKIE } from "../../../lib/auth/session";

const XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";

export const dynamic = "force-dynamic";

export async function GET(): Promise<Response> {
  const sessionToken = (await cookies()).get(SESSION_COOKIE)?.value;
  if (!sessionToken) return new Response("Sessão expirada. Entre novamente.", { status: 401 });

  try {
    const upstream = await apiRequest("/api/admin/exportations/leads", {
      cache: "no-store",
      headers: { Cookie: `${SESSION_COOKIE}=${sessionToken}` },
    });
    return new Response(upstream.body, {
      status: upstream.status,
      headers: {
        "Cache-Control": "no-store",
        "Content-Type": upstream.headers.get("content-type") ?? XLSX_MEDIA_TYPE,
        "Content-Disposition":
          upstream.headers.get("content-disposition") ?? 'attachment; filename="leads.xlsx"',
      },
    });
  } catch (error) {
    const status =
      error instanceof ApiRequestError && (error.status === 401 || error.status === 403)
        ? error.status
        : 503;
    const message =
      status === 401
        ? "Sessão expirada. Entre novamente."
        : status === 403
          ? "Você não tem permissão para esta ação."
          : "Não foi possível gerar a exportação. Tente novamente.";
    return new Response(message, { status, headers: { "Cache-Control": "no-store" } });
  }
}
