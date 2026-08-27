# Etapa 1 — Esqueleto executável Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar um workspace local reproduzível com Next.js, Supabase via Docker, testes, qualidade automatizada e uma página mínima que comprove a conexão, sem implementar regras de negócio.

**Architecture:** Um workspace npm concentra a aplicação Next.js em `apps/web`; o Supabase CLI controla a infraestrutura local em `supabase`; scripts pequenos em `tooling` isolam configuração e verificações. O navegador recebe somente URL e chave pública local. O único arquivo externo ao diretório do produto é o workflow de descoberta obrigatória do GitHub Actions.

**Tech Stack:** Node.js 24 LTS, npm workspaces, Next.js 16/App Router, React, TypeScript, Supabase CLI 2.115.0, Docker, Vitest 4.1.11, Playwright 1.62.1, YAML 2.8.1, ESLint e Prettier 3.9.6.

**Spec:** `gerec_leads/SPEC_GERENCIADOR_DE_LEADS_WTG.md`, `gerec_leads/ROADMAP.md`, `gerec_leads/docs/ARQUITETURA.md` e `gerec_leads/docs/DECISOES.md`.

## Global Constraints

- [ ] Ler integralmente `SPEC_GERENCIADOR_DE_LEADS_WTG.md` antes de iniciar a execução.
- [ ] Trabalhar somente em `gerec_leads/`, exceto pelo arquivo autorizado `.github/workflows/gerec-leads-ci.yml`.
- [ ] Não criar tabelas comerciais, migrações de domínio, usuários, RLS, fila, campanhas, integrações reais ou telas definitivas nesta etapa.
- [ ] Não copiar código das pastas legadas. Materiais legados continuam disponíveis apenas como referência visual futura.
- [ ] Nunca versionar `.env.local`, chaves administrativas, `service_role`, dados pessoais ou saída sensível do Supabase.
- [ ] Tratar a interface como exclusivamente desktop, com largura mínima suportada de 1280 px; não implementar nem prometer suporte funcional a tablet ou celular.
- [ ] Usar `apply_patch` para edições manuais e preservar mudanças preexistentes do usuário.
- [ ] Seguir TDD em cada unidade criada: teste falhando, implementação mínima, teste passando e verificação de regressão.
- [ ] Não avançar para uma tarefa enquanto o gate da tarefa atual não passar.
- [ ] Fazer commits pequenos nos pontos indicados, sem incluir alterações alheias ao plano.

## Matriz de arquivos e responsabilidades

| Caminho | Responsabilidade na Etapa 1 |
|---|---|
| `gerec_leads/package.json` | Scripts e dependências compartilhados do workspace. |
| `gerec_leads/package-lock.json` | Instalação determinística de todas as dependências. |
| `gerec_leads/.nvmrc` | Runtime Node.js local padronizado. |
| `gerec_leads/apps/web/` | Aplicação Next.js e diagnóstico da conexão local. |
| `gerec_leads/supabase/` | Configuração gerada pelo Supabase CLI, sem domínio comercial. |
| `gerec_leads/tooling/` | Testes estruturais e scripts locais sem regra de negócio. |
| `gerec_leads/tests/e2e/` | Teste ponta a ponta da fundação. |
| `gerec_leads/integrations/n8n/` | Limite documentado para workflows futuros; nenhuma conexão real agora. |
| `gerec_leads/WTG - Leads.xlsx` | Fixture mock A–Q fornecido pelo usuário e já versionado no pré-requisito; não modificar na Etapa 1. |
| `.github/workflows/gerec-leads-ci.yml` | Entrada mínima do GitHub Actions, limitada ao workspace. |

---

### Task 1: Fixar o runtime e criar o workspace Next.js vazio

**Files:**

- Create: `gerec_leads/.nvmrc`
- Create: `gerec_leads/package.json`
- Create: `gerec_leads/package-lock.json`
- Create: `gerec_leads/apps/web/**`
- Create: `gerec_leads/integrations/n8n/README.md`
- Create: `gerec_leads/tests/contracts/README.md`
- Create: `gerec_leads/tooling/tests/workspace-structure.test.mjs`

- [ ] **Step 1: Confirmar o runtime disponível e selecionar Node.js 24**

Executar na raiz do repositório:

```powershell
node --version
npm --version
nvm version
```

Se a versão principal do Node não for 24:

```powershell
nvm install 24
nvm use 24
node --version
```

Esperado: `node --version` começa com `v24.`. Não continuar com Node 20.

