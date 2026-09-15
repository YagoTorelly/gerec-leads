// @vitest-environment jsdom

import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

const { acknowledge } = vi.hoisted(() => ({ acknowledge: vi.fn() }));

vi.mock("../lib/notifications/actions", () => ({
  acknowledgeNewLeadsAction: acknowledge,
}));

import { NewLeadsNotificationModal } from "./new-leads-notification-modal";

const snapshot = {
  items: [
    {
      leadId: "lead-1",
      contactName: "Ana Souza",
      assignedAt: "2026-09-15T12:00:00.000Z",
    },
  ],
  watermark: "2026-09-15T12:01:00.000Z",
  acknowledgementToken: "token-assinado",
  watermarkSequence: 8,
};

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("janela de novos leads", () => {
  it("confirma o watermark somente ao fechar", async () => {
    acknowledge.mockResolvedValue({ ok: true, message: "Novos leads confirmados." });
    const user = userEvent.setup();
    render(<NewLeadsNotificationModal snapshot={snapshot} />);

    expect(acknowledge).not.toHaveBeenCalled();
    await user.click(screen.getByRole("button", { name: "Fechar" }));

    await waitFor(() => expect(acknowledge).toHaveBeenCalledWith(snapshot));
    expect(screen.queryByRole("dialog", { name: "Novos leads" })).toBeNull();
  });

  it("abre a nova janela quando a revalidação entrega outro snapshot", async () => {
    acknowledge.mockResolvedValue({ ok: true, message: "Novos leads confirmados." });
    const user = userEvent.setup();
    const { rerender } = render(<NewLeadsNotificationModal snapshot={snapshot} />);

    await user.click(screen.getByRole("button", { name: "Fechar" }));
    await waitFor(() => expect(screen.queryByRole("dialog", { name: "Novos leads" })).toBeNull());

    rerender(
      <NewLeadsNotificationModal
        snapshot={{
          ...snapshot,
          items: [{ ...snapshot.items[0], leadId: "lead-2", contactName: "Beatriz Lima" }],
          watermark: "2026-09-15T12:02:00.000Z",
          acknowledgementToken: "outro-token-assinado",
          watermarkSequence: 9,
        }}
      />,
    );

    expect(await screen.findByRole("dialog", { name: "Novos leads" })).toBeTruthy();
    expect(screen.getByText("Beatriz Lima")).toBeTruthy();
  });

  it("mantém a janela aberta após falha de confirmação", async () => {
    acknowledge.mockResolvedValue({
      ok: false,
      message: "Não foi possível confirmar os novos leads.",
    });
    const user = userEvent.setup();
    render(<NewLeadsNotificationModal snapshot={snapshot} />);

    await user.keyboard("{Escape}");

    expect((await screen.findByRole("alert")).textContent).toContain(
      "Não foi possível confirmar os novos leads.",
    );
    expect(screen.getByRole("dialog", { name: "Novos leads" })).toBeTruthy();
  });

  it("permite nova tentativa quando a confirmação remota é rejeitada", async () => {
    acknowledge.mockRejectedValue(new Error("falha de transporte"));
    const user = userEvent.setup();
    render(<NewLeadsNotificationModal snapshot={snapshot} />);

    await user.click(screen.getByRole("button", { name: "Fechar" }));

    expect((await screen.findByRole("alert")).textContent).toContain(
      "Não foi possível confirmar os novos leads.",
    );
    expect(screen.getByRole("dialog", { name: "Novos leads" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Fechar" }).hasAttribute("disabled")).toBe(false);
  });

  it("devolve o foco anterior depois de fechar", async () => {
    acknowledge.mockResolvedValue({ ok: true, message: "Novos leads confirmados." });
    const user = userEvent.setup();
    const trigger = document.createElement("button");
    trigger.textContent = "Origem";
    document.body.append(trigger);
    trigger.focus();

    render(<NewLeadsNotificationModal snapshot={snapshot} />);
    await user.click(screen.getByRole("button", { name: "Fechar" }));

    await waitFor(() => expect(document.activeElement).toBe(trigger));
    trigger.remove();
  });
});
