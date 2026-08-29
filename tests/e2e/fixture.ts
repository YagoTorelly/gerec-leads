import { expect, type Page } from "@playwright/test";

/** Dados públicos e descartáveis do processo E2E local. Nunca são credenciais reais. */
export const E2E_USERS = {
  admin: { email: "yago.e2e@wtg.test", password: "teste-local-wtg" },
  seller: { email: "jessica.e2e@wtg.test", password: "teste-local-wtg" },
} as const;

export async function signIn(page: Page, user: keyof typeof E2E_USERS): Promise<void> {
  const credentials = E2E_USERS[user];
  await page.goto("/login");
  await page.getByLabel("E-mail").fill(credentials.email);
  await page.getByLabel("Senha").fill(credentials.password);
  await page.getByRole("button", { name: "Entrar no sistema" }).click();
  await expect(page).toHaveURL(/\/dashboard$/);
}

/** Controle exclusivo do processo local E2E; os comandos do produto seguem pela interface. */
export async function resetFixture(page: Page): Promise<void> {
  const response = await page.request.post("http://127.0.0.1:18012/__e2e/reset");
  expect(response.status()).toBe(204);
}