- [ ] **Step 2: Escrever primeiro o teste estrutural**

Criar `gerec_leads/tooling/tests/workspace-structure.test.mjs`:

```js
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

test("o workspace mantém a estrutura aprovada", () => {
  const requiredPaths = [
    "apps/web/package.json",
    "integrations/n8n/README.md",
    "tests/contracts/README.md",
  ];

  for (const relativePath of requiredPaths) {
    assert.equal(existsSync(resolve(root, relativePath)), true, relativePath);
  }

  const workspace = JSON.parse(
    readFileSync(resolve(root, "package.json"), "utf8"),
  );
  const web = JSON.parse(
    readFileSync(resolve(root, "apps/web/package.json"), "utf8"),
  );

  assert.equal(workspace.private, true);
  assert.deepEqual(workspace.workspaces, ["apps/*"]);
  assert.equal(workspace.engines.node, ">=24 <25");
  assert.equal(web.name, "@wtg/web");
  assert.equal(typeof web.scripts.dev, "string");
  assert.equal(typeof web.scripts.build, "string");
  assert.equal(typeof web.scripts.lint, "string");
  assert.equal(typeof web.scripts.typecheck, "string");
});
```

- [ ] **Step 3: Executar o teste e comprovar a falha inicial**

```powershell
Set-Location gerec_leads
node --test tooling/tests/workspace-structure.test.mjs
```

Esperado: `FAIL`, porque `package.json` e `apps/web` ainda não existem. Se passar, interromper e investigar estado preexistente.

- [ ] **Step 4: Criar os arquivos mínimos do workspace**

Criar `.nvmrc` com exatamente:

```text
24
```

Criar `package.json`:

```json
{
  "name": "@wtg/gerenciador-de-leads",
  "version": "0.1.0",
  "private": true,
  "workspaces": ["apps/*"],
  "engines": {
    "node": ">=24 <25"
  },
  "scripts": {
    "dev": "npm --workspace @wtg/web run dev",
    "build": "npm --workspace @wtg/web run build",
    "lint": "npm --workspace @wtg/web run lint",
    "typecheck": "npm --workspace @wtg/web run typecheck",
    "test:structure": "node --test tooling/tests/workspace-structure.test.mjs"
  }
}
```

Gerar a aplicação sem instalar dependências e sem criar outro repositório:

```powershell
npx create-next-app@16.3.3 apps/web --ts --eslint --tailwind --app --src-dir --import-alias "@/*" --empty --use-npm --skip-install --disable-git --no-agents-md
```

No `apps/web/package.json` gerado:

- trocar `name` por `@wtg/web`;
- adicionar `"typecheck": "tsc --noEmit"` aos scripts;
- não adicionar dependências além das geradas pelo scaffold nesta tarefa.

Criar `integrations/n8n/README.md`:

```md
# Integrações n8n

Este diretório receberá workflows exportados e documentação na Etapa 7.
O n8n atua como adaptador e não contém regras críticas de negócio.
```

Criar `tests/contracts/README.md`:

```md
# Testes de contrato

Este diretório abrigará contratos de integrações externas a partir da Etapa 4.
Não há integração real habilitada na Etapa 1.
```

Instalar uma única árvore de dependências e gerar somente o lockfile da raiz:

```powershell
npm install
```

- [ ] **Step 5: Executar o gate da tarefa**

```powershell
npm run test:structure
npm run lint
npm run typecheck
npm run build
Get-ChildItem -Recurse -Filter package-lock.json | Select-Object -ExpandProperty FullName
```

Esperado: todos os comandos passam e existe apenas `gerec_leads/package-lock.json`.

- [ ] **Step 6: Commit da fundação**

```powershell
git add gerec_leads/.nvmrc gerec_leads/package.json gerec_leads/package-lock.json gerec_leads/apps gerec_leads/integrations gerec_leads/tests gerec_leads/tooling/tests/workspace-structure.test.mjs
git commit -m "chore(gerec-leads): cria workspace executavel"
```

---

### Task 2: Adicionar formatação e testes unitários

**Files:**

- Create: `gerec_leads/prettier.config.mjs`
- Create: `gerec_leads/.prettierignore`
- Create: `gerec_leads/apps/web/vitest.config.ts`
- Modify: `gerec_leads/package.json`
- Modify: `gerec_leads/apps/web/package.json`
- Modify: `gerec_leads/package-lock.json`

- [ ] **Step 1: Instalar as ferramentas com versões fixas**

```powershell
npm install --save-dev prettier@3.9.6
npm install --save-dev vitest@4.1.11 --workspace @wtg/web
```

