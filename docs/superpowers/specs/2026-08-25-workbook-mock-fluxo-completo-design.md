# Workbook mock e fluxo operacional completo — desenho aprovado

- **Data:** 25 de agosto de 2026
- **Status:** aprovado por Yago para planejamento
- **Fonte funcional:** `SPEC_GERENCIADOR_DE_LEADS_WTG.md`
- **Estratégia de entrega:** backend por camadas, seguido pelos frontends administrativo e do vendedor

## 1. Objetivo

Transformar o esqueleto local da Etapa 1 em um fluxo operacional completo e demonstrável, usando o arquivo `WTG - Leads.xlsx` como fonte real de desenvolvimento. O sistema deverá importar o workbook sem modificá-lo, registrar e corrigir pendências, aprovar campanhas, liberar o bootstrap em lotes, distribuir leads pela fila transacional e permitir que cada vendedor acompanhe e finalize somente os próprios leads.

Esta entrega abrange as Etapas 2 a 6 do roadmap, respeitando os gates entre elas. A interface só será construída sobre comandos de backend já testados.

## 2. Decisões preservadas

- O SPEC continua sendo a fonte canônica.
- Todo o sistema permanece dentro de `gerec_leads/`, exceto a exceção de CI já aprovada.
- O PostgreSQL/Supabase decide fila, cursor, elegibilidade, propriedade, créditos, prazos e resultados.
- Next.js não atualiza diretamente colunas críticas.
- O workbook é somente leitura; nenhuma ação do sistema escreve nele.
- `WTG - Leads.xlsx` continua sendo um mock provisório da aba `Leads`, com colunas A–Q.
- A projeção de dados de origem do vendedor permanece limitada a M–P.
- A coluna M é uma resposta à pergunta sobre possuir CNPJ/MEI, não um documento real.
- A planilha Google definitiva e o n8n permanecem para a etapa de integrações reais.
- A aplicação é exclusivamente desktop, com largura mínima de 1280 px.

## 3. Escopo funcional

### 3.1 Incluído

- Supabase Auth local com as cinco contas iniciais.
- Perfis `admin` e `seller` e isolamento por RLS.
- Modelo comercial, fila, calendário útil, SLA, auditoria e outbox.
- Botão administrativo para reler o workbook fixo.
- Importação completa, idempotente e observável.
- Pendências para os dados que o mock não fornece.
- Correção administrativa de CPF/CNPJ e Estado.
- Detecção e aprovação de campanhas.
- Liberação manual do bootstrap por lote.
- Distribuição global Renato → Sandra → Jessica → Nelma.
- Bloqueio por feedback vencido e créditos compensatórios.
- Feedback, tentativas, qualificação, desqualificação, encerramento sem conversão e ganho.
- Frontend funcional do administrador e do vendedor.
- Testes de banco, RLS, concorrência, contrato, componentes e E2E.

### 3.2 Não incluído

- Google Sheets e credenciais oficiais.
- Workflows ativos do n8n Cloudfy.
- Entrega real de e-mails.
- Supabase remoto, Vercel, staging ou produção.
- WhatsApp corporativo ou envio automático de mensagens.
- Alteração do workbook pelo sistema.
- Interface para tablet ou celular.
- Aplicação do mockup visual definitivo, que ainda será fornecido.

## 4. Arquitetura

### 4.1 PostgreSQL/Supabase

É a fonte de verdade e oferece comandos transacionais explícitos. Encapsula normalização crítica, idempotência, locks, constraints, histórico, auditoria, outbox e autorização.

### 4.2 Next.js

Oferece autenticação, páginas, consultas server-side e ações autorizadas. Os componentes React coletam intenção e exibem resultados; não escolhem vendedor, não calculam o cursor e não encerram estados diretamente.

### 4.3 Adapter do workbook mock

É um módulo server-only que implementa uma interface de fonte de leads. Ele:

1. abre `WTG - Leads.xlsx` sem permissão de escrita;
2. exige a aba `Leads`;
3. valida os 17 headers A–Q, na ordem canônica;
4. converte cada linha para o contrato interno versionado;
5. calcula o hash da linha normalizada;
6. entrega lotes ao comando de ingestão;
7. finaliza o snapshot somente após leitura completa.

O futuro adapter Google Sheets produzirá o mesmo contrato interno. A troca não alcançará o motor de fila nem o frontend.

