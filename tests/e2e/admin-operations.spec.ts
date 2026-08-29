import { expect, test } from "@playwright/test";

import { resetFixture, signIn } from "./fixture";

test.describe("operações administrativas", () => {
  test.beforeEach(async ({ page }) => resetFixture(page));

  test("admin cria vendedor no fim da fila, pausa, ativa e redefine senha pela interface", async ({
    page,
  }) => {
    await signIn(page, "admin");
    await page.getByRole("link", { name: "Usuários" }).click();

    await page.getByRole("button", { name: "Novo usuário" }).click();
    await page.getByLabel("Nome completo").fill("Bianca E2E");
    await page.getByLabel("E-mail").fill("bianca.e2e@wtg.test");
    await page.getByLabel("Papel").selectOption("seller");
    await page.getByLabel("Senha inicial").fill("senha-bianca-e2e");
    await page.getByRole("button", { name: "Criar usuário" }).click();
    await expect(page.getByRole("status")).toHaveText("Usuário criado.");

    await page.getByRole("link", { name: "Fila de leads" }).click();
    const queueRow = page.getByRole("row").filter({ hasText: "Bianca E2E" });
    await expect(queueRow).toContainText("5");

    await page.getByRole("link", { name: "Usuários" }).click();
    await page.getByRole("button", { name: "Pausar Jessica" }).click();
    await page.getByRole("button", { name: "Confirmar pausa" }).click();
    await expect(page.getByRole("status")).toHaveText("Vendedor pausado.");
    await expect(page.getByRole("article").filter({ hasText: "Jessica" })).toContainText("Pausado");

    await page.getByRole("button", { name: "Ativar Jessica" }).click();
    await page.getByRole("button", { name: "Confirmar ativação" }).click();
    await expect(page.getByRole("status")).toHaveText("Vendedor ativado.");

    await page.getByRole("button", { name: "Redefinir senha de Jessica" }).click();
    await page.getByLabel("Nova senha").fill("nova-senha-jessica-e2e");
    await page.getByRole("button", { name: "Salvar nova senha" }).click();
    await page.getByRole("button", { name: "Confirmar redefinição" }).click();
    await expect(page.getByRole("status")).toHaveText("Senha redefinida.");
  });

  test("admin lê a tratativa, mas não tem controle para editá-la", async ({ page }) => {
    await signIn(page, "admin");
    await expect(page.getByRole("button", { name: "Registrar tratativa" })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Ver histórico" }).first()).toBeVisible();
  });
});
