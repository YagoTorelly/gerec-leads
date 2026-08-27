# Roadmap — Gerenciador de Leads WTG

- **Baseline:** 25 de agosto de 2026
- **Fonte funcional:** `SPEC_GERENCIADOR_DE_LEADS_WTG.md`
- **Estratégia:** construir fundação, banco e núcleo transacional antes da interface
- **Estado atual:** Etapa 1 concluída; Etapa 2 aguardando planejamento

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
- arquitetura inicial documentada;
- registro das decisões aprovadas;
- estrutura futura concentrada em `gerec_leads/`;
- arquivos temporários e segredos ignorados pelo Git.

Critério de saída:

- documentação revisada e aprovada por Yago;
- nenhuma ambiguidade estrutural bloqueando o esqueleto.

## Etapa 1 — Esqueleto executável

**Objetivo:** criar uma fundação local reproduzível, ainda sem regras funcionais.

Plano aprovado para execução: `docs/superpowers/plans/2026-08-25-etapa-1-esqueleto-executavel.md`.

Entregáveis:

- workspace modular;
- Node.js 24 LTS declarado como runtime do workspace;
- Next.js com App Router e TypeScript em `apps/web`;
- Supabase local executado por Docker;
- diretórios para n8n, testes, documentação e ferramentas;
- `.env.example` sem segredos;
- lint, formatação, typecheck, testes e CI;
- workflow mínimo do GitHub Actions na exceção aprovada `.github/workflows/gerec-leads-ci.yml`, limitado a `gerec_leads/**`;
- página mínima de diagnóstico da aplicação e conexão local.

Critério de saída:

- um novo desenvolvedor consegue iniciar aplicação e banco seguindo a documentação;
- todos os comandos de qualidade passam;
- nenhum recurso de negócio foi antecipado.

## Etapa 2 — Modelo de dados, Auth e RLS

**Objetivo:** criar a fundação de dados e provar o isolamento entre perfis.

Entregáveis:

- migrações versionadas do modelo aprovado;
- Supabase Auth e tabela de perfis;
- cinco contas iniciais locais;
- senhas aleatórias administráveis, sem troca obrigatória inicial;
- papéis `admin` e `seller`;
- RLS em todas as tabelas comerciais;
- histórico próprio somente leitura após transferência;
- seed exclusivamente sintético;
- testes de banco, Auth e RLS.

Critério de saída:

- administrador acessa o escopo global permitido;
- cada vendedor acessa apenas dados e histórico próprios;
- acesso cruzado falha também por chamada direta ao banco.

## Etapa 3 — Núcleo transacional

**Objetivo:** provar as regras críticas independentemente da interface e do n8n.

Entregáveis:

- calendário de dias úteis e relógio controlável;
- SLA de 24 horas úteis e lembrete de 4 horas úteis;
- fila global e cursor transacional;
- bloqueio derivado de feedback vencido;
- perda de vez e créditos compensatórios;
- propriedade da empresa e recorrência entre campanhas;
- atribuição temporária e transferência permanente;
- FIFO de leads parados;
- idempotência, locks, constraints, histórico e auditoria;
- testes unitários, integrados e concorrentes.

Critério de saída:

- resultados equivalentes ao processamento sequencial sob concorrência;
- nenhuma atribuição ou venda duplicada;
- regras críticas dos critérios de aceite comprovadas automaticamente.

## Etapa 4 — Ingestão e operação do backend

**Objetivo:** completar os fluxos operacionais com dados sintéticos antes das telas definitivas.

Entregáveis:

- contrato versionado para Google Sheets;
- fixture `WTG - Leads.xlsx` documentado como mock A–Q da aba `Leads`, com projeção de origem M–P para o vendedor;
- adaptador para a planilha mock e substituição localizada pela planilha final;
- bootstrap completo com liberação manual em lotes;
- sincronização incremental idempotente;
- campanhas e pendências;
- feedbacks e renovação do SLA;
- tentativas em dias úteis distintos;
- qualificação, desqualificação, sem conversão e ganho;
- overrides e conflitos;
- outbox e contratos de notificação;
- comandos administrativos e testes.

Critério de saída:

- fluxo completo funciona sem interface definitiva;
- linhas repetidas, movidas ou removidas produzem o resultado previsto;
- falhas de integração não desfazem ações de negócio.

## Etapa 5 — Frontend do administrador

**Objetivo:** permitir operação global com clareza, segurança e rastreabilidade.

Entregáveis:

- login e estrutura visual WTG compartilhada;
- dashboard global;
- campanhas e aprovação;
- fila, cursor, pausas e créditos;
- central de pendências;
- listas e detalhes de leads;
- overrides e conflitos;
- auditoria, relatórios e exportações;
- estados de carregamento, vazio, erro e confirmação.

Critério de saída:

- administrador executa os casos de uso previstos sem acesso direto ao banco;
- ações críticas possuem confirmação e auditoria;
- interface desktop passa por acessibilidade e E2E do perfil em largura suportada de no mínimo 1280 px.

## Etapa 6 — Frontend do vendedor

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

## Etapa 7 — Integrações reais

**Objetivo:** conectar serviços externos sem transferir regras de negócio para eles.

Entregáveis:

- workflows versionados do n8n;
- conexão com o n8n hospedado na Cloudfy;
- Google Sheets definitivo;
- sincronização a cada 5 minutos;
- provedor de e-mail escolhido e configurado;
- resumos, alertas e lembretes idempotentes;
- tentativas, reprocessamento e fila de falhas;
- observabilidade das integrações.

Critério de saída:

- reexecuções não duplicam leads, atribuições ou mensagens;
- indisponibilidade externa é recuperável;
- nenhuma credencial aparece no navegador ou no repositório.

## Etapa 8 — Hardening e piloto

**Objetivo:** comprovar que o sistema pode receber dados e usuários reais com risco controlado.

Entregáveis:

- suíte E2E dos dois perfis;
- auditoria de RLS, segurança e LGPD;
- validação de desempenho e acessibilidade;
- backup e restauração testados;
- staging isolado e sem dados pessoais reais;
- importação inicial em lotes controlados;
- piloto acompanhado com critérios de interrupção e recuperação.

Critério de saída:

- critérios de aceite do SPEC validados;
- nenhuma falha crítica aberta;
- staging aprovado por Yago.

## Etapa 9 — Produção e estabilização

**Objetivo:** implantar, monitorar e estabilizar o MVP.

Entregáveis:

- projeto Supabase de produção separado;
- aplicação publicada na Vercel;
- n8n Cloudfy conectado ao ambiente oficial;
- domínio, segredos, alertas e backups configurados;
- plano de go-live e rollback;
- documentação operacional;
- período de estabilização monitorado.

Critério de saída final:

- 30 critérios de aceite validados;
- testes críticos, RLS, concorrência e E2E aprovados;
- importação real idempotente;
- backup e recuperação comprovados;
- piloto sem falhas críticas abertas;
- aceite final de Yago.

## Dependências externas conhecidas

- planilha Google definitiva;
- projeto Supabase remoto para staging e produção;
- definição do provedor de e-mail;
- credenciais do Google Sheets e do n8n;
- domínio final;
- calendário oficial de feriados nacionais e estaduais de São Paulo.

Essas dependências não bloqueiam as Etapas 0 a 4 quando adapters e dados sintéticos forem usados.
