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
