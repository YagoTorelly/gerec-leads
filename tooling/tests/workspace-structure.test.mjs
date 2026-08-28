import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

test("o workspace mantém a estrutura aprovada", () => {
  const requiredPaths = [
    "apps/web/package.json",
    "apps/api/.env.example",
    "scripts/start-mongodb.ps1",
    "scripts/stop-mongodb.ps1",
    "scripts/start-api.ps1",
    "scripts/start-web.ps1",
    "scripts/start-worker.ps1",
    "integrations/n8n/README.md",
    "tests/contracts/README.md",
  ];

  for (const relativePath of requiredPaths) {
    assert.equal(existsSync(resolve(root, relativePath)), true, relativePath);
  }

  const workspace = JSON.parse(readFileSync(resolve(root, "package.json"), "utf8"));
  const web = JSON.parse(readFileSync(resolve(root, "apps/web/package.json"), "utf8"));

  assert.equal(workspace.private, true);
  assert.deepEqual(workspace.workspaces, ["apps/*"]);
  assert.equal(workspace.engines.node, ">=24 <25");
  assert.equal(web.name, "@wtg/web");
  assert.equal(typeof web.scripts.dev, "string");
  assert.equal(typeof web.scripts.build, "string");
  assert.equal(typeof web.scripts.lint, "string");
  assert.equal(typeof web.scripts.typecheck, "string");

  for (const retiredPath of ["supabase", "tooling/supabase"]) {
    assert.equal(existsSync(resolve(root, retiredPath)), false, retiredPath);
  }

  for (const command of [
    "mongodb:start",
    "mongodb:stop",
    "mongodb:bootstrap",
    "api:start",
    "web:start",
    "worker:start",
  ]) {
    assert.equal(typeof workspace.scripts[command], "string", command);
  }

  assert.equal(JSON.stringify(workspace).match(/supabase|postgres|postgrest/i), null);
});
