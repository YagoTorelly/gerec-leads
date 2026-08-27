# Design de organização e roadmap do Gerenciador de Leads WTG

- **Data:** 25 de agosto de 2026
- **Estado:** design aprovado; Etapa 1 concluída e Etapa 2 aguardando planejamento
- **Escopo:** organização do projeto e trilha até a entrega do MVP

## Contexto

O repositório contém uma aplicação legada fora de `gerec_leads/`, mas o novo Gerenciador de Leads será construído do zero. O arquivo `SPEC_GERENCIADOR_DE_LEADS_WTG.md` já descreve o produto, as regras canônicas, a arquitetura recomendada e os critérios de aceite.

O problema desta etapa não é implementar funcionalidades. É estabelecer um contexto persistente, uma organização navegável e uma sequência de desenvolvimento que impeça o frontend ou integrações externas de antecederem o núcleo transacional.

## Objetivos

- Confinar o novo produto a `gerec_leads/`.
- Tornar a leitura do SPEC obrigatória para trabalhos futuros.
- Registrar decisões já aprovadas e evitar rediscussões acidentais.
- Adotar uma estrutura que separe responsabilidades sem criar infraestrutura desnecessária.
- Definir gates verificáveis desde o esqueleto até a estabilização em produção.

## Abordagens consideradas

### Workspace modular — escolhida

Organiza Next.js, Supabase, n8n, testes e documentação em diretórios próprios sob `gerec_leads/`.

Vantagens:

- separação clara de responsabilidades;
- desenvolvimento e CI coordenados;
- integrações externas substituíveis por adapters;
- espaço para crescer sem antecipar um backend separado.

### Next.js diretamente na raiz — rejeitada

Reduz configuração inicial, mas mistura aplicação, banco, integrações e ferramentas à medida que o MVP cresce.

### Backend Node separado — rejeitada

Adiciona autenticação, deploy, observabilidade e interfaces operacionais sem benefício proporcional. Também enfraquece a decisão de concentrar transações críticas no PostgreSQL.

## Design aprovado

### Governança

`AGENTS.md` instrui agentes a ler o SPEC, relatar divergências, obter aprovação de plano e usar skills relevantes. `ROADMAP.md` define a trilha e os gates. `docs/DECISOES.md` registra escolhas aprovadas.

### Arquitetura

- Next.js/React/TypeScript oferece a interface e comandos server-side.
- Supabase Auth/PostgreSQL/RLS fornece autenticação, dados, permissões e núcleo transacional.
- n8n Cloudfy lê Google Sheets e entrega notificações.
- Google Sheets é origem somente leitura.
- Não existe backend Node separado no MVP.

### Dados e permissões

- Desenvolvimento começa localmente com Docker e Supabase CLI.
- Cinco usuários iniciais: um administrador e quatro vendedores.
- Senhas são aleatórias e não exigem troca no primeiro login nesta versão.
- Vendedor vê somente dados próprios.
- Após transferência, o vendedor anterior vê apenas seus registros históricos em leitura; não vê ações posteriores do novo responsável.

### Ingestão

- Não haverá migração do legado.
- `WTG - Leads.xlsx` é o fixture da planilha mock atual, com A–Q na aba `Leads`.
- Somente M–P formam a projeção de origem do vendedor; Q fica excluída, e campos operacionais internos autorizados permanecem disponíveis conforme o perfil.
- M é resposta à pergunta `você_tem_cnpj_ou_mei?`, não o número real do CNPJ; o mock ainda não satisfaz identidade, deduplicação ou recorrência por CNPJ.
- A planilha final altera somente o adapter e seus testes.
- Bootstrap importa tudo, mas o administrador libera lotes manualmente.
- Operação normal sincroniza a cada 5 minutos e aciona o motor da fila para leads válidos.

### Frontend

- Só começa depois de banco, RLS, núcleo e backend operacional testados.
- Implementa primeiro a base compartilhada, depois administrador e vendedor.
- Usa identidade visual WTG; materiais legados podem servir apenas como referência visual.
- É exclusivamente desktop, acessível e suportado a partir de 1280 px de largura; tablet e celular ficam fora do escopo funcional.

### Integrações e implantação

- Provedor de e-mail será escolhido na etapa de integrações reais.
- A outbox e seu contrato antecedem o adapter real.
- Development, staging e production são isolados.
- Produção usa Vercel, Supabase remoto e n8n Cloudfy.
- O go-live depende de piloto controlado, backup e recuperação testados.

## Fluxo de erro e recuperação

- Erro do Google Sheets ou n8n não cria atribuições parciais.
- Repetição de importação usa idempotência e não duplica ocorrências.
- Erro de e-mail preserva a ação de negócio e mantém o evento para reprocessamento.
- Falha no motor transacional reverte cursor, crédito, atribuição, histórico e outbox juntos.
- Conflitos de origem e overrides são pendências administrativas, nunca mesclagens silenciosas.

## Estratégia de testes

- TDD para prazo útil, fila, recorrência, duplicidade, permissões e resultados.
- Testes SQL/integrados para locks, rollback, constraints, idempotência e RLS.
- Relógio injetável para fins de semana e feriados.
- Contratos para planilha mock/final e notificações.
- E2E separado por perfil.
- Verificação visual e de acessibilidade em desktop antes do piloto.

## Roadmap aprovado

1. Governança e organização.
2. Esqueleto executável.
3. Modelo de dados, Auth e RLS.
4. Núcleo transacional.
5. Ingestão e operação do backend.
6. Frontend do administrador.
7. Frontend do vendedor.
8. Integrações reais.
9. Hardening e piloto.
10. Produção e estabilização.

Os entregáveis e critérios de saída completos estão em `ROADMAP.md`.

## Dependências deliberadamente adiadas

As definições abaixo não impedem a organização nem o desenvolvimento local até o backend operacional:

- planilha Google definitiva;
- projetos Supabase remotos;
- provedor de e-mail;
- credenciais externas;
- domínio final.

Cada dependência possui uma etapa explícita para ser conectada e validada antes do go-live.

## Critério de sucesso deste design

- Todo trabalho futuro começa pelo SPEC.
- O novo código não se mistura ao legado.
- Cada etapa tem resultado verificável e gate de qualidade.
- O núcleo transacional precede a interface.
- O MVP não é declarado entregue sem critérios de aceite, RLS, concorrência, E2E, recuperação e piloto aprovados.
