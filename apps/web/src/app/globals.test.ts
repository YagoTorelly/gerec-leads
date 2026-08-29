import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const stylesheetPath = fileURLToPath(new URL("./globals.css", import.meta.url));

describe("tokens visuais da operação", () => {
  it("define tokens contrastantes para os quatro estados comerciais", async () => {
    const stylesheet = await readFile(stylesheetPath, "utf8");

    expect(stylesheet).toContain("--status-undefined-bg:");
    expect(stylesheet).toContain("--status-negotiation-bg:");
    expect(stylesheet).toContain("--status-won-bg:");
    expect(stylesheet).toContain("--status-disqualified-bg:");
  });

  it("mantém a superfície desktop, tabelas, modais e controles indisponíveis estilizados", async () => {
    const stylesheet = await readFile(stylesheetPath, "utf8");

    expect(stylesheet).toContain("min-width: 1280px");
    expect(stylesheet).toContain(".table-card table");
    expect(stylesheet).toContain(".modal-backdrop");
    expect(stylesheet).toContain("button:disabled");
    expect(stylesheet).toContain(".empty-state");
  });

  it("preserva badges de situação nas atividades resumidas", async () => {
    const stylesheet = await readFile(stylesheetPath, "utf8");

    expect(stylesheet).toContain(".activity-item__meta .commercial-status");
  });
});
