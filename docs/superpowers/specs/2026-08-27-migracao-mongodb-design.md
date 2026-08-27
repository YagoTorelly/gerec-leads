# Migração do Gerenciador de Leads para MongoDB

**Data:** 27 de agosto de 2026  
**Status:** desenho aprovado em conversa; aguardando revisão escrita antes da implementação  
**Banco alvo:** MongoDB, database `gerec_leads`

## 1. Decisão e governança

O banco principal do Gerenciador de Leads será MongoDB. A aplicação não usará Supabase, PostgreSQL, Supabase Auth ou RLS.

### Regra anterior

O SPEC definia Next.js/React + Supabase Auth/PostgreSQL/RLS como arquitetura principal, com o PostgreSQL concentrando consistência, concorrência, permissões e comandos críticos.

### Nova regra proposta

Next.js/React será o site publicado na Vercel. Uma API/backend Python na Railway será o único núcleo de autenticação, domínio, persistência e automações. MongoDB será a única infraestrutura de dados, incluindo usuários, sessões, dados comerciais, fila, histórico, auditoria e outbox. As regras críticas serão comandos Python executados em transações MongoDB.

### Motivo

O produto será operado no MongoDB recém-criado para este sistema. O database está vazio, portanto não existe migração de dados comerciais a preservar.

### Impacto em dados

Nenhum dado será migrado. O workbook continua sendo mock de origem e a coluna `você_tem_cnpj_ou_mei?` não será interpretada como CNPJ real.

### Impacto técnico

- substituir migrations SQL por criação versionada de índices e validações MongoDB;
- substituir RLS por autorização no backend Python e filtros obrigatórios nos repositórios;
- substituir Supabase Auth por autenticação própria no backend Python;
- exigir MongoDB replica set para transações locais, staging e produção;
- publicar o site Next.js na Vercel e a API/worker Python na Railway;
- executar sincronizações, notificações e tarefas agendadas exclusivamente na Railway;
- atualizar tooling, testes, documentação e CI;
- manter as regras funcionais do SPEC, salvo aprovação posterior registrada.

### Testes novos ou ajustados

Serão necessários testes de índices, transações, rollback, idempotência, concorrência, autorização por papel, sessões revogadas e isolamento de vendedor. Os 30 critérios de aceite do SPEC continuam válidos.

## 2. Arquitetura aprovada

```text
Navegador
  -> site Next.js na Vercel
  -> API/backend Python na Railway
  -> adapter MongoDB
  -> MongoDB replica set (database gerec_leads)
```

O navegador nunca acessa o MongoDB diretamente. O frontend não decide atribuição, cursor, propriedade, SLA, créditos ou venda; ele chama a API Python autorizada.

Módulos e responsabilidades:

- `web`: apresentação Next.js e experiência desktop na Vercel;
- `auth`: usuários, derivação de senha, sessões, revogação e autorização no backend Python;
- `leads`: origem, normalização, deduplicação, campanhas, empresas e ocorrências;
- `queue`: cursor global, elegibilidade, rodízio, pausas e créditos de pulo;
- `operations`: feedbacks, SLA, tentativas, qualificação, conversão e vendas;
- `audit`: histórico imutável e auditoria;
- `notifications`: outbox, reprocessamento e integrações;
- `automation`: sincronização da origem, e-mails, alertas e tarefas agendadas na Railway;
- `mongo`: conexão, transações, índices e repositórios.

Cada módulo de domínio expõe uma interface pequena e profunda. A API Python e o worker de automações reutilizam essas mesmas interfaces. O adapter MongoDB fica atrás de uma seam única, permitindo testes com banco real e adapter em memória controlado.

## 2.1. Implantação

- Vercel hospeda somente o site Next.js e seus assets públicos;
- Railway hospeda a API Python e os workers/agendamentos Python;
- MongoDB é compartilhado por API e workers através de URI server-side;
- nenhum segredo ou URI do MongoDB chega ao bundle do navegador;
- ambientes local, staging e produção usam URIs, credenciais e bancos isolados.

## 3. Coleções do database `gerec_leads`

