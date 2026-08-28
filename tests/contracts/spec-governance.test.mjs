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

const requiredRelations = [
  "Ambos impedem somente novas atribuições e preservam os leads existentes.",
  "Pausa manual é definida e removida somente pelo administrador.",
  "Bloqueado por atraso é derivado de qualquer ciclo de SLA aberto vencido.",
  "cessa automaticamente após a regularização de todos os ciclos vencidos.",
  "Quando coexistirem, Pausado prevalece na apresentação e na elegibilidade.",
  "A regularização não devolve turnos perdidos.",
  "O vendedor atualmente responsável é o único autor de tratativa.",
  "O administrador possui somente leitura global da tratativa.",
];

function governanceBlock(spec) {
  const match = spec.match(/### GOV-004 — Operação comercial, SLA e permissões\r?\n([\s\S]*?)(?=\r?\n---)/);
  assert.ok(match, "GOV-004 deve existir como bloco de governança");
  return match[0];
}

function decisionLine(decisions) {
  const match = decisions.match(/^\| DEC-028 \|.*$/m);
  assert.ok(match, "DEC-028 deve existir como linha de decisão");
  return match[0];
}

function assertFormalizedDecision(document, name) {
  for (const term of requiredTerms) assert.ok(document.includes(term), `${name} deve registrar ${term}`);
  for (const relation of requiredRelations)
    assert.ok(document.includes(relation), `${name} deve registrar: ${relation}`);
}

test("GOV-004 formaliza a operação comercial, o SLA e as permissões aprovadas", async () => {
  const spec = await readFile("SPEC_GERENCIADOR_DE_LEADS_WTG.md", "utf8");

  assertFormalizedDecision(governanceBlock(spec), "GOV-004");
});

test("DEC-028 preserva a decisão de governança da reconstrução", async () => {
  const decisions = await readFile("docs/DECISOES.md", "utf8");

  assertFormalizedDecision(decisionLine(decisions), "DEC-028");
});
