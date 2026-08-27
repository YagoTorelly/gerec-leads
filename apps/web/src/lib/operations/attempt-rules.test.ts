import { describe, expect, it } from "vitest";
import { nextFeedbackDueAt, validateAttempt } from "./attempt-rules";

describe("regras de tentativa", () => {
  it("agenda o próximo prazo 24 horas depois", () => {
    const start = new Date("2026-08-26T12:00:00.000Z");
    expect(nextFeedbackDueAt(start).toISOString()).toBe("2026-08-27T12:00:00.000Z");
  });
});