## 5. Modelo de dados

### 5.1 Identidade e fila

- `profiles`: perfil associado a `auth.users`, papel e estado ativo.
- `seller_queue`: ordem administrativa e pausa de cada vendedor.
- `queue_state`: próximo vendedor do cursor global e versão.
- `seller_skip_balances`: saldo não negativo de créditos compensatórios.

### 5.2 Origem e importação

- `import_runs`: execução, modo, correlation ID, contagens, duração e resultado.
- `lead_source_records`: ID estável da origem, dados normalizados, payload controlado, hash, presença e vínculo opcional com um lead.
- `source_data_issues`: campos ausentes ou inválidos que impedem resolução e distribuição.
- `source_corrections`: valores administrativos fornecidos antes da resolução comercial, com autor e data.

`lead_source_records.lead_id` pode permanecer vazio enquanto documento ou Estado estiverem pendentes. O sistema não criará empresa fictícia nem interpretará M como CNPJ.

### 5.3 Operação comercial

- `campaigns`: identidade externa, nome de origem, nome de exibição e aprovação.
- `companies`: documento normalizado, nome, Estado, proprietário e data de cliente.
- `leads`: ocorrência comercial consolidada por empresa e campanha, com eixos de estado separados.
- `assignments`: histórico de responsáveis e tipo de atribuição.
- `feedback_cycles`: ciclos de SLA com início, lembrete, vencimento e encerramento.
- `feedbacks`: comentários operacionais imutáveis.
- `contact_attempts`: tentativas contabilizadas por dia útil.
- `qualification_events`: decisões e reversões de qualificação.
- `sales`: uma venda ativa por lead e vendedor creditado.
- `business_holidays`: calendário configurável nacional e estadual de São Paulo.

### 5.4 Rastreabilidade

- `field_overrides` e `source_conflicts`: precedência administrativa e conflitos posteriores.
- `notification_outbox`: eventos externos idempotentes.
- `notification_incidents`: controle do limiar de leads parados.
- `audit_log`: ação, ator, entidade, antes/depois, instante e correlation ID.

### 5.5 Integridade e desempenho

- Chaves internas usam `bigint identity`; IDs externos permanecem separados.
- Instantes usam `timestamptz`; valores monetários usam `numeric`.
- Identificadores SQL usam `snake_case` em minúsculas.
- Chaves estrangeiras e colunas de RLS ou filtros frequentes recebem índices.
- Constraints impedem atribuição atual duplicada, venda ativa duplicada, saldo negativo, posição repetida, tentativa contabilizada duas vezes no mesmo dia e categorias inválidas.
- Registros históricos não são apagados por operações comuns.

## 6. Auth, credenciais locais e RLS

Um bootstrap local cria Yago como administrador e Renato, Sandra, Jessica e Nelma como vendedores. As senhas são aleatórias, sem troca obrigatória no primeiro login, e ficam somente em arquivo local ignorado pelo Git.

As políticas devem provar que:

- administrador possui o escopo operacional global aprovado;
- vendedor consulta somente o lead atualmente atribuído a ele;
- vendedor vê somente sua posição, elegibilidade e saldo na fila;
- vendedor insere feedback, tentativa ou resultado apenas quando é o responsável atual;
- antigo responsável vê apenas sua atribuição e os registros produzidos enquanto era responsável;
- antigo responsável não vê ações posteriores do novo responsável;
- a projeção de origem disponível ao vendedor contém apenas M–P;
- chamadas diretas ao banco não ampliam o acesso fornecido pela interface.

Funções privilegiadas terão `search_path` explícito, validação interna de `auth.uid()` e papel, além de `EXECUTE` concedido somente aos papéis necessários. O navegador nunca receberá `service_role`.

## 7. Fluxo de importação

1. O administrador aciona **Sincronizar workbook**.
2. Uma execução recebe `sync_run_id`, idempotency key e correlation ID.
3. O adapter valida o contrato antes de iniciar gravações definitivas.
4. Linhas são enviadas em lotes para `upsert` atômico por ID de origem.
5. Hash idêntico produz resultado `ignored` e nenhum evento novo.
6. Linhas sem documento real ou Estado ficam em pendência.
7. Campanhas desconhecidas são criadas com aprovação pendente.
8. O snapshot só é finalizado quando todas as páginas e linhas forem processadas.
9. Apenas a finalização bem-sucedida pode arquivar IDs ausentes da origem.
10. A resposta apresenta contagens e resultados por linha sem expor payload pessoal integral em logs.

