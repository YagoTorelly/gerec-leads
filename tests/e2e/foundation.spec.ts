import { expect, test } from "@playwright/test";

test("exibe a aplicação e a conexão local", async ({ page }) => {
  await page.goto("/");

  const heading = page.getByRole("heading", { level: 1, name: "Gerenciador de Leads WTG" });

  await expect(heading).toBeVisible();
  await expect(page.locator('meta[name="theme-color"]')).toHaveAttribute("content", "#f3f5f4");
  await expect(heading).toHaveCSS("text-wrap", "balance");
  await expect(page.getByText("Supabase local conectado")).toBeVisible();
});
