import { expect, test } from "@playwright/test";

const configured = Boolean(
  process.env.E2E_EMAIL && process.env.E2E_PASSWORD && process.env.E2E_SELLER_EMAIL,
);

test.skip(!configured, "Requer usuários E2E e API inicializada.");

async function signIn(page: import("@playwright/test").Page, email: string) {
  await page.goto("/login");
  await page.getByLabel("E-mail").fill(email);
  await page.getByLabel("Senha").fill(process.env.E2E_PASSWORD!);
  await page.getByRole("button", { name: "Entrar no sistema" }).click();
  await expect(page).toHaveURL(/\/dashboard$/);
}

test("administrador vê navegação global", async ({ page }) => {
  await signIn(page, process.env.E2E_EMAIL!);

  await expect(page.getByRole("link", { name: "Usuários" })).toBeVisible();
  await page.getByRole("link", { name: "Usuários" }).click();
  await expect(page).toHaveURL(/\/usuarios$/);
  await expect(page.getByText(process.env.E2E_SELLER_EMAIL!)).toBeVisible();
});

test("vendedor não vê colegas nem controle administrativo", async ({ page }) => {
  await signIn(page, process.env.E2E_SELLER_EMAIL!);

  await expect(page.getByRole("link", { name: "Usuários" })).toHaveCount(0);
  await expect(page.getByText("Lead privado do vendedor")).toBeVisible();
  await expect(page.getByText("Lead da Jessica")).toHaveCount(0);
});
