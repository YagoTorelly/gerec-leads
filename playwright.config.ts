import { defineConfig, devices } from "@playwright/test";

import { withoutNoColor } from "./tooling/playwright/sanitize-environment.mjs";

const webServerEnvironment = withoutNoColor(process.env);
const useExternalFixture = process.env.E2E_EXTERNAL === "1";
const baseURL = useExternalFixture
  ? (process.env.E2E_BASE_URL ?? "http://127.0.0.1:3000")
  : "http://127.0.0.1:3000";

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false,
  workers: 1,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL,
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 1440, height: 900 },
      },
    },
  ],
  snapshotPathTemplate: "{testDir}/visual/{testFilePath}/{arg}{ext}",
  webServer: useExternalFixture
    ? undefined
    : {
        command: "node tooling/playwright/e2e-fixture-stack.mjs",
        env: webServerEnvironment,
        url: baseURL,
        reuseExistingServer: !process.env.CI,
        timeout: 120_000,
      },
});
