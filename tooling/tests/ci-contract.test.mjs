import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { parse } from "yaml";

const productRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const workflowPath = resolve(productRoot, ".github/workflows/gerec-leads-ci.yml");

test("CI inicia stack Mongo, API e web antes dos contratos e E2E", () => {
  const workflow = parse(readFileSync(workflowPath, "utf8"));
  const steps = workflow.jobs.quality.steps;
  const commands = steps.flatMap((step) => (step.run ? [step.run] : []));

  assert.deepEqual(workflow.permissions, { contents: "read" });
  assert.deepEqual(
    steps.flatMap((step) => (step.uses ? [step.uses] : [])),
    ["actions/checkout@v7", "actions/setup-node@v7", "actions/setup-python@v6"],
  );
  assert.ok(commands.some((command) => command.includes("npm ci")));
  assert.ok(commands.some((command) => command.includes("npm run test:e2e:install:ci")));
  assert.ok(
    commands.some((command) => command.includes('python -m pip install -e "apps/api[dev]"')),
  );
  assert.ok(
    commands.some((command) =>
      command.includes("docker compose -f infra/mongodb/docker-compose.yml up -d"),
    ),
  );
  assert.ok(commands.some((command) => command.includes("gerec_api.main:create_app")));
  assert.equal(commands.some((command) => command.includes("npm run dev")), false);
  assert.ok(commands.includes("python -m pytest apps/api/tests -q"));
  assert.equal(commands.includes("npm run check"), false);
  const scopedWeb = steps.find((step) => step.name === "Validar TypeScript e testes web escopados");
  assert.match(scopedWeb?.run ?? "", /npm run lint\s+npm run typecheck\s+npm run test/);
  assert.ok(commands.includes("npm run test:contracts"));
  assert.ok(commands.includes("npm run test:e2e"));

  const cleanup = steps.find((step) => step.name === "Encerrar serviços");
  assert.equal(cleanup?.if, "always()");
  assert.match(cleanup?.run ?? "", /docker compose .* down --volumes/);
  assert.equal(JSON.stringify(workflow).includes("${{ secrets."), false);
  assert.equal(
    steps.find((step) => step.name === "Registrar format check legado")?.["continue-on-error"],
    true,
  );
  assert.equal(
    steps.find((step) => step.name === "Registrar format check legado")?.run,
    "npm run format:check",
  );
  assert.equal("APP_SECRET" in workflow.jobs.quality.env, false);
  assert.equal("E2E_PASSWORD" in workflow.jobs.quality.env, false);
  assert.ok(commands.some((command) => command.includes("openssl rand")));
});
