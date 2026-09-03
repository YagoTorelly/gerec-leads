// @vitest-environment jsdom

import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Treatment } from "../lib/api/types";

const actions = vi.hoisted(() => ({
  loadHistory: vi.fn(async () => ({ status: "success" as const, items: [] as Treatment[] })),
  submit: vi.fn(),
}));

vi.mock("../lib/operations/treatment-actions", () => ({
  initialTreatmentActionState: { status: "idle", message: null, submission: null },
  loadLeadTreatmentHistoryAction: actions.loadHistory,
  submitLeadTreatmentAction: actions.submit,
}));

import { LeadTable } from "./lead-table";
import { LeadTreatmentModal } from "./lead-treatment-modal";

const lead = {
  id: "lead-1",
  contactName: "Débora Souza",
  sellerName: "Jessica",
  companyName: "Empresa da Débora",
  campaignName: "Campanha WTG",
  phoneDisplay: "(11) 98830-8029",
  email: "debora@example.com",
  commercialStatus: "undefined" as const,
  isDisqualified: false,
  commentCount: 2,
  assignedAt: "2026-08-28T12:00:00.000Z",
  feedbackDueAt: null,
  lastUpdatedAt: "2026-08-28T12:00:00.000Z",
};

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("acessibilidade e interação do modal de tratativa", () => {
  it("foca o primeiro controle de leitura, prende Tab e devolve foco após Escape", async () => {
    const user = userEvent.setup();
    render(<LeadTreatmentModal lead={lead} mode="read" />);
    const trigger = screen.getByRole("button", { name: "Ver histórico" });

    await user.click(trigger);
    const close = screen.getByRole("button", { name: "Fechar janela" });
    await waitFor(() => expect(document.activeElement).toBe(close));
    await user.tab();
    expect(document.activeElement).toBe(close);
    await user.tab({ shift: true });
    expect(document.activeElement).toBe(close);
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(document.activeElement).toBe(trigger);
  });

  it("bloqueia a submissão com comentário menor que seis caracteres", async () => {
    const user = userEvent.setup();
    render(<LeadTreatmentModal lead={lead} mode="write" />);

    await user.click(screen.getByRole("button", { name: "Registrar tratativa" }));
    await user.type(screen.getByLabelText("Comentário"), "curto");

    expect(
      (screen.getByRole("button", { name: "Salvar tratativa" }) as HTMLButtonElement).disabled,
    ).toBe(true);
    expect(actions.submit).not.toHaveBeenCalled();
  });

  it("gera a chave de idempotência depois da hidratação, sem aleatoriedade no HTML inicial", async () => {
    const user = userEvent.setup();
    render(<LeadTreatmentModal lead={lead} mode="write" />);

    await user.click(screen.getByRole("button", { name: "Registrar tratativa" }));
    await waitFor(() => {
      const input = document.querySelector('input[name="idempotencyKey"]') as HTMLInputElement;
      expect(input?.value).toBeTruthy();
    });
  });

  it("mantém Tab e Shift+Tab dentro do formulário com múltiplos controles", async () => {
    const user = userEvent.setup();
    render(<LeadTreatmentModal lead={lead} mode="write" />);

    await user.click(screen.getByRole("button", { name: "Registrar tratativa" }));
    await user.type(screen.getByLabelText("Comentário"), "Contato realizado por telefone.");
    const close = screen.getByRole("button", { name: "Fechar janela" });
    const submit = screen.getByRole("button", { name: "Salvar tratativa" });
    const comment = screen.getByLabelText("Comentário");
    close.focus();

    await user.tab({ shift: true });
    expect(document.activeElement).toBe(submit);
    await user.tab();
    expect(document.activeElement).toBe(close);
    await user.tab();
    expect(document.activeElement).toBe(comment);
  });

  it("mostra carregamento e depois renderiza o histórico devolvido pela API", async () => {
    let resolveHistory: ((value: { status: "success"; items: Treatment[] }) => void) | undefined;
    actions.loadHistory.mockImplementation(
      () =>
        new Promise<{ status: "success"; items: Treatment[] }>((resolve) => {
          resolveHistory = resolve;
        }),
    );
    const user = userEvent.setup();
    render(<LeadTreatmentModal lead={lead} mode="read" />);

    await user.click(screen.getByRole("button", { name: "Ver histórico" }));
    expect(screen.getByText("Carregando histórico…")).toBeTruthy();
    resolveHistory?.({
      status: "success",
      items: [
        {
          leadName: "Débora Souza",
          sellerName: "Jessica",
          comment: "Histórico carregado da API.",
          commercialStatus: "negotiation",
          isDisqualified: false,
          createdAt: "2026-08-29T12:00:00.000Z",
        },
      ] as Treatment[],
    });

    expect(await screen.findByText("Histórico carregado da API.")).toBeTruthy();
  });

  it("exibe carregamento, atualiza contador/histórico e confirma após sucesso", async () => {
    let resolveSubmission: ((value: unknown) => void) | undefined;
    actions.submit.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveSubmission = resolve;
        }),
    );
    actions.loadHistory
      .mockResolvedValueOnce({ status: "success", items: [] })
      .mockResolvedValueOnce({
        status: "success",
        items: [
          {
            leadName: "Débora Souza",
            sellerName: "Jessica",
            comment: "Contato registrado com sucesso.",
            commercialStatus: "negotiation",
            isDisqualified: false,
            createdAt: "2026-08-29T12:00:00.000Z",
          },
        ] as Treatment[],
      })
      .mockResolvedValue({
        status: "success",
        items: [
          {
            leadName: "Débora Souza",
            sellerName: "Jessica",
            comment: "Contato registrado com sucesso.",
            commercialStatus: "negotiation",
            isDisqualified: false,
            createdAt: "2026-08-29T12:00:00.000Z",
          },
        ] as Treatment[],
      });
    const user = userEvent.setup();
    render(<LeadTable leads={[lead]} role="seller" />);

    await user.click(screen.getByRole("button", { name: "Registrar tratativa" }));
    await user.type(screen.getByLabelText("Comentário"), "Contato registrado com sucesso.");
    await user.click(screen.getByRole("button", { name: "Salvar tratativa" }));
    expect(screen.getByRole("button", { name: "Salvando…" })).toBeTruthy();

    resolveSubmission?.({
      status: "success",
      message: "Tratativa registrada.",
      submission: {
        leadId: "lead-1",
        treatmentId: "treatment-1",
        status: "created",
        commercialStatus: "negotiation",
        isDisqualified: false,
        commentCount: 3,
        reminderAt: null,
        dueAt: null,
        lastUpdatedAt: "2026-08-29T15:00:00.000Z",
      },
    });

    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
    expect(screen.getByRole("status").textContent).toContain("Tratativa registrada.");
    expect(screen.getByText("3 comentários")).toBeTruthy();
    expect(screen.getByText("Negociação")).toBeTruthy();
    await waitFor(() => expect(actions.loadHistory).toHaveBeenCalledTimes(2));
    expect(document.activeElement).toBe(
      screen.getByRole("button", { name: "Registrar tratativa" }),
    );

    await user.click(screen.getByRole("button", { name: "Registrar tratativa" }));
    expect(await screen.findByText("Contato registrado com sucesso.")).toBeTruthy();
  });

  it("mostra o erro 422 seguro no formulário", async () => {
    actions.submit.mockResolvedValue({
      status: "error",
      message: "Revise os dados informados e tente novamente.",
      submission: null,
    });
    const user = userEvent.setup();
    render(<LeadTreatmentModal lead={lead} mode="write" />);

    await user.click(screen.getByRole("button", { name: "Registrar tratativa" }));
    await user.type(screen.getByLabelText("Comentário"), "Contato registrado com sucesso.");
    await user.click(screen.getByRole("button", { name: "Salvar tratativa" }));

    expect(await screen.findByText("Revise os dados informados e tente novamente.")).toBeTruthy();
    expect(screen.getByRole("dialog")).toBeTruthy();
  });

  it("encerra o SLA visível quando a tratativa desqualifica o lead", async () => {
    actions.submit.mockResolvedValue({
      status: "success",
      message: "Tratativa registrada.",
      submission: {
        leadId: "lead-1",
        treatmentId: "treatment-2",
        status: "created",
        commercialStatus: "won",
        isDisqualified: true,
        commentCount: 3,
        reminderAt: null,
        dueAt: null,
        lastUpdatedAt: "2026-08-29T15:00:00.000Z",
      },
    });
    actions.loadHistory
      .mockResolvedValueOnce({ status: "success", items: [] })
      .mockResolvedValueOnce({
        status: "success",
        items: [
          {
            leadName: "Débora Souza",
            sellerName: "Jessica",
            comment: "Fora do escopo, mas com fechamento excepcional.",
            commercialStatus: "won",
            isDisqualified: true,
            createdAt: "2026-08-29T13:00:00.000Z",
          },
        ] as Treatment[],
      });
    const user = userEvent.setup();
    render(
      <LeadTable leads={[{ ...lead, feedbackDueAt: "2026-08-29T16:03:04.876Z" }]} role="seller" />,
    );

    await user.click(screen.getByRole("button", { name: "Registrar tratativa" }));
    await user.type(
      screen.getByLabelText("Comentário"),
      "Fora do escopo, mas com fechamento excepcional.",
    );
    await user.click(screen.getByLabelText("Marcar como Desqualificado"));
    await user.click(screen.getByRole("button", { name: "Salvar tratativa" }));

    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
    expect(screen.getByText("Desqualificado")).toBeTruthy();
    expect(screen.queryByText("Não informado")).toBeNull();
  });
});
