# Etapa 2 — Modelo, Auth e RLS Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Criar o modelo completo de dados do Gerenciador de Leads, as cinco contas locais e o isolamento de administrador/vendedor comprovado por testes diretos no banco.

**Architecture:** O PostgreSQL/Supabase receberá migrações versionadas para identidade, fila, origem, operação e auditoria. A autorização será aplicada por RLS e funções auxiliares privadas; mutações críticas serão reservadas a comandos de domínio das etapas seguintes. O bootstrap local usará a API administrativa do Auth somente em processo server-side e nunca gravará segredos no repositório.

**Tech Stack:** Supabase CLI 2.115.0, PostgreSQL 17, Supabase Auth, SQL/pgTAP, Node.js 24, TypeScript/JavaScript tooling e Vitest.

**Spec:** `docs/superpowers/specs/2026-08-25-workbook-mock-fluxo-completo-design.md` e `SPEC_GERENCIADOR_DE_LEADS_WTG.md`.

## Global Constraints

- Todo código, migração, teste, documentação e configuração permanece dentro de `gerec_leads/`, exceto o workflow CI já aprovado.
- O SPEC é a fonte canônica; nenhuma regra de negócio será alterada silenciosamente.
- PostgreSQL decide fila, cursor, elegibilidade, propriedade, prazos, créditos e resultados.
- `service_role` nunca chega ao navegador, ao `.env.example` ou ao Git.
- Google Sheets é somente entrada; nesta etapa nenhuma planilha é lida ou escrita.
- A interface final será exclusivamente desktop com largura mínima de 1280 px; esta etapa não cria interface operacional.
- O vendedor só acessa próprios dados e histórico permitido; o administrador acessa o escopo global aprovado.
- Migrações novas nunca editam migrações aplicadas.
- Toda função nova deve ter teste que falhe antes da implementação, salvo configuração declarativa.
- Datas persistidas usam `timestamptz`; valores monetários usam `numeric`; identificadores SQL usam `snake_case` minúsculo.
- Dados de seed são sintéticos e não contêm contatos reais.

## Estrutura de arquivos

| Arquivo | Responsabilidade |
|---|---|
| `supabase/config.toml` | Desabilitar cadastro público e fixar política local de senha. |
| `supabase/migrations/20260825100000_create_private_helpers.sql` | Extensões, schema privado e funções auxiliares de papel. |
| `supabase/migrations/20260825101000_create_identity_queue.sql` | Perfis, vendedores, cursor e créditos. |
| `supabase/migrations/20260825102000_create_source_commercial.sql` | Importações, origem, pendências, campanhas, empresas e leads. |
| `supabase/migrations/20260825103000_create_operations_audit.sql` | Atribuições, SLA, feedbacks, tentativas, resultados, vendas, outbox e auditoria. |
| `supabase/migrations/20260825104000_enable_rls.sql` | RLS, grants mínimos, projeções e políticas por perfil. |
| `supabase/seed.sql` | Configurações sintéticas estáveis; não cria usuários Auth. |
| `tooling/supabase/local-runtime.mjs` | Ler status local sem imprimir chaves administrativas. |
| `tooling/supabase/bootstrap-local-users.mjs` | Criar/reconciliar as cinco contas e gravar credenciais somente em `supabase/.temp`. |
| `tooling/supabase/local-runtime.test.mjs` | Testes de parsing e não exposição de segredos. |
| `tooling/supabase/bootstrap-local-users.test.mjs` | Testes das regras de usuários, ordem e senha aleatória. |
| `supabase/tests/001_schema_contract.sql` | pgTAP para tabelas, colunas, constraints e índices. |
| `supabase/tests/002_rls_contract.sql` | pgTAP para habilitação de RLS e grants. |
| `tooling/tests/rls-integration.mjs` | Teste HTTP/Auth real de administrador, vendedor e chamada cruzada. |
| `package.json` | Comandos de bootstrap e teste de banco. |
| `docs/evidencias/etapa-2.md` | Evidências de comandos, contagens e decisões da etapa. |
| `ROADMAP.md` | Marcar Etapa 2 somente após todos os gates. |

## Interfaces produzidas

O plano produz estes contratos para as etapas seguintes:

```ts
type LocalSupabaseRuntime = {
  apiUrl: string;
  publishableKey: string;
  serviceRoleKey: string;
};

type LocalUserCredential = {
  email: string;
  password: string;
  role: "admin" | "seller";
  position: number | null;
};

type SellerProfile = {
  userId: string;
  fullName: string;
  email: string;
  role: "admin" | "seller";
  isActive: boolean;
};
```

Os comandos da Etapa 3 consumirão as tabelas e políticas deste plano sem atualizar diretamente colunas críticas pelo cliente.

---

### Task 1: Fixar configuração de Auth e contratos de tooling

**Files:**
- Modify: `supabase/config.toml`
- Modify: `package.json`
- Create: `tooling/supabase/local-runtime.mjs`
- Create: `tooling/supabase/local-runtime.test.mjs`
- Test: `tooling/tests/auth-config.test.mjs`

**Interfaces:**
- Produz `readLocalSupabaseRuntime({ cwd }): LocalSupabaseRuntime`.
- O parser consome `supabase status -o env` e exige `API_URL`, `PUBLISHABLE_KEY` ou `ANON_KEY` e `SERVICE_ROLE_KEY` apenas em memória.
- Nenhuma função imprime o valor de qualquer chave.

- [ ] **Step 1: Escrever os testes vermelhos de configuração**

