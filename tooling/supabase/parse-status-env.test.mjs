import assert from "node:assert/strict";
import test from "node:test";

import { parseSupabaseStatusEnv, renderNextEnv } from "./parse-status-env.mjs";

test("usa PUBLISHABLE_KEY como chave pública", () => {
  const source = [
    'API_URL="http://127.0.0.1:54321"',
    'PUBLISHABLE_KEY="publishable-local-key"',
    'SERVICE_ROLE_KEY="never-expose-this"',
  ].join("\n");

  const parsed = parseSupabaseStatusEnv(source);

  assert.deepEqual(parsed, {
    NEXT_PUBLIC_SUPABASE_URL: "http://127.0.0.1:54321",
    NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY: "publishable-local-key",
    SUPABASE_SERVICE_ROLE_KEY: "never-expose-this",
  });
});

test("usa ANON_KEY como fallback quando PUBLISHABLE_KEY não existe", () => {
  const parsed = parseSupabaseStatusEnv(
    ['API_URL="http://127.0.0.1:54321"', 'ANON_KEY="anon-local-key"'].join("\n"),
  );

  assert.equal(parsed.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY, "anon-local-key");
});

test("PUBLISHABLE_KEY tem precedência quando as duas chaves existem", () => {
  const parsed = parseSupabaseStatusEnv(
    [
      'API_URL="http://127.0.0.1:54321"',
      'PUBLISHABLE_KEY="publishable-local-key"',
      'ANON_KEY="anon-local-key"',
    ].join("\n"),
  );

  assert.equal(parsed.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY, "publishable-local-key");
});

test("recusa configuração pública incompleta", () => {
  assert.throws(
    () => parseSupabaseStatusEnv('PUBLISHABLE_KEY="publishable-local-key"'),
    /URL ou chave pública/i,
  );
  assert.throws(
    () => parseSupabaseStatusEnv('API_URL="http://127.0.0.1:54321"'),
    /URL ou chave pública/i,
  );
});

test("renderiza URL pública e chave administrativa apenas para o servidor", () => {
  const parsed = parseSupabaseStatusEnv(
    [
      'API_URL="http://127.0.0.1:54321"',
      'PUBLISHABLE_KEY="publishable-local-key"',
      'SERVICE_ROLE_KEY="never-expose-this"',
    ].join("\n"),
  );

  assert.equal(
    renderNextEnv(parsed),
    [
      "NEXT_PUBLIC_SUPABASE_URL=http://127.0.0.1:54321",
      "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=publishable-local-key",
      "SUPABASE_SERVICE_ROLE_KEY=never-expose-this",
      "",
    ].join("\n"),
  );
});
