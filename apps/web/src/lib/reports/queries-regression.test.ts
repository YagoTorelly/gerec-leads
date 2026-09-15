import { describe, expect, it } from "vitest";

import { reportPeriod } from "./queries";

describe("regressões de período de relatórios", () => {
  it("rejeita dia e mês inexistentes sem normalizar o intervalo personalizado", () => {
    for (const searchParams of [
      { period: "custom", from: "2026-02-30", to: "2026-03-05" },
      { period: "custom", from: "2026-13-01", to: "2026-13-02" },
    ]) {
      expect(reportPeriod(searchParams, new Date("2026-09-15T15:30:00.000Z"))).toEqual({
        key: "custom",
        from: searchParams.from,
        to: searchParams.to,
        error: "Informe as duas datas de um período personalizado válido.",
      });
    }
  });

  it("mantém período personalizado inválido fora do histórico inteiro", () => {
    expect(
      reportPeriod(
        { period: "custom", from: "2026-09-01", to: "" },
        new Date("2026-09-15T15:30:00.000Z"),
      ),
    ).toEqual({
      key: "custom",
      from: "2026-09-01",
      to: null,
      error: "Informe as duas datas de um período personalizado válido.",
    });
  });
});
