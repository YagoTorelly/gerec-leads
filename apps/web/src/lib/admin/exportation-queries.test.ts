import { beforeEach, describe, expect, it, vi } from "vitest";

const { apiFetch } = vi.hoisted(() => ({ apiFetch: vi.fn() }));
vi.mock("../api/client", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../api/client")>()),
  apiFetch,
}));

import { getExportationHistory } from "./exportation-queries";

describe("consulta do hist\u00f3rico de exporta\u00e7\u00f5es", () => {
  beforeEach(() => vi.clearAllMocks());

  it("encaminha pagina\u00e7\u00e3o e sess\u00e3o ao endpoint administrativo", async () => {
    apiFetch.mockResolvedValue({ items: [], page: 2, pageSize: 25, total: 0 });

    await expect(getExportationHistory("sessao-admin", 2, 25)).resolves.toEqual({
      items: [],
      page: 2,
      pageSize: 25,
      total: 0,
    });
    expect(apiFetch).toHaveBeenCalledWith("/api/admin/exportations?page=2&limit=25", {
      cache: "no-store",
      headers: { Cookie: "gerec_session=sessao-admin" },
    });
  });

  it("rejeita um item malformado em vez de renderizar hist\u00f3rico inconsistente", async () => {
    apiFetch.mockResolvedValue({
      items: [
        {
          createdAt: "2026-09-22T15:30:00Z",
          administratorName: "Yago",
          leadCount: -1,
          filters: {},
          status: "success",
        },
      ],
      page: 1,
      pageSize: 50,
      total: 1,
    });

    await expect(getExportationHistory("sessao-admin")).rejects.toThrow(
      "A resposta do hist\u00f3rico de exporta\u00e7\u00f5es \u00e9 inv\u00e1lida.",
    );
  });
});
