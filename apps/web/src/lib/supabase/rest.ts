export type SupabaseRuntime = {
  url: string;
  publishableKey: string;
};

export type SupabaseError = {
  message: string;
  status?: number;
};

export class SupabaseRequestError extends Error {
  status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = "SupabaseRequestError";
    this.status = status;
  }
}

export function getPublicSupabaseRuntime(): SupabaseRuntime | null {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const publishableKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;
  if (!url || !publishableKey || publishableKey === "replace-with-local-public-key") return null;
  return { url: url.replace(/\/$/, ""), publishableKey };
}

export async function supabaseAuthRequest<T>(
  path: string,
  init: RequestInit,
  runtime = getPublicSupabaseRuntime(),
): Promise<T> {
  if (!runtime) throw new SupabaseRequestError("Supabase local ainda nao configurado.");

  const response = await fetch(`${runtime.url}${path}`, {
    ...init,
    cache: "no-store",
    headers: {
      apikey: runtime.publishableKey,
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
  });

  const body = await response.text();
  const parsed = body ? JSON.parse(body) : null;
  if (!response.ok) {
    throw new SupabaseRequestError(
      parsed?.msg ?? parsed?.message ?? "Supabase recusou a requisicao.",
      response.status,
    );
  }

  return parsed as T;
}

export async function supabaseRestSelect<T>(
  path: string,
  accessToken: string,
  runtime = getPublicSupabaseRuntime(),
): Promise<T[]> {
  if (!runtime) throw new SupabaseRequestError("Supabase local ainda nao configurado.");

  const response = await fetch(`${runtime.url}/rest/v1/${path}`, {
    cache: "no-store",
    headers: {
      apikey: runtime.publishableKey,
      Authorization: `Bearer ${accessToken}`,
      Accept: "application/json",
    },
  });

  const body = await response.text();
  const parsed = body ? JSON.parse(body) : null;
  if (!response.ok) {
    throw new SupabaseRequestError(
      parsed?.message ?? "Consulta ao Supabase falhou.",
      response.status,
    );
  }

  return parsed as T[];
}

export function inFilter(values: Array<number | string>) {
  return values.length === 0 ? "(null)" : `(${values.map(String).join(",")})`;
}
