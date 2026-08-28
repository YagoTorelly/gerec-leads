import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const requiredTerms = [
  "09:00",
  "18:00",
  "Bloqueado por atraso",
  "isDisqualified",
  "senha não vazia",
  "comentário",
  "Yago, André, Renato, Sandra, Jessica e Nelma",
];

test("GOV-004 formaliza a operação comercial, o SLA e as permissões aprovadas", async () => {
  const spec = await readFile("SPEC_GERENCIADOR_DE_LEADS_WTG.md", "utf8");

  assert.match(spec, /GOV-004 — Operação comercial, SLA e permissões/);
  for (const term of requiredTerms) assert.ok(spec.includes(term), `GOV-004 deve registrar ${term}`);
});

test("DEC-028 preserva a decisão de governança da reconstrução", async () => {
  const decisions = await readFile("docs/DECISOES.md", "utf8");

  assert.match(decisions, /DEC-028/);
  for (const term of requiredTerms) assert.ok(decisions.includes(term), `DEC-028 deve registrar ${term}`);
});
