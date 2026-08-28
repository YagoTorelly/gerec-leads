import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const launcherPath = resolve(root, "scripts/start-local-stack.ps1");

test("launcher local cria processos com ambiente isolado, público e auditável", () => {
  assert.equal(existsSync(launcherPath), true);
  const launcher = readFileSync(launcherPath, "utf8");

  assert.match(launcher, /System\.Diagnostics\.ProcessStartInfo/);
  assert.match(launcher, /EnvironmentVariables\[\$entry\.Key\] = \$entry\.Value/);
  assert.match(launcher, /MONGODB_URI = \$MongoUri/);
  assert.match(launcher, /APP_SECRET = \$AppSecret/);
  assert.match(launcher, /\[switch\]\$PublicWebEnvironment/);
  assert.match(launcher, /EnvironmentVariables\.Clear\(\)/);
  assert.match(launcher, /-PublicWebEnvironment/);
  assert.match(launcher, /api\.log/);
  assert.match(launcher, /web\.log/);
  assert.match(launcher, /CreateNoWindow = \$true/);
  assert.doesNotMatch(launcher, /-MongoUri `"\$MongoUri`"/);
  assert.doesNotMatch(launcher, /-AppSecret `"\$AppSecret`"/);
});
