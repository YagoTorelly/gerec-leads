# Instruções permanentes do Gerenciador de Leads WTG

Estas instruções valem para todo arquivo dentro de `gerec_leads/`.

## Fonte canônica

1. Antes de analisar, planejar, implementar, corrigir, revisar ou testar o sistema, leia integralmente `SPEC_GERENCIADOR_DE_LEADS_WTG.md`.
2. Trate o SPEC como fonte de verdade funcional e técnica. Código, protótipos, mockups e documentos auxiliares não o substituem.
3. Se o código ou outra documentação divergir do SPEC, apresente a divergência e o impacto antes de continuar.
4. Não altere regra de negócio silenciosamente. Mudanças seguem a governança da seção 39 do SPEC e exigem aprovação de Yago.

## Escopo do novo sistema

- O Gerenciador de Leads é um projeto novo e isolado dentro de `gerec_leads/`.
- Não reutilize código, arquitetura, dados ou integrações das pastas legadas `backend/`, `frontend/` e `ingestao/` sem análise e autorização explícita.
- Os materiais visuais legados da WTG podem ser consultados apenas como referência de identidade visual.
- A interface é exclusivamente desktop, com largura mínima suportada de 1280 px. Tablet e celular estão fora do escopo funcional.
- `WTG - Leads.xlsx` é o fixture mock atual A–Q. Preserve o binário; somente M–P formam a projeção de origem do vendedor, Q fica excluída e M não deve ser interpretada como CNPJ real.
- Todo código, migração, teste, documentação e configuração do novo sistema deve permanecer dentro de `gerec_leads/`.
- A única exceção estrutural aprovada é `.github/workflows/gerec-leads-ci.yml`, porque o GitHub Actions só descobre workflows nessa pasta da raiz. Esse arquivo deve reagir apenas a mudanças em `gerec_leads/**`; toda a lógica e configuração executada por ele permanece em `gerec_leads/`.

## Fluxo obrigatório antes de implementar

Antes de escrever código, apresente e aguarde aprovação de:

1. resumo do entendimento;
2. riscos, dependências e ambiguidades;
3. arquitetura proposta sem contrariar decisões canônicas;
4. plano pequeno, sequencial e verificável.

Também:

- faça perguntas objetivas quando uma regra crítica estiver ambígua;
- mostre o diff proposto antes de mudanças importantes;
- preserve a lógica existente que estiver alinhada ao SPEC;
- não realize refatorações alheias ao objetivo da etapa;
- explique causa provável e impacto ao corrigir bugs;
- considere cenários reais, de borda e de erro;
- sugira e implemente testes proporcionais ao risco.

## Restrições arquiteturais

- Use o workspace modular descrito em `docs/ARQUITETURA.md`.
- Next.js/React não decide sozinho atribuição, cursor, propriedade, venda ou créditos de pulo.
- Regras críticas vivem em comandos transacionais do PostgreSQL/Supabase, protegidos por constraints, locks e testes.
- Não coloque lógica de negócio crítica em controllers, handlers, componentes React ou workflows do n8n.
- O n8n atua como adaptador de Google Sheets, agendas e notificações.
- Google Sheets é somente origem; o sistema nunca escreve na planilha.
- A planilha definitiva continua uma dependência posterior. Mantenha o contrato físico da origem atrás do adapter e não enfraqueça identidade, deduplicação ou recorrência por CNPJ para acomodar o mock.
- Toda mudança de banco usa nova migração versionada. Nunca edite uma migração já aplicada.
- RLS deve proteger os dados no banco; ocultar elementos na interface não é controle de acesso.
- `service_role` e demais segredos nunca podem chegar ao navegador.

## Permissões já aprovadas

- Administrador: visão e operação globais conforme o SPEC.
- Vendedor: somente seus leads, métricas, posição e registros próprios.
- Após transferência, o vendedor anterior mantém somente leitura dos registros produzidos enquanto era responsável; não vê ações posteriores do novo responsável.
- As cinco contas iniciais são Yago, Renato, Sandra, Jessica e Nelma.
- No MVP inicial, as contas recebem senhas aleatórias e não exigem troca no primeiro login. O administrador pode redefini-las.

## Qualidade e testes

- Aplique TDD às regras de distribuição, prazo útil, duplicidade, permissões e resultados finais.
- Testes de tempo usam relógio controlável e nunca dependem do horário real.
- Testes de banco devem cobrir concorrência, rollback, idempotência, constraints e RLS.
- Testes ponta a ponta devem cobrir os fluxos dos dois perfis sem compartilhar dados indevidos.
- Uma etapa só termina com comandos de verificação executados e evidências registradas.
- O MVP só termina quando os critérios de aceite do SPEC, segurança, backup, recuperação e piloto estiverem validados.

## Seleção de skills

Use somente as skills relevantes à tarefa, quando disponíveis:

- descoberta e desenho: `using-superpowers`, `brainstorming`, `product-brainstorming`, `writing-plans`;
- arquitetura e interfaces: `codebase-design`, `vercel-composition-patterns`;
- banco e segurança: `supabase-postgres-best-practices`;
- implementação: `test-driven-development`;
- React/Next.js: `vercel-react-best-practices`;
- interface: `frontend-design`, `ui-ux-pro-max`, `high-end-visual-design` ou `minimalist-ui`, conforme a direção aprovada;
- validação visual e E2E: `agent-browser`, `web-design-guidelines`;
- bugs: `systematic-debugging`;
- encerramento: `verification-before-completion`, `requesting-code-review`.

Não aplique todas as skills indiscriminadamente. A skill escolhida deve ter relação direta com o trabalho atual.

## Documentos de navegação

- Fonte de verdade: `SPEC_GERENCIADOR_DE_LEADS_WTG.md`
- Trilha de entrega: `ROADMAP.md`
- Plano executável da Etapa 1: `docs/superpowers/plans/2026-08-25-etapa-1-esqueleto-executavel.md`
- Organização técnica: `docs/ARQUITETURA.md`
- Decisões aprovadas: `docs/DECISOES.md`
