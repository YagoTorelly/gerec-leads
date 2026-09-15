# Task 7 — E2E, capturas e evidências

## Entrega

### Correção WB-05 residual — calendário personalizado

- `saoPauloDate` passou a validar os componentes reconstruídos de `Date.UTC` contra o texto recebido. Dias inexistentes, meses fora de 01–12 e demais overflows deixam o período `custom` explícito e inválido, sem normalização ou consulta indevida.
- RED: `2026-02-30` era serializada como `2026-03-02T03:00:00.000Z`; o teste também registrou a rejeição de `2026-13-01`. GREEN: ambos preservam os valores informados no erro de período personalizado, enquanto o intervalo válido e a conversão America/Sao_Paulo → UTC permanecem cobertos.
- Verificações: testes web de relatórios (6 arquivos, 13 testes), `npm run typecheck` e `npm run lint` passaram; este último tem somente o aviso preexistente de `<img>` em `login-form.tsx`. O spec E2E de notificações/relatórios passou com 3 testes.
- A suíte E2E integral teve 14 de 15 cenários funcionais aprovados; o snapshot visual preexistente do dashboard vendedor capturou a tela transitória “Carregando dados da operação…” em vez da referência já preenchida (19% de diferença). Nenhum snapshot, fixture ou código fora da WB-05 foi alterado nesta correção.

### Verificação complementar antes do commit

- A regressão de falha de consulta também verifica que os dois limites personalizados continuam no formulário de nova tentativa. `npm run test` passou com 110 testes em 28 arquivos; os read models e relatórios da API passaram com 19 testes.
- `npm run lint`, `npm run typecheck` e `npm run test:ci-contract` passaram novamente. O lint conserva somente o aviso preexistente de `<img>` em `apps/web/src/components/login-form.tsx`.

- Criado o teste de aceitação integrado para a vendedora Sandra: nova janela de leads, tratativa `Potencial` e remoção do marcador de desqualificação conforme a última tratativa.
- Criado o cenário administrativo de filtro por responsável e acesso aos relatórios por situação e vendedor.
- Preservada e ampliada a verificação de autorização: vendedor em `/relatorios` é redirecionado para `/dashboard`, não recebe a navegação administrativa e não inicia consulta de distribuição.
- Complementada apenas a fixture E2E local para os novos contratos; não houve alteração de produção nem backend.
- Geradas as três capturas 1440×900 exigidas e atualizadas as referências Playwright para a composição visual aprovada das Tasks 1–6.

## TDD e correções de compatibilidade

- RED: o novo spec falhou inicialmente porque a fixture não expunha a janela de novos leads, `potential`, o filtro nem o relatório.
- GREEN: o spec passou com 3 cenários após o complemento mínimo da fixture.
- A suíte integral revelou seletores legados que passaram a encontrar conteúdo oculto ou repetido pela nova interface e uma expectativa textual antiga (`Não informado` em vez de `Indefinido`). As correções foram limitadas aos seletores/expectativa dos testes e foram validadas por execução focada de 7 cenários.
- Os snapshots visuais apresentaram diferenças de 2% (admin) e 3% (vendedor), inspecionadas visualmente: controles de filtro e composição aprovada após Tasks 1–6. As referências foram regeneradas pelo Playwright e a suíte integral passou.

## Evidências finais

- `python -m pytest apps/api/tests -q`: 187 aprovados, 9 ignorados.
- `npm run test`: 25 arquivos, 105 testes aprovados.
- `npm run lint`: 0 erros e o único aviso preexistente de `<img>` em `login-form.tsx`.
- `npm run typecheck`: aprovado.
- `npm run build`: aprovado.
- `npm run test:e2e`: 15 testes aprovados.
- Capturas em `docs/evidencias/`: `seller-new-leads-1440x900.png`, `admin-lead-filter-1440x900.png` e `admin-reports-1440x900.png`.
- Evidência detalhada em `docs/evidencias/2026-09-14-notificacoes-internas-tratativas-relatorios.md`.

## Divergência de caminho resolvida

O briefing citava `apps/web/e2e`, mas a configuração oficial do Playwright usa `tests/e2e`. O novo spec foi colocado em `tests/e2e/operacao-notificacoes-relatorios.spec.ts`, para que seja executado por `npm run test:e2e`, sem mudança de configuração.

## Correção final da revisão global

- `sort=situation` agora ordena antes da paginação pela sequência aprovada de rótulos: Ganho (`won`), Indefinido (`undefined`), Negociação (`negotiation`) e Potencial (`potential`), preservando `createdAt` descendente e `_id` ascendente como desempates.
- Mês atual e intervalo personalizado passam a interpretar calendário em `America/Sao_Paulo` e só então serializam os limites UTC exigidos pela API. Todo o histórico continua usando o marco UTC aprovado. Intervalo personalizado inválido permanece explícito, com as datas informadas, em vez de retornar silenciosamente ao histórico inteiro.
- A janela de novos leads reabre quando a revalidação fornece snapshot com nova sequência/token; a confirmação anterior não oculta atribuições posteriores.
- A página de relatórios preserva o shell administrativo em falhas de consulta, mantém os limites personalizados, mostra o período baseado na atribuição atual e oferece nova tentativa pelo formulário.
- O workflow não inicia mais um Next.js concorrente: o Playwright sobe sua fixture isolada, compatível com os dados e o reset HTTP dos testes locais. O contrato de CI verifica a ausência do servidor prévio.

### Evidências da correção final

- RED: regressões novas falharam para ordem lexicográfica, calendário UTC, custom inválido, snapshot revalidado, formulário vazio, falha sem shell e servidor concorrente no CI.
- GREEN focal: 16 testes de read model Python, 14 testes web e contrato de CI aprovados.
- Gates: `python -m pytest apps/api/tests -q` — 187 aprovados, 9 ignorados; `npm run test` — 109 testes em 28 arquivos; lint, typecheck e build aprovados; `E2E_WEB_PORT=3002 npm run test:e2e` — 15 aprovados.
