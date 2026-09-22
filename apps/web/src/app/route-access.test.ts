import { renderToStaticMarkup } from "react-dom/server";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { getDashboardData, getManagedUsers, getSessionContext, redirect } = vi.hoisted(() => ({
  getDashboardData: vi.fn(),
  getManagedUsers: vi.fn(),
  getSessionContext: vi.fn(),
  redirect: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  redirect,
  usePathname: () => "/fila",
  useRouter: () => ({ push: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
}));
vi.mock("../lib/auth/session", () => ({ getSessionContext }));
vi.mock("../lib/api/client", () => ({ getManagedUsers }));
vi.mock("../lib/dashboard/queries", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../lib/dashboard/queries")>()),
  getDashboardData,
}));

import DashboardPage from "./dashboard/page";
import QueuePage from "./fila/page";
import HistoryPage from "./historico/page";

const sellerSession = {
  status: "authenticated" as const,
  sessionToken: "seller-session",
  profile: {
    id: "seller-1",
    userId: "seller-1",
    fullName: "Jessica",
    email: "jessica@wtgseguros.com.br",
    role: "seller" as const,
  },
};

describe("proteção das rotas operacionais", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    redirect.mockImplementation((target: string) => {
      throw new Error(`REDIRECT:${target}`);
    });
  });

  it("permite ao vendedor abrir suas próprias tratativas por URL", async () => {
    getSessionContext.mockResolvedValue(sellerSession);
    getDashboardData.mockResolvedValue({
      user: { id: "seller-1", email: sellerSession.profile.email, role: "seller" },
      leads: { items: [], page: 1, pageSize: 50, total: 0 },
      history: { items: [], page: 1, pageSize: 50, total: 0 },
      queue: { position: 2, availability: "active", skipBalance: 0 },
    });

    const markup = renderToStaticMarkup(await HistoryPage({ searchParams: Promise.resolve({}) }));
    expect(markup).toContain("Minhas tratativas");
    expect(markup).toContain("Nenhuma tratativa registrada.");
    expect(redirect).not.toHaveBeenCalled();
  });

  it("permite ao vendedor abrir sua fila por URL sem dados globais", async () => {
    getSessionContext.mockResolvedValue(sellerSession);
    getDashboardData.mockResolvedValue({
      user: { id: "seller-1", email: sellerSession.profile.email, role: "seller" },
      leads: { items: [], page: 1, pageSize: 50, total: 0 },
      history: { items: [], page: 1, pageSize: 50, total: 0 },
      queue: { position: 3, availability: "active", skipBalance: 0 },
    });

    const markup = renderToStaticMarkup(await QueuePage({ searchParams: Promise.resolve({}) }));
    expect(markup).toContain("Minha fila");
    expect(markup).toContain("Posição 3");
    expect(markup).not.toContain("Fila comercial");
    expect(redirect).not.toHaveBeenCalled();
  });

  it("renderiza um estado seguro quando a API não disponibiliza o dashboard", async () => {
    getSessionContext.mockResolvedValue({
      ...sellerSession,
      profile: { ...sellerSession.profile, role: "admin" as const },
    });
    getDashboardData.mockRejectedValue(new Error("INTERNAL_DETAIL_X"));

    const markup = renderToStaticMarkup(await DashboardPage({ searchParams: Promise.resolve({}) }));

    expect(markup).toContain("Não foi possível carregar a visão geral.");
    expect(markup).toContain("Tente atualizar a página em alguns instantes.");
    expect(markup).not.toContain("INTERNAL_DETAIL_X");
  });

  it("mostra o cadastro manual no dashboard administrativo", async () => {
    getSessionContext.mockResolvedValue({
      ...sellerSession,
      profile: { ...sellerSession.profile, role: "admin" as const },
    });
    getDashboardData.mockResolvedValue({
      user: { id: "admin-1", email: "yago@wtgseguros.com.br", role: "admin" },
      leads: { items: [], page: 1, pageSize: 50, total: 0 },
      history: { items: [], page: 1, pageSize: 50, total: 0 },
      queue: { position: 1, availability: "active", skipBalance: 0, items: [] },
    });
    getManagedUsers.mockResolvedValue({ items: [], page: 1, pageSize: 200, total: 0 });

    const markup = renderToStaticMarkup(await DashboardPage({ searchParams: Promise.resolve({}) }));

    expect(markup).toContain("Adicionar leads");
  });
});