- `users`: identidade, e-mail normalizado, senha derivada, papel, ativo e posição;
- `sessions`: hash do token, usuário, criação, expiração e revogação;
- `queue_state`: documento singleton com cursor global e versão;
- `seller_queue`: posição, pausa e estado operacional;
- `skip_balances`: créditos compensatórios;
- `campaigns`: identidade externa, nomes e aprovação;
- `companies`: documento normalizado, dados, proprietário e status de cliente;
- `leads`: ocorrência única ativa por empresa + campanha, estados e SLA;
- `source_records`: linhas da origem, hash, presença e payload normalizado;
- `assignments`: histórico de responsáveis, tipo, período e idempotência;
- `feedback_cycles`: ciclos de 24 horas úteis, lembrete e vencimento;
- `feedbacks`: comentários operacionais válidos;
- `contact_attempts`: tentativas WhatsApp em dias úteis distintos;
- `qualification_events`: qualificação, desqualificação, reversão e motivos;
- `sales`: negócio ganho único por lead e vendedor creditado;
- `holidays`: feriados nacionais e de São Paulo;
- `notification_outbox`: eventos pendentes, tentativas e idempotência;
- `audit_log`: ator, ação, entidade, antes/depois e correlation ID;
- `system_settings`: fuso, SLA, lembrete, limiar e horário de resumo.

A coleção vazia atualmente chamada `gerec_leads` não concentrará todo o domínio. A coleção operacional de ocorrências será `leads`.

Índices únicos e validações devem garantir, no mínimo: e-mail, `sourceLeadId`, CNPJ válido quando presente, empresa + campanha ativa, uma atribuição atual, uma venda ativa, uma tentativa por lead/data útil, saldo não negativo e idempotência de comandos.

## 4. Comandos transacionais

Os comandos críticos usam uma transação MongoDB única e registram alteração, histórico, auditoria e outbox no mesmo commit:

- distribuir lead normal;
- atribuir recorrência;
- registrar feedback ou tentativa;
- qualificar, desqualificar ou encerrar sem conversão;
- registrar ou reverter negócio ganho;
- transferir proprietário;
- direcionar temporariamente;
- pausar, reativar ou reordenar a fila;
- importar linha idempotente e arquivar linha removida.

Cada comando recebe `idempotencyKey`. Repetição devolve o resultado original sem criar novo evento operacional.

O cursor da fila usa documento singleton, controle de versão e transação. O algoritmo preserva rodízio global, perda de vez, bloqueio por atraso, créditos de pulo, recorrência e FIFO conforme o SPEC.

## 5. Autenticação e autorização

Usuários e sessões serão armazenados no MongoDB. Senhas nunca serão persistidas em texto puro; será usado Argon2id ou scrypt com parâmetros configuráveis.

Sessões usarão token opaco em cookie `httpOnly`, `secure` em produção, `sameSite=lax`, expiração e revogação server-side. Usuário desativado não poderá iniciar sessão, consultar dados ou executar comandos.

O papel será verificado no servidor em toda ação. Repositórios receberão o contexto autorizado e aplicarão filtros de escopo, garantindo que vendedores só consultem seus leads e histórico permitido, inclusive por chamadas diretas.

## 6. Falhas e observabilidade

Erros serão classificados como validação, autorização, conflito de estado, duplicidade/idempotência, indisponibilidade do MongoDB ou falha posterior de notificação.

Falha de e-mail não desfaz a operação confirmada; o evento permanece na outbox para retry. Logs estruturados não registrarão senhas, tokens ou payloads pessoais completos.

MongoDB local, staging e produção terão replica set, URI isolada, credenciais separadas, backup e restauração testados.

## 7. Estratégia de testes

- unitários: normalização, calendário útil, SLA, elegibilidade, créditos e métricas;
- integração: índices, constraints, transações, rollback e outbox;
- concorrência: distribuições simultâneas com resultado equivalente ao sequencial;
- autorização: admin, vendedor, histórico pós-transferência e usuário desativado;
- E2E: login, dashboard, fila, feedback, tentativa, qualificação, conversão e exportação;
- relógio controlável: fins de semana, feriados e vencimentos;
- recuperação: backup e restauração antes do piloto.

## 8. Sequência de implementação

1. atualizar SPEC, decisões e arquitetura para a governança MongoDB/Vercel/Railway;
2. remover Supabase e criar configuração do site Vercel e da API Python;
3. criar adapter, conexão, replica set local e índices;
4. implementar autenticação e sessões no backend Python;
5. implementar coleções e repositórios, começando por `leads`;
6. migrar comandos transacionais de fila, SLA, propriedade e resultados para Python;
7. implementar automações Python, adapter do workbook e importação idempotente;
8. adaptar o site Next.js para consumir a API Python;
9. concluir testes unitários, integração, concorrência e E2E;
10. validar deploy Vercel/Railway, backup, restauração e piloto.

Nenhuma implementação começa antes da revisão escrita deste documento.
