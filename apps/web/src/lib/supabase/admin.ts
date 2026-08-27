import { SupabaseRequestError } from "./rest";

type AdminRuntime = {
  url: string;
  serviceRoleKey: string;
};

function getAdminRuntime(): AdminRuntime {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

  if (!url || !serviceRoleKey) {
    throw new SupabaseRequestError("Supabase local sem chave administrativa no servidor.");
  }

  return {
    url: url.replace(/\/$/, ""),
    serviceRoleKey,
  };
}

export async function supabaseAdminRequest<T>(
  path: string,
  init: RequestInit = {},
  runtime = getAdminRuntime(),
): Promise<T> {
  const response = await fetch(`${runtime.url}${path}`, {
    ...init,
    cache: "no-store",
    headers: {
      apikey: runtime.serviceRoleKey,
      Authorization: `Bearer ${runtime.serviceRoleKey}`,
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
  });

  const body = await response.text();
  const parsed = body ? JSON.parse(body) : null;
  if (!response.ok) {
    throw new SupabaseRequestError(
      parsed?.msg ?? parsed?.message ?? "Supabase administrativo recusou a requisicao.",
      response.status,
    );
  }

  return parsed as T;
}

export async function supabaseAdminRestSelect<T>(path: string) {
  return supabaseAdminRequest<T[]>(`/rest/v1/${path}`, { method: "GET" });
}

export async function supabaseAdminRestUpsert(path: string, body: unknown, prefer?: string) {
  return supabaseAdminRequest(`/rest/v1/${path}`, {
    method: "POST",
    headers: prefer ? { Prefer: prefer } : undefined,
    body: JSON.stringify(body),
  });
}

export async function supabaseAdminRestPatch(path: string, body: unknown) {
  return supabaseAdminRequest(`/rest/v1/${path}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}
