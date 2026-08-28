# Registro de decisões iniciais

As decisões abaixo foram aprovadas na organização inicial do projeto. Mudanças futuras devem registrar motivo, impacto e aprovação.

| ID | Decisão | Motivo e impacto | Estado |
|---|---|---|---|
| DEC-001 | Tudo relacionado ao novo sistema fica dentro de `gerec_leads/`. | Isola o produto do código legado e torna o contexto navegável. | Aprovada |
| DEC-002 | O projeto é greenfield. | As pastas legadas não fornecem arquitetura, código ou dados automaticamente. | Aprovada |
| DEC-003 | O SPEC é a fonte canônica. | Divergências devem ser apresentadas; regras não mudam silenciosamente. | Aprovada |
| DEC-004 | Usar workspace modular. | Separa cliente web, API Python, automações, testes e documentação sem criar serviços desnecessários. | Aprovada |
| DEC-005 | A arquitetura inicialmente aprovada usava Next.js/React/TypeScript e Supabase/PostgreSQL. | Registro histórico substituído pela arquitetura MongoDB/Python da DEC-024; não orienta novas implementações. | Substituída pela DEC-024 |
| DEC-006 | A fundação inicial usava Supabase local via Docker. | Registro histórico substituído pelo MongoDB em replica set da DEC-024; os artefatos existentes são legados temporários. | Substituída pela DEC-024 |
| DEC-007 | Google Sheets é a única origem inicial de leads. | O MongoDB novo está vazio; não haverá migração de dados comerciais de outro banco ou do Pipedrive. | Aprovada |
| DEC-008 | A planilha atual é mock e a definitiva será fornecida depois. | O contrato ficará isolado em adapter testado para permitir ajuste localizado. | Aprovada |
| DEC-009 | A arquitetura inicial previa n8n hospedado na Cloudfy. | Registro histórico substituído por automações Python idempotentes na Railway; não orienta novas implementações. | Substituída pela DEC-026 |
| DEC-010 | Os usuários iniciais são Yago, Renato, Sandra, Jessica e Nelma. | Yago é administrador; os demais são vendedores na ordem canônica da fila. | Aprovada |
| DEC-011 | Contas usam senhas aleatórias sem troca obrigatória inicial. | Simplifica o primeiro MVP; redefinição administrativa permanece disponível. | Aprovada |
| DEC-012 | Vendedor vê somente seus dados. | Após transferência, mantém apenas seus próprios registros históricos em leitura, sem ações posteriores do novo responsável. | Aprovada |
| DEC-013 | O backend e banco precedem o frontend. | A interface não pode antecipar regras críticas ainda não comprovadas. | Aprovada |
| DEC-014 | A interface usa a identidade visual WTG. | Materiais do legado podem ser consultados apenas como referência visual. | Aprovada |
| DEC-015 | O provedor de e-mail será definido depois. | A outbox e a interface de notificação serão construídas antes do adapter real. | Aprovada |
| DEC-016 | Entrega usa development, staging e production isolados. | Reduz risco de dados e credenciais cruzados. | Aprovada |
| DEC-017 | A implantação inicial previa Vercel, Supabase remoto e n8n na Cloudfy. | Registro histórico substituído pela separação Vercel/Railway/MongoDB da DEC-026. | Substituída pela DEC-026 |
| DEC-018 | Cada etapa possui gate de qualidade. | Não há avanço sem testes, evidências e ausência de falhas críticas. | Aprovada |
| DEC-019 | O MVP termina após aceite automatizado e piloto controlado. | Interface pronta isoladamente não comprova o núcleo operacional. | Aprovada |
| DEC-020 | `.github/workflows/gerec-leads-ci.yml` é a única exceção à pasta do produto. | O GitHub Actions exige essa localização; o gatilho fica limitado a `gerec_leads/**` e toda lógica executada continua no workspace. | Aprovada |
| DEC-021 | O workspace usa Node.js 24 LTS. | Mantém um runtime ativo e uniforme entre máquinas locais e CI, declarado em `.nvmrc` e `package.json`. | Aprovada |
| DEC-022 | A interface é exclusivamente desktop, com largura mínima suportada de 1280 px. | Tablet e celular ficam fora do escopo funcional; implementação e testes de interface concentram-se no ambiente operacional aprovado. | Aprovada |
| DEC-023 | `WTG - Leads.xlsx` é o fixture mock A–Q atual; somente M–P formam a projeção de origem do vendedor e a planilha definitiva virá depois. | Q não integra a projeção; M é resposta a uma pergunta, não CNPJ real. O adapter preserva a troca localizada do contrato sem alterar identidade, recorrência ou permissões. | Aprovada |
| DEC-024 | MongoDB é a única persistência do sistema novo, no database `gerec_leads`; o backend/API Python concentra autenticação, autorização e regras críticas. | Coleções normalizadas, índices e transações multi-documento preservam os invariantes. Todos os ambientes exigem replica set. O sistema novo não usa Supabase, PostgreSQL, RLS nem `service_role`. | Aprovada em 27/08/2026 |
| DEC-025 | Next.js/React é somente cliente web e nunca acessa MongoDB diretamente. | Toda leitura e comando passam pela API Python autorizada; URI e credenciais do banco permanecem server-side. | Aprovada em 27/08/2026 |
| DEC-026 | Vercel hospeda o cliente Next.js/React; Railway hospeda a API, workers, jobs e agendamentos Python. | As automações usam comandos compartilhados e outbox idempotente, sem manter invariantes do domínio. O sistema novo não usa n8n. | Aprovada em 27/08/2026 |
| DEC-027 | Não haverá migração de dados comerciais nesta mudança arquitetural. | O MongoDB destinado ao produto está vazio. A mudança preserva as regras, métricas e o contrato do fixture; artefatos legados serão retirados em tarefa própria. | Aprovada em 27/08/2026 |
| DEC-028 | A operação comercial usa SLA de 24 horas úteis apenas entre 09:00 e 18:00; `isDisqualified` é marcador adicional que encerra o SLA; administrador tem leitura global, sem editar comentário, status ou responsável da tratativa. | Vendedor atrasado fica Bloqueado por atraso sem redistribuir leads; ganhos e desqualificados são métricas independentes. As contas aprovadas neste ambiente são Yago, André, Renato, Sandra, Jessica e Nelma: Yago e André são administradores; os demais são vendedores. Criação e redefinição aceitam senha não vazia, sem política adicional. Histórico é preservado, e prazos, projeções e métricas são recalculados idempotentemente por migração. | Aprovada em 28/08/2026 |
