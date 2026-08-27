import { spawn } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { withoutNoColor } from "./sanitize-environment.mjs";

const toolingDirectory = dirname(fileURLToPath(import.meta.url));
const projectRoot = resolve(toolingDirectory, "../..");
const playwrightCli = resolve(projectRoot, "node_modules/playwright/cli.js");

const playwright = spawn(process.execPath, [playwrightCli, "test", ...process.argv.slice(2)], {
  cwd: projectRoot,
  env: withoutNoColor(process.env),
  stdio: "inherit",
});

playwright.once("error", (error) => {
  console.error(error);
  process.exitCode = 1;
});

playwright.once("exit", (code) => {
  process.exitCode = code ?? 1;
});
