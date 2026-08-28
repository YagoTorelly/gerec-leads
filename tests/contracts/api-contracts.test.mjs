import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { randomBytes } from "node:crypto";
import { once } from "node:events";
import { dirname, resolve } from "node:path";
import test, { after, before } from "node:test";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const port = 18011;
const baseUrl = `http://127.0.0.1:${port}`;
const serverPath = resolve(root, "tests/contracts/api-contract-server.py");
let server;
const testPassword = randomBytes(24).toString("base64url");
const invalidPassword = randomBytes(24).toString("base64url");
const appSecret = randomBytes(32).toString("hex");

async function waitForServer() {
  for (let attempt = 0; attempt < 40; attempt += 1) {
    try {
      const response = await fetch(`${baseUrl}/health`);
      if (response.ok) return;
    } catch {
      // O processo Python ainda está subindo.
    }
    await new Promise((resolveDelay) => setTimeout(resolveDelay, 100));
  }
  throw new Error("Servidor controlado de contrato não iniciou.");
}

before(async () => {
  server = spawn("python", [serverPath, "--port", String(port)], {
    cwd: root,
    env: {
      ...process.env,
      PYTHONPATH: resolve(root, "apps/api/src"),
      CONTRACT_TEST_APP_SECRET: appSecret,
      CONTRACT_TEST_PASSWORD: testPassword,
    },
    stdio: "pipe",
  });
  await waitForServer();
});

after(async () => {
  if (!server || server.exitCode !== null) return;
  server.kill("SIGTERM");
  await once(server, "exit");
});

async function request(path, init) {
  const response = await fetch(`${baseUrl}${path}`, init);
  assert.match(response.headers.get("content-type") ?? "", /application\/json/i);
  assert.equal(response.headers.get("x-gerec-api-contract-version"), "1");
  return { response, body: await response.json() };
}

async function login() {
  const result = await request("/auth/login", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ email: "admin.contract@test", password: testPassword }),
  });
  const token = result.response.headers.get("set-cookie")?.match(/gerec_session=([^;]+)/)?.[1];
  assert.ok(token);
  return { ...result, cookie: `gerec_session=${token}` };
}

test("contrato versionado expõe health e autenticação pública mínima", async () => {
  const health = await request("/health");
  const authenticated = await login();
  const me = await request("/auth/me", { headers: { Cookie: authenticated.cookie } });
  const invalid = await request("/auth/login", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ email: "admin.contract@test", password: invalidPassword }),
  });

  assert.deepEqual(health.body, { status: "ok", database: "gerec_contracts" });
  assert.equal(authenticated.response.status, 200);
  assert.deepEqual(authenticated.body.user, {
    id: "000000000000000000000001",
    email: "admin.contract@test",
    role: "admin",
  });
  assert.deepEqual(me.body, authenticated.body.user);
  assert.deepEqual(invalid.body, { detail: "Invalid credentials" });
  assert.equal(invalid.response.status, 401);
});

test("contrato valida erros e limites de leads, queue, operations e admin", async () => {
  const session = await login();
  const [leads, queue, operations, admin] = await Promise.all([
    request("/api/internal/imports/google-sheets/sync", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: "{}",
    }),
    request("/api/internal/queue/leads/not-an-id/distribute-normal", {
      method: "POST",
      headers: { "content-type": "application/json", "X-Internal-Key": appSecret },
      body: JSON.stringify({ command_id: "contract-queue" }),
    }),
    request("/api/leads/not-an-id/feedbacks", {
      method: "POST",
      headers: { "content-type": "application/json", Cookie: session.cookie },
      body: JSON.stringify({
        comment: "Contato válido",
        contact_started: true,
        idempotency_key: "contract-operation",
      }),
    }),
    request("/api/admin/users?page=1&limit=50", { headers: { Cookie: session.cookie } }),
  ]);

  assert.equal(leads.response.status, 422);
  assert.ok(Array.isArray(leads.body.detail));
  assert.deepEqual(queue.body, { detail: "Invalid object id" });
  assert.equal(queue.response.status, 422);
  assert.deepEqual(operations.body, { detail: "Invalid object id" });
  assert.equal(operations.response.status, 422);
  assert.equal(admin.response.status, 200);
  assert.equal(admin.body.page, 1);
  assert.equal(admin.body.pageSize, 50);
  assert.equal(admin.body.total, 1);
  assert.deepEqual(admin.body.items[0], {
    id: "000000000000000000000001",
    emailNormalized: "admin.contract@test",
    role: "admin",
    active: true,
    createdAt: "2026-08-28T00:00:00Z",
  });
  assert.equal("passwordHash" in admin.body.items[0], false);
});
