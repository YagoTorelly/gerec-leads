import assert from "node:assert/strict";
import test from "node:test";

const baseUrl = process.env.API_CONTRACT_BASE_URL?.replace(/\/$/, "");
const version = "1";

async function request(path, init) {
  const response = await fetch(`${baseUrl}${path}`, init);
  const contentType = response.headers.get("content-type") ?? "";
  assert.match(contentType, /application\/json/i);
  assert.equal(response.headers.get("x-gerec-api-contract-version"), version);
  return { response, body: await response.json() };
}

test("contrato Vercel-Railway expõe versão e health mínimo", { skip: !baseUrl }, async () => {
  const { response, body } = await request("/health");

  assert.equal(response.status, 200);
  assert.equal(body.status, "ok");
  assert.equal(typeof body.database, "string");
});

test("contrato rejeita payloads inválidos em auth e imports", { skip: !baseUrl }, async () => {
  const auth = await request("/auth/login", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: "{}",
  });
  const leads = await request("/api/internal/imports/google-sheets/sync", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: "{}",
  });

  assert.equal(auth.response.status, 422);
  assert.ok(Array.isArray(auth.body.detail));
  assert.equal(leads.response.status, 422);
  assert.ok(Array.isArray(leads.body.detail));
});

test("contrato mantém limites HTTP de queue, operations e admin", { skip: !baseUrl }, async () => {
  const [queue, operations, admin] = await Promise.all([
    request("/api/internal/queue/leads/not-an-id/distribute-normal", { method: "GET" }),
    request("/api/leads/not-an-id/feedbacks", { method: "GET" }),
    request("/api/admin/users", { method: "OPTIONS" }),
  ]);

  assert.equal(queue.response.status, 405);
  assert.equal(operations.response.status, 405);
  assert.equal(admin.response.status, 405);
  for (const { body } of [queue, operations, admin]) assert.equal(typeof body.detail, "string");
});
