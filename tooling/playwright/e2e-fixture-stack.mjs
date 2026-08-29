import { spawn } from "node:child_process";
import { resolve } from "node:path";
import { createE2eFixtureServer } from "./e2e-fixture-api.mjs";

const apiPort = Number(process.env.E2E_FIXTURE_API_PORT ?? "18012");
const webPort = Number(process.env.E2E_WEB_PORT ?? "3000");
const api = createE2eFixtureServer();
let next;

function stop(code = 0) {
  if (next && next.exitCode === null) next.kill("SIGTERM");
  api.close(() => process.exit(code));
}

api.listen(apiPort, "127.0.0.1", () => {
  next = spawn(
    process.execPath,
    [resolve("node_modules/next/dist/bin/next"), "dev", "--port", String(webPort)],
    {
      cwd: resolve("apps/web"),
      env: { ...process.env, NEXT_PUBLIC_API_URL: `http://127.0.0.1:${apiPort}`, E2E_FIXTURE: "1" },
      stdio: "inherit",
    },
  );
  next.once("exit", (code) => stop(code ?? 1));
});

process.once("SIGINT", () => stop());
process.once("SIGTERM", () => stop());
