import { expect, test } from "@playwright/test";

import { E2E_USERS, resetFixture, signIn } from "./fixture";

test.beforeEach(async ({ page }) => resetFixture(page));

test("login com conta fixture encaminha ao dashboard", async ({ page }) => {
  await signIn(page, "admin");
  await expect(page.getByRole("heading", { name: "Visão geral" })).toBeVisible();
});

test("senha inválida não cria sessão", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("E-mail").fill(E2E_USERS.admin.email);
  await page.getByLabel("Senha").fill("senha-incorreta-local");
  await page.getByRole("button", { name: "Entrar no sistema" }).click();

  await expect(page).toHaveURL(/\/login$/);
  await expect(page.locator(".form-error")).toHaveText("Sessão expirada. Entre novamente.");
});
