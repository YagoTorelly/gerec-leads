import { expect, test } from "@playwright/test";

import { resetFixture, signIn } from "./fixture";

test.beforeEach(async ({ page }) => resetFixture(page));

test("referências visuais administrativas em desktop", async ({ page }) => {
  await signIn(page, "admin");
  await expect(page).toHaveScreenshot("admin-dashboard.png", { animations: "disabled" });

  await page.getByRole("link", { name: "Usuários" }).click();
  await page.getByRole("button", { name: "Novo usuário" }).click();
  await expect(page).toHaveScreenshot("admin-users-modal.png", { animations: "disabled" });

  await page.getByRole("button", { name: "Cancelar" }).click();
  await page.getByRole("link", { name: "Fila de leads" }).click();
  await expect(page).toHaveScreenshot("admin-queue.png", { animations: "disabled" });

  await page.getByRole("link", { name: "Histórico" }).click();
  await expect(page).toHaveScreenshot("admin-history.png", { animations: "disabled" });
});

test("referências visuais do vendedor em desktop", async ({ page }) => {
  await signIn(page, "seller");
  await expect(page).toHaveScreenshot("seller-dashboard.png", { animations: "disabled" });

  await page
    .getByRole("row")
    .filter({ hasText: "Lead Jessica 1" })
    .getByRole("button", { name: "Registrar tratativa" })
    .click();
  await expect(page).toHaveScreenshot("seller-treatment-modal.png", { animations: "disabled" });
});
