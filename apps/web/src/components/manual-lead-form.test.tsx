// @vitest-environment jsdom

import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

const actions = vi.hoisted(() => ({ createManualLead: vi.fn() }));

vi.mock("../lib/admin/manual-lead-actions", () => ({
  createManualLeadAction: actions.createManualLead,
}));

import { ManualLeadForm } from "./manual-lead-form";

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("cadastro manual de lead", () => {
  it("exibe situação fixa, campos opcionais e nunca permite escolher responsável", async () => {
    const user = userEvent.setup();
    render(
      <ManualLeadForm
        latestCampaignDefaults={{ campaign: "Campanha vigente", source: "Meta Ads" }}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Adicionar leads" }));

    expect(screen.getByRole("dialog", { name: "Adicionar lead" })).toBeTruthy();
    expect(screen.getByLabelText("Nome")).toBeTruthy();
    expect(screen.getByLabelText("E-mail")).toBeTruthy();
    expect(screen.getByLabelText("Telefone")).toBeTruthy();
    expect(screen.getByLabelText("Campanha (opcional)")).toHaveProperty(
      "value",
      "Campanha vigente",
    );
    expect(screen.getByLabelText("Origem (opcional)")).toHaveProperty("value", "Meta Ads");
    expect(screen.getByLabelText("Situação")).toMatchObject({
      value: "Indefinido",
      readOnly: true,
    });
    expect(screen.queryByLabelText(/responsável/i)).toBeNull();
  });

  it("exige nome, e-mail e telefone antes de permitir o envio", async () => {
    const user = userEvent.setup();
    render(<ManualLeadForm latestCampaignDefaults={null} />);

    await user.click(screen.getByRole("button", { name: "Adicionar leads" }));
    const submit = screen.getByRole("button", { name: "Cadastrar lead" });
    expect(submit).toHaveProperty("disabled", true);

    await user.type(screen.getByLabelText("Nome"), "Contato manual");
    await user.type(screen.getByLabelText("E-mail"), "contato@example.com");
    await user.type(screen.getByLabelText("Telefone"), "+55 11 99999-1234");
    expect(submit).toHaveProperty("disabled", false);
  });

  it("envia somente dados de contato e origem, mostrando a atribuição confirmada", async () => {
    actions.createManualLead.mockResolvedValue({
      ok: true,
      message: "Lead cadastrado e distribuído.",
      lead: {
        leadId: "lead-1",
        manualQueueLeadId: "MAN-123",
        assigneeId: "seller-1",
        assignedAt: "2026-09-22T13:00:00Z",
        commercialStatus: "undefined",
        source: "manual",
      },
    });
    const user = userEvent.setup();
    render(<ManualLeadForm latestCampaignDefaults={null} />);

    await user.click(screen.getByRole("button", { name: "Adicionar leads" }));
    await user.type(screen.getByLabelText("Nome"), "  Contato manual  ");
    await user.type(screen.getByLabelText("E-mail"), "  contato@example.com  ");
    await user.type(screen.getByLabelText("Telefone"), "  +55 11 99999-1234  ");
    await user.click(screen.getByRole("button", { name: "Cadastrar lead" }));

    await waitFor(() =>
      expect(actions.createManualLead).toHaveBeenCalledWith({
        name: "Contato manual",
        email: "contato@example.com",
        phone: "+55 11 99999-1234",
        campaign: undefined,
        source: undefined,
      }),
    );
    expect((await screen.findByRole("status")).textContent).toContain(
      "Lead cadastrado e distribuído.",
    );
    expect(screen.getByRole("status").textContent).toContain("MAN-123");
    expect(screen.getByRole("status").textContent).toContain("seller-1");
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("mantém o formulário aberto e recuperável quando o cadastro falha", async () => {
    actions.createManualLead.mockResolvedValue({
      ok: false,
      message: "Revise os dados informados e tente novamente.",
    });
    const user = userEvent.setup();
    render(<ManualLeadForm latestCampaignDefaults={null} />);

    await user.click(screen.getByRole("button", { name: "Adicionar leads" }));
    await user.type(screen.getByLabelText("Nome"), "Contato manual");
    await user.type(screen.getByLabelText("E-mail"), "contato@example.com");
    await user.type(screen.getByLabelText("Telefone"), "11999991234");
    await user.click(screen.getByRole("button", { name: "Cadastrar lead" }));

    expect(await screen.findByText("Revise os dados informados e tente novamente.")).toBeTruthy();
    expect(screen.getByRole("dialog", { name: "Adicionar lead" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Cadastrar lead" })).toBeTruthy();
  });
});
