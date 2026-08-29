import { beforeEach, describe, expect, it, vi } from "vitest";

const { apiFetch } = vi.hoisted(() => ({ apiFetch: vi.fn() }));
vi.mock("../api/client", () => ({ apiFetch }));

import { getDashboardData, isAdminDashboard, pageNumber } from "./queries";

describe("getDashboardData", () => {
  beforeEach(() => vi.clearAllMocks());

  it("solicita a página pedida e encaminha cookie de sessão", async () => {
    apiFetch.mockResolvedValue({});
    await getDashboardData("opaque", 3);
    expect(apiFetch).toHaveBeenCalledWith(
      "/api/dashboard?page=3&limit=50",
      expect.objectContaining({ headers: { Cookie: "gerec_session=opaque" } }),
    );
  });

  it.each(["0", "-1", "1.5", "Infinity", "não-numero"])("recusa página inválida: %s", (value) => {
    expect(() => pageNumber(value)).toThrow("Página inválida");
  });

  it("separa a projeção administrativa pelo papel devolvido pela API", () => {
    expect(
      isAdminDashboard({
        user: { id: "admin-1", email: "admin@wtgseguros.com.br", role: "admin" },
        leads: { items: [], page: 1, pageSize: 50, total: 0 },
        history: { items: [], page: 1, pageSize: 50, total: 0 },
        queue: { items: [], total: 0, nextSellerName: "Não informado", cursorSellerName: "Não informado" },
      }),
    ).toBe(true);
  });

  it("mantém a fila do vendedor sem dados globais", () => {
    const dashboard = {
      user: { id: "seller-1", email: "seller@wtgseguros.com.br", role: "seller" as const },
      leads: { items: [], page: 1, pageSize: 50, total: 0 },
      history: { items: [], page: 1, pageSize: 50, total: 0 },
      queue: { position: 2, availability: "active" as const, skipBalance: 0 },
    };

    expect(isAdminDashboard(dashboard)).toBe(false);
    expect(dashboard.queue).not.toHaveProperty("items");
    expect(dashboard.queue).not.toHaveProperty("nextSellerName");
  });
});
