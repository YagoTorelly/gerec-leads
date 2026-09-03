# Design — Alertas de novos leads por e-mail

**Data:** 03/09/2026  
**Status:** Design aprovado em conversa; aguardando revisão do documento antes do plano de implementação.  
**Escopo:** alertas operacionais por e-mail e normalização de horários exibidos.

## 1. Objetivo

Enviar alertas úteis aos vendedores sem alterar a lógica da fila, a atribuição transacional ou as permissões.

Existem dois fluxos:

1. novos leads atribuídos por uma execução de sincronização: um resumo por vendedor e por sincronização;
2. transferência manual de propriedade: um aviso individual imediato ao novo proprietário.

Uma falha de e-mail nunca desfaz uma atribuição, uma transferência, uma alteração de status ou qualquer outro efeito comercial confirmado.

## 2. Decisões aprovadas

- O resumo de uma sincronização agrupa todos os leads novos recebidos pelo mesmo vendedor naquela execução.
- Não haverá um e-mail por lead dentro de uma sincronização.
- Uma transferência manual gera um aviso individual ao novo proprietário.
- O remetente é `contato@wtgseguros.com.br`.
- O SMTP é `smtp.oncorretor.com.br`, porta `587`.
- A conexão usa STARTTLS obrigatório.
- Usuário SMTP: `contato@wtgseguros.com.br`.
- Senha SMTP: variável de ambiente exclusiva da Railway.
- Nenhuma credencial fica no código, MongoDB, navegador, documentação pública ou logs.
- O conteúdo contém somente nome do lead, telefone e link para o dashboard.
- Não incluir campanha, e-mail do lead ou outros campos de origem.
- A URL do dashboard vem de configuração por ambiente.
- Datas, quando exibidas, usam `America/Sao_Paulo`.
- O horário sem fuso da planilha é horário local de São Paulo.
- Instantes são armazenados em UTC e devolvidos com offset explícito.
- O administrador acompanha falhas e pendências, mas não edita tratativas de vendedor.

## 3. Arquitetura existente aproveitada

O projeto já possui:

- `SyncJob`, responsável por importar e disparar atribuições;
- comandos transacionais da fila;
- coleção MongoDB `notification_outbox`;
- `MongoOutboxRepository` com claim atômico;
- `OutboxWorker` com retry, lock, idempotência e dead-letter;
- `WebhookDeliveryAdapter` como fronteira atual de entrega;
- auditoria e eventos de atribuição.

Não criar um segundo sistema de fila ou uma integração paralela fora da outbox.

## 4. Fluxo de resumo da sincronização

1. A sincronização recebe um `syncRunId` determinístico e não vazio.
2. Cada atribuição automática permanece em sua própria transação da fila.
3. O evento de atribuição gravado na outbox recebe `syncRunId`, `sellerId`, `leadId`, tipo da atribuição e chave idempotente.
4. O evento também identifica o grupo lógico `assignment-summary:{syncRunId}:{sellerId}`.
5. Um agregador consulta eventos pendentes do mesmo grupo.
6. O agregador resolve o e-mail atual do vendedor e os dados mínimos de cada lead.
7. A lista é ordenada de forma determinística por instante de atribuição e identificador do lead.
8. Se o grupo não tiver leads, nenhum e-mail é enviado.
9. O adapter SMTP monta uma mensagem HTML acessível e uma parte texto simples.
10. O worker envia o resumo usando STARTTLS.
11. Somente após confirmação de sucesso todos os eventos do grupo são marcados como enviados.
12. Uma nova tentativa encontra a mesma chave idempotente e não cria outro grupo lógico.

O agregador não pode marcar eventos como enviados antes do SMTP confirmar sucesso.

## 5. Fluxo de transferência manual

1. O administrador confirma a transferência pela operação existente.
2. A transação mantém as regras atuais: não altera cursor, ordem FIFO ou créditos.
3. A transação grava o evento `lead.owner_transferred` na outbox.
4. O evento usa chave `owner-transfer:{leadId}:{commandId}`.
5. O destinatário é o novo responsável ativo no momento do preparo do envio.
6. O worker monta um e-mail individual com nome, telefone e link para o dashboard.
7. O antigo vendedor continua sem qualquer acesso operacional ao lead, conforme a decisão vigente.
8. O histórico permanece disponível para administração e novo responsável.

Transferência não deve entrar no resumo de uma sincronização.

## 6. Contrato dos eventos