Adicionar ao `package.json` da raiz:

```json
{
  "scripts": {
    "test": "npm --workspace @wtg/web run test",
    "format": "prettier --write .",
    "format:check": "prettier --check .",
    "check": "npm run format:check && npm run lint && npm run typecheck && npm run test && npm run test:structure && npm run build"
  }
}
```

Preservar os scripts já existentes ao mesclar esse bloco. Adicionar ao `apps/web/package.json`:

```json
{
  "scripts": {
    "test": "vitest run --passWithNoTests"
  }
}
```

- [ ] **Step 2: Configurar o formatador sem alterar o SPEC**

Criar `prettier.config.mjs`:

```js
/** @type {import("prettier").Config} */
const config = {
  printWidth: 100,
  semi: true,
  singleQuote: false,
  trailingComma: "all",
};

export default config;
```

Criar `.prettierignore`:

```text
node_modules
.next
.superpowers
coverage
playwright-report
test-results
supabase/.temp
supabase/.branches
package-lock.json
**/*.md
```

- [ ] **Step 3: Configurar o runner unitário sem criar teste artificial de constante**

Criar `apps/web/vitest.config.ts`:

```ts
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "node",
    include: ["src/**/*.test.ts"],
  },
});
```

- [ ] **Step 4: Comprovar que o runner encerra com sucesso sem testes**

```powershell
npm run test
```

Esperado: `PASS`, com o Vitest informando que não encontrou testes e encerrando com código zero por causa de `--passWithNoTests`. Os primeiros testes comportamentais reais serão criados na Task 4.

- [ ] **Step 5: Executar o gate e formatar**

```powershell
npm run test
npm run format
npm run check
```

Esperado: runner aprovado sem testes e `check` totalmente verde.

- [ ] **Step 6: Commit das ferramentas de qualidade**

```powershell
git add gerec_leads
git commit -m "test(gerec-leads): configura qualidade e testes unitarios"
```

---

### Task 3: Inicializar Supabase local e gerar ambiente público com segurança

**Files:**

- Create: `gerec_leads/supabase/config.toml`
- Create: `gerec_leads/supabase/seed.sql`
- Create: `gerec_leads/apps/web/.env.example`
- Create: `gerec_leads/tooling/supabase/parse-status-env.test.mjs`
- Create: `gerec_leads/tooling/supabase/parse-status-env.mjs`
- Create: `gerec_leads/tooling/supabase/write-web-env.mjs`
- Modify: `gerec_leads/package.json`
- Modify: `gerec_leads/package-lock.json`

- [ ] **Step 1: Instalar o Supabase CLI no próprio workspace**

```powershell
npm install --save-dev supabase@2.115.0
```

Adicionar os scripts abaixo ao `package.json` da raiz:

```json
{
  "scripts": {
    "supabase:init": "supabase init",
    "supabase:start": "supabase start",
    "supabase:stop": "supabase stop",
    "supabase:status": "supabase status",
    "supabase:reset": "supabase db reset",
    "env:local": "node tooling/supabase/write-web-env.mjs",
    "test:supabase-tooling": "node --test tooling/supabase/*.test.mjs"
  }
}
```

Atualizar `check` para executar `npm run test:supabase-tooling` antes do build.

- [ ] **Step 2: Escrever o teste do filtro de variáveis antes da implementação**

Criar `tooling/supabase/parse-status-env.test.mjs`:

```js
import assert from "node:assert/strict";
import test from "node:test";

import { parseSupabaseStatusEnv, renderNextEnv } from "./parse-status-env.mjs";

test("expõe somente URL e chave pública do Supabase", () => {
  const source = [
    'API_URL="http://127.0.0.1:54321"',
    'ANON_KEY="public-local-key"',
    'SERVICE_ROLE_KEY="never-expose-this"',
  ].join("\n");

  const parsed = parseSupabaseStatusEnv(source);

  assert.deepEqual(parsed, {
    NEXT_PUBLIC_SUPABASE_URL: "http://127.0.0.1:54321",
    NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY: "public-local-key",
  });
  assert.equal(renderNextEnv(parsed).includes("SERVICE_ROLE"), false);
  assert.equal(renderNextEnv(parsed).includes("never-expose-this"), false);
});

test("recusa uma saída sem configuração pública completa", () => {
  assert.throws(
    () => parseSupabaseStatusEnv('API_URL="http://127.0.0.1:54321"'),
    /chave pública/i,
  );
});
```

