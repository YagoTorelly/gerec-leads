# DEC-031 — Remoção integral de SLA e reconciliação da fila

Status: aprovada por Yago em 04/09/2026.

## Decisão

O fluxo vigente não cria, calcula, expõe ou entrega prazo, lembrete, ciclo de
SLA ou bloqueio automático. A disponibilidade da fila é exclusivamente
`Ativo` ou `Pausado`; a pausa é manual e administrativa.

Após importar o lote inteiro, a sincronização reconcilia em FIFO os leads
normais sem responsável que estejam `ready` ou estacionados exclusivamente por
`no_eligible_seller`. Assim, um lead que chegou quando não havia vendedor
elegível volta automaticamente à distribuição em uma sincronização posterior.

Leads recorrentes cujo proprietário está indisponível continuam estacionados
com `owner_unavailable` e não interrompem a distribuição dos leads normais.

## Migração e histórico

A migração versionada `20260904_remove_operational_sla` remove as projeções de
prazo dos leads, fecha ciclos legados abertos e cancela alertas de prazo ainda
não terminais. O bootstrap remove de forma idempotente o índice ativo desses
ciclos fora da transação, pois MongoDB não permite DDL em transações.
Comentários, atribuições, ciclos e alertas já concluídos permanecem como
histórico de auditoria.

O worker também recusa entregar um alerta legado caso ele tenha sido obtido por
um worker concorrente durante a execução da migração.

## Critérios de aceite

- Nenhuma API ou tela vigente contém prazo, lembrete ou bloqueio por atraso.
- Novo comentário altera somente a tratativa e sua situação comercial.
- O próximo sync atribui em FIFO os leads normais antes estacionados assim que
  houver vendedor ativo.
- Reexecutar sync sem mudança de disponibilidade não duplica eventos de
  estacionamento.
- O histórico legado não é apagado.
