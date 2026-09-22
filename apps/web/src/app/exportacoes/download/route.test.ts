import { beforeEach, describe, expect, it, vi } from "vitest";

const { apiRequest, cookies } = vi.hoisted(() => ({
  apiRequest: vi.fn(),
  cookies: vi.fn(),
}));

vi.mock("next/headers", () => ({ cookies }));
vi.mock("../../../lib/api/client", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../../lib/api/client")>()),
  apiRequest,
}));

import { ApiRequestError } from "../../../lib/api/client";
import { GET } from "./route";

describe("GET /exportacoes/download", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    cookies.mockResolvedValue({ get: () => ({ value: "admin-session" }) });
  });

  it("repassa a sess\u00e3o e transmite o corpo XLSX sem convert\u00ea-lo em texto", async () => {
    const bytes = new Uint8Array([0x50, 0x4b, 0x03, 0x04]);
    const upstream = new Response(bytes, {
      headers: {
        "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "Content-Disposition": 'attachment; filename="leads-20260922-123000.xlsx"',
      },
    });
    apiRequest.mockResolvedValue(upstream);

    const response = await GET();

    expect(apiRequest).toHaveBeenCalledWith("/api/admin/exportations/leads", {
      cache: "no-store",
      headers: { Cookie: "gerec_session=admin-session" },
    });
    expect(response.headers.get("content-type")).toContain(
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    );
    expect(response.headers.get("content-disposition")).toBe(
      'attachment; filename="leads-20260922-123000.xlsx"',
    );
    expect(Array.from(new Uint8Array(await response.arrayBuffer()))).toEqual(Array.from(bytes));
  });

  it("responde de forma segura e recuper\u00e1vel quando a API rejeita o download", async () => {
    apiRequest.mockRejectedValue(new ApiRequestError("segredo interno", 503));

    const response = await GET();

    expect(response.status).toBe(503);
    expect(await response.text()).toBe(
      "N\u00e3o foi poss\u00edvel gerar a exporta\u00e7\u00e3o. Tente novamente.",
    );
  });
});