- [ ] **Step 3: Executar o teste e confirmar a falha inicial**

```powershell
npm run test:supabase-tooling
```

Esperado: `FAIL` porque `parse-status-env.mjs` ainda não existe.

- [ ] **Step 4: Implementar o parser mínimo e seguro**

Criar `tooling/supabase/parse-status-env.mjs`:

```js
export function parseSupabaseStatusEnv(source) {
  const values = Object.fromEntries(
    source
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter((line) => line && !line.startsWith("#") && line.includes("="))
      .map((line) => {
        const separator = line.indexOf("=");
        const key = line.slice(0, separator);
        const value = line.slice(separator + 1).replace(/^"|"$/g, "");
        return [key, value];
      }),
  );

  const publicKey = values.PUBLISHABLE_KEY ?? values.ANON_KEY;

  if (!values.API_URL || !publicKey) {
    throw new Error("Supabase local sem URL ou chave pública disponível.");
  }

  return {
    NEXT_PUBLIC_SUPABASE_URL: values.API_URL,
    NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY: publicKey,
  };
}

export function renderNextEnv(values) {
  return `${Object.entries(values)
    .map(([key, value]) => `${key}=${value}`)
    .join("\n")}\n`;
}
```

Criar `tooling/supabase/write-web-env.mjs`:

```js
import { execFileSync } from "node:child_process";
import { chmodSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { parseSupabaseStatusEnv, renderNextEnv } from "./parse-status-env.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const npmCommand = process.platform === "win32" ? "npm.cmd" : "npm";
const status = execFileSync(
  npmCommand,
  ["exec", "--", "supabase", "status", "-o", "env"],
  { cwd: root, encoding: "utf8" },
);
const destination = resolve(root, "apps/web/.env.local");

writeFileSync(destination, renderNextEnv(parseSupabaseStatusEnv(status)), {
  encoding: "utf8",
  mode: 0o600,
});

if (process.platform !== "win32") {
  chmodSync(destination, 0o600);
}

console.log("Ambiente web local criado somente com URL e chave pública.");
```

- [ ] **Step 5: Inicializar o Supabase sem domínio comercial**

```powershell
npm run supabase:init
```

Manter o `config.toml` gerado pelo CLI. Criar `supabase/seed.sql` apenas com:

```sql
-- Dados sintéticos de domínio serão adicionados na Etapa 2, após o modelo aprovado.
```

Criar `apps/web/.env.example`:

```dotenv
NEXT_PUBLIC_SUPABASE_URL=http://127.0.0.1:54321
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=replace-with-local-public-key
```

- [ ] **Step 6: Subir o ambiente e gerar `.env.local`**

Com Docker Desktop ativo:

```powershell
npm run supabase:start
npm run env:local
npm run supabase:status
git check-ignore apps/web/.env.local
```

Esperado: serviços locais saudáveis, `apps/web/.env.local` ignorado pelo Git e nenhum valor de `service_role` nesse arquivo. Não imprimir o conteúdo das chaves no terminal ou em documentação.

- [ ] **Step 7: Executar o gate e fazer commit**

```powershell
npm run test:supabase-tooling
npm run check
git status --short
```

Confirmar que `.env.local`, `supabase/.temp` e `supabase/.branches` não aparecem no stage.

```powershell
git add gerec_leads
git commit -m "chore(gerec-leads): configura supabase local seguro"
```

---

### Task 4: Criar diagnóstico testado da conexão local

**Files:**

- Create: `gerec_leads/apps/web/src/lib/health/check-supabase.test.ts`
- Create: `gerec_leads/apps/web/src/lib/health/check-supabase.ts`
- Modify: `gerec_leads/apps/web/src/app/page.tsx`
- Modify: `gerec_leads/apps/web/src/app/layout.tsx`
- Modify: `gerec_leads/apps/web/src/app/globals.css`

- [ ] **Step 1: Escrever os testes do diagnóstico**

Criar `apps/web/src/lib/health/check-supabase.test.ts`:

