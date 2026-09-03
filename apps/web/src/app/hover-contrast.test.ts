import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const stylesheetPath = fileURLToPath(new URL("./globals.css", import.meta.url));

describe("contraste dos estados de interação", () => {
  it("preserva contraste no hover da ação primária", async () => {
    const stylesheet = await readFile(stylesheetPath, "utf8");
    const start = stylesheet.indexOf(".table-action:not(:disabled):hover {");
    const block = stylesheet.slice(start, stylesheet.indexOf("}", start) + 1);

    expect(block).toContain("color: #fff;");
  });

  it("preserva contraste no hover das linhas da tabela", async () => {
    const stylesheet = await readFile(stylesheetPath, "utf8");
    const start = stylesheet.indexOf(".table-card tbody tr:hover {");
    const block = stylesheet.slice(start, stylesheet.indexOf("}", start) + 1);

    expect(block).toContain("color: var(--text-strong);");
  });
});
