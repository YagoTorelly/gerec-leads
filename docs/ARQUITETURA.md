# Arquitetura inicial — Gerenciador de Leads WTG

## Estado

Arquitetura aprovada. A Etapa 1 está concluída, e a Etapa 2 aguarda planejamento.

## Princípio central

O produto será um workspace modular dentro de `gerec_leads/`. O PostgreSQL/Supabase concentra consistência, concorrência, permissões e comandos críticos. Next.js oferece a experiência do usuário e interfaces server-side. O n8n integra sistemas externos sem controlar regras de negócio.

## Estrutura planejada

```text
gerec_leads/
├── apps/
│   └── web/                  # Next.js, React e TypeScript
├── supabase/
│   ├── migrations/           # Mudanças versionadas do banco
│   ├── seed/                 # Dados sintéticos locais
│   ├── tests/                # Constraints, comandos e RLS
│   └── config.toml           # Configuração local
├── integrations/
│   └── n8n/                  # Workflows exportados e documentação
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

A estrutura pode ganhar arquivos internos durante o planejamento, mas não deve criar um backend Node separado sem nova decisão arquitetural.

O workspace usa Node.js 24 LTS. A versão fica declarada em `.nvmrc` e em `package.json` para reduzir diferenças entre desenvolvimento local e CI.

### Exceção técnica do CI

O único arquivo do novo sistema autorizado fora de `gerec_leads/` é `.github/workflows/gerec-leads-ci.yml`, pois essa localização é obrigatória para descoberta pelo GitHub Actions. O workflow observa somente `gerec_leads/**` e chama scripts definidos dentro do workspace; ele não recebe regras de negócio nem configurações secretas.

## Módulos e interfaces

### Aplicação web

Responsável por:

- autenticação e sessão;
- páginas e ações autorizadas;
- validação de entrada para experiência do usuário;
- consultas paginadas e filtradas no servidor;
- apresentação em português do Brasil;
- experiência exclusivamente desktop, com largura mínima suportada de 1280 px.

Não pode decidir diretamente:

- próximo vendedor;
- avanço do cursor;
- bloqueio por atraso;
- propriedade de empresa;
- consumo de créditos;
- resultado de venda.

### Núcleo transacional

É um módulo profundo: oferece comandos pequenos e explícitos, ocultando locks, constraints, histórico, auditoria e idempotência em sua implementação.

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

Os callers e os testes atravessam as mesmas interfaces. Colunas sensíveis não são atualizadas diretamente pelo cliente.

### Adapter Google Sheets/n8n

Responsável por:

- ler a planilha;
- normalizar o payload externo;
- fornecer idempotency key e correlation ID;
- chamar o comando de ingestão;
- registrar e reprocessar falhas externas.

O fixture `WTG - Leads.xlsx` registra a planilha mock atual: aba `Leads`, colunas A–Q. Para o vendedor, a projeção de dados originados da planilha é limitada a M–P (`você_tem_cnpj_ou_mei?`, `full_name`, `phone_number` e `email`); Q `lead_status` fica excluída. Campanha, status interno, prazo, tentativas e outros campos operacionais autorizados pelo sistema continuam disponíveis conforme o perfil porque não compõem essa projeção de origem.

A coluna M é somente a resposta a uma pergunta e não contém o número real do CNPJ. Portanto, o mock não satisfaz as regras de identidade, deduplicação e recorrência por CNPJ. O adapter da planilha mock será substituído de forma localizada quando a planilha definitiva for fornecida, sem deslocar essas regras para a integração.

### Adapter de notificações

Responsável por consumir a outbox e entregar mensagens. O provedor real será definido depois. A indisponibilidade de e-mail nunca desfaz uma ação de negócio.

## Fluxo principal de dados

```text
Google Sheets
    ↓ leitura a cada 5 minutos
n8n Cloudfy
    ↓ comando idempotente
Supabase/PostgreSQL
    ↓ transação: validar → deduplicar → distribuir ou deixar pendente
Histórico + auditoria + outbox
    ↓ consultas autorizadas por JWT e RLS
Next.js
    ↓
Administrador ou vendedor
```

## Segurança

- Supabase Auth gerencia credenciais.
- RLS protege todas as tabelas comerciais.
- Vendedores consultam somente seus dados e sua participação histórica permitida.
- O histórico do antigo responsável não inclui ações posteriores do novo responsável.
- Ações administrativas verificam o papel também no servidor.
- Chaves administrativas ficam apenas no servidor/n8n.
- Logs evitam payloads pessoais completos.

## Ambientes

- `development`: Supabase local, Docker e dados sintéticos.
- `staging`: Vercel e Supabase próprios, sem dados pessoais reais.
- `production`: Vercel, Supabase e credenciais oficiais separados.

O n8n hospedado na Cloudfy deve usar credenciais diferentes por ambiente ou conexões explicitamente isoladas.

## Tratamento do legado

O código fora de `gerec_leads/` não integra a nova arquitetura. Ele pode ser consultado somente para compreender identidade visual autorizada. Reutilização de código ou dados exige análise e aprovação próprias.

## Qualidade arquitetural

- Criar seams somente onde existe variação real, como planilha mock/final e provedor de notificações.
- Evitar módulos rasos que apenas repassam chamadas.
- Concentrar regras para obter locality: uma correção na fila deve valer para todos os callers.
- Dependências de tempo, integrações e autenticação devem ser controláveis em testes.
- Toda etapa segue os critérios de saída de `ROADMAP.md`.