### 6.1 Resumo de atribuição

```json
{
  "eventType": "lead.assignment_email_requested",
  "syncRunId": "sync-2026-09-03-001",
  "sellerId": "...",
  "groupKey": "assignment-summary:sync-2026-09-03-001:...",
  "leadIds": ["..."],
  "idempotencyKey": "assignment-summary:sync-2026-09-03-001:..."
}
```

O payload persistido deve conter identificadores e metadados operacionais, não cópia desnecessária de dados pessoais.

### 6.2 Transferência

```json
{
  "eventType": "lead.owner_transfer_email_requested",
  "leadId": "...",
  "sellerId": "...",
  "idempotencyKey": "owner-transfer:...:..."
}
```

O worker busca nome e telefone atuais no momento de preparar a mensagem. Se o lead tiver sido arquivado ou estiver sem telefone, a regra de fallback deverá ser definida no plano e coberta por teste; não inventar dados.

## 7. Adapter SMTP

Criar uma fronteira testável, independente do domínio:

- recebe uma mensagem já renderizada;
- abre conexão com host e porta configurados;
- inicia STARTTLS;
- autentica com usuário e senha server-side;
- envia remetente, destinatário, assunto e partes MIME;
- fecha a conexão mesmo em erro;
- transforma falhas de rede/autenticação em erro de entrega para retry.

O worker não deve conter regra de negócio de fila, status comercial ou propriedade.

Configuração prevista, com nomes finais definidos no plano:

- `SMTP_HOST=smtp.oncorretor.com.br`;
- `SMTP_PORT=587`;
- `SMTP_USERNAME=contato@wtgseguros.com.br`;
- `SMTP_PASSWORD`;
- `SMTP_FROM=contato@wtgseguros.com.br`;
- `DASHBOARD_PUBLIC_URL`.

Valores de produção não devem ser commitados.

## 8. Templates

### 8.1 Resumo de novos leads

Assunto:

`Chegaram leads novos para você — WTG`

Texto base:

```text
Chegaram leads novos para você!!!

As informações dos novos leads já estão no gerenciador de leads.

{nome do lead}
{telefone do lead}
{link para acesso}
```

Para vários leads, repetir o bloco de nome, telefone e link, sem expor identificadores internos.

### 8.2 Transferência

Assunto:

`Lead transferido para você — WTG`

Texto base:

```text
Um lead foi transferido para você.

{nome do lead}
{telefone do lead}
{link para acesso}
```

Os templates terão versão HTML e texto simples. O link aponta para o dashboard configurado e não deve incluir dados sensíveis na URL.

## 9. Idempotência e concorrência

- `syncRunId` identifica uma execução completa.
- `groupKey` identifica um resumo por vendedor dentro da execução.
- Índice único impede dois grupos iguais.
- Claim atômico impede dois workers de processarem o mesmo evento simultaneamente.
- Lock expirado permite recuperação de worker interrompido.
- Retry usa backoff e limite configurado.
- Dead-letter registra evento, chave, tipo e erro resumido.
- O envio duplicado por uma falha após o SMTP e antes do `mark_sent` deve ser tratado como risco de entrega externa; o adapter deve usar a chave idempotente quando o provedor suportar. O plano deve documentar esse limite operacional.

## 10. Política de falhas

- Timeout/conexão recusada: retry.
- Erro temporário SMTP: retry.
- Falha de autenticação: retry limitado e alerta técnico.
- Destinatário inválido: dead-letter, sem desfazer o negócio.
- Vendedor desativado antes do preparo: evento não é enviado automaticamente; fica rastreável para decisão administrativa.
- Lead sem dados mínimos: falha explícita e segura, sem fabricar conteúdo.
- Falha de consulta ao MongoDB: retry do evento.

Logs devem conter somente `eventId`, `eventType`, `groupKey`, tentativa, status e erro técnico truncado. Nunca registrar senha, token ou corpo integral do lead.

## 11. Contrato de horário

- Timestamp ingênuo da planilha: `America/Sao_Paulo`.
- Timestamp com `Z` ou offset: respeitar o offset informado.
- Persistência: UTC.
- API: ISO 8601 com `Z` ou offset.
- Frontend: `Intl.DateTimeFormat` em `America/Sao_Paulo`.
- E-mail: mesma conversão, se datas forem incluídas.

O plano deve localizar todos os parsers e formatadores, sem alterar registros legados sem evidência da semântica original. Qualquer correção histórica precisa de migração versionada, relatório de afetados e rollback operacional.

