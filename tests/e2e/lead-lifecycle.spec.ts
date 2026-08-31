import { expect, test } from "@playwright/test";

import { resetFixture, signIn } from "./fixture";

test.beforeEach(async ({ page }) => resetFixture(page));

test("fila e histórico usam paginação semântica e dados legíveis", async ({ page }) => {
  await signIn(page, "admin");
  await page.getByRole("link", { name: "Fila de leads" }).click();
  const queueTable = page.getByRole("region", { name: "Fila comercial" }).getByRole("table");
  await expect(queueTable).toContainText("Renato");
  await expect(queueTable).toContainText("Jessica");
  await expect(page.getByText("Próximo elegível")).toBeVisible();

  await page.getByRole("link", { name: "Histórico" }).click();
  await expect(page.getByRole("region", { name: "Tratativas" })).toContainText("Lead Nelma 1");
  await expect(page.getByRole("button", { name: "Página anterior" })).toBeDisabled();
  await expect(page.getByRole("button", { name: "Próxima página" })).toBeDisabled();
});
