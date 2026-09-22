# Task 3 — Relatório de implementação

## Status

Implementada a exportação administrativa de todos os leads em Excel e a
consulta paginada do histórico de exportações. As duas rotas são exclusivas de
administrador; vendedor recebe `403` antes de qualquer leitura ou gravação.

O arquivo contém somente a aba `Leads`, com os campos aprovados no design. Datas
são strings ISO 8601 em `America/Sao_Paulo`; IDs e telefones são células de texto.
O telefone original da origem tem precedência sobre a versão normalizada, e
valores iniciados por `=` permanecem texto em vez de fórmulas do Excel.

## Arquivos

- Criado `apps/api/src/gerec_api/domain/exportations.py` com
  `ExportationService`, `ExportationResult`, geração XLSX e erro público seguro.
- Criado
  `apps/api/src/gerec_api/infrastructure/mongo/exportation_repository.py` com a
  projeção administrativa, resolução de referências e histórico paginado.
- Criada a migração versionada
  `apps/api/src/gerec_api/infrastructure/mongo/migrations/20260923_exportation_history.py`;
  a migração aplicada de 22/09 não foi editada.
- Alterados registro de coleções, validator, índices e runner para a coleção
  `exportations` e os índices de `createdAt` e `actorId + createdAt`.
- Alterados `apps/api/src/gerec_api/routes/admin.py` e
  `apps/api/src/gerec_api/main.py` para as rotas e injeção do serviço.
- Criado `apps/api/tests/integration/test_exportations.py` e ajustado o contrato
  de índices não únicos em `apps/api/tests/integration/test_indexes.py`.

## Contratos entregues

- `GET /api/admin/exportations` retorna `items`, `page`, `pageSize` e `total`;
  cada item possui `createdAt`, `administratorName`, `leadCount`, `filters` e
  `status`, em ordem decrescente de criação.
- `GET /api/admin/exportations/leads` responde com MIME XLSX e
  `Content-Disposition` de anexo.
- Exportação vazia produz workbook válido somente com cabeçalho e registra
  `leadCount=0`.
- Sucesso é registrado somente depois de o workbook estar pronto. Falhas de
  leitura, geração ou persistência retornam mensagem recuperável sem stack trace,
  URI ou payload privado; a tentativa de erro usa apenas `errorCode` estável.
- O nome do administrador vem de `users.fullName`, com e-mail autenticado como
  fallback.

## Evidência TDD

- RED inicial: `python -m pytest apps/api/tests/integration/test_exportations.py -q`
  falhou na coleta com `ModuleNotFoundError: gerec_api.domain.exportations`.
- RED de segurança/schema: 2 falhas esperadas, por fórmula Excel (`data_type='f'`)
  e validator ausente para `exportations`.
- RED de telefone: a exportação usou `0551199991234` em vez de
  `(055) 11 9999-1234` até a precedência da origem ser corrigida.
- GREEN focado final: `9 passed`.

## Verificações

- `python -m pytest apps/api/tests/integration/test_exportations.py -q` —
  `9 passed`.
- `python -m pytest apps/api/tests -q -rs` — `222 passed, 12 skipped`.
- `python -m compileall -q apps/api/src apps/api/tests` — exit `0`.
- `git diff --check` — exit `0`.

Os 12 skips são exclusivamente testes que exigem MongoDB replica set `rs0`,
indisponível no ambiente local. Não houve fallback silencioso para fake nesses
cenários.

## Preservação de escopo

- Nenhum arquivo de frontend foi alterado por esta task.
- A remoção preexistente de `apps/api/.env.example` e o diretório não rastreado
  `tools/google-sheets-diagnostic/` foram preservados fora do staging/commit.
- A revisão por subagente não foi executada porque a delegação da Task 3 proibiu
  subagentes; a revisão foi feita diretamente sobre o diff e validada pela suíte.

## Correção pós-revisão — rodada 1

### Causa corrigida

A gravação de `success` usava `insert_one` sem identidade da tentativa. Se o
MongoDB confirmasse a escrita e o ACK fosse perdido, o serviço interpretava a
exceção como ausência de commit e inseria outro documento `error`, deixando o
histórico contraditório.

Cada chamada agora gera um `attemptId` UUID estável. O repositório finaliza a
tentativa com `upsert + $setOnInsert`, de modo que o primeiro estado final vence.
Após uma exceção ao gravar `success`, o serviço consulta a mesma tentativa: se o
sucesso já estiver persistido, entrega o arquivo; se não houver registro,
finaliza aquela identidade como `error`. Nenhum segundo documento é criado.

Foi adicionada a migração versionada
`20260924_exportation_attempt_id.py`, que atribui IDs determinísticos
`legacy:<_id>` aos registros anteriores. O bootstrap aplica depois da migração o
índice único `exportations_attempt_id_unique`. A migração aplicada de 23/09 não
foi editada nem passou a criar implicitamente o índice novo.

### Evidência RED → GREEN

- RED dirigido: `4 failed, 9 passed`:
  - falha antes do commit não possuía `attemptId`;
  - sucesso confirmado com ACK perdido retornava `ExportationError`;
  - repositório não aceitava finalização idempotente por tentativa;
  - migração/índice único ainda não existiam.
- GREEN focado: `13 passed`.
- Runner/schema/índices: `30 passed, 4 skipped` por `rs0` indisponível.
- API completa: `226 passed, 12 skipped` por `rs0` indisponível.

### Verificações da correção

- `python -m pytest apps/api/tests/integration/test_exportations.py -q` —
  `13 passed`.
- `python -m pytest apps/api/tests -q -rs` — `226 passed, 12 skipped`.
- `python -m compileall -q apps/api/src apps/api/tests` — exit `0`.
- `git diff --check` — exit `0`.