```ts
import { describe, expect, it, vi } from "vitest";

import {
  checkSupabaseHealth,
  type HealthRequest,
} from "./check-supabase";

describe("checkSupabaseHealth", () => {
  it("informa conexão quando o Auth local responde", async () => {
    const request = vi
      .fn<HealthRequest>()
      .mockResolvedValue(new Response(null, { status: 200 }));

    await expect(
      checkSupabaseHealth(
        { url: "http://127.0.0.1:54321", publishableKey: "public-key" },
        request,
      ),
    ).resolves.toEqual({ status: "connected", message: "Supabase local conectado" });

    expect(request).toHaveBeenCalledWith(
      "http://127.0.0.1:54321/auth/v1/health",
      expect.objectContaining({
        cache: "no-store",
        headers: { apikey: "public-key" },
      }),
    );
  });

  it("não tenta conectar sem configuração pública", async () => {
    const request = vi.fn<HealthRequest>();

    await expect(
      checkSupabaseHealth({ url: undefined, publishableKey: undefined }, request),
    ).resolves.toEqual({
      status: "not_configured",
      message: "Supabase local ainda não configurado",
    });
    expect(request).not.toHaveBeenCalled();
  });

  it("degrada de forma segura quando o serviço está indisponível", async () => {
    const request = vi
      .fn<HealthRequest>()
      .mockRejectedValue(new Error("connection refused"));

    await expect(
      checkSupabaseHealth(
        { url: "http://127.0.0.1:54321", publishableKey: "public-key" },
        request,
      ),
    ).resolves.toEqual({
      status: "unavailable",
      message: "Supabase local indisponível",
    });
  });
});
```

- [ ] **Step 2: Executar o teste e comprovar a falha**

```powershell
npm run test
```

Esperado: `FAIL` pela ausência de `check-supabase.ts`.

- [ ] **Step 3: Implementar o diagnóstico sem expor segredos**

Criar `apps/web/src/lib/health/check-supabase.ts`:

```ts
export type SupabaseHealth = {
  status: "connected" | "not_configured" | "unavailable";
  message: string;
};

export type HealthRequest = (
  input: string,
  init?: RequestInit,
) => Promise<Response>;

type HealthConfig = {
  url: string | undefined;
  publishableKey: string | undefined;
};

export async function checkSupabaseHealth(
  config: HealthConfig = {
    url: process.env.NEXT_PUBLIC_SUPABASE_URL,
    publishableKey: process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY,
  },
  request: HealthRequest = fetch,
): Promise<SupabaseHealth> {
  if (!config.url || !config.publishableKey) {
    return {
      status: "not_configured",
      message: "Supabase local ainda não configurado",
    };
  }

  try {
    const response = await request(
      `${config.url.replace(/\/$/, "")}/auth/v1/health`,
      {
        cache: "no-store",
        headers: { apikey: config.publishableKey },
      },
    );

    if (response.ok) {
      return { status: "connected", message: "Supabase local conectado" };
    }
  } catch {
    // O estado de indisponibilidade é exibido sem registrar URL, chave ou payload.
  }

  return {
    status: "unavailable",
    message: "Supabase local indisponível",
  };
}
```

- [ ] **Step 4: Criar a página mínima de fundação**

Substituir `layout.tsx` por:

```tsx
import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import type { ReactNode } from "react";

import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Gerenciador de Leads WTG",
  description: "Fundação local do Gerenciador de Leads WTG",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="pt-BR">
      <body className={`${geistSans.variable} ${geistMono.variable}`}>
        {children}
      </body>
    </html>
  );
}
```

Substituir `page.tsx` por:

```tsx
import { checkSupabaseHealth } from "@/lib/health/check-supabase";

export const dynamic = "force-dynamic";

export default async function Home() {
  const health = await checkSupabaseHealth();

  return (
    <main className="foundation-shell">
      <section className="foundation-card" aria-labelledby="product-title">
        <p className="foundation-kicker">WTG • ambiente de desenvolvimento</p>
        <h1 id="product-title">Gerenciador de Leads WTG</h1>
        <p>
          Esqueleto local preparado. As regras comerciais começam somente após a
          aprovação da próxima etapa.
        </p>
        <div className="health-line" data-status={health.status} role="status">
          <span aria-hidden="true" />
          {health.message}
        </div>
      </section>
    </main>
  );
}
```

Substituir `globals.css` pelo CSS mínimo abaixo. Ele é apenas diagnóstico, não o design definitivo, e respeita o suporte exclusivamente desktop aprovado:

```css
@import "tailwindcss";

:root {
  color-scheme: light;
  --background: #f3f5f4;
  --foreground: #17201d;
  --surface: #ffffff;
  --border: #d8dfdc;
  --accent: #176b51;
  --muted: #596660;
}

* {
  box-sizing: border-box;
}

html {
  min-width: 1280px;
  background: var(--background);
}

body {
  min-height: 100vh;
  margin: 0;
  color: var(--foreground);
  background: var(--background);
  font-family: var(--font-geist-sans), Arial, Helvetica, sans-serif;
}

:focus-visible {
  outline: 3px solid var(--accent);
  outline-offset: 3px;
}

.foundation-shell {
  display: grid;
  min-height: 100vh;
  place-items: center;
  padding: 24px;
}

.foundation-card {
  width: min(100%, 640px);
  padding: clamp(24px, 6vw, 48px);
  border: 1px solid var(--border);
  border-radius: 20px;
  background: var(--surface);
}

.foundation-kicker {
  margin: 0 0 12px;
  color: var(--accent);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.foundation-card h1 {
  margin: 0;
  font-size: clamp(2rem, 7vw, 3.5rem);
  line-height: 1;
  letter-spacing: -0.04em;
}

.foundation-card > p:not(.foundation-kicker) {
  max-width: 54ch;
  margin: 20px 0 0;
  color: var(--muted);
  line-height: 1.6;
}

.health-line {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 32px;
  padding-top: 20px;
  border-top: 1px solid var(--border);
  font-weight: 650;
}

.health-line span {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #9a5b15;
}

.health-line[data-status="connected"] span {
  background: var(--accent);
}

.health-line[data-status="unavailable"] span {
  background: #a43737;
}
```

- [ ] **Step 5: Executar o gate com os três estados cobertos**

```powershell
npm run test
npm run lint
npm run typecheck
npm run build
```

Esperado: três testes do diagnóstico aprovados e build sem avisos de segredo ou acesso externo.

- [ ] **Step 6: Commit do diagnóstico**

```powershell
git add gerec_leads/apps/web
git commit -m "feat(gerec-leads): adiciona diagnostico local testado"
```

---

### Task 5: Provar o fluxo local no navegador com Playwright

**Files:**

- Create: `gerec_leads/playwright.config.ts`
- Create: `gerec_leads/tests/e2e/foundation.spec.ts`
- Modify: `gerec_leads/package.json`
- Modify: `gerec_leads/package-lock.json`

- [ ] **Step 1: Instalar Playwright no workspace**

```powershell
npm install --save-dev @playwright/test@1.62.1
```

Adicionar ao `package.json` da raiz:

```json
{
  "scripts": {
    "test:e2e": "playwright test",
    "test:e2e:install": "playwright install chromium",
    "test:e2e:install:ci": "playwright install --with-deps chromium"
  }
}
```

- [ ] **Step 2: Configurar o servidor controlado pelo teste**

Criar `playwright.config.ts`:

```ts
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: "http://127.0.0.1:3000",
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
  webServer: {
    command: "npm run dev",
    url: "http://127.0.0.1:3000",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
```

- [ ] **Step 3: Escrever o teste ponta a ponta antes de ajustar qualquer falha**

Criar `tests/e2e/foundation.spec.ts`:

```ts
import { expect, test } from "@playwright/test";

test("exibe a aplicação e a conexão local", async ({ page }) => {
  await page.goto("/");

  await expect(
    page.getByRole("heading", { level: 1, name: "Gerenciador de Leads WTG" }),
  ).toBeVisible();
  await expect(page.getByText("Supabase local conectado")).toBeVisible();
});
```

- [ ] **Step 4: Comprovar RED com o Supabase explicitamente parado**

```powershell
npm run test:e2e:install
npm run supabase:stop
npm run test:e2e
```

Esperado: `FAIL` porque o teste exige “Supabase local conectado” e o serviço foi parado deliberadamente. Registrar essa evidência RED. Se a falha ocorrer antes dessa asserção, diagnosticar navegador ausente, `.env.local` ausente, porta ocupada ou regressão da página; não alterar a expectativa correta para mascarar falha de infraestrutura.

- [ ] **Step 5: Garantir a infraestrutura e repetir**

```powershell
npm run supabase:start
npm run env:local
npm run test:e2e
```

Esperado: um teste aprovado no Chromium e nenhuma chave exibida na página, screenshot ou trace.

- [ ] **Step 6: Executar o gate e fazer commit**

```powershell
npm run check
npm run test:e2e
git add gerec_leads
git commit -m "test(gerec-leads): valida fundacao no navegador"
```

---

### Task 6: Adicionar CI isolado e testá-lo como contrato

**Files:**

- Create: `.github/workflows/gerec-leads-ci.yml`
- Create: `gerec_leads/tooling/tests/ci-contract.test.mjs`
- Modify: `gerec_leads/package.json`
- Modify: `gerec_leads/package-lock.json`

- [ ] **Step 1: Instalar o parser YAML e escrever o contrato antes do workflow**

