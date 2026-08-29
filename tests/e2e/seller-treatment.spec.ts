import { expect, test } from "@playwright/test";

import { resetFixture, signIn } from "./fixture";

test.describe("tratativas do vendedor", () => {
  test.beforeEach(async ({ page }) => resetFixture(page));
  test("vendedor valida comentário curto e registra negociação atualizando contador e situação", async ({
    page,
  }) => {
    await signIn(page, "seller");
    const lead = page.getByRole("row").filter({ hasText: "Lead Jessica 1" });
    await expect(lead).toBeVisible();
    await expect(lead).toContainText("0 comentários");
    await expect(page.getByText("Renato")).toHaveCount(0);

    await lead.getByRole("button", { name: "Registrar tratativa" }).click();
    await page.getByLabel("Comentário").fill("curto");
    await expect(page.getByRole("button", { name: "Salvar tratativa" })).toBeDisabled();
    await page.getByLabel("Comentário").fill("Cliente pediu uma proposta detalhada.");
    await page.getByLabel("Situação comercial").selectOption("negotiation");
    await page.getByRole("button", { name: "Salvar tratativa" }).click();
    await expect(page.getByRole("status")).toHaveText("Tratativa registrada.");
    await expect(lead).toContainText("Negociação");
    await expect(lead).toContainText("1 comentário");
  });

  test("desqualificação com comentário encerra SLA e mostra marcador", async ({ page }) => {
    await signIn(page, "seller");
    const lead = page.getByRole("row").filter({ hasText: "Lead Jessica 1" });
    await lead.getByRole("button", { name: "Registrar tratativa" }).click();
    await page.getByLabel("Comentário").fill("Cliente não se enquadra no escopo comercial.");
    await page.getByLabel("Marcar como Desqualificado").check();
    await page.getByRole("button", { name: "Salvar tratativa" }).click();
    await expect(page.getByRole("status")).toHaveText("Tratativa registrada.");
    await expect(lead).toContainText("Desqualificado");
    await expect(lead).toContainText("Não informado");
  });
});
