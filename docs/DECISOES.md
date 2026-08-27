# Registro de decisões iniciais

As decisões abaixo foram aprovadas na organização inicial do projeto. Mudanças futuras devem registrar motivo, impacto e aprovação.

| ID | Decisão | Motivo e impacto | Estado |
|---|---|---|---|
| DEC-001 | Tudo relacionado ao novo sistema fica dentro de `gerec_leads/`. | Isola o produto do código legado e torna o contexto navegável. | Aprovada |
| DEC-002 | O projeto é greenfield. | As pastas legadas não fornecem arquitetura, código ou dados automaticamente. | Aprovada |
| DEC-003 | O SPEC é a fonte canônica. | Divergências devem ser apresentadas; regras não mudam silenciosamente. | Aprovada |
| DEC-004 | Usar workspace modular. | Separa web, Supabase, integrações, testes e documentação sem criar serviços desnecessários. | Aprovada |
| DEC-005 | Usar Next.js/React/TypeScript e Supabase/PostgreSQL. | Mantém a aplicação web simples e o núcleo crítico transacional. | Aprovada |
| DEC-006 | Começar com Supabase local via Docker. | Permite migrações e testes reproduzíveis antes de conectar projetos remotos. | Aprovada |
| DEC-007 | Google Sheets é a única origem inicial de leads. | Não haverá migração de MongoDB ou Pipedrive. | Aprovada |
| DEC-008 | A planilha atual é mock e a definitiva será fornecida depois. | O contrato ficará isolado em adapter testado para permitir ajuste localizado. | Aprovada |
| DEC-009 | O n8n será hospedado na Cloudfy e configurado em etapa posterior. | Workflows ficam versionados no repositório; regras críticas não ficam no n8n. | Aprovada |
| DEC-010 | Os usuários iniciais são Yago, Renato, Sandra, Jessica e Nelma. | Yago é administrador; os demais são vendedores na ordem canônica da fila. | Aprovada |
| DEC-011 | Contas usam senhas aleatórias sem troca obrigatória inicial. | Simplifica o primeiro MVP; redefinição administrativa permanece disponível. | Aprovada |
| DEC-012 | Vendedor vê somente seus dados. | Após transferência, mantém apenas seus próprios registros históricos em leitura, sem ações posteriores do novo responsável. | Aprovada |
| DEC-013 | O backend e banco precedem o frontend. | A interface não pode antecipar regras críticas ainda não comprovadas. | Aprovada |
| DEC-014 | A interface usa a identidade visual WTG. | Materiais do legado podem ser consultados apenas como referência visual. | Aprovada |
| DEC-015 | O provedor de e-mail será definido depois. | A outbox e a interface de notificação serão construídas antes do adapter real. | Aprovada |
| DEC-016 | Entrega usa development, staging e production isolados. | Reduz risco de dados e credenciais cruzados. | Aprovada |
| DEC-017 | Vercel hospeda o frontend, Supabase remoto hospeda dados e Auth, e Cloudfy hospeda n8n. | Composição alinhada ao SPEC e ao ambiente escolhido. | Aprovada |
| DEC-018 | Cada etapa possui gate de qualidade. | Não há avanço sem testes, evidências e ausência de falhas críticas. | Aprovada |
| DEC-019 | O MVP termina após aceite automatizado e piloto controlado. | Interface pronta isoladamente não comprova o núcleo operacional. | Aprovada |
| DEC-020 | `.github/workflows/gerec-leads-ci.yml` é a única exceção à pasta do produto. | O GitHub Actions exige essa localização; o gatilho fica limitado a `gerec_leads/**` e toda lógica executada continua no workspace. | Aprovada |
| DEC-021 | O workspace usa Node.js 24 LTS. | Mantém um runtime ativo e uniforme entre máquinas locais e CI, declarado em `.nvmrc` e `package.json`. | Aprovada |
| DEC-022 | A interface é exclusivamente desktop, com largura mínima suportada de 1280 px. | Tablet e celular ficam fora do escopo funcional; implementação e testes de interface concentram-se no ambiente operacional aprovado. | Aprovada |
| DEC-023 | `WTG - Leads.xlsx` é o fixture mock A–Q atual; somente M–P formam a projeção de origem do vendedor e a planilha definitiva virá depois. | Q não integra a projeção; M é resposta a uma pergunta, não CNPJ real. O adapter preserva a troca localizada do contrato sem alterar identidade, recorrência ou permissões. | Aprovada |
