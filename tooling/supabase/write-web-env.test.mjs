import assert from "node:assert/strict";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { runSupabaseStatusEnv } from "./write-web-env.mjs";

test("executa o launcher do Supabase de forma portável", () => {
  const temporaryRoot = mkdtempSync(join(tmpdir(), "gerec-supabase-"));
  const launcherDirectory = join(temporaryRoot, "launcher com espaco");
  mkdirSync(launcherDirectory);

  const launcher = join(launcherDirectory, "supabase-fixture.mjs");
  const source = [
    "console.log('API_URL=\"http://127.0.0.1:55321\"');",
    "console.log('ANON_KEY=\"public-test-key\"');",
  ].join("\n");

  try {
    writeFileSync(launcher, source, "utf8");

    const status = runSupabaseStatusEnv({
      cliPath: launcher,
      cwd: temporaryRoot,
    });

    assert.match(status, /API_URL="http:\/\/127\.0\.0\.1:55321"/);
    assert.match(status, /ANON_KEY="public-test-key"/);
  } finally {
    rmSync(temporaryRoot, { recursive: true, force: true });
  }
});
