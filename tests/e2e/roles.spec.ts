import { expect, test } from "@playwright/test";

import { resetFixture, signIn } from "./fixture";

test.beforeEach(async ({ page }) => resetFixture(page));

test("administrador vê a navegação global e Jessica como próxima na fila", async ({ page }) => {
  await signIn(page, "admin");
  await expect(page.getByRole("link", { name: "Usuários" })).toBeVisible();
  await expect(page.getByText("Próximo vendedor")).toBeVisible();
  await expect(page.getByText("Jessica", { exact: true }).first()).toBeVisible();

  await page.getByRole("link", { name: "Fila de leads" }).click();
  await expect(page.getByText("Próximo elegível")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Fila comercial" }).first()).toBeVisible();
});

test("vendedor só vê a própria operação nas páginas separadas", async ({ page }) => {
  await signIn(page, "seller");
  await expect(page.getByRole("link", { name: "Usuários" })).toHaveCount(0);
  await expect(page.getByText("Lead Jessica 1", { exact: true })).toBeVisible();
  await expect(page.getByText("Renato", { exact: true })).toHaveCount(0);

  await page.getByRole("link", { name: "Minha fila" }).click();
  await expect(page).toHaveURL(/\/fila$/);
  await expect(page.getByRole("heading", { name: "Minha fila" }).first()).toBeVisible();
  await expect(page.getByText("Lead Jessica 1", { exact: true })).toBeVisible();

  await page.getByRole("link", { name: "Minhas tratativas" }).click();
  await expect(page).toHaveURL(/\/historico$/);
  await expect(page.getByRole("heading", { name: "Minhas tratativas" }).first()).toBeVisible();
  await expect(page.getByRole("heading", { name: "Tratativas", exact: true })).toBeVisible();
  await expect(page.getByText("Renato", { exact: true })).toHaveCount(0);

  await page.goto("/usuarios");
  await expect(page).toHaveURL(/\/dashboard$/);
});
