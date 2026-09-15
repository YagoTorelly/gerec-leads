import { describe, expect, it } from "vitest";

import { reportPeriod } from "./queries";

describe("regressões de período de relatórios", () => {
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
