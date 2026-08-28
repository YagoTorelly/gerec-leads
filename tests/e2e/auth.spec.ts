import { expect, test, type Page } from "@playwright/test";

const configured = Boolean(
  process.env.E2E_EMAIL && process.env.E2E_PASSWORD && process.env.E2E_DISABLED_EMAIL,
);

test.skip(!configured, "Requer credenciais E2E e API inicializada.");

async function signIn(page: Page) {
  await page.goto("/login");
  await page.getByLabel("E-mail").fill(process.env.E2E_EMAIL!);
  await page.getByLabel("Senha").fill(process.env.E2E_PASSWORD!);
  await page.getByRole("button", { name: "Entrar no sistema" }).click();
}

test("login encaminha sessão válida ao dashboard", async ({ page }) => {
  await signIn(page);

  await expect(page).toHaveURL(/\/dashboard$/);
  await expect(page.getByText("API Python")).toBeVisible();
});

test("usuário desativado não cria sessão", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("E-mail").fill(process.env.E2E_DISABLED_EMAIL!);
  await page.getByLabel("Senha").fill(process.env.E2E_PASSWORD!);
  await page.getByRole("button", { name: "Entrar no sistema" }).click();

  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByRole("alert")).toHaveText("Invalid credentials");
});
