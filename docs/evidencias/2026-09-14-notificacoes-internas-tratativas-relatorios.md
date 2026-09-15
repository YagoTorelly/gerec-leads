# Evidências — notificações internas, tratativas e relatórios

Data da validação: 15/09/2026.

## Aceitação E2E

| Cenário | Resultado | Evidência |
| --- | --- | --- |
| Vendedora Sandra recebe a janela de novos leads, registra `Potencial` e remove o marcador atual | Aprovado | `tests/e2e/operacao-notificacoes-relatorios.spec.ts` |
| Administrador filtra a lista pelo responsável Sandra e acessa os dois agrupamentos de relatórios | Aprovado | `tests/e2e/operacao-notificacoes-relatorios.spec.ts` |
| Vendedora é redirecionada de `/relatorios` para `/dashboard` sem requisição a `/api/admin/reports/lead-distribution` | Aprovado | Asserção direta de URL, navegação e requisições no spec de aceitação |
| Referências visuais integradas | Aprovado | 15 cenários E2E, incluindo 2 snapshots visuais, aprovados |

O briefing indicava `apps/web/e2e`, mas o `playwright.config.ts` executa exclusivamente `tests/e2e`. O spec foi criado em `tests/e2e/operacao-notificacoes-relatorios.spec.ts` para permanecer coberto pela gate oficial, sem alterar a configuração do runner.

## Capturas visuais — 1440×900

| Estado validado | Arquivo |
| --- | --- |
| Janela interna de novos leads para Sandra | [seller-new-leads-1440x900.png](seller-new-leads-1440x900.png) |
| Dashboard administrativo filtrado por Sandra | [admin-lead-filter-1440x900.png](admin-lead-filter-1440x900.png) |
| Relatórios administrativos por situação e vendedor | [admin-reports-1440x900.png](admin-reports-1440x900.png) |

As capturas foram produzidas com `agent-browser`, sessão isolada `task7-a5e9fbb32f66`, viewport 1440×900 e estados confirmados pela árvore de acessibilidade. As referências Playwright foram atualizadas para a composição aprovada após as Tasks 1–6.

## Gates finais

| Comando | Resultado real |
| --- | --- |
| `python -m pytest apps/api/tests -q` | 187 aprovados, 9 ignorados, em 20,73 s |
| `npm run test` | 25 arquivos, 105 testes aprovados, em 11,42 s |
| `npm run lint` | 0 erros; 1 aviso preexistente |
| `npm run typecheck` | Aprovado |
| `npm run build` | Aprovado; build otimizado concluído |
| `npm run test:e2e` | 15 testes aprovados, em 26,1 s |
| `git diff --check` | Aprovado após regeneração do contexto |

## Aviso preexistente

`apps/web/src/components/login-form.tsx:13:38` mantém o aviso `@next/next/no-img-element` para `<img>`. Não foi introduzido nem alterado nesta tarefa; o lint terminou sem erros.

## Escopo da correção de fixture

A fixture local E2E passou a representar a janela pendente somente para Sandra, adicionou os contratos de notificação/acknowledgement, filtro administrativo e agregação de relatórios. Também acompanha `potential` e o marcador de desqualificação da última tratativa. Nenhum arquivo de produção ou backend foi modificado.
