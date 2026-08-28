export type UserRole = "admin" | "seller";

export type ApiUser = { id: string; email: string; role: UserRole };

export type Page<T> = { items: T[]; page: number; pageSize: number; total: number };

export type ApiDashboard = {
  user: ApiUser;
  leads: Page<Record<string, unknown>>;
  history: Page<Record<string, unknown>>;
  queue: Page<Record<string, unknown>>;
  skipBalance: Record<string, unknown> | null;
};