```js
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

test("Auth local impede cadastro público", () => {
  const config = readFileSync("supabase/config.toml", "utf8");
  assert.match(config, /enable_signup\s*=\s*false/);
  assert.match(config, /\[auth\.email\][\s\S]*enable_signup\s*=\s*false/);
});

test("configuração não contém service_role em arquivo público", () => {
  const files = ["apps/web/.env.example", "README.md", "supabase/config.toml"];
  for (const file of files) assert.doesNotMatch(readFileSync(file, "utf8"), /service_role/i);
});
```

- [ ] **Step 2: Rodar o teste vermelho**

Run: `node --test tooling/tests/auth-config.test.mjs`

Expected: FAIL porque o Auth local ainda permite signup público.

- [ ] **Step 3: Implementar a configuração mínima**

Em `supabase/config.toml`, alterar somente:

```toml
[auth]
enable_signup = false
minimum_password_length = 12
password_requirements = "lower_upper_letters_digits_symbols"

[auth.email]
enable_signup = false
enable_confirmations = false
```

Adicionar em `package.json`:

```json
{
  "scripts": {
    "test:db": "supabase test db --local",
    "supabase:bootstrap-users": "node tooling/supabase/bootstrap-local-users.mjs"
  }
}
```

- [ ] **Step 4: Implementar o parser privado do runtime**

`tooling/supabase/local-runtime.mjs` deve exportar:

```js
export function parseLocalRuntimeEnv(source) {
  const values = Object.fromEntries(
    source.split(/\r?\n/).filter((line) => line.includes("=")).map((line) => {
      const index = line.indexOf("=");
      return [line.slice(0, index), line.slice(index + 1).replace(/^"|"$/g, "")];
    }),
  );
  const publishableKey = values.PUBLISHABLE_KEY ?? values.ANON_KEY;
  if (!values.API_URL || !publishableKey || !values.SERVICE_ROLE_KEY) {
    throw new Error("Supabase local sem configuração administrativa completa.");
  }
  return { apiUrl: values.API_URL, publishableKey, serviceRoleKey: values.SERVICE_ROLE_KEY };
}
```

`readLocalSupabaseRuntime({ cwd })` deve executar o binário local existente com `status -o env`, retornar o objeto acima e nunca fazer `console.log` do resultado bruto.

- [ ] **Step 5: Rodar testes verdes e checagem de segredos**

Run: `node --test tooling/tests/auth-config.test.mjs tooling/supabase/local-runtime.test.mjs`

Expected: PASS; nenhuma chave administrativa aparece no output.

- [ ] **Step 6: Commitar a configuração**

```bash
git add supabase/config.toml package.json tooling/supabase/local-runtime.mjs tooling/supabase/local-runtime.test.mjs tooling/tests/auth-config.test.mjs
git commit -m "feat(gerec-leads): prepara auth local e runtime seguro"
```

### Task 2: Criar helpers privados e identidade da fila

**Files:**
- Create: `supabase/migrations/20260825100000_create_private_helpers.sql`
- Create: `supabase/migrations/20260825101000_create_identity_queue.sql`
- Test: `supabase/tests/001_schema_contract.sql`

**Interfaces:**
- `private.current_user_role() returns text`.
- `private.is_admin() returns boolean`.
- `private.is_current_seller(seller_id uuid) returns boolean`.
- `profiles`, `seller_queue`, `queue_state` e `seller_skip_balances` ficam disponíveis para RLS e comandos.

- [ ] **Step 1: Escrever o teste vermelho do contrato de identidade**

```sql
begin;
select plan(11);
select has_table('public', 'profiles');
select has_table('public', 'seller_queue');
select has_table('public', 'queue_state');
select has_table('public', 'seller_skip_balances');
select has_column('public', 'profiles', 'user_id');
select has_column('public', 'profiles', 'role');
select col_type_is('public', 'profiles', 'role', 'text');
select col_has_check('public', 'profiles', 'profiles_role_check');
select col_is_pk('public', 'profiles', 'user_id');
select has_index('public', 'seller_queue', 'seller_queue_position_key');
select has_function('private', 'is_admin', 0);
select * from finish();
rollback;
```

- [ ] **Step 2: Rodar o teste vermelho**

Run: `npm run supabase:start; npm run test:db -- supabase/tests/001_schema_contract.sql`

Expected: FAIL informando que as tabelas ainda não existem.

- [ ] **Step 3: Criar schema privado e helpers mínimos**

```sql
create schema if not exists private;

create or replace function private.current_user_role()
returns text
language sql
stable
security definer
set search_path = ''
as $$
  select p.role
  from public.profiles p
  where p.user_id = (select auth.uid())
    and p.is_active = true;
$$;

create or replace function private.is_admin()
returns boolean
language sql
stable
security definer
set search_path = ''
as $$ select coalesce((select private.current_user_role()) = 'admin', false); $$;

create or replace function private.is_current_seller(target_seller_id uuid)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select target_seller_id = (select auth.uid())
    and (select private.current_user_role()) = 'seller';
$$;

revoke all on schema private from public, anon, authenticated, service_role;
revoke all on function private.current_user_role() from public, anon, authenticated, service_role;
revoke all on function private.is_admin() from public, anon, authenticated, service_role;
revoke all on function private.is_current_seller(uuid) from public, anon, authenticated, service_role;
```

- [ ] **Step 4: Criar tabelas de identidade e fila**

