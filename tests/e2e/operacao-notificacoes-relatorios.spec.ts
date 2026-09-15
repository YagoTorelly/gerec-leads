import { expect, test, type Page } from "@playwright/test";

import { resetFixture } from "./fixture";

const fixturePassword = "teste-local-wtg";

async function signInAs(page: Page, email: string): Promise<void> {
  await page.goto("/login");
  await page.getByLabel("E-mail").fill(email);
  await page.getByLabel("Senha").fill(fixturePassword);
  await page.getByRole("button", { name: "Entrar no sistema" }).click();
  await expect(page).toHaveURL(/\/dashboard$/);
}

test.describe("notificações internas, tratativas e relatórios", () => {
  test.beforeEach(async ({ page }) => resetFixture(page));

  test("vendedora vê novos leads, registra Potencial e remove o marcador atual", async ({ page }) => {
    await signInAs(page, "sandra.e2e@wtg.test");
    await expect(page.getByRole("dialog", { name: "Novos leads" })).toBeVisible();
    await page.getByRole("button", { name: "Fechar" }).click();

    const lead = page.getByRole("row").filter({ hasText: "Wesley Souza" });
    await expect(lead).toContainText("Desqualificado");
    await lead.getByRole("button", { name: "Registrar tratativa" }).click();
    await page.getByLabel("Situação comercial").selectOption("potential");
    await page.getByLabel("Marcar como Desqualificado").uncheck();
    await page.getByLabel("Comentário").fill("Cliente pediu nova proposta comercial");
    await page.getByRole("button", { name: "Salvar tratativa" }).click();

    await expect(page.getByRole("status")).toHaveText("Tratativa registrada.");
    await expect(lead).toContainText("Potencial");
    await expect(lead).not.toContainText("Desqualificado");
  });

  test("administrador filtra leads por responsável e visualiza relatórios", async ({ page }) => {
    await signInAs(page, "yago.e2e@wtg.test");
    await page.getByLabel("Responsável").selectOption({ label: "Sandra" });
    await expect(page).toHaveURL(/assigneeId=seller-sandra/);
    await expect(page.getByRole("row").filter({ hasText: "Wesley Souza" })).toBeVisible();
    await expect(page.getByText("Lead Jessica 1", { exact: true })).toHaveCount(0);

    await page.getByRole("link", { name: "Relatórios" }).click();
    await expect(page.getByRole("heading", { name: "Por situação" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Por vendedor" })).toBeVisible();
  });

  test("vendedora é redirecionada sem consultar a distribuição administrativa", async ({ page }) => {
    const reportRequests: string[] = [];
    page.on("request", (request) => {
      if (request.url().includes("/api/admin/reports/lead-distribution")) reportRequests.push(request.url());
    });

    await signInAs(page, "sandra.e2e@wtg.test");
    await page.goto("/relatorios");

    await expect(page).toHaveURL(/\/dashboard$/);
    await expect(page.getByRole("link", { name: "Relatórios" })).toHaveCount(0);
    expect(reportRequests).toEqual([]);
  });
});