Falha estrutural de aba ou headers bloqueia toda a sincronização. Falha localizada de uma linha é registrada nessa linha e não é escondida pelas demais.

## 8. Correção, aprovação e bootstrap

O administrador complementa documento e Estado em uma pendência. O backend normaliza os valores, valida CPF/CNPJ e UF e então resolve campanha, empresa, duplicidade e ocorrência comercial.

Campanhas desconhecidas permanecem pendentes até aprovação administrativa. Aprovar uma campanha preserva a data original de entrada dos seus registros.

O primeiro snapshot é um bootstrap completo e não distribui automaticamente o histórico. O administrador informa a quantidade a liberar; o comando seleciona os elegíveis por data de entrada e ID de origem. Registros ainda pendentes não entram no lote.

Após o bootstrap, novas ocorrências elegíveis seguem a operação normal. Como o mock não fornece documento e Estado, elas só poderão chegar à fila depois da correção administrativa.

## 9. Motor transacional da fila

O distribuidor usa um lock transacional exclusivo para a fila global. A transação inclui avaliação de elegibilidade, consumo de créditos, avanço do cursor, atribuição, SLA, histórico, auditoria e outbox.

Regras preservadas:

- ordem inicial Renato → Sandra → Jessica → Nelma;
- um atraso é suficiente para bloquear novas entregas normais;
- vendedor inativo ou pausado perde a vez;
- a vez perdida não é recuperada;
- regularização não concede lead imediato;
- crédito compensatório consome uma futura vez natural;
- recorrência não movimenta o cursor;
- proprietário bloqueado faz a recorrência aguardar;
- ausência total de elegibilidade mantém o lead parado em FIFO;
- repetição da mesma idempotency key retorna o resultado anterior.

Locks são adquiridos em ordem consistente e mantidos somente durante a transação de banco. Nenhuma leitura de arquivo ou chamada externa ocorre enquanto o lock estiver ativo.

## 10. SLA, feedback e tentativas

- O prazo inicial é de 24 horas úteis após a atribuição.
- O lembrete ocorre 4 horas úteis antes.
- Fuso: `America/Sao_Paulo`.
- Sábados, domingos e feriados nacionais ou estaduais de São Paulo configurados não contam.
- Não existe janela comercial diária.
- Testes usam relógio controlável; comandos públicos usam o relógio do banco.
- Feedback exige responsável atual, contato iniciado e comentário com seis caracteres úteis.
- Cada feedback válido fecha o ciclo atual e abre outro enquanto o lead estiver ativo.
- Nota administrativa não altera o SLA.
- Tentativa de WhatsApp conta no máximo uma vez por dia útil.
- A quinta tentativa apenas habilita a desqualificação manual pelo motivo canônico.

## 11. Resultados

O comando de resultado aceita:

- `qualified_follow_up`;
- `qualified_closed_no_conversion`;
- `disqualified`;
- `won`.

Todos exigem comentário, autor, instante, auditoria e idempotency key. `disqualified` aceita somente os três motivos do SPEC e verifica suas pré-condições. `won` cria uma única venda, transforma a empresa em cliente, credita o responsável atual e não muda automaticamente o proprietário. Resultados terminais encerram o SLA. Apenas o administrador pode revertê-los.

## 12. Outbox

A transação comercial grava eventos reais em `notification_outbox`. No ambiente local, eles permanecem consultáveis como pendentes ou processados por um adapter de teste, sem afirmar que um e-mail externo foi entregue.

Falhas ou repetições da outbox não desfazem importação, atribuição, feedback ou resultado.

## 13. Frontend administrativo

- Login real com Supabase Auth.
- Dashboard com importações, pendências, distribuídos, parados e atrasos.
- Botão **Sincronizar workbook** e relatório da execução.
- Central de pendências para documento e Estado.
- Aprovação de campanhas.
- Liberação do bootstrap por quantidade.
- Fila com ordem, cursor, elegibilidade, pausas, atrasos e créditos.
- Lista e detalhe dos leads com filtros no servidor.
- Histórico, auditoria e estado da outbox.

Ações críticas exigem confirmação e apresentam o resultado retornado pelo comando de banco.