```sql
create table public.profiles (
  user_id uuid primary key references auth.users(id) on delete restrict,
  full_name text not null check (length(btrim(full_name)) >= 2),
  email citext not null unique,
  role text not null check (role in ('admin', 'seller')),
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.seller_queue (
  seller_id uuid primary key references public.profiles(user_id) on delete restrict,
  position smallint not null unique check (position between 1 and 4),
  is_paused boolean not null default false,
  version bigint not null default 0 check (version >= 0),
  updated_at timestamptz not null default now()
);

create table public.queue_state (
  singleton boolean primary key default true check (singleton = true),
  next_seller_id uuid not null references public.profiles(user_id) on delete restrict,
  version bigint not null default 0 check (version >= 0),
  updated_at timestamptz not null default now()
);

create table public.seller_skip_balances (
  seller_id uuid primary key references public.profiles(user_id) on delete restrict,
  balance integer not null default 0 check (balance >= 0),
  updated_at timestamptz not null default now()
);

create index seller_queue_position_idx on public.seller_queue(position);
create index seller_skip_balances_balance_idx on public.seller_skip_balances(balance);
```

- [ ] **Step 5: Conceder somente privilégios de leitura necessários à etapa**

```sql
revoke all on public.profiles, public.seller_queue, public.queue_state,
  public.seller_skip_balances from public, anon, authenticated;
grant select on public.profiles, public.seller_queue, public.seller_skip_balances
  to authenticated;
```

- [ ] **Step 6: Rodar o contrato de schema**

Run: `npm run supabase:reset; npm run test:db -- supabase/tests/001_schema_contract.sql`

Expected: PASS nas tabelas, tipos, chave primária, índice e helper privado.

- [ ] **Step 7: Commitar a identidade**

```bash
git add supabase/migrations/20260825100000_create_private_helpers.sql supabase/migrations/20260825101000_create_identity_queue.sql supabase/tests/001_schema_contract.sql
git commit -m "feat(gerec-leads): cria identidade e estado da fila"
```

### Task 3: Criar origem, campanhas, empresas e leads

**Files:**
- Create: `supabase/migrations/20260825102000_create_source_commercial.sql`
- Modify: `supabase/tests/001_schema_contract.sql`

**Interfaces:**
- `lead_source_records.lead_id` é nullable enquanto houver pendência de documento/Estado.
- `lead_source_records.source_lead_id` é a identidade estável do workbook.
- `campaigns`, `companies` e `leads` ficam prontos para os comandos de importação e fila das etapas seguintes.

- [ ] **Step 1: Adicionar asserções vermelhas para origem e ocorrência**

```sql
select has_table('public', 'import_runs');
select has_table('public', 'lead_source_records');
select has_table('public', 'source_data_issues');
select has_table('public', 'source_corrections');
select has_table('public', 'campaigns');
select has_table('public', 'companies');
select has_table('public', 'leads');
select has_table('public', 'source_snapshot_records');
select col_is_unique('public', 'lead_source_records', 'source_lead_id');
select col_is_pk('public', 'campaigns', 'id');
select col_is_pk('public', 'companies', 'id');
```

- [ ] **Step 2: Rodar o teste vermelho**

Run: `npm run test:db -- supabase/tests/001_schema_contract.sql`

Expected: FAIL nas tabelas de origem ainda ausentes.

- [ ] **Step 3: Criar as tabelas com constraints**

Implementar nesta migração:

