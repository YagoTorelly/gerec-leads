import { renderToStaticMarkup } from "react-dom/server";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { getExportationHistory, getSessionContext, redirect } = vi.hoisted(() => ({
  getExportationHistory: vi.fn(),
  getSessionContext: vi.fn(),
  redirect: vi.fn(),
}));

vi.mock("next/image", () => ({ default: () => <span /> }));
vi.mock("next/navigation", () => ({ redirect }));
vi.mock("../../lib/auth/actions", () => ({ signOutAction: vi.fn() }));
vi.mock("../../lib/auth/session", () => ({ getSessionContext }));
vi.mock("../../lib/admin/exportation-queries", () => ({ getExportationHistory }));

import ExportationsPage from "./page";
import ExportationsLayout from "./layout";
import Loading from "./loading";

const adminSession = {
  status: "authenticated" as const,
  sessionToken: "admin-session",
  profile: {
    id: "admin-1",
    userId: "admin-1",
    fullName: "Yago",
    email: "yago@wtgseguros.com.br",
    role: "admin" as const,
  },
};

describe("ExportationsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    redirect.mockImplementation((path: string) => {
      throw new Error(`REDIRECT:${path}`);
    });
  });

  it("redireciona vendedor antes de consultar o hist\u00f3rico", async () => {
    getSessionContext.mockResolvedValue({
      ...adminSession,
      profile: { ...adminSession.profile, role: "seller" },
    });

    await expect(ExportationsLayout({ children: <p>restrito</p> })).rejects.toThrow(
      "REDIRECT:/dashboard",
    );
    expect(getExportationHistory).not.toHaveBeenCalled();
  });

  it("preserva o shell administrativo e oferece retry quando a consulta falha", async () => {
    getSessionContext.mockResolvedValue(adminSession);
    getExportationHistory.mockRejectedValue(new Error("mongodb://segredo-interno"));

    const page = await ExportationsPage({ searchParams: Promise.resolve({ page: "2" }) });
    const markup = renderToStaticMarkup(await ExportationsLayout({ children: page }));

    expect(markup).toContain("Exporta\u00e7\u00f5es");
    expect(markup).toContain("Sistema conectado");
    expect(markup).toContain("Tentar novamente");
    expect(markup).toContain("/exportacoes?page=2");
    expect(markup).not.toContain("segredo-interno");
  });

  it("mantém o shell enquanto o histórico está carregando", async () => {
    getSessionContext.mockResolvedValue(adminSession);

    const markup = renderToStaticMarkup(await ExportationsLayout({ children: <Loading /> }));

    expect(markup).toContain("Sistema conectado");
    expect(markup).toContain("Carregando histórico de exportações");
    expect(markup).toContain('aria-busy="true"');
  });
});