## 12. Testes obrigatórios

### Domínio e integração

- uma sincronização com vários leads para um vendedor produz um resumo único;
- dois vendedores na mesma sincronização produzem dois grupos;
- sincronização sem novas atribuições não produz e-mail;
- recorrências atribuídas automaticamente entram no resumo quando forem novas atribuições daquela execução;
- transferências ficam fora do resumo;
- transferência cria aviso individual para o novo responsável;
- repetição da mesma sincronização não cria grupo duplicado;
- dois workers concorrentes não enviam dois grupos lógicos;
- atribuição permanece confirmada se SMTP falhar;
- erro de SMTP retorna ao retry e depois dead-letter;
- vendedor sem e-mail válido é rastreável;
- payload não contém campanha, e-mail do lead ou segredo.

### SMTP

- usa host e porta corretos;
- exige STARTTLS;
- autentica com variáveis de ambiente;
- envia remetente aprovado;
- produz MIME HTML + texto simples;
- encerra conexão em sucesso e erro;
- não registra credenciais.

### Horário

- `14:11` sem fuso permanece `14:11` em São Paulo;
- `17:11Z` aparece como `14:11` em São Paulo;
- timestamps com offset diferente são convertidos corretamente;
- o envio não calcula SLA, prazo ou lembrete; timestamps seguem apenas a conversão de origem para America/Sao_Paulo;
- horários legados não são deslocados sem classificação;
- e-mail e interface usam a mesma regra.

### Frontend e E2E

- vendedor recebe resumo renderizado com nome, telefone e link;
- link abre o dashboard;
- transferência mostra o aviso individual após confirmação;
- estados de pendência e erro são legíveis;
- admin visualiza estado da outbox sem editar tratativas;
- screenshot em 1440×900;
- acesso de vendedor continua restrito aos próprios leads.

## 13. Observabilidade e operação

Adicionar métricas/logs para:

- eventos criados por tipo;
- grupos agregados;
- mensagens enviadas;
- tempo entre atribuição e envio;
- retries;
- dead-letter;
- falhas por código SMTP;
- grupos sem destinatário;
- última execução de sincronização com alertas.

O administrador deve conseguir distinguir:

- atribuição concluída e e-mail pendente;
- e-mail enviado;
- retry em andamento;
- dead-letter que exige intervenção.

Desativar o alerta deve ser uma configuração operacional independente da fila.

## 14. Alterações documentais necessárias antes do código

- registrar a nova regra na seção de governança do SPEC: regra anterior, nova regra, motivo, impactos, migração, testes e aprovação;
- atualizar `docs/DECISOES.md` com decisão sobre resumo por sincronização, transferência individual, SMTP e horário;
- regenerar `docs/CONTEXTO_MESTRE_GERENCIADOR_DE_LEADS.md`;
- atualizar `docs/ARQUITETURA.md` se a fronteira do worker SMTP mudar;
- documentar variáveis sem valores secretos;
- criar plano de rollout, rollback e piloto.

## 15. Fora do escopo

- envio de WhatsApp;
- alteração da fila FIFO;
- alteração de status comercial por e-mail;
- edição administrativa de tratativas;
- inclusão de campanha, e-mail do lead ou dados adicionais no alerta;
- migração ampla de timestamps sem classificação;
- painel de preferências individuais de e-mail;
- provedor externo adicional além do SMTP aprovado.

## 16. Critérios de aceite

1. Após uma sincronização com novos leads, cada vendedor recebe no máximo um resumo daquela execução.
2. O resumo lista todos os leads novos atribuídos ao vendedor naquela execução.
3. O resumo contém apenas nome, telefone e link do dashboard.
4. Uma transferência manual envia um aviso individual ao novo proprietário.
5. Nenhum alerta de transferência afeta cursor, posição ou créditos da fila.
6. Retry e dead-letter funcionam sem desfazer atribuições.
7. STARTTLS e credenciais server-side são obrigatórios.
8. Horário local da planilha não aparece três horas adiantado.
9. Timestamps UTC existentes continuam sendo exibidos corretamente em São Paulo.
10. Todos os testes obrigatórios e gates de build, lint, typecheck e E2E passam.

## 17. Próximo passo

Após a revisão e aprovação deste documento, criar o plano executável em `docs/superpowers/plans/` com tarefas TDD pequenas, implementação por subagentes, revisão independente e evidências no ledger.