```sql
create table public.import_runs (
  id uuid primary key default gen_random_uuid(),
  source_type text not null check (source_type in ('mock_workbook', 'google_sheets')),
  mode text not null check (mode in ('bootstrap', 'snapshot', 'incremental')),
  idempotency_key text not null unique,
  correlation_id uuid not null,
  status text not null check (status in ('running', 'completed', 'partial', 'failed')),
  rows_read integer not null default 0 check (rows_read >= 0),
  rows_created integer not null default 0 check (rows_created >= 0),
  rows_updated integer not null default 0 check (rows_updated >= 0),
  rows_ignored integer not null default 0 check (rows_ignored >= 0),
  rows_pending integer not null default 0 check (rows_pending >= 0),
  rows_failed integer not null default 0 check (rows_failed >= 0),
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  error_summary text
);

create table public.campaigns (
  id bigint generated always as identity primary key,
  external_id text,
  source_name text not null check (length(btrim(source_name)) > 0),
  display_name text not null check (length(btrim(display_name)) > 0),
  status text not null default 'pending_approval'
    check (status in ('pending_approval', 'approved', 'archived')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create unique index campaigns_external_id_uq on public.campaigns(external_id)
  where external_id is not null;
create unique index campaigns_source_name_fallback_uq
  on public.campaigns((lower(btrim(source_name)))) where external_id is null;

create table public.companies (
  id bigint generated always as identity primary key,
  document_type text check (document_type in ('cpf', 'cnpj')),
  document_normalized text,
  document_display text,
  legal_name text,
  state text check (state is null or state ~ '^[A-Z]{2}$'),
  owner_id uuid references public.profiles(user_id) on delete restrict,
  client_since timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check ((document_type is null and document_normalized is null)
    or (document_type is not null and document_normalized is not null))
);
create unique index companies_document_uq on public.companies(document_normalized)
  where document_normalized is not null;

create table public.leads (
  id bigint generated always as identity primary key,
  company_id bigint not null references public.companies(id) on delete restrict,
  campaign_id bigint not null references public.campaigns(id) on delete restrict,
  source_entered_at timestamptz not null,
  assignment_status text not null default 'ready'
    check (assignment_status in ('ready', 'parked', 'assigned', 'archived')),
  qualification_status text not null default 'pending'
    check (qualification_status in ('pending', 'qualified', 'disqualified')),
  conversion_status text not null default 'active'
    check (conversion_status in ('active', 'qualified_follow_up', 'closed_no_conversion', 'won')),
  current_assignee_id uuid references public.profiles(user_id) on delete restrict,
  feedback_due_at timestamptz,
  parked_reason text check (parked_reason is null or parked_reason in (
    'no_eligible_seller', 'owner_blocked', 'campaign_pending')),
  source_phase text,
  estimated_value numeric(14,2) check (estimated_value is null or estimated_value >= 0),
  archived_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create unique index leads_company_campaign_active_uq
  on public.leads(company_id, campaign_id) where archived_at is null;
create index leads_assignment_filter_idx
  on public.leads(assignment_status, source_entered_at, id) where archived_at is null;
create index leads_current_assignee_idx
  on public.leads(current_assignee_id, assignment_status) where archived_at is null;
create index leads_campaign_idx on public.leads(campaign_id, source_entered_at);

create table public.lead_source_records (
  id bigint generated always as identity primary key,
  source_lead_id text not null unique,
  import_run_id uuid not null references public.import_runs(id) on delete restrict,
  lead_id bigint references public.leads(id) on delete restrict,
  source_row integer not null check (source_row >= 2),
  source_entered_at timestamptz,
  campaign_external_id text,
  campaign_name text,
  mock_has_cnpj_or_mei text,
  full_name text,
  phone text,
  email citext,
  source_status text,
  row_hash text not null check (row_hash ~ '^[0-9a-f]{64}$'),
  normalized_payload jsonb not null,
  is_present boolean not null default true,
  removed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index lead_source_records_lead_idx on public.lead_source_records(lead_id);
create index lead_source_records_present_idx on public.lead_source_records(is_present, source_entered_at);

create table public.source_snapshot_records (
  import_run_id uuid not null references public.import_runs(id) on delete cascade,
  source_record_id bigint not null references public.lead_source_records(id) on delete cascade,
  observed_hash text not null check (observed_hash ~ '^[0-9a-f]{64}$'),
  outcome text not null check (outcome in ('created', 'updated', 'ignored', 'pending', 'error')),
  primary key (import_run_id, source_record_id)
);

create table public.source_data_issues (
  id bigint generated always as identity primary key,
  source_record_id bigint not null references public.lead_source_records(id) on delete restrict,
  field_name text not null check (field_name in ('document', 'state', 'campaign', 'contact_name', 'phone', 'email')),
  issue_code text not null,
  status text not null default 'open' check (status in ('open', 'resolved')),
  resolved_by uuid references public.profiles(user_id) on delete restrict,
  resolved_at timestamptz,
  created_at timestamptz not null default now()
);
create unique index source_data_issues_open_uq
  on public.source_data_issues(source_record_id, field_name) where status = 'open';

create table public.source_corrections (
  id bigint generated always as identity primary key,
  source_record_id bigint not null references public.lead_source_records(id) on delete restrict,
  field_name text not null check (field_name in ('document', 'state')),
  value text not null check (length(btrim(value)) > 0),
  normalized_value text not null,
  actor_id uuid not null references public.profiles(user_id) on delete restrict,
  active boolean not null default true,
  created_at timestamptz not null default now()
);
create unique index source_corrections_active_uq
  on public.source_corrections(source_record_id, field_name) where active;
```

- [ ] **Step 4: Adicionar todos os índices de foreign key**

Criar índices para `import_run_id`, `campaign_id`, `company_id`, `lead_id`, `source_record_id` e `owner_id` em todas as tabelas que os referenciarem. Verificar com a consulta de constraints do skill Supabase antes de prosseguir.

- [ ] **Step 5: Rodar schema e validar pendência sem empresa fictícia**

Run: `npm run supabase:reset; npm run test:db -- supabase/tests/001_schema_contract.sql`

Expected: PASS; o schema aceita `lead_source_records.lead_id` nulo e rejeita documento inválido quando uma empresa for criada.

- [ ] **Step 6: Commitar origem e comercial**

```bash
git add supabase/migrations/20260825102000_create_source_commercial.sql supabase/tests/001_schema_contract.sql
git commit -m "feat(gerec-leads): cria origem e entidades comerciais"
```

### Task 4: Criar operações, histórico e outbox

**Files:**
- Create: `supabase/migrations/20260825103000_create_operations_audit.sql`
- Modify: `supabase/tests/001_schema_contract.sql`

**Interfaces:**
- Tabelas de evento são append-only para o domínio.
- Toda tabela operacional contém as chaves necessárias para rastrear atribuição, autor e idempotência.

- [ ] **Step 1: Escrever asserções vermelhas**

```sql
select has_table('public', 'assignments');
select has_table('public', 'feedback_cycles');
select has_table('public', 'feedbacks');
select has_table('public', 'contact_attempts');
select has_table('public', 'qualification_events');
select has_table('public', 'sales');
select has_table('public', 'business_holidays');
select has_table('public', 'notification_outbox');
select has_table('public', 'audit_log');
select col_is_unique('public', 'sales', 'id');
```

- [ ] **Step 2: Rodar o teste vermelho**

Run: `npm run test:db -- supabase/tests/001_schema_contract.sql`

Expected: FAIL porque as tabelas operacionais ainda não existem.

- [ ] **Step 3: Criar as tabelas de operação**

Criar estas definições, mantendo checks e índices:

```sql
create table public.assignments (
  id bigint generated always as identity primary key,
  lead_id bigint not null references public.leads(id) on delete restrict,
  seller_id uuid not null references public.profiles(user_id) on delete restrict,
  assignment_type text not null check (assignment_type in ('normal', 'recurring', 'temporary', 'permanent_transfer')),
  started_at timestamptz not null default now(),
  ended_at timestamptz,
  actor_id uuid references public.profiles(user_id) on delete restrict,
  reason text,
  idempotency_key text not null unique,
  check (ended_at is null or ended_at >= started_at)
);
create unique index assignments_current_lead_uq
  on public.assignments(lead_id) where ended_at is null;
create index assignments_seller_idx on public.assignments(seller_id, started_at, ended_at);

create table public.feedback_cycles (
  id bigint generated always as identity primary key,
  lead_id bigint not null references public.leads(id) on delete restrict,
  assignment_id bigint not null references public.assignments(id) on delete restrict,
  cycle_number integer not null check (cycle_number >= 1),
  starts_at timestamptz not null,
  reminder_at timestamptz not null,
  due_at timestamptz not null,
  closed_at timestamptz,
  close_reason text,
  unique (lead_id, cycle_number),
  check (reminder_at <= due_at),
  check (closed_at is null or closed_at >= starts_at)
);
create unique index feedback_cycles_open_lead_uq on public.feedback_cycles(lead_id) where closed_at is null;
create index feedback_cycles_due_idx on public.feedback_cycles(due_at) where closed_at is null;

create table public.feedbacks (
  id bigint generated always as identity primary key,
  lead_id bigint not null references public.leads(id) on delete restrict,
  assignment_id bigint not null references public.assignments(id) on delete restrict,
  seller_id uuid not null references public.profiles(user_id) on delete restrict,
  comment text not null check (length(btrim(comment)) >= 6),
  contact_started boolean not null check (contact_started),
  idempotency_key text not null unique,
  created_at timestamptz not null default now()
);
create index feedbacks_lead_idx on public.feedbacks(lead_id, created_at);

create table public.contact_attempts (
  id bigint generated always as identity primary key,
  lead_id bigint not null references public.leads(id) on delete restrict,
  assignment_id bigint not null references public.assignments(id) on delete restrict,
  seller_id uuid not null references public.profiles(user_id) on delete restrict,
  channel text not null check (channel = 'whatsapp'),
  business_date date not null,
  comment text not null check (length(btrim(comment)) >= 6),
  idempotency_key text not null unique,
  created_at timestamptz not null default now(),
  unique (lead_id, business_date)
);

create table public.qualification_events (
  id bigint generated always as identity primary key,
  lead_id bigint not null references public.leads(id) on delete restrict,
  assignment_id bigint not null references public.assignments(id) on delete restrict,
  actor_id uuid not null references public.profiles(user_id) on delete restrict,
  outcome text not null check (outcome in ('qualified_follow_up', 'qualified_closed_no_conversion', 'disqualified', 'won', 'reversed')),
  reason text check (reason is null or reason in ('no_answer_after_five_attempts', 'no_cnpj', 'outside_sp')),
  comment text not null check (length(btrim(comment)) >= 6),
  idempotency_key text not null unique,
  reversed_event_id bigint references public.qualification_events(id) on delete restrict,
  created_at timestamptz not null default now(),
  check ((outcome = 'disqualified' and reason is not null) or (outcome <> 'disqualified'))
);
create index qualification_events_lead_idx on public.qualification_events(lead_id, created_at);

create table public.sales (
  id bigint generated always as identity primary key,
  lead_id bigint not null references public.leads(id) on delete restrict,
  credited_seller_id uuid not null references public.profiles(user_id) on delete restrict,
  qualification_event_id bigint not null unique references public.qualification_events(id) on delete restrict,
  comment text not null check (length(btrim(comment)) >= 6),
  won_at timestamptz not null default now(),
  reversed_at timestamptz,
  reversed_by uuid references public.profiles(user_id) on delete restrict
);
create unique index sales_active_lead_uq on public.sales(lead_id) where reversed_at is null;

create table public.business_holidays (
  holiday_date date not null,
  scope text not null check (scope in ('national', 'sp')),
  name text not null check (length(btrim(name)) > 0),
  primary key (holiday_date, scope)
);
```

- [ ] **Step 4: Criar auditoria, outbox e configurações**

```sql
create table public.notification_outbox (
  id uuid primary key default gen_random_uuid(),
  event_type text not null,
  aggregate_type text not null,
  aggregate_id text not null,
  idempotency_key text not null unique,
  payload jsonb not null,
  status text not null default 'pending' check (status in ('pending', 'processing', 'sent', 'failed')),
  attempts integer not null default 0 check (attempts >= 0),
  available_at timestamptz not null default now(),
  last_error text,
  created_at timestamptz not null default now(),
  processed_at timestamptz
);
create index notification_outbox_pending_idx on public.notification_outbox(status, available_at);

create table public.notification_incidents (
  id uuid primary key default gen_random_uuid(),
  incident_type text not null check (incident_type = 'parked_threshold'),
  opened_at timestamptz not null default now(),
  resolved_at timestamptz
);
create unique index notification_incidents_open_uq
  on public.notification_incidents(incident_type) where resolved_at is null;

create table public.audit_log (
  id bigint generated always as identity primary key,
  actor_id uuid references public.profiles(user_id) on delete restrict,
  action text not null,
  entity_type text not null,
  entity_id text not null,
  before_data jsonb,
  after_data jsonb,
  correlation_id uuid not null,
  created_at timestamptz not null default now()
);
create index audit_log_entity_idx on public.audit_log(entity_type, entity_id, created_at);

create table public.system_settings (
  singleton boolean primary key default true check (singleton = true),
  timezone text not null default 'America/Sao_Paulo',
  feedback_hours integer not null default 24 check (feedback_hours > 0),
  reminder_hours integer not null default 4 check (reminder_hours > 0 and reminder_hours < feedback_hours),
  parked_threshold integer not null default 2 check (parked_threshold >= 2),
  digest_time time not null default time '09:00:00',
  updated_at timestamptz not null default now()
);
```

