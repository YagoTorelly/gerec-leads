# Design: cadastro manual, fila alternativa e exportações administrativas

**Data:** 2026-09-22  
**Status:** aprovado em conversa e revisado
**Escopo:** Gerenciador de Leads WTG

## 1. Objetivo

Adicionar ao painel administrativo um fluxo para cadastrar leads manualmente,
distribuí-los em uma fila alternativa independente da fila automática e
exportar os leads atuais em Excel. O sistema também exibirá um histórico das
exportações realizadas, sem incluir esse histórico no arquivo baixado.

## 2. Regras funcionais aprovadas

### 2.1 Cadastro manual

- Somente administradores podem criar leads manuais.
- Campos principais do formulário:
  - nome, obrigatório;
  - e-mail, obrigatório;
  - telefone, obrigatório;
  - situação, sempre iniciada como `Indefinido`;
  - dados de campanha/origem, opcionais.
- O administrador não escolhe o vendedor no formulário.
- Cada lead manual recebe um identificador único em coluna própria,
  `manualQueueLeadId`, gerado pelo backend.
- O identificador manual não reutiliza nem altera `sourceLeadId` ou qualquer
  identificador originado da planilha.
- Quando campanha/origem não forem informadas, o backend usa os dados de
  campanha do lead automático mais recente. Se não existir um lead automático,
  os campos permanecem vazios.
- A criação registra auditoria com administrador, data/hora, payload original
  e identificador gerado.

### 2.2 Fila alternativa

- Leads manuais usam uma fila e um cursor separados da fila automática.
- A ordem dos vendedores é a mesma ordem configurada para a fila principal.
- Avançar o cursor alternativo nunca altera cursor, posição, créditos ou
  atribuições da fila automática.
- Vendedores Pausados ou indisponíveis são pulados; o próximo vendedor Ativo
  elegível recebe o lead.
- A atribuição alternativa registra responsável atual, data de atribuição,
  sequência e auditoria.
- O vendedor responsável enxerga o lead na operação normal e pode registrar
  tratativas com as mesmas regras dos leads automáticos.
- A atribuição manual gera a notificação interna de novos leads já existente.
- Transferências futuras usam as regras vigentes de transferência e não
  reescrevem o cursor da fila automática.

### 2.3 Permissões

- Administrador: cria leads manuais, visualiza ambas as filas, exporta leads e
  consulta o histórico de exportações.
- Vendedor: não cria, exporta ou consulta histórico de exportações; vê e trata
  somente leads que se tornaram seus pela fila alternativa ou automática,
  conforme as regras de escopo existentes.
- O frontend não é fonte de autorização; as regras são impostas pela API e
  pelas operações transacionais do domínio.

## 3. Exportação

### 3.1 Arquivo

- O download será um arquivo Excel `.xlsx`.
- O arquivo contém somente leads, nunca o histórico de tratativas nem o
  histórico de exportações.
- A exportação inicial abrange todos os leads visíveis ao administrador.
- Colunas mínimas:
  - `leadId`;
  - `manualQueueLeadId`, quando existir;
  - nome;
  - responsável atual;
  - telefone;
  - e-mail;
  - campanha/origem;
  - situação comercial;
  - marcador Desqualificado;
  - data de criação;
  - data de atribuição;
  - última atualização;
  - origem `automatico` ou `manual`.
- Datas serão serializadas com timezone operacional
  `America/Sao_Paulo` para não confundir os vendedores.
- Telefones e identificadores serão escritos como texto para preservar `55`,
  zeros à esquerda e a formatação original.

### 3.2 Histórico de exportações

- A guia administrativa terá uma lista somente de leitura das exportações.
- Cada registro contém data/hora, administrador responsável, quantidade de
  leads, filtros aplicados e status.
- A consulta do histórico é exclusiva de administradores.
- O histórico não é anexado ao Excel.
- Falhas de geração devem registrar status de erro sem criar um registro falso
  de sucesso e devem apresentar uma mensagem recuperável na interface.

## 4. Arquitetura proposta

