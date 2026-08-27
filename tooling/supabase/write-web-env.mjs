import { execFileSync } from "node:child_process";
import { chmodSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { parseSupabaseStatusEnv, renderNextEnv } from "./parse-status-env.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const statusArguments = ["status", "-o", "env"];

export function runSupabaseStatusEnv({
  cliPath = resolve(root, "node_modules/supabase/dist/supabase.js"),
  cwd,
}) {
  return execFileSync(process.execPath, [cliPath, ...statusArguments], {
    cwd,
    encoding: "utf8",
  });
}

function writeWebEnv() {
  const status = runSupabaseStatusEnv({ cwd: root });
  const destination = resolve(root, "apps/web/.env.local");

  writeFileSync(destination, renderNextEnv(parseSupabaseStatusEnv(status)), {
    encoding: "utf8",
    mode: 0o600,
  });

  if (process.platform !== "win32") {
    chmodSync(destination, 0o600);
  }

  console.log("Ambiente web local criado com URL, chave publica e chave server-only.");
}

if (resolve(process.argv[1] ?? "") === fileURLToPath(import.meta.url)) {
  writeWebEnv();
}
