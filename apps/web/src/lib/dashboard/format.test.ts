import { describe, expect, it } from "vitest";

import { formatDateTime, getSlaState } from "./format";

describe("formatDateTime", () => {
  it("formata horarios no fuso de Sao Paulo", () => {
    expect(formatDateTime("2026-08-26T15:30:00.000Z")).toBe("26/08/2026, 12:30");
  });

  it("retorna texto vazio para valor ausente", () => {
    expect(formatDateTime(null)).toBe("");
  });
});

describe("getSlaState", () => {
  it("marca feedback vencido como atrasado", () => {
    expect(getSlaState("2026-08-26T10:00:00.000Z", new Date("2026-08-26T11:00:00.000Z"))).toBe(
      "overdue",
    );
  });

  it("marca feedback do dia como vence hoje", () => {
    expect(getSlaState("2026-08-26T21:00:00.000Z", new Date("2026-08-26T11:00:00.000Z"))).toBe(
      "today",
    );
  });
});