### 4.1 Backend

- Criar um comando transacional de criação de lead manual; controller/rota
  apenas valida entrada e delega ao domínio.
- Persistir `manualQueueLeadId`, origem manual e metadados de auditoria em
  documentos de lead e eventos de atribuição.
- Reutilizar o motor de seleção de vendedor com um `queueKind` explícito,
  mantendo estado/cursor separado para `automatic` e `manual`.
- Criar leitura administrativa para exportação e um gerador `.xlsx` no backend
  ou serviço de aplicação, sem conexão do navegador ao MongoDB.
- Criar coleção ou agregado de histórico de exportação com índices por
  `createdAt` e `actorId`.
- Manter idempotência, constraints, locks e validação de escopo na API.

### 4.2 Web

- Adicionar ação “Adicionar leads” ao shell de administrador.
- Criar formulário com validação de campos obrigatórios e estado inicial
  fixo `Indefinido`.
- Exibir o responsável atribuído depois da criação, sem seletor de vendedor.
- Adicionar guia “Exportações” somente para administrador, com botão de
  download e tabela de histórico.
- Mostrar estados de carregamento, sucesso, erro e retry sem remover o shell.
- Revalidar dashboard, fila e notificações após a criação/atribuição.

### 4.3 Relatórios

- Manter somente os dois gráficos já existentes:
  - distribuição de leads por situação;
  - distribuição de leads por vendedor.
- Usar gráficos de colunas verticais, com rótulo textual e valor numérico
  visível para acessibilidade.
- Cada gráfico ocupa uma linha completa da área de conteúdo, sem dividir os
  dois gráficos lado a lado nem deixar uma coluna vazia.
- Preservar filtros de período e as regras de proprietário atual já aprovadas.

## 5. Concorrência e casos de borda

- Dois administradores criando leads simultaneamente não podem gerar o mesmo
  `manualQueueLeadId` nem atribuir o mesmo lead duas vezes.
- Se todos os vendedores estiverem pausados/indisponíveis, o lead manual fica
  sem atribuição, com estado operacional auditável, até haver elegível.
- Se o último lead automático não tiver campanha, os campos herdados ficam
  vazios; não copiar nome, telefone, e-mail ou identidade do último lead.
- Repetir a confirmação de criação com a mesma chave idempotente não cria
  outro lead.
- Exportação vazia deve gerar um Excel válido com cabeçalho e registrar
  quantidade zero.
- Falhas de armazenamento/geração não devem expor stack trace ou segredos.

## 6. Testes de aceite

### Backend

- autorização: vendedor não cria lead manual nem exporta;
- campos obrigatórios e situação inicial `Indefinido`;
- ID manual único e idempotência;
- herança apenas de campanha/origem do lead automático mais recente;
- cursor alternativo independente do cursor automático;
- salto de vendedores pausados;
- atribuição e notificação do vendedor;
- concorrência e rollback da criação/atribuição;
- exportação Excel com todos os campos e datas em São Paulo;
- histórico de exportação somente para administradores;
- falha de exportação sem registro falso de sucesso.

### Web/E2E

- administrador abre formulário, cria lead e vê confirmação;
- vendedor recebe a notificação e vê/trata o lead;
- fila automática não muda após cadastro manual;
- administrador baixa `.xlsx` e confirma as colunas;
- histórico mostra data, administrador responsável, quantidade e status;
- relatórios mostram os dois gráficos de colunas em linhas completas;
- vendedor não vê a guia nem consegue acessar endpoints;
- estados de loading/erro/retry preservam o shell;
- captura visual em 1440×900 para cadastro e exportações.

## 7. Decisões e limites

- Não haverá e-mail nesta funcionalidade; a notificação é a janela interna já
  aprovada.
- Não haverá escolha manual de responsável no cadastro.
- Não haverá download de tratativas ou do histórico de exportações.
- A fila alternativa não altera a FIFO automática.
- A primeira implementação não inclui filtros adicionais de exportação; o
  escopo inicial é exportar todos os leads administrativos.
