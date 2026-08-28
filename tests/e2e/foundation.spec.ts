import { expect, test } from "@playwright/test";

test("redireciona visitante ao login", async ({ page }) => {
  await page.goto("/");

  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByRole("heading", { name: /gerenciador de leads/i })).toBeVisible();
  await expect(page.getByRole("button", { name: "Entrar no sistema" })).toBeVisible();
});
