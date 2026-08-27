export type SupabaseHealth = {
  status: "connected" | "not_configured" | "unavailable";
  message: string;
};

export type HealthRequest = (input: string, init?: RequestInit) => Promise<Response>;

type HealthConfig = {
  url: string | undefined;
  publishableKey: string | undefined;
};

export async function checkSupabaseHealth(
  config: HealthConfig = {
    url: process.env.NEXT_PUBLIC_SUPABASE_URL,
    publishableKey: process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY,
  },
  request: HealthRequest = fetch,
): Promise<SupabaseHealth> {
  if (!config.url || !config.publishableKey) {
    return {
      status: "not_configured",
      message: "Supabase local ainda não configurado",
    };
  }

  try {
    const response = await request(`${config.url.replace(/\/$/, "")}/auth/v1/health`, {
      cache: "no-store",
      headers: { apikey: config.publishableKey },
    });

    if (response.ok) {
      return { status: "connected", message: "Supabase local conectado" };
    }
  } catch {
    // O estado de indisponibilidade é exibido sem registrar URL, chave ou payload.
  }

  return {
    status: "unavailable",
    message: "Supabase local indisponível",
  };
}
