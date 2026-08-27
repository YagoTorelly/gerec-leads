import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

test("Auth local impede cadastro público", () => {
  const config = readFileSync("supabase/config.toml", "utf8");
  const authSection = config.slice(config.indexOf("[auth]"), config.indexOf("[auth.rate_limit]"));
  const emailSection = config.slice(config.indexOf("[auth.email]"), config.indexOf("[auth.sms]"));
  assert.match(authSection, /enable_signup\s*=\s*false/);
  assert.match(emailSection, /enable_signup\s*=\s*false/);
});

test("configuração pública não contém chave administrativa", () => {
  const files = ["apps/web/.env.example", "README.md", "supabase/config.toml"];
  for (const file of files) {
    assert.doesNotMatch(readFileSync(file, "utf8"), /SERVICE_ROLE_KEY\s*=/i);
  }
});
