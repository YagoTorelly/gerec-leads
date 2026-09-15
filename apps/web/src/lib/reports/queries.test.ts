import { beforeEach, describe, expect, it, vi } from "vitest";

const { apiFetch } = vi.hoisted(() => ({ apiFetch: vi.fn() }));
vi.mock("../api/client", () => ({ apiFetch }));

import { getLeadDistributionReport, reportPeriod } from "./queries";

describe("consultas de relat\u00f3rios", () => {
  beforeEach(() => vi.clearAllMocks());

  it("usa todo o hist\u00f3rico desde o marco UTC aprovado", () => {
    expect(reportPeriod({}, new Date("2026-09-15T15:30:00.000Z"))).toEqual({
      key: "all",
      fromAt: "1970-01-01T00:00:00.000Z",
      toAt: "2026-09-15T15:30:00.000Z",
    });
  });

  it("calcula o m\u00eas atual a partir do primeiro dia UTC", () => {
    expect(reportPeriod({ period: "month" }, new Date("2026-10-01T01:00:00.000Z"))).toEqual({
      key: "month",
      fromAt: "2026-09-01T03:00:00.000Z",
      toAt: "2026-10-01T01:00:00.000Z",
    });
  });

  it("calcula os \u00faltimos 30 dias a partir do rel\u00f3gio informado", () => {
    expect(reportPeriod({ period: "last30" }, new Date("2026-09-15T15:30:00.000Z"))).toEqual({
      key: "last30",
      fromAt: "2026-08-16T15:30:00.000Z",
      toAt: "2026-09-15T15:30:00.000Z",
    });
  });

  it("preserva um intervalo personalizado v\u00e1lido", () => {
    expect(
      reportPeriod(
        { period: "custom", from: "2026-09-01", to: "2026-09-15" },
        new Date("2026-09-15T15:30:00.000Z"),
      ),
    ).toEqual({
      key: "custom",
      fromAt: "2026-09-01T03:00:00.000Z",
      toAt: "2026-09-15T03:00:00.000Z",
    });
  });

  it("encaminha o intervalo e a sess\u00e3o ao endpoint administrativo", async () => {
    apiFetch.mockResolvedValue({});
    await getLeadDistributionReport("sessao", {
      key: "all",
      fromAt: "1970-01-01T00:00:00.000Z",
      toAt: "2026-09-15T15:30:00.000Z",
    });

    expect(apiFetch).toHaveBeenCalledWith(
      "/api/admin/reports/lead-distribution?fromAt=1970-01-01T00%3A00%3A00.000Z&toAt=2026-09-15T15%3A30%3A00.000Z",
      expect.objectContaining({ headers: { Cookie: "gerec_session=sessao" } }),
    );
  });
});
