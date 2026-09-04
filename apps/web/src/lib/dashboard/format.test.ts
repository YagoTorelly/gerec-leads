import { describe, expect, it } from "vitest";

import {
  NOT_INFORMED,
  formatCommercialStatus,
  formatCommentCount,
  formatDateTime,
  formatDisqualificationMarker,
  formatPhone,
  formatText,
} from "./format";

describe("formatDateTime", () => {
  it("formata horários no fuso de São Paulo", () => {
    expect(formatDateTime("2026-08-26T15:30:00.000Z")).toBe("26/08/2026, 12:30");
  });

  it("retorna fallback para valor ausente", () => {
    expect(formatDateTime(null)).toBe(NOT_INFORMED);
  });
});

describe("formatação de projeção operacional", () => {
  it("traduz situação comercial e marcador sem decidir regras de negócio", () => {
    expect(formatCommercialStatus("undefined")).toBe("Indefinido");
    expect(formatCommercialStatus("negotiation")).toBe("Negociação");
    expect(formatCommercialStatus("won")).toBe("Ganho");
    expect(formatDisqualificationMarker(true)).toBe("Desqualificado");
    expect(formatDisqualificationMarker(false)).toBe("Não desqualificado");
  });

  it("formata contador, prazo, telefone e texto ausente para o operador", () => {
    expect(formatCommentCount(1)).toBe("1 comentário");
    expect(formatCommentCount(2)).toBe("2 comentários");
    expect(formatPhone("5511988308029")).toBe("(11) 98830-8029");
    expect(formatText("   ")).toBe(NOT_INFORMED);
  });
});
