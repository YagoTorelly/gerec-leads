# MVP Dashboard por Perfil — Plano de Implementação

> **Para agentes:** executar as tarefas em ordem, com TDD e checkpoints de verificação.

**Objetivo:** substituir o health check por um sistema desktop funcional, com login Supabase, visão global do administrador e visão restrita de cada vendedor.

**Arquitetura:** Next.js App Router com páginas server-side e componentes client apenas para interação. O Supabase Auth identifica o usuário; as consultas de leads usam RLS como segunda barreira. Dados sintéticos serão inseridos por seed apenas para desenvolvimento local.

**Stack:** Next.js 16, React 19, TypeScript, Supabase local, CSS próprio e Vitest.

**Spec:** `docs/superpowers/specs/2026-08-25-workbook-mock-fluxo-completo-design.md` e `SPEC_GERENCIADOR_DE_LEADS_WTG.md`.

## Restrições globais

- Desktop only: manter largura mínima de 1280px.
- Vendedor vê apenas seus leads atuais/históricos permitidos; administrador vê todos.
- Horários exibidos em `America/Sao_Paulo`.
- Chaves administrativas permanecem no servidor e nunca no bundle do navegador.
- Interface deve mostrar estados de carregamento, vazio, erro e atraso de SLA.

### Tarefa 1: Cliente Supabase server e sessão

**Arquivos:** criar `apps/web/src/lib/supabase/server.ts`, `apps/web/src/lib/auth/get-session-context.ts`; criar testes correspondentes.

- Escrever testes para sessão ausente, perfil admin e perfil seller.
- Implementar cliente server com cookies e leitura do perfil.
- Criar redirect de sessão ausente para `/login`.
- Verificar com `npm --workspace @wtg/web run test` e `typecheck`.

### Tarefa 2: Seed de leads demonstrativos

**Arquivos:** modificar `supabase/seed.sql`; criar `supabase/tests/003_demo_seed.sql`.

- Inserir cinco perfis/usuários apenas via bootstrap já existente e inserir campanhas, empresas, leads e atribuições sintéticas usando os IDs encontrados por e-mail.
- Criar horários de feedback passados, próximos e normais para demonstrar SLA.
- Validar contagem, status e ausência de dados de vendedor cruzado por RLS.

### Tarefa 3: Login e shell de aplicação

**Arquivos:** substituir `apps/web/src/app/page.tsx`; criar `apps/web/src/app/login/page.tsx`, `apps/web/src/app/dashboard/page.tsx`, `apps/web/src/components/app-shell.tsx` e estilos.

- Login por e-mail/senha local.
- Shell com marca WTG, usuário atual, perfil, relógio local, sair e navegação.
- Renderizar estado de indisponibilidade sem esconder a causa.

### Tarefa 4: Dashboard administrativo

**Arquivos:** criar `apps/web/src/components/admin-dashboard.tsx` e `apps/web/src/lib/dashboard/admin-data.ts`.

- Cards de total, em fila, atrasados, pendências e ganhos.
- Tabela global com lead, contato M–P, vendedor, status, prazo e última atividade.
- Filtros por vendedor/status e ordenação por SLA.

### Tarefa 5: Dashboard do vendedor

**Arquivos:** criar `apps/web/src/components/seller-dashboard.tsx` e `apps/web/src/lib/dashboard/seller-data.ts`.

- Mostrar somente leads retornados pela política RLS para o usuário autenticado.
- Cards de minha fila, feedbacks hoje, atrasados e tentativas.
- Tabela com contato, prazo, estado e ações desabilitadas quando houver bloqueio de SLA.

### Tarefa 6: Interações e testes de isolamento

**Arquivos:** criar `apps/web/src/components/lead-actions.tsx`, testes Vitest e teste Playwright.

- Feedback/tentativa/resultados terão controles visuais e mensagens de validação; mutações transacionais completas ficam para a Etapa 3.
- Testar que admin recebe visão global e seller recebe somente seus registros.
- Rodar format, lint, typecheck, testes web, contratos Supabase e build.