## 14. Frontend do vendedor

- Dashboard exclusivamente individual.
- Leads ativos, próximos do vencimento e atrasados.
- Posição, elegibilidade e créditos próprios.
- Detalhe do lead com M–P e campos operacionais autorizados.
- Link para WhatsApp sem contabilizar tentativa automaticamente.
- Registro explícito de feedback e tentativa.
- Ações de qualificar, desqualificar, encerrar sem conversão e ganhar.
- Histórico permitido pela RLS, sem dados dos colegas.

## 15. Direção visual e acessibilidade

A interface usa um shell desktop compartilhado e componentes separados por responsabilidade. A identidade WTG será codificada em tokens de cor, tipografia, espaçamento, borda e estados, permitindo aplicar o mockup definitivo posteriormente sem alterar o domínio.

Todos os estados possuem texto, foco visível e contraste adequado. A implementação e os testes consideram largura mínima de 1280 px e viewport de referência 1440 × 900. Tablet e celular não recebem comportamento funcional próprio.

## 16. Erros e bordas

- Aba ou headers inválidos: nenhuma importação ou remoção é confirmada.
- Snapshot incompleto: nenhum registro ausente é arquivado.
- Linha inválida: resultado localizado e pendência ou erro auditável.
- Duplo clique ou retry: mesma idempotency key, mesmo resultado.
- Concorrência: resultado equivalente à execução sequencial.
- Falha no meio da fila: cursor, atribuição, SLA e histórico sofrem rollback juntos.
- Sessão expirada: retorno ao login sem revelar dados protegidos.
- Comando proibido: rejeição no banco mesmo por chamada direta.
- Entrada inválida: estado anterior preservado.
- Falha externa: ação de negócio permanece confirmada e a outbox permite reprocessamento.

## 17. Estratégia de testes

### Gate 1 — Dados, Auth e RLS

- migrações e seed reproduzíveis;
- cinco contas e ordem inicial;
- constraints e índices;
- administrador global;
- vendedor isolado;
- histórico limitado após transferência;
- ausência de acesso cruzado por API direta.

### Gate 2 — Núcleo transacional

- calendário e relógio controlável;
- AC-01 a AC-11, AC-18 a AC-21, AC-24, AC-28 a AC-30;
- concorrência, deadlock, rollback e idempotência;
- fila parada, créditos e recorrência.

### Gate 3 — Ingestão e operação

- contrato exato A–Q e projeção M–P;
- M nunca interpretada como documento;
- linha nova, idêntica, alterada, movida e removida;
- snapshot parcial não arquiva;
- pendência, correção, campanha e bootstrap;
- feedbacks, resultados, outbox, overrides e conflitos.

### Gate 4 — Frontend administrativo

- componentes e ações administrativas;
- estados de carregamento, vazio, erro e confirmação;
- fluxo importar → corrigir → aprovar → liberar;
- acessibilidade e viewport desktop.

### Gate 5 — Frontend do vendedor

- visualização exclusivamente individual;
- projeção M–P;
- feedback, tentativa e cada resultado;
- nenhuma informação dos colegas.

### Gate 6 — Verificação final

- fluxo E2E completo dos dois perfis;
- build, lint, tipos e testes;
- auditoria de RLS e segredos;
- validação visual em 1440 × 900;
- revisão de código e evidência registrada.

## 18. Critérios de conclusão

A entrega termina somente quando:

1. o botão relê o workbook real e registra uma execução observável;
2. uma linha do mock entra em pendência sem ser falsamente distribuída;
3. o administrador complementa os dados e aprova a campanha;
4. a liberação em lote distribui o lead por comando transacional;
5. o vendedor correto visualiza e acompanha o lead;
6. outro vendedor não consegue acessar esse lead diretamente;
7. feedback, tentativa e resultado alteram o domínio conforme o SPEC;
8. retries e concorrência não duplicam importações, atribuições ou vendas;
9. histórico, auditoria e outbox permanecem reproduzíveis;
10. todos os gates de teste e revisão passam.

## 19. Dependências posteriores

Não bloqueiam esta entrega local:

- planilha Google definitiva e nome da aba;
- credencial Google Sheets;
- n8n Cloudfy;
- provedor real de e-mail;
- Supabase remoto;
- domínio e Vercel;
- calendário oficial usado no go-live;
- mockup visual definitivo.

