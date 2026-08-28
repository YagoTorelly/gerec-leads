import { beforeEach, describe, expect, it, vi } from "vitest";

const { apiFetch } = vi.hoisted(() => ({ apiFetch: vi.fn() }));
vi.mock("../api/client", () => ({ apiFetch }));

import { getDashboardData, pageNumber } from "./queries";

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
});
