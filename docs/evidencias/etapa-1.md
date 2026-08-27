# Evidência de conclusão da Etapa 1

- Data: 25 de agosto de 2026
- Ambiente: desenvolvimento local, Node.js 24 LTS e Supabase via Docker
- `npm ci`: aprovado
- `npm run test:e2e:install`: aprovado com Chromium já confirmado no processo novo
- `npm run supabase:start`: aprovado com o projeto `gerec_leads`, portas dedicadas 55320–55329 e Vector opcional excluído por `-x vector`
- `npm run env:local`: aprovado; gerou somente URL e chave pública locais em arquivo ignorado pelo Git
- `npm run format:check`: aprovado
- `npm run lint`: aprovado
- `npm run typecheck`: aprovado
- `npm run check`: aprovado
- testes unitários e estruturais: aprovados
- tooling Playwright, contrato do CI e build de produção: aprovados por `npm run check`
- Playwright/Chromium com Supabase local: aprovado
- verificação de whitespace com `git diff --check`: aprovada; `git status --short` pós-commit limpo
- segredos e arquivos locais no Git: ausentes
- `npm audit --omit=dev`: nenhuma vulnerabilidade de produção encontrada
- workbook `WTG - Leads.xlsx`: SHA-256 preservado em `83238297C3460E25D938142E5248F33039F02F75720C9E8BE690B4DC98D72CF4`

QA adicional executado via `agent-browser` em controlador real, no viewport 1440 × 900: heading e status presentes, console sem erros, axe-core 4.12.1 com 27 passes, 0 violações e 0 itens incompletos; TTFB 46,7 ms, LCP 88 ms e CLS 0.

A fundação executável foi validada sem antecipar regras de negócio das Etapas 2 a 4.
