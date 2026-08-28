import { expect, test } from "@playwright/test";

const configured = Boolean(
  process.env.E2E_EMAIL &&
  process.env.E2E_PASSWORD &&
  process.env.E2E_SELLER_EMAIL &&
  process.env.API_CONTRACT_BASE_URL &&
  process.env.E2E_LIFECYCLE_LEAD_ID &&
  process.env.E2E_ATTEMPTS_LEAD_ID,
);

test.skip(!configured, "Requer dados E2E, API e sessão de vendedor.");

async function sellerApi(
  page: import("@playwright/test").Page,
  path: string,
  body: Record<string, unknown>,
) {
  const cookie = (await page.context().cookies()).find(({ name }) => name === "gerec_session");
  expect(cookie).toBeTruthy();
  return page.request.post(`${process.env.API_CONTRACT_BASE_URL}${path}`, {
    data: body,
    headers: { Cookie: `gerec_session=${cookie!.value}` },
  });
}

async function signIn(page: import("@playwright/test").Page) {
  await page.goto("/login");
  await page.getByLabel("E-mail").fill(process.env.E2E_SELLER_EMAIL!);
  await page.getByLabel("Senha").fill(process.env.E2E_PASSWORD!);
  await page.getByRole("button", { name: "Entrar no sistema" }).click();
  await expect(page).toHaveURL(/\/dashboard$/);
}

test("lead passa por contato, qualificação e venda única", async ({ page }) => {
  await signIn(page);
  const leadId = process.env.E2E_LIFECYCLE_LEAD_ID!;

  const feedback = await sellerApi(page, `/api/leads/${leadId}/feedbacks`, {
    comment: "Contato iniciado com retorno do cliente",
    contact_started: true,
    idempotency_key: "e2e-feedback",
  });
  const qualified = await sellerApi(page, `/api/leads/${leadId}/outcome`, {
    outcome: "qualified_follow_up",
    comment: "Cliente respondeu e pediu proposta",
    response_confirmed: true,
    idempotency_key: "e2e-qualified",
  });
  const won = await sellerApi(page, `/api/leads/${leadId}/outcome`, {
    outcome: "won",
    comment: "Venda confirmada pelo cliente",
    idempotency_key: "e2e-won",
  });
  const replay = await sellerApi(page, `/api/leads/${leadId}/outcome`, {
    outcome: "won",
    comment: "Venda confirmada pelo cliente",
    idempotency_key: "e2e-won",
  });

  for (const response of [feedback, qualified, won, replay]) expect(response.status()).toBe(200);
  expect(await replay.json()).toEqual(await won.json());
});

test("quinta tentativa habilita desqualificação manual", async ({ page }) => {
  await signIn(page);
  const leadId = process.env.E2E_ATTEMPTS_LEAD_ID!;
  const dates = ["2026-08-17", "2026-08-18", "2026-08-19", "2026-08-20", "2026-08-21"];

  for (const [index, business_date] of dates.entries()) {
    const response = await sellerApi(page, `/api/leads/${leadId}/attempts`, {
      comment: "Tentativa de contato sem resposta",
      business_date,
      idempotency_key: `e2e-attempt-${index}`,
    });
    expect(response.status()).toBe(200);
  }
  const outcome = await sellerApi(page, `/api/leads/${leadId}/outcome`, {
    outcome: "disqualified",
    comment: "Não atende após cinco tentativas válidas",
    disqualification_reason: "no_answer_after_5_attempts",
    idempotency_key: "e2e-disqualified",
  });

  expect(outcome.status()).toBe(200);
  expect((await outcome.json()).outcome).toBe("disqualified");
});