```powershell
npm install --save-dev yaml@2.8.1
```

Criar `gerec_leads/tooling/tests/ci-contract.test.mjs`:

```js
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { parse } from "yaml";

const productRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const workflowPath = resolve(
  productRoot,
  "../.github/workflows/gerec-leads-ci.yml",
);

test("o CI permanece limitado ao Gerenciador de Leads", () => {
  const workflow = parse(readFileSync(workflowPath, "utf8"));

  assert.deepEqual(workflow.on.push.paths, ["gerec_leads/**"]);
  assert.deepEqual(workflow.on.pull_request.paths, ["gerec_leads/**"]);
  assert.equal(workflow.defaults.run["working-directory"], "gerec_leads");

  const steps = workflow.jobs.quality.steps;
  assert.equal(steps[0].uses, "actions/checkout@v7");

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
  assert.equal(serializedWorkflow.includes("service_role"), false);
  assert.equal(serializedWorkflow.includes("SERVICE_ROLE_KEY"), false);
});
```

Adicionar à raiz:

```json
{
  "scripts": {
    "test:ci-contract": "node --test tooling/tests/ci-contract.test.mjs"
  }
}
```

Atualizar `check` para:

```json
"check": "npm run format:check && npm run lint && npm run typecheck && npm run test && npm run test:structure && npm run test:supabase-tooling && npm run test:ci-contract && npm run build"
```

- [ ] **Step 2: Executar o contrato e confirmar a falha**

```powershell
npm run test:ci-contract
```

Esperado: `FAIL` porque o único arquivo externo autorizado ainda não existe.

- [ ] **Step 3: Criar o workflow mínimo na raiz**

Criar `.github/workflows/gerec-leads-ci.yml`:

```yaml
name: Gerenciador de Leads CI

on:
  push:
    paths:
      - "gerec_leads/**"
  pull_request:
    paths:
      - "gerec_leads/**"

permissions:
  contents: read

concurrency:
  group: gerec-leads-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

defaults:
  run:
    working-directory: gerec_leads

jobs:
  quality:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - name: Checkout
        uses: actions/checkout@v7

      - name: Node.js 24
        uses: actions/setup-node@v7
        with:
          node-version: 24
          cache: npm
          cache-dependency-path: gerec_leads/package-lock.json

      - name: Instalar dependências
        run: npm ci

      - name: Instalar Chromium
        run: npm run test:e2e:install:ci

      - name: Iniciar Supabase local
        run: npm run supabase:start

      - name: Gerar ambiente público local
        run: npm run env:local

      - name: Verificações estáticas e unitárias
        run: npm run check

      - name: Teste ponta a ponta
        run: npm run test:e2e

      - name: Encerrar Supabase local
        if: always()
        run: npm run supabase:stop
```

Não mover scripts para `.github`; o workflow somente orquestra comandos definidos em `gerec_leads/package.json`.

- [ ] **Step 4: Executar o gate do contrato e o gate completo**

```powershell
npm run test:ci-contract
npm run check
npm run test:e2e
```

Esperado: tudo aprovado; o YAML é interpretado com `parse`, e gatilhos, diretório de trabalho, Node 24 e steps são validados semanticamente.

- [ ] **Step 5: Revisar o diff externo antes do commit**

```powershell
git diff -- .github/workflows/gerec-leads-ci.yml gerec_leads/package.json gerec_leads/tooling/tests/ci-contract.test.mjs
git diff --check
```

Confirmar visualmente: nenhum segredo, nenhuma referência às aplicações legadas e nenhuma regra comercial no workflow.

- [ ] **Step 6: Commit do CI**

```powershell
git add .github/workflows/gerec-leads-ci.yml gerec_leads/package.json gerec_leads/package-lock.json gerec_leads/tooling/tests/ci-contract.test.mjs
git commit -m "ci(gerec-leads): adiciona pipeline isolado"
```

---

### Task 7: Documentar operação e fechar o gate da Etapa 1

**Files:**

- Create: `gerec_leads/README.md`
- Create: `gerec_leads/docs/evidencias/etapa-1.md`
- Modify: `gerec_leads/ROADMAP.md`

- [ ] **Step 1: Criar um guia reproduzível**

Criar `README.md` com estas seções e comandos exatos:

````md
# Gerenciador de Leads WTG

Projeto novo e isolado. Antes de desenvolver, leia `AGENTS.md`, o SPEC e o roadmap.

## Pré-requisitos

- Node.js 24 LTS
- npm
- Docker Desktop em execução

