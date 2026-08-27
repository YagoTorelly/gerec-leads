# Roadmap — Gerenciador de Leads WTG

- **Baseline:** 27 de agosto de 2026
- **Fonte funcional:** `SPEC_GERENCIADOR_DE_LEADS_WTG.md`
- **Arquitetura aprovada:** MongoDB como persistência única; backend e automações Python na Railway; cliente Next.js/React na Vercel
- **Estratégia:** consolidar a fundação MongoDB e o backend Python antes da interface e das integrações reais
- **Estado atual:** governança da migração MongoDB/Vercel/Railway em registro; fundação anterior concluída, porém tecnicamente substituída e tratada como legado

## Regra de avanço

Uma etapa só libera a seguinte quando:

- todos os entregáveis previstos existem;
- os testes e verificações da etapa passam;
- divergências com o SPEC foram resolvidas;
- não existem falhas críticas abertas;
- a evidência de validação foi registrada.

## Etapa 0 — Governança e organização

**Objetivo:** tornar o projeto navegável e impedir decisões silenciosas.

Entregáveis:

- SPEC definido como fonte canônica;
- `AGENTS.md` com fluxo obrigatório de desenvolvimento;
- roadmap com etapas e critérios de saída;
- arquitetura MongoDB/Vercel/Railway documentada;
- registro das decisões aprovadas e das decisões substituídas;
- estrutura futura concentrada em `gerec_leads/`;
- `.github/workflows/gerec-leads-ci.yml` mantido como única exceção técnica fora da pasta do produto;
- `WTG - Leads.xlsx` preservado como fixture mock A–Q, com projeção M–P para o vendedor;
- arquivos temporários e segredos ignorados pelo Git.

Critério de saída:

- documentação revisada e aprovada por Yago;
- nenhuma ambiguidade estrutural bloqueando a fundação MongoDB.

## Etapa 1 — Fundação anterior registrada como legado

**Objetivo histórico:** criar uma fundação local reproduzível, ainda sem regras funcionais.

Plano executado: `docs/superpowers/plans/2026-08-25-etapa-1-esqueleto-executavel.md`.

Estado:

- o workspace, o cliente Next.js, o tooling e o CI existentes podem ser aproveitados quando compatíveis;
- componentes de Supabase/PostgreSQL e n8n pertencem à fundação substituída e não recebem novas regras, dados ou dependências;
- a remoção física do legado ocorre em tarefa própria, depois que os comandos equivalentes estiverem cobertos pela nova arquitetura.

Critério de saída:

- concluída historicamente; não autoriza continuar a arquitetura substituída.

## Etapa 2 — Fundação MongoDB e backend Python

**Objetivo:** estabelecer o único banco e a fronteira server-side do produto.

Entregáveis:

- backend/API Python 3.12+ com configuração validada;
- MongoDB local em replica set e database `gerec_leads`;
- coleções normalizadas, validações e índices versionados;
- transações multi-documento disponíveis em development, staging e production;
- autenticação própria, sessões revogáveis e senhas derivadas com algoritmo forte;
- papéis `admin` e `seller` e autorização aplicada pela API e pelos repositórios;
- cinco contas iniciais sintéticas/locais conforme a configuração aprovada;
- testes de conexão, schema, índices, transações, autenticação e acesso cruzado.

Critério de saída:

- o backend falha explicitamente sem replica set;
- administrador acessa o escopo global permitido;
- cada vendedor acessa apenas dados e histórico próprios, inclusive por chamada direta à API;
- nenhuma URI ou credencial MongoDB chega ao cliente web.

## Etapa 3 — Núcleo transacional Python

**Objetivo:** provar as regras críticas independentemente da interface e das automações.

Entregáveis:

- calendário de dias úteis e relógio controlável;
- SLA de 24 horas úteis e lembrete de 4 horas úteis;
- fila global e cursor versionado em transação MongoDB;
- bloqueio derivado de feedback vencido;
- perda de vez e créditos compensatórios;
- propriedade da empresa e recorrência entre campanhas;
- atribuição temporária e transferência permanente;
- FIFO de leads parados;
- idempotência, índices únicos, histórico, auditoria e outbox no mesmo commit transacional;
- testes unitários, integrados e concorrentes.

Critério de saída:

- resultados equivalentes ao processamento sequencial sob concorrência;
- nenhuma atribuição ou venda duplicada;
- rollback não deixa cursor, histórico, auditoria ou outbox parciais;
- regras críticas dos critérios de aceite comprovadas automaticamente.

## Etapa 4 — Ingestão e operação do backend

**Objetivo:** completar os fluxos operacionais com dados sintéticos antes das telas definitivas.

Entregáveis:

- contrato versionado para Google Sheets;
- fixture `WTG - Leads.xlsx` documentado como mock A–Q da aba `Leads`, com projeção de origem M–P para o vendedor;
- adapter para a planilha mock e substituição localizada pela planilha final;
- bootstrap completo com liberação manual em lotes;
- sincronização incremental idempotente;
- campanhas e pendências;
- feedbacks e renovação do SLA;
- tentativas em dias úteis distintos;
- qualificação, desqualificação, sem conversão e ganho;
- overrides e conflitos;
- comandos administrativos e testes.

