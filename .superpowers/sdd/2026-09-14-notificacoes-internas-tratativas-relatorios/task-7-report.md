# Task 7 — E2E, capturas e evidências

## Entrega

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