## Primeira execução

```powershell
nvm use 24
npm ci
npm run test:e2e:install
npm run supabase:start
npm run env:local
npm run dev
```

Acesse `http://127.0.0.1:3000` e confirme “Supabase local conectado”.

## Verificação

```powershell
npm run check
npm run test:e2e
```

## Encerramento

```powershell
npm run supabase:stop
```

`.env.local` é gerado apenas com URL e chave pública locais e nunca deve ser versionado.
````

Ao aplicar esse trecho, use uma cerca externa de quatro crases ou `apply_patch` para preservar corretamente os blocos internos.

- [ ] **Step 2: Executar uma instalação limpa e todos os gates**

Com Docker ativo e Node 24 selecionado:

```powershell
npm ci
npm run supabase:start
npm run env:local
npm run format:check
npm run lint
npm run typecheck
npm run test
npm run test:structure
npm run test:supabase-tooling
npm run test:ci-contract
npm run build
npm run test:e2e
git diff --check
git status --short
```

Esperado: todos os comandos aprovados. Se qualquer comando falhar, não marcar a etapa como concluída e usar `systematic-debugging` antes de corrigir.

- [ ] **Step 3: Registrar a evidência somente após o gate verde**

Criar `docs/evidencias/etapa-1.md` com este conteúdo depois da execução bem-sucedida:

```md
# Evidência de conclusão da Etapa 1

- Data: 25 de agosto de 2026
- Ambiente: desenvolvimento local, Node.js 24 LTS e Supabase via Docker
- `npm ci`: aprovado
- `npm run format:check`: aprovado
- `npm run lint`: aprovado
- `npm run typecheck`: aprovado
- testes unitários e estruturais: aprovados
- contrato do CI: aprovado
- build de produção: aprovado
- Playwright/Chromium com Supabase local: aprovado
- verificação de whitespace com `git diff --check`: aprovada
- segredos e arquivos locais no Git: ausentes

A fundação executável foi validada sem antecipar regras de negócio das Etapas 2 a 4.
```

- [ ] **Step 4: Atualizar o estado do roadmap**

Somente depois dos resultados anteriores, trocar em `ROADMAP.md`:

```md
- **Estado atual:** Etapa 1 concluída; Etapa 2 aguardando planejamento
```

- [ ] **Step 5: Revisão final contra escopo**

```powershell
rg -n "TO[D]O|TB[D]|FIXM[E]|PLACEHOLDE[R]" gerec_leads/apps gerec_leads/integrations gerec_leads/supabase gerec_leads/tests gerec_leads/tooling .github/workflows/gerec-leads-ci.yml
rg -n "service_role|SERVICE_ROLE_KEY" gerec_leads/apps gerec_leads/tests .github/workflows/gerec-leads-ci.yml
git diff --stat
git diff --check
```

Esperado: nenhuma pendência ou segredo. A única ocorrência aceitável de `service_role` é documentação preventiva ou o teste que garante sua ausência; nunca um valor real.

- [ ] **Step 6: Commit de encerramento da etapa**

```powershell
git add gerec_leads/README.md gerec_leads/docs/evidencias/etapa-1.md gerec_leads/ROADMAP.md
git commit -m "docs(gerec-leads): conclui etapa 1"
```

## Critério final de aceite da Etapa 1

A Etapa 1 está concluída somente quando, em uma instalação limpa:

- Node.js 24 e o lockfile reproduzem a aplicação;
- Supabase local sobe via Docker e gera apenas configuração pública para a web;
- a página informa conexão real, configuração ausente e indisponibilidade sem quebrar;
- lint, formatação, typecheck, testes unitários, testes estruturais e build passam;
- Playwright comprova a aplicação e a conexão no Chromium;
- o CI executa os mesmos gates e observa somente `gerec_leads/**`;
- nenhum arquivo funcional, segredo ou dado do novo produto escapou do escopo aprovado;
- nenhuma regra comercial foi antecipada.

## Referências técnicas para a execução

- Node.js releases: <https://nodejs.org/en/about/previous-releases>
- Next.js installation: <https://nextjs.org/docs/app/getting-started/installation>
- Supabase local development: <https://supabase.com/docs/guides/local-development>
- Supabase CLI: <https://supabase.com/docs/reference/cli/introduction>
- Vitest guide: <https://vitest.dev/guide/>
- Playwright CI: <https://playwright.dev/docs/ci>
- GitHub Actions workflow syntax: <https://docs.github.com/actions/reference/workflows-and-actions/workflow-syntax>
