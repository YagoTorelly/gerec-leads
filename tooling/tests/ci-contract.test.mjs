import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { parse } from "yaml";

const productRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const workflowPath = resolve(productRoot, "../.github/workflows/gerec-leads-ci.yml");

test("o CI permanece limitado ao Gerenciador de Leads", () => {
  const workflow = parse(readFileSync(workflowPath, "utf8"));

  assert.deepEqual(workflow.on.push.paths, ["gerec_leads/**"]);
  assert.deepEqual(workflow.on.pull_request.paths, ["gerec_leads/**"]);
  assert.deepEqual(workflow.permissions, { contents: "read" });
  assert.equal(workflow.defaults.run["working-directory"], "gerec_leads");

  const steps = workflow.jobs.quality.steps;
  assert.deepEqual(
    steps.flatMap((step) => (step.uses ? [step.uses] : [])),
    ["actions/checkout@v7", "actions/setup-node@v7"],
  );

  const setupNode = steps.find((step) => step.uses === "actions/setup-node@v7");
  assert.ok(setupNode);
  assert.equal(setupNode.with["node-version"], 24);
  assert.equal(setupNode.with["cache-dependency-path"], "gerec_leads/package-lock.json");

  assert.deepEqual(
    steps.flatMap((step) => (step.run ? [step.run] : [])),
    [
      "npm ci",
      "npm run test:e2e:install:ci",
      "npm run supabase:start",
      "npm run env:local",
      "npm run check",
      "npm run test:e2e",
      "npm run supabase:stop",
    ],
  );

  const stopSupabase = steps.find((step) => step.run === "npm run supabase:stop");
  assert.equal(stopSupabase?.if, "always()");

  const serializedWorkflow = JSON.stringify(workflow);
  assert.equal(serializedWorkflow.includes("${{ secrets."), false);
});