Critério de saída:

- fluxo completo funciona pela API Python sem interface definitiva;
- linhas repetidas, movidas ou removidas produzem o resultado previsto;
- falhas externas não desfazem ações de negócio confirmadas.

## Etapa 5 — Automações Python na Railway

**Objetivo:** executar integrações e tarefas agendadas sem deslocar regras do domínio.

Entregáveis:

- worker Python para consumir a outbox;
- job Python de sincronização do Google Sheets;
- agendas, locks e idempotency keys persistidos no MongoDB;
- alertas, lembretes e relatórios consolidados;
- retries limitados, fila de falhas e observabilidade;
- configuração de serviços e variáveis da Railway sem credenciais no repositório.

Critério de saída:

- reexecuções não duplicam leads, atribuições, vendas ou mensagens;
- workers reutilizam os mesmos serviços de domínio da API;
- nenhum job escolhe vendedor, altera cursor ou decide resultado por conta própria.

## Etapa 6 — Cliente Vercel do administrador

**Objetivo:** permitir operação global com clareza, segurança e rastreabilidade.

Entregáveis:

- login e estrutura visual WTG compartilhada;
- cliente Next.js/React configurado para chamar somente a API Python;
- dashboard global;
- campanhas e aprovação;
- fila, cursor, pausas e créditos;
- central de pendências;
- listas e detalhes de leads;
- overrides e conflitos;
- auditoria, relatórios e exportações;
- estados de carregamento, vazio, erro e confirmação.

Critério de saída:

- administrador executa os casos de uso previstos sem acesso direto ao MongoDB;
- ações críticas possuem confirmação e auditoria;
- interface desktop passa por acessibilidade e E2E em largura mínima de 1280 px.

## Etapa 7 — Cliente Vercel do vendedor

**Objetivo:** oferecer uma experiência privada e focada no acompanhamento comercial.

Entregáveis:

- dashboard exclusivamente individual;
- próximos vencimentos e atrasados;
- leads próprios e histórico permitido;
- posição e saldo individuais na fila;
- detalhe, contato, feedback e tentativa;
- qualificação, desqualificação, encerramento e ganho;
- experiência exclusivamente desktop, com largura mínima suportada de 1280 px.

Critério de saída:

- vendedor conclui seus fluxos ponta a ponta;
- nenhuma tela, consulta ou chamada revela dados dos colegas;
- estados e prazos são compreensíveis sem depender apenas de cor.

## Etapa 8 — Integrações reais

**Objetivo:** conectar serviços externos pelos jobs Python da Railway.

Entregáveis:

- Google Sheets definitivo;
- sincronização a cada 5 minutos;
- provedor de e-mail escolhido e configurado;
- resumos, alertas e lembretes idempotentes;
- tentativas, reprocessamento e fila de falhas;
- observabilidade das integrações.

Critério de saída:

- indisponibilidade externa é recuperável;
- reexecuções preservam idempotência;
- nenhuma credencial aparece no navegador ou no repositório;
- regras críticas permanecem no backend Python.

## Etapa 9 — Hardening e piloto

**Objetivo:** comprovar que o sistema pode receber dados e usuários reais com risco controlado.

Entregáveis:

- suíte E2E dos dois perfis;
- auditoria de autorização, segurança e LGPD;
- validação de desempenho e acessibilidade;
- backup e restauração do MongoDB testados;
- staging isolado e sem dados pessoais reais;
- implantação validada do cliente na Vercel e dos serviços Python na Railway;
- importação inicial em lotes controlados;
- piloto acompanhado com critérios de interrupção e recuperação.

Critério de saída:

- critérios de aceite do SPEC validados;
- nenhuma falha crítica aberta;
- staging aprovado por Yago.

## Etapa 10 — Produção e estabilização

**Objetivo:** implantar, monitorar e estabilizar o MVP.

Entregáveis:

- cluster MongoDB de produção com replica set, backup e credenciais próprios;
- cliente Next.js/React publicado na Vercel;
- API, workers e agendas Python publicados na Railway;
- domínio, segredos e alertas configurados;
- plano de go-live e rollback;
- documentação operacional;
- remoção final dos artefatos legados após comprovação de equivalência;
- período de estabilização monitorado.

Critério de saída final:

- 30 critérios de aceite validados;
- testes críticos, autorização, concorrência e E2E aprovados;
- importação real idempotente;
- backup e recuperação comprovados;
- piloto sem falhas críticas abertas;
- aceite final de Yago.

## Dependências externas conhecidas

- planilha Google definitiva;
- clusters MongoDB isolados para staging e production, ambos com replica set;
- projetos Railway para API, workers e agendas Python;
- projeto Vercel para o cliente Next.js/React;
- definição do provedor de e-mail;
- credencial de leitura do Google Sheets;
- domínio final;
- calendário oficial de feriados nacionais e estaduais de São Paulo.

Essas dependências não bloqueiam as Etapas 0 a 4 quando adapters, serviços locais e dados sintéticos forem usados.