- [ ] **Step 5: Atualizar seed sintético**

`supabase/seed.sql` deve inserir somente:

```sql
insert into public.system_settings(singleton) values (true) on conflict (singleton) do nothing;
insert into public.business_holidays(holiday_date, scope, name) values
  ('2026-01-01', 'national', 'Confraternização Universal'),
  ('2026-04-21', 'national', 'Tiradentes'),
  ('2026-09-07', 'national', 'Independência do Brasil'),
  ('2026-10-12', 'national', 'Nossa Senhora Aparecida'),
  ('2026-11-02', 'national', 'Finados'),
  ('2026-11-15', 'national', 'Proclamação da República'),
  ('2026-11-20', 'national', 'Consciência Negra'),
  ('2026-12-25', 'national', 'Natal')
on conflict do nothing;
```

Datas adicionais de teste serão inseridas dentro de transações de teste, não como regra permanente do seed.

- [ ] **Step 6: Rodar o contrato completo**

Run: `npm run supabase:reset; npm run test:db -- supabase/tests/001_schema_contract.sql`

Expected: PASS para todas as tabelas, checks, índices e settings.

- [ ] **Step 7: Commitar operações e auditoria**

```bash
git add supabase/migrations/20260825103000_create_operations_audit.sql supabase/seed.sql supabase/tests/001_schema_contract.sql
git commit -m "feat(gerec-leads): cria operação, histórico e outbox"
```

### Task 5: Aplicar RLS e grants por perfil

**Files:**
- Create: `supabase/migrations/20260825104000_enable_rls.sql`
- Create: `supabase/tests/002_rls_contract.sql`

**Interfaces:**
- Todas as tabelas comerciais têm RLS habilitada e forçada.
- Leitura administrativa é global.
- Leitura de vendedor é limitada a atribuição atual ou ao histórico próprio permitido.
- Tabelas de origem técnica, auditoria, outbox e conflitos não são consultáveis diretamente pelo vendedor.

- [ ] **Step 1: Escrever testes vermelhos de RLS e grants**

```sql
begin;
select plan(12);
select policies_are('public', 'profiles', array['profiles_select_self_or_admin']);
select policies_are('public', 'leads', array['leads_admin_select', 'leads_current_seller_select']);
select policies_are('public', 'feedbacks', array['feedbacks_admin_select', 'feedbacks_current_or_historical_select']);
select policies_are('public', 'contact_attempts', array['attempts_admin_select', 'attempts_current_or_historical_select']);
select policies_are('public', 'audit_log', array['audit_admin_select']);
select policies_are('public', 'notification_outbox', array['outbox_admin_select']);
select table_privilege_is('authenticated', 'public', 'profiles', 'SELECT', true);
select table_privilege_is('authenticated', 'public', 'leads', 'UPDATE', false);
select table_privilege_is('authenticated', 'public', 'audit_log', 'SELECT', false);
select has_function('private', 'current_user_role', 0);
select has_function('private', 'is_admin', 0);
select * from finish();
rollback;
```

- [ ] **Step 2: Rodar o teste vermelho**

Run: `npm run test:db -- supabase/tests/002_rls_contract.sql`

Expected: FAIL porque políticas e grants ainda não existem.

- [ ] **Step 3: Habilitar RLS em todas as tabelas comerciais**

Executar `alter table ... enable row level security; alter table ... force row level security;` para `profiles`, `seller_queue`, `queue_state`, `seller_skip_balances`, `import_runs`, `campaigns`, `companies`, `leads`, `lead_source_records`, `source_snapshot_records`, `source_data_issues`, `source_corrections`, `assignments`, `feedback_cycles`, `feedbacks`, `contact_attempts`, `qualification_events`, `sales`, `business_holidays`, `field_overrides`, `source_conflicts`, `notification_outbox`, `notification_incidents`, `audit_log` e `system_settings`.

- [ ] **Step 4: Criar funções de escopo server-side**

Adicionar helpers privados para:

```sql
create or replace function private.can_read_current_lead(target_lead_id bigint)
returns boolean language sql stable security definer set search_path = '' as $$
  select exists (
    select 1 from public.leads l
    where l.id = target_lead_id
      and l.current_assignee_id = (select auth.uid())
      and (select private.current_user_role()) = 'seller'
  );
$$;

create or replace function private.can_read_own_assignment(target_assignment_id bigint)
returns boolean language sql stable security definer set search_path = '' as $$
  select exists (
    select 1 from public.assignments a
    where a.id = target_assignment_id and a.seller_id = (select auth.uid())
  );
$$;
```

As funções devem validar o papel internamente e ter execução revogada para os papéis de API.

- [ ] **Step 5: Criar políticas de leitura**

Usar `((select auth.uid()) = column)` ou helpers encapsulados, nunca chamada não-cacheada por linha. O núcleo das políticas será:

