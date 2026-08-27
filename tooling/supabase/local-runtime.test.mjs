import assert from "node:assert/strict";
import test from "node:test";

import { parseLocalRuntimeEnv } from "./local-runtime.mjs";

test("parser usa publishable key e preserva service role em memória", () => {
  const runtime = parseLocalRuntimeEnv(
    [
      'API_URL="http://127.0.0.1:55321"',
      'PUBLISHABLE_KEY="public-key"',
      'SERVICE_ROLE_KEY="server-only-key"',
    ].join("\n"),
  );

  assert.deepEqual(runtime, {
    apiUrl: "http://127.0.0.1:55321",
    publishableKey: "public-key",
    serviceRoleKey: "server-only-key",
  });
});

test("parser rejeita runtime sem chave administrativa", () => {
  assert.throws(
    () => parseLocalRuntimeEnv("API_URL=http://127.0.0.1:55321\nANON_KEY=public-key"),
    /configuração administrativa completa/,
  );
});
