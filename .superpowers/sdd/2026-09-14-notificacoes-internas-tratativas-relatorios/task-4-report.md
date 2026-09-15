# Task 4 — Contratos web, Potencial, destaque e controles de lista

## Entrega

- `CommercialStatus` agora aceita `potential`, apresentado como `Potencial`.
- A lista destaca somente a linha cujo `commentCount` seja exatamente zero, sem alterar fila, permissões ou disponibilidade.
- `LeadListControls` mantém os parâmetros existentes da URL, incluindo `page`; administrador pode incluir/remover `assigneeId` e ambos os perfis podem incluir/remover `sort=situation`.
- Dashboard e fila validam os valores de busca antes de encaminhá-los ao endpoint de dashboard.
- A action de tratativa também aceita `potential`. Esse ajuste adicional é necessário para que a opção do formulário não seja rejeitada antes de chegar à API.

## TDD e validação

- RED: os testes focados falharam inicialmente porque os parâmetros de consulta, o componente de controles, a opção `Potencial` e a classe de destaque ainda não existiam.
- RED adicional: a action de tratativa não encaminhava `potential` à API (`submitLeadTreatment` recebeu zero chamadas).
- GREEN: `npm run test -- src/lib/operations/treatment-actions.test.ts src/components/lead-table.test.tsx src/components/lead-treatment-modal.dom.test.tsx src/lib/dashboard/queries.test.ts` — 4 arquivos, 23 testes aprovados.
- `npm run typecheck` — aprovado.
- `npm run lint` — sem erros novos; permanece um aviso preexistente em `src/components/login-form.tsx` sobre `<img>`, fora do escopo desta task.
- `git diff --check` — aprovado.

## Escopo preservado

Nenhum arquivo de backend, notificações ou relatórios web foi modificado. As alterações preexistentes em `apps/api/.env.example` e `tools/google-sheets-diagnostic/` foram preservadas sem inclusão no commit.
