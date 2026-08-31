# Evidências da reconstrução operacional — Gerenciador de Leads WTG

Data da verificação: 31/08/2026
Worktree: `.worktrees/migracao-mongodb-vercel-railway`
Branch: `feat/migracao-mongodb-vercel-railway`

## Escopo validado

Este registro fecha o gate operacional das Tasks 1–16 do plano de reconstrução. A validação cobre o núcleo Python/MongoDB, contratos HTTP, cliente Next.js, permissões administrativas e de vendedor, tratativas comerciais, fila FIFO dinâmica, paginação, usuários, SLA de 24 horas úteis e os fluxos E2E em desktop.

## Comandos e resultados

| Comando | Resultado observado |
| --- | --- |
| `python -m pytest apps/api/tests -q` | **151 passed, 8 skipped** em 20,82 s |
| `npm run test --workspace=@wtg/web -- --run` | **16 arquivos, 78 testes aprovados** |
| `npm run lint --workspace=@wtg/web` | **0 erros, 2 avisos** preexistentes: uso de `<img>` e import não usado em teste |
| `npm run typecheck --workspace=@wtg/web` | **Aprovado**, `tsc --noEmit` sem saída de erro |
| `npm run build --workspace=@wtg/web` | **Aprovado**, Next.js 16.3.3 compilou e gerou as rotas |
| `node --test tests/contracts/*.test.mjs` | **5 testes aprovados** |
| `npx playwright test --project=chromium` | **12 testes aprovados** em 18,1 s |
| `powershell -ExecutionPolicy Bypass -File scripts/generate-master-context.ps1` | **Aprovado**, contexto mestre regenerado com 19.521 linhas |
| `git diff --check` | Executado no gate; nenhuma falha de whitespace registrada |

## E2E e referências visuais

Os fluxos foram executados com fixture local determinística, sem produção, Google Sheets ou MongoDB real. A suíte Chromium usa viewport 1440×900 e cobre:

- autenticação válida e inválida;
- redirecionamento e isolamento por perfil;
- criação de vendedor no fim da fila, pausa, ativação e redefinição de senha;
- leitura administrativa sem controles de edição de tratativas;
- paginação semântica de fila e histórico;
- tratativa do vendedor com comentário mínimo, status, contador e desqualificação;
- snapshots do dashboard administrativo, usuários/modal, fila/histórico e dashboard/modal do vendedor.

## Limitações conhecidas

- O escopo continua exclusivamente desktop (largura mínima de 1280 px).
- Os oito skips da suíte API correspondem aos testes condicionados à disponibilidade de replica set MongoDB.
- O lint mantém dois avisos não bloqueantes listados acima; não há erros.
- A suíte visual é uma referência determinística do fixture e não substitui validação com dados reais da operação.
- Integração definitiva com a planilha, e-mail, WhatsApp e operação de produção permanecem fora deste gate.

## Correção necessária encontrada no gate

O contrato HTTP controlado ainda não preenchia `last_updated_at` ao criar seu `TreatmentResult`, embora o domínio já exigisse o carimbo persistido autoritativo. O fixture foi atualizado para usar um timestamp fixo de 28/08/2026; após a correção, os cinco contratos HTTP passaram. Nenhuma regra de negócio de produção foi alterada.

## Integridade e arquivos protegidos

Não foram feitos push, merge, deploy ou ações externas. Os arquivos preexistentes protegidos foram preservados sem inclusão:

- `apps/api/.env.example` permanece uma exclusão preexistente;
- `tools/google-sheets-diagnostic/` permanece não rastreado e fora da alteração.

Segredos, credenciais e acesso direto ao MongoDB não foram expostos ao navegador nem adicionados à evidência.
