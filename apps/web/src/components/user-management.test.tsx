// @vitest-environment jsdom

import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { ManagedUser } from "../lib/api/types";

const actions = vi.hoisted(() => ({
  create: vi.fn(),
  availability: vi.fn(),
  resetPassword: vi.fn(),
}));

const navigation = vi.hoisted(() => ({ push: vi.fn(), refresh: vi.fn() }));

vi.mock("../lib/users/actions", () => ({
  createManagedUserAction: actions.create,
  setManagedUserAvailabilityAction: actions.availability,
  resetManagedUserPasswordAction: actions.resetPassword,
}));

vi.mock("next/navigation", () => ({ useRouter: () => navigation }));

import { UserManagement } from "./user-management";

const users: ManagedUser[] = [
  { id: "admin-1", fullName: "Yago", email: "yago@wtgseguros.com.br", role: "admin", active: true, paused: null },
  { id: "seller-1", fullName: "Renato", email: "renato@wtgseguros.com.br", role: "seller", active: true, paused: false },
];

const createdSeller: ManagedUser = {
  id: "seller-2",
  fullName: "Sandra",
  email: "sandra@wtgseguros.com.br",
  role: "seller",
  active: true,
  paused: false,
};

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("gestão operacional de usuários", () => {
  it("abre o cadastro com foco inicial e exige uma senha não vazia", async () => {
    const user = userEvent.setup();
    render(<UserManagement users={users} />);

    const trigger = screen.getByRole("button", { name: "Novo usuário" });
    await user.click(trigger);

    expect(screen.getByRole("dialog", { name: "Novo usuário" })).toBeTruthy();
    expect(document.activeElement).toBe(screen.getByLabelText("Nome completo"));
    expect((screen.getByRole("button", { name: "Criar usuário" }) as HTMLButtonElement).disabled).toBe(true);

    await user.type(screen.getByLabelText("Nome completo"), "Sandra");
    await user.type(screen.getByLabelText("E-mail"), "sandra@wtgseguros.com.br");
    await user.type(screen.getByLabelText("Senha inicial"), "   ");
    expect((screen.getByRole("button", { name: "Criar usuário" }) as HTMLButtonElement).disabled).toBe(true);

    await user.clear(screen.getByLabelText("Senha inicial"));
    await user.type(screen.getByLabelText("Senha inicial"), "senha inicial");
    expect((screen.getByRole("button", { name: "Criar usuário" }) as HTMLButtonElement).disabled).toBe(false);
  });

  it("cria usuário, atualiza a lista e nunca apresenta a senha salva", async () => {
    actions.create.mockResolvedValue({ status: "success", message: "Usuário criado.", user: createdSeller });
    const user = userEvent.setup();
    render(<UserManagement users={users} />);

    await user.click(screen.getByRole("button", { name: "Novo usuário" }));
    await user.type(screen.getByLabelText("Nome completo"), "Sandra");
    await user.type(screen.getByLabelText("E-mail"), "sandra@wtgseguros.com.br");
    await user.type(screen.getByLabelText("Senha inicial"), "senha confidencial");
    await user.click(screen.getByRole("button", { name: "Criar usuário" }));

    await waitFor(() => expect(actions.create).toHaveBeenCalledWith({
      fullName: "Sandra",
      email: "sandra@wtgseguros.com.br",
      role: "seller",
      password: "senha confidencial",
    }));
    expect((await screen.findByRole("status")).textContent).toContain("Usuário criado.");
    expect(screen.getByText("Sandra")).toBeTruthy();
    expect(screen.queryByText("senha confidencial")).toBeNull();
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("mostra carregamento enquanto o cadastro aguarda a resposta", async () => {
    let resolveCreation: ((value: unknown) => void) | undefined;
    actions.create.mockImplementation(() => new Promise((resolve) => { resolveCreation = resolve; }));
    const user = userEvent.setup();
    render(<UserManagement users={users} />);

    await user.click(screen.getByRole("button", { name: "Novo usuário" }));
    await user.type(screen.getByLabelText("Nome completo"), "Sandra");
    await user.type(screen.getByLabelText("E-mail"), "sandra@wtgseguros.com.br");
    await user.type(screen.getByLabelText("Senha inicial"), "senha inicial");
    await user.click(screen.getByRole("button", { name: "Criar usuário" }));
    expect(screen.getByRole("button", { name: "Criando…" })).toBeTruthy();

    resolveCreation?.({ status: "success", message: "Usuário criado.", user: createdSeller });
    await screen.findByRole("status");
  });

  it("confirma a pausa de vendedor e atualiza seu estado visível", async () => {
    actions.availability.mockResolvedValue({
      status: "success",
      message: "Vendedor pausado.",
      user: { ...users[1], paused: true },
    });
    const user = userEvent.setup();
    render(<UserManagement users={users} />);

    await user.click(screen.getByRole("button", { name: "Pausar Renato" }));
    expect(screen.getByRole("dialog", { name: "Confirmar pausa" })).toBeTruthy();
    await user.click(screen.getByRole("button", { name: "Confirmar pausa" }));

    await waitFor(() => expect(actions.availability).toHaveBeenCalledWith("seller-1", true));
    expect((await screen.findByRole("status")).textContent).toContain("Vendedor pausado.");
    expect(screen.getByText("Pausado")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Ativar Renato" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Pausar Yago" })).toBeNull();
  });

  it("mostra conta inativa sem oferecer uma pausa manual inválida", () => {
    render(<UserManagement users={[...users, {
      id: "seller-3",
      fullName: "Nelma",
      email: "nelma@wtgseguros.com.br",
      role: "seller",
      active: false,
      paused: false,
    }]} />);

    expect(screen.getByText("Inativo")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Pausar Nelma" })).toBeNull();
  });

  it("exige senha nova e confirma a redefinição sem expor seu conteúdo", async () => {
    actions.resetPassword.mockResolvedValue({ status: "success", message: "Senha redefinida.", user: users[1] });
    const user = userEvent.setup();
    render(<UserManagement users={users} />);

    await user.click(screen.getByRole("button", { name: "Redefinir senha de Renato" }));
    expect(screen.getByRole("dialog", { name: "Redefinir senha" })).toBeTruthy();
    expect((screen.getByRole("button", { name: "Salvar nova senha" }) as HTMLButtonElement).disabled).toBe(true);
    await user.type(screen.getByLabelText("Nova senha"), "nova senha secreta");
    await user.click(screen.getByRole("button", { name: "Salvar nova senha" }));
    expect(screen.getByRole("dialog", { name: "Confirmar redefinição de senha" })).toBeTruthy();
    await user.click(screen.getByRole("button", { name: "Confirmar redefinição" }));

    await waitFor(() => expect(actions.resetPassword).toHaveBeenCalledWith("seller-1", "nova senha secreta"));
    expect((await screen.findByRole("status")).textContent).toContain("Senha redefinida.");
    expect(screen.queryByText("nova senha secreta")).toBeNull();
  });

  it("cancela e fecha modais com Escape devolvendo foco ao acionador", async () => {
    const user = userEvent.setup();
    render(<UserManagement users={users} />);
    const trigger = screen.getByRole("button", { name: "Novo usuário" });

    await user.click(trigger);
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(document.activeElement).toBe(trigger);
  });

  it("mantém o modal aberto e apresenta erro seguro quando a ação falha", async () => {
    actions.create.mockResolvedValue({ status: "error", message: "Revise os dados informados e tente novamente.", user: null });
    const user = userEvent.setup();
    render(<UserManagement users={users} />);

    await user.click(screen.getByRole("button", { name: "Novo usuário" }));
    await user.type(screen.getByLabelText("Nome completo"), "Sandra");
    await user.type(screen.getByLabelText("E-mail"), "sandra@wtgseguros.com.br");
    await user.type(screen.getByLabelText("Senha inicial"), "senha inicial");
    await user.click(screen.getByRole("button", { name: "Criar usuário" }));

    expect(await screen.findByText("Revise os dados informados e tente novamente.")).toBeTruthy();
    expect(screen.getByRole("dialog", { name: "Novo usuário" })).toBeTruthy();
  });

  it("recupera rejeição do cadastro sem manter o botão em carregamento", async () => {
    actions.create.mockRejectedValue(new Error("segredo técnico"));
    const user = userEvent.setup();
    render(<UserManagement users={users} />);

    await user.click(screen.getByRole("button", { name: "Novo usuário" }));
    await user.type(screen.getByLabelText("Nome completo"), "Sandra");
    await user.type(screen.getByLabelText("E-mail"), "sandra@wtgseguros.com.br");
    await user.type(screen.getByLabelText("Senha inicial"), "senha inicial");
    await user.click(screen.getByRole("button", { name: "Criar usuário" }));

    expect(await screen.findByText("Não foi possível concluir a ação. Tente novamente.")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Criar usuário" })).toBeTruthy();
  });

  it("recupera rejeição da pausa sem deixar a confirmação bloqueada", async () => {
    actions.availability.mockRejectedValue(new Error("segredo técnico"));
    const user = userEvent.setup();
    render(<UserManagement users={users} />);

    await user.click(screen.getByRole("button", { name: "Pausar Renato" }));
    await user.click(screen.getByRole("button", { name: "Confirmar pausa" }));

    expect((await screen.findByRole("status")).textContent).toContain("Não foi possível concluir a ação. Tente novamente.");
    expect(screen.queryByRole("button", { name: "Salvando…" })).toBeNull();
  });

  it("recupera rejeição da redefinição de senha no formulário", async () => {
    actions.resetPassword.mockRejectedValue(new Error("segredo técnico"));
    const user = userEvent.setup();
    render(<UserManagement users={users} />);

    await user.click(screen.getByRole("button", { name: "Redefinir senha de Renato" }));
    await user.type(screen.getByLabelText("Nova senha"), "nova senha secreta");
    await user.click(screen.getByRole("button", { name: "Salvar nova senha" }));
    await user.click(screen.getByRole("button", { name: "Confirmar redefinição" }));

    expect(await screen.findByText("Não foi possível concluir a ação. Tente novamente.")).toBeTruthy();
    expect(screen.getByRole("dialog", { name: "Redefinir senha" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Salvar nova senha" })).toBeTruthy();
  });

  it("redireciona à primeira página após criar em uma página posterior", async () => {
    actions.create.mockResolvedValue({ status: "success", message: "Usuário criado.", user: createdSeller });
    const user = userEvent.setup();
    render(<UserManagement users={users} page={2} />);

    await user.click(screen.getByRole("button", { name: "Novo usuário" }));
    await user.type(screen.getByLabelText("Nome completo"), "Sandra");
    await user.type(screen.getByLabelText("E-mail"), "sandra@wtgseguros.com.br");
    await user.type(screen.getByLabelText("Senha inicial"), "senha inicial");
    await user.click(screen.getByRole("button", { name: "Criar usuário" }));

    await waitFor(() => expect(navigation.push).toHaveBeenCalledWith("/usuarios"));
    expect(screen.queryByText("Sandra")).toBeNull();
  });
});
