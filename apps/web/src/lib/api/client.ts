export class ApiRequestError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiRequestError";
  }
}

function apiUrl(path: string): string {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "");
  if (!baseUrl) {
    throw new ApiRequestError("API do Gerenciador de Leads não configurada.", 503);
  }
  return `${baseUrl}/${path.replace(/^\//, "")}`;
}

async function errorMessage(response: Response): Promise<string> {
  try {
    const payload: unknown = await response.json();
    if (typeof payload === "object" && payload !== null && "detail" in payload) {
      const detail = payload.detail;
      return typeof detail === "string" ? detail : "Dados inválidos.";
    }
  } catch {
    // A API pode responder sem corpo em erros HTTP.
  }
  return response.status === 401
    ? "Sessão expirada. Entre novamente."
    : response.status === 403
      ? "Você não tem permissão para esta ação."
      : "Não foi possível concluir a solicitação.";
}

export async function apiRequest(path: string, init: RequestInit = {}): Promise<Response> {
  const response = await fetch(apiUrl(path), {
    ...init,
    credentials: "include",
    headers: {
      Accept: "application/json",
      ...init.headers,
    },
  });
  if (!response.ok) throw new ApiRequestError(await errorMessage(response), response.status);
  return response;
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await apiRequest(path, init);
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}
