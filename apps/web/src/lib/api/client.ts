import type {
  CreateManagedUserInput,
  ManagedUser,
  Page,
  Treatment,
  TreatmentInput,
  TreatmentSubmission,
} from "./types";

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

function messageForStatus(status: number): string {
  switch (status) {
    case 401:
      return "Sessão expirada. Entre novamente.";
    case 403:
      return "Você não tem permissão para esta ação.";
    case 409:
      return "A operação conflita com o estado atual. Atualize os dados e tente novamente.";
    case 422:
      return "Revise os dados informados e tente novamente.";
    default:
      return "Não foi possível concluir a solicitação.";
  }
}

async function errorMessage(response: Response): Promise<string> {
  // O corpo de erro é um contrato técnico da API. Nunca o exponha ao usuário:
  // pode conter termos internos, texto em outro idioma ou dados sensíveis.
  return messageForStatus(response.status);
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

/** Único ponto de entrada HTTP da interface; as regras permanecem na API. */
export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await apiRequest(path, init);
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

function sessionHeaders(sessionToken: string, headers: HeadersInit = {}): HeadersInit {
  return {
    "Content-Type": "application/json",
    Cookie: `gerec_session=${sessionToken}`,
    ...headers,
  };
}

function managedUser(value: unknown): ManagedUser {
  if (typeof value !== "object" || value === null) {
    throw new ApiRequestError("A resposta de usuários é inválida.", 502);
  }
  const record = value as Record<string, unknown>;
  const email = text(record.email) ?? text(record.emailNormalized);
  const fullName = text(record.fullName);
  const id = text(record.id);
  const role = record.role;
  if (
    !id ||
    !fullName ||
    !email ||
    (role !== "admin" && role !== "seller") ||
    typeof record.active !== "boolean"
  ) {
    throw new ApiRequestError("A resposta de usuários é inválida.", 502);
  }
  return {
    id,
    fullName,
    email,
    role,
    active: record.active,
    paused: typeof record.paused === "boolean" ? record.paused : null,
  };
}

function text(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function managedUserPage(value: unknown): Page<ManagedUser> {
  if (typeof value !== "object" || value === null) {
    throw new ApiRequestError("A resposta de usuários é inválida.", 502);
  }
  const page = value as Record<string, unknown>;
  if (
    !Array.isArray(page.items) ||
    typeof page.page !== "number" ||
    !Number.isInteger(page.page) ||
    typeof page.pageSize !== "number" ||
    !Number.isInteger(page.pageSize) ||
    typeof page.total !== "number" ||
    !Number.isInteger(page.total)
  ) {
    throw new ApiRequestError("A resposta de usuários é inválida.", 502);
  }
  return {
    items: page.items.map(managedUser),
    page: page.page,
    pageSize: page.pageSize,
    total: page.total,
  };
}

export async function getManagedUsers(
  sessionToken: string,
  page = 1,
  limit = 50,
): Promise<Page<ManagedUser>> {
  return managedUserPage(
    await apiFetch<unknown>(`/api/admin/users?page=${page}&limit=${limit}`, {
      cache: "no-store",
      headers: { Cookie: `gerec_session=${sessionToken}` },
    }),
  );
}

export async function createManagedUser(
  input: CreateManagedUserInput,
  sessionToken: string,
): Promise<ManagedUser> {
  return managedUser(
    await apiFetch<unknown>("/api/admin/users", {
      method: "POST",
      headers: sessionHeaders(sessionToken),
      body: JSON.stringify(input),
    }),
  );
}

export async function setManagedUserAvailability(
  userId: string,
  paused: boolean,
  sessionToken: string,
): Promise<ManagedUser> {
  return managedUser(
    await apiFetch<unknown>(`/api/admin/users/${encodeURIComponent(userId)}/availability`, {
      method: "PATCH",
      headers: sessionHeaders(sessionToken),
      body: JSON.stringify({ paused }),
    }),
  );
}

export async function resetManagedUserPassword(
  userId: string,
  password: string,
  sessionToken: string,
): Promise<ManagedUser> {
  return managedUser(
    await apiFetch<unknown>(`/api/admin/users/${encodeURIComponent(userId)}/password`, {
      method: "PATCH",
      headers: sessionHeaders(sessionToken),
      body: JSON.stringify({ password }),
    }),
  );
}

export async function submitLeadTreatment(
  leadId: string,
  input: TreatmentInput,
  sessionToken: string,
): Promise<TreatmentSubmission> {
  return apiFetch<TreatmentSubmission>(`/api/leads/${encodeURIComponent(leadId)}/treatments`, {
    method: "POST",
    headers: sessionHeaders(sessionToken),
    body: JSON.stringify(input),
  });
}

export async function getLeadTreatments(
  leadId: string,
  sessionToken: string,
  page = 1,
  limit = 50,
): Promise<Page<Treatment>> {
  return apiFetch<Page<Treatment>>(
    `/api/leads/${encodeURIComponent(leadId)}/treatments?page=${page}&limit=${limit}`,
    {
      cache: "no-store",
      headers: { Cookie: `gerec_session=${sessionToken}` },
    },
  );
}

export async function transferLeadOwnership(
  leadId: string,
  sellerId: string,
  reason: string,
  commandId: string,
  sessionToken: string,
): Promise<{ leadId: string; sellerId: string; status: string }> {
  return apiFetch(`/api/admin/leads/${encodeURIComponent(leadId)}/transfer-owner`, {
    method: "POST",
    headers: sessionHeaders(sessionToken),
    body: JSON.stringify({ seller_id: sellerId, reason, command_id: commandId, confirmed: true }),
  });
}