```sql
create policy profiles_select_self_or_admin on public.profiles
for select to authenticated
using ((select private.is_admin()) or user_id = (select auth.uid()));

create policy leads_admin_select on public.leads
for select to authenticated
using ((select private.is_admin()));

create policy leads_current_seller_select on public.leads
for select to authenticated
using ((select private.can_read_current_lead(id)));

create policy feedbacks_current_or_historical_select on public.feedbacks
for select to authenticated
using (
  (select private.is_admin())
  or seller_id = (select auth.uid())
  or (select private.can_read_current_lead(lead_id))
);

create policy audit_admin_select on public.audit_log
for select to authenticated using ((select private.is_admin()));
```

Aplicar a mesma regra de histórico próprio para `contact_attempts`, `qualification_events` e `assignments`. `feedback_cycles` será filtrada pelo `assignment_id`. `lead_source_records` e tabelas técnicas terão leitura administrativa somente nesta etapa; a projeção M–P do vendedor será um RPC da Etapa 5.

- [ ] **Step 6: Revogar escrita direta e expor somente leitura necessária**

```sql
revoke all on all tables in schema public from anon, authenticated;
grant select on public.profiles, public.seller_queue, public.seller_skip_balances,
  public.campaigns, public.companies, public.leads, public.assignments,
  public.feedback_cycles, public.feedbacks, public.contact_attempts,
  public.qualification_events, public.sales to authenticated;
```

Depois do `revoke`, conceder `select` apenas nas tabelas listadas e manter `audit_log`, `notification_outbox`, conflitos e origem técnica restritos ao administrador via policies. Nenhuma tabela recebe `insert`, `update` ou `delete` do cliente.

- [ ] **Step 7: Rodar contrato de RLS**

Run: `npm run supabase:reset; npm run test:db -- supabase/tests/002_rls_contract.sql`

Expected: PASS; RLS habilitada, policies nomeadas e mutações diretas negadas.

- [ ] **Step 8: Commitar RLS**

```bash
git add supabase/migrations/20260825104000_enable_rls.sql supabase/tests/002_rls_contract.sql
git commit -m "feat(gerec-leads): protege dados com RLS e grants mínimos"
```

### Task 6: Criar bootstrap idempotente das cinco contas

**Files:**
- Create: `tooling/supabase/bootstrap-local-users.mjs`
- Create: `tooling/supabase/bootstrap-local-users.test.mjs`
- Modify: `supabase/seed.sql`

**Interfaces:**
- `buildLocalUsers()` retorna a ordem canônica sem senha fixa.
- `bootstrapLocalUsers({ runtime, writeCredentials })` cria ou atualiza contas usando somente a API administrativa.
- Credenciais são gravadas em `supabase/.temp/local-users.json`, ignorado pelo Git.

- [ ] **Step 1: Escrever teste vermelho sem tocar Auth real**

```js
import test from "node:test";
import assert from "node:assert/strict";
import { buildLocalUsers } from "./bootstrap-local-users.mjs";

test("contas locais preservam ordem e papéis canônicos", () => {
  const users = buildLocalUsers(() => "SenhaLocal-A1!");
  assert.deepEqual(users.map(({ email }) => email), [
    "yago@wtgseguros.com.br",
    "renato@wtgseguros.com.br",
    "sandracristina@wtgseguros.com.br",
    "jessicaalmeida@wtgseguros.com.br",
    "nelmacastro@wtgseguros.com.br",
  ]);
  assert.equal(users[0].role, "admin");
  assert.deepEqual(users.slice(1).map(({ position }) => position), [1, 2, 3, 4]);
});

test("senha gerada não é constante", () => {
  const first = buildLocalUsers(() => crypto.randomUUID());
  const second = buildLocalUsers(() => crypto.randomUUID());
  assert.notEqual(first[0].password, second[0].password);
});
```

- [ ] **Step 2: Rodar o teste vermelho**

Run: `node --test tooling/supabase/bootstrap-local-users.test.mjs`

Expected: FAIL porque o bootstrap ainda não existe.

- [ ] **Step 3: Implementar criação/reconciliação**

O script deve:

1. obter `LocalSupabaseRuntime` sem imprimir valores;
2. criar cliente Supabase com `serviceRoleKey` somente em memória;
3. usar `auth.admin.listUsers`, `createUser` ou `updateUserById`;
4. confirmar e-mail localmente;
5. fazer upsert de `profiles` com papel e posição;
6. fazer upsert de `seller_queue`, `seller_skip_balances` e `queue_state`;
7. gerar senha com `crypto.randomBytes` e alfabeto seguro;
8. gravar apenas o conjunto de credenciais em `supabase/.temp/local-users.json`;
9. imprimir somente os e-mails e o caminho do arquivo, nunca senhas ou chaves.

O arquivo terá modo JSON com:

```json
{
  "generatedAt": "2026-08-25T00:00:00.000Z",
  "users": [{ "email": "yago@wtgseguros.com.br", "password": "...", "role": "admin", "position": null }]
}
```

- [ ] **Step 4: Rodar teste unitário e bootstrap local**

Run: `node --test tooling/supabase/bootstrap-local-users.test.mjs; npm run supabase:bootstrap-users`

Expected: testes PASS; cinco usuários aparecem no Auth local e o arquivo ignorado é criado sem aparecer no `git status`.

- [ ] **Step 5: Validar login com cliente público**

Usar as credenciais do arquivo local em um script de teste, sem imprimir senha:

```js
const { data, error } = await publicClient.auth.signInWithPassword({ email, password });
assert.ifError(error);
assert.ok(data.session?.access_token);
```

- [ ] **Step 6: Commitar bootstrap**

```bash
git add tooling/supabase/bootstrap-local-users.mjs tooling/supabase/bootstrap-local-users.test.mjs supabase/seed.sql
git commit -m "feat(gerec-leads): provisiona contas locais aleatórias"
```

