# Task 2 — Relatório de implementação

## Status

Implementada a fronteira HTTP administrativa para cadastro manual de leads,
com autorização de administrador, `Idempotency-Key` obrigatório, validação de
entrada e resposta pública `201`. A rota delega integralmente ao comando
transacional da Task 1 e usa o relógio do MongoDB.

A atribuição manual incrementa a sequência global de notificações já consumida
pela janela interna do vendedor. Não foi criado um segundo canal nem envio de
e-mail.

## Arquivos

- Alterado `apps/api/src/gerec_api/routes/admin.py` para expor
  `POST /api/admin/leads/manual` e reconciliar a fila manual ao reativar um
  vendedor.
- Alterado `apps/api/src/gerec_api/main.py` para registrar
  `ManualLeadService` e o relógio do banco no estado da aplicação.
- Alterado `apps/api/src/gerec_api/domain/lead_notifications.py` para explicitar
  o contrato de watermark único entre tipos de atribuição.
- Alterado `apps/api/src/gerec_api/automation/sync_job.py` para executar
  `reconcile_pending_manual` depois da reconciliação automática.
- Alterado `apps/api/tests/integration/test_manual_leads.py` com cobertura da
  rota, autorização, validação, idempotência, resposta, notificação e
  reativação.
- Alterado `apps/api/tests/unit/test_automation.py` com cobertura do gatilho de
  reconciliação manual na sincronização.

## Evidência TDD

- RED: os testes focados apresentaram 9 falhas esperadas:
  - rota ausente retornando `404` nos cenários de sucesso, autorização,
    validação e notificação;
  - lead manual permanecendo `parked` após reativação de vendedor;
  - job de sincronização sem chamada ao reconciliador manual.
- GREEN focado: `25 passed, 3 skipped`.
- O teste transacional real já existente
  `test_manual_command_rolls_back_every_side_effect_after_assignment` continua
  cobrindo rollback de lead, cursor, atribuição, auditoria, outbox e recibo. Ele
  é coletado e pula somente quando o replica set `rs0` não está disponível.

## Contratos validados

- vendedor recebe `403` e nenhuma escrita é criada;
- nome/telefone vazios, e-mail inválido e ausência de `Idempotency-Key`
  retornam `422`;
- resposta `201` contém somente `leadId`, `manualQueueLeadId`, `assigneeId`,
  `assignedAt`, `commercialStatus` e `source`;
- repetição da mesma chave retorna o mesmo recibo e não duplica o lead;
- a janela existente do vendedor recebe o lead manual pelo mesmo
  `watermarkSequence` persistido;
- reativação administrativa e sincronização completa tentam novamente, em
  FIFO próprio, apenas os leads da fila manual.

## Verificações executadas

- `python -m pytest apps/api/tests/integration/test_manual_leads.py apps/api/tests/unit/test_automation.py -q`
  — `25 passed, 3 skipped`.
- `python -m pytest apps/api/tests/integration/test_manual_leads.py apps/api/tests/integration/test_user_administration.py apps/api/tests/integration/test_lead_notifications.py apps/api/tests/integration/test_auth.py apps/api/tests/unit/test_automation.py -q -rs`
  — `48 passed, 4 skipped`.
- `python -m pytest apps/api/tests -q -rs`
  — `206 passed, 12 skipped`.
- `python -m compileall -q apps/api/src apps/api/tests` — exit `0`.
- `git diff --check` — exit `0`.

Todos os skips informados são de testes que exigem MongoDB replica set `rs0`,
indisponível no ambiente local; não houve fallback silencioso para fake nesses
cenários.

## Preservação de escopo

- Nenhum arquivo de frontend ou da Task 3 foi alterado.
- A remoção preexistente de `apps/api/.env.example` e o diretório não rastreado
  `tools/google-sheets-diagnostic/` foram preservados fora deste trabalho e não
  devem entrar no commit.

## Correção pós-revisão — rodada 1

### Finding corrigido

O cadastro manual agora reutiliza `normalize_email` e `normalize_phone` para
validar os contatos antes de entrar na persistência. E-mails com espaço ou mais
de um `@` e telefones alfabéticos ou curtos são rejeitados com `422`, sem criar
lead. Formatos reais com pontuação, DDD e código `55` continuam aceitos.

O e-mail segue persistido na forma canônica em minúsculas. O telefone informado
continua preservado após `trim`, mantendo o contrato existente de exibição e
auditoria. O adapter e as regras dos leads automáticos não foram alterados.

### Evidência RED → GREEN

- RED dirigido: `4 failed, 7 passed`; falharam exatamente `a@b@c`,
  `a b@example.com`, `abc` e `123`, todos ainda retornando `201` antes da
  correção.
- GREEN dirigido: `11 passed, 18 deselected`.
- Focado: `32 passed, 3 skipped`.
- Permissões e API correlata: `55 passed, 4 skipped`.
- API completa: `213 passed, 12 skipped`.

Os skips permanecem exclusivamente ligados à indisponibilidade local do
replica set MongoDB `rs0`.
