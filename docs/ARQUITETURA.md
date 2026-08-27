# Arquitetura inicial — Gerenciador de Leads WTG

## Estado

Arquitetura de migração aprovada em 27 de agosto de 2026. A fundação anterior é legada; a próxima etapa implementa o backend Python e a persistência MongoDB.

## Princípio central

O produto permanece um workspace modular dentro de `gerec_leads/`. MongoDB é a única fonte de persistência, no banco `gerec_leads`. O backend/API Python concentra autenticação, autorização, consistência, concorrência e comandos críticos. Next.js/React é somente o cliente web na Vercel; automações são jobs Python idempotentes na Railway.

## Estrutura planejada

```text
gerec_leads/
├── apps/
│   └── web/                  # Next.js, React e TypeScript
├── services/
│   ├── api/                  # Backend/API Python e regras críticas
│   └── workers/              # Ingestão, outbox e agendas Python
├── database/
│   ├── migrations/           # Evolução versionada de dados, schemas e índices
│   ├── seed/                 # Dados sintéticos locais
│   └── tests/                # Transações, índices e autorização
├── integrations/             # Contratos dos serviços externos
├── tests/
│   ├── e2e/                  # Fluxos ponta a ponta
│   └── contracts/            # Contratos das integrações
├── docs/                     # Arquitetura, decisões e operação
├── tooling/                  # Scripts de desenvolvimento e validação
├── AGENTS.md
├── ROADMAP.md
├── WTG - Leads.xlsx         # Fixture mock A–Q fornecido pelo usuário
└── SPEC_GERENCIADOR_DE_LEADS_WTG.md
```

A estrutura pode ganhar arquivos internos durante o planejamento, mas o backend do produto é Python e não deve ser substituído por APIs Next.js ou por um backend Node separado sem nova decisão arquitetural.

O workspace usa Node.js 24 LTS. A versão fica declarada em `.nvmrc` e em `package.json` para reduzir diferenças entre desenvolvimento local e CI.

### Exceção técnica do CI

O único arquivo do novo sistema autorizado fora de `gerec_leads/` é `.github/workflows/gerec-leads-ci.yml`, pois essa localização é obrigatória para descoberta pelo GitHub Actions. O workflow observa somente `gerec_leads/**` e chama scripts definidos dentro do workspace; ele não recebe regras de negócio nem configurações secretas.

## Módulos e interfaces

### Cliente web

Responsável por:

- páginas, formulários e estado de sessão do cliente;
- chamadas HTTPS autenticadas à API Python;
- validação de entrada para experiência do usuário;
- apresentação de consultas paginadas e filtradas pela API;
- apresentação em português do Brasil;
- experiência exclusivamente desktop, com largura mínima suportada de 1280 px.

Não pode decidir diretamente:

- próximo vendedor;
- avanço do cursor;
- bloqueio por atraso;
- propriedade de empresa;
- consumo de créditos;
- resultado de venda.

Também não pode abrir conexão com MongoDB, conter credenciais de banco ou executar regras críticas em Route Handlers/Server Actions.

### Núcleo transacional

É um módulo profundo no backend Python: oferece comandos pequenos e explícitos, ocultando transações MongoDB, escritas condicionais, índices, histórico, auditoria e idempotência em sua implementação.

Interfaces conceituais principais:

- sincronizar registros de origem;
- liberar lote inicial;
- distribuir lead elegível;
- registrar feedback ou tentativa;
- registrar resultado;
- aprovar campanha;
- direcionar temporariamente;
- transferir propriedade;
- reverter resultado autorizado.

Os callers e os testes atravessam as mesmas interfaces. Campos sensíveis não são atualizados diretamente pelo cliente. Comandos multi-documento usam transações e exigem MongoDB configurado como replica set em todos os ambientes.

### Job Python de Google Sheets

Responsável por:

- ler a planilha;
- normalizar o payload externo;
- fornecer idempotency key e correlation ID;
- chamar o comando de ingestão;
- registrar e reprocessar falhas externas.

O job roda na Railway, é idempotente e chama a mesma camada de aplicação usada pela API; ele nunca decide distribuição, cursor ou propriedade.

O fixture `WTG - Leads.xlsx` registra a planilha mock atual: aba `Leads`, colunas A–Q. Para o vendedor, a projeção de dados originados da planilha é limitada a M–P (`você_tem_cnpj_ou_mei?`, `full_name`, `phone_number` e `email`); Q `lead_status` fica excluída. Campanha, status interno, prazo, tentativas e outros campos operacionais autorizados pelo sistema continuam disponíveis conforme o perfil porque não compõem essa projeção de origem.

A coluna M é somente a resposta a uma pergunta e não contém o número real do CNPJ. Portanto, o mock não satisfaz as regras de identidade, deduplicação e recorrência por CNPJ. O adapter da planilha mock será substituído de forma localizada quando a planilha definitiva for fornecida, sem deslocar essas regras para a integração.

### Worker Python de notificações

Responsável por consumir a outbox de forma idempotente e entregar mensagens. Roda na Railway; o provedor real será definido depois. A indisponibilidade de e-mail nunca desfaz uma ação de negócio.

## Fluxo principal de dados

```text
Google Sheets
    ↓ leitura a cada 5 minutos
Job Python na Railway
    ↓ comando idempotente
Backend/API Python na Railway
    ↓ transação: validar → deduplicar → distribuir ou deixar pendente
MongoDB / gerec_leads (replica set)
    ↓ coleções normalizadas + histórico + auditoria + outbox
Backend/API Python
    ↓ HTTPS; autorização por perfil
Next.js/React na Vercel
    ↓
Administrador ou vendedor
```

## Segurança

- O backend Python gerencia autenticação, sessão e autorização; senhas ficam somente como hash forte.
- Toda consulta e alteração comercial aplica escopo por perfil no backend e no filtro MongoDB.
- Vendedores consultam somente seus dados e sua participação histórica permitida.
- O histórico do antigo responsável não inclui ações posteriores do novo responsável.
- Ações administrativas verificam o papel também no servidor.
- Credenciais administrativas e do MongoDB ficam apenas nos serviços da Railway.
- O cliente hospedado na Vercel nunca recebe URI, usuário ou senha do MongoDB.
- Logs evitam payloads pessoais completos.

## Ambientes

- `development`: backend e workers Python locais, MongoDB em replica set e dados sintéticos.
- `staging`: cliente na Vercel, serviços na Railway e cluster MongoDB próprios, sem dados pessoais reais.
- `production`: projetos Vercel/Railway e cluster MongoDB oficiais, todos separados de staging.

Cada ambiente usa credenciais próprias. Sem replica set, a inicialização do backend falha explicitamente porque os comandos críticos dependem de transações multi-documento.

## Tratamento do legado

O código fora de `gerec_leads/` não integra a nova arquitetura. Ele pode ser consultado somente para compreender identidade visual autorizada. Reutilização de código ou dados exige análise e aprovação próprias.

## Qualidade arquitetural

- Criar seams somente onde existe variação real, como planilha mock/final e provedor de notificações.
- Evitar módulos rasos que apenas repassam chamadas.
- Concentrar regras para obter locality: uma correção na fila deve valer para todos os callers.
- Dependências de tempo, integrações e autenticação devem ser controláveis em testes.
- Toda etapa segue os critérios de saída de `ROADMAP.md`.