### Task 7: Provar RLS com chamadas autenticadas

**Files:**
- Create: `tooling/tests/rls-integration.mjs`
- Modify: `package.json`

**Interfaces:**
- O teste usa somente URL e chave pública no cliente do usuário.
- O administrador pode consultar a fila completa e os leads globais.
- Cada vendedor consulta apenas a própria posição e não consegue consultar o lead de outro vendedor pela API.

- [ ] **Step 1: Escrever teste vermelho de isolamento**

Criar dados sintéticos dentro de uma transação/fixture controlada com dois vendedores, dois leads e atribuições atuais. O teste deve autenticar Renato e Sandra e executar:

```js
const renatoRows = await renatoClient.from("leads").select("id,current_assignee_id");
assert.equal(renatoRows.error, null);
assert.deepEqual(renatoRows.data.map(({ current_assignee_id }) => current_assignee_id), [renatoId]);

const crossRead = await renatoClient.from("leads").select("*").eq("id", sandraLeadId);
assert.equal(crossRead.error, null);
assert.deepEqual(crossRead.data, []);

const directUpdate = await renatoClient.from("leads").update({ current_assignee_id: renatoId }).eq("id", sandraLeadId);
assert.ok(directUpdate.error);
```

- [ ] **Step 2: Rodar teste vermelho**

Run: `node tooling/tests/rls-integration.mjs`

Expected: FAIL até o bootstrap, dados sintéticos e policies estarem disponíveis.

- [ ] **Step 3: Criar fixture controlada de integração**

Implementar comandos server-side de teste que usem `service_role` somente no processo do teste, insiram dois vendedores/atribuições e removam os dados ao final. O cliente de cada vendedor deve usar exclusivamente a chave pública e o token retornado pelo Auth.

- [ ] **Step 4: Rodar teste verde e testar histórico pós-transferência**

Adicionar caso em que Renato possui feedback próprio, o lead é atribuído a Sandra e Renato consegue ler apenas o feedback dele, sem ler o feedback posterior de Sandra.

Run: `npm run supabase:reset; npm run supabase:bootstrap-users; node tooling/tests/rls-integration.mjs`

Expected: PASS sem dados cruzados e sem mutação direta crítica.

- [ ] **Step 5: Adicionar comando de CI local**

Em `package.json`:

```json
{
  "scripts": {
    "test:rls": "node tooling/tests/rls-integration.mjs",
    "test:etapa-2": "npm run test:db && npm run test:rls"
  }
}
```

- [ ] **Step 6: Commitar integração RLS**

```bash
git add tooling/tests/rls-integration.mjs package.json
git commit -m "test(gerec-leads): prova isolamento por perfil"
```

### Task 8: Evidenciar e fechar a Etapa 2

**Files:**
- Create: `docs/evidencias/etapa-2.md`
- Modify: `ROADMAP.md`
- Modify: `docs/ARQUITETURA.md`

- [ ] **Step 1: Rodar a verificação completa da etapa**

Run: `npm run supabase:reset; npm run supabase:bootstrap-users; npm run test:etapa-2; npm run check`

Expected: todos os contratos, testes RLS, lint, tipos, testes existentes e build passam.

- [ ] **Step 2: Registrar evidência sem segredos**

Documentar somente comandos, contagens, hash das migrações, resultado dos testes, perfis exercitados e limitações locais. Nunca copiar `service_role`, senhas ou payloads pessoais.

- [ ] **Step 3: Atualizar o roadmap com o gate correto**

Marcar Etapa 2 como concluída apenas se:

- migrações reproduzem o schema;
- cinco contas locais funcionam;
- RLS impede acesso cruzado por API direta;
- não há falha crítica;
- evidência foi registrada.

Manter Etapa 3 como próxima etapa em andamento; não marcar ingestão ou frontend como concluídos.

- [ ] **Step 4: Commitar evidência**

```bash
git add docs/evidencias/etapa-2.md ROADMAP.md docs/ARQUITETURA.md
git commit -m "docs(gerec-leads): fecha gate de modelo auth e rls"
```

## Planos seguintes

Após o gate desta etapa, criar e revisar planos independentes, sem alterar este documento:

1. `2026-08-25-etapa-3-nucleo-transacional.md`: calendário, SLA, fila, locks, propriedade, recorrência, créditos, comandos e concorrência.
2. `2026-08-25-etapa-4-ingestao-operacao.md`: adapter do workbook, snapshot, pendências, campanhas, feedbacks, resultados, overrides e outbox.
3. `2026-08-25-etapa-5-frontend-admin.md`: login, shell, dashboard, sincronização, pendências, campanhas, fila, leads e auditoria.
4. `2026-08-25-etapa-6-frontend-vendedor.md`: dashboard privado, detalhe, feedback, tentativas, resultados, E2E e hardening visual.

Cada plano seguinte consumirá somente interfaces testadas da etapa anterior e terá seu próprio commit, evidência e gate no `ROADMAP.md`.

## Verificação do plano

- Cobertura do SPEC: identidade/Auth/RLS (seções 8, 9 e 28), origem e pendências (12 e 13), modelo (25), segurança (28), falhas (29), auditoria (30), testes (33) e governança (39) estão mapeados nas Tasks 1–8.
- Concorrência do cursor, SLA, importação prática e frontend não são implementados neste plano; estão explicitamente reservados aos planos 3–6.
- Não há marcador de incompletude, função sem assinatura ou dependência de planilha definitiva.
- Todas as migrations são novas e ordenadas por timestamp.
- O contrato de runtime não expõe chave administrativa.
