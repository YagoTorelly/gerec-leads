// @vitest-environment jsdom

import { fireEvent, render, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ExportLeadsButton } from "./export-leads-button";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("ExportLeadsButton", () => {
  it("mostra loading e bloqueia cliques duplicados durante a exportação", async () => {
    let resolveDownload!: (response: Response) => void;
    vi.stubGlobal("fetch", vi.fn(() => new Promise<Response>((resolve) => { resolveDownload = resolve; })));
    vi.stubGlobal("URL", {
      createObjectURL: vi.fn(() => "blob:exportacao"),
      revokeObjectURL: vi.fn(),
    });

    const screen = render(<ExportLeadsButton />);
    fireEvent.click(screen.getByRole("button", { name: "Exportar leads em Excel" }));

    expect((screen.getByRole("button", { name: "Processando exportação" }) as HTMLButtonElement).disabled).toBe(true);
    expect(screen.getByRole("progressbar")).toBeTruthy();

    resolveDownload(new Response(new Blob(["xlsx"]), { status: 200 }));
    await waitFor(() => expect((screen.getByRole("button", { name: "Exportar leads em Excel" }) as HTMLButtonElement).disabled).toBe(false));
  });
});
