# Contexto Mestre - Gerenciador de Leads WTG

> Gerado em 2026-09-22 14:07:19 UTC por `scripts/generate-master-context.ps1`.

## Como usar este documento

Este é um pacote de contexto autocontido para desenvolvimento e revisão. Ele consolida fontes documentais e um retrato do código relevante; não substitui os arquivos de origem.

### Hierarquia de autoridade

1. `SPEC_GERENCIADOR_DE_LEADS_WTG.md` é a regra funcional canônica.
2. Decisões de governança aprovadas por Yago alteram explicitamente o SPEC.
3. `AGENTS.md` contém regras permanentes para o trabalho no repositório.
4. Desenhos, planos, evidências e relatórios explicam contexto, histórico e execução; divergências devem ser apontadas antes de qualquer implementação.
5. O código e as configurações são um retrato técnico do branch que gerou este arquivo e nunca substituem uma regra de negócio canônica.

### Escopo incluído

- documentação Markdown rastreada do projeto;
- configurações de build e deploy sem segredos;
- código Python da API e automações;
- código TypeScript/TSX/CSS do frontend, incluindo testes próximos ao código.

Arquivos de ambiente, credenciais, dumps, planilhas e dependências geradas são excluídos por segurança e para evitar contexto inútil.

## Fonte canônica: `SPEC_GERENCIADOR_DE_LEADS_WTG.md`

# Gerenciador de Leads WTG

## Especificação Funcional e Técnica — v1.0

**Data:** 25 de agosto de 2026
**Status:** especificação consolidada para revisão
**Produto:** sistema interno de distribuição, acompanhamento, qualificação e conversão de leads da WTG Corretora de Seguros
**Fonte de verdade:** este documento substitui protótipos, trechos de código e interpretações anteriores sobre este projeto. Se uma implementação divergir desta especificação, a especificação prevalece até que uma alteração seja formalmente aprovada.

---

## 1. Como usar esta especificação com outra inteligência artificial

A IA responsável pelo desenvolvimento deve:

1. Ler este documento integralmente antes de propor código ou estrutura de pastas.
2. Não alterar silenciosamente nenhuma regra de negócio.
3. Identificar contradições entre o código existente e esta especificação antes de continuar.
4. Produzir um plano de implementação dividido em etapas pequenas e verificáveis.
5. Implementar primeiro o núcleo transacional e seus testes; a interface não deve anteceder as regras críticas de fila.
6. Versionar toda alteração de schema, índices ou validações do MongoDB.
7. Aplicar TDD nas regras de distribuição, prazo útil, duplicidade, permissões e resultados finais.
8. Manter a lógica crítica de rodízio no backend/API Python, nunca em jobs de automação.
9. Não expor credenciais administrativas ou de banco no navegador.
10. Considerar concluído somente o que tiver critérios de aceite automatizados e evidência de validação.

### Prompt curto de inicialização para a IA desenvolvedora

> Leia integralmente `SPEC_GERENCIADOR_DE_LEADS_WTG.md`. Trate-o como fonte de verdade. Antes de programar, devolva: (1) resumo do entendimento; (2) riscos e dependências; (3) arquitetura proposta sem contrariar as decisões registradas; (4) plano de implementação testável. Não implemente antes da aprovação desse plano. Toda mudança de regra deve ser apresentada como proposta, nunca aplicada silenciosamente.

---

## 2. Resumo executivo

A WTG recebe leads em uma planilha Google alimentada por anúncios e outras fontes comerciais. O sistema deverá sincronizar essa planilha, organizar os leads por campanha e distribuí-los entre quatro vendedores por meio de uma única fila global:

1. Renato
2. Sandra
3. Jessica
4. Nelma

A distribuição não é apenas um rodízio simples. Um vendedor com qualquer feedback vencido fica temporariamente bloqueado para novas entregas e perde as suas próximas vezes naturais enquanto permanecer irregular. O sistema também precisa preservar o proprietário de uma empresa quando o mesmo CNPJ reaparecer em outra campanha, compensando futuramente quem recebeu entregas direcionadas fora do rodízio.

Depois da entrega, o vendedor registra contatos, tentativas e feedbacks periódicos. O sistema separa três conceitos que não podem ser confundidos:

- contato e acompanhamento;
- qualificação do lead;
- conversão em negócio ganho.

Não converter uma venda não desqualifica o lead. A desqualificação é reservada a critérios objetivos definidos pela WTG.

O MVP terá interface exclusivamente desktop, autenticação por e-mail e senha, dashboards por perfil, campanhas, fila, pendências, histórico, exportações e notificações por e-mail. A integração de um chatbot e de uma caixa corporativa compartilhada do WhatsApp será uma fase posterior.

---

## 3. Problema que o produto resolve

O processo atual depende de uma planilha e de acompanhamento humano para responder perguntas operacionais críticas:

- Quem deve receber o próximo lead?
- Um vendedor está apto a receber ou está atrasado?
- Um lead está parado por falta de vendedor, campanha não aprovada ou dado incompleto?
- O mesmo CNPJ já possui um proprietário na WTG?
- O vendedor entrou em contato e manteve o acompanhamento atualizado?
- O lead foi realmente desqualificado ou apenas não converteu?
- Qual campanha produz mais leads qualificados?
- Quem deve receber crédito por uma venda quando houve direcionamento temporário?

Sem uma fonte operacional única, o rodízio pode se tornar injusto, leads podem ficar esquecidos e indicadores de qualificação podem ser distorcidos.

---

## 4. Objetivos do MVP

### 4.1 Objetivos de negócio

- Distribuir leads com ordem, justiça e rastreabilidade.
- Impedir novas entregas a vendedores que não mantêm feedbacks em dia.
- Preservar o relacionamento de empresas recorrentes com o mesmo proprietário.
- Diferenciar claramente lead qualificado, desqualificado, sem conversão e convertido.
- Permitir que o administrador identifique rapidamente tudo que está parado.
- Medir a qualidade dos leads e das campanhas sem confundir qualificação com venda.
- Reduzir acompanhamento manual, mensagens dispersas e decisões baseadas em memória.

### 4.2 Objetivos técnicos

- Garantir distribuição exatamente uma vez, mesmo com sincronizações ou requisições simultâneas.
- Tornar importações idempotentes.
- Preservar histórico completo de alterações, atribuições e resultados.
- Aplicar isolamento por perfil no backend/API e em toda consulta ao banco, não apenas na interface.
- Manter integrações externas desacopladas do núcleo de negócio.
- Permitir evolução posterior para WhatsApp corporativo sem refazer a modelagem principal.

### 4.3 Indicadores de sucesso do produto

- Nenhum lead apto é atribuído duas vezes por concorrência.
- Nenhum vendedor bloqueado recebe lead normal pelo rodízio.
- Todo lead atribuído possui proprietário atual, data de atribuição e prazo calculado.
- Todo resultado final possui autor, comentário e data.
- Toda mudança de fila ou proprietário feita pelo administrador é auditável.
- A taxa de qualificação por campanha pode ser reproduzida a partir dos dados brutos.
- As telas de vendedor nunca revelam indicadores ou leads de outros vendedores.

---

## 5. Escopo

### 5.1 Incluído no MVP

- Login por e-mail e senha.
- Perfis de administrador e vendedor.
- Sincronização Google Sheets → sistema a cada 5 minutos.
- Importação inicial completa e operação incremental posterior.
- Cadastro e aprovação de campanhas.
- Fila global de distribuição.
- Bloqueio por feedback atrasado.
- Fila FIFO de leads parados.
- Propriedade de empresa por CNPJ.
- Direcionamento recorrente entre campanhas.
- Créditos de pulos compensatórios.
- Direcionamento temporário e transferência permanente pelo administrador.
- Feedback periódico com comentário mínimo.
- Registro de tentativas de contato pelo WhatsApp.
- Qualificação, desqualificação, encerramento sem conversão e negócio ganho.
- Dashboards por campanha e por perfil.
- Central de pendências.
- Notificações e relatórios por e-mail.
- Exportação CSV/XLSX pelo administrador.
- Auditoria das ações críticas.
- Arquivamento de linhas removidas da origem.

### 5.2 Fora do MVP

- Chatbot de WhatsApp.
- Caixa de entrada compartilhada do WhatsApp.
- Envio automático de mensagens de WhatsApp.
- Escrita ou correção automática na planilha Google.
- Aplicativo móvel nativo.
- Transferência de leads realizada por vendedores.
- Filas diferentes por campanha.
- Campanhas restritas a subconjuntos de vendedores.
- Cadastro público de usuários.
- Previsão de vendas por inteligência artificial.
- Pontuação automática de leads.
- Integração com CRM financeiro, emissão de apólices ou comissionamento.

### 5.3 Fase futura: WhatsApp corporativo

A fase posterior deverá usar um único número corporativo compartilhado. O chatbot fará atendimento inicial e, quando necessário, entregará a conversa a uma pessoa real. A propriedade da conversa deverá respeitar o vendedor atualmente responsável pelo lead. O módulo futuro deverá ser integrado por uma interface de provedor, sem acoplar o domínio a uma ferramenta específica.

---

## 6. Abordagens arquiteturais avaliadas

### 6.1 Opção aprovada — backend Python transacional com MongoDB

**Composição:** Next.js/React + TypeScript como cliente web hospedado na Vercel; backend/API e automações em Python hospedados na Railway; MongoDB como única fonte de persistência.

**Vantagens:**

- A atribuição ocorre em transação do MongoDB.
- Regras de concorrência usam transações, escritas condicionais, índices únicos e controle de versão.
- O histórico e a auditoria permanecem próximos dos dados.
- O backend Python aplica autorização por perfil em todos os comandos e consultas.
- Jobs podem falhar ou repetir um evento sem duplicar atribuições, pois outbox e comandos são idempotentes.

**Desvantagem:** transações do MongoDB exigem replica set em todos os ambientes e testes explícitos de concorrência, autorização e recuperação.

**Decisão:** adotar esta abordagem.

### 6.2 Alternativa rejeitada — regra de fila em automações externas

Seria mais rápida para uma demonstração, mas exporia a operação a condições de corrida, execuções duplicadas, dificuldade de reprocessamento e baixa testabilidade. As automações serão jobs Python na Railway e atuarão somente como adaptadores idempotentes; não controlarão regras de negócio.

### 6.3 Alternativa rejeitada — acesso do cliente web ao banco

Conectar o Next.js/React diretamente ao MongoDB reduziria a separação de responsabilidades e permitiria contornar autorização e invariantes do domínio. O cliente web acessará somente a API Python.

### 6.4 Tecnologias removidas da arquitetura nova

O sistema novo não usará Supabase, PostgreSQL, RLS, `service_role` nem n8n. Artefatos legados dessas tecnologias podem permanecer temporariamente no repositório até uma tarefa própria de remoção, mas não são fonte de verdade nem destino de novas implementações.

---

## 7. Arquitetura recomendada

```mermaid
flowchart TD
    A["Google Sheets"] -->|"leitura a cada 5 min"| B["Job Python de ingestão — Railway"]
    B -->|"comando idempotente"| C["Backend/API Python — Railway"]
    C --> D["MongoDB — banco gerec_leads"]
    C --> E["Motor transacional de fila"]
    E --> D
    D --> F["Outbox de eventos"]
    F --> G["Workers Python de notificações — Railway"]
    H["Next.js / React — Vercel"] -->|"HTTPS; sem acesso direto ao banco"| C
    I["Administrador e vendedores"] --> H
```

### 7.1 Responsabilidades por componente

| Componente | Responsabilidade | Não deve fazer |
|---|---|---|
| Next.js/React na Vercel | Cliente web, apresentação e validação de experiência | Acessar MongoDB ou decidir regras críticas |
| Backend/API Python na Railway | Autenticação, autorização, comandos, consultas e regras críticas | Delegar invariantes ao cliente ou aos jobs |
| MongoDB (`gerec_leads`) | Única fonte de persistência para estados, histórico, auditoria e outbox | Ser acessado diretamente pelo cliente web |
| Jobs Python na Railway | Ler a planilha, normalizar payload, consumir outbox e chamar comandos idempotentes | Manter cursor de fila, escolher vendedor ou alterar resultado por conta própria |
| Google Sheets | Entrada de dados da operação | Receber atualizações do sistema |
| Vercel | Hospedagem do cliente Next.js/React | Hospedar o núcleo Python ou armazenar segredos no cliente |

O MongoDB usa o banco `gerec_leads`, com coleções normalizadas por agregado e referência explícita entre entidades. Índices únicos, validações de schema e transações multi-documento protegem os invariantes; essas transações só são suportadas sobre replica set, obrigatório em desenvolvimento, staging e produção.

### 7.2 Princípio estrutural

As ações críticas deverão ser comandos explícitos do domínio implementados em Python. Não se deve permitir que o frontend atualize diretamente campos sensíveis como `assignee_id`, `queue_cursor`, `won_by` ou `remaining_skips`, nem que possua credencial ou conexão com MongoDB.

---

## 8. Usuários iniciais

| Pessoa | E-mail | Perfil | Posição inicial |
|---|---|---|---:|
| Yago | yago@wtgseguros.com.br | Administrador | — |
| Renato | renato@wtgseguros.com.br | Vendedor | 1 |
| Sandra | sandracristina@wtgseguros.com.br | Vendedor | 2 |
| Jessica | jessicaalmeida@wtgseguros.com.br | Vendedor | 3 |
| Nelma | nelmacastro@wtgseguros.com.br | Vendedor | 4 |

### 8.1 Autenticação

- Login por e-mail e senha.
- Contas criadas somente pelo administrador ou por processo interno de convite.
- Não haverá cadastro público.
- Recuperação de senha será enviada ao e-mail do usuário.
- Ao desativar um usuário, suas sessões deverão ser revogadas e ele deixará de participar da fila.
- A desativação não apagará atribuições, feedbacks ou vendas históricas.

---

## 9. Papéis e permissões

### 9.1 Matriz de acesso

| Recurso/ação | Administrador | Vendedor |
|---|---:|---:|
| Ver todos os leads | Sim | Não |
| Ver leads próprios | Sim | Sim |
| Ver métricas globais | Sim | Não |
| Ver métricas próprias | Sim | Sim |
| Ver posição de todos na fila | Sim | Não |
| Ver a própria posição | Sim | Sim |
| Reordenar fila | Sim | Não |
| Pausar/reativar vendedor | Sim | Não |
| Aprovar campanha | Sim | Não |
| Editar campos vindos da planilha | Sim, com override auditado | Não |
| Registrar feedback em lead | Nota administrativa separada | Sim, se for responsável atual |
| Qualificar/desqualificar | Pode corrigir e reverter | Sim, no próprio lead |
| Marcar negócio ganho | Sim | Sim, no próprio lead |
| Reverter desqualificação | Sim | Não |
| Reverter negócio ganho | Sim | Não |
| Direcionar temporariamente | Sim | Não |
| Transferir propriedade permanentemente | Sim | Não |
| Exportar todos os dados | Sim | Não |
| Ver auditoria | Sim | Não |

### 9.2 Restrições adicionais do vendedor

- Não pode transferir leads.
- Não pode alterar a ordem da fila.
- Não pode ver nomes, atrasos, posições ou indicadores dos outros vendedores.
- Não pode editar CNPJ, empresa, telefone, e-mail, campanha ou campos de origem.
- Não pode registrar feedback em lead que não esteja atualmente atribuído a ele.
- Não pode reabrir um resultado final.

### 9.3 Notas administrativas

O administrador pode acrescentar uma nota administrativa, mas essa nota não conta como feedback do vendedor, não renova o SLA e não desbloqueia o vendedor. Isso impede regularização artificial do acompanhamento.

### 9.4 Transferência manual de propriedade do lead

- Somente o administrador pode transferir manualmente a propriedade de um lead.
- A transferência altera o responsável atual e não altera o cursor, a ordem da fila ou créditos de pulo.
- Após a transferência, o vendedor anterior perde totalmente o acesso ao lead e às tratativas relacionadas, inclusive em leitura.
- O histórico permanece preservado para auditoria administrativa e para o novo responsável conforme suas permissões.

---

## 10. Glossário canônico

| Termo | Definição |
|---|---|
| Empresa | Entidade comercial identificada prioritariamente por CNPJ |
| Lead | Ocorrência comercial de uma empresa/contato dentro de uma campanha |
| Campanha | Origem comercial agrupadora dos leads |
| Anúncio | Peça/origem específica dentro de uma campanha; seu ID não é tratado como único por lead |
| Proprietário da empresa | Vendedor que recebeu a primeira atribuição válida daquele CNPJ, salvo transferência permanente |
| Responsável atual | Vendedor que deve atender o lead neste momento |
| Responsável temporário | Vendedor escolhido pelo administrador sem mudar o proprietário da empresa |
| Turno natural | Vez de um vendedor na ordem global do rodízio |
| Crédito de pulo | Débito de equidade que faz o vendedor perder uma futura vez natural por ter recebido lead direcionado |
| Feedback válido | Comentário operacional do responsável atual, após contato iniciado, com ao menos 6 caracteres úteis |
| Tentativa | Registro manual de contato pelo WhatsApp em um dia útil distinto |
| Qualificado | Lead que deu uma devolutiva real após contato, positiva ou negativa |
| Desqualificado | Lead que atende um dos critérios objetivos de desqualificação |
| Sem conversão | Lead qualificado que não gerou venda; não é desqualificação |
| Negócio ganho | Conversão confirmada; a empresa passa a ser cliente |
| Lead parado | Lead ainda não entregue por impedimento operacional |
| Override | Valor editado pelo administrador que passa a prevalecer sobre a planilha naquele campo |

---

## 11. Modelo conceitual de estados

O sistema não deverá usar uma única coluna genérica de “fase” para representar tudo. Cada eixo possui finalidade própria.

### 11.1 Eixos de estado

| Eixo | Valores principais |
|---|---|
| Origem | ativo, arquivado |
| Campanha | aprovação pendente, aprovada, arquivada |
| Atribuição | pendência de dados, pendência de campanha, pronto, parado, atribuído |
| Qualificação | pendente, qualificado, desqualificado |
| Conversão | ativo, acompanhamento qualificado, encerrado sem conversão, ganho |

### 11.2 Fluxo principal do lead

```mermaid
stateDiagram-v2
    [*] --> Importado
    Importado --> PendenteDados: dado obrigatório ausente
    Importado --> PendenteCampanha: campanha desconhecida
    Importado --> Pronto: dados e campanha válidos
    PendenteDados --> Pronto: administrador corrige
    PendenteCampanha --> Pronto: administrador aprova
    Pronto --> Parado: ninguém elegível
    Pronto --> Atribuido: distribuição
    Parado --> Atribuido: condição regularizada
    Atribuido --> Qualificado: houve devolutiva
    Atribuido --> Desqualificado: critério objetivo
    Qualificado --> Acompanhamento: oportunidade continua
    Qualificado --> SemConversao: venda não ocorreu
    Qualificado --> Ganho: venda confirmada
```

### 11.3 Regras de terminalidade

- `desqualificado`, `encerrado sem conversão` e `ganho` encerram o SLA de feedback.
- Um lead `qualificado em acompanhamento` continua sujeito a feedback periódico.
- Apenas o administrador pode reverter `desqualificado` ou `ganho`.
- A reversão gera evento de auditoria; o registro anterior não é apagado.
- `negócio ganho` pode ser registrado uma única vez por lead enquanto o estado não for revertido pelo administrador.

---

## 12. Contrato da planilha Google

### 12.1 Direção da integração

```text
Google Sheets  ───── leitura ─────>  Gerenciador de Leads
Google Sheets  <──── proibido ─────  Gerenciador de Leads
```

O sistema nunca deve inserir, alterar, reorganizar ou apagar células da planilha.

### 12.2 Colunas canônicas

| Ordem | Coluna | Obrigatoriedade | Uso |
|---:|---|---|---|
| A | ID do Lead | Obrigatória em produção | Identidade estável e idempotência |
| B | Data de entrada | Obrigatória | Ordenação, métricas e importação inicial |
| C | ID do anúncio | Recomendada | Rastreabilidade da origem; não é chave única |
| D | Nome do anúncio | Recomendada | Exibição e análise |
| E | ID da Campanha | Recomendada | Identidade externa da campanha |
| F | Nome da campanha | Obrigatória | Aprovação e agrupamento |
| G | Nome da Empresa | Opcional | Empresa exibida; usar o nome do contato como fallback |
| H | Número p/ contato | Obrigatória | Contato comercial |
| I | E-mail | Obrigatória | Contato e deduplicação auxiliar |
| J | CPF/CNPJ | Obrigatória | Identificação; vazio ou inválido gera pendência |
| K | Estado | Obrigatória | Avaliação manual de abrangência |
| L | Nome | Obrigatória | Pessoa de contato |
| M | Fase | Opcional operacionalmente | Armazenada apenas como dado de origem |
| N | Valor estimado | Opcional | Contexto comercial e relatórios |
| O | Proprietário do relacionamento | Opcional | Referência da origem, não controla a fila |

### 12.3 Regras dos identificadores

- `ID do Lead` é a única identidade de origem que deve ser única e estável.
- `ID do anúncio` é armazenado, mas o sistema não presume unicidade. Vários leads podem vir do mesmo anúncio.
- Linhas podem mudar de posição sem alterar o lead, pois o número da linha não é identidade.
- Uma linha sem `ID do Lead` não entra em produção. Registros legados devem receber um ID antes da sincronização inicial.

### 12.4 Validade mínima para distribuição

Para entrar na fila, a linha precisa ter `ID do Lead`, `Data de entrada`, campanha, nome do contato, telefone, e-mail, documento válido e Estado. A ausência de qualquer um desses dados cria pendência administrativa e impede a atribuição. Pendências de dados não contam para o limiar de dois leads parados, pois ainda não estão aptas à distribuição.

### 12.5 Normalização

- CNPJ/CPF: manter somente dígitos para comparação; preservar versão formatada apenas para exibição.
- Telefone: normalizar para código do país + DDD + número quando possível.
- E-mail: `trim` e comparação sem diferença entre maiúsculas e minúsculas.
- Estado: converter para sigla de duas letras.
- Datas: converter para instante usando `America/Sao_Paulo`.
- Valores: converter para decimal monetário sem depender de símbolo ou separador visual.
- Textos: remover espaços externos; não destruir acentos.

### 12.6 Modos de sincronização

#### Bootstrap

- Importar todas as linhas válidas.
- Não distribuir automaticamente todo o histórico.
- O administrador escolhe manualmente a quantidade de leads que deseja liberar por lote.
- Cada lote preserva ordem FIFO por `Data de entrada`, com `ID do Lead` como desempate.
- Após o lote, cada vendedor recebe um único e-mail consolidado com suas atribuições.

#### Operação normal

- Executar sincronização a cada 5 minutos.
- Novas linhas criam um registro de origem e criam ou atualizam a ocorrência comercial correspondente.
- Linhas alteradas atualizam campos sem override administrativo.
- Linhas idênticas não geram trabalho nem eventos novos.
- Linhas removidas arquivam seus registros de origem; a ocorrência comercial só é arquivada quando não restar outra origem ativa, e o histórico nunca é apagado.

### 12.7 Linha removida

Ao desaparecer do snapshot da origem:

- marcar o registro de origem como ausente/arquivado;
- registrar data e motivo `removed_from_source`;
- arquivar a ocorrência e retirá-la de filas/SLAs somente quando não restar outro registro de origem ativo vinculado à mesma ocorrência;
- preservar atribuições, feedbacks, vendas e auditoria;
- não excluir empresa ou campanha.

### 12.8 Precedência de edição

```text
override administrativo > valor atual da planilha > valor anterior importado
```

- Campo sem override acompanha a planilha.
- Editar um campo no sistema cria override por campo, com autor e data.
- Se a planilha mudar um campo com override, abrir conflito para análise manual.
- Até a resolução, o valor administrativo continua visível e operacional.
- “Aceitar origem” remove o override e aplica o valor da planilha.
- “Manter edição” fecha o conflito e preserva o override.
- Vendedores têm somente leitura desses campos.

### 12.9 Coluna `Fase`

A `Fase` da planilha é dado informativo de origem. Ela não pode atribuir lead, desqualificar, marcar venda, alterar proprietário ou substituir os estados internos.

### 12.10 Contrato físico provisório do workbook mock

O fixture `WTG - Leads.xlsx` representa somente a planilha mock atual. Na aba `Leads`, o contrato físico provisório ocupa as colunas A–Q, nesta ordem e com estes headers exatos:

| Coluna | Header físico do mock |
|---|---|
| A | `id` |
| B | `created_time` |
| C | `ad_id` |
| D | `ad_name` |
| E | `adset_id` |
| F | `adset_name` |
| G | `campaign_id` |
| H | `campaign_name` |
| I | `form_id` |
| J | `form_name` |
| K | `is_organic` |
| L | `platform` |
| M | `você_tem_cnpj_ou_mei?` |
| N | `full_name` |
| O | `phone_number` |
| P | `email` |
| Q | `lead_status` |

Para o vendedor, a projeção de dados originados da planilha contém exclusivamente M–P: resposta a `você_tem_cnpj_ou_mei?`, nome, telefone e e-mail. A coluna Q `lead_status` não integra essa projeção. Campos operacionais internos autorizados pelo sistema — como campanha, status interno, prazo e tentativas — não são dados originados da planilha e continuam disponíveis conforme o perfil e as permissões desta especificação.

A coluna M contém apenas a resposta a uma pergunta; ela não contém o número real do CNPJ e não satisfaz a identidade, a deduplicação nem a recorrência por CNPJ definidas na seção 13. A planilha definitiva continua sendo uma dependência posterior. O adapter é a fronteira obrigatória entre este contrato físico provisório e o contrato definitivo, para que a troca da planilha não altere silenciosamente as regras canônicas.

---

## 13. Identidade, duplicidade e recorrência

### 13.1 Níveis de identidade

1. **Registro de origem:** uma linha identificada por `source_lead_id`.
2. **Empresa:** CNPJ normalizado.
3. **Ocorrência comercial:** empresa + campanha.

Mais de um registro de origem pode apontar para a mesma ocorrência comercial. Essa separação é obrigatória para preservar IDs únicos da planilha sem duplicar um lead do mesmo CNPJ na mesma campanha.

### 13.2 Regras de deduplicação

- Mesmo `ID do Lead`: atualizar o mesmo registro de origem e sua ocorrência vinculada.
- Novo `ID do Lead`, mas mesmo CNPJ e mesma campanha: criar novo registro de origem vinculado à ocorrência existente; não criar outra ocorrência comercial.
- Mesmo CNPJ e campanha diferente: criar nova ocorrência ligada à mesma empresa.
- A combinação auxiliar de duplicidade é CNPJ + telefone + e-mail, todos normalizados.
- O sistema pode sinalizar provável duplicidade por telefone/e-mail, mas não deve mesclar automaticamente empresas com CNPJs diferentes.
- Sem CNPJ não há mesclagem automática de empresa.

### 13.3 Documento ausente ou inválido

- Campo vazio ou documento com quantidade inválida de dígitos gera `pendência de dados` e impede distribuição.
- Um CPF válido pode entrar na operação como contato identificado; o vendedor decide manualmente se a ausência de CNPJ desqualifica o lead.
- O administrador pode corrigir o documento. A correção dispara nova verificação de duplicidade antes da distribuição.

### 13.4 Mesmo CNPJ e mesma campanha após resultado final

No MVP, a nova linha atualiza a ocorrência existente e não abre automaticamente um novo ciclo comercial. Se a WTG quiser uma nova oportunidade na mesma campanha, o administrador deverá reabrir explicitamente o lead, gerando auditoria.

---

## 14. Campanhas

### 14.1 Regras gerais

- A campanha vem em coluna da planilha.
- Toda campanha desconhecida nasce como `aprovação pendente`.
- Somente o administrador pode aprovar.
- Enquanto pendente, seus leads não são distribuídos.
- Leads de campanha pendente contam como parados para o alerta operacional.
- Ao aprovar, os leads elegíveis entram na fila FIFO pela data original de entrada.
- Todas as campanhas usam a mesma fila global e os mesmos quatro vendedores.
- Não há especialização de vendedores por campanha no MVP.

### 14.2 Identidade da campanha

- Preferir `ID da Campanha` como chave externa.
- Se o ID estiver ausente, usar nome normalizado apenas para localizar a proposta de campanha.
- O administrador pode definir um nome de exibição diferente do texto da planilha.
- O nome de exibição não altera o valor da origem.

### 14.3 Tela de campanha

Cada campanha deverá apresentar:

- nome de exibição;
- ID externo;
- anúncios vinculados;
- quantidade de leads recebidos;
- atribuídos, parados, pendentes, qualificados, desqualificados e ganhos;
- taxa de qualificação;
- taxa de conversão;
- tempo médio até primeiro feedback;
- período filtrado;
- lista de leads.

---

## 15. Fila global de distribuição

### 15.1 Ordem inicial

```text
Renato → Sandra → Jessica → Nelma → Renato → ...
```

### 15.2 Princípios

- Existe um único cursor global, compartilhado por todas as campanhas.
- O cursor representa a próxima vez natural.
- A ordem pode ser alterada somente pelo administrador.
- A atribuição precisa ocorrer em transação serializada.
- Uma campanha nunca mantém cursor próprio.
- Um lead direcionado por recorrência não movimenta o cursor global.

### 15.3 Elegibilidade do vendedor

O vendedor está elegível se, simultaneamente:

- usuário ativo;
- não está pausado/ausente;
- não possui nenhum lead ativo com feedback vencido;
- não está sendo pulado por crédito compensatório naquela vez natural.

### 15.4 Bloqueio por atraso

- Um único feedback atrasado bloqueia novas atribuições normais.
- O bloqueio é derivado dos dados; não deve depender de um botão manual.
- A verificação crítica compara `feedback_due_at` com o relógio do banco no momento da distribuição; não depende de um cron ter marcado previamente o vendedor como bloqueado.
- O vendedor permanece responsável pelos leads já atribuídos.
- Registrar feedback válido regulariza aquele lead.
- O vendedor volta a estar disponível somente quando não restar nenhum lead atrasado.
- Regularizar não concede entrega imediata e não restaura uma vez perdida.
- Ele será considerado quando o cursor alcançar novamente sua posição.

### 15.5 Perda de vez

Quando chega a vez de um vendedor bloqueado, pausado ou com crédito de pulo:

1. a vez é consumida;
2. o cursor avança;
3. o lead procura o próximo candidato;
4. a vez não fica guardada;
5. não existe compensação por bloqueio ou ausência.

### 15.6 Pseudocódigo do rodízio normal

```text
função distribuir_lead_normal(lead):
    adquirir bloqueio transacional da fila global

    enquanto existir pelo menos um vendedor operacionalmente disponível:
        vendedor = fila[cursor]
        cursor = próxima_posição(cursor)

        se vendedor está inativo, ausente ou possui atraso:
            registrar pulo por indisponibilidade
            continuar

        se vendedor possui créditos_de_pulo > 0:
            decrementar exatamente 1 crédito
            registrar pulo compensatório
            continuar

        atribuir lead ao vendedor
        iniciar SLA de feedback
        registrar histórico e evento de notificação
        confirmar transação
        retornar atribuição

    marcar lead como parado por falta de vendedor elegível
    confirmar transação
```

Se todos os vendedores disponíveis possuírem créditos de pulo, o algoritmo pode completar novas voltas na mesma transação até consumir os créditos necessários e encontrar o primeiro candidato elegível. Se todos estiverem realmente bloqueados/ausentes, o lead fica parado.

### 15.7 Concorrência

- Duas sincronizações simultâneas não podem ler e atualizar o mesmo cursor sem bloqueio.
- Usar uma transação MongoDB que faça escrita condicional no documento único de `queue_state`, com versão, dentro de uma sessão conectada a replica set.
- A atribuição, o avanço do cursor, o consumo de crédito e a criação do histórico devem confirmar ou falhar juntos.
- Cada lead possui índice único parcial que impede duas atribuições atuais.

### 15.8 Reordenação

- Apenas administrador.
- Exibir ordem anterior e nova em auditoria.
- Reordenar não apaga créditos de pulo.
- O próximo cursor deve ser remapeado para a identidade do vendedor que era o próximo, não apenas para o número do índice, evitando mudança acidental da vez.

---

## 16. Empresas recorrentes e propriedade

### 16.1 Definição do proprietário

- O primeiro vendedor a receber uma atribuição efetiva de um CNPJ torna-se proprietário da empresa.
- Um lead parado não define proprietário.
- A propriedade pertence à empresa, não à campanha.
- A propriedade não muda quando surge novo lead em campanha diferente.

### 16.2 Novo lead da mesma empresa em campanha diferente

Quando um CNPJ conhecido reaparece em outra campanha:

1. criar uma nova ocorrência de lead;
2. vinculá-la à empresa existente;
3. direcioná-la ao proprietário da empresa;
4. não avançar o cursor global;
5. adicionar um crédito de pulo ao vendedor que recebeu a entrega direcionada.

### 16.3 Créditos de pulo

- Um lead direcionado gera um crédito.
- Três leads direcionados geram três créditos.
- Cada crédito é consumido em uma futura vez natural do vendedor.
- Os créditos podem atravessar várias rotações.
- O saldo nunca pode ficar negativo.
- O administrador visualiza o saldo de todos.
- O vendedor visualiza apenas o próprio saldo, sem informações dos colegas.

### 16.4 Proprietário bloqueado

- Se o proprietário estiver bloqueado ou pausado, o lead recorrente aguarda.
- O lead conta como parado para o alerta operacional.
- O sistema não o entrega automaticamente a outro vendedor.
- Quando o proprietário se regulariza, o lead recorrente pode ser atribuído imediatamente a ele, pois não depende da vez natural.
- O SLA começa somente na atribuição efetiva.

### 16.5 Direcionamento temporário

O administrador pode escolher outro responsável para atender um lead recorrente parado.

- O proprietário da empresa permanece original.
- O vendedor temporário torna-se responsável atual do lead.
- A atribuição temporária não altera o cursor.
- O vendedor temporário recebe um crédito de pulo.
- Se ele marcar negócio ganho, o crédito da venda é dele.
- Futuras recorrências continuam indo ao proprietário original.

### 16.6 Transferência permanente

- Somente o administrador pode transferir.
- Altera o proprietário da empresa para os leads futuros.
- Não reescreve responsáveis ou créditos de vendas históricas.
- Deve exigir motivo e confirmação.
- Gera evento de auditoria com proprietário anterior e novo.

---

## 17. Leads parados e fila FIFO

### 17.1 Motivos

| Motivo | Distribuição automática | Conta no alerta de 2 parados |
|---|---:|---:|
| Todos os vendedores bloqueados/ausentes | Sim, ao surgir elegibilidade | Sim |
| Proprietário recorrente bloqueado | Sim, quando ele regulariza | Sim |
| Campanha aguardando aprovação | Sim, depois da aprovação | Sim |
| Dado mínimo ausente ou inválido | Sim, depois da correção | Não |

### 17.2 Ordem FIFO

- Ordenar por `Data de entrada`.
- Usar `ID do Lead` como desempate estável.
- A prioridade não muda quando o motivo da pendência muda.
- Leads recorrentes respeitam seu proprietário e não concorrem com a fila normal.

### 17.3 Incidente de dois parados

- Abrir incidente quando a contagem elegível cruza de menos de 2 para 2 ou mais.
- Enviar um único alerta ao administrador por incidente.
- Enquanto o incidente estiver aberto, novos leads não geram alertas repetidos.
- Resolver quando a contagem cai para menos de 2.
- Um novo cruzamento após a resolução abre novo incidente.
- Leads com pendência de dados — inclusive CNPJ, telefone ou e-mail — aparecem no painel, mas não entram nessa contagem.

### 17.4 Falta total de vendedores

Se todos estiverem bloqueados ou pausados:

- os leads normais permanecem parados;
- nenhum é descartado;
- a ordem FIFO é preservada;
- quando alguém se regularizar, o distribuidor é acionado automaticamente;
- o vendedor regularizado recebe apenas conforme a posição do cursor, exceto lead recorrente que pertence a ele.

---

## 18. SLA e feedback periódico

### 18.1 Prazo

- Prazo inicial: 24 horas úteis após a atribuição.
- Sábados, domingos, feriados nacionais e feriados estaduais de São Paulo não contam.
- Feriados municipais não entram no MVP.
- Fuso: `America/Sao_Paulo`.
- Não há janela comercial de 9h às 18h; o relógio conta continuamente em dias elegíveis e pausa integralmente em dias não úteis.

### 18.2 Exemplos

| Atribuição | Calendário | Vencimento |
|---|---|---|
| Quinta, 10h | Sexta útil | Sexta, 10h |
| Sexta, 14h | Fim de semana comum | Segunda, 14h |
| Sexta, 14h | Segunda é feriado | Terça, 14h |

### 18.3 Lembrete

- Enviar 4 horas úteis antes do vencimento.
- O lembrete é transacional e não deve esperar o resumo diário.
- Criar chave idempotente por `lead + ciclo de SLA + tipo de lembrete`.

### 18.4 Feedback válido

Um feedback é válido quando:

- foi criado pelo responsável atual;
- está vinculado a uma ação explícita de contato/retorno;
- possui comentário com pelo menos 6 caracteres após remover espaços externos;
- não é apenas uma nota administrativa;
- não é duplicação idempotente da mesma submissão.

### 18.5 Renovação de prazo

- Cada feedback válido cria um novo ciclo de 24 horas úteis enquanto o lead estiver ativo.
- O ciclo anterior fica no histórico.
- Resultado final encerra o ciclo atual.
- Um comentário posterior ao vencimento regulariza aquele lead e cria novo prazo, caso ele continue ativo.
- O vendedor só é desbloqueado se nenhum outro lead dele permanecer atrasado.

### 18.6 Duração do acompanhamento

O acompanhamento é por tempo indeterminado. Não existe encerramento automático por idade do lead. Ele permanece ativo até que seja qualificado e encerrado, desqualificado, ganho ou arquivado por decisão válida.

---

## 19. Tentativas de contato

### 19.1 Regra

- Canal inicial do MVP: WhatsApp.
- Limite operacional: 5 tentativas.
- As tentativas devem ocorrer em 5 dias úteis distintos.
- No máximo uma tentativa conta por lead em cada data útil.
- Cada tentativa exige comentário válido.
- O sistema registra autor, data, hora, canal e número sequencial.

### 19.2 Após a quinta tentativa

- O sistema habilita o motivo `Não atende após 5 tentativas`.
- A desqualificação continua manual.
- O sistema nunca desqualifica automaticamente.
- Tentativas por telefone ou e-mail podem ser descritas no comentário, mas não substituem a contagem de WhatsApp no MVP.

### 19.3 Integridade

- Não permitir tentativa futura.
- Não permitir duas tentativas contabilizadas no mesmo dia útil.
- Não permitir tentativa em sábado, domingo ou feriado configurado.
- Correção de tentativa contabilizada exige administrador e auditoria.

---

## 20. Qualificação, desqualificação e conversão

### 20.1 Qualificação

Um lead é qualificado quando houve devolutiva real do contato após conversa iniciada pelo vendedor. A devolutiva pode ser positiva ou negativa.

Para qualificar:

- responsável atual realiza a ação;
- comentário com ao menos 6 caracteres;
- ação confirma explicitamente que houve resposta do contato;
- registrar data da decisão.

### 20.2 Não conversão

Não comprar, recusar proposta, escolher concorrente ou adiar a contratação não são motivos de desqualificação quando houve uma conversa real.

Nesses casos:

- `qualification_status = qualified`;
- `conversion_status = closed_no_conversion` quando o acompanhamento terminar;
- o lead continua contando como qualificado na taxa de campanha;
- não conta como negócio ganho.

### 20.3 Motivos permitidos de desqualificação

1. Não atende após 5 tentativas válidas em dias úteis distintos.
2. Não possui CNPJ.
3. Não pertence ao Estado de São Paulo.

Nenhum outro motivo pode ser escrito livremente como categoria. O comentário detalha o contexto, mas a categoria deve ser uma das três.

### 20.4 Avaliação manual

- O Estado diferente de SP não bloqueia a distribuição automaticamente; o vendedor analisa e desqualifica manualmente.
- Um CPF pode ser distribuído para análise; o vendedor pode confirmar ausência de CNPJ e desqualificar manualmente.
- Documento vazio ou inválido fica em pendência administrativa antes da distribuição.
- O sistema não toma decisão comercial automática com base apenas nos dados da planilha.

### 20.5 Negócio ganho

- Exige comentário válido.
- Marca o lead como qualificado e ganho.
- Converte a empresa em cliente.
- Registra responsável creditado, data e histórico.
- Se havia responsável temporário, a venda é creditada a ele.
- O proprietário original da empresa não muda por causa da venda temporária.
- A ação é idempotente e não pode criar dois eventos de venda para o mesmo lead.
- Somente o administrador pode reverter.

### 20.6 Resultado final e propriedade

Qualificar, desqualificar, encerrar sem conversão ou ganhar não muda automaticamente o proprietário da empresa.

---

## 21. Métricas e fórmulas

### 21.1 Taxa de qualificação

```text
leads qualificados
──────────────────────────────────────────────
leads qualificados + leads desqualificados
```

- Negócios ganhos pertencem ao conjunto de qualificados.
- Qualificados encerrados sem conversão continuam no numerador.
- Leads pendentes, novos, em contato ou parados não entram no denominador.
- O filtro de período usa `qualification_decided_at`.

### 21.2 Taxa de conversão dos qualificados

```text
negócios ganhos
────────────────────────────
leads qualificados decididos
```

### 21.3 SLA de primeiro feedback

```text
leads com primeiro feedback dentro do prazo
────────────────────────────────────────────
leads atribuídos com prazo já mensurável
```

### 21.4 Indicadores do administrador

- Leads recebidos.
- Leads distribuídos.
- Leads parados por motivo.
- Campanhas pendentes.
- CNPJs/documentos pendentes.
- Taxa de qualificação geral e por campanha.
- Conversões e valor estimado ganho.
- Feedbacks próximos do vencimento e atrasados.
- Tempo médio até primeira interação.
- Distribuição por vendedor.
- Créditos de pulo pendentes.
- Histórico de conflitos com a planilha.

### 21.5 Indicadores do vendedor

Somente seus próprios dados:

- leads ativos;
- feedbacks próximos do vencimento;
- feedbacks atrasados;
- qualificados;
- ganhos;
- taxa de qualificação própria;
- sua posição atual na fila;
- seu saldo de pulos compensatórios.

O vendedor não recebe totais individuais dos colegas.

### 21.6 Dimensão temporal

- Entrada: `source_entered_at`.
- Atribuição: `assigned_at`.
- Feedback: `feedback_created_at`.
- Qualificação: `qualification_decided_at`.
- Venda: `won_at`.

Cada gráfico deve declarar qual data utiliza. Não filtrar todos os indicadores por uma única coluna genérica.

---

## 22. Notificações e e-mails

### 22.1 Identidade de envio

- Remetente: `contato@wtgseguros.com.br`.
- Nome de exibição recomendado: `WTG — Contato Comercial`.
- Não copiar automaticamente o administrador nos e-mails de vendedor.

### 22.2 E-mails do vendedor

| Evento | Destinatário | Forma |
|---|---|---|
| Novas atribuições da operação normal | Somente vendedor responsável | Um consolidado diário por vendedor às 9h |
| Lote da importação inicial | Somente vendedor responsável | Um consolidado ao concluir o lote |
| Prazo a 4 horas úteis | Responsável atual | Imediato/transacional |
| Feedback vencido | Responsável atual | Uma notificação por ciclo vencido |

Se o vendedor não tiver novas atribuições no período, não enviar resumo vazio.
As atribuições aparecem imediatamente no dashboard; a consolidação afeta apenas o e-mail, não a disponibilidade do lead no sistema nem o início do SLA.

### 22.3 E-mails do administrador

As categorias não devem ser combinadas no mesmo e-mail:

1. Campanhas aguardando aprovação — consolidado diário às 9h.
2. Leads com CNPJ/documento pendente — consolidado diário às 9h.
3. Relatório geral de pendências — consolidado diário às 9h.
4. Incidente de 2 ou mais leads parados elegíveis — alerta no momento do cruzamento do limite.

### 22.4 Outbox e idempotência

- A transação de negócio grava um evento na coleção `notification_outbox`.
- Um worker Python idempotente na Railway consome eventos pendentes.
- Cada mensagem usa uma chave idempotente.
- Falha de e-mail não desfaz atribuição ou feedback.
- Reenvios preservam o mesmo evento e incrementam tentativas.
- Após limite de tentativas, mover para fila de falha e alertar administrador.

---

## 23. Experiência do usuário

### 23.1 Diretrizes gerais

- Interface em português do Brasil.
- Interface exclusivamente desktop, com largura mínima suportada de 1280 px; tablet e celular estão fora do escopo funcional.
- Estados e prazos devem ser entendidos por texto, não apenas cor.
- Datas exibidas no horário de São Paulo.
- Ações finais exigem confirmação clara.
- A interface nunca deve sugerir que “desqualificado” significa “não vendeu”.

### 23.2 Rotas recomendadas

```text
/login
/dashboard
/leads
/leads/:id
/campanhas
/campanhas/:id
/fila
/pendencias
/relatorios
/configuracoes
```

As rotas podem compartilhar o mesmo shell, mas o conteúdo é filtrado pelo perfil no servidor e no banco.

### 23.3 Dashboard do administrador

- KPIs globais.
- Filtro de período.
- Filtro de campanha.
- Taxa de qualificação por campanha.
- Conversão.
- Total e motivos de leads parados.
- Lista da fila com estados e créditos.
- Feedbacks atrasados.
- Campanhas para aprovação.
- Sincronização mais recente.

### 23.4 Dashboard do vendedor

- Somente indicadores próprios.
- Próximos vencimentos.
- Atrasados.
- Leads ativos.
- Qualificados e ganhos.
- Posição individual na fila.
- Não exibir nomes nem estados dos demais vendedores.

### 23.5 Lista de leads

Filtros:

- campanha;
- responsável;
- estado de atribuição;
- qualificação;
- conversão;
- prazo;
- Estado;
- período;
- busca por empresa, contato, CNPJ, telefone ou e-mail.

Colunas mínimas:

- empresa/contato;
- campanha/anúncio;
- responsável atual;
- proprietário da empresa quando diferente;
- estado de qualificação;
- estado de conversão;
- próximo prazo;
- número de tentativas;
- data de entrada.

### 23.6 Detalhe do lead

- Dados importados.
- Sinalização de override/conflito.
- Campanha e anúncio.
- Empresa e proprietário.
- Responsável atual e tipo de atribuição.
- Linha do tempo completa.
- SLA atual.
- Tentativas.
- Formulário de feedback.
- Ações de qualificar, desqualificar, encerrar sem conversão e ganhar.
- Link para abrir WhatsApp ou copiar o telefone; abrir a conversa não registra tentativa automaticamente.

### 23.7 Tela de fila

Administrador:

- ordem completa;
- próximo cursor;
- estado de cada vendedor;
- número de atrasos;
- saldo de créditos de pulo;
- ações de subir/descer, pausar e reativar;
- histórico de alterações.

Vendedor:

- somente sua posição;
- se está elegível ou bloqueado;
- motivo próprio do bloqueio;
- saldo próprio de pulos.

### 23.8 Central de pendências

Separar em abas ou grupos:

- campanhas pendentes;
- documentos/CNPJ pendentes;
- leads parados por disponibilidade;
- proprietários recorrentes bloqueados;
- feedbacks atrasados;
- conflitos de origem;
- falhas de sincronização/notificação.

### 23.9 Exportação

- Somente administrador no MVP.
- CSV e XLSX.
- Respeitar filtros atuais.
- Incluir data/hora, usuário que exportou e quantidade de registros na auditoria.
- Não incluir segredos, hashes de senha ou payloads técnicos.

---

## 24. Casos de uso principais

### UC-01 — Sincronizar nova linha

**Ator:** job Python de integração na Railway.
**Pré-condição:** linha possui ID do Lead.
**Fluxo:** normalizar → validar → deduplicar → resolver campanha/empresa → gravar → distribuir ou deixar pendente.
**Pós-condição:** uma única ocorrência criada ou atualizada, com histórico da sincronização.

### UC-02 — Distribuir lead normal

**Ator:** sistema.
**Fluxo:** bloquear fila → avaliar cursor → consumir pulos necessários → atribuir → criar SLA → registrar outbox → confirmar.
**Pós-condição:** exatamente um responsável ou motivo de parada.

### UC-03 — Registrar feedback

**Ator:** responsável atual.
**Fluxo:** escrever comentário válido → opcionalmente registrar tentativa → salvar → renovar SLA.
**Pós-condição:** histórico imutável e possível desbloqueio derivado.

### UC-04 — Qualificar

**Ator:** responsável atual.
**Fluxo:** confirmar devolutiva → comentar → escolher continuidade ou encerramento sem conversão.
**Pós-condição:** taxa de qualificação atualizada sem marcar venda automaticamente.

### UC-05 — Desqualificar

**Ator:** responsável atual.
**Fluxo:** selecionar motivo permitido → cumprir pré-condições → comentar → confirmar.
**Pós-condição:** SLA encerrado e evento auditado.

### UC-06 — Marcar negócio ganho

**Ator:** responsável atual.
**Fluxo:** comentar → confirmar → registrar venda única.
**Pós-condição:** empresa cliente, crédito ao responsável atual, propriedade preservada.

### UC-07 — Aprovar campanha

**Ator:** administrador.
**Fluxo:** revisar campanha → aprovar → liberar leads FIFO.
**Pós-condição:** leads elegíveis processados pela fila.

### UC-08 — Direcionar temporariamente

**Ator:** administrador.
**Fluxo:** escolher lead recorrente parado → escolher vendedor → informar motivo → confirmar.
**Pós-condição:** responsável temporário, proprietário original intacto, crédito de pulo criado.

### UC-09 — Transferir empresa

**Ator:** administrador.
**Fluxo:** escolher novo proprietário → justificar → confirmar.
**Pós-condição:** futuras recorrências usam o novo proprietário; histórico preservado.

---

## 25. Modelo de dados recomendado no MongoDB

O banco canônico chama-se `gerec_leads`. Cada entidade abaixo corresponde a uma coleção normalizada, ligada por identificadores estáveis. Não duplicar estado crítico em documentos embutidos quando isso impedir atualização atômica, auditoria ou aplicação uniforme de permissões.

### 25.1 Entidades

| Entidade | Finalidade | Campos essenciais |
|---|---|---|
| `profiles` | Perfil do usuário autenticado | user_id, nome, e-mail, papel, ativo |
| `seller_queue` | Ordem e disponibilidade administrativa | seller_id, posição, pausado, versão |
| `queue_state` | Cursor global | next_seller_id, versão, updated_at |
| `seller_skip_balances` | Créditos compensatórios | seller_id, saldo |
| `campaigns` | Campanhas internas e externas | external_id, source_name, display_name, status |
| `companies` | Empresa consolidada | cnpj, nome, estado, owner_id, client_since |
| `leads` | Ocorrência por empresa/campanha | company_id, campaign_id, dados operacionais, estados |
| `lead_source_records` | Linhas/IDs da planilha vinculados à ocorrência | source_lead_id, lead_id, source_row, row_hash, payload, present |
| `assignments` | Histórico de responsáveis | lead_id, seller_id, tipo, início, fim, autor |
| `feedback_cycles` | Cada SLA de 24h úteis | lead_id, start_at, reminder_at, due_at, closed_at |
| `feedbacks` | Comentários operacionais | lead_id, seller_id, comment, created_at |
| `contact_attempts` | Tentativas contabilizadas | lead_id, seller_id, channel, attempt_date |
| `qualification_events` | Decisões de qualificação | lead_id, outcome, reason, comment, actor |
| `sales` | Negócio ganho idempotente | lead_id único, credited_seller_id, won_at |
| `business_holidays` | Calendário nacional/SP | date, name, scope |
| `source_snapshots` | Execuções e presença dos registros de origem | sync_id, source_record_id, present |
| `field_overrides` | Precedência administrativa por campo | lead_id, field_name, value, actor |
| `source_conflicts` | Mudanças conflitantes | lead_id, field_name, source/admin values, status |
| `notification_outbox` | Eventos para integração | event_type, aggregate_id, idempotency_key, status |
| `notification_incidents` | Controle de alertas únicos | type, opened_at, resolved_at |
| `audit_log` | Trilha imutável | actor, entity, action, before, after, created_at |
| `system_settings` | Parâmetros globais | timezone, SLA, lembrete, limiar, horário digest |

### 25.2 Relações principais

```mermaid
erDiagram
    PROFILES ||--o{ ASSIGNMENTS : recebe
    PROFILES ||--o{ FEEDBACKS : registra
    PROFILES ||--o{ COMPANIES : possui
    COMPANIES ||--o{ LEADS : origina
    CAMPAIGNS ||--o{ LEADS : agrupa
    LEADS ||--o{ LEAD_SOURCE_RECORDS : consolida
    LEADS ||--o{ ASSIGNMENTS : historico
    LEADS ||--o{ FEEDBACKS : acompanha
    LEADS ||--o| SALES : converte
    PROFILES ||--o| SELLER_SKIP_BALANCES : compensa
```

### 25.3 Índices e validações essenciais

- índice único de `profiles.email_normalized`.
- índice único parcial de `companies.cnpj` quando presente e válido.
- índice único de `lead_source_records.source_lead_id`.
- índice único parcial para ocorrência ativa por `company_id + campaign_id`.
- uma atribuição atual por lead.
- `sales.lead_id` único.
- saldo de pulo maior ou igual a zero.
- posição de fila única entre vendedores ativos.
- comentário com mínimo de 6 caracteres após `trim`.
- uma tentativa contabilizada por lead/data útil.
- motivo de desqualificação pertencente ao conjunto permitido.
- `won_at` obrigatório quando conversão for ganha.

### 25.4 Histórico e transações

Coleções de evento não devem ser atualizadas destrutivamente. Correções criam eventos de reversão ou novos documentos. Dados atuais podem ser materializados nas coleções principais para consulta rápida, mas devem ser reproduzíveis a partir do histórico crítico.

Comandos que alteram mais de uma coleção — incluindo atribuição, cursor, créditos, histórico, auditoria e outbox — executam em uma única transação MongoDB. Todos os ambientes precisam fornecer replica set; a aplicação deve falhar de forma explícita na inicialização quando o ambiente não suportar essas transações.

---

## 26. Comandos de domínio e contratos de API

Os nomes abaixo são recomendados; a implementação pode ajustar rotas sem alterar semântica.

### 26.1 Ingestão

`POST /api/internal/imports/google-sheets/sync`

Requisitos:

- autenticação de serviço;
- `sync_run_id` e idempotency key;
- coleção de linhas normalizadas;
- resposta por linha: criada, atualizada, ignorada, pendente ou erro;
- não retornar segredos.

### 26.2 Feedback

`POST /api/leads/:leadId/feedbacks`

Payload conceitual:

```json
{
  "comment": "Contato respondeu e pediu retorno amanhã.",
  "contactStarted": true,
  "attempt": {
    "count": true,
    "channel": "whatsapp",
    "businessDate": "2026-08-25"
  },
  "idempotencyKey": "uuid"
}
```

O servidor calcula os prazos. O cliente nunca envia `due_at` como fonte de verdade.

### 26.3 Resultado

`POST /api/leads/:leadId/outcome`

Resultados aceitos:

- `qualified_follow_up`;
- `qualified_closed_no_conversion`;
- `disqualified`;
- `won`.

Todos exigem comentário; `disqualified` exige motivo; `won` cria registro de venda.

### 26.4 Administração

- `POST /api/admin/campaigns/:id/approve`
- `POST /api/admin/queue/reorder`
- `POST /api/admin/sellers/:id/pause`
- `POST /api/admin/leads/:id/temporary-assignment`
- `POST /api/admin/companies/:id/transfer-owner`
- `POST /api/admin/source-conflicts/:id/resolve`
- `POST /api/admin/leads/:id/reverse-outcome`

### 26.5 Leitura

As consultas devem aplicar autorização por perfil e filtros no backend Python. Não baixar todos os leads para filtrar no navegador e nunca consultar MongoDB diretamente a partir do cliente web.

---

## 27. Eventos de domínio

Eventos mínimos:

- `lead.imported`
- `lead.source_updated`
- `lead.archived`
- `lead.parked`
- `lead.assigned`
- `lead.feedback_due_soon`
- `lead.feedback_overdue`
- `lead.feedback_recorded`
- `lead.qualified`
- `lead.disqualified`
- `lead.closed_without_conversion`
- `lead.won`
- `campaign.detected`
- `campaign.approved`
- `seller.blocked`
- `seller.unblocked`
- `seller.skip_credited`
- `seller.skip_consumed`
- `company.owner_transferred`
- `source.conflict_detected`
- `parked.threshold_crossed`

Cada evento deve ter ID único, instante, agregado, ator quando aplicável e payload versionado.

---

## 28. Segurança e LGPD

### 28.1 Controles obrigatórios

- Autorização por perfil em todos os comandos e consultas do backend Python.
- Filtros obrigatórios de vendedor baseados no responsável atual e no histórico permitido, aplicados antes de consultar ou alterar coleções.
- Rotas administrativas verificam papel no servidor.
- Credenciais do MongoDB e chaves administrativas somente no backend e nos jobs Python da Railway.
- Segredos em variáveis de ambiente ou cofre, nunca no repositório.
- Senhas armazenadas somente como hash forte pelo serviço de autenticação do backend Python; nunca em texto puro nem em documentos comerciais.
- Proteção contra enumeração de contas no login/recuperação.
- Auditoria de exportação e ações finais.
- Sessão expirada e logout confiável.

### 28.2 Dados pessoais

Telefone, e-mail, nome, CPF/CNPJ e histórico de contato são dados protegidos. Exibir apenas a usuários com necessidade operacional. Logs técnicos não devem copiar payload completo sem necessidade.

### 28.3 Autorização e escopo de dados esperados

- Administrador: acesso operacional completo.
- Vendedor: leitura de leads cujo responsável atual é ele; histórico necessário de leads que atendeu é retornado por projeção restrita, sem permitir novas alterações.
- Feedback: inserção somente pelo responsável atual.
- Fila global: o backend retorna ao vendedor apenas uma projeção da própria posição.
- Métricas: consultas de vendedor sempre incluem o identificador do usuário autenticado no filtro MongoDB e passam por testes de acesso cruzado.

---

## 29. Falhas, consistência e recuperação

### 29.1 Sincronização repetida

Resultado esperado: nenhuma duplicação. O `ID do Lead` identifica o registro de origem, o hash evita atualizações vazias e a chave empresa + campanha consolida a ocorrência comercial.

### 29.2 Falha no meio da atribuição

Resultado esperado: transação inteira é revertida. Não pode avançar cursor sem atribuir, nem atribuir sem criar histórico.

### 29.3 E-mail indisponível

Resultado esperado: ação de negócio permanece confirmada; evento continua na outbox para nova tentativa.

### 29.4 Feriado ausente

O administrador pode adicionar/corrigir o calendário. O sistema recalcula apenas ciclos ainda abertos e registra a alteração; ciclos encerrados permanecem históricos.

### 29.5 Usuário desativado com leads ativos

- Pausar imediatamente novas entregas.
- Exibir pendência ao administrador.
- Não transferir automaticamente.
- Administrador decide direcionamento temporário ou transferência permanente.

### 29.6 Campanha renomeada na planilha

Se `ID da Campanha` for o mesmo, atualizar `source_name` sem criar campanha. Preservar o nome de exibição administrativo.

Se o `ID da Campanha` de um registro de origem mudar:

- antes de qualquer atribuição, remapear a ocorrência e revalidar a aprovação normalmente;
- depois de atribuição, feedback ou resultado, não reescrever o histórico automaticamente; abrir conflito para o administrador decidir entre corrigir a campanha histórica ou criar/vincular uma nova ocorrência.

### 29.7 Alteração de CNPJ

É uma mudança sensível:

- revalidar empresa e duplicidade;
- se existir override, abrir conflito;
- se a empresa mudar, não migrar ownership automaticamente sem revisão administrativa;
- impedir mesclagem silenciosa de históricos.

---

## 30. Auditoria

Registrar ao menos:

- login relevante e falhas de acesso;
- criação/desativação de usuário;
- reordenação e pausa da fila;
- atribuição e seus pulos;
- créditos criados/consumidos;
- feedbacks e tentativas;
- decisões de qualificação;
- negócio ganho e reversões;
- aprovação de campanha;
- overrides e conflitos;
- direcionamento temporário e transferência permanente;
- importações e arquivamentos;
- exportações.

Cada registro deve conter `actor_id`, ação, entidade, antes/depois quando aplicável, instante e correlation ID.

---

## 31. Observabilidade

### 31.1 Painel técnico do administrador

- última sincronização;
- duração;
- linhas lidas, criadas, atualizadas, ignoradas e com erro;
- último e-mail enviado por fluxo;
- eventos pendentes na outbox;
- falhas definitivas;
- versão da aplicação e do schema de dados.

### 31.2 Logs

- Estruturados em JSON.
- Correlation ID por sincronização/comando.
- Não registrar senha, token ou conteúdo integral de dados pessoais sem necessidade.
- Diferenciar erro recuperável de violação de regra.

### 31.3 Alertas técnicos

- sincronização sem sucesso por período superior ao esperado;
- fila de outbox crescendo;
- erro de autenticação do Google Sheets;
- falha do provedor de e-mail;
- alteração de schema ou índice inconsistente.

---

## 32. Requisitos não funcionais

| Categoria | Requisito |
|---|---|
| Consistência | Nenhuma atribuição dupla; comandos críticos transacionais |
| Idempotência | Importações, feedbacks, resultados e e-mails aceitam repetição segura |
| Desempenho | P95 das telas comuns abaixo de 2 segundos em condições normais |
| Escalabilidade | Paginação e filtros no servidor; sem carregar toda a base no cliente |
| Disponibilidade | Falha de integração não interrompe consultas e feedbacks já disponíveis |
| Acessibilidade | Navegação por teclado, foco visível, rótulos e contraste adequados |
| Suporte desktop | Uso funcional em desktop com largura mínima de 1280 px; tablet e celular fora do escopo funcional |
| Localização | pt-BR, moeda BRL e horário de São Paulo |
| Histórico | Dados operacionais não são apagados fisicamente por ações comuns |
| Backup | Backups automáticos do banco e procedimento de restauração testado |
| Segurança | Autorização server-side, filtros por perfil, segredos fora do cliente, auditoria e princípio do menor privilégio |

---

## 33. Estratégia de testes

### 33.1 Testes unitários

- normalização de CNPJ/CPF, telefone, e-mail e datas;
- cálculo de 24 horas úteis;
- lembrete de 4 horas úteis;
- fins de semana e feriados;
- chave de duplicidade;
- elegibilidade de vendedor;
- consumo de créditos de pulo;
- fórmulas de métricas.

### 33.2 Testes de banco/integrados

- distribuição concorrente;
- rollback do cursor;
- mesmo CNPJ/mesma campanha;
- mesmo CNPJ/campanha diferente;
- owner bloqueado;
- atribuição temporária;
- índice único de venda por lead;
- autorização e isolamento de administrador/vendedor;
- override e conflito;
- arquivamento de linha removida;
- outbox idempotente.

### 33.3 Testes ponta a ponta

- login de cada perfil;
- vendedor não vê colegas;
- administrador aprova campanha;
- lead passa por novo → contato → qualificado → ganho;
- cinco tentativas → desqualificação manual;
- feedback atrasado bloqueia e regularização remove bloqueio;
- exportação administrativa;
- recuperação de senha.

### 33.4 Relógio controlável

Testes de SLA não podem depender do relógio real. O serviço de tempo deve ser injetável para simular sexta-feira, fim de semana e feriado.

---

## 34. Critérios de aceite em cenários

### AC-01 — Rodízio básico

**Dado** cursor em Renato e todos elegíveis
**Quando** quatro leads normais forem processados em sequência
**Então** Renato, Sandra, Jessica e Nelma recebem exatamente um, nessa ordem.

### AC-02 — Vendedor atrasado perde a vez

**Dado** cursor em Renato e Renato com um feedback vencido
**Quando** chegar um lead normal
**Então** Renato é pulado, Sandra recebe e o cursor avança após Sandra.

### AC-03 — Regularização não restaura vez

**Dado** Renato foi pulado por atraso
**Quando** ele registrar feedback válido
**Então** não recebe imediatamente um lead normal; aguarda o próximo retorno natural do cursor.

### AC-04 — Um atraso é suficiente

**Dado** vendedor com dez leads ativos e apenas um vencido
**Então** ele fica bloqueado para novas entregas.

### AC-05 — Todos bloqueados

**Dado** todos os vendedores bloqueados
**Quando** chegar um lead apto
**Então** o lead fica parado, sem responsável e em FIFO.

### AC-06 — Liberação da fila parada

**Dado** leads normais parados e Sandra se regulariza
**Quando** o distribuidor for acionado
**Então** processa FIFO respeitando o cursor, sem furar a ordem.

### AC-07 — Recorrência entre campanhas

**Dado** CNPJ proprietário de Renato na campanha A
**Quando** surgir na campanha B
**Então** cria novo lead, atribui a Renato, não move cursor e adiciona um crédito de pulo a Renato.

### AC-08 — Múltiplas recorrências

**Dado** Renato recebeu três leads direcionados
**Então** perde suas três próximas vezes naturais, mesmo em rotações diferentes.

### AC-09 — Proprietário recorrente bloqueado

**Dado** novo lead recorrente de Renato e Renato bloqueado
**Então** o lead espera por Renato e conta como parado; não vai automaticamente a Sandra.

### AC-10 — Direcionamento temporário

**Dado** lead recorrente de Renato parado
**Quando** administrador direcionar temporariamente a Sandra
**Então** Sandra atende, recebe um crédito de pulo e Renato continua proprietário da empresa.

### AC-11 — Venda temporária

**Dado** Sandra como responsável temporária
**Quando** marcar negócio ganho com comentário válido
**Então** a venda é creditada a Sandra e a empresa continua de Renato.

### AC-12 — Duplicidade na mesma campanha

**Dado** CNPJ já existente na campanha A
**Quando** nova sincronização trouxer o mesmo CNPJ/campanha
**Então** vincula o novo registro de origem, atualiza a ocorrência e não cria outra ocorrência comercial.

### AC-13 — Linha movida

**Dado** a linha mudou de posição, mas manteve ID do Lead
**Então** o mesmo registro é atualizado.

### AC-14 — Linha removida

**Dado** ID do Lead não aparece no snapshot completo
**Então** o registro de origem é arquivado; a ocorrência é arquivada somente se nenhum outro registro de origem ativo permanecer vinculado, e nada é apagado.

### AC-15 — Override administrativo

**Dado** administrador alterou telefone no sistema
**Quando** a planilha trouxer outro telefone
**Então** o valor administrativo permanece e nasce conflito manual.

### AC-16 — Campanha nova

**Dado** campanha desconhecida
**Quando** seus leads forem importados
**Então** ficam pendentes e contam como parados até aprovação.

### AC-17 — Documento vazio

**Dado** linha sem CPF/CNPJ
**Então** fica em pendência de dados, não é distribuída e não entra no limiar de dois parados.

### AC-18 — Prazo no fim de semana

**Dado** lead atribuído sexta às 14h e sem feriado
**Então** o prazo vence segunda às 14h e o lembrete ocorre segunda às 10h.

### AC-19 — Comentário inválido

**Dado** comentário com menos de 6 caracteres úteis
**Então** não salva, não renova prazo e não desbloqueia vendedor.

### AC-20 — Feedback periódico

**Dado** lead ativo com feedback válido
**Então** abre novo ciclo de 24 horas úteis.

### AC-21 — Cinco tentativas

**Dado** quatro tentativas válidas
**Então** não permite desqualificar como não atende.
**Quando** a quinta tentativa em dia útil distinto for registrada
**Então** habilita a decisão manual.

### AC-22 — Não converteu

**Dado** cliente respondeu, mas recusou a proposta
**Então** pode ser qualificado e encerrado sem conversão; não pode ser desqualificado por esse motivo.

### AC-23 — Estado fora de SP

**Dado** lead com Estado RJ
**Então** é entregue normalmente com alerta visual; o vendedor decide manualmente pela desqualificação.

### AC-24 — Negócio ganho

**Dado** lead ativo e comentário válido
**Quando** responsável marcar ganho
**Então** cria uma única venda, transforma empresa em cliente e encerra SLA.

### AC-25 — Permissões do vendedor

**Dado** Renato autenticado
**Então** não consegue consultar leads, métricas ou posição individual de Sandra, nem diretamente pela API.

### AC-26 — Alerta de dois parados

**Dado** contagem elegível passou de 1 para 2
**Então** enviar um alerta ao administrador.
**Quando** subir para 3 no mesmo incidente
**Então** não repetir.
**Quando** cair para 1 e depois voltar a 2
**Então** enviar novo alerta.

### AC-27 — E-mail diário por vendedor

**Dado** Sandra recebeu vários leads desde o último resumo
**Às** 9h
**Então** recebe um único e-mail com somente seus leads.

### AC-28 — Venda única sob repetição

**Dado** dupla submissão do botão negócio ganho com a mesma idempotency key
**Então** existe uma venda e uma resposta idempotente, não duas vendas.

### AC-29 — Concorrência

**Dado** dois novos leads processados simultaneamente
**Então** cada um recebe uma atribuição única e o cursor final é equivalente ao processamento sequencial.

### AC-30 — Administrador não desbloqueia com nota

**Dado** lead atrasado de Jessica
**Quando** administrador escrever nota administrativa
**Então** o atraso e o bloqueio permanecem.

---

## 35. Ordem recomendada de desenvolvimento

Esta ordem é de dependência, não uma autorização automática para implementar.

1. Fundação do repositório, ambientes e qualidade.
2. Backend/API Python, configuração do MongoDB com replica set e modelo de coleções normalizadas.
3. Autenticação, perfis e autorização server-side.
4. Calendário útil e serviço de prazo.
5. Motor transacional da fila com testes concorrentes.
6. Importação idempotente e deduplicação.
7. Campanhas e pendências.
8. Feedbacks, tentativas e bloqueios.
9. Qualificação, conversão e propriedade.
10. Outbox e notificações.
11. Interface do administrador.
12. Interface do vendedor.
13. Dashboards, métricas e exportação.
14. Auditoria, observabilidade e recuperação.
15. Piloto controlado com importação em lotes.
16. Estabilização antes da fase WhatsApp.

---

## 36. Ambientes e entrega

### 36.1 Ambientes

- `development`: dados sintéticos, serviços locais ou projetos separados.
- `staging`: cópia estrutural de produção, sem contatos reais ou com dados anonimizados.
- `production`: dados reais e integrações oficiais.

Nenhum ambiente deve compartilhar chaves administrativas com outro.

### 36.2 CI/CD

- lint;
- typecheck;
- testes unitários;
- testes de banco, transações e autorização;
- build;
- alterações de schema e índices validadas;
- deploy de preview;
- aprovação antes de produção.

### 36.3 Evolução do schema MongoDB

- Nunca alterar silenciosamente um script de evolução já aplicado.
- Uma nova alteração gera um script versionado e idempotente para dados, validações ou índices.
- Toda alteração possui rollback operacional ou plano de recuperação.
- Seed de desenvolvimento separado de produção.

---

## 37. Dependências de configuração para implantação real

Antes do go-live, serão necessários:

- cluster MongoDB com replica set e banco `gerec_leads` para cada ambiente;
- serviço de backend/API Python e workers na Railway;
- projeto Vercel para o cliente Next.js/React;
- planilha Google oficial e nome da aba;
- credencial de leitura da Google Sheets;
- agenda dos jobs Python de integração na Railway;
- provedor SMTP/transacional autorizado para `contato@wtgseguros.com.br`;
- lista anual de feriados nacionais e estaduais de SP;
- domínio/URL final da aplicação;
- política de retenção e backup;
- senhas iniciais ou fluxo de convite dos cinco usuários.

Essas configurações não alteram as regras desta especificação.

---

## 38. Decisões canônicas consolidadas

1. A fila é global e começa em Renato → Sandra → Jessica → Nelma.
2. Todas as campanhas usam todos os vendedores.
3. Um atraso bloqueia novas entregas.
4. A vez perdida não é guardada.
5. Regularização não gera lead normal imediato.
6. Feedback vence em 24 horas úteis e renova periodicamente.
7. Lembrete ocorre 4 horas úteis antes.
8. Fins de semana, feriados nacionais e estaduais de SP não contam.
9. Comentário válido exige 6 caracteres úteis.
10. São 5 tentativas pelo WhatsApp, em dias úteis distintos.
11. Desqualificação é sempre manual.
12. Não converter não é desqualificar.
13. Qualificado significa que houve devolutiva real.
14. Negócio ganho transforma a empresa em cliente.
15. Apenas administrador reverte desqualificação ou venda.
16. Mesmo CNPJ/mesma campanha atualiza; campanha diferente cria nova ocorrência.
17. Primeiro recebedor torna-se proprietário da empresa.
18. Recorrência vai ao proprietário e gera crédito de pulo.
19. Créditos podem atravessar várias rotações.
20. Proprietário bloqueado faz o lead esperar.
21. Administrador pode direcionar temporariamente ou transferir permanentemente.
22. Venda temporária é creditada ao temporário sem mudar proprietário.
23. Campanhas desconhecidas exigem aprovação administrativa.
24. Campanhas pendentes contam como paradas.
25. Documento vazio fica pendente e não conta no alerta de dois parados.
26. O alerta de dois parados é único por incidente.
27. Google Sheets é somente entrada; o sistema nunca escreve nela.
28. Admin overrides prevalecem e mudanças conflitantes exigem análise manual.
29. Sincronização ocorre a cada 5 minutos.
30. Importação inicial é completa e liberada em lotes manuais.
31. Linhas removidas são arquivadas, nunca apagadas.
32. E-mail de atribuição é consolidado e enviado somente ao vendedor responsável.
33. Relatórios administrativos são separados e enviados às 9h.
34. Vendedor vê apenas seus leads, métricas e posição.
35. Somente administrador reordena a fila e gerencia ausências.
36. WhatsApp corporativo compartilhado fica para a fase posterior.
37. A interface é exclusivamente desktop, com largura mínima suportada de 1280 px; tablet e celular ficam fora do escopo funcional.
38. `WTG - Leads.xlsx` é o fixture mock atual A–Q; somente M–P compõem a projeção de origem do vendedor, Q fica excluída, M não é CNPJ real e a planilha definitiva será integrada posteriormente pela fronteira do adapter.

---

## 39. Regra de governança da especificação

Qualquer alteração futura deve registrar:

- regra anterior;
- nova regra;
- motivo;
- impacto em dados existentes;
- impacto em métricas;
- migração necessária;
- novos testes de aceite;
- aprovação de Yago/administrador do produto.

Nenhuma IA ou desenvolvedor deve “melhorar” uma regra de negócio sem apresentar a mudança explicitamente.

### GOV-001 — Interface exclusivamente desktop

- **Regra anterior:** o MVP previa interface responsiva, funcional em desktop, tablet e celular.
- **Nova regra:** o produto é exclusivamente desktop, com largura mínima suportada de 1280 px; tablet e celular ficam fora do escopo funcional.
- **Motivo:** alinhar a experiência ao ambiente operacional aprovado e evitar custo e critérios de aceite para dispositivos que não serão usados.
- **Impacto em dados existentes:** nenhum; a mudança afeta apenas suporte de interface e critérios de apresentação.
- **Impacto em métricas:** nenhum nas fórmulas de negócio; métricas técnicas de uso e qualidade passam a considerar somente o viewport desktop suportado.
- **Migração necessária:** nenhuma migração de dados; documentação, estilos e testes visuais/E2E devem adotar o mínimo de 1280 px.
- **Novos testes de aceite:** validar os fluxos funcionais e a acessibilidade em viewport desktop, incluindo o viewport de referência 1440 × 900; não criar gates funcionais para tablet ou celular.
- **Aprovação:** Yago, em 25 de agosto de 2026.

### GOV-002 — Workbook mock e projeção de origem do vendedor

- **Regra anterior:** o contrato canônico descrevia a planilha definitiva esperada, enquanto a estrutura física da planilha mock atual e a projeção de origem do vendedor não estavam registradas.
- **Nova regra:** `WTG - Leads.xlsx` é o fixture mock atual da aba `Leads`, com headers A–Q definidos na seção 12.10; somente M–P são dados de origem mostrados ao vendedor, Q fica fora dessa projeção, e campos operacionais internos autorizados continuam disponíveis conforme o perfil. A coluna M é uma pergunta/resposta, não um número real de CNPJ. A planilha definitiva será conectada posteriormente pela fronteira do adapter.
- **Motivo:** tornar o fixture atual reproduzível sem confundi-lo com o contrato definitivo nem ampliar a exposição dos dados de origem.
- **Impacto em dados existentes:** nenhum dado é migrado neste registro. Como o mock não fornece CNPJ real, seus registros ainda não satisfazem identidade, deduplicação ou recorrência por CNPJ e não podem ser tratados como produção para essas regras.
- **Impacto em métricas:** as fórmulas aprovadas não mudam; métricas dependentes de identidade por CNPJ só podem ser calculadas quando a origem definitiva fornecer documento real e válido.
- **Migração necessária:** nenhuma agora. Na chegada da planilha definitiva, mapear e validar o novo contrato no adapter, preservando histórico e regras canônicas.
- **Novos testes de aceite:** verificar os 17 headers A–Q e sua ordem; comprovar a projeção M–P e a exclusão de Q; impedir que M seja interpretada como CNPJ; testar a substituição localizada do contrato pelo adapter sem enfraquecer permissões.
- **Aprovação:** Yago, em 25 de agosto de 2026.

### GOV-003 — MongoDB, backend Python e separação de hospedagem

- **Regra anterior:** o núcleo transacional, autenticação e persistência seriam implementados com Supabase/PostgreSQL/RLS; integrações usariam n8n; Vercel hospedaria frontend e APIs compatíveis.
- **Nova regra:** MongoDB é a única persistência, no banco `gerec_leads`, com coleções normalizadas e transações dependentes de replica set. O backend/API Python concentra autenticação, autorização e regras críticas; backend e automações Python idempotentes rodam na Railway. O Next.js/React roda na Vercel exclusivamente como cliente web e nunca acessa MongoDB diretamente. O sistema novo não usa Supabase, PostgreSQL, RLS, `service_role` nem n8n.
- **Motivo:** adotar a infraestrutura aprovada para o sistema novo, com fronteira única de backend, implantação independente do cliente web e automações versionadas em Python.
- **Impacto em dados existentes:** não há migração de dados nesta tarefa documental. Artefatos locais da fundação anterior são legados temporários e não devem receber novas regras ou dados; uma etapa própria definirá sua retirada e qualquer conversão necessária.
- **Impacto em métricas:** nenhum. Fórmulas, dimensões temporais e regras de visibilidade permanecem inalteradas; consultas passam a ser calculadas pela API Python sobre MongoDB.
- **Migração necessária:** criar o modelo normalizado de coleções e índices no banco `gerec_leads`, exigir replica set em todos os ambientes, implementar autenticação/autorização no backend Python e substituir integrações anteriores por jobs/outbox Python na Railway. Não editar migrações legadas nesta mudança.
- **Novos testes de aceite:** comprovar transações multi-documento e rollback em replica set; concorrência equivalente ao processamento sequencial; índices únicos e idempotência; acesso cruzado negado pela API; ausência de conexão ou credencial MongoDB no cliente; reprocessamento seguro de jobs e outbox.
- **Aprovação:** Yago, em 27 de agosto de 2026.

### GOV-004 — Operação comercial, SLA e permissões

- **Regra anterior:** o SLA de 24 horas úteis contava continuamente nos dias elegíveis, sem janela comercial; `desqualificado` era um resultado terminal e exclusivo; o administrador podia registrar notas e corrigir resultados; as contas iniciais configuradas eram Yago, Renato, Sandra, Jessica e Nelma, e as senhas iniciais eram aleatórias.
- **Nova regra:** o SLA continua com 24 horas úteis em `America/Sao_Paulo`, mas acumula tempo somente entre **09:00** (inclusivo) e **18:00** (exclusivo) nos dias úteis elegíveis. Vendedor com ao menos um ciclo aberto vencido fica em estado **Bloqueado por atraso**. Ambos impedem somente novas atribuições e preservam os leads existentes. Pausa manual é definida e removida somente pelo administrador. Bloqueado por atraso é derivado de qualquer ciclo de SLA aberto vencido. Ele cessa automaticamente após a regularização de todos os ciclos vencidos. Quando coexistirem, Pausado prevalece na apresentação e na elegibilidade. A regularização não devolve turnos perdidos. O vendedor atualmente responsável é o único autor de tratativa. Ele registra comentário de pelo menos seis caracteres úteis e uma situação primária `Indefinido`, `Negociação` ou `Ganho`; `isDisqualified` é um marcador adicional que exige o comentário da mesma submissão, pode coexistir com `Ganho` e encerra o SLA sem reabri-lo automaticamente. O administrador possui somente leitura global da tratativa. Ele não edita status, comentário ou responsável nessa tela. As contas aprovadas neste ambiente são Yago e André como administradores; Renato, Sandra, Jessica e Nelma como vendedores. Ao criar ou redefinir uma conta, o administrador informa senha não vazia, sem política adicional de tamanho, composição ou troca forçada nesta etapa.
- **Motivo:** tornar a operação comercial utilizável pelas telas reconstruídas, refletir a jornada de trabalho aprovada, separar bloqueio automático de pausa manual, preservar a dupla classificação comercial solicitada e viabilizar a gestão explícita de usuários.
- **Impacto em dados existentes:** nenhum histórico é apagado. Registros anteriores recebem projeção compatível; ciclos de SLA abertos e lembretes são recalculados de modo idempotente. O estado atual da tratativa, seu contador de comentários e as métricas são materializados a partir do histórico imutável. A conta André deve existir como administradora neste ambiente, sem participação na fila de vendedores.
- **Impacto em métricas:** ganhos e desqualificados passam a ser contabilizados de forma independente, permitindo `Ganho + Desqualificado`. Leads com `isDisqualified` não permanecem em SLA aberto nem bloqueiam vendedor por atraso. Métricas de prazo passam a considerar somente a janela comercial de 09:00–18:00.
- **Migração necessária:** versionar uma migração idempotente que introduza a projeção de situação primária, `isDisqualified`, contador e histórico de tratativas; encerre ciclos de SLA de leads marcados como desqualificados; recalcule prazos abertos pela janela comercial; crie/atualize as seis contas aprovadas com papéis corretos, mantendo hashes de senha e revogando sessões em redefinições. Não apagar eventos, atribuições ou dados comerciais existentes.
- **Novos testes de aceite:** cobrir início antes, na borda, dentro e após 09:00–18:00, incluindo fins de semana e feriados com relógio controlado; validar **Bloqueado por atraso**, regularização sem recuperar turno e pausa manual independente; negar ao administrador criação de comentário ou alteração de situação; exigir comentário válido, permitir `Ganho + Desqualificado` e encerrar o SLA do marcador; validar senha não vazia sem política adicional, redefinição com revogação de sessão e a configuração das contas Yago, André, Renato, Sandra, Jessica e Nelma.
- **Aprovação:** Yago, em 28 de agosto de 2026.

---

### GOV-005 — Transferência manual e revogação de acesso do vendedor anterior

- **Regra anterior:** após transferência, o vendedor anterior podia consultar em leitura os registros históricos produzidos enquanto era responsável.
- **Nova regra:** somente o administrador pode transferir manualmente um lead. A transferência altera apenas o responsável/proprietário do lead, não move o cursor, não altera a ordem FIFO e não cria nem consome créditos. A partir da confirmação, o vendedor anterior perde qualquer acesso ao lead e às tratativas relacionadas, inclusive leitura; o novo responsável passa a ser o único vendedor com acesso operacional.
- **Motivo:** garantir que a propriedade transferida represente também a separação operacional e de confidencialidade entre vendedores.
- **Impacto em dados existentes:** nenhum registro é apagado. Os tratamentos permanecem disponíveis ao administrador para auditoria e ao novo responsável segundo suas permissões; consultas do vendedor anterior deixam de retornar o lead e seus tratamentos.
- **Impacto em métricas:** atribuições e tratativas históricas continuam contabilizadas globalmente; métricas do vendedor anterior deixam de incluir esse lead após a transferência, enquanto métricas administrativas permanecem completas.
- **Migração necessária:** nenhuma migração estrutural; ajustar filtros de autorização e registrar evento de transferência com responsável anterior e novo responsável.
- **Novos testes de aceite:** administrador transfere lead sem alterar cursor/FIFO; vendedor anterior recebe 403 e não vê o lead nem tratamentos; novo responsável vê o lead e pode tratar; auditoria mantém o evento e o histórico.
- **Aprovação:** Yago, em 3 de setembro de 2026.

## 40. Encerramento

O núcleo do produto é uma máquina operacional auditável, não apenas um dashboard. A qualidade da solução dependerá principalmente de quatro pontos:

1. distribuição transacional;
2. separação entre qualificação e conversão;
3. propriedade consistente de empresas recorrentes;
4. proteção de dados e permissões reais no banco.

Uma implementação que tenha uma interface bonita, mas não consiga provar essas quatro propriedades, não atende esta especificação.
### GOV-006 â€” Disponibilidade manual sem SLA operacional

- **Regra anterior:** a GOV-004/DEC-028 previa SLA de 24 horas Ãºteis, lembrete, ciclos de feedback e estado derivado **Bloqueado por atraso**, que impedia novas atribuiÃ§Ãµes.
- **Nova regra:** a disponibilidade operacional possui somente **Ativo** e **Pausado**. Pausado Ã© uma aÃ§Ã£o manual, definida e removida exclusivamente pelo administrador. NÃ£o hÃ¡ prazo, SLA comercial, lembrete, bloqueio automÃ¡tico ou estado Bloqueado por atraso. AusÃªncia de comentÃ¡rio nÃ£o altera fila, elegibilidade ou estado do vendedor. ComentÃ¡rios, situaÃ§Ã£o primÃ¡ria e marcador Desqualificado continuam sendo registrados manualmente pelo vendedor; Desqualificado exige comentÃ¡rio na mesma tratativa.
- **Motivo:** alinhar o sistema Ã  operaÃ§Ã£o real aprovada e remover uma consequÃªncia automÃ¡tica que nÃ£o faz parte do processo comercial atual.
- **Impacto em dados existentes:** nenhum evento, comentÃ¡rio, atribuiÃ§Ã£o ou timestamp histÃ³rico Ã© apagado. Campos/ciclos legados de SLA podem permanecer somente para auditoria, sem serem calculados, exibidos ou usados na elegibilidade corrente.
- **Impacto em mÃ©tricas:** remover prazo, lembrete, atraso e bloqueio das mÃ©tricas operacionais atuais; manter contadores de comentÃ¡rios, situaÃ§Ã£o primÃ¡ria, marcador e atribuiÃ§Ãµes. A fila continua FIFO e transferÃªncia nÃ£o altera cursor.
- **MigraÃ§Ã£o necessÃ¡ria:** versionar ajustes de projeÃ§Ãµes, comandos e contratos para aceitar apenas `active`/`paused`; nÃ£o editar migraÃ§Ãµes aplicadas nem remover dados histÃ³ricos.
- **Novos testes de aceite:** vendedor ativo e pausado sÃ£o os Ãºnicos estados; pausa/ativaÃ§Ã£o manual do administrador funciona; lead sem comentÃ¡rio nÃ£o Ã© bloqueado nem muda de posiÃ§Ã£o; nenhuma tela ou alerta apresenta prazo/SLA/Bloqueado por atraso; comentÃ¡rio vÃ¡lido atualiza apenas tratativa/status/marcador; FIFO permanece inalterado.
- **AprovaÃ§Ã£o:** Yago, em 03 de setembro de 2026.

---

### GOV-007 â€” NotificaÃ§Ãµes internas, situaÃ§Ã£o potencial e relatÃ³rios operacionais

- **Regra anterior:** o SPEC previa notificaÃ§Ãµes de novos leads por e-mail; a situaÃ§Ã£o primÃ¡ria da tratativa era limitada a `Indefinido`, `NegociaÃ§Ã£o` e `Ganho`; a projeÃ§Ã£o atual podia preservar o marcador `Desqualificado` mesmo quando uma tratativa posterior o removesse. A operaÃ§Ã£o nÃ£o possuÃ­a a visÃ£o de relatÃ³rios aprovada nesta etapa.
- **Nova regra:** novos leads sÃ£o avisados por janela interna, exclusiva do vendedor, consultando atribuiÃ§Ãµes e transferÃªncias posteriores ao cursor persistente de leitura do prÃ³prio vendedor. A primeira implantaÃ§Ã£o inicializa esse cursor e nÃ£o notifica leads antigos. Nenhum e-mail Ã© enviado nesta etapa. `Potencial` passa a ser situaÃ§Ã£o primÃ¡ria vÃ¡lida ao lado de `Indefinido`, `NegociaÃ§Ã£o` e `Ganho`. `Desqualificado` continua marcador adicional, mas o estado materializado do lead reflete exatamente a Ãºltima tratativa; retirar a marca em nova tratativa a remove apenas da projeÃ§Ã£o atual e preserva todo o histÃ³rico. Leads sem tratativa recebem destaque visual amarelo sem mudar FIFO, permissÃ£o ou disponibilidade. Administrador pode filtrar leads pelo responsÃ¡vel atual; administrador e vendedor podem ordenar por situaÃ§Ã£o. RelatÃ³rios por situaÃ§Ã£o e proprietÃ¡rio atual sÃ£o exclusivos de administrador e filtram pela data da atribuiÃ§Ã£o atual, que passa a ser a data de transferÃªncia quando houver transferÃªncia.
- **Motivo:** alinhar o sistema Ã  rotina real de acompanhamento sem depender de e-mail, tornar a situaÃ§Ã£o comercial mais expressiva, corrigir a projeÃ§Ã£o divergente do marcador e disponibilizar leitura gerencial segura.
- **Impacto em dados existentes:** criar campo de cursor de leitura no usuÃ¡rio por migraÃ§Ã£o idempotente, inicializado no instante da implantaÃ§Ã£o apenas quando ausente. NÃ£o apagar tratativas, atribuiÃ§Ãµes ou marcaÃ§Ãµes histÃ³ricas. A correÃ§Ã£o da projeÃ§Ã£o vale para novas tratativas; qualquer reparo em massa de dados anteriores exige decisÃ£o e migraÃ§Ã£o prÃ³prias.
- **Impacto em seguranÃ§a e mÃ©tricas:** vendedor consulta e confirma somente sua prÃ³pria janela; transferÃªncia continua revogando o acesso do vendedor anterior. AgregaÃ§Ãµes globais sÃ£o exclusivas de administrador. A janela e o destaque nÃ£o alteram cursor FIFO, posiÃ§Ã£o, crÃ©ditos ou disponibilidade.
- **MigraÃ§Ã£o necessÃ¡ria:** nova migraÃ§Ã£o versionada para cursor ausente e expansÃ£o de validadores/contratos para `potential`; nenhuma migraÃ§Ã£o aplicada pode ser editada.
- **Novos testes de aceite:** validar cursor inicial e concorrente, atribuiÃ§Ã£o e transferÃªncia futuras, negaÃ§Ã£o de acesso cruzado, `Potencial`, remoÃ§Ã£o do marcador atual preservando histÃ³rico, destaque de primeiro comentÃ¡rio, filtro/ordenaÃ§Ã£o autorizados e relatÃ³rios exclusivos de administrador por atribuiÃ§Ã£o atual.
- **AprovaÃ§Ã£o:** Yago, em 14 de setembro de 2026.

## Documento de orientação: `AGENTS.md`

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
- Regras críticas vivem em comandos transacionais do MongoDB, protegidos por índices, escritas condicionais, locks lógicos e testes.
- Não coloque lógica de negócio crítica em controllers, handlers, componentes React ou workflows do n8n.
- O n8n atua como adaptador de Google Sheets, agendas e notificações.
- Google Sheets é somente origem; o sistema nunca escreve na planilha.
- A planilha definitiva continua uma dependência posterior. Mantenha o contrato físico da origem atrás do adapter e não enfraqueça identidade, deduplicação ou recorrência por CNPJ para acomodar o mock.
- Toda mudança de banco usa nova migração versionada. Nunca edite uma migração já aplicada.
- RLS deve proteger os dados no banco; ocultar elementos na interface não é controle de acesso.
- `MONGODB_URI`, `MONGODB_DATABASE`, `APP_SECRET` e demais segredos nunca podem chegar ao navegador.

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
- banco e segurança: práticas de transações, índices e segredos do MongoDB;
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

## Documento de orientação: `README.md`

# Gerenciador de Leads WTG

O produto usa MongoDB como único banco, API e automações Python na Railway e cliente Next.js na Vercel. Leia `AGENTS.md` e `SPEC_GERENCIADOR_DE_LEADS_WTG.md` antes de alterar o sistema.

## Pré-requisitos

- Node.js 24 LTS e npm para o cliente web.
- Python 3.12 ou 3.13 para API e workers.
- Docker Desktop para o replica set MongoDB local.

## Configuração local

Instale dependências uma vez:

```powershell
npm ci
cd apps/api
python -m pip install -e ".[dev]"
cd ../..
```

Defina as variáveis server-side somente no processo do backend ou worker. Use `apps/api/.env.example` como referência; os valores abaixo são placeholders locais, não credenciais reais:

```powershell
$env:MONGODB_URI = "mongodb://127.0.0.1:27017/?replicaSet=rs0"
$env:MONGODB_DATABASE = "gerec_leads"
$env:APP_SECRET = "replace-with-a-local-secret"
```

Defina a variável pública somente no processo web:

```powershell
$env:NEXT_PUBLIC_API_URL = "http://127.0.0.1:8000"
```

## Serviços locais

Em terminais separados, execute:

```powershell
npm run mongodb:start
npm run mongodb:bootstrap
npm run api:start
npm run web:start
npm run worker:start
```

`npm run start:local` inicia MongoDB, aplica o bootstrap e abre API e web em segundo plano. O worker continua um processo separado porque depende do webhook de entrega configurado para o ambiente. Para encerrar o banco, execute `npm run mongodb:stop`; acrescente `-RemoveVolumes` ao chamar `scripts/stop-mongodb.ps1` diretamente quando quiser apagar dados locais.

O cliente web recebe somente `NEXT_PUBLIC_API_URL`. `MONGODB_URI`, `MONGODB_DATABASE` e `APP_SECRET` pertencem exclusivamente à API e aos workers Python; nunca os adicione ao ambiente Vercel ou a arquivos versionados.

## Verificação

```powershell
python -m pytest apps/api/tests -q
npm run lint
npm run typecheck
npm run test
npm run test:contracts
npm run build
npm run test:e2e
```

Consulte `infra/railway/README.md` para os comandos e variáveis de cada serviço Railway.

## Documento de orientação: `ROADMAP.md`

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

## Documento de orientação: `docs/ARQUITETURA.md`

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

## Documento de orientação: `docs/DECISOES.md`

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
| DEC-012 | Vendedor vê somente seus dados. | Regra substituída pela DEC-029 para transferência de propriedade: após a transferência, o vendedor anterior perde qualquer acesso ao lead e às tratativas relacionadas. | Substituída pela DEC-029 |
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
| DEC-028 | A operação comercial usa SLA de 24 horas úteis apenas entre 09:00 e 18:00; `isDisqualified` é marcador adicional que encerra o SLA. Ambos impedem somente novas atribuições e preservam os leads existentes. Pausa manual é definida e removida somente pelo administrador. Bloqueado por atraso é derivado de qualquer ciclo de SLA aberto vencido. Ele cessa automaticamente após a regularização de todos os ciclos vencidos. Quando coexistirem, Pausado prevalece na apresentação e na elegibilidade. A regularização não devolve turnos perdidos. O vendedor atualmente responsável é o único autor de tratativa. O administrador possui somente leitura global da tratativa. | Vendedor atrasado fica Bloqueado por atraso sem redistribuir leads; ganhos e desqualificados são métricas independentes. As contas aprovadas neste ambiente são Yago, André, Renato, Sandra, Jessica e Nelma: Yago e André são administradores; os demais são vendedores. Criação e redefinição aceitam senha não vazia, sem política adicional. Histórico é preservado, e prazos, projeções e métricas são recalculados idempotentemente por migração. Administrador não edita comentário, status ou responsável da tratativa. | Aprovada em 28/08/2026 |
| DEC-029 | Transferência manual de propriedade não altera o cursor ou a ordem FIFO; após a confirmação, o vendedor anterior perde totalmente o acesso ao lead e às tratativas, inclusive leitura. | A transferência é exclusiva do administrador, auditável e preserva os dados para auditoria administrativa e para o novo responsável. | Aprovada em 03/09/2026 |
| DEC-030 | A disponibilidade operacional possui somente `Ativo` e `Pausado`. `Pausado` Ã© definido e removido manualmente pelo administrador. NÃ£o existe prazo/SLA comercial, lembrete, estado `Bloqueado por atraso` ou bloqueio automÃ¡tico por ausÃªncia de comentÃ¡rio. | Alinhar o produto Ã  operaÃ§Ã£o real: tratativas, situaÃ§Ã£o comercial e marcador de desqualificaÃ§Ã£o sÃ£o registrados manualmente pelo vendedor, sem consequÃªncia automÃ¡tica por demora. A DEC-028 fica superada somente nesses pontos; seus demais controles de permissÃ£o, contas e tratativa permanecem vÃ¡lidos. HistÃ³ricos e campos legados de SLA sÃ£o preservados apenas para auditoria, sem uso operacional. | Aprovada em 03/09/2026 |
| DEC-031 | Novos leads serÃ£o avisados por janela interna persistente por vendedor, e nÃ£o por e-mail nesta etapa. `Potencial` Ã© situaÃ§Ã£o primÃ¡ria vÃ¡lida. O marcador `Desqualificado` materializado reflete a Ãºltima tratativa e pode ser removido sem alterar o histÃ³rico. RelatÃ³rios por situaÃ§Ã£o e proprietÃ¡rio atual sÃ£o exclusivos de administrador e usam a data da atribuiÃ§Ã£o atual. | A janela usa cursor persistente, inclui atribuiÃ§Ãµes e transferÃªncias futuras e nÃ£o altera FIFO. Leads sem tratativa recebem somente destaque visual. Filtro administrativo por responsÃ¡vel e ordenaÃ§Ã£o alfabÃ©tica por situaÃ§Ã£o sÃ£o consultas de leitura autorizadas no backend. O desenho de e-mail de 03/09/2026 nÃ£o serÃ¡ executado neste pacote. | Aprovada em 14/09/2026 |

## Desenho de produto: `docs/superpowers/specs/2026-08-25-organizacao-roadmap-design.md`

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

## Desenho de produto: `docs/superpowers/specs/2026-08-25-workbook-mock-fluxo-completo-design.md`

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


## Desenho de produto: `docs/superpowers/specs/2026-08-27-migracao-mongodb-design.md`

# Migração do Gerenciador de Leads para MongoDB

**Data:** 27 de agosto de 2026
**Status:** desenho aprovado em conversa; aguardando revisão escrita antes da implementação
**Banco alvo:** MongoDB, database `gerec_leads`

## 1. Decisão e governança

O banco principal do Gerenciador de Leads será MongoDB. A aplicação não usará Supabase, PostgreSQL, Supabase Auth ou RLS.

### Regra anterior

O SPEC definia Next.js/React + Supabase Auth/PostgreSQL/RLS como arquitetura principal, com o PostgreSQL concentrando consistência, concorrência, permissões e comandos críticos.

### Nova regra proposta

Next.js/React será o site publicado na Vercel. Uma API/backend Python na Railway será o único núcleo de autenticação, domínio, persistência e automações. MongoDB será a única infraestrutura de dados, incluindo usuários, sessões, dados comerciais, fila, histórico, auditoria e outbox. As regras críticas serão comandos Python executados em transações MongoDB.

### Motivo

O produto será operado no MongoDB recém-criado para este sistema. O database está vazio, portanto não existe migração de dados comerciais a preservar.

### Impacto em dados

Nenhum dado será migrado. O workbook continua sendo mock de origem e a coluna `você_tem_cnpj_ou_mei?` não será interpretada como CNPJ real.

### Impacto técnico

- substituir migrations SQL por criação versionada de índices e validações MongoDB;
- substituir RLS por autorização no backend Python e filtros obrigatórios nos repositórios;
- substituir Supabase Auth por autenticação própria no backend Python;
- exigir MongoDB replica set para transações locais, staging e produção;
- publicar o site Next.js na Vercel e a API/worker Python na Railway;
- executar sincronizações, notificações e tarefas agendadas exclusivamente na Railway;
- atualizar tooling, testes, documentação e CI;
- manter as regras funcionais do SPEC, salvo aprovação posterior registrada.

### Testes novos ou ajustados

Serão necessários testes de índices, transações, rollback, idempotência, concorrência, autorização por papel, sessões revogadas e isolamento de vendedor. Os 30 critérios de aceite do SPEC continuam válidos.

## 2. Arquitetura aprovada

```text
Navegador
  -> site Next.js na Vercel
  -> API/backend Python na Railway
  -> adapter MongoDB
  -> MongoDB replica set (database gerec_leads)
```

O navegador nunca acessa o MongoDB diretamente. O frontend não decide atribuição, cursor, propriedade, SLA, créditos ou venda; ele chama a API Python autorizada.

Módulos e responsabilidades:

- `web`: apresentação Next.js e experiência desktop na Vercel;
- `auth`: usuários, derivação de senha, sessões, revogação e autorização no backend Python;
- `leads`: origem, normalização, deduplicação, campanhas, empresas e ocorrências;
- `queue`: cursor global, elegibilidade, rodízio, pausas e créditos de pulo;
- `operations`: feedbacks, SLA, tentativas, qualificação, conversão e vendas;
- `audit`: histórico imutável e auditoria;
- `notifications`: outbox, reprocessamento e integrações;
- `automation`: sincronização da origem, e-mails, alertas e tarefas agendadas na Railway;
- `mongo`: conexão, transações, índices e repositórios.

Cada módulo de domínio expõe uma interface pequena e profunda. A API Python e o worker de automações reutilizam essas mesmas interfaces. O adapter MongoDB fica atrás de uma seam única, permitindo testes com banco real e adapter em memória controlado.

## 2.1. Implantação

- Vercel hospeda somente o site Next.js e seus assets públicos;
- Railway hospeda a API Python e os workers/agendamentos Python;
- MongoDB é compartilhado por API e workers através de URI server-side;
- nenhum segredo ou URI do MongoDB chega ao bundle do navegador;
- ambientes local, staging e produção usam URIs, credenciais e bancos isolados.

## 3. Coleções do database `gerec_leads`

- `users`: identidade, e-mail normalizado, senha derivada, papel, ativo e posição;
- `sessions`: hash do token, usuário, criação, expiração e revogação;
- `queue_state`: documento singleton com cursor global e versão;
- `seller_queue`: posição, pausa e estado operacional;
- `skip_balances`: créditos compensatórios;
- `campaigns`: identidade externa, nomes e aprovação;
- `companies`: documento normalizado, dados, proprietário e status de cliente;
- `leads`: ocorrência única ativa por empresa + campanha, estados e SLA;
- `source_records`: linhas da origem, hash, presença e payload normalizado;
- `assignments`: histórico de responsáveis, tipo, período e idempotência;
- `feedback_cycles`: ciclos de 24 horas úteis, lembrete e vencimento;
- `feedbacks`: comentários operacionais válidos;
- `contact_attempts`: tentativas WhatsApp em dias úteis distintos;
- `qualification_events`: qualificação, desqualificação, reversão e motivos;
- `sales`: negócio ganho único por lead e vendedor creditado;
- `holidays`: feriados nacionais e de São Paulo;
- `notification_outbox`: eventos pendentes, tentativas e idempotência;
- `audit_log`: ator, ação, entidade, antes/depois e correlation ID;
- `system_settings`: fuso, SLA, lembrete, limiar e horário de resumo.

A coleção vazia atualmente chamada `gerec_leads` não concentrará todo o domínio. A coleção operacional de ocorrências será `leads`.

Índices únicos e validações devem garantir, no mínimo: e-mail, `sourceLeadId`, CNPJ válido quando presente, empresa + campanha ativa, uma atribuição atual, uma venda ativa, uma tentativa por lead/data útil, saldo não negativo e idempotência de comandos.

## 4. Comandos transacionais

Os comandos críticos usam uma transação MongoDB única e registram alteração, histórico, auditoria e outbox no mesmo commit:

- distribuir lead normal;
- atribuir recorrência;
- registrar feedback ou tentativa;
- qualificar, desqualificar ou encerrar sem conversão;
- registrar ou reverter negócio ganho;
- transferir proprietário;
- direcionar temporariamente;
- pausar, reativar ou reordenar a fila;
- importar linha idempotente e arquivar linha removida.

Cada comando recebe `idempotencyKey`. Repetição devolve o resultado original sem criar novo evento operacional.

O cursor da fila usa documento singleton, controle de versão e transação. O algoritmo preserva rodízio global, perda de vez, bloqueio por atraso, créditos de pulo, recorrência e FIFO conforme o SPEC.

## 5. Autenticação e autorização

Usuários e sessões serão armazenados no MongoDB. Senhas nunca serão persistidas em texto puro; será usado Argon2id ou scrypt com parâmetros configuráveis.

Sessões usarão token opaco em cookie `httpOnly`, `secure` em produção, `sameSite=lax`, expiração e revogação server-side. Usuário desativado não poderá iniciar sessão, consultar dados ou executar comandos.

O papel será verificado no servidor em toda ação. Repositórios receberão o contexto autorizado e aplicarão filtros de escopo, garantindo que vendedores só consultem seus leads e histórico permitido, inclusive por chamadas diretas.

## 6. Falhas e observabilidade

Erros serão classificados como validação, autorização, conflito de estado, duplicidade/idempotência, indisponibilidade do MongoDB ou falha posterior de notificação.

Falha de e-mail não desfaz a operação confirmada; o evento permanece na outbox para retry. Logs estruturados não registrarão senhas, tokens ou payloads pessoais completos.

MongoDB local, staging e produção terão replica set, URI isolada, credenciais separadas, backup e restauração testados.

## 7. Estratégia de testes

- unitários: normalização, calendário útil, SLA, elegibilidade, créditos e métricas;
- integração: índices, constraints, transações, rollback e outbox;
- concorrência: distribuições simultâneas com resultado equivalente ao sequencial;
- autorização: admin, vendedor, histórico pós-transferência e usuário desativado;
- E2E: login, dashboard, fila, feedback, tentativa, qualificação, conversão e exportação;
- relógio controlável: fins de semana, feriados e vencimentos;
- recuperação: backup e restauração antes do piloto.

## 8. Sequência de implementação

1. atualizar SPEC, decisões e arquitetura para a governança MongoDB/Vercel/Railway;
2. remover Supabase e criar configuração do site Vercel e da API Python;
3. criar adapter, conexão, replica set local e índices;
4. implementar autenticação e sessões no backend Python;
5. implementar coleções e repositórios, começando por `leads`;
6. migrar comandos transacionais de fila, SLA, propriedade e resultados para Python;
7. implementar automações Python, adapter do workbook e importação idempotente;
8. adaptar o site Next.js para consumir a API Python;
9. concluir testes unitários, integração, concorrência e E2E;
10. validar deploy Vercel/Railway, backup, restauração e piloto.

Nenhuma implementação começa antes da revisão escrita deste documento.

## Desenho de produto: `docs/superpowers/specs/2026-08-28-reconstrucao-interacoes-sla-design.md`

# Reconstrução das interações, status e SLA — desenho

**Status:** aprovado para implementação em 28 de agosto de 2026; formalizado por GOV-004 e DEC-028.
**Produto:** Gerenciador de Leads WTG
**Aprovação de produto:** Yago, 28 de agosto de 2026.

## Objetivo

Transformar as telas atuais, que exibem dados parciais e controles sem ação, em uma operação funcional: administrador gerencia usuários e consulta a tratativa; vendedor trata apenas seus leads, registra comentário e altera a situação comercial; a fila gira de acordo com o cursor real e com a elegibilidade de cada vendedor.

## Decisões aprovadas

### 1. SLA, bloqueio automático e pausa manual

- O prazo de feedback continua sendo de **24 horas úteis**, no fuso `America/Sao_Paulo`.
- Só acumulam horas de **09:00 (inclusivo) até 18:00 (exclusivo)**, em segunda a sexta-feira que não seja feriado nacional ou estadual de São Paulo. Feriado municipal permanece fora do MVP.
- Exemplo: uma atribuição na sexta às 17:00 consome uma hora até 18:00; restam 23 horas úteis a partir das 09:00 da próxima data útil.
- Quatro horas úteis antes do vencimento gera o lembrete já previsto.
- Um vendedor com pelo menos um lead ativo atrasado fica **Bloqueado por atraso**. Isso impede somente novas atribuições; seus leads atuais continuam com ele e não são redistribuídos.
- O bloqueio é calculado a partir dos prazos em aberto, sem botão administrativo. Depois de comentário válido em todos os leads atrasados, o vendedor volta a estar elegível na próxima vez natural do cursor; não recupera turnos perdidos.
- **Pausado** é estado manual, definido por administrador. Também impede novas atribuições, preserva os leads existentes e só termina quando o administrador ativa o vendedor.
- A interface deve mostrar separadamente `Ativo`, `Pausado` e `Bloqueado por atraso`, com texto acessível além de cor.

### 2. Comentário e situação comercial

- Somente o vendedor atualmente responsável registra comentário e muda a situação de seu lead. Administrador tem leitura global, sem editar status, comentário ou responsável por essa tela.
- Todo comentário exige texto com no mínimo seis caracteres úteis e a seleção explícita de uma situação primária: `Indefinido`, `Negociação` ou `Ganho`.
- `Desqualificado` é um marcador adicional, não substitui a situação primária. Portanto, `Ganho + Desqualificado` é válido e conta tanto como ganho quanto como desqualificado nas métricas solicitadas.
- Marcar `Desqualificado` exige o comentário da mesma submissão. Não há lista obrigatória de motivos nesta etapa.
- Marcar `Desqualificado` encerra imediatamente o ciclo de SLA daquele lead, independentemente da situação primária. Ele deixa de exigir feedback periódico e não pode bloquear o vendedor por atraso. Uma tratativa posterior pode atualizar a situação primária, inclusive para `Ganho`, preservando o marcador e o histórico; ela não reabre o SLA automaticamente.
- Cada submissão gera evento imutável, preservando autor, data/hora, texto, situação primária e marcador. O lead materializa apenas o estado atual e o contador de comentários para leitura rápida.
- O histórico mostra cada tratativa; o contador aparece na tabela de leads e na visão do vendedor.

### 3. Usuários e fila

- A área administrativa terá ações reais, com confirmação e retorno de sucesso/erro: criar usuário, pausar/ativar vendedor e redefinir senha.
- Criar usuário solicita nome, e-mail, papel e senha inicial. E-mail é único; senha nunca é retornada pela API nem exibida após o salvamento.
- A senha inicial e a redefinição exigem somente valor não vazio. Não há comprimento mínimo, composição obrigatória ou troca forçada nesta etapa.
- Um novo vendedor ativo entra ao final da fila global. Um novo administrador não entra na fila.
- Redefinir senha recebe a nova senha e salva. As sessões ativas do usuário redefinido serão revogadas por segurança.
- Pausar/ativar muda apenas a disponibilidade manual. Não transfere leads existentes.
- A fila é derivada da ordem persistida, cursor real e disponibilidade atual. Após uma atribuição, o cursor avança e todas as telas passam a apresentar o próximo vendedor elegível; ela não é uma lista fixa decorativa.
- Administrador vê sequência completa, cursor e motivo de indisponibilidade. Vendedor vê somente sua posição/estado, sem dados dos demais.

### 4. Interface desktop

- As páginas administrativas permanecem: Visão geral, Fila, Histórico e Usuários. A página do vendedor mostra seus leads e sua situação na fila.
- A tabela de leads passa a conter somente informações operacionais inteligíveis: nome, vendedor responsável, empresa, campanha, telefone, e-mail, situação comercial, marcador de desqualificação, prazo e contador de comentários.
- IDs técnicos deixam de ser o conteúdo principal. Quando nome de empresa/campanha não existir na origem, a tela exibe `Não informado`, sem inventar um nome.
- Telefone brasileiro deve ser apresentado como `(DD) 9XXXX-XXXX`, removendo o código de país `55` quando este vier na origem.
- Tabelas de fila, histórico e usuários terão botões reais de anterior/próxima; botões indisponíveis terão semântica e aparência de desabilitados, sem parecer texto quebrado.
- O modal de comentário oferece texto, situação primária, marcador de desqualificação e histórico daquele lead. Administrador recebe somente o histórico em modo leitura.
- A tela não terá mais o controle de teste “Simular entrada de leads”.

## Arquitetura proposta

### Módulo de operação comercial

Criar um módulo de domínio no backend que concentra três comandos: `registrar_tratativa`, `calcular_disponibilidade` e `atualizar_usuario`. As rotas HTTP apenas autenticam, validam formato e chamam esse módulo. Ele preserva transação, propriedade do lead, auditoria e efeitos derivados (novo ciclo de SLA, contador e cursor).

O modelo do lead mantém os campos antigos para compatibilidade de leitura, mas passa a ter estado comercial explícito:

```text
commercialStatus: "undefined" | "negotiation" | "won"
isDisqualified: boolean
commentCount: integer >= 0
lastCommentAt: datetime | null
feedbackDueAt: datetime | null
```

Uma coleção/evento de tratativas conserva o histórico imutável. A interface consome uma projeção de leitura enriquecida pelo backend, nunca decide SLA, elegibilidade, proprietário ou cursor no navegador.

### Cálculo de tempo útil

Um único módulo de calendário recebe horário inicial, duração e calendário de feriados. Sua interface atende tanto vencimento de 24 horas quanto lembrete de quatro horas. Ele avança apenas dentro da janela `[09:00, 18:00)` em dias elegíveis, permitindo relógio controlado nos testes.

### Projeções de leitura

O `DashboardService` passa a devolver contratos específicos para `admin` e `seller`:

- lead com nomes resolvidos, vendedor, prazo, estado comercial, marcador, contagem e permissões;
- fila com posição derivada do cursor, disponibilidade e motivo;
- histórico de atribuições e histórico de comentários enriquecidos;
- métricas que contam ganhos e desqualificados de forma independente, permitindo a dupla classificação aprovada.

## Alterações de governança a registrar no SPEC

Após a revisão deste documento, registrar uma decisão de governança com estas mudanças explícitas:

| Regra anterior | Nova regra | Impacto |
| --- | --- | --- |
| O relógio de SLA contava continuamente em dia útil, sem janela comercial. | Conta somente 09:00–18:00 em dias úteis elegíveis. | Recalcular prazos abertos e lembretes; adicionar testes de borda da janela. |
| `desqualificado` era terminal e exclusivo; administrador podia revertê-lo. | É marcador adicional a `Indefinido`, `Negociação` ou `Ganho`; vendedor o registra junto de comentário e encerra o SLA. | Separar situação primária e marcador; métricas podem contar ambos e ciclos abertos precisam ser encerrados. |
| Administrador podia registrar notas/corrigir resultado conforme SPEC atual. | Nesta operação, administrador consulta status e comentários, sem editar tratativa. | Bloquear comandos administrativos de status/comentário e testar autorização. |
| Senha inicial era aleatória. | Administrador informa senha não vazia ao criar e ao redefinir usuário. | Manter hash e revogar sessões na redefinição; não impor política de tamanho ou composição nesta etapa. |

Nenhum dado histórico será apagado. Registros antigos recebem projeção compatível; o estado atual e as métricas serão recalculados de modo idempotente durante a migração.

## Critérios de aceite e testes

1. Cálculo de 24 h e lembrete de 4 h cobre início antes/na/dentro/depois da janela, fins de semana e feriados, com relógio controlado.
2. Um lead vencido bloqueia vendedor automaticamente; regularização de todos os atrasos o libera sem recuperar turno; pausa manual permanece independente.
3. Vendedor não vê nem altera lead de outro vendedor; administrador lê tudo, mas recebe erro ao tentar criar comentário ou mudar situação.
4. Comentário com menos de seis caracteres falha; todo comentário persiste situação primária; desqualificação sem comentário falha; `Ganho + Desqualificado` atualiza as duas métricas; desqualificação encerra o SLA e não bloqueia o vendedor.
5. Criar vendedor coloca-o ao final da fila; pausar/ativar preserva leads; senha não vazia é aceita sem política adicional; redefinição de senha invalida sessão anterior; senha não aparece em resposta ou log.
6. Paginação anterior/próxima funciona nas quatro telas administrativas e não exibe controles falsamente interativos.
7. E2E em 1440 × 900 valida administrador e vendedor, com captura visual das ações reais e verificação de que não há IDs técnicos como rótulo principal.

## Fora deste corte

- envio de e-mails e notificações;
- integração com a planilha definitiva além do adapter já existente;
- alteração de proprietário, campanhas, regras de recorrência e créditos de pulo;
- suporte a tablet/celular.

## Desenho de produto: `docs/superpowers/specs/2026-09-03-alertas-email-leads-design.md`

# Design — Alertas de novos leads por e-mail

**Data:** 03/09/2026
**Status:** Design aprovado em conversa; aguardando revisão do documento antes do plano de implementação.
**Escopo:** alertas operacionais por e-mail e normalização de horários exibidos.

## 1. Objetivo

Enviar alertas úteis aos vendedores sem alterar a lógica da fila, a atribuição transacional ou as permissões.

Existem dois fluxos:

1. novos leads atribuídos por uma execução de sincronização: um resumo por vendedor e por sincronização;
2. transferência manual de propriedade: um aviso individual imediato ao novo proprietário.

Uma falha de e-mail nunca desfaz uma atribuição, uma transferência, uma alteração de status ou qualquer outro efeito comercial confirmado.

## 2. Decisões aprovadas

- O resumo de uma sincronização agrupa todos os leads novos recebidos pelo mesmo vendedor naquela execução.
- Não haverá um e-mail por lead dentro de uma sincronização.
- Uma transferência manual gera um aviso individual ao novo proprietário.
- O remetente é `contato@wtgseguros.com.br`.
- O SMTP é `smtp.oncorretor.com.br`, porta `587`.
- A conexão usa STARTTLS obrigatório.
- Usuário SMTP: `contato@wtgseguros.com.br`.
- Senha SMTP: variável de ambiente exclusiva da Railway.
- Nenhuma credencial fica no código, MongoDB, navegador, documentação pública ou logs.
- O conteúdo contém somente nome do lead, telefone e link para o dashboard.
- Não incluir campanha, e-mail do lead ou outros campos de origem.
- A URL do dashboard vem de configuração por ambiente.
- Datas, quando exibidas, usam `America/Sao_Paulo`.
- O horário sem fuso da planilha é horário local de São Paulo.
- Instantes são armazenados em UTC e devolvidos com offset explícito.
- O administrador acompanha falhas e pendências, mas não edita tratativas de vendedor.

## 3. Arquitetura existente aproveitada

O projeto já possui:

- `SyncJob`, responsável por importar e disparar atribuições;
- comandos transacionais da fila;
- coleção MongoDB `notification_outbox`;
- `MongoOutboxRepository` com claim atômico;
- `OutboxWorker` com retry, lock, idempotência e dead-letter;
- `WebhookDeliveryAdapter` como fronteira atual de entrega;
- auditoria e eventos de atribuição.

Não criar um segundo sistema de fila ou uma integração paralela fora da outbox.

## 4. Fluxo de resumo da sincronização

1. A sincronização recebe um `syncRunId` determinístico e não vazio.
2. Cada atribuição automática permanece em sua própria transação da fila.
3. O evento de atribuição gravado na outbox recebe `syncRunId`, `sellerId`, `leadId`, tipo da atribuição e chave idempotente.
4. O evento também identifica o grupo lógico `assignment-summary:{syncRunId}:{sellerId}`.
5. Um agregador consulta eventos pendentes do mesmo grupo.
6. O agregador resolve o e-mail atual do vendedor e os dados mínimos de cada lead.
7. A lista é ordenada de forma determinística por instante de atribuição e identificador do lead.
8. Se o grupo não tiver leads, nenhum e-mail é enviado.
9. O adapter SMTP monta uma mensagem HTML acessível e uma parte texto simples.
10. O worker envia o resumo usando STARTTLS.
11. Somente após confirmação de sucesso todos os eventos do grupo são marcados como enviados.
12. Uma nova tentativa encontra a mesma chave idempotente e não cria outro grupo lógico.

O agregador não pode marcar eventos como enviados antes do SMTP confirmar sucesso.

## 5. Fluxo de transferência manual

1. O administrador confirma a transferência pela operação existente.
2. A transação mantém as regras atuais: não altera cursor, ordem FIFO ou créditos.
3. A transação grava o evento `lead.owner_transferred` na outbox.
4. O evento usa chave `owner-transfer:{leadId}:{commandId}`.
5. O destinatário é o novo responsável ativo no momento do preparo do envio.
6. O worker monta um e-mail individual com nome, telefone e link para o dashboard.
7. O antigo vendedor continua sem qualquer acesso operacional ao lead, conforme a decisão vigente.
8. O histórico permanece disponível para administração e novo responsável.

Transferência não deve entrar no resumo de uma sincronização.

## 6. Contrato dos eventos

### 6.1 Resumo de atribuição

```json
{
  "eventType": "lead.assignment_email_requested",
  "syncRunId": "sync-2026-09-03-001",
  "sellerId": "...",
  "groupKey": "assignment-summary:sync-2026-09-03-001:...",
  "leadIds": ["..."],
  "idempotencyKey": "assignment-summary:sync-2026-09-03-001:..."
}
```

O payload persistido deve conter identificadores e metadados operacionais, não cópia desnecessária de dados pessoais.

### 6.2 Transferência

```json
{
  "eventType": "lead.owner_transfer_email_requested",
  "leadId": "...",
  "sellerId": "...",
  "idempotencyKey": "owner-transfer:...:..."
}
```

O worker busca nome e telefone atuais no momento de preparar a mensagem. Se o lead tiver sido arquivado ou estiver sem telefone, a regra de fallback deverá ser definida no plano e coberta por teste; não inventar dados.

## 7. Adapter SMTP

Criar uma fronteira testável, independente do domínio:

- recebe uma mensagem já renderizada;
- abre conexão com host e porta configurados;
- inicia STARTTLS;
- autentica com usuário e senha server-side;
- envia remetente, destinatário, assunto e partes MIME;
- fecha a conexão mesmo em erro;
- transforma falhas de rede/autenticação em erro de entrega para retry.

O worker não deve conter regra de negócio de fila, status comercial ou propriedade.

Configuração prevista, com nomes finais definidos no plano:

- `SMTP_HOST=smtp.oncorretor.com.br`;
- `SMTP_PORT=587`;
- `SMTP_USERNAME=contato@wtgseguros.com.br`;
- `SMTP_PASSWORD`;
- `SMTP_FROM=contato@wtgseguros.com.br`;
- `DASHBOARD_PUBLIC_URL`.

Valores de produção não devem ser commitados.

## 8. Templates

### 8.1 Resumo de novos leads

Assunto:

`Chegaram leads novos para você — WTG`

Texto base:

```text
Chegaram leads novos para você!!!

As informações dos novos leads já estão no gerenciador de leads.

{nome do lead}
{telefone do lead}
{link para acesso}
```

Para vários leads, repetir o bloco de nome, telefone e link, sem expor identificadores internos.

### 8.2 Transferência

Assunto:

`Lead transferido para você — WTG`

Texto base:

```text
Um lead foi transferido para você.

{nome do lead}
{telefone do lead}
{link para acesso}
```

Os templates terão versão HTML e texto simples. O link aponta para o dashboard configurado e não deve incluir dados sensíveis na URL.

## 9. Idempotência e concorrência

- `syncRunId` identifica uma execução completa.
- `groupKey` identifica um resumo por vendedor dentro da execução.
- Índice único impede dois grupos iguais.
- Claim atômico impede dois workers de processarem o mesmo evento simultaneamente.
- Lock expirado permite recuperação de worker interrompido.
- Retry usa backoff e limite configurado.
- Dead-letter registra evento, chave, tipo e erro resumido.
- O envio duplicado por uma falha após o SMTP e antes do `mark_sent` deve ser tratado como risco de entrega externa; o adapter deve usar a chave idempotente quando o provedor suportar. O plano deve documentar esse limite operacional.

## 10. Política de falhas

- Timeout/conexão recusada: retry.
- Erro temporário SMTP: retry.
- Falha de autenticação: retry limitado e alerta técnico.
- Destinatário inválido: dead-letter, sem desfazer o negócio.
- Vendedor desativado antes do preparo: evento não é enviado automaticamente; fica rastreável para decisão administrativa.
- Lead sem dados mínimos: falha explícita e segura, sem fabricar conteúdo.
- Falha de consulta ao MongoDB: retry do evento.

Logs devem conter somente `eventId`, `eventType`, `groupKey`, tentativa, status e erro técnico truncado. Nunca registrar senha, token ou corpo integral do lead.

## 11. Contrato de horário

- Timestamp ingênuo da planilha: `America/Sao_Paulo`.
- Timestamp com `Z` ou offset: respeitar o offset informado.
- Persistência: UTC.
- API: ISO 8601 com `Z` ou offset.
- Frontend: `Intl.DateTimeFormat` em `America/Sao_Paulo`.
- E-mail: mesma conversão, se datas forem incluídas.

O plano deve localizar todos os parsers e formatadores, sem alterar registros legados sem evidência da semântica original. Qualquer correção histórica precisa de migração versionada, relatório de afetados e rollback operacional.

## 12. Testes obrigatórios

### Domínio e integração

- uma sincronização com vários leads para um vendedor produz um resumo único;
- dois vendedores na mesma sincronização produzem dois grupos;
- sincronização sem novas atribuições não produz e-mail;
- recorrências atribuídas automaticamente entram no resumo quando forem novas atribuições daquela execução;
- transferências ficam fora do resumo;
- transferência cria aviso individual para o novo responsável;
- repetição da mesma sincronização não cria grupo duplicado;
- dois workers concorrentes não enviam dois grupos lógicos;
- atribuição permanece confirmada se SMTP falhar;
- erro de SMTP retorna ao retry e depois dead-letter;
- vendedor sem e-mail válido é rastreável;
- payload não contém campanha, e-mail do lead ou segredo.

### SMTP

- usa host e porta corretos;
- exige STARTTLS;
- autentica com variáveis de ambiente;
- envia remetente aprovado;
- produz MIME HTML + texto simples;
- encerra conexão em sucesso e erro;
- não registra credenciais.

### Horário

- `14:11` sem fuso permanece `14:11` em São Paulo;
- `17:11Z` aparece como `14:11` em São Paulo;
- timestamps com offset diferente são convertidos corretamente;
- o envio não calcula SLA, prazo ou lembrete; timestamps seguem apenas a conversão de origem para America/Sao_Paulo;
- horários legados não são deslocados sem classificação;
- e-mail e interface usam a mesma regra.

### Frontend e E2E

- vendedor recebe resumo renderizado com nome, telefone e link;
- link abre o dashboard;
- transferência mostra o aviso individual após confirmação;
- estados de pendência e erro são legíveis;
- admin visualiza estado da outbox sem editar tratativas;
- screenshot em 1440×900;
- acesso de vendedor continua restrito aos próprios leads.

## 13. Observabilidade e operação

Adicionar métricas/logs para:

- eventos criados por tipo;
- grupos agregados;
- mensagens enviadas;
- tempo entre atribuição e envio;
- retries;
- dead-letter;
- falhas por código SMTP;
- grupos sem destinatário;
- última execução de sincronização com alertas.

O administrador deve conseguir distinguir:

- atribuição concluída e e-mail pendente;
- e-mail enviado;
- retry em andamento;
- dead-letter que exige intervenção.

Desativar o alerta deve ser uma configuração operacional independente da fila.

## 14. Alterações documentais necessárias antes do código

- registrar a nova regra na seção de governança do SPEC: regra anterior, nova regra, motivo, impactos, migração, testes e aprovação;
- atualizar `docs/DECISOES.md` com decisão sobre resumo por sincronização, transferência individual, SMTP e horário;
- regenerar `docs/CONTEXTO_MESTRE_GERENCIADOR_DE_LEADS.md`;
- atualizar `docs/ARQUITETURA.md` se a fronteira do worker SMTP mudar;
- documentar variáveis sem valores secretos;
- criar plano de rollout, rollback e piloto.

## 15. Fora do escopo

- envio de WhatsApp;
- alteração da fila FIFO;
- alteração de status comercial por e-mail;
- edição administrativa de tratativas;
- inclusão de campanha, e-mail do lead ou dados adicionais no alerta;
- migração ampla de timestamps sem classificação;
- painel de preferências individuais de e-mail;
- provedor externo adicional além do SMTP aprovado.

## 16. Critérios de aceite

1. Após uma sincronização com novos leads, cada vendedor recebe no máximo um resumo daquela execução.
2. O resumo lista todos os leads novos atribuídos ao vendedor naquela execução.
3. O resumo contém apenas nome, telefone e link do dashboard.
4. Uma transferência manual envia um aviso individual ao novo proprietário.
5. Nenhum alerta de transferência afeta cursor, posição ou créditos da fila.
6. Retry e dead-letter funcionam sem desfazer atribuições.
7. STARTTLS e credenciais server-side são obrigatórios.
8. Horário local da planilha não aparece três horas adiantado.
9. Timestamps UTC existentes continuam sendo exibidos corretamente em São Paulo.
10. Todos os testes obrigatórios e gates de build, lint, typecheck e E2E passam.

## 17. Próximo passo

Após a revisão e aprovação deste documento, criar o plano executável em `docs/superpowers/plans/` com tarefas TDD pequenas, implementação por subagentes, revisão independente e evidências no ledger.

## Desenho de produto: `docs/superpowers/specs/2026-09-04-remocao-sla-e-reconciliacao.md`

# DEC-031 — Remoção integral de SLA e reconciliação da fila

Status: aprovada por Yago em 04/09/2026.

## Decisão

O fluxo vigente não cria, calcula, expõe ou entrega prazo, lembrete, ciclo de
SLA ou bloqueio automático. A disponibilidade da fila é exclusivamente
`Ativo` ou `Pausado`; a pausa é manual e administrativa.

Após importar o lote inteiro, a sincronização reconcilia em FIFO os leads
normais sem responsável que estejam `ready` ou estacionados exclusivamente por
`no_eligible_seller`. Assim, um lead que chegou quando não havia vendedor
elegível volta automaticamente à distribuição em uma sincronização posterior.

Leads recorrentes cujo proprietário está indisponível continuam estacionados
com `owner_unavailable` e não interrompem a distribuição dos leads normais.

## Migração e histórico

A migração versionada `20260904_remove_operational_sla` remove as projeções de
prazo dos leads, fecha ciclos legados abertos e cancela alertas de prazo ainda
não terminais. O bootstrap remove de forma idempotente o índice ativo desses
ciclos fora da transação, pois MongoDB não permite DDL em transações.
Comentários, atribuições, ciclos e alertas já concluídos permanecem como
histórico de auditoria.

O worker também recusa entregar um alerta legado caso ele tenha sido obtido por
um worker concorrente durante a execução da migração.

## Critérios de aceite

- Nenhuma API ou tela vigente contém prazo, lembrete ou bloqueio por atraso.
- Novo comentário altera somente a tratativa e sua situação comercial.
- O próximo sync atribui em FIFO os leads normais antes estacionados assim que
  houver vendedor ativo.
- Reexecutar sync sem mudança de disponibilidade não duplica eventos de
  estacionamento.
- O histórico legado não é apagado.

## Desenho de produto: `docs/superpowers/specs/2026-09-14-notificacoes-internas-tratativas-relatorios-design.md`

# Design — notificações internas, tratativas, filtros e relatórios

**Data:** 14/09/2026
**Status:** aprovado para documentação e planejamento; implementação depende da revisão deste documento.
**Aprovação de produto:** Yago, 14/09/2026.

## 1. Objetivo e escopo

Evoluir a operação comercial sem alterar a fila FIFO, a regra de propriedade ou a permissão de tratativas:

1. avisar internamente cada vendedor sobre leads que lhe foram atribuídos ou transferidos desde sua última visualização;
2. tornar explícito quais leads ainda não receberam nenhuma tratativa;
3. adicionar `Potencial` às situações comerciais;
4. permitir filtro administrativo por responsável e ordenação alfabética por situação nas visões administrativa e comercial;
5. disponibilizar relatórios administrativos por situação e por proprietário atual, filtráveis pela data da atribuição atual;
6. corrigir a projeção atual de `Desqualificado`, para que ela reflita a última tratativa e não fique permanentemente marcada.

Não há envio de e-mail neste escopo. O desenho de e-mail de 03/09/2026 fica substituído nesta etapa por notificação interna; nenhum adaptador SMTP, worker ou credencial será criado ou acionado.

## 2. Decisões aprovadas

### 2.1 Situação e tratativa

- As situações primárias permitidas são `Indefinido`, `Potencial`, `Negociação` e `Ganho`.
- O vendedor atual escolhe exatamente uma situação ao registrar uma tratativa válida, com comentário de ao menos seis caracteres úteis.
- `Desqualificado` continua marcador adicional e pode coexistir com qualquer situação primária.
- O estado materializado do lead (`commercialStatus` e `isDisqualified`) representa **exatamente a última tratativa**.
- Cada tratativa permanece imutável. Portanto, uma tratativa antiga pode continuar exibindo `Desqualificado` mesmo que a tratativa posterior o tenha removido.
- Desmarcar o checkbox em uma tratativa posterior remove apenas o marcador atual do lead; não apaga ou reescreve o histórico.

### 2.2 Destaque de pendência de tratativa

- Um lead com `commentCount === 0` recebe destaque amarelo na linha completa da tabela de leads.
- O destaque existe nas visões administrativa e comercial.
- Ao registrar a primeira tratativa confirmada, a projeção atualiza `commentCount`, e o destaque deixa de aparecer na próxima leitura/revalidação.
- O destaque é somente visual: não altera fila, disponibilidade, permissão, atribuição ou prioridade.

### 2.3 Notificação interna de novos leads

- A notificação é uma janela interna, exclusiva do vendedor, sem e-mail.
- Ao abrir o dashboard, o vendedor consulta leads de propriedade atual atribuídos ou transferidos após seu cursor persistente de leitura.
- Fechar a janela confirma a visualização até a marca d'água retornada pela API. O cursor avança monotonicamente e não pode retroceder.
- A lista inclui somente leads cujo `assigneeId` atual é o vendedor autenticado. Um lead transferido antes de ser visualizado não é exposto ao proprietário anterior.
- Transferências entram na janela do novo proprietário; não afetam cursor FIFO, posição ou créditos.
- Na primeira implantação, todos os cursores ausentes recebem o instante da migração. Assim, somente atribuições e transferências futuras geram aviso.
- Administradores não recebem a janela; seu acesso global continua pela visão administrativa.

### 2.4 Filtros, ordenação e relatórios

- Administrador pode selecionar um responsável atual ou `Todos` na lista de leads.
- Administrador e vendedor podem ordenar os leads alfabeticamente pela situação exibida: `Ganho`, `Indefinido`, `Negociação`, `Potencial`.
- Empates preservam a ordenação secundária atual e determinística da consulta.
- A aba `/relatorios` é exclusiva de administrador.
- O período padrão é todo o histórico. A interface oferece atalhos e intervalo personalizado.
- O período é aplicado à data da atribuição para o proprietário atual. Após transferência, usa-se a data da transferência, porque ela é a atribuição atual.
- As agregações usam o proprietário atual, inclusive para leads originalmente atribuídos a outro vendedor.
- Os gráficos exibem distribuição por situação e por vendedor; não há card separado de “quantidade total de leads”.

## 3. Divergências canônicas e governança

O SPEC ainda descreve notificações por e-mail e três situações primárias; o comportamento histórico também preservava `isDisqualified` após uma tratativa posterior sem o marcador. Estas regras são substituídas para esta operação pela decisão aprovada neste documento:

- notificação de novos leads é interna e persistente por vendedor, não um envio SMTP;
- `Potencial` é situação primária válida;
- `Desqualificado` é reversível na projeção atual por decisão explícita do vendedor em uma nova tratativa;
- relatórios globais são exclusivos de administrador.

A implementação deve registrar GOV-007 no SPEC e DEC-031 em `docs/DECISOES.md`, com motivo, impacto, migração e testes de aceite. Não poderá manter o envio de e-mail como efeito colateral deste pacote.

## 4. Alternativas analisadas

| Alternativa | Vantagem | Limitação | Decisão |
| --- | --- | --- | --- |
| Cursor persistente no usuário | Funciona entre computadores, preserva transferências e exige pouco estado | Requer marca d'água segura para não perder itens concorrentes | Adotada |
| Evento individual com estado de leitura | Auditoria detalhada item a item | Nova coleção, endpoints e ciclo operacional sem necessidade atual | Não adotada |
| `localStorage` | Implementação curta | Falha em outro dispositivo, sessão anônima e limpeza do navegador | Rejeitada |

## 5. Modelo de dados e migração

### 5.1 Usuários

Adicionar o campo opcional abaixo à projeção de usuários vendedores:

```text
newLeadsSeenAt: datetime | null
```

Uma nova migração MongoDB versionada preencherá apenas documentos sem esse campo com o instante controlado da migração. Ela será idempotente e não alterará `assignedAt`, histórico de tratativas, fila ou propriedade.

### 5.2 Leads e tratativas

- Expandir os validadores, tipos de domínio, Pydantic e TypeScript para aceitar `potential`.
- `lead_treatments.isDisqualified` é o valor submetido naquela tratativa e nunca é alterado.
- `leads.isDisqualified` recebe exatamente `command.is_disqualified`; não pode combinar o valor antigo com OR lógico.
- `leads.commercialStatus` recebe exatamente a situação da nova tratativa.
- `assignedAt` já representa a atribuição do proprietário atual e será mantido como fonte do filtro de relatórios e da busca de novos leads.

Não há migração de histórico para apagar desqualificações antigas. A correção aplica-se às novas tratativas; qualquer reparo retrospectivo de projeções divergentes só poderá ser feito em migração separada, com lista de afetados e aprovação explícita.

## 6. Contratos de API

### 6.1 Dashboard e lista de leads

Estender a consulta de leitura de leads com parâmetros opcionais, sempre aplicados no backend:

```text
GET /api/dashboard?page=&limit=&assigneeId=&sort=situation
```

- `assigneeId` é aceito apenas para administrador; vendedor sempre recebe a própria projeção, ignorando qualquer identificador externo.
- `sort=situation` aplica a ordenação alfabética aprovada no banco/read model.
- A resposta existente continua retornando `commentCount`, situação, marcador, responsável e `assignedAt`.

### 6.2 Novos leads

```text
GET  /api/lead-notifications/new
POST /api/lead-notifications/new/acknowledge
```

A leitura retorna itens mínimos do lead e uma `watermark` do servidor. A confirmação recebe essa marca d'água e atualiza `newLeadsSeenAt` com operação de máximo. A API limita a confirmação à marca d'água emitida para a sessão/consulta, evitando que um fechamento avance sobre atribuições ocorridas depois da leitura.

Ambas as rotas exigem vendedor autenticado. Administrador e vendedor diferente recebem negação de autorização; nenhum identificador de vendedor é aceito no cliente.

### 6.3 Relatórios

```text
GET /api/admin/reports/lead-distribution?from=&to=
```

- Exclusivo de administrador.
- `from` é inclusivo e `to` é exclusivo; atalhos de calendário são convertidos no servidor para intervalos explícitos em `America/Sao_Paulo` e armazenados/consultados como UTC.
- A consulta filtra pela `assignedAt` vigente do lead e agrega por `commercialStatus` e `assigneeId` atual.
- A resposta contém somente rótulos e contagens necessários para os dois gráficos; não expõe telefone, e-mail ou histórico de tratativas.

## 7. Interface

### 7.1 Janela de novos leads

O dashboard do vendedor monta uma janela modal acessível quando a consulta retorna itens. Cada item apresenta nome e botão existente de contato, sem expor dados adicionais fora da regra atual. Fechar, usar `Esc` ou clicar no controle de fechar confirma a marca d'água; se a confirmação falhar, a janela informa o erro e não avança o cursor localmente.

### 7.2 Tabelas

- Adicionar classe semântica de linha pendente quando `commentCount` é zero, com amarelo legível e contraste suficiente para texto, selo e hover.
- Incluir seletor de responsável apenas para administrador.
- Incluir seletor de ordenação por situação para ambos os perfis.
- Preservar ações existentes: vendedor registra tratativa; administrador lê histórico e transfere propriedade. Nenhum filtro cria permissão adicional.

### 7.3 Relatórios

A navegação mostra `Relatórios` somente para administrador. A página usa filtro de período, mensagem vazia explícita e dois gráficos de barras acessíveis (rótulos, contagens e equivalente textual), um por situação e outro por vendedor. O estado de carregamento/erro não esconde o shell nem quebra as demais páginas.

## 8. Segurança, concorrência e falhas

- A identidade do vendedor vem apenas da sessão autenticada.
- A confirmação de leitura é compare-and-max transacional/atômica e não reduz um cursor atualizado por outra aba.
- O snapshot de novos leads é delimitado por marca d'água: atribuição posterior continua pendente após o fechamento da janela atual.
- Transferência mantém as garantias existentes de autorização e FIFO; a notificação é leitura derivada, nunca comando de fila.
- Falha de consulta ou confirmação da notificação resulta em estado legível e tentativa posterior, sem perder dados nem criar e-mail.
- Agregações de relatório são calculadas no backend e protegidas por papel administrativo.
- A interface não é a camada de autorização; as novas rotas aplicam escopo no serviço/repositório.

## 9. Testes de aceite

### Domínio e persistência

- aceitar `potential` e rejeitar qualquer situação fora da enumeração;
- registrar `Desqualificado=true`, depois `Negociação + false`, preservar as duas tratativas e materializar o lead com marcador `false`;
- repetir o mesmo comando idempotente sem duplicar tratativa ou contador;
- validar a migração de cursor ausente como idempotente;
- consulta de novos leads inclui atribuição e transferência futuras, mas não dados anteriores ao cursor;
- confirmação concorrente nunca reduz cursor nem perde lead atribuído após a marca d'água;
- filtro administrativo respeita proprietário atual; vendedor não consegue consultar outro responsável;
- agregações filtram por data da atribuição atual e agrupam por proprietário atual;
- rota de relatório nega vendedor.

### Web, acessibilidade e E2E

- modal de novos leads abre para vendedor com itens pendentes e confirma visualização ao fechar;
- modal não aparece para administrador nem mostra lead transferido ao proprietário anterior;
- linhas sem tratativa possuem destaque amarelo legível e o perdem após primeira tratativa;
- seletor de `Potencial` aparece e é enviado pela tratativa;
- filtro de responsável é visível somente ao administrador;
- ordenação por situação funciona nos dois perfis;
- aba de relatórios não aparece nem responde para vendedor;
- gráficos possuem rótulo textual, dados vazios e intervalo personalizado;
- screenshots desktop 1440×900 cobrem dashboard vendedor, lista administrativa e relatórios.

## 10. Fora do escopo

- e-mail, SMTP, n8n, WhatsApp ou outro canal externo;
- mudança em FIFO, cursor de distribuição ou créditos de pulo;
- alteração administrativa de comentários, situação ou marcador;
- alteração retroativa massiva de `isDisqualified` já materializado;
- permissões de relatório para vendedor;
- indicadores financeiros, funil ou campanhas além das distribuições aprovadas.

## 11. Sequência de implementação

1. Governança e atualização documental; regenerar contexto mestre.
2. Contratos, enumeração `potential` e teste vermelho do marcador reversível.
3. Migração e serviço de cursor/notificação, com autorização e concorrência.
4. Filtros, ordenação e projeções administrativas/comerciais.
5. Endpoint de agregação e página de relatórios exclusiva de administrador.
6. Interface de notificação, destaque amarelo, filtros e gráficos.
7. E2E, screenshots 1440×900, testes completos e revisão independente.

## 12. Critérios de aceite finais

1. Nenhum e-mail é disparado por atribuição ou transferência neste pacote.
2. Vendedor visualiza, em qualquer computador, somente seus leads recebidos desde a última confirmação da janela.
3. A primeira implantação não notifica leads antigos; atribuições e transferências posteriores são notificadas.
4. `Potencial` pode ser registrado e aparece nas listas, histórico, filtros e gráficos.
5. O marcador atual de desqualificação é removido por nova tratativa sem marcador, sem alterar o histórico anterior.
6. Leads sem tratativa são imediatamente distinguíveis visualmente, sem efeito operacional.
7. Administrador filtra por responsável; ambos os perfis ordenam por situação.
8. Relatórios globais só são acessíveis ao administrador e usam período por atribuição atual e proprietário atual.
9. Toda alteração preserva a fila FIFO, a propriedade, a autorização e as garantias de transferência já aprovadas.

## Desenho de produto: `docs/superpowers/specs/2026-09-22-cadastro-manual-fila-alternativa-exportacoes-design.md`

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

## Plano histórico ou executável: `docs/superpowers/plans/2026-08-25-etapa-1-esqueleto-executavel.md`

# Etapa 1 — Esqueleto executável Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar um workspace local reproduzível com Next.js, Supabase via Docker, testes, qualidade automatizada e uma página mínima que comprove a conexão, sem implementar regras de negócio.

**Architecture:** Um workspace npm concentra a aplicação Next.js em `apps/web`; o Supabase CLI controla a infraestrutura local em `supabase`; scripts pequenos em `tooling` isolam configuração e verificações. O navegador recebe somente URL e chave pública local. O único arquivo externo ao diretório do produto é o workflow de descoberta obrigatória do GitHub Actions.

**Tech Stack:** Node.js 24 LTS, npm workspaces, Next.js 16/App Router, React, TypeScript, Supabase CLI 2.115.0, Docker, Vitest 4.1.11, Playwright 1.62.1, YAML 2.8.1, ESLint e Prettier 3.9.6.

**Spec:** `gerec_leads/SPEC_GERENCIADOR_DE_LEADS_WTG.md`, `gerec_leads/ROADMAP.md`, `gerec_leads/docs/ARQUITETURA.md` e `gerec_leads/docs/DECISOES.md`.

## Global Constraints

- [ ] Ler integralmente `SPEC_GERENCIADOR_DE_LEADS_WTG.md` antes de iniciar a execução.
- [ ] Trabalhar somente em `gerec_leads/`, exceto pelo arquivo autorizado `.github/workflows/gerec-leads-ci.yml`.
- [ ] Não criar tabelas comerciais, migrações de domínio, usuários, RLS, fila, campanhas, integrações reais ou telas definitivas nesta etapa.
- [ ] Não copiar código das pastas legadas. Materiais legados continuam disponíveis apenas como referência visual futura.
- [ ] Nunca versionar `.env.local`, chaves administrativas, `service_role`, dados pessoais ou saída sensível do Supabase.
- [ ] Tratar a interface como exclusivamente desktop, com largura mínima suportada de 1280 px; não implementar nem prometer suporte funcional a tablet ou celular.
- [ ] Usar `apply_patch` para edições manuais e preservar mudanças preexistentes do usuário.
- [ ] Seguir TDD em cada unidade criada: teste falhando, implementação mínima, teste passando e verificação de regressão.
- [ ] Não avançar para uma tarefa enquanto o gate da tarefa atual não passar.
- [ ] Fazer commits pequenos nos pontos indicados, sem incluir alterações alheias ao plano.

## Matriz de arquivos e responsabilidades

| Caminho | Responsabilidade na Etapa 1 |
|---|---|
| `gerec_leads/package.json` | Scripts e dependências compartilhados do workspace. |
| `gerec_leads/package-lock.json` | Instalação determinística de todas as dependências. |
| `gerec_leads/.nvmrc` | Runtime Node.js local padronizado. |
| `gerec_leads/apps/web/` | Aplicação Next.js e diagnóstico da conexão local. |
| `gerec_leads/supabase/` | Configuração gerada pelo Supabase CLI, sem domínio comercial. |
| `gerec_leads/tooling/` | Testes estruturais e scripts locais sem regra de negócio. |
| `gerec_leads/tests/e2e/` | Teste ponta a ponta da fundação. |
| `gerec_leads/integrations/n8n/` | Limite documentado para workflows futuros; nenhuma conexão real agora. |
| `gerec_leads/WTG - Leads.xlsx` | Fixture mock A–Q fornecido pelo usuário e já versionado no pré-requisito; não modificar na Etapa 1. |
| `.github/workflows/gerec-leads-ci.yml` | Entrada mínima do GitHub Actions, limitada ao workspace. |

---

### Task 1: Fixar o runtime e criar o workspace Next.js vazio

**Files:**

- Create: `gerec_leads/.nvmrc`
- Create: `gerec_leads/package.json`
- Create: `gerec_leads/package-lock.json`
- Create: `gerec_leads/apps/web/**`
- Create: `gerec_leads/integrations/n8n/README.md`
- Create: `gerec_leads/tests/contracts/README.md`
- Create: `gerec_leads/tooling/tests/workspace-structure.test.mjs`

- [ ] **Step 1: Confirmar o runtime disponível e selecionar Node.js 24**

Executar na raiz do repositório:

```powershell
node --version
npm --version
nvm version
```

Se a versão principal do Node não for 24:

```powershell
nvm install 24
nvm use 24
node --version
```

Esperado: `node --version` começa com `v24.`. Não continuar com Node 20.

- [ ] **Step 2: Escrever primeiro o teste estrutural**

Criar `gerec_leads/tooling/tests/workspace-structure.test.mjs`:

```js
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

test("o workspace mantém a estrutura aprovada", () => {
  const requiredPaths = [
    "apps/web/package.json",
    "integrations/n8n/README.md",
    "tests/contracts/README.md",
  ];

  for (const relativePath of requiredPaths) {
    assert.equal(existsSync(resolve(root, relativePath)), true, relativePath);
  }

  const workspace = JSON.parse(
    readFileSync(resolve(root, "package.json"), "utf8"),
  );
  const web = JSON.parse(
    readFileSync(resolve(root, "apps/web/package.json"), "utf8"),
  );

  assert.equal(workspace.private, true);
  assert.deepEqual(workspace.workspaces, ["apps/*"]);
  assert.equal(workspace.engines.node, ">=24 <25");
  assert.equal(web.name, "@wtg/web");
  assert.equal(typeof web.scripts.dev, "string");
  assert.equal(typeof web.scripts.build, "string");
  assert.equal(typeof web.scripts.lint, "string");
  assert.equal(typeof web.scripts.typecheck, "string");
});
```

- [ ] **Step 3: Executar o teste e comprovar a falha inicial**

```powershell
Set-Location gerec_leads
node --test tooling/tests/workspace-structure.test.mjs
```

Esperado: `FAIL`, porque `package.json` e `apps/web` ainda não existem. Se passar, interromper e investigar estado preexistente.

- [ ] **Step 4: Criar os arquivos mínimos do workspace**

Criar `.nvmrc` com exatamente:

```text
24
```

Criar `package.json`:

```json
{
  "name": "@wtg/gerenciador-de-leads",
  "version": "0.1.0",
  "private": true,
  "workspaces": ["apps/*"],
  "engines": {
    "node": ">=24 <25"
  },
  "scripts": {
    "dev": "npm --workspace @wtg/web run dev",
    "build": "npm --workspace @wtg/web run build",
    "lint": "npm --workspace @wtg/web run lint",
    "typecheck": "npm --workspace @wtg/web run typecheck",
    "test:structure": "node --test tooling/tests/workspace-structure.test.mjs"
  }
}
```

Gerar a aplicação sem instalar dependências e sem criar outro repositório:

```powershell
npx create-next-app@16.3.3 apps/web --ts --eslint --tailwind --app --src-dir --import-alias "@/*" --empty --use-npm --skip-install --disable-git --no-agents-md
```

No `apps/web/package.json` gerado:

- trocar `name` por `@wtg/web`;
- adicionar `"typecheck": "tsc --noEmit"` aos scripts;
- não adicionar dependências além das geradas pelo scaffold nesta tarefa.

Criar `integrations/n8n/README.md`:

```md
# Integrações n8n

Este diretório receberá workflows exportados e documentação na Etapa 7.
O n8n atua como adaptador e não contém regras críticas de negócio.
```

Criar `tests/contracts/README.md`:

```md
# Testes de contrato

Este diretório abrigará contratos de integrações externas a partir da Etapa 4.
Não há integração real habilitada na Etapa 1.
```

Instalar uma única árvore de dependências e gerar somente o lockfile da raiz:

```powershell
npm install
```

- [ ] **Step 5: Executar o gate da tarefa**

```powershell
npm run test:structure
npm run lint
npm run typecheck
npm run build
Get-ChildItem -Recurse -Filter package-lock.json | Select-Object -ExpandProperty FullName
```

Esperado: todos os comandos passam e existe apenas `gerec_leads/package-lock.json`.

- [ ] **Step 6: Commit da fundação**

```powershell
git add gerec_leads/.nvmrc gerec_leads/package.json gerec_leads/package-lock.json gerec_leads/apps gerec_leads/integrations gerec_leads/tests gerec_leads/tooling/tests/workspace-structure.test.mjs
git commit -m "chore(gerec-leads): cria workspace executavel"
```

---

### Task 2: Adicionar formatação e testes unitários

**Files:**

- Create: `gerec_leads/prettier.config.mjs`
- Create: `gerec_leads/.prettierignore`
- Create: `gerec_leads/apps/web/vitest.config.ts`
- Modify: `gerec_leads/package.json`
- Modify: `gerec_leads/apps/web/package.json`
- Modify: `gerec_leads/package-lock.json`

- [ ] **Step 1: Instalar as ferramentas com versões fixas**

```powershell
npm install --save-dev prettier@3.9.6
npm install --save-dev vitest@4.1.11 --workspace @wtg/web
```

Adicionar ao `package.json` da raiz:

```json
{
  "scripts": {
    "test": "npm --workspace @wtg/web run test",
    "format": "prettier --write .",
    "format:check": "prettier --check .",
    "check": "npm run format:check && npm run lint && npm run typecheck && npm run test && npm run test:structure && npm run build"
  }
}
```

Preservar os scripts já existentes ao mesclar esse bloco. Adicionar ao `apps/web/package.json`:

```json
{
  "scripts": {
    "test": "vitest run --passWithNoTests"
  }
}
```

- [ ] **Step 2: Configurar o formatador sem alterar o SPEC**

Criar `prettier.config.mjs`:

```js
/** @type {import("prettier").Config} */
const config = {
  printWidth: 100,
  semi: true,
  singleQuote: false,
  trailingComma: "all",
};

export default config;
```

Criar `.prettierignore`:

```text
node_modules
.next
.superpowers
coverage
playwright-report
test-results
supabase/.temp
supabase/.branches
package-lock.json
**/*.md
```

- [ ] **Step 3: Configurar o runner unitário sem criar teste artificial de constante**

Criar `apps/web/vitest.config.ts`:

```ts
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "node",
    include: ["src/**/*.test.ts"],
  },
});
```

- [ ] **Step 4: Comprovar que o runner encerra com sucesso sem testes**

```powershell
npm run test
```

Esperado: `PASS`, com o Vitest informando que não encontrou testes e encerrando com código zero por causa de `--passWithNoTests`. Os primeiros testes comportamentais reais serão criados na Task 4.

- [ ] **Step 5: Executar o gate e formatar**

```powershell
npm run test
npm run format
npm run check
```

Esperado: runner aprovado sem testes e `check` totalmente verde.

- [ ] **Step 6: Commit das ferramentas de qualidade**

```powershell
git add gerec_leads
git commit -m "test(gerec-leads): configura qualidade e testes unitarios"
```

---

### Task 3: Inicializar Supabase local e gerar ambiente público com segurança

**Files:**

- Create: `gerec_leads/supabase/config.toml`
- Create: `gerec_leads/supabase/seed.sql`
- Create: `gerec_leads/apps/web/.env.example`
- Create: `gerec_leads/tooling/supabase/parse-status-env.test.mjs`
- Create: `gerec_leads/tooling/supabase/parse-status-env.mjs`
- Create: `gerec_leads/tooling/supabase/write-web-env.mjs`
- Modify: `gerec_leads/package.json`
- Modify: `gerec_leads/package-lock.json`

- [ ] **Step 1: Instalar o Supabase CLI no próprio workspace**

```powershell
npm install --save-dev supabase@2.115.0
```

Adicionar os scripts abaixo ao `package.json` da raiz:

```json
{
  "scripts": {
    "supabase:init": "supabase init",
    "supabase:start": "supabase start",
    "supabase:stop": "supabase stop",
    "supabase:status": "supabase status",
    "supabase:reset": "supabase db reset",
    "env:local": "node tooling/supabase/write-web-env.mjs",
    "test:supabase-tooling": "node --test tooling/supabase/*.test.mjs"
  }
}
```

Atualizar `check` para executar `npm run test:supabase-tooling` antes do build.

- [ ] **Step 2: Escrever o teste do filtro de variáveis antes da implementação**

Criar `tooling/supabase/parse-status-env.test.mjs`:

```js
import assert from "node:assert/strict";
import test from "node:test";

import { parseSupabaseStatusEnv, renderNextEnv } from "./parse-status-env.mjs";

test("expõe somente URL e chave pública do Supabase", () => {
  const source = [
    'API_URL="http://127.0.0.1:54321"',
    'ANON_KEY="public-local-key"',
    'SERVICE_ROLE_KEY="never-expose-this"',
  ].join("\n");

  const parsed = parseSupabaseStatusEnv(source);

  assert.deepEqual(parsed, {
    NEXT_PUBLIC_SUPABASE_URL: "http://127.0.0.1:54321",
    NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY: "public-local-key",
  });
  assert.equal(renderNextEnv(parsed).includes("SERVICE_ROLE"), false);
  assert.equal(renderNextEnv(parsed).includes("never-expose-this"), false);
});

test("recusa uma saída sem configuração pública completa", () => {
  assert.throws(
    () => parseSupabaseStatusEnv('API_URL="http://127.0.0.1:54321"'),
    /chave pública/i,
  );
});
```

- [ ] **Step 3: Executar o teste e confirmar a falha inicial**

```powershell
npm run test:supabase-tooling
```

Esperado: `FAIL` porque `parse-status-env.mjs` ainda não existe.

- [ ] **Step 4: Implementar o parser mínimo e seguro**

Criar `tooling/supabase/parse-status-env.mjs`:

```js
export function parseSupabaseStatusEnv(source) {
  const values = Object.fromEntries(
    source
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter((line) => line && !line.startsWith("#") && line.includes("="))
      .map((line) => {
        const separator = line.indexOf("=");
        const key = line.slice(0, separator);
        const value = line.slice(separator + 1).replace(/^"|"$/g, "");
        return [key, value];
      }),
  );

  const publicKey = values.PUBLISHABLE_KEY ?? values.ANON_KEY;

  if (!values.API_URL || !publicKey) {
    throw new Error("Supabase local sem URL ou chave pública disponível.");
  }

  return {
    NEXT_PUBLIC_SUPABASE_URL: values.API_URL,
    NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY: publicKey,
  };
}

export function renderNextEnv(values) {
  return `${Object.entries(values)
    .map(([key, value]) => `${key}=${value}`)
    .join("\n")}\n`;
}
```

Criar `tooling/supabase/write-web-env.mjs`:

```js
import { execFileSync } from "node:child_process";
import { chmodSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { parseSupabaseStatusEnv, renderNextEnv } from "./parse-status-env.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const npmCommand = process.platform === "win32" ? "npm.cmd" : "npm";
const status = execFileSync(
  npmCommand,
  ["exec", "--", "supabase", "status", "-o", "env"],
  { cwd: root, encoding: "utf8" },
);
const destination = resolve(root, "apps/web/.env.local");

writeFileSync(destination, renderNextEnv(parseSupabaseStatusEnv(status)), {
  encoding: "utf8",
  mode: 0o600,
});

if (process.platform !== "win32") {
  chmodSync(destination, 0o600);
}

console.log("Ambiente web local criado somente com URL e chave pública.");
```

- [ ] **Step 5: Inicializar o Supabase sem domínio comercial**

```powershell
npm run supabase:init
```

Manter o `config.toml` gerado pelo CLI. Criar `supabase/seed.sql` apenas com:

```sql
-- Dados sintéticos de domínio serão adicionados na Etapa 2, após o modelo aprovado.
```

Criar `apps/web/.env.example`:

```dotenv
NEXT_PUBLIC_SUPABASE_URL=http://127.0.0.1:54321
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=replace-with-local-public-key
```

- [ ] **Step 6: Subir o ambiente e gerar `.env.local`**

Com Docker Desktop ativo:

```powershell
npm run supabase:start
npm run env:local
npm run supabase:status
git check-ignore apps/web/.env.local
```

Esperado: serviços locais saudáveis, `apps/web/.env.local` ignorado pelo Git e nenhum valor de `service_role` nesse arquivo. Não imprimir o conteúdo das chaves no terminal ou em documentação.

- [ ] **Step 7: Executar o gate e fazer commit**

```powershell
npm run test:supabase-tooling
npm run check
git status --short
```

Confirmar que `.env.local`, `supabase/.temp` e `supabase/.branches` não aparecem no stage.

```powershell
git add gerec_leads
git commit -m "chore(gerec-leads): configura supabase local seguro"
```

---

### Task 4: Criar diagnóstico testado da conexão local

**Files:**

- Create: `gerec_leads/apps/web/src/lib/health/check-supabase.test.ts`
- Create: `gerec_leads/apps/web/src/lib/health/check-supabase.ts`
- Modify: `gerec_leads/apps/web/src/app/page.tsx`
- Modify: `gerec_leads/apps/web/src/app/layout.tsx`
- Modify: `gerec_leads/apps/web/src/app/globals.css`

- [ ] **Step 1: Escrever os testes do diagnóstico**

Criar `apps/web/src/lib/health/check-supabase.test.ts`:

```ts
import { describe, expect, it, vi } from "vitest";

import {
  checkSupabaseHealth,
  type HealthRequest,
} from "./check-supabase";

describe("checkSupabaseHealth", () => {
  it("informa conexão quando o Auth local responde", async () => {
    const request = vi
      .fn<HealthRequest>()
      .mockResolvedValue(new Response(null, { status: 200 }));

    await expect(
      checkSupabaseHealth(
        { url: "http://127.0.0.1:54321", publishableKey: "public-key" },
        request,
      ),
    ).resolves.toEqual({ status: "connected", message: "Supabase local conectado" });

    expect(request).toHaveBeenCalledWith(
      "http://127.0.0.1:54321/auth/v1/health",
      expect.objectContaining({
        cache: "no-store",
        headers: { apikey: "public-key" },
      }),
    );
  });

  it("não tenta conectar sem configuração pública", async () => {
    const request = vi.fn<HealthRequest>();

    await expect(
      checkSupabaseHealth({ url: undefined, publishableKey: undefined }, request),
    ).resolves.toEqual({
      status: "not_configured",
      message: "Supabase local ainda não configurado",
    });
    expect(request).not.toHaveBeenCalled();
  });

  it("degrada de forma segura quando o serviço está indisponível", async () => {
    const request = vi
      .fn<HealthRequest>()
      .mockRejectedValue(new Error("connection refused"));

    await expect(
      checkSupabaseHealth(
        { url: "http://127.0.0.1:54321", publishableKey: "public-key" },
        request,
      ),
    ).resolves.toEqual({
      status: "unavailable",
      message: "Supabase local indisponível",
    });
  });
});
```

- [ ] **Step 2: Executar o teste e comprovar a falha**

```powershell
npm run test
```

Esperado: `FAIL` pela ausência de `check-supabase.ts`.

- [ ] **Step 3: Implementar o diagnóstico sem expor segredos**

Criar `apps/web/src/lib/health/check-supabase.ts`:

```ts
export type SupabaseHealth = {
  status: "connected" | "not_configured" | "unavailable";
  message: string;
};

export type HealthRequest = (
  input: string,
  init?: RequestInit,
) => Promise<Response>;

type HealthConfig = {
  url: string | undefined;
  publishableKey: string | undefined;
};

export async function checkSupabaseHealth(
  config: HealthConfig = {
    url: process.env.NEXT_PUBLIC_SUPABASE_URL,
    publishableKey: process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY,
  },
  request: HealthRequest = fetch,
): Promise<SupabaseHealth> {
  if (!config.url || !config.publishableKey) {
    return {
      status: "not_configured",
      message: "Supabase local ainda não configurado",
    };
  }

  try {
    const response = await request(
      `${config.url.replace(/\/$/, "")}/auth/v1/health`,
      {
        cache: "no-store",
        headers: { apikey: config.publishableKey },
      },
    );

    if (response.ok) {
      return { status: "connected", message: "Supabase local conectado" };
    }
  } catch {
    // O estado de indisponibilidade é exibido sem registrar URL, chave ou payload.
  }

  return {
    status: "unavailable",
    message: "Supabase local indisponível",
  };
}
```

- [ ] **Step 4: Criar a página mínima de fundação**

Substituir `layout.tsx` por:

```tsx
import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import type { ReactNode } from "react";

import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Gerenciador de Leads WTG",
  description: "Fundação local do Gerenciador de Leads WTG",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="pt-BR">
      <body className={`${geistSans.variable} ${geistMono.variable}`}>
        {children}
      </body>
    </html>
  );
}
```

Substituir `page.tsx` por:

```tsx
import { checkSupabaseHealth } from "@/lib/health/check-supabase";

export const dynamic = "force-dynamic";

export default async function Home() {
  const health = await checkSupabaseHealth();

  return (
    <main className="foundation-shell">
      <section className="foundation-card" aria-labelledby="product-title">
        <p className="foundation-kicker">WTG • ambiente de desenvolvimento</p>
        <h1 id="product-title">Gerenciador de Leads WTG</h1>
        <p>
          Esqueleto local preparado. As regras comerciais começam somente após a
          aprovação da próxima etapa.
        </p>
        <div className="health-line" data-status={health.status} role="status">
          <span aria-hidden="true" />
          {health.message}
        </div>
      </section>
    </main>
  );
}
```

Substituir `globals.css` pelo CSS mínimo abaixo. Ele é apenas diagnóstico, não o design definitivo, e respeita o suporte exclusivamente desktop aprovado:

```css
@import "tailwindcss";

:root {
  color-scheme: light;
  --background: #f3f5f4;
  --foreground: #17201d;
  --surface: #ffffff;
  --border: #d8dfdc;
  --accent: #176b51;
  --muted: #596660;
}

* {
  box-sizing: border-box;
}

html {
  min-width: 1280px;
  background: var(--background);
}

body {
  min-height: 100vh;
  margin: 0;
  color: var(--foreground);
  background: var(--background);
  font-family: var(--font-geist-sans), Arial, Helvetica, sans-serif;
}

:focus-visible {
  outline: 3px solid var(--accent);
  outline-offset: 3px;
}

.foundation-shell {
  display: grid;
  min-height: 100vh;
  place-items: center;
  padding: 24px;
}

.foundation-card {
  width: min(100%, 640px);
  padding: clamp(24px, 6vw, 48px);
  border: 1px solid var(--border);
  border-radius: 20px;
  background: var(--surface);
}

.foundation-kicker {
  margin: 0 0 12px;
  color: var(--accent);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.foundation-card h1 {
  margin: 0;
  font-size: clamp(2rem, 7vw, 3.5rem);
  line-height: 1;
  letter-spacing: -0.04em;
}

.foundation-card > p:not(.foundation-kicker) {
  max-width: 54ch;
  margin: 20px 0 0;
  color: var(--muted);
  line-height: 1.6;
}

.health-line {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 32px;
  padding-top: 20px;
  border-top: 1px solid var(--border);
  font-weight: 650;
}

.health-line span {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #9a5b15;
}

.health-line[data-status="connected"] span {
  background: var(--accent);
}

.health-line[data-status="unavailable"] span {
  background: #a43737;
}
```

- [ ] **Step 5: Executar o gate com os três estados cobertos**

```powershell
npm run test
npm run lint
npm run typecheck
npm run build
```

Esperado: três testes do diagnóstico aprovados e build sem avisos de segredo ou acesso externo.

- [ ] **Step 6: Commit do diagnóstico**

```powershell
git add gerec_leads/apps/web
git commit -m "feat(gerec-leads): adiciona diagnostico local testado"
```

---

### Task 5: Provar o fluxo local no navegador com Playwright

**Files:**

- Create: `gerec_leads/playwright.config.ts`
- Create: `gerec_leads/tests/e2e/foundation.spec.ts`
- Modify: `gerec_leads/package.json`
- Modify: `gerec_leads/package-lock.json`

- [ ] **Step 1: Instalar Playwright no workspace**

```powershell
npm install --save-dev @playwright/test@1.62.1
```

Adicionar ao `package.json` da raiz:

```json
{
  "scripts": {
    "test:e2e": "playwright test",
    "test:e2e:install": "playwright install chromium",
    "test:e2e:install:ci": "playwright install --with-deps chromium"
  }
}
```

- [ ] **Step 2: Configurar o servidor controlado pelo teste**

Criar `playwright.config.ts`:

```ts
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: "http://127.0.0.1:3000",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 1440, height: 900 },
      },
    },
  ],
  webServer: {
    command: "npm run dev",
    url: "http://127.0.0.1:3000",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
```

- [ ] **Step 3: Escrever o teste ponta a ponta antes de ajustar qualquer falha**

Criar `tests/e2e/foundation.spec.ts`:

```ts
import { expect, test } from "@playwright/test";

test("exibe a aplicação e a conexão local", async ({ page }) => {
  await page.goto("/");

  await expect(
    page.getByRole("heading", { level: 1, name: "Gerenciador de Leads WTG" }),
  ).toBeVisible();
  await expect(page.getByText("Supabase local conectado")).toBeVisible();
});
```

- [ ] **Step 4: Comprovar RED com o Supabase explicitamente parado**

```powershell
npm run test:e2e:install
npm run supabase:stop
npm run test:e2e
```

Esperado: `FAIL` porque o teste exige “Supabase local conectado” e o serviço foi parado deliberadamente. Registrar essa evidência RED. Se a falha ocorrer antes dessa asserção, diagnosticar navegador ausente, `.env.local` ausente, porta ocupada ou regressão da página; não alterar a expectativa correta para mascarar falha de infraestrutura.

- [ ] **Step 5: Garantir a infraestrutura e repetir**

```powershell
npm run supabase:start
npm run env:local
npm run test:e2e
```

Esperado: um teste aprovado no Chromium e nenhuma chave exibida na página, screenshot ou trace.

- [ ] **Step 6: Executar o gate e fazer commit**

```powershell
npm run check
npm run test:e2e
git add gerec_leads
git commit -m "test(gerec-leads): valida fundacao no navegador"
```

---

### Task 6: Adicionar CI isolado e testá-lo como contrato

**Files:**

- Create: `.github/workflows/gerec-leads-ci.yml`
- Create: `gerec_leads/tooling/tests/ci-contract.test.mjs`
- Modify: `gerec_leads/package.json`
- Modify: `gerec_leads/package-lock.json`

- [ ] **Step 1: Instalar o parser YAML e escrever o contrato antes do workflow**

```powershell
npm install --save-dev yaml@2.8.1
```

Criar `gerec_leads/tooling/tests/ci-contract.test.mjs`:

```js
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { parse } from "yaml";

const productRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const workflowPath = resolve(
  productRoot,
  "../.github/workflows/gerec-leads-ci.yml",
);

test("o CI permanece limitado ao Gerenciador de Leads", () => {
  const workflow = parse(readFileSync(workflowPath, "utf8"));

  assert.deepEqual(workflow.on.push.paths, ["gerec_leads/**"]);
  assert.deepEqual(workflow.on.pull_request.paths, ["gerec_leads/**"]);
  assert.equal(workflow.defaults.run["working-directory"], "gerec_leads");

  const steps = workflow.jobs.quality.steps;
  assert.equal(steps[0].uses, "actions/checkout@v7");

  const setupNode = steps.find((step) => step.uses === "actions/setup-node@v7");
  assert.ok(setupNode);
  assert.equal(setupNode.with["node-version"], 24);
  assert.equal(setupNode.with["cache-dependency-path"], "gerec_leads/package-lock.json");

  assert.deepEqual(
    steps.flatMap((step) => (step.run ? [step.run] : [])),
    [
      "npm ci",
      "npm run test:e2e:install:ci",
      "npm run supabase:start",
      "npm run env:local",
      "npm run check",
      "npm run test:e2e",
      "npm run supabase:stop",
    ],
  );

  const stopSupabase = steps.find((step) => step.run === "npm run supabase:stop");
  assert.equal(stopSupabase?.if, "always()");

  const serializedWorkflow = JSON.stringify(workflow);
  assert.equal(serializedWorkflow.includes("service_role"), false);
  assert.equal(serializedWorkflow.includes("SERVICE_ROLE_KEY"), false);
});
```

Adicionar à raiz:

```json
{
  "scripts": {
    "test:ci-contract": "node --test tooling/tests/ci-contract.test.mjs"
  }
}
```

Atualizar `check` para:

```json
"check": "npm run format:check && npm run lint && npm run typecheck && npm run test && npm run test:structure && npm run test:supabase-tooling && npm run test:ci-contract && npm run build"
```

- [ ] **Step 2: Executar o contrato e confirmar a falha**

```powershell
npm run test:ci-contract
```

Esperado: `FAIL` porque o único arquivo externo autorizado ainda não existe.

- [ ] **Step 3: Criar o workflow mínimo na raiz**

Criar `.github/workflows/gerec-leads-ci.yml`:

```yaml
name: Gerenciador de Leads CI

on:
  push:
    paths:
      - "gerec_leads/**"
  pull_request:
    paths:
      - "gerec_leads/**"

permissions:
  contents: read

concurrency:
  group: gerec-leads-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

defaults:
  run:
    working-directory: gerec_leads

jobs:
  quality:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - name: Checkout
        uses: actions/checkout@v7

      - name: Node.js 24
        uses: actions/setup-node@v7
        with:
          node-version: 24
          cache: npm
          cache-dependency-path: gerec_leads/package-lock.json

      - name: Instalar dependências
        run: npm ci

      - name: Instalar Chromium
        run: npm run test:e2e:install:ci

      - name: Iniciar Supabase local
        run: npm run supabase:start

      - name: Gerar ambiente público local
        run: npm run env:local

      - name: Verificações estáticas e unitárias
        run: npm run check

      - name: Teste ponta a ponta
        run: npm run test:e2e

      - name: Encerrar Supabase local
        if: always()
        run: npm run supabase:stop
```

Não mover scripts para `.github`; o workflow somente orquestra comandos definidos em `gerec_leads/package.json`.

- [ ] **Step 4: Executar o gate do contrato e o gate completo**

```powershell
npm run test:ci-contract
npm run check
npm run test:e2e
```

Esperado: tudo aprovado; o YAML é interpretado com `parse`, e gatilhos, diretório de trabalho, Node 24 e steps são validados semanticamente.

- [ ] **Step 5: Revisar o diff externo antes do commit**

```powershell
git diff -- .github/workflows/gerec-leads-ci.yml gerec_leads/package.json gerec_leads/tooling/tests/ci-contract.test.mjs
git diff --check
```

Confirmar visualmente: nenhum segredo, nenhuma referência às aplicações legadas e nenhuma regra comercial no workflow.

- [ ] **Step 6: Commit do CI**

```powershell
git add .github/workflows/gerec-leads-ci.yml gerec_leads/package.json gerec_leads/package-lock.json gerec_leads/tooling/tests/ci-contract.test.mjs
git commit -m "ci(gerec-leads): adiciona pipeline isolado"
```

---

### Task 7: Documentar operação e fechar o gate da Etapa 1

**Files:**

- Create: `gerec_leads/README.md`
- Create: `gerec_leads/docs/evidencias/etapa-1.md`
- Modify: `gerec_leads/ROADMAP.md`

- [ ] **Step 1: Criar um guia reproduzível**

Criar `README.md` com estas seções e comandos exatos:

````md
# Gerenciador de Leads WTG

Projeto novo e isolado. Antes de desenvolver, leia `AGENTS.md`, o SPEC e o roadmap.

## Pré-requisitos

- Node.js 24 LTS
- npm
- Docker Desktop em execução

## Primeira execução

```powershell
nvm use 24
npm ci
npm run test:e2e:install
npm run supabase:start
npm run env:local
npm run dev
```

Acesse `http://127.0.0.1:3000` e confirme “Supabase local conectado”.

## Verificação

```powershell
npm run check
npm run test:e2e
```

## Encerramento

```powershell
npm run supabase:stop
```

`.env.local` é gerado apenas com URL e chave pública locais e nunca deve ser versionado.
````

Ao aplicar esse trecho, use uma cerca externa de quatro crases ou `apply_patch` para preservar corretamente os blocos internos.

- [ ] **Step 2: Executar uma instalação limpa e todos os gates**

Com Docker ativo e Node 24 selecionado:

```powershell
npm ci
npm run supabase:start
npm run env:local
npm run format:check
npm run lint
npm run typecheck
npm run test
npm run test:structure
npm run test:supabase-tooling
npm run test:ci-contract
npm run build
npm run test:e2e
git diff --check
git status --short
```

Esperado: todos os comandos aprovados. Se qualquer comando falhar, não marcar a etapa como concluída e usar `systematic-debugging` antes de corrigir.

- [ ] **Step 3: Registrar a evidência somente após o gate verde**

Criar `docs/evidencias/etapa-1.md` com este conteúdo depois da execução bem-sucedida:

```md
# Evidência de conclusão da Etapa 1

- Data: 25 de agosto de 2026
- Ambiente: desenvolvimento local, Node.js 24 LTS e Supabase via Docker
- `npm ci`: aprovado
- `npm run format:check`: aprovado
- `npm run lint`: aprovado
- `npm run typecheck`: aprovado
- testes unitários e estruturais: aprovados
- contrato do CI: aprovado
- build de produção: aprovado
- Playwright/Chromium com Supabase local: aprovado
- verificação de whitespace com `git diff --check`: aprovada
- segredos e arquivos locais no Git: ausentes

A fundação executável foi validada sem antecipar regras de negócio das Etapas 2 a 4.
```

- [ ] **Step 4: Atualizar o estado do roadmap**

Somente depois dos resultados anteriores, trocar em `ROADMAP.md`:

```md
- **Estado atual:** Etapa 1 concluída; Etapa 2 aguardando planejamento
```

- [ ] **Step 5: Revisão final contra escopo**

```powershell
rg -n "TO[D]O|TB[D]|FIXM[E]|PLACEHOLDE[R]" gerec_leads/apps gerec_leads/integrations gerec_leads/supabase gerec_leads/tests gerec_leads/tooling .github/workflows/gerec-leads-ci.yml
rg -n "service_role|SERVICE_ROLE_KEY" gerec_leads/apps gerec_leads/tests .github/workflows/gerec-leads-ci.yml
git diff --stat
git diff --check
```

Esperado: nenhuma pendência ou segredo. A única ocorrência aceitável de `service_role` é documentação preventiva ou o teste que garante sua ausência; nunca um valor real.

- [ ] **Step 6: Commit de encerramento da etapa**

```powershell
git add gerec_leads/README.md gerec_leads/docs/evidencias/etapa-1.md gerec_leads/ROADMAP.md
git commit -m "docs(gerec-leads): conclui etapa 1"
```

## Critério final de aceite da Etapa 1

A Etapa 1 está concluída somente quando, em uma instalação limpa:

- Node.js 24 e o lockfile reproduzem a aplicação;
- Supabase local sobe via Docker e gera apenas configuração pública para a web;
- a página informa conexão real, configuração ausente e indisponibilidade sem quebrar;
- lint, formatação, typecheck, testes unitários, testes estruturais e build passam;
- Playwright comprova a aplicação e a conexão no Chromium;
- o CI executa os mesmos gates e observa somente `gerec_leads/**`;
- nenhum arquivo funcional, segredo ou dado do novo produto escapou do escopo aprovado;
- nenhuma regra comercial foi antecipada.

## Referências técnicas para a execução

- Node.js releases: <https://nodejs.org/en/about/previous-releases>
- Next.js installation: <https://nextjs.org/docs/app/getting-started/installation>
- Supabase local development: <https://supabase.com/docs/guides/local-development>
- Supabase CLI: <https://supabase.com/docs/reference/cli/introduction>
- Vitest guide: <https://vitest.dev/guide/>
- Playwright CI: <https://playwright.dev/docs/ci>
- GitHub Actions workflow syntax: <https://docs.github.com/actions/reference/workflows-and-actions/workflow-syntax>

## Plano histórico ou executável: `docs/superpowers/plans/2026-08-25-etapa-2-modelo-auth-rls.md`

# Etapa 2 — Modelo, Auth e RLS Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Criar o modelo completo de dados do Gerenciador de Leads, as cinco contas locais e o isolamento de administrador/vendedor comprovado por testes diretos no banco.

**Architecture:** O PostgreSQL/Supabase receberá migrações versionadas para identidade, fila, origem, operação e auditoria. A autorização será aplicada por RLS e funções auxiliares privadas; mutações críticas serão reservadas a comandos de domínio das etapas seguintes. O bootstrap local usará a API administrativa do Auth somente em processo server-side e nunca gravará segredos no repositório.

**Tech Stack:** Supabase CLI 2.115.0, PostgreSQL 17, Supabase Auth, SQL/pgTAP, Node.js 24, TypeScript/JavaScript tooling e Vitest.

**Spec:** `docs/superpowers/specs/2026-08-25-workbook-mock-fluxo-completo-design.md` e `SPEC_GERENCIADOR_DE_LEADS_WTG.md`.

## Global Constraints

- Todo código, migração, teste, documentação e configuração permanece dentro de `gerec_leads/`, exceto o workflow CI já aprovado.
- O SPEC é a fonte canônica; nenhuma regra de negócio será alterada silenciosamente.
- PostgreSQL decide fila, cursor, elegibilidade, propriedade, prazos, créditos e resultados.
- `service_role` nunca chega ao navegador, ao `.env.example` ou ao Git.
- Google Sheets é somente entrada; nesta etapa nenhuma planilha é lida ou escrita.
- A interface final será exclusivamente desktop com largura mínima de 1280 px; esta etapa não cria interface operacional.
- O vendedor só acessa próprios dados e histórico permitido; o administrador acessa o escopo global aprovado.
- Migrações novas nunca editam migrações aplicadas.
- Toda função nova deve ter teste que falhe antes da implementação, salvo configuração declarativa.
- Datas persistidas usam `timestamptz`; valores monetários usam `numeric`; identificadores SQL usam `snake_case` minúsculo.
- Dados de seed são sintéticos e não contêm contatos reais.

## Estrutura de arquivos

| Arquivo | Responsabilidade |
|---|---|
| `supabase/config.toml` | Desabilitar cadastro público e fixar política local de senha. |
| `supabase/migrations/20260825100000_create_private_helpers.sql` | Extensões, schema privado e funções auxiliares de papel. |
| `supabase/migrations/20260825101000_create_identity_queue.sql` | Perfis, vendedores, cursor e créditos. |
| `supabase/migrations/20260825102000_create_source_commercial.sql` | Importações, origem, pendências, campanhas, empresas e leads. |
| `supabase/migrations/20260825103000_create_operations_audit.sql` | Atribuições, SLA, feedbacks, tentativas, resultados, vendas, outbox e auditoria. |
| `supabase/migrations/20260825104000_enable_rls.sql` | RLS, grants mínimos, projeções e políticas por perfil. |
| `supabase/seed.sql` | Configurações sintéticas estáveis; não cria usuários Auth. |
| `tooling/supabase/local-runtime.mjs` | Ler status local sem imprimir chaves administrativas. |
| `tooling/supabase/bootstrap-local-users.mjs` | Criar/reconciliar as cinco contas e gravar credenciais somente em `supabase/.temp`. |
| `tooling/supabase/local-runtime.test.mjs` | Testes de parsing e não exposição de segredos. |
| `tooling/supabase/bootstrap-local-users.test.mjs` | Testes das regras de usuários, ordem e senha aleatória. |
| `supabase/tests/001_schema_contract.sql` | pgTAP para tabelas, colunas, constraints e índices. |
| `supabase/tests/002_rls_contract.sql` | pgTAP para habilitação de RLS e grants. |
| `tooling/tests/rls-integration.mjs` | Teste HTTP/Auth real de administrador, vendedor e chamada cruzada. |
| `package.json` | Comandos de bootstrap e teste de banco. |
| `docs/evidencias/etapa-2.md` | Evidências de comandos, contagens e decisões da etapa. |
| `ROADMAP.md` | Marcar Etapa 2 somente após todos os gates. |

## Interfaces produzidas

O plano produz estes contratos para as etapas seguintes:

```ts
type LocalSupabaseRuntime = {
  apiUrl: string;
  publishableKey: string;
  serviceRoleKey: string;
};

type LocalUserCredential = {
  email: string;
  password: string;
  role: "admin" | "seller";
  position: number | null;
};

type SellerProfile = {
  userId: string;
  fullName: string;
  email: string;
  role: "admin" | "seller";
  isActive: boolean;
};
```

Os comandos da Etapa 3 consumirão as tabelas e políticas deste plano sem atualizar diretamente colunas críticas pelo cliente.

---

### Task 1: Fixar configuração de Auth e contratos de tooling

**Files:**
- Modify: `supabase/config.toml`
- Modify: `package.json`
- Create: `tooling/supabase/local-runtime.mjs`
- Create: `tooling/supabase/local-runtime.test.mjs`
- Test: `tooling/tests/auth-config.test.mjs`

**Interfaces:**
- Produz `readLocalSupabaseRuntime({ cwd }): LocalSupabaseRuntime`.
- O parser consome `supabase status -o env` e exige `API_URL`, `PUBLISHABLE_KEY` ou `ANON_KEY` e `SERVICE_ROLE_KEY` apenas em memória.
- Nenhuma função imprime o valor de qualquer chave.

- [ ] **Step 1: Escrever os testes vermelhos de configuração**

```js
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

test("Auth local impede cadastro público", () => {
  const config = readFileSync("supabase/config.toml", "utf8");
  assert.match(config, /enable_signup\s*=\s*false/);
  assert.match(config, /\[auth\.email\][\s\S]*enable_signup\s*=\s*false/);
});

test("configuração não contém service_role em arquivo público", () => {
  const files = ["apps/web/.env.example", "README.md", "supabase/config.toml"];
  for (const file of files) assert.doesNotMatch(readFileSync(file, "utf8"), /service_role/i);
});
```

- [ ] **Step 2: Rodar o teste vermelho**

Run: `node --test tooling/tests/auth-config.test.mjs`

Expected: FAIL porque o Auth local ainda permite signup público.

- [ ] **Step 3: Implementar a configuração mínima**

Em `supabase/config.toml`, alterar somente:

```toml
[auth]
enable_signup = false
minimum_password_length = 12
password_requirements = "lower_upper_letters_digits_symbols"

[auth.email]
enable_signup = false
enable_confirmations = false
```

Adicionar em `package.json`:

```json
{
  "scripts": {
    "test:db": "supabase test db --local",
    "supabase:bootstrap-users": "node tooling/supabase/bootstrap-local-users.mjs"
  }
}
```

- [ ] **Step 4: Implementar o parser privado do runtime**

`tooling/supabase/local-runtime.mjs` deve exportar:

```js
export function parseLocalRuntimeEnv(source) {
  const values = Object.fromEntries(
    source.split(/\r?\n/).filter((line) => line.includes("=")).map((line) => {
      const index = line.indexOf("=");
      return [line.slice(0, index), line.slice(index + 1).replace(/^"|"$/g, "")];
    }),
  );
  const publishableKey = values.PUBLISHABLE_KEY ?? values.ANON_KEY;
  if (!values.API_URL || !publishableKey || !values.SERVICE_ROLE_KEY) {
    throw new Error("Supabase local sem configuração administrativa completa.");
  }
  return { apiUrl: values.API_URL, publishableKey, serviceRoleKey: values.SERVICE_ROLE_KEY };
}
```

`readLocalSupabaseRuntime({ cwd })` deve executar o binário local existente com `status -o env`, retornar o objeto acima e nunca fazer `console.log` do resultado bruto.

- [ ] **Step 5: Rodar testes verdes e checagem de segredos**

Run: `node --test tooling/tests/auth-config.test.mjs tooling/supabase/local-runtime.test.mjs`

Expected: PASS; nenhuma chave administrativa aparece no output.

- [ ] **Step 6: Commitar a configuração**

```bash
git add supabase/config.toml package.json tooling/supabase/local-runtime.mjs tooling/supabase/local-runtime.test.mjs tooling/tests/auth-config.test.mjs
git commit -m "feat(gerec-leads): prepara auth local e runtime seguro"
```

### Task 2: Criar helpers privados e identidade da fila

**Files:**
- Create: `supabase/migrations/20260825100000_create_private_helpers.sql`
- Create: `supabase/migrations/20260825101000_create_identity_queue.sql`
- Test: `supabase/tests/001_schema_contract.sql`

**Interfaces:**
- `private.current_user_role() returns text`.
- `private.is_admin() returns boolean`.
- `private.is_current_seller(seller_id uuid) returns boolean`.
- `profiles`, `seller_queue`, `queue_state` e `seller_skip_balances` ficam disponíveis para RLS e comandos.

- [ ] **Step 1: Escrever o teste vermelho do contrato de identidade**

```sql
begin;
select plan(11);
select has_table('public', 'profiles');
select has_table('public', 'seller_queue');
select has_table('public', 'queue_state');
select has_table('public', 'seller_skip_balances');
select has_column('public', 'profiles', 'user_id');
select has_column('public', 'profiles', 'role');
select col_type_is('public', 'profiles', 'role', 'text');
select col_has_check('public', 'profiles', 'profiles_role_check');
select col_is_pk('public', 'profiles', 'user_id');
select has_index('public', 'seller_queue', 'seller_queue_position_key');
select has_function('private', 'is_admin', 0);
select * from finish();
rollback;
```

- [ ] **Step 2: Rodar o teste vermelho**

Run: `npm run supabase:start; npm run test:db -- supabase/tests/001_schema_contract.sql`

Expected: FAIL informando que as tabelas ainda não existem.

- [ ] **Step 3: Criar schema privado e helpers mínimos**

```sql
create schema if not exists private;

create or replace function private.current_user_role()
returns text
language sql
stable
security definer
set search_path = ''
as $$
  select p.role
  from public.profiles p
  where p.user_id = (select auth.uid())
    and p.is_active = true;
$$;

create or replace function private.is_admin()
returns boolean
language sql
stable
security definer
set search_path = ''
as $$ select coalesce((select private.current_user_role()) = 'admin', false); $$;

create or replace function private.is_current_seller(target_seller_id uuid)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select target_seller_id = (select auth.uid())
    and (select private.current_user_role()) = 'seller';
$$;

revoke all on schema private from public, anon, authenticated, service_role;
revoke all on function private.current_user_role() from public, anon, authenticated, service_role;
revoke all on function private.is_admin() from public, anon, authenticated, service_role;
revoke all on function private.is_current_seller(uuid) from public, anon, authenticated, service_role;
```

- [ ] **Step 4: Criar tabelas de identidade e fila**

```sql
create table public.profiles (
  user_id uuid primary key references auth.users(id) on delete restrict,
  full_name text not null check (length(btrim(full_name)) >= 2),
  email citext not null unique,
  role text not null check (role in ('admin', 'seller')),
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.seller_queue (
  seller_id uuid primary key references public.profiles(user_id) on delete restrict,
  position smallint not null unique check (position between 1 and 4),
  is_paused boolean not null default false,
  version bigint not null default 0 check (version >= 0),
  updated_at timestamptz not null default now()
);

create table public.queue_state (
  singleton boolean primary key default true check (singleton = true),
  next_seller_id uuid not null references public.profiles(user_id) on delete restrict,
  version bigint not null default 0 check (version >= 0),
  updated_at timestamptz not null default now()
);

create table public.seller_skip_balances (
  seller_id uuid primary key references public.profiles(user_id) on delete restrict,
  balance integer not null default 0 check (balance >= 0),
  updated_at timestamptz not null default now()
);

create index seller_queue_position_idx on public.seller_queue(position);
create index seller_skip_balances_balance_idx on public.seller_skip_balances(balance);
```

- [ ] **Step 5: Conceder somente privilégios de leitura necessários à etapa**

```sql
revoke all on public.profiles, public.seller_queue, public.queue_state,
  public.seller_skip_balances from public, anon, authenticated;
grant select on public.profiles, public.seller_queue, public.seller_skip_balances
  to authenticated;
```

- [ ] **Step 6: Rodar o contrato de schema**

Run: `npm run supabase:reset; npm run test:db -- supabase/tests/001_schema_contract.sql`

Expected: PASS nas tabelas, tipos, chave primária, índice e helper privado.

- [ ] **Step 7: Commitar a identidade**

```bash
git add supabase/migrations/20260825100000_create_private_helpers.sql supabase/migrations/20260825101000_create_identity_queue.sql supabase/tests/001_schema_contract.sql
git commit -m "feat(gerec-leads): cria identidade e estado da fila"
```

### Task 3: Criar origem, campanhas, empresas e leads

**Files:**
- Create: `supabase/migrations/20260825102000_create_source_commercial.sql`
- Modify: `supabase/tests/001_schema_contract.sql`

**Interfaces:**
- `lead_source_records.lead_id` é nullable enquanto houver pendência de documento/Estado.
- `lead_source_records.source_lead_id` é a identidade estável do workbook.
- `campaigns`, `companies` e `leads` ficam prontos para os comandos de importação e fila das etapas seguintes.

- [ ] **Step 1: Adicionar asserções vermelhas para origem e ocorrência**

```sql
select has_table('public', 'import_runs');
select has_table('public', 'lead_source_records');
select has_table('public', 'source_data_issues');
select has_table('public', 'source_corrections');
select has_table('public', 'campaigns');
select has_table('public', 'companies');
select has_table('public', 'leads');
select has_table('public', 'source_snapshot_records');
select col_is_unique('public', 'lead_source_records', 'source_lead_id');
select col_is_pk('public', 'campaigns', 'id');
select col_is_pk('public', 'companies', 'id');
```

- [ ] **Step 2: Rodar o teste vermelho**

Run: `npm run test:db -- supabase/tests/001_schema_contract.sql`

Expected: FAIL nas tabelas de origem ainda ausentes.

- [ ] **Step 3: Criar as tabelas com constraints**

Implementar nesta migração:

```sql
create table public.import_runs (
  id uuid primary key default gen_random_uuid(),
  source_type text not null check (source_type in ('mock_workbook', 'google_sheets')),
  mode text not null check (mode in ('bootstrap', 'snapshot', 'incremental')),
  idempotency_key text not null unique,
  correlation_id uuid not null,
  status text not null check (status in ('running', 'completed', 'partial', 'failed')),
  rows_read integer not null default 0 check (rows_read >= 0),
  rows_created integer not null default 0 check (rows_created >= 0),
  rows_updated integer not null default 0 check (rows_updated >= 0),
  rows_ignored integer not null default 0 check (rows_ignored >= 0),
  rows_pending integer not null default 0 check (rows_pending >= 0),
  rows_failed integer not null default 0 check (rows_failed >= 0),
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  error_summary text
);

create table public.campaigns (
  id bigint generated always as identity primary key,
  external_id text,
  source_name text not null check (length(btrim(source_name)) > 0),
  display_name text not null check (length(btrim(display_name)) > 0),
  status text not null default 'pending_approval'
    check (status in ('pending_approval', 'approved', 'archived')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create unique index campaigns_external_id_uq on public.campaigns(external_id)
  where external_id is not null;
create unique index campaigns_source_name_fallback_uq
  on public.campaigns((lower(btrim(source_name)))) where external_id is null;

create table public.companies (
  id bigint generated always as identity primary key,
  document_type text check (document_type in ('cpf', 'cnpj')),
  document_normalized text,
  document_display text,
  legal_name text,
  state text check (state is null or state ~ '^[A-Z]{2}$'),
  owner_id uuid references public.profiles(user_id) on delete restrict,
  client_since timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check ((document_type is null and document_normalized is null)
    or (document_type is not null and document_normalized is not null))
);
create unique index companies_document_uq on public.companies(document_normalized)
  where document_normalized is not null;

create table public.leads (
  id bigint generated always as identity primary key,
  company_id bigint not null references public.companies(id) on delete restrict,
  campaign_id bigint not null references public.campaigns(id) on delete restrict,
  source_entered_at timestamptz not null,
  assignment_status text not null default 'ready'
    check (assignment_status in ('ready', 'parked', 'assigned', 'archived')),
  qualification_status text not null default 'pending'
    check (qualification_status in ('pending', 'qualified', 'disqualified')),
  conversion_status text not null default 'active'
    check (conversion_status in ('active', 'qualified_follow_up', 'closed_no_conversion', 'won')),
  current_assignee_id uuid references public.profiles(user_id) on delete restrict,
  feedback_due_at timestamptz,
  parked_reason text check (parked_reason is null or parked_reason in (
    'no_eligible_seller', 'owner_blocked', 'campaign_pending')),
  source_phase text,
  estimated_value numeric(14,2) check (estimated_value is null or estimated_value >= 0),
  archived_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create unique index leads_company_campaign_active_uq
  on public.leads(company_id, campaign_id) where archived_at is null;
create index leads_assignment_filter_idx
  on public.leads(assignment_status, source_entered_at, id) where archived_at is null;
create index leads_current_assignee_idx
  on public.leads(current_assignee_id, assignment_status) where archived_at is null;
create index leads_campaign_idx on public.leads(campaign_id, source_entered_at);

create table public.lead_source_records (
  id bigint generated always as identity primary key,
  source_lead_id text not null unique,
  import_run_id uuid not null references public.import_runs(id) on delete restrict,
  lead_id bigint references public.leads(id) on delete restrict,
  source_row integer not null check (source_row >= 2),
  source_entered_at timestamptz,
  campaign_external_id text,
  campaign_name text,
  mock_has_cnpj_or_mei text,
  full_name text,
  phone text,
  email citext,
  source_status text,
  row_hash text not null check (row_hash ~ '^[0-9a-f]{64}$'),
  normalized_payload jsonb not null,
  is_present boolean not null default true,
  removed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index lead_source_records_lead_idx on public.lead_source_records(lead_id);
create index lead_source_records_present_idx on public.lead_source_records(is_present, source_entered_at);

create table public.source_snapshot_records (
  import_run_id uuid not null references public.import_runs(id) on delete cascade,
  source_record_id bigint not null references public.lead_source_records(id) on delete cascade,
  observed_hash text not null check (observed_hash ~ '^[0-9a-f]{64}$'),
  outcome text not null check (outcome in ('created', 'updated', 'ignored', 'pending', 'error')),
  primary key (import_run_id, source_record_id)
);

create table public.source_data_issues (
  id bigint generated always as identity primary key,
  source_record_id bigint not null references public.lead_source_records(id) on delete restrict,
  field_name text not null check (field_name in ('document', 'state', 'campaign', 'contact_name', 'phone', 'email')),
  issue_code text not null,
  status text not null default 'open' check (status in ('open', 'resolved')),
  resolved_by uuid references public.profiles(user_id) on delete restrict,
  resolved_at timestamptz,
  created_at timestamptz not null default now()
);
create unique index source_data_issues_open_uq
  on public.source_data_issues(source_record_id, field_name) where status = 'open';

create table public.source_corrections (
  id bigint generated always as identity primary key,
  source_record_id bigint not null references public.lead_source_records(id) on delete restrict,
  field_name text not null check (field_name in ('document', 'state')),
  value text not null check (length(btrim(value)) > 0),
  normalized_value text not null,
  actor_id uuid not null references public.profiles(user_id) on delete restrict,
  active boolean not null default true,
  created_at timestamptz not null default now()
);
create unique index source_corrections_active_uq
  on public.source_corrections(source_record_id, field_name) where active;
```

- [ ] **Step 4: Adicionar todos os índices de foreign key**

Criar índices para `import_run_id`, `campaign_id`, `company_id`, `lead_id`, `source_record_id` e `owner_id` em todas as tabelas que os referenciarem. Verificar com a consulta de constraints do skill Supabase antes de prosseguir.

- [ ] **Step 5: Rodar schema e validar pendência sem empresa fictícia**

Run: `npm run supabase:reset; npm run test:db -- supabase/tests/001_schema_contract.sql`

Expected: PASS; o schema aceita `lead_source_records.lead_id` nulo e rejeita documento inválido quando uma empresa for criada.

- [ ] **Step 6: Commitar origem e comercial**

```bash
git add supabase/migrations/20260825102000_create_source_commercial.sql supabase/tests/001_schema_contract.sql
git commit -m "feat(gerec-leads): cria origem e entidades comerciais"
```

### Task 4: Criar operações, histórico e outbox

**Files:**
- Create: `supabase/migrations/20260825103000_create_operations_audit.sql`
- Modify: `supabase/tests/001_schema_contract.sql`

**Interfaces:**
- Tabelas de evento são append-only para o domínio.
- Toda tabela operacional contém as chaves necessárias para rastrear atribuição, autor e idempotência.

- [ ] **Step 1: Escrever asserções vermelhas**

```sql
select has_table('public', 'assignments');
select has_table('public', 'feedback_cycles');
select has_table('public', 'feedbacks');
select has_table('public', 'contact_attempts');
select has_table('public', 'qualification_events');
select has_table('public', 'sales');
select has_table('public', 'business_holidays');
select has_table('public', 'notification_outbox');
select has_table('public', 'audit_log');
select col_is_unique('public', 'sales', 'id');
```

- [ ] **Step 2: Rodar o teste vermelho**

Run: `npm run test:db -- supabase/tests/001_schema_contract.sql`

Expected: FAIL porque as tabelas operacionais ainda não existem.

- [ ] **Step 3: Criar as tabelas de operação**

Criar estas definições, mantendo checks e índices:

```sql
create table public.assignments (
  id bigint generated always as identity primary key,
  lead_id bigint not null references public.leads(id) on delete restrict,
  seller_id uuid not null references public.profiles(user_id) on delete restrict,
  assignment_type text not null check (assignment_type in ('normal', 'recurring', 'temporary', 'permanent_transfer')),
  started_at timestamptz not null default now(),
  ended_at timestamptz,
  actor_id uuid references public.profiles(user_id) on delete restrict,
  reason text,
  idempotency_key text not null unique,
  check (ended_at is null or ended_at >= started_at)
);
create unique index assignments_current_lead_uq
  on public.assignments(lead_id) where ended_at is null;
create index assignments_seller_idx on public.assignments(seller_id, started_at, ended_at);

create table public.feedback_cycles (
  id bigint generated always as identity primary key,
  lead_id bigint not null references public.leads(id) on delete restrict,
  assignment_id bigint not null references public.assignments(id) on delete restrict,
  cycle_number integer not null check (cycle_number >= 1),
  starts_at timestamptz not null,
  reminder_at timestamptz not null,
  due_at timestamptz not null,
  closed_at timestamptz,
  close_reason text,
  unique (lead_id, cycle_number),
  check (reminder_at <= due_at),
  check (closed_at is null or closed_at >= starts_at)
);
create unique index feedback_cycles_open_lead_uq on public.feedback_cycles(lead_id) where closed_at is null;
create index feedback_cycles_due_idx on public.feedback_cycles(due_at) where closed_at is null;

create table public.feedbacks (
  id bigint generated always as identity primary key,
  lead_id bigint not null references public.leads(id) on delete restrict,
  assignment_id bigint not null references public.assignments(id) on delete restrict,
  seller_id uuid not null references public.profiles(user_id) on delete restrict,
  comment text not null check (length(btrim(comment)) >= 6),
  contact_started boolean not null check (contact_started),
  idempotency_key text not null unique,
  created_at timestamptz not null default now()
);
create index feedbacks_lead_idx on public.feedbacks(lead_id, created_at);

create table public.contact_attempts (
  id bigint generated always as identity primary key,
  lead_id bigint not null references public.leads(id) on delete restrict,
  assignment_id bigint not null references public.assignments(id) on delete restrict,
  seller_id uuid not null references public.profiles(user_id) on delete restrict,
  channel text not null check (channel = 'whatsapp'),
  business_date date not null,
  comment text not null check (length(btrim(comment)) >= 6),
  idempotency_key text not null unique,
  created_at timestamptz not null default now(),
  unique (lead_id, business_date)
);

create table public.qualification_events (
  id bigint generated always as identity primary key,
  lead_id bigint not null references public.leads(id) on delete restrict,
  assignment_id bigint not null references public.assignments(id) on delete restrict,
  actor_id uuid not null references public.profiles(user_id) on delete restrict,
  outcome text not null check (outcome in ('qualified_follow_up', 'qualified_closed_no_conversion', 'disqualified', 'won', 'reversed')),
  reason text check (reason is null or reason in ('no_answer_after_five_attempts', 'no_cnpj', 'outside_sp')),
  comment text not null check (length(btrim(comment)) >= 6),
  idempotency_key text not null unique,
  reversed_event_id bigint references public.qualification_events(id) on delete restrict,
  created_at timestamptz not null default now(),
  check ((outcome = 'disqualified' and reason is not null) or (outcome <> 'disqualified'))
);
create index qualification_events_lead_idx on public.qualification_events(lead_id, created_at);

create table public.sales (
  id bigint generated always as identity primary key,
  lead_id bigint not null references public.leads(id) on delete restrict,
  credited_seller_id uuid not null references public.profiles(user_id) on delete restrict,
  qualification_event_id bigint not null unique references public.qualification_events(id) on delete restrict,
  comment text not null check (length(btrim(comment)) >= 6),
  won_at timestamptz not null default now(),
  reversed_at timestamptz,
  reversed_by uuid references public.profiles(user_id) on delete restrict
);
create unique index sales_active_lead_uq on public.sales(lead_id) where reversed_at is null;

create table public.business_holidays (
  holiday_date date not null,
  scope text not null check (scope in ('national', 'sp')),
  name text not null check (length(btrim(name)) > 0),
  primary key (holiday_date, scope)
);
```

- [ ] **Step 4: Criar auditoria, outbox e configurações**

```sql
create table public.notification_outbox (
  id uuid primary key default gen_random_uuid(),
  event_type text not null,
  aggregate_type text not null,
  aggregate_id text not null,
  idempotency_key text not null unique,
  payload jsonb not null,
  status text not null default 'pending' check (status in ('pending', 'processing', 'sent', 'failed')),
  attempts integer not null default 0 check (attempts >= 0),
  available_at timestamptz not null default now(),
  last_error text,
  created_at timestamptz not null default now(),
  processed_at timestamptz
);
create index notification_outbox_pending_idx on public.notification_outbox(status, available_at);

create table public.notification_incidents (
  id uuid primary key default gen_random_uuid(),
  incident_type text not null check (incident_type = 'parked_threshold'),
  opened_at timestamptz not null default now(),
  resolved_at timestamptz
);
create unique index notification_incidents_open_uq
  on public.notification_incidents(incident_type) where resolved_at is null;

create table public.audit_log (
  id bigint generated always as identity primary key,
  actor_id uuid references public.profiles(user_id) on delete restrict,
  action text not null,
  entity_type text not null,
  entity_id text not null,
  before_data jsonb,
  after_data jsonb,
  correlation_id uuid not null,
  created_at timestamptz not null default now()
);
create index audit_log_entity_idx on public.audit_log(entity_type, entity_id, created_at);

create table public.system_settings (
  singleton boolean primary key default true check (singleton = true),
  timezone text not null default 'America/Sao_Paulo',
  feedback_hours integer not null default 24 check (feedback_hours > 0),
  reminder_hours integer not null default 4 check (reminder_hours > 0 and reminder_hours < feedback_hours),
  parked_threshold integer not null default 2 check (parked_threshold >= 2),
  digest_time time not null default time '09:00:00',
  updated_at timestamptz not null default now()
);
```

- [ ] **Step 5: Atualizar seed sintético**

`supabase/seed.sql` deve inserir somente:

```sql
insert into public.system_settings(singleton) values (true) on conflict (singleton) do nothing;
insert into public.business_holidays(holiday_date, scope, name) values
  ('2026-01-01', 'national', 'Confraternização Universal'),
  ('2026-04-21', 'national', 'Tiradentes'),
  ('2026-09-07', 'national', 'Independência do Brasil'),
  ('2026-10-12', 'national', 'Nossa Senhora Aparecida'),
  ('2026-11-02', 'national', 'Finados'),
  ('2026-11-15', 'national', 'Proclamação da República'),
  ('2026-11-20', 'national', 'Consciência Negra'),
  ('2026-12-25', 'national', 'Natal')
on conflict do nothing;
```

Datas adicionais de teste serão inseridas dentro de transações de teste, não como regra permanente do seed.

- [ ] **Step 6: Rodar o contrato completo**

Run: `npm run supabase:reset; npm run test:db -- supabase/tests/001_schema_contract.sql`

Expected: PASS para todas as tabelas, checks, índices e settings.

- [ ] **Step 7: Commitar operações e auditoria**

```bash
git add supabase/migrations/20260825103000_create_operations_audit.sql supabase/seed.sql supabase/tests/001_schema_contract.sql
git commit -m "feat(gerec-leads): cria operação, histórico e outbox"
```

### Task 5: Aplicar RLS e grants por perfil

**Files:**
- Create: `supabase/migrations/20260825104000_enable_rls.sql`
- Create: `supabase/tests/002_rls_contract.sql`

**Interfaces:**
- Todas as tabelas comerciais têm RLS habilitada e forçada.
- Leitura administrativa é global.
- Leitura de vendedor é limitada a atribuição atual ou ao histórico próprio permitido.
- Tabelas de origem técnica, auditoria, outbox e conflitos não são consultáveis diretamente pelo vendedor.

- [ ] **Step 1: Escrever testes vermelhos de RLS e grants**

```sql
begin;
select plan(12);
select policies_are('public', 'profiles', array['profiles_select_self_or_admin']);
select policies_are('public', 'leads', array['leads_admin_select', 'leads_current_seller_select']);
select policies_are('public', 'feedbacks', array['feedbacks_admin_select', 'feedbacks_current_or_historical_select']);
select policies_are('public', 'contact_attempts', array['attempts_admin_select', 'attempts_current_or_historical_select']);
select policies_are('public', 'audit_log', array['audit_admin_select']);
select policies_are('public', 'notification_outbox', array['outbox_admin_select']);
select table_privilege_is('authenticated', 'public', 'profiles', 'SELECT', true);
select table_privilege_is('authenticated', 'public', 'leads', 'UPDATE', false);
select table_privilege_is('authenticated', 'public', 'audit_log', 'SELECT', false);
select has_function('private', 'current_user_role', 0);
select has_function('private', 'is_admin', 0);
select * from finish();
rollback;
```

- [ ] **Step 2: Rodar o teste vermelho**

Run: `npm run test:db -- supabase/tests/002_rls_contract.sql`

Expected: FAIL porque políticas e grants ainda não existem.

- [ ] **Step 3: Habilitar RLS em todas as tabelas comerciais**

Executar `alter table ... enable row level security; alter table ... force row level security;` para `profiles`, `seller_queue`, `queue_state`, `seller_skip_balances`, `import_runs`, `campaigns`, `companies`, `leads`, `lead_source_records`, `source_snapshot_records`, `source_data_issues`, `source_corrections`, `assignments`, `feedback_cycles`, `feedbacks`, `contact_attempts`, `qualification_events`, `sales`, `business_holidays`, `field_overrides`, `source_conflicts`, `notification_outbox`, `notification_incidents`, `audit_log` e `system_settings`.

- [ ] **Step 4: Criar funções de escopo server-side**

Adicionar helpers privados para:

```sql
create or replace function private.can_read_current_lead(target_lead_id bigint)
returns boolean language sql stable security definer set search_path = '' as $$
  select exists (
    select 1 from public.leads l
    where l.id = target_lead_id
      and l.current_assignee_id = (select auth.uid())
      and (select private.current_user_role()) = 'seller'
  );
$$;

create or replace function private.can_read_own_assignment(target_assignment_id bigint)
returns boolean language sql stable security definer set search_path = '' as $$
  select exists (
    select 1 from public.assignments a
    where a.id = target_assignment_id and a.seller_id = (select auth.uid())
  );
$$;
```

As funções devem validar o papel internamente e ter execução revogada para os papéis de API.

- [ ] **Step 5: Criar políticas de leitura**

Usar `((select auth.uid()) = column)` ou helpers encapsulados, nunca chamada não-cacheada por linha. O núcleo das políticas será:

```sql
create policy profiles_select_self_or_admin on public.profiles
for select to authenticated
using ((select private.is_admin()) or user_id = (select auth.uid()));

create policy leads_admin_select on public.leads
for select to authenticated
using ((select private.is_admin()));

create policy leads_current_seller_select on public.leads
for select to authenticated
using ((select private.can_read_current_lead(id)));

create policy feedbacks_current_or_historical_select on public.feedbacks
for select to authenticated
using (
  (select private.is_admin())
  or seller_id = (select auth.uid())
  or (select private.can_read_current_lead(lead_id))
);

create policy audit_admin_select on public.audit_log
for select to authenticated using ((select private.is_admin()));
```

Aplicar a mesma regra de histórico próprio para `contact_attempts`, `qualification_events` e `assignments`. `feedback_cycles` será filtrada pelo `assignment_id`. `lead_source_records` e tabelas técnicas terão leitura administrativa somente nesta etapa; a projeção M–P do vendedor será um RPC da Etapa 5.

- [ ] **Step 6: Revogar escrita direta e expor somente leitura necessária**

```sql
revoke all on all tables in schema public from anon, authenticated;
grant select on public.profiles, public.seller_queue, public.seller_skip_balances,
  public.campaigns, public.companies, public.leads, public.assignments,
  public.feedback_cycles, public.feedbacks, public.contact_attempts,
  public.qualification_events, public.sales to authenticated;
```

Depois do `revoke`, conceder `select` apenas nas tabelas listadas e manter `audit_log`, `notification_outbox`, conflitos e origem técnica restritos ao administrador via policies. Nenhuma tabela recebe `insert`, `update` ou `delete` do cliente.

- [ ] **Step 7: Rodar contrato de RLS**

Run: `npm run supabase:reset; npm run test:db -- supabase/tests/002_rls_contract.sql`

Expected: PASS; RLS habilitada, policies nomeadas e mutações diretas negadas.

- [ ] **Step 8: Commitar RLS**

```bash
git add supabase/migrations/20260825104000_enable_rls.sql supabase/tests/002_rls_contract.sql
git commit -m "feat(gerec-leads): protege dados com RLS e grants mínimos"
```

### Task 6: Criar bootstrap idempotente das cinco contas

**Files:**
- Create: `tooling/supabase/bootstrap-local-users.mjs`
- Create: `tooling/supabase/bootstrap-local-users.test.mjs`
- Modify: `supabase/seed.sql`

**Interfaces:**
- `buildLocalUsers()` retorna a ordem canônica sem senha fixa.
- `bootstrapLocalUsers({ runtime, writeCredentials })` cria ou atualiza contas usando somente a API administrativa.
- Credenciais são gravadas em `supabase/.temp/local-users.json`, ignorado pelo Git.

- [ ] **Step 1: Escrever teste vermelho sem tocar Auth real**

```js
import test from "node:test";
import assert from "node:assert/strict";
import { buildLocalUsers } from "./bootstrap-local-users.mjs";

test("contas locais preservam ordem e papéis canônicos", () => {
  const users = buildLocalUsers(() => "SenhaLocal-A1!");
  assert.deepEqual(users.map(({ email }) => email), [
    "yago@wtgseguros.com.br",
    "renato@wtgseguros.com.br",
    "sandracristina@wtgseguros.com.br",
    "jessicaalmeida@wtgseguros.com.br",
    "nelmacastro@wtgseguros.com.br",
  ]);
  assert.equal(users[0].role, "admin");
  assert.deepEqual(users.slice(1).map(({ position }) => position), [1, 2, 3, 4]);
});

test("senha gerada não é constante", () => {
  const first = buildLocalUsers(() => crypto.randomUUID());
  const second = buildLocalUsers(() => crypto.randomUUID());
  assert.notEqual(first[0].password, second[0].password);
});
```

- [ ] **Step 2: Rodar o teste vermelho**

Run: `node --test tooling/supabase/bootstrap-local-users.test.mjs`

Expected: FAIL porque o bootstrap ainda não existe.

- [ ] **Step 3: Implementar criação/reconciliação**

O script deve:

1. obter `LocalSupabaseRuntime` sem imprimir valores;
2. criar cliente Supabase com `serviceRoleKey` somente em memória;
3. usar `auth.admin.listUsers`, `createUser` ou `updateUserById`;
4. confirmar e-mail localmente;
5. fazer upsert de `profiles` com papel e posição;
6. fazer upsert de `seller_queue`, `seller_skip_balances` e `queue_state`;
7. gerar senha com `crypto.randomBytes` e alfabeto seguro;
8. gravar apenas o conjunto de credenciais em `supabase/.temp/local-users.json`;
9. imprimir somente os e-mails e o caminho do arquivo, nunca senhas ou chaves.

O arquivo terá modo JSON com:

```json
{
  "generatedAt": "2026-08-25T00:00:00.000Z",
  "users": [{ "email": "yago@wtgseguros.com.br", "password": "...", "role": "admin", "position": null }]
}
```

- [ ] **Step 4: Rodar teste unitário e bootstrap local**

Run: `node --test tooling/supabase/bootstrap-local-users.test.mjs; npm run supabase:bootstrap-users`

Expected: testes PASS; cinco usuários aparecem no Auth local e o arquivo ignorado é criado sem aparecer no `git status`.

- [ ] **Step 5: Validar login com cliente público**

Usar as credenciais do arquivo local em um script de teste, sem imprimir senha:

```js
const { data, error } = await publicClient.auth.signInWithPassword({ email, password });
assert.ifError(error);
assert.ok(data.session?.access_token);
```

- [ ] **Step 6: Commitar bootstrap**

```bash
git add tooling/supabase/bootstrap-local-users.mjs tooling/supabase/bootstrap-local-users.test.mjs supabase/seed.sql
git commit -m "feat(gerec-leads): provisiona contas locais aleatórias"
```

### Task 7: Provar RLS com chamadas autenticadas

**Files:**
- Create: `tooling/tests/rls-integration.mjs`
- Modify: `package.json`

**Interfaces:**
- O teste usa somente URL e chave pública no cliente do usuário.
- O administrador pode consultar a fila completa e os leads globais.
- Cada vendedor consulta apenas a própria posição e não consegue consultar o lead de outro vendedor pela API.

- [ ] **Step 1: Escrever teste vermelho de isolamento**

Criar dados sintéticos dentro de uma transação/fixture controlada com dois vendedores, dois leads e atribuições atuais. O teste deve autenticar Renato e Sandra e executar:

```js
const renatoRows = await renatoClient.from("leads").select("id,current_assignee_id");
assert.equal(renatoRows.error, null);
assert.deepEqual(renatoRows.data.map(({ current_assignee_id }) => current_assignee_id), [renatoId]);

const crossRead = await renatoClient.from("leads").select("*").eq("id", sandraLeadId);
assert.equal(crossRead.error, null);
assert.deepEqual(crossRead.data, []);

const directUpdate = await renatoClient.from("leads").update({ current_assignee_id: renatoId }).eq("id", sandraLeadId);
assert.ok(directUpdate.error);
```

- [ ] **Step 2: Rodar teste vermelho**

Run: `node tooling/tests/rls-integration.mjs`

Expected: FAIL até o bootstrap, dados sintéticos e policies estarem disponíveis.

- [ ] **Step 3: Criar fixture controlada de integração**

Implementar comandos server-side de teste que usem `service_role` somente no processo do teste, insiram dois vendedores/atribuições e removam os dados ao final. O cliente de cada vendedor deve usar exclusivamente a chave pública e o token retornado pelo Auth.

- [ ] **Step 4: Rodar teste verde e testar histórico pós-transferência**

Adicionar caso em que Renato possui feedback próprio, o lead é atribuído a Sandra e Renato consegue ler apenas o feedback dele, sem ler o feedback posterior de Sandra.

Run: `npm run supabase:reset; npm run supabase:bootstrap-users; node tooling/tests/rls-integration.mjs`

Expected: PASS sem dados cruzados e sem mutação direta crítica.

- [ ] **Step 5: Adicionar comando de CI local**

Em `package.json`:

```json
{
  "scripts": {
    "test:rls": "node tooling/tests/rls-integration.mjs",
    "test:etapa-2": "npm run test:db && npm run test:rls"
  }
}
```

- [ ] **Step 6: Commitar integração RLS**

```bash
git add tooling/tests/rls-integration.mjs package.json
git commit -m "test(gerec-leads): prova isolamento por perfil"
```

### Task 8: Evidenciar e fechar a Etapa 2

**Files:**
- Create: `docs/evidencias/etapa-2.md`
- Modify: `ROADMAP.md`
- Modify: `docs/ARQUITETURA.md`

- [ ] **Step 1: Rodar a verificação completa da etapa**

Run: `npm run supabase:reset; npm run supabase:bootstrap-users; npm run test:etapa-2; npm run check`

Expected: todos os contratos, testes RLS, lint, tipos, testes existentes e build passam.

- [ ] **Step 2: Registrar evidência sem segredos**

Documentar somente comandos, contagens, hash das migrações, resultado dos testes, perfis exercitados e limitações locais. Nunca copiar `service_role`, senhas ou payloads pessoais.

- [ ] **Step 3: Atualizar o roadmap com o gate correto**

Marcar Etapa 2 como concluída apenas se:

- migrações reproduzem o schema;
- cinco contas locais funcionam;
- RLS impede acesso cruzado por API direta;
- não há falha crítica;
- evidência foi registrada.

Manter Etapa 3 como próxima etapa em andamento; não marcar ingestão ou frontend como concluídos.

- [ ] **Step 4: Commitar evidência**

```bash
git add docs/evidencias/etapa-2.md ROADMAP.md docs/ARQUITETURA.md
git commit -m "docs(gerec-leads): fecha gate de modelo auth e rls"
```

## Planos seguintes

Após o gate desta etapa, criar e revisar planos independentes, sem alterar este documento:

1. `2026-08-25-etapa-3-nucleo-transacional.md`: calendário, SLA, fila, locks, propriedade, recorrência, créditos, comandos e concorrência.
2. `2026-08-25-etapa-4-ingestao-operacao.md`: adapter do workbook, snapshot, pendências, campanhas, feedbacks, resultados, overrides e outbox.
3. `2026-08-25-etapa-5-frontend-admin.md`: login, shell, dashboard, sincronização, pendências, campanhas, fila, leads e auditoria.
4. `2026-08-25-etapa-6-frontend-vendedor.md`: dashboard privado, detalhe, feedback, tentativas, resultados, E2E e hardening visual.

Cada plano seguinte consumirá somente interfaces testadas da etapa anterior e terá seu próprio commit, evidência e gate no `ROADMAP.md`.

## Verificação do plano

- Cobertura do SPEC: identidade/Auth/RLS (seções 8, 9 e 28), origem e pendências (12 e 13), modelo (25), segurança (28), falhas (29), auditoria (30), testes (33) e governança (39) estão mapeados nas Tasks 1–8.
- Concorrência do cursor, SLA, importação prática e frontend não são implementados neste plano; estão explicitamente reservados aos planos 3–6.
- Não há marcador de incompletude, função sem assinatura ou dependência de planilha definitiva.
- Todas as migrations são novas e ordenadas por timestamp.
- O contrato de runtime não expõe chave administrativa.

## Plano histórico ou executável: `docs/superpowers/plans/2026-08-26-mvp-dashboard-perfis.md`

# MVP Dashboard por Perfil — Plano de Implementação

> **Para agentes:** executar as tarefas em ordem, com TDD e checkpoints de verificação.

**Objetivo:** substituir o health check por um sistema desktop funcional, com login Supabase, visão global do administrador e visão restrita de cada vendedor.

**Arquitetura:** Next.js App Router com páginas server-side e componentes client apenas para interação. O Supabase Auth identifica o usuário; as consultas de leads usam RLS como segunda barreira. Dados sintéticos serão inseridos por seed apenas para desenvolvimento local.

**Stack:** Next.js 16, React 19, TypeScript, Supabase local, CSS próprio e Vitest.

**Spec:** `docs/superpowers/specs/2026-08-25-workbook-mock-fluxo-completo-design.md` e `SPEC_GERENCIADOR_DE_LEADS_WTG.md`.

## Restrições globais

- Desktop only: manter largura mínima de 1280px.
- Vendedor vê apenas seus leads atuais/históricos permitidos; administrador vê todos.
- Horários exibidos em `America/Sao_Paulo`.
- Chaves administrativas permanecem no servidor e nunca no bundle do navegador.
- Interface deve mostrar estados de carregamento, vazio, erro e atraso de SLA.

### Tarefa 1: Cliente Supabase server e sessão

**Arquivos:** criar `apps/web/src/lib/supabase/server.ts`, `apps/web/src/lib/auth/get-session-context.ts`; criar testes correspondentes.

- Escrever testes para sessão ausente, perfil admin e perfil seller.
- Implementar cliente server com cookies e leitura do perfil.
- Criar redirect de sessão ausente para `/login`.
- Verificar com `npm --workspace @wtg/web run test` e `typecheck`.

### Tarefa 2: Seed de leads demonstrativos

**Arquivos:** modificar `supabase/seed.sql`; criar `supabase/tests/003_demo_seed.sql`.

- Inserir cinco perfis/usuários apenas via bootstrap já existente e inserir campanhas, empresas, leads e atribuições sintéticas usando os IDs encontrados por e-mail.
- Criar horários de feedback passados, próximos e normais para demonstrar SLA.
- Validar contagem, status e ausência de dados de vendedor cruzado por RLS.

### Tarefa 3: Login e shell de aplicação

**Arquivos:** substituir `apps/web/src/app/page.tsx`; criar `apps/web/src/app/login/page.tsx`, `apps/web/src/app/dashboard/page.tsx`, `apps/web/src/components/app-shell.tsx` e estilos.

- Login por e-mail/senha local.
- Shell com marca WTG, usuário atual, perfil, relógio local, sair e navegação.
- Renderizar estado de indisponibilidade sem esconder a causa.

### Tarefa 4: Dashboard administrativo

**Arquivos:** criar `apps/web/src/components/admin-dashboard.tsx` e `apps/web/src/lib/dashboard/admin-data.ts`.

- Cards de total, em fila, atrasados, pendências e ganhos.
- Tabela global com lead, contato M–P, vendedor, status, prazo e última atividade.
- Filtros por vendedor/status e ordenação por SLA.

### Tarefa 5: Dashboard do vendedor

**Arquivos:** criar `apps/web/src/components/seller-dashboard.tsx` e `apps/web/src/lib/dashboard/seller-data.ts`.

- Mostrar somente leads retornados pela política RLS para o usuário autenticado.
- Cards de minha fila, feedbacks hoje, atrasados e tentativas.
- Tabela com contato, prazo, estado e ações desabilitadas quando houver bloqueio de SLA.

### Tarefa 6: Interações e testes de isolamento

**Arquivos:** criar `apps/web/src/components/lead-actions.tsx`, testes Vitest e teste Playwright.

- Feedback/tentativa/resultados terão controles visuais e mensagens de validação; mutações transacionais completas ficam para a Etapa 3.
- Testar que admin recebe visão global e seller recebe somente seus registros.
- Rodar format, lint, typecheck, testes web, contratos Supabase e build.


## Plano histórico ou executável: `docs/superpowers/plans/2026-08-27-migracao-mongodb-vercel-railway.md`

# Migração MongoDB, Vercel e Railway — Plano de Implementação

> **Para agentes:** REQUISITO: usar `superpowers:subagent-driven-development` (recomendado) ou `superpowers:executing-plans` para executar este plano tarefa por tarefa. Os passos usam caixas de seleção (`- [ ]`).

**Objetivo:** substituir integralmente Supabase/PostgreSQL por um backend Python transacional na Railway, MongoDB como banco único e site Next.js publicado na Vercel.

**Arquitetura:** O navegador acessa somente o site Next.js na Vercel. O site chama uma API Python na Railway. API e workers Python compartilham o database MongoDB `gerec_leads`; apenas o backend possui a URI e credenciais. Regras de fila, SLA, propriedade, resultados e auditoria vivem nos módulos de domínio Python e são confirmadas em transações MongoDB.

**Stack:** Python 3.12+, FastAPI, PyMongo, Pydantic Settings, Argon2id, pytest, MongoDB replica set, Next.js 16, React 19, TypeScript e Playwright.

**Spec:** `docs/superpowers/specs/2026-08-27-migracao-mongodb-design.md` e `SPEC_GERENCIADOR_DE_LEADS_WTG.md`, após atualização canônica prevista na Tarefa 1.

## Restrições globais

- O MongoDB é o único banco e usa o database `gerec_leads`.
- A Vercel hospeda somente o site Next.js e assets públicos.
- A Railway hospeda a API Python e automações Python.
- O navegador nunca recebe URI, usuário ou senha do MongoDB.
- O MongoDB local, staging e produção operam com replica set para transações.
- O SPEC continua sendo a fonte de verdade das regras de negócio.
- A interface continua exclusivamente desktop, com largura mínima suportada de 1280 px.
- Senhas são derivadas com Argon2id ou scrypt; nunca são armazenadas em texto puro.
- Todo comando crítico possui idempotência, auditoria e teste de rollback/concorrência.
- Dados do workbook mock permanecem sintéticos; a coluna `você_tem_cnpj_ou_mei?` não é CNPJ.
- Nenhuma migração de dados comerciais será feita, pois o MongoDB está vazio.

## Arquivos e módulos

| Área | Arquivos principais | Responsabilidade |
|---|---|---|
| Backend Python | `apps/api/pyproject.toml`, `apps/api/src/gerec_api/` | API, autenticação, domínio e acesso ao MongoDB |
| Domínio | `apps/api/src/gerec_api/domain/` | Fila, SLA, leads, resultados e invariantes |
| Persistência | `apps/api/src/gerec_api/infrastructure/mongo/` | Cliente, transações, coleções e índices |
| Automação | `apps/api/src/gerec_api/automation/` | Sync do workbook, outbox, e-mails e jobs Railway |
| Site | `apps/web/src/` | Telas e cliente HTTP da API Python |
| Infra local | `infra/mongodb/`, `scripts/` | Replica set, variáveis e comandos locais |
| Contratos | `tests/contracts/`, `apps/api/tests/`, `tests/e2e/` | Contratos, integração, concorrência e E2E |

---

### Tarefa 1: Registrar a mudança canônica de arquitetura

**Arquivos:**
- Modificar: `SPEC_GERENCIADOR_DE_LEADS_WTG.md` nas seções 6, 7, 25, 26, 28, 36, 37, 38 e 39
- Modificar: `docs/ARQUITETURA.md`
- Modificar: `docs/DECISOES.md`
- Modificar: `ROADMAP.md`
- Teste: `tooling/tests/workspace-structure.test.mjs`

**Interfaces produzidas:** documentação canônica alinhada ao desenho MongoDB/Vercel/Railway; nenhuma regra funcional é removida.

- [ ] **Passo 1: Escrever asserções de governança**

Adicionar ao teste verificações de que a arquitetura menciona MongoDB, Vercel e Railway, que Supabase não aparece como dependência futura e que o database é `gerec_leads`.

- [ ] **Passo 2: Rodar o teste e confirmar a falha**

Executar: `node --test tooling/tests/workspace-structure.test.mjs`

Resultado esperado: falha até a documentação registrar a nova arquitetura.

- [ ] **Passo 3: Atualizar documentação**

Registrar a regra anterior, a nova regra, motivo, impacto nulo nos dados, impacto nas métricas, migração necessária, testes e aprovação de Yago. Atualizar o roadmap para separar fundação MongoDB, backend Python, site Vercel e automações Railway.

- [ ] **Passo 4: Validar documentação**

Executar: `git diff --check` e `node --test tooling/tests/workspace-structure.test.mjs`

- [ ] **Passo 5: Commitar**

```bash
git add SPEC_GERENCIADOR_DE_LEADS_WTG.md docs/ARQUITETURA.md docs/DECISOES.md ROADMAP.md tooling/tests/workspace-structure.test.mjs
git commit -m "docs(gerec-leads): oficializa MongoDB Vercel e Railway"
```

### Tarefa 2: Criar o backend Python e o MongoDB local

**Arquivos:**
- Criar: `apps/api/pyproject.toml`
- Criar: `apps/api/src/gerec_api/main.py`
- Criar: `apps/api/src/gerec_api/config.py`
- Criar: `apps/api/src/gerec_api/infrastructure/mongo/client.py`
- Criar: `apps/api/src/gerec_api/infrastructure/mongo/collections.py`
- Criar: `infra/mongodb/docker-compose.yml`
- Criar: `apps/api/tests/test_health.py`
- Modificar: `README.md`, `.gitignore`

**Interfaces:**
- `Settings.from_env() -> Settings`
- `MongoClientFactory.create(settings) -> MongoDatabase`
- `create_app() -> FastAPI`
- `GET /health` retorna `{ "status": "ok", "database": "gerec_leads" }`

- [ ] **Passo 1: Escrever teste vermelho da API e configuração**

Testar que `create_app()` expõe `/health` e que configuração ausente gera erro sem tentar conexão implícita.

- [ ] **Passo 2: Configurar dependências Python**

Usar `pyproject.toml` com FastAPI, Uvicorn, PyMongo, Pydantic Settings, Argon2 e pytest. Fixar Python `>=3.12,<3.14`.

- [ ] **Passo 3: Configurar replica set local**

O `docker-compose.yml` deve iniciar um MongoDB com `--replSet rs0`, healthcheck `mongosh --eval "db.adminCommand({ ping: 1 })"` e script de inicialização que execute `rs.initiate()` uma única vez.

- [ ] **Passo 4: Implementar cliente server-side**

Ler `MONGODB_URI`, `MONGODB_DATABASE` e `APP_SECRET` exclusivamente no backend. Recusar inicialização quando a URI ou o database não existir.

- [ ] **Passo 5: Rodar teste e healthcheck**

Executar: `cd apps/api; python -m pytest -q`; depois `docker compose -f infra/mongodb/docker-compose.yml up -d` e `curl http://127.0.0.1:8000/health`.

- [ ] **Passo 6: Commitar fundação**

```bash
git add apps/api infra/mongodb README.md .gitignore
git commit -m "feat(gerec-leads): cria API Python e MongoDB local"
```

### Tarefa 3: Criar coleções, validações e índices MongoDB

**Arquivos:**
- Criar: `apps/api/src/gerec_api/infrastructure/mongo/bootstrap.py`
- Criar: `apps/api/src/gerec_api/infrastructure/mongo/indexes.py`
- Criar: `apps/api/tests/integration/test_indexes.py`
- Criar: `scripts/mongodb-bootstrap.ps1`

**Interfaces:**
- `ensure_schema(db) -> None`
- `collection(db, name) -> Collection`
- `MongoCollections` expõe nomes canônicos sem queries espalhadas.

- [ ] **Passo 1: Escrever testes vermelhos de índices**

Verificar índices únicos para `users.emailNormalized`, `source_records.sourceLeadId`, `companies.documentNormalized`, `leads(companyId,campaignId,archivedAt)`, `sales.leadId`, `sessions.tokenHash` e idempotência por comando.

- [ ] **Passo 2: Implementar validações e índices**

Criar índices com `unique=True` e índices parciais para documentos presentes, leads não arquivados e vendas não revertidas. Criar validação de documento via código de domínio antes da persistência.

- [ ] **Passo 3: Implementar bootstrap idempotente**

`ensure_schema` cria/atualiza índices sem apagar coleções nem dados. O script local deve poder ser executado repetidamente.

- [ ] **Passo 4: Rodar testes contra replica set**

Executar: `docker compose -f infra/mongodb/docker-compose.yml up -d`; `cd apps/api; python -m pytest tests/integration/test_indexes.py -q`.

- [ ] **Passo 5: Commitar schema Mongo**

```bash
git add apps/api/src/gerec_api/infrastructure/mongo apps/api/tests/integration scripts/mongodb-bootstrap.ps1
git commit -m "feat(gerec-leads): define coleções e índices MongoDB"
```

### Tarefa 4: Implementar autenticação e sessões no MongoDB

**Arquivos:**
- Criar: `apps/api/src/gerec_api/auth/passwords.py`
- Criar: `apps/api/src/gerec_api/auth/sessions.py`
- Criar: `apps/api/src/gerec_api/auth/dependencies.py`
- Criar: `apps/api/src/gerec_api/routes/auth.py`
- Criar: `apps/api/tests/unit/test_passwords.py`
- Criar: `apps/api/tests/integration/test_auth.py`

**Interfaces:**
- `hash_password(password: str) -> str`
- `verify_password(password: str, digest: str) -> bool`
- `AuthService.login(email: str, password: str) -> SessionResult`
- `AuthService.logout(raw_token: str) -> None`
- `get_current_user(request: Request) -> CurrentUser`

- [ ] **Passo 1: Escrever testes vermelhos**

Cobrir senha nunca armazenada em texto puro, login válido/inválido, cookie `httpOnly`, expiração, logout, revogação e usuário desativado sem acesso.

- [ ] **Passo 2: Implementar hash e sessão opaca**

Usar Argon2id. Gerar token aleatório, persistir somente `sha256(token)`, guardar `userId`, `expiresAt`, `revokedAt` e timestamps.

- [ ] **Passo 3: Implementar rotas**

Criar `POST /auth/login`, `POST /auth/logout` e `GET /auth/me`. A API define cookie seguro e nunca retorna digest, senha ou segredo.

- [ ] **Passo 4: Rodar testes**

Executar: `cd apps/api; python -m pytest tests/unit/test_passwords.py tests/integration/test_auth.py -q`.

- [ ] **Passo 5: Commitar autenticação**

```bash
git add apps/api/src/gerec_api/auth apps/api/src/gerec_api/routes/auth.py apps/api/tests
git commit -m "feat(gerec-leads): adiciona autenticação MongoDB"
```

### Tarefa 5: Implementar módulo profundo de leads e importação idempotente

**Arquivos:**
- Criar: `apps/api/src/gerec_api/domain/leads.py`
- Criar: `apps/api/src/gerec_api/domain/normalization.py`
- Criar: `apps/api/src/gerec_api/infrastructure/mongo/lead_repository.py`
- Criar: `apps/api/src/gerec_api/automation/workbook_adapter.py`
- Criar: `apps/api/src/gerec_api/routes/leads.py`
- Criar: `apps/api/tests/unit/test_normalization.py`
- Criar: `apps/api/tests/integration/test_import.py`

**Interfaces:**
- `normalize_source_row(row: dict) -> NormalizedSourceRow`
- `LeadService.import_row(row: NormalizedSourceRow, idempotency_key: str) -> ImportResult`
- `LeadService.archive_missing(source_snapshot_id: str) -> ArchiveResult`
- `WorkbookAdapter.read(path: Path) -> Iterable[NormalizedSourceRow]`

- [ ] **Passo 1: Escrever testes vermelhos**

Cobrir normalização de documento, telefone, e-mail, estado, datas, headers A–Q, projeção M–P, exclusão de Q, M não interpretada como CNPJ, mesma origem repetida, mesma empresa/campanha e linha removida.

- [ ] **Passo 2: Implementar adapter do workbook**

Ler somente a aba `Leads`, validar headers exatos A–Q e transformar a resposta M em campo informativo. O adapter não cria CNPJ a partir de M.

- [ ] **Passo 3: Implementar importação transacional**

Dentro de `with_transaction`, criar ou atualizar `source_records`, resolver campanha/empresa, criar/atualizar `leads` e gravar resultado idempotente. Pendências de documento/campanha não entram na fila.

- [ ] **Passo 4: Implementar snapshot e arquivamento**

Marcar origem ausente como arquivada; arquivar ocorrência somente quando não houver outra origem ativa. Preservar histórico.

- [ ] **Passo 5: Rodar testes**

Executar: `cd apps/api; python -m pytest tests/unit/test_normalization.py tests/integration/test_import.py -q`.

- [ ] **Passo 6: Commitar leads e adapter**

```bash
git add apps/api/src/gerec_api/domain/leads.py apps/api/src/gerec_api/domain/normalization.py apps/api/src/gerec_api/infrastructure/mongo/lead_repository.py apps/api/src/gerec_api/automation/workbook_adapter.py apps/api/src/gerec_api/routes/leads.py apps/api/tests
git commit -m "feat(gerec-leads): implementa leads e importação MongoDB"
```

### Tarefa 6: Implementar fila transacional, propriedade e créditos

**Arquivos:**
- Criar: `apps/api/src/gerec_api/domain/queue.py`
- Criar: `apps/api/src/gerec_api/infrastructure/mongo/queue_repository.py`
- Criar: `apps/api/src/gerec_api/routes/queue.py`
- Criar: `apps/api/tests/unit/test_queue_rules.py`
- Criar: `apps/api/tests/integration/test_queue_transactions.py`
- Criar: `apps/api/tests/integration/test_queue_concurrency.py`

**Interfaces:**
- `QueueService.distribute_normal(lead_id: ObjectId, command_id: str) -> AssignmentResult`
- `QueueService.assign_recurring(lead_id: ObjectId, command_id: str) -> AssignmentResult`
- `QueueService.assign_temporarily(lead_id: ObjectId, seller_id: ObjectId, reason: str, command_id: str) -> AssignmentResult`
- `QueueService.transfer_owner(company_id: ObjectId, seller_id: ObjectId, reason: str, command_id: str) -> TransferResult`

- [ ] **Passo 1: Escrever testes vermelhos dos critérios AC-01 a AC-11 e AC-29**

Testar rodízio Renato/Sandra/Jessica/Nelma, perda de vez, bloqueio por um atraso, todos bloqueados, FIFO, recorrência, créditos atravessando rotações, proprietário bloqueado, direcionamento temporário, transferência e concorrência.

- [ ] **Passo 2: Implementar transação da fila**

Bloquear `queue_state` com atualização versionada dentro de sessão MongoDB. Em uma transação, avaliar elegibilidade, consumir crédito, criar assignment, atualizar lead, gravar auditoria e outbox.

- [ ] **Passo 3: Implementar propriedade**

O primeiro assignment efetivo define `companies.ownerId`. Recorrência direciona ao proprietário sem mover cursor e cria crédito. Venda temporária preserva proprietário.

- [ ] **Passo 4: Implementar testes concorrentes**

Executar duas transações simultâneas sobre leads diferentes e verificar assignments únicos, cursor equivalente ao sequencial e nenhum saldo negativo.

- [ ] **Passo 5: Commitar fila**

```bash
git add apps/api/src/gerec_api/domain/queue.py apps/api/src/gerec_api/infrastructure/mongo/queue_repository.py apps/api/src/gerec_api/routes/queue.py apps/api/tests
git commit -m "feat(gerec-leads): implementa fila transacional MongoDB"
```

### Tarefa 7: Implementar calendário útil, SLA, feedbacks, tentativas e resultados

**Arquivos:**
- Criar: `apps/api/src/gerec_api/domain/business_time.py`
- Criar: `apps/api/src/gerec_api/domain/operations.py`
- Criar: `apps/api/src/gerec_api/routes/operations.py`
- Criar: `apps/api/tests/unit/test_business_time.py`
- Criar: `apps/api/tests/unit/test_operations.py`
- Criar: `apps/api/tests/integration/test_operations_transactions.py`

**Interfaces:**
- `BusinessClock.add_business_hours(start: datetime, hours: int) -> datetime`
- `OperationsService.register_feedback(command) -> FeedbackResult`
- `OperationsService.register_attempt(command) -> AttemptResult`
- `OperationsService.register_outcome(command) -> OutcomeResult`

- [ ] **Passo 1: Escrever testes vermelhos AC-18 a AC-24, AC-28 e AC-30**

Cobrir 24 horas úteis, lembrete em 4 horas úteis, feriados nacionais/SP, comentário mínimo, uma tentativa por dia útil, cinco dias distintos, desqualificação manual, não conversão, venda única e nota administrativa sem desbloqueio.

- [ ] **Passo 2: Implementar relógio injetável**

Toda regra recebe `Clock.now()` e `HolidayRepository`; nenhum teste usa horário real. Dias não úteis são ignorados integralmente.

- [ ] **Passo 3: Implementar comandos transacionais**

Feedback válido fecha ciclo anterior e abre o próximo. Tentativa valida dia útil distinto, comentário e limite. Resultado final encerra SLA, cria evento e, em `won`, cria uma única venda e marca empresa cliente.

- [ ] **Passo 4: Rodar testes de operação**

Executar: `cd apps/api; python -m pytest tests/unit/test_business_time.py tests/unit/test_operations.py tests/integration/test_operations_transactions.py -q`.

- [ ] **Passo 5: Commitar operações**

```bash
git add apps/api/src/gerec_api/domain/business_time.py apps/api/src/gerec_api/domain/operations.py apps/api/src/gerec_api/routes/operations.py apps/api/tests
git commit -m "feat(gerec-leads): implementa SLA feedbacks e resultados"
```

### Tarefa 8: Completar autorização, leituras e auditoria

**Arquivos:**
- Criar: `apps/api/src/gerec_api/auth/permissions.py`
- Criar: `apps/api/src/gerec_api/routes/dashboard.py`
- Criar: `apps/api/src/gerec_api/routes/admin.py`
- Criar: `apps/api/tests/integration/test_permissions.py`
- Criar: `apps/api/tests/integration/test_audit.py`

**Interfaces:**
- `PermissionService.require_admin(user) -> None`
- `PermissionService.scope_query(user, resource) -> MongoFilter`
- `DashboardService.for_user(user) -> DashboardPayload`

- [ ] **Passo 1: Escrever testes vermelhos de isolamento**

Verificar que vendedor só lê leads próprios, históricos permitidos e saldo próprio; admin lê global; vendedor não executa comandos administrativos; usuário desativado falha mesmo com sessão antiga; chamadas diretas não atravessam escopo.

- [ ] **Passo 2: Implementar filtros server-side**

Toda query recebe `CurrentUser`; repositórios recusam filtro ausente. Não há endpoint que aceite `sellerId` arbitrário para ampliar escopo.

- [ ] **Passo 3: Implementar dashboard e administração**

Expor leituras paginadas para leads, fila, histórico e usuários; ações administrativas chamam comandos de domínio, nunca atualizações diretas de documentos sensíveis.

- [ ] **Passo 4: Validar auditoria**

Cada comando grava ator, ação, entidade, antes/depois, timestamp e correlation ID na mesma transação.

- [ ] **Passo 5: Commitar autorização**

```bash
git add apps/api/src/gerec_api/auth apps/api/src/gerec_api/routes apps/api/tests
git commit -m "feat(gerec-leads): aplica autorização e auditoria no backend"
```

### Tarefa 9: Adaptar o site Next.js para a API Python

**Arquivos:**
- Criar: `apps/web/src/lib/api/client.ts`
- Criar: `apps/web/src/lib/api/types.ts`
- Modificar: `apps/web/src/lib/auth/actions.ts`
- Modificar: `apps/web/src/lib/auth/get-session-context.ts`
- Modificar: `apps/web/src/lib/dashboard/queries.ts`
- Modificar: `apps/web/src/lib/operations/actions.ts`
- Modificar: `apps/web/src/lib/admin/**/*.ts`
- Modificar: páginas e componentes que atualmente assumem Supabase
- Remover após cobertura equivalente: `apps/web/src/lib/supabase/`
- Teste: `apps/web/src/lib/api/client.test.ts`

**Interfaces:**
- `apiFetch<T>(path, init?) -> Promise<T>`
- `getSessionContext() -> AuthenticatedSession`
- Server actions chamam endpoints Python e nunca conhecem MongoDB.

- [ ] **Passo 1: Escrever testes vermelhos do cliente HTTP**

Cobrir propagação de cookies, erro 401 para `/login`, erro 403, payload de validação e ausência de URI MongoDB no bundle.

- [ ] **Passo 2: Substituir login/sessão**

Usar `NEXT_PUBLIC_API_URL` somente para a URL pública da API. O site não recebe segredos e não monta queries MongoDB.

- [ ] **Passo 3: Substituir leituras**

Trocar consultas PostgREST por endpoints paginados Python. Preservar componentes, textos pt-BR, estado demo apenas em ambiente local explicitamente habilitado.

- [ ] **Passo 4: Substituir ações**

Feedback, tentativa, resultado, arquivamento, usuários e simulação chamam comandos Python idempotentes. Remover updates diretos e fallback demo em staging/produção.

- [ ] **Passo 5: Rodar testes web**

Executar: `npm --workspace @wtg/web run test`, `npm --workspace @wtg/web run typecheck`, `npm --workspace @wtg/web run lint`.

- [ ] **Passo 6: Commitar integração Vercel**

```bash
git add apps/web
git commit -m "feat(gerec-leads): conecta site Vercel à API Python"
```

### Tarefa 10: Implementar automações Python na Railway

**Arquivos:**
- Criar: `apps/api/src/gerec_api/automation/sync_job.py`
- Criar: `apps/api/src/gerec_api/automation/outbox_worker.py`
- Criar: `apps/api/src/gerec_api/automation/scheduler.py`
- Criar: `apps/api/tests/integration/test_automation_idempotency.py`
- Criar: `railway.json`
- Modificar: `integrations/n8n/README.md` para documentar remoção do n8n

**Interfaces:**
- `run_sync(source: SourceAdapter, run_id: str) -> SyncResult`
- `process_outbox(batch_size: int) -> int`
- `run_due_jobs(now: datetime) -> JobResult`

- [ ] **Passo 1: Escrever testes vermelhos**

Testar sync a cada 5 minutos, repetição segura, snapshot completo, outbox idempotente, retry de e-mail e não duplicação de alertas.

- [ ] **Passo 2: Implementar worker**

O worker usa os mesmos serviços de domínio da API, executa jobs com lock/idempotência no MongoDB e não duplica atribuições.

- [ ] **Passo 3: Configurar Railway**

Definir um serviço web para a API Python e um worker/cron Python para automações, com variáveis `MONGODB_URI`, `MONGODB_DATABASE`, `APP_SECRET` e credenciais externas somente na Railway.

- [ ] **Passo 4: Rodar testes**

Executar: `cd apps/api; python -m pytest tests/integration/test_automation_idempotency.py -q`.

- [ ] **Passo 5: Commitar automações**

```bash
git add apps/api/src/gerec_api/automation railway.json integrations/n8n/README.md apps/api/tests
git commit -m "feat(gerec-leads): move automações para Python Railway"
```

### Tarefa 11: Configurar deploy Vercel, contratos e E2E

**Arquivos:**
- Criar: `vercel.json`
- Modificar: `playwright.config.ts`
- Modificar: `tests/e2e/*.spec.ts`
- Criar: `tests/e2e/auth.spec.ts`
- Criar: `tests/e2e/roles.spec.ts`
- Criar: `tests/e2e/lead-lifecycle.spec.ts`
- Modificar: `.github/workflows/gerec-leads-ci.yml`
- Criar: `tests/contracts/api-contracts.test.mjs`

**Interfaces produzidas:** contrato HTTP versionado entre Vercel e Railway e suíte E2E dos dois perfis.

- [ ] **Passo 1: Atualizar teste E2E legado**

Substituir o teste que espera o antigo health check por login, dashboard e indicação da API conectada.

- [ ] **Passo 2: Escrever contratos HTTP**

Validar status, payloads, erros e campos mínimos de `/auth`, `/leads`, `/queue`, `/operations` e `/admin`.

- [ ] **Passo 3: Escrever E2E de isolamento e ciclo**

Cobrir admin global, vendedor privado, usuário desativado, novo → contato → qualificado → ganho, cinco tentativas e venda única.

- [ ] **Passo 4: Configurar CI**

O CI deve iniciar MongoDB replica set, API Python, site Next.js, executar testes Python/TypeScript/E2E e derrubar serviços com `if: always()`.

- [ ] **Passo 5: Rodar suíte completa**

Executar: `python -m pytest apps/api/tests -q`; `npm run check`; `npm run test:e2e`.

- [ ] **Passo 6: Commitar deploy e contratos**

```bash
git add vercel.json playwright.config.ts tests .github/workflows/gerec-leads-ci.yml
git commit -m "test(gerec-leads): valida contratos Vercel Railway e E2E"
```

### Tarefa 12: Remover Supabase e fechar documentação operacional

**Arquivos:**
- Remover após cobertura equivalente: `supabase/`, `tooling/supabase/`
- Modificar: `package.json`, `package-lock.json`, `README.md`, `apps/web/.env.example`
- Criar: `apps/api/.env.example`
- Modificar: `docs/evidencias/etapa-2.md` ou criar evidência da migração

**Interfaces produzidas:** comandos locais reproduzíveis para MongoDB, API Python, site e workers.

- [ ] **Passo 1: Confirmar ausência de dependências Supabase**

Executar `rg -n -i "supabase|service_role|postgres|postgrest" --glob '!docs/superpowers/specs/**' --glob '!docs/superpowers/plans/**'` e resolver cada ocorrência de runtime, teste e documentação operacional.

- [ ] **Passo 2: Atualizar comandos**

Substituir scripts Supabase por scripts PowerShell versionados: iniciar replica set, executar bootstrap Mongo, iniciar API, iniciar web e executar worker.

- [ ] **Passo 3: Validar secrets**

Garantir que somente `MONGODB_URI`, `MONGODB_DATABASE` e `APP_SECRET` server-side existam no backend; a Vercel recebe apenas `NEXT_PUBLIC_API_URL`.

- [ ] **Passo 4: Rodar verificação final**

Executar `git diff --check`, testes Python, testes web, contratos, build e E2E. Confirmar `git status --short` limpo após o commit.

- [ ] **Passo 5: Commitar remoção**

```bash
git add -A
git commit -m "refactor(gerec-leads): remove dependência do Supabase"
```

## Gate final

A migração só será considerada concluída quando:

- a API Python funcionar localmente e na Railway;
- o site funcionar pela URL da Vercel;
- MongoDB for o único banco usado em runtime;
- não houver dependência de Supabase no código operacional;
- fila, SLA, recorrência, permissões, venda única e auditoria tiverem testes passando;
- CI, backup, restauração e E2E dos dois perfis estiverem validados;
- nenhuma credencial aparecer no bundle, logs ou repositório;
- as limitações e evidências estiverem registradas na documentação.

## Plano histórico ou executável: `docs/superpowers/plans/2026-08-28-reconstrucao-operacional-interface.md`

# Reconstrução operacional do Gerenciador de Leads — Plano de implementação

> **Para agentes de implementação:** SUB-SKILL OBRIGATÓRIA: usar `subagent-driven-development` para executar este plano tarefa a tarefa. Todas as tarefas usam checklist e exigem revisão independente antes do próximo commit.

**Objetivo:** transformar o sistema implantado em uma operação desktop funcional, na qual o vendedor trata somente seus leads e o administrador administra usuários e consulta a operação sem alterar a tratativa.

**Arquitetura:** regras de calendário, situação comercial, disponibilidade e rodízio permanecem no backend Python, dentro de comandos transacionais MongoDB. A API retorna projeções distintas por papel; o Next.js apenas exibe dados e envia intenções autenticadas. A mudança começa por governança, contrato e testes de domínio, prossegue para persistência/API e só então para interface e E2E visual.

**Tecnologias:** Python 3.12, FastAPI, Pydantic, PyMongo/MongoDB Replica Set, Argon2id, Next.js/React/TypeScript, Vitest, Playwright e Railway/Vercel.

**Fontes de verdade:** `SPEC_GERENCIADOR_DE_LEADS_WTG.md`, `docs/CONTEXTO_MESTRE_GERENCIADOR_DE_LEADS.md`, `docs/superpowers/specs/2026-08-28-reconstrucao-interacoes-sla-design.md`, `AGENTS.md`.

## Restrições globais

- Interface exclusivamente desktop; mínimo suportado 1280 px e validação de referência em 1440 × 900.
- Todo texto novo é em português do Brasil; IDs MongoDB não são rótulos principais na interface.
- Google Sheets permanece somente origem; M–P são a projeção de origem permitida ao vendedor e Q continua excluída.
- MongoDB é a única persistência; toda escrita crítica usa transação em replica set, escrita condicional e idempotency key.
- Nenhum segredo, URI MongoDB, hash ou senha chega ao navegador, às respostas API ou aos logs.
- Vendedor não recebe dados de outros vendedores; administrador pode ler globalmente, mas não cria nem altera tratativas, status ou responsável neste corte.
- SLA: 24 horas úteis em `America/Sao_Paulo`, segunda–sexta, exceto feriado nacional/estadual de SP, dentro de `[09:00,18:00)`; lembrete em quatro horas úteis antes do vencimento.
- Situação primária obrigatória em toda tratativa: `undefined`, `negotiation` ou `won`; `isDisqualified` é marcador adicional, exige comentário e encerra SLA sem reabri-lo automaticamente.
- Comentário útil tem ao menos 6 caracteres; vendedor atual é o único autor possível.
- Vendedor recém-criado ativo entra no final da fila; administrador não entra; pausa manual não transfere leads; reset de senha revoga todas as sessões.
- O estado real da fila é derivado de ordem persistida + cursor + disponibilidade: `Ativo`, `Pausado` ou `Bloqueado por atraso`.
- Não alterar arquivos locais alheios já pendentes: `apps/api/.env.example` removido e `tools/google-sheets-diagnostic/` não rastreado.

## Estrutura de arquivos e responsabilidades

| Área | Arquivos principais | Responsabilidade |
| --- | --- | --- |
| Governança | `SPEC_GERENCIADOR_DE_LEADS_WTG.md`, `docs/DECISOES.md`, desenho e contexto mestre | Registrar a substituição explícita de regras canônicas antes da implementação. |
| Tempo | `apps/api/src/gerec_api/domain/business_time.py` | Calcular apenas tempo útil dentro da janela comercial e com relógio controlável. |
| Tratativa | `apps/api/src/gerec_api/domain/operations.py`, `infrastructure/mongo/operations_repository.py` | Validar, gravar atomicamente e projetar comentários/status/marcador/SLA. |
| Usuários e sessão | `auth/sessions.py`, novo módulo de administração e `routes/admin.py` | Criar usuários, pausar/ativar vendedores, redefinir senha e revogar sessões. |
| Fila | `domain/queue.py`, `infrastructure/mongo/queue_repository.py` | Derivar disponibilidade, inserir vendedores e expor cursor/ordem dinâmica. |
| Leitura | `auth/permissions.py`, `routes/dashboard.py`, `routes/leads.py` | Contratos seguros e enriquecidos para administrador e vendedor. |
| Interface | `apps/web/src/app/**`, `components/**`, `lib/api/**` | Controles reais, páginas por papel, modais e apresentação desktop. |
| Verificação | `apps/api/tests/**`, `apps/web/src/**/*.test.ts`, `tests/contracts/**`, `tests/e2e/**` | Testes unitários, integração, contratos, E2E e screenshots determinísticas. |

---

### Task 1 — Registrar a governança da reconstrução

**Arquivos:**
- Modificar: `SPEC_GERENCIADOR_DE_LEADS_WTG.md` (seção 39; criar `GOV-004`).
- Modificar: `docs/DECISOES.md` (criar `DEC-028`).
- Modificar: `docs/superpowers/specs/2026-08-28-reconstrucao-interacoes-sla-design.md`.
- Modificar: `scripts/generate-master-context.ps1` somente se novos documentos não forem incluídos automaticamente.
- Gerar: `docs/CONTEXTO_MESTRE_GERENCIADOR_DE_LEADS.md`.

**Consome:** decisões aprovadas no desenho de 28/08.

**Produz:** governança canônica para todas as tarefas seguintes.

- [ ] **Passo 1: Escrever a verificação documental que deve falhar.**

Criar em `tests/contracts/spec-governance.test.mjs` verificações textuais para `GOV-004` e `DEC-028`, exigindo as expressões `09:00`, `18:00`, `Bloqueado por atraso`, `isDisqualified`, `senha não vazia`, `comentário` e `Yago, André, Renato, Sandra, Jessica e Nelma`.

- [ ] **Passo 2: Executar a verificação vermelha.**

Executar: `node --test tests/contracts/spec-governance.test.mjs`

Esperado: falha porque `GOV-004` e `DEC-028` ainda não existem.

- [ ] **Passo 3: Registrar a alteração aprovada.**

Inserir `GOV-004 — Operação comercial, SLA e permissões` com a regra anterior, regra nova, motivo, impactos em dados/métricas, migração e aceite. Registrar também que as contas iniciais configuradas neste ambiente são Yago e André administradores; Renato, Sandra, Jessica e Nelma vendedores. Em `DEC-028`, repetir a decisão sem contradizer GOV-004. Marcar o desenho como aprovado para implementação e regenerar o contexto mestre.

- [ ] **Passo 4: Executar a verificação verde.**

Executar: `node --test tests/contracts/spec-governance.test.mjs; powershell -ExecutionPolicy Bypass -File scripts/generate-master-context.ps1`

Esperado: teste verde e contexto mestre contendo `GOV-004` e `DEC-028`.

- [ ] **Passo 5: Revisar e versionar.**

Executar: `git diff --check` e `git diff -- SPEC_GERENCIADOR_DE_LEADS_WTG.md docs/DECISOES.md docs/superpowers/specs/2026-08-28-reconstrucao-interacoes-sla-design.md docs/CONTEXTO_MESTRE_GERENCIADOR_DE_LEADS.md`.

Commit: `docs(gerec-leads): formaliza reconstrução operacional`

### Task 2 — Corrigir o calendário de horas úteis por TDD

**Arquivos:**
- Modificar: `apps/api/src/gerec_api/domain/business_time.py`.
- Modificar: `apps/api/tests/unit/test_business_time.py`.

**Consome:** GOV-004.

**Produz:** `add_business_hours(start_at, hours, calendar)` e `subtract_business_hours(deadline_at, hours, calendar)` corretos dentro de `[09:00,18:00)`.

- [ ] **Passo 1: Escrever testes de borda controlados.**

Adicionar casos explícitos: sexta 17:00 + 24h = quarta útil seguinte 14:00; 08:30 inicia às 09:00; 18:00 inicia às 09:00 do próximo dia útil; 17:59 preserva um minuto; travessia de sábado/domingo; feriado estadual de SP; lembrete calculado com subtração de quatro horas úteis.

- [ ] **Passo 2: Executar a suíte vermelha.**

Executar: `python -m pytest apps/api/tests/unit/test_business_time.py -q`

Esperado: falhas que revelem o limite atual em meia-noite.

- [ ] **Passo 3: Implementar o cálculo mínimo.**

Normalizar a entrada para o próximo instante elegível, consumir somente o intervalo até 18:00 e pular para 09:00 do próximo dia elegível quando necessário. Reutilizar o mesmo predicado de dia útil em soma e subtração; manter timezone aware e sem acessar relógio real.

- [ ] **Passo 4: Executar a suíte verde.**

Executar: `python -m pytest apps/api/tests/unit/test_business_time.py -q`

Esperado: todos os casos de janela, fim de semana e feriado verdes.

- [ ] **Passo 5: Versionar.**

Commit: `fix(gerec-leads): calcula SLA na janela comercial`

### Task 3 — Versionar schema e migração idempotente de reconstrução

**Arquivos:**
- Criar: `apps/api/src/gerec_api/infrastructure/mongo/migrations/20260828_operacao_comercial.py`.
- Criar: `apps/api/src/gerec_api/infrastructure/mongo/migrations/runner.py`.
- Modificar: `apps/api/src/gerec_api/infrastructure/mongo/bootstrap.py`.
- Modificar: `apps/api/src/gerec_api/infrastructure/mongo/collections.py`.
- Modificar: `apps/api/src/gerec_api/infrastructure/mongo/indexes.py`.
- Criar: `apps/api/tests/integration/test_operational_migration.py`.

**Consome:** calendário da Tarefa 2 e documentos existentes de leads, assignments, feedbacks, queue state e usuários.

**Produz:** coleção `lead_treatments`; campos de projeção em `leads`; índices de fila, tratativa e idempotência; registro de migração aplicado.

- [ ] **Passo 1: Escrever testes de migração.**

Criar fixture com lead legado, assignment, feedback legado, sessão e posição de fila. Exigir que a primeira execução materialize `commercialStatus`, `isDisqualified`, `commentCount`, `lastCommentAt`, `feedbackDueAt`, `feedbackReminderAt`; que a segunda execução não altere resultado; que não apague eventos ou sessões; e que índices únicos sejam criados.

- [ ] **Passo 2: Executar o teste vermelho.**

Executar: `python -m pytest apps/api/tests/integration/test_operational_migration.py -q`

Esperado: falha por ausência de runner/migração.

- [ ] **Passo 3: Implementar migração idempotente.**

Adicionar `schema_migrations` com identificador único. Converter outcomes antigos para `commercialStatus`, preservar `isDisqualified` quando outcome legado for desqualificado, contar somente eventos de comentário válidos, recalcular ciclos abertos pela Tarefa 2 e criar índices: `lead_treatments(leadId, createdAt)`, chave única `lead_treatments(leadId, idempotencyKey)`, `seller_queue(sellerId)` e posição única parcial/validada conforme capacidade do Mongo.

- [ ] **Passo 4: Executar integração verde.**

Executar: `python -m pytest apps/api/tests/integration/test_operational_migration.py apps/api/tests/integration/test_indexes.py -q`

Esperado: migração repetível sem perda de histórico.

- [ ] **Passo 5: Versionar.**

Commit: `feat(gerec-leads): versiona schema operacional`

### Task 4 — Implementar o comando transacional de tratativa

**Arquivos:**
- Modificar: `apps/api/src/gerec_api/domain/operations.py`.
- Modificar: `apps/api/src/gerec_api/infrastructure/mongo/operations_repository.py`.
- Criar: `apps/api/tests/unit/test_treatment_rules.py`.
- Modificar: `apps/api/tests/integration/test_operations_transactions.py`.

**Interface produzida:**

```python
TreatmentCommand(
    lead_id: ObjectId,
    comment: str,
    commercial_status: Literal["undefined", "negotiation", "won"],
    is_disqualified: bool,
    idempotency_key: str,
)
OperationsService.with_actor(...).register_treatment(command) -> TreatmentResult
```

- [ ] **Passo 1: Escrever testes vermelhos de regra e transação.**

Cobrir: cinco caracteres falham; situação ausente falha; desqualificado sem comentário falha; vendedor não responsável recebe negação; admin recebe negação; comentário válido atualiza campos e cria evento; `won + isDisqualified=True` é aceito; reenvio com mesma chave não duplica contador; falha intermediária faz rollback de evento, lead, auditoria e ciclo.

- [ ] **Passo 2: Executar os testes vermelhos.**

Executar: `python -m pytest apps/api/tests/unit/test_treatment_rules.py apps/api/tests/integration/test_operations_transactions.py -q`

Esperado: falhas porque o comando e a projeção ainda não existem.

- [ ] **Passo 3: Implementar o comando mínimo.**

Validar texto útil com `strip()`, validar situação fechada, conferir dono atual e papel seller. Na transação: gravar `lead_treatments` imutável, atualizar projeção do lead e auditoria. Para marcador desqualificado, definir `feedbackDueAt`/`feedbackReminderAt` como `null` e fechar ciclo; nos demais casos abrir/renovar SLA pela Tarefa 2. Nunca permitir endpoint administrativo para esse comando.

- [ ] **Passo 4: Executar testes verdes.**

Executar: `python -m pytest apps/api/tests/unit/test_treatment_rules.py apps/api/tests/integration/test_operations_transactions.py -q`

Esperado: invariantes, idempotência e rollback verdes.

- [ ] **Passo 5: Versionar.**

Commit: `feat(gerec-leads): registra tratativa comercial imutável`

### Task 5 — Implementar disponibilidade e rotação real da fila

**Arquivos:**
- Modificar: `apps/api/src/gerec_api/domain/queue.py`.
- Modificar: `apps/api/src/gerec_api/infrastructure/mongo/queue_repository.py`.
- Modificar: `apps/api/tests/unit/test_queue_rules.py`.
- Modificar: `apps/api/tests/integration/test_queue_transactions.py`.
- Modificar: `apps/api/tests/integration/test_queue_concurrency.py`.

**Interface produzida:**

```python
SellerAvailability(status: Literal["active", "paused", "blocked_overdue"], reason: str | None)
QueueSnapshot(cursor_seller_id: ObjectId | None, entries: list[QueueEntry])
```

- [ ] **Passo 1: Escrever testes vermelhos de disponibilidade.**

Cobrir: lead vencido bloqueia vendedor, desqualificado não bloqueia, regularização de todos remove apenas bloqueio automático, pausa continua após regularização, pausa preserva leads, cursor avança sobre indisponíveis e a lista apresentada começa no próximo elegível. Cobrir concorrência para que duas distribuições preservem uma única ordem/cursor.

- [ ] **Passo 2: Executar testes vermelhos.**

Executar: `python -m pytest apps/api/tests/unit/test_queue_rules.py apps/api/tests/integration/test_queue_transactions.py apps/api/tests/integration/test_queue_concurrency.py -q`

Esperado: falhas nas projeções de motivo/cursor e no efeito do novo SLA.

- [ ] **Passo 3: Implementar cálculo único de disponibilidade.**

Criar uma única função que prioriza `paused` sobre `blocked_overdue`, deriva atraso de ciclos abertos e retorna `active` caso contrário. Ordenar leitura por `position` circular a partir de `queue_state.nextSellerId`, sem usar ordem de `createdAt`; após atribuição persistir cursor do próximo participante elegível e nunca restaurar turnos perdidos.

- [ ] **Passo 4: Executar testes verdes.**

Executar: `python -m pytest apps/api/tests/unit/test_queue_rules.py apps/api/tests/integration/test_queue_transactions.py apps/api/tests/integration/test_queue_concurrency.py -q`

Esperado: rodízio dinâmico, pausa e bloqueio demonstrados em transação.

- [ ] **Passo 5: Versionar.**

Commit: `feat(gerec-leads): deriva fila pela disponibilidade real`

### Task 6 — Implementar comandos administrativos de usuários e sessões

**Arquivos:**
- Criar: `apps/api/src/gerec_api/domain/user_administration.py`.
- Criar: `apps/api/src/gerec_api/infrastructure/mongo/user_repository.py`.
- Modificar: `apps/api/src/gerec_api/auth/sessions.py`.
- Modificar: `apps/api/src/gerec_api/routes/admin.py`.
- Modificar: `apps/api/tests/integration/test_auth.py`.
- Criar: `apps/api/tests/integration/test_user_administration.py`.

**Interface produzida:**

```text
POST /api/admin/users {fullName, email, role, password}
PATCH /api/admin/users/{id}/availability {paused}
PATCH /api/admin/users/{id}/password {password}
```

- [ ] **Passo 1: Escrever testes vermelhos.**

Cobrir admin cria usuário com senha não vazia, e-mail único, resposta sem hash/senha, novo seller ativo entra na última posição, novo admin não entra na fila, pausa/ativação não transfere leads, vendedor recebe 403, reset invalida dois tokens existentes e senha antiga deixa de autenticar.

- [ ] **Passo 2: Executar testes vermelhos.**

Executar: `python -m pytest apps/api/tests/integration/test_user_administration.py apps/api/tests/integration/test_auth.py -q`

Esperado: falhas por ausência dos comandos e revogação em massa.

- [ ] **Passo 3: Implementar serviços e rotas finas.**

Usar Argon2id já existente. Rejeitar somente senha vazia após `strip()`; não aplicar mínimo/composição. Dentro da transação de criação, inserir usuário e, se seller ativo, calcular `max(position)+1` com proteção contra concorrência. No reset, trocar hash e revogar todas as sessões por `userId`; retornar somente metadados públicos. Registrar auditoria sem senha.

- [ ] **Passo 4: Executar testes verdes.**

Executar: `python -m pytest apps/api/tests/integration/test_user_administration.py apps/api/tests/integration/test_auth.py -q`

Esperado: CRUD restrito ao admin e sessões antigas inválidas.

- [ ] **Passo 5: Versionar.**

Commit: `feat(gerec-leads): administra usuários e sessões`

### Task 7 — Separar contratos de leitura por papel

**Arquivos:**
- Modificar: `apps/api/src/gerec_api/auth/permissions.py`.
- Modificar: `apps/api/src/gerec_api/routes/dashboard.py`.
- Modificar: `apps/api/src/gerec_api/routes/leads.py`.
- Modificar: `apps/api/src/gerec_api/routes/queue.py`.
- Criar: `apps/api/tests/integration/test_operational_read_models.py`.

**Interface produzida:**

```text
GET /api/dashboard
GET /api/leads/{id}/treatments?page=&limit=
GET /api/queue
```

Admin recebe leads globais, fila completa e histórico de tratativas somente leitura. Seller recebe somente seus leads, suas tratativas e sua própria posição/estado, sem `nextSellerName`, lista ou contagem de colegas.

- [ ] **Passo 1: Escrever testes vermelhos.**

Exigir campos legíveis no lead: `contactName`, `sellerName`, `companyName`, `campaignName`, `phoneDisplay`, `email`, `commercialStatus`, `isDisqualified`, `commentCount`, `feedbackDueAt`. Exigir fallback `Não informado`; admin lê tratamentos; seller A não lê lead/tratamento/fila de B e não recebe `nextSellerName`.

- [ ] **Passo 2: Executar testes vermelhos.**

Executar: `python -m pytest apps/api/tests/integration/test_permissions.py apps/api/tests/integration/test_operational_read_models.py -q`

Esperado: falhas por campos ausentes e vazamento de fila global.

- [ ] **Passo 3: Implementar projeções.**

Separar explicitamente `for_admin` e `for_seller`; resolver nomes server-side, normalizar telefone removendo prefixo nacional `55`, formatar apenas no web, retirar IDs públicos não necessários e expor motivo de indisponibilidade/cursor somente ao admin. Ordenar histórico de tratativas por data decrescente e paginar no servidor.

- [ ] **Passo 4: Executar testes verdes.**

Executar: `python -m pytest apps/api/tests/integration/test_permissions.py apps/api/tests/integration/test_operational_read_models.py -q`

Esperado: escopo de vendedor e leitura administrativa seguros.

- [ ] **Passo 5: Versionar.**

Commit: `feat(gerec-leads): separa leituras administrativas e vendedor`

### Task 8 — Expor a tratativa pela API e retirar comandos conflitantes

**Arquivos:**
- Modificar: `apps/api/src/gerec_api/routes/operations.py`.
- Modificar: `apps/api/src/gerec_api/main.py` se for necessário registrar novas dependências.
- Modificar: `tests/contracts/api-contract-server.py`.
- Modificar: `tests/contracts/api-contracts.test.mjs`.

**Interface produzida:**

```text
POST /api/leads/{leadId}/treatments
{ comment, commercialStatus, isDisqualified, idempotencyKey }
```

- [ ] **Passo 1: Escrever contrato vermelho.**

Adicionar exemplos 201/422/403/409: sucesso, comentário curto, status inválido, admin proibido, seller sem propriedade proibido e reenvio idempotente. Declarar que `/api/admin/leads/{id}/notes` não faz parte do contrato operacional novo.

- [ ] **Passo 2: Executar contrato vermelho.**

Executar: `node --test tests/contracts/api-contracts.test.mjs`

Esperado: falha até a rota e os exemplos existirem.

- [ ] **Passo 3: Implementar boundary fino.**

Criar `TreatmentRequest` Pydantic com `min_length=6`, enum fechado e chave idempotente. Chamar somente `OperationsService.register_treatment`; mapear validação para 422, autorização para 403 e conflito para 409. Remover rota de nota administrativa e não reutilizar endpoint de tentativas para comentário.

- [ ] **Passo 4: Executar contrato e API verde.**

Executar: `node --test tests/contracts/api-contracts.test.mjs; python -m pytest apps/api/tests/integration/test_operations_transactions.py apps/api/tests/integration/test_permissions.py -q`

Esperado: contrato HTTP e políticas verdes.

- [ ] **Passo 5: Versionar.**

Commit: `feat(gerec-leads): expõe tratativa segura na API`

### Task 9 — Tipos web, cliente HTTP e formatação de apresentação

**Arquivos:**
- Modificar: `apps/web/src/lib/api/types.ts`.
- Modificar: `apps/web/src/lib/api/client.ts`.
- Modificar: `apps/web/src/lib/dashboard/queries.ts`.
- Modificar: `apps/web/src/lib/dashboard/format.ts`.
- Modificar: testes correspondentes em `apps/web/src/lib/**/*.test.ts`.

**Produz:** tipos separados `AdminDashboard`, `SellerDashboard`, `OperationalLead`, `Treatment`, `QueueEntry`, `ManagedUser`; chamadas HTTP para usuários, disponibilidade, senha, tratativa e histórico.

- [ ] **Passo 1: Escrever testes vermelhos.**

Cobrir mapeamento de `commercialStatus`, marcador, contador, prazo, `Não informado`, telefone `5511988308029 → (11) 98830-8029`, data em `America/Sao_Paulo` e serialização das requisições de tratativa/usuário sem senha em retorno.

- [ ] **Passo 2: Executar testes vermelhos.**

Executar: `npm run test --workspace=@wtg/web -- --run`

Esperado: tipos/clientes ausentes ou incompatíveis com o contrato novo.

- [ ] **Passo 3: Implementar o cliente tipado.**

Centralizar `apiFetch`, tratar 401/403/409/422 como erros de interface legíveis e manter os identificadores técnicos somente como chave interna. Não duplicar regra de SLA, cursor, elegibilidade ou status no navegador.

- [ ] **Passo 4: Executar testes verdes e TypeScript.**

Executar: `npm run test --workspace=@wtg/web -- --run; npm run typecheck --workspace=@wtg/web`

Esperado: testes e verificação de tipos verdes.

- [ ] **Passo 5: Versionar.**

Commit: `feat(gerec-leads): tipa contratos operacionais do cliente`

### Task 10 — Reconstruir navegação e dashboard por perfil

**Arquivos:**
- Modificar: `apps/web/src/components/app-shell.tsx`.
- Modificar: `apps/web/src/app/dashboard/page.tsx`.
- Criar: `apps/web/src/components/admin-dashboard.tsx`.
- Criar: `apps/web/src/components/seller-dashboard.tsx`.
- Modificar: `apps/web/src/app/globals.css`.
- Criar: testes em `apps/web/src/components/*.test.tsx`.

- [ ] **Passo 1: Escrever testes de renderização vermelhos.**

Exigir admin com cartões de total, atribuições, posições, próximo vendedor e fila completa; seller com total próprio, comentários, SLA e apenas sua posição. Exigir que seller não tenha links de Fila global, Histórico global ou Usuários, nem nomes de colegas.

- [ ] **Passo 2: Executar testes vermelhos.**

Executar: `npm run test --workspace=@wtg/web -- --run src/components`

Esperado: componentes específicos ainda inexistentes.

- [ ] **Passo 3: Implementar composição por papel.**

Montar o shell a partir do `role` retornado pela API; manter quatro páginas admin e visão própria do seller. Exibir situação e marcador sempre como texto/badge acessível. Remover `admin-controls.tsx` e qualquer referência a “Simular entrada de leads”.

- [ ] **Passo 4: Executar testes verdes.**

Executar: `npm run test --workspace=@wtg/web -- --run src/components; npm run lint --workspace=@wtg/web`

Esperado: navegação e dashboard sem elementos indevidos por perfil.

- [ ] **Passo 5: Versionar.**

Commit: `feat(gerec-leads): separa dashboards por perfil`

### Task 11 — Construir tabela de leads e modal de tratativa do vendedor

**Arquivos:**
- Criar: `apps/web/src/components/lead-table.tsx`.
- Criar: `apps/web/src/components/lead-treatment-modal.tsx`.
- Criar: `apps/web/src/lib/operations/treatment-actions.ts`.
- Modificar: `apps/web/src/app/dashboard/page.tsx`.
- Remover: `apps/web/src/components/comment-modal.tsx` depois da migração completa.
- Criar: `apps/web/src/components/lead-treatment-modal.test.tsx`.

- [ ] **Passo 1: Escrever testes vermelhos de interação.**

Cobrir coluna de responsável somente para admin, campos nome/empresa/campanha/telefone/e-mail/situação/marcador/prazo/comentários, botão `Registrar tratativa` somente para seller responsável, modal com três opções primárias, checkbox desqualificado e histórico somente leitura. Validar bloqueio de envio abaixo de 6 caracteres, exibição de erro 422 e incremento de contador após sucesso.

- [ ] **Passo 2: Executar testes vermelhos.**

Executar: `npm run test --workspace=@wtg/web -- --run src/components/lead-treatment-modal.test.tsx`

Esperado: falha porque o componente não existe.

- [ ] **Passo 3: Implementar tratamento real.**

Enviar `POST /api/leads/{id}/treatments`, mostrar progresso/sucesso/erro, invalidar a consulta do dashboard e renderizar histórico recebido da API. Administrador visualiza a mesma linha e histórico, sem botão ou campo editável. O comentário que marca desqualificação deve ser a submissão atual, nunca uma inferência da UI.

- [ ] **Passo 4: Executar testes verdes.**

Executar: `npm run test --workspace=@wtg/web -- --run src/components/lead-treatment-modal.test.tsx; npm run typecheck --workspace=@wtg/web`

Esperado: interação do vendedor e leitura administrativa verdes.

- [ ] **Passo 5: Versionar.**

Commit: `feat(gerec-leads): permite tratativa de lead pelo vendedor`

### Task 12 — Construir gestão funcional de usuários

**Arquivos:**
- Modificar: `apps/web/src/app/usuarios/page.tsx`.
- Modificar: `apps/web/src/components/user-management.tsx`.
- Criar: `apps/web/src/components/user-form-modal.tsx`.
- Criar: `apps/web/src/components/user-password-modal.tsx`.
- Criar: `apps/web/src/lib/users/actions.ts`.
- Criar: `apps/web/src/components/user-management.test.tsx`.

- [ ] **Passo 1: Escrever testes vermelhos de controles reais.**

Cobrir botão `Novo usuário`, modal com nome/e-mail/papel/senha, senha obrigatória não vazia, criação bem-sucedida, `Pausar`/`Ativar` com confirmação, `Redefinir senha` com confirmação, estado de carregamento, feedback de sucesso/erro e ausência da senha após salvar.

- [ ] **Passo 2: Executar testes vermelhos.**

Executar: `npm run test --workspace=@wtg/web -- --run src/components/user-management.test.tsx`

Esperado: falha porque os controles atuais são apenas texto/botões desabilitados.

- [ ] **Passo 3: Implementar ações.**

Chamar as três rotas administrativas da Tarefa 6; usar botões HTML reais, modal com foco inicial, escape/cancelamento, confirmação antes da mutação e atualização da lista. Exibir status `Ativo`/`Pausado`; nunca mostrar `Bloqueado por atraso` como controle manual nem permitir pausar administrador caso a API não suporte esse fluxo.

- [ ] **Passo 4: Executar testes verdes.**

Executar: `npm run test --workspace=@wtg/web -- --run src/components/user-management.test.tsx; npm run lint --workspace=@wtg/web`

Esperado: todos os controles disparam ações tipadas e acessíveis.

- [ ] **Passo 5: Versionar.**

Commit: `feat(gerec-leads): torna gestão de usuários operacional`

### Task 13 — Reconstruir fila, histórico e paginação administrativa

**Arquivos:**
- Modificar: `apps/web/src/app/fila/page.tsx`.
- Modificar: `apps/web/src/app/historico/page.tsx`.
- Modificar: `apps/web/src/components/pagination.tsx`.
- Criar: `apps/web/src/components/queue-table.tsx`.
- Criar: `apps/web/src/components/treatment-history-table.tsx`.
- Remover: `apps/web/src/components/resource-table.tsx` quando não houver consumidores.
- Criar: testes para tabelas e paginação.

- [ ] **Passo 1: Escrever testes vermelhos.**

Exigir fila admin ordenada a partir do cursor real, vendedor/nome, posição atual, disponibilidade e motivo; histórico com lead, vendedor, texto, situação, marcador e data; paginação com `<button>` anterior/próxima, `disabled` quando necessário e `aria-label` correspondente.

- [ ] **Passo 2: Executar testes vermelhos.**

Executar: `npm run test --workspace=@wtg/web -- --run src/components/queue-table.test.tsx src/components/treatment-history-table.test.tsx src/components/pagination.test.tsx`

Esperado: componentes e semântica novos ausentes.

- [ ] **Passo 3: Implementar visualização verdadeira.**

Usar somente projeções da Tarefa 7. A fila do admin exibe o cursor e a primeira pessoa elegível; indisponibilidades possuem badge e texto. O histórico não é a lista de assignments: deve ser `lead_treatments`. A paginação mantém query string, evita navegação quando desabilitada e não exibe rótulos colados como `AnteriorPágina`.

- [ ] **Passo 4: Executar testes verdes.**

Executar: `npm run test --workspace=@wtg/web -- --run src/components/queue-table.test.tsx src/components/treatment-history-table.test.tsx src/components/pagination.test.tsx`

Esperado: três telas administrativas com dados operacionais compreensíveis.

- [ ] **Passo 5: Versionar.**

Commit: `feat(gerec-leads): exibe fila e histórico operacionais`

### Task 14 — Consolidar CSS desktop, estados e acessibilidade

**Arquivos:**
- Modificar: `apps/web/src/app/globals.css`.
- Modificar: componentes criados nas Tarefas 10–13, somente para classes/atributos de acessibilidade.
- Criar: `apps/web/src/app/globals.test.ts` se a configuração permitir testar tokens; caso contrário validar exclusivamente por Playwright na Tarefa 15.

- [ ] **Passo 1: Definir os estados visuais verificáveis.**

Criar tokens para: indefinido vermelho, negociação amarelo, ganho verde, desqualificado cinza; todos com texto e contraste legível. Definir grid desktop, tabela com cabeçalho fixo de leitura, cards de fila, modal, estados de carregamento/erro/vazio e botão desabilitado.

- [ ] **Passo 2: Implementar sem inventar dados.**

Remover colunas técnicas como conteúdo principal, exibir `Não informado` para empresa/campanha ausentes, usar a formatação de telefone da Tarefa 9 e manter largura mínima de 1280 px. Não inserir gradientes, elementos decorativos sem função ou controles falsos.

- [ ] **Passo 3: Verificar qualidade estática.**

Executar: `npm run lint --workspace=@wtg/web; npm run typecheck --workspace=@wtg/web; npm run build --workspace=@wtg/web`

Esperado: lint, tipos e build verdes.

- [ ] **Passo 4: Versionar.**

Commit: `style(gerec-leads): consolida interface operacional desktop`

### Task 15 — Cobrir fluxos reais com E2E e validação visual

**Arquivos:**
- Modificar: `tests/e2e/auth.spec.ts`.
- Modificar: `tests/e2e/roles.spec.ts`.
- Modificar: `tests/e2e/lead-lifecycle.spec.ts`.
- Criar: `tests/e2e/admin-operations.spec.ts`.
- Criar: `tests/e2e/seller-treatment.spec.ts`.
- Criar: `tests/e2e/visual/` com snapshots aprovados.
- Modificar: `playwright.config.ts` somente se necessário para estabilidade de dados/servidores.

- [ ] **Passo 1: Preparar fixtures determinísticas.**

Usar relógio controlável e dados sintéticos: seis contas, seis leads distribuídos Renato 2/Sandra 2/Jessica 1/Nelma 1, cursor seguinte Jessica, ao menos um prazo vencido e um lead desqualificado. Não usar credenciais de produção nem Google Sheets real.

- [ ] **Passo 2: Escrever E2E vermelhos pela interface.**

Cobrir admin cria seller e vê-o no fim da fila, pausa/ativa seller e redefine senha; admin lê mas não encontra botão de editar tratativa; seller abre modal, comentário curto falha, negociação salva, contador sobe e status aparece; desqualificação com comentário encerra SLA; seller não vê colegas; anterior/próxima são botões corretos; fila mostra Jessica como próxima após a distribuição descrita.

- [ ] **Passo 3: Executar E2E vermelho.**

Executar: `npx playwright test tests/e2e/admin-operations.spec.ts tests/e2e/seller-treatment.spec.ts --project=chromium`

Esperado: falhas até a aplicação completa estar conectada à API fixture.

- [ ] **Passo 4: Criar capturas de referência.**

Adicionar `expect(page).toHaveScreenshot(...)` a 1440 × 900 para dashboard admin, usuários/modal, fila/histórico, dashboard seller e modal de tratativa. Mascarar relógio variável; não mascarar status, nomes, contadores, botões ou dados visíveis.

- [ ] **Passo 5: Executar E2E verde.**

Executar: `npx playwright test --project=chromium`

Esperado: todos os fluxos e screenshots verdes, sem chamadas diretas à API para a ação que a interface deve realizar.

- [ ] **Passo 6: Versionar.**

Commit: `test(gerec-leads): valida operação administrativa e vendedor`

### Task 16 — Executar o gate final e registrar evidências

**Arquivos:**
- Criar: `docs/evidencias/2026-08-28-reconstrucao-operacional.md`.
- Modificar: `ROADMAP.md` apenas para registrar o estado real das entregas concluídas.
- Gerar: `docs/CONTEXTO_MESTRE_GERENCIADOR_DE_LEADS.md`.

- [ ] **Passo 1: Executar todas as verificações.**

Executar, nesta ordem:

```powershell
python -m pytest apps/api/tests -q
npm run test --workspace=@wtg/web -- --run
npm run lint --workspace=@wtg/web
npm run typecheck --workspace=@wtg/web
npm run build --workspace=@wtg/web
node --test tests/contracts/*.test.mjs
npx playwright test --project=chromium
powershell -ExecutionPolicy Bypass -File scripts/generate-master-context.ps1
git diff --check
```

- [ ] **Passo 2: Registrar evidências factuais.**

Informar versões/comandos, contagem de testes, resultado de cada gate, capturas produzidas, limitações conhecidas e confirmação de que não foram incluídos `.env` ou arquivos locais alheios.

- [ ] **Passo 3: Revisão independente.**

Enviar o diff completo para um subagente revisor. Resolver qualquer achado crítico e repetir os comandos afetados.

- [ ] **Passo 4: Versionar.**

Commit: `docs(gerec-leads): registra evidências da reconstrução`

## Revisão do plano

### Cobertura do desenho aprovado

| Decisão/critério | Tarefas |
| --- | --- |
| Governança e divergências do SPEC | 1 |
| SLA 09–18 e lembrete | 2, 3, 4, 5 |
| Tratativa/status/marcador/comentários | 3, 4, 7, 8, 11, 15 |
| Bloqueio automático e pausa manual | 3, 5, 6, 7, 13, 15 |
| Usuários, senha e sessões | 6, 12, 15 |
| Cursor e ordem dinâmica | 5, 7, 10, 13, 15 |
| Projeções e permissões admin/vendedor | 7, 8, 10, 11, 15 |
| Interface sem controles falsos | 10–14 |
| Paginação real | 13, 15 |
| E2E, visual, build e evidência | 15, 16 |

### Resultado da auto-revisão

- Não há passo que dependa de regra não aprovada: os pontos que contradizem o SPEC são formalizados na Tarefa 1 antes da implementação.
- Todas as alterações de domínio começam por teste vermelho e terminam em teste verde.
- A UI não inicia antes de contratos e projeções de API estáveis.
- O fornecedor de e-mail, planilha definitiva, recorrência/transferência/créditos e suporte mobile permanecem explicitamente fora deste corte.

## Plano histórico ou executável: `docs/superpowers/plans/2026-09-03-alertas-email-leads.md`

# Alertas de novos leads por e-mail — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar alertas SMTP seguros e idempotentes para novos leads agrupados por vendedor/sincronização, avisos individuais de transferência e horários corretos em `America/Sao_Paulo`.

**Architecture:** A atribuição continua transacional no MongoDB. Eventos leves entram na `notification_outbox`; um agregador forma um grupo por `syncRunId + sellerId`, enquanto transferências usam evento individual. O worker Railway resolve os dados mínimos, renderiza texto/HTML e entrega por SMTP STARTTLS com retry/dead-letter.

**Tech Stack:** Python 3, FastAPI, MongoDB/PyMongo, `smtplib`/MIME da biblioteca padrão, Railway worker, Next.js/React, Vitest, Pytest, Playwright.

**Spec:** `docs/superpowers/specs/2026-09-03-alertas-email-leads-design.md`

## Global Constraints

- Ler integralmente `AGENTS.md`, `SPEC_GERENCIADOR_DE_LEADS_WTG.md` e `docs/CONTEXTO_MESTRE_GERENCIADOR_DE_LEADS.md` antes de cada tarefa.
- MongoDB é a única persistência; não adicionar Supabase/PostgreSQL/n8n.
- Regras críticas permanecem em serviços/comandos Python, nunca em React, controller ou worker de integração.
- Google Sheets é somente origem; nunca escrever na planilha.
- SMTP: `smtp.oncorretor.com.br:587`, STARTTLS obrigatório, remetente `contato@wtgseguros.com.br`.
- `SMTP_PASSWORD` e demais segredos só existem nas variáveis da Railway.
- Nenhum e-mail de lead inclui campanha, e-mail do lead ou identificadores internos.
- Datas sem fuso da origem são `America/Sao_Paulo`; armazenamento é UTC; apresentação é São Paulo.
- Uma falha de e-mail nunca desfaz atribuição, transferência ou fila; o fluxo não possui SLA, prazo, lembrete ou bloqueio automático operacional.
- Aplicar TDD: teste vermelho observado antes de cada implementação.
- Não alterar `D apps/api/.env.example` nem `?? tools/google-sheets-diagnostic/`.
- Não fazer push/deploy sem autorização explícita para a etapa; commits devem ser pequenos e auditáveis.

## Mapa de arquivos e responsabilidades

- `apps/api/src/gerec_api/domain/normalization.py`: interpretação de datas da origem.
- `apps/api/src/gerec_api/automation/sync_job.py`: ciclo de sincronização e `syncRunId`.
- `apps/api/src/gerec_api/infrastructure/mongo/queue_repository.py`: eventos transacionais de atribuição/transferência.
- `apps/api/src/gerec_api/infrastructure/mongo/collections.py` e `indexes.py`: nomes e índices da outbox.
- `apps/api/src/gerec_api/automation/outbox_worker.py`: claim, agrupamento e entrega.
- `apps/api/src/gerec_api/automation/email_templates.py`: MIME/texto/HTML sem regra de negócio.
- `apps/api/src/gerec_api/automation/smtp_delivery.py`: adapter SMTP isolado e testável.
- `apps/api/src/gerec_api/config.py`: configuração validada sem segredos no cliente.
- `apps/api/src/gerec_api/routes/admin.py`: endpoint administrativo de leitura da outbox.
- `apps/api/src/gerec_api/auth/permissions.py`: leitura administrativa segura de estado da outbox.
- `apps/api/tests/unit/` e `apps/api/tests/integration/`: testes de domínio, Mongo e concorrência.
- `apps/web/src/lib/dashboard/format.ts`: apresentação de timestamps em São Paulo.
- `apps/web/src/components/admin-notification-status.tsx`: estados visuais de alertas administrativos.
- `docs/DECISOES.md`, `SPEC_GERENCIADOR_DE_LEADS_WTG.md`, `docs/ARQUITETURA.md`: governança e contratos.
- `docs/CONTEXTO_MESTRE_GERENCIADOR_DE_LEADS.md`: contexto regenerado após mudanças documentais.

---

### Task 1: Registrar governança e contrato operacional

**Files:**
- Modify: `SPEC_GERENCIADOR_DE_LEADS_WTG.md` seção 39 e dependências de implantação.
- Modify: `docs/DECISOES.md` adicionando decisão após DEC-029.
- Modify: `docs/ARQUITETURA.md` fronteira do outbox worker.
- Regenerate: `docs/CONTEXTO_MESTRE_GERENCIADOR_DE_LEADS.md` via `scripts/generate-master-context.ps1`.
- Test: inspeção documental com `rg`.

**Interfaces:** produz os nomes de eventos, variáveis e política temporal consumidos pelas tarefas seguintes.

- [ ] **Step 1: Escrever primeiro a verificação documental**

```powershell
rg -n "assignment_email_requested|owner_transfer_email_requested|SMTP_HOST|America/Sao_Paulo|agrup" SPEC_GERENCIADOR_DE_LEADS_WTG.md docs/DECISOES.md docs/ARQUITETURA.md
```

Esperado: falha porque os contratos novos ainda não estão registrados.

- [ ] **Step 2: Registrar regra anterior, nova regra, motivo, impacto, migração, testes e aprovação de Yago** nas três documentações canônicas.
- [ ] **Step 3: Regenerar o contexto mestre** com `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/generate-master-context.ps1`.
- [ ] **Step 4: Reexecutar o `rg` e confirmar todos os contratos.**
- [ ] **Step 5: Commit** `docs: registra alertas smtp e contrato de horario`.

### Task 2: Remover SLA e bloqueio automático da operação

**Objetivo:** alinhar API, fila, métricas e telas aos únicos estados de disponibilidade `Ativo` e `Pausado`, ambos manuais, preservando campos legados somente para auditoria.

**Arquivos principais:** `apps/api/src/gerec_api/infrastructure/mongo/queue_repository.py`, `apps/api/src/gerec_api/auth/permissions.py`, projeções/dashboard em `apps/web/src/`, testes de domínio/API/E2E e migração versionada quando necessária.

- [ ] Escrever testes vermelhos para rejeitar `blocked`, ignorar atraso na elegibilidade e ocultar prazo/SLA da projeção operacional.
- [ ] Implementar a remoção mínima de bloqueio derivado, due/reminder e consequências automáticas, sem alterar cursor FIFO nem histórico.
- [ ] Implementar/validar pausa e ativação manuais do administrador.
- [ ] Executar testes unitários, integração e interface; registrar evidências no ledger.
- [ ] Commit `feat: remove sla operacional e bloqueio automatico`.

### Task 3: Corrigir e congelar o contrato de horário

**Files:**
- Modify: `apps/api/src/gerec_api/domain/normalization.py` apenas se a regressão localizar parser incorreto.
- Modify: `apps/web/src/lib/dashboard/format.ts` apenas se a regressão localizar formato incorreto.
- Test: `apps/api/tests/unit/test_normalization.py` e novo teste de formato web.

**Interfaces:** `normalize_datetime(value) -> datetime | None` interpreta valor ingênuo em São Paulo e retorna UTC; `formatDateTime(value) -> string` exibe São Paulo.

- [ ] **Step 1: Adicionar testes vermelhos** para `14:11` ingênuo, `17:11Z`, offset externo e timestamp inválido.
- [ ] **Step 2: Executar** `python -m pytest apps/api/tests/unit/test_normalization.py -q` e `npm test -- --run src/lib/dashboard/format.test.ts`; confirmar falha da expectativa nova.
- [ ] **Step 3: Implementar somente a normalização/formatação mínima**, sem deslocar timestamps já aware.
- [ ] **Step 4: Executar os testes direcionados e depois a suíte completa de API/Web.**
- [ ] **Step 5: Auditar registros reais/legados por consulta somente leitura; nenhuma migração corretiva sem classificação explícita.**
- [ ] **Step 6: Commit** `fix: normaliza timestamps da origem em sao paulo`.

### Task 3: Propagar `syncRunId` até a atribuição

**Files:**
- Modify: `apps/api/src/gerec_api/automation/sync_job.py`.
- Modify: `apps/api/src/gerec_api/domain/queue.py` assinaturas do comando.
- Modify: `apps/api/src/gerec_api/infrastructure/mongo/queue_repository.py` payload do evento de atribuição.
- Test: `apps/api/tests/unit/test_sync_job.py` e `apps/api/tests/integration/test_queue_transactions.py`.

**Interfaces:** `QueueService.distribute_ready(lead_id, command_id, *, actor_id, sync_run_id: str | None = None) -> AssignmentResult`; eventos carregam `syncRunId` quando atribuídos pelo `SyncJob`.

- [ ] **Step 1: Criar teste vermelho** que execute uma sincronização e inspecione o evento criado para conter o mesmo `syncRunId`.
- [ ] **Step 2: Rodar o teste direcionado e confirmar falha por ausência do campo.**
- [ ] **Step 3: Propagar o argumento sem mudar cursor, critérios de elegibilidade ou créditos.**
- [ ] **Step 4: Rodar testes de sincronização, fila e concorrência.**
- [ ] **Step 5: Commit** `feat: vincula atribuicoes ao ciclo de sincronizacao`.

### Task 4: Criar eventos de notificação de atribuição e transferência

**Files:**
- Modify: `apps/api/src/gerec_api/infrastructure/mongo/queue_repository.py`.
- Modify: `apps/api/src/gerec_api/infrastructure/mongo/indexes.py` se uma chave auxiliar exigir índice.
- Test: `apps/api/tests/integration/test_queue_transactions.py`.

**Interfaces:** `lead.assignment_email_requested` usa `groupKey=assignment-summary:{syncRunId}:{sellerId}`; `lead.owner_transfer_email_requested` usa `owner-transfer:{leadId}:{commandId}`.

- [ ] **Step 1: Escrever testes vermelhos** para resumo automático e transferência individual, verificando destinatário lógico, lead ID e ausência de dados pessoais redundantes.
- [ ] **Step 2: Executar os testes e confirmar falha.**
- [ ] **Step 3: Gravar eventos na mesma transação da atribuição/transferência; não criar evento de SLA, prazo ou bloqueio automático.**
- [ ] **Step 4: Verificar replay idempotente e cursor inalterado.**
- [ ] **Step 5: Commit** `feat: grava eventos de alerta de atribuicao`.

### Task 5: Implementar agregação por vendedor e sincronização

**Files:**
- Modify: `apps/api/src/gerec_api/automation/outbox_worker.py` ou criar `apps/api/src/gerec_api/automation/notification_groups.py`.
- Test: `apps/api/tests/unit/test_notification_groups.py` e `apps/api/tests/integration/test_automation_idempotency.py`.

**Interfaces:** `NotificationGroupRepository.claim_group(group_key, now, max_attempts) -> NotificationGroup`; `NotificationGroupRepository.mark_group_sent(group, now) -> bool`; grupos de transferência nunca agregam com sincronização.

- [ ] **Step 1: Criar testes vermelhos** para dois leads do mesmo vendedor, dois vendedores da mesma sincronização, grupo vazio e dois workers concorrentes.
- [ ] **Step 2: Confirmar falhas com `pytest`.**
- [ ] **Step 3: Implementar claim atômico por `groupKey`, lock e fencing token reaproveitando a outbox.**
- [ ] **Step 4: Marcar todos os eventos do grupo somente após entrega bem-sucedida.**
- [ ] **Step 5: Testar crash antes/depois do envio e documentar limite de duplicidade externa.**
- [ ] **Step 6: Commit** `feat: agrupa alertas por sincronizacao e vendedor`.

### Task 6: Criar templates de e-mail HTML e texto

**Files:**
- Create: `apps/api/src/gerec_api/automation/email_templates.py`.
- Test: `apps/api/tests/unit/test_email_templates.py`.

**Interfaces:** `render_assignment_summary(items, dashboard_url) -> EmailMessageData`; `render_owner_transfer(item, dashboard_url) -> EmailMessageData`.

- [ ] **Step 1: Escrever testes vermelhos** para assunto, texto aprovado, nome, telefone, link e ausência de campanha/e-mail/IDs.
- [ ] **Step 2: Rodar `pytest apps/api/tests/unit/test_email_templates.py -q` e confirmar falha.**
- [ ] **Step 3: Implementar MIME multipart com versão texto simples e HTML escapado.**
- [ ] **Step 4: Testar nomes/telefones com caracteres especiais e lista vazia.**
- [ ] **Step 5: Commit** `feat: adiciona templates de alerta por email`.

### Task 7: Implementar adapter SMTP STARTTLS

**Files:**
- Create: `apps/api/src/gerec_api/automation/smtp_delivery.py`.
- Modify: `apps/api/src/gerec_api/config.py` para configuração validada.
- Test: `apps/api/tests/unit/test_smtp_delivery.py`.

**Interfaces:** `SmtpSettings.from_env() -> SmtpSettings`; `SmtpDelivery(settings, smtp_factory=smtplib.SMTP).send(message, idempotency_key) -> None`.

- [ ] **Step 1: Escrever testes vermelhos** para host/porta, STARTTLS, login, remetente, timeout e falhas convertidas em erro retryable.
- [ ] **Step 2: Confirmar falha dos testes.**
- [ ] **Step 3: Implementar com `smtplib.SMTP`, `starttls()`, `login()` e fechamento garantido.**
- [ ] **Step 4: Garantir que senha nunca apareça em exceção/log.**
- [ ] **Step 5: Rodar testes unitários e lint Python.**
- [ ] **Step 6: Commit** `feat: entrega alertas via smtp starttls`.

### Task 8: Integrar worker, dados mínimos e retry

**Files:**
- Modify: `apps/api/src/gerec_api/automation/outbox_worker.py`.
- Modify: `apps/api/src/gerec_api/infrastructure/mongo/indexes.py` para consultas por IDs/grupos.
- Test: `apps/api/tests/integration/test_automation_idempotency.py` e novo teste de integração de entrega.

**Interfaces:** `EmailNotificationWorker.process(batch_size, now=None) -> int`; resolução de vendedor/lead retorna somente e-mail do vendedor, nome e telefone do lead.

- [ ] **Step 1: Escrever testes vermelhos** de envio agrupado, transferência individual, retry, dead-letter e vendedor sem e-mail.
- [ ] **Step 2: Confirmar falhas.**
- [ ] **Step 3: Integrar agregador, templates e SMTP no worker Railway sem remover o webhook até a substituição estar coberta.**
- [ ] **Step 4: Executar entrega somente depois do claim; `mark_sent` só após sucesso.**
- [ ] **Step 5: Verificar que falha não altera leads, assignments ou queue_state, e que nenhum SLA/prazo é criado.**
- [ ] **Step 6: Commit** `feat: integra worker de alertas de leads`.

### Task 9: Configurar Railway e documentação operacional

**Files:**
- Modify: `docs/ARQUITETURA.md` seção de configuração e operação Railway, sem valores secretos.
- Test: validação de configuração unitária e inspeção de arquivos.

**Interfaces:** variáveis `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM`, `DASHBOARD_PUBLIC_URL`, `SMTP_ENABLED`.

- [ ] **Step 1: Escrever teste vermelho** que rejeite configuração SMTP incompleta quando `SMTP_ENABLED=true`.
- [ ] **Step 2: Implementar validação; permitir `SMTP_ENABLED=false` em desenvolvimento sem enviar mensagens.**
- [ ] **Step 3: Documentar configuração Railway e procedimento de rotação da senha.**
- [ ] **Step 4: Confirmar que nenhum segredo está no repositório com `rg`.**
- [ ] **Step 5: Commit** `chore: documenta configuracao smtp da railway`.

### Task 10: Expor observabilidade administrativa sem dados sensíveis

**Files:**
- Modify: `apps/api/src/gerec_api/auth/permissions.py`.
- Modify: `apps/api/src/gerec_api/routes/admin.py`.
- Create: `apps/web/src/components/admin-notification-status.tsx`.
- Modify: `apps/web/src/components/admin-dashboard.tsx` para incluir o painel de status.
- Test: API/Web de leitura administrativa.

**Interfaces:** leitura admin-only de contagens/status: pending, processing, retry, sent, dead_letter, último erro truncado e última sincronização; nenhuma ação de edição de tratativa.

- [ ] **Step 1: Escrever testes vermelhos** para admin autorizado, vendedor negado e ausência de senha/payload pessoal.
- [ ] **Step 2: Implementar projeção agregada server-side com paginação/limites.**
- [ ] **Step 3: Renderizar estados claros de pendente, retry e dead-letter.**
- [ ] **Step 4: Rodar API/Web tests e verificar acessibilidade básica.**
- [ ] **Step 5: Commit** `feat: adiciona observabilidade dos alertas`.

### Task 11: E2E e screenshots do fluxo completo

**Files:**
- Modify/Create: `tests/e2e/email-alerts.spec.ts` e fixtures de teste.
- Create: evidências em diretório de artefatos do teste, sem dados reais.

**Interfaces:** sincronização mock → atribuição → resumo; transferência → aviso individual; relógio controlado; SMTP fake.

- [ ] **Step 1: Escrever cenários E2E vermelhos** para resumo agrupado, transferência, falha/retry e horário 14:11.
- [ ] **Step 2: Executar Playwright em viewport 1440×900 e confirmar falhas antes da implementação final.**
- [ ] **Step 3: Implementar fixtures/fakes isolados sem SMTP real.**
- [ ] **Step 4: Capturar screenshots de dashboard admin, dashboard vendedor, outbox e lead com horário correto.**
- [ ] **Step 5: Commit** `test: cobre alertas de leads no fluxo e2e`.

### Task 12: Verificação final, piloto e handoff

**Files:**
- Create/Modify: `.superpowers/sdd/2026-09-03-alertas-email-leads/progress.md`, sem apagar histórico.
- Review: diff completo, SPEC, design e plano.

- [ ] **Step 1: Rodar API completa:** `python -m pytest apps/api/tests -q`.
- [ ] **Step 2: Rodar Web completa:** `npm test` em `apps/web`.
- [ ] **Step 3: Rodar `npm run typecheck`, `npm run lint` e `npm run build`.**
- [ ] **Step 4: Rodar E2E/screenshot e revisar manualmente as evidências.**
- [ ] **Step 5: Verificar `git diff --check`, arquivos protegidos e ausência de segredos.**
- [ ] **Step 6: Atualizar contexto mestre após todas as mudanças documentais.**
- [ ] **Step 7: Solicitar revisão independente; corrigir achados; só então preparar rollout/piloto com `SMTP_ENABLED=false` inicialmente e habilitação autorizada.**
- [ ] **Step 8: Commit final de documentação/evidências; não declarar concluído sem saídas recentes dos comandos.**

## Critério de conclusão

O trabalho só está concluído quando os critérios de aceite da especificação de design forem demonstrados por testes recentes, revisão independente, screenshots em 1440×900, configuração SMTP validada em staging e evidência de que atribuições/fila permanecem corretas quando o provedor de e-mail falha.

## Matriz de cobertura do design

| Design | Tarefas do plano |
|---|---|
| Arquitetura e fluxo de sincronização | 3, 4, 5, 8 |
| Transferência individual | 4, 5, 8, 11 |
| Contrato de eventos e idempotência | 3, 4, 5, 8 |
| Templates HTML/texto | 6 |
| SMTP STARTTLS e configuração | 7, 9 |
| Retry, dead-letter e observabilidade | 5, 8, 10, 12 |
| Timezone e registros legados | 1, 2, 12 |
| Segurança, permissões e dados mínimos | 1, 6, 8, 10, 11 |
| E2E, screenshots, rollout e rollback | 9, 11, 12 |

## Plano histórico ou executável: `docs/superpowers/plans/2026-09-14-notificacoes-internas-tratativas-relatorios.md`

# NotificaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Âµes internas, tratativas e relatÃƒÆ’Ã‚Â³rios Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar notificaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o interna de novos leads, situaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o Potencial, marcador Desqualificado reversÃƒÆ’Ã‚Â­vel, destaque de leads sem tratativa, filtros/ordenaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o e relatÃƒÆ’Ã‚Â³rios administrativos seguros.

**Architecture:** A API Python mantÃƒÆ’Ã‚Â©m regras, autorizaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o e projeÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Âµes de leitura. Um cursor persistente no usuÃƒÆ’Ã‚Â¡rio delimita a janela de novos leads sem alterar FIFO; o frontend Next.js apenas consome contratos autorizados. RelatÃƒÆ’Ã‚Â³rios sÃƒÆ’Ã‚Â£o agregaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Âµes MongoDB exclusivas de administrador e usam a atribuiÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o do proprietÃƒÆ’Ã‚Â¡rio atual.

**Tech Stack:** Python 3.13, FastAPI, Pydantic, PyMongo/MongoDB replica set, pytest; Next.js 16, React 19, TypeScript, Vitest, Testing Library e agent-browser.

**Spec:** docs/superpowers/specs/2026-09-14-notificacoes-internas-tratativas-relatorios-design.md

## Global Constraints

- Trabalhar no worktree feat/migracao-mongodb-vercel-railway; nÃƒÆ’Ã‚Â£o modificar apps/api/.env.example removido ou tools/google-sheets-diagnostic/ nÃƒÆ’Ã‚Â£o rastreado.
- NÃƒÆ’Ã‚Â£o criar e-mail, SMTP, n8n, WhatsApp ou outro efeito externo.
- NÃƒÆ’Ã‚Â£o alterar FIFO, cursor de distribuiÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o, posiÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o, crÃƒÆ’Ã‚Â©ditos, propriedade, pausa manual ou permissÃƒÆ’Ã‚Âµes de transferÃƒÆ’Ã‚Âªncia.
- Cada alteraÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o MongoDB usa nova migraÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o versionada; nÃƒÆ’Ã‚Â£o editar migraÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Âµes aplicadas.
- Vendedor nÃƒÆ’Ã‚Â£o informa sellerId para leitura ou confirmaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o de notificaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o; identidade vem da sessÃƒÆ’Ã‚Â£o.
- Interface desktop com evidÃƒÆ’Ã‚Âªncia visual 1440ÃƒÆ’Ã¢â‚¬â€900, sem controles decorativos.
- ComeÃƒÆ’Ã‚Â§ar cada comportamento com teste vermelho, implementar o mÃƒÆ’Ã‚Â­nimo, executar teste verde e solicitar revisÃƒÆ’Ã‚Â£o independente.
- ApÃƒÆ’Ã‚Â³s alterar documentaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o, executar powershell -NoProfile -ExecutionPolicy Bypass -File scripts/generate-master-context.ps1.

## PrÃƒÆ’Ã‚Â©requisito de governanÃƒÆ’Ã‚Â§a concluÃƒÆ’Ã‚Â­do

O commit 6c8dd82 jÃƒÆ’Ã‚Â¡ registra GOV-007, DEC-031, o desenho aprovado e o contexto mestre. As tarefas seguintes implementam somente essa regra: sem e-mail, Potencial como situaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o primÃƒÆ’Ã‚Â¡ria, marcador atual reversÃƒÆ’Ã‚Â­vel, notificaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o interna, filtros e relatÃƒÆ’Ã‚Â³rios administrativos.

## Interfaces produzidas

    CommercialStatus = Literal["undefined", "potential", "negotiation", "won"]

    GET  /api/lead-notifications/new
    POST /api/lead-notifications/new/acknowledge
    GET  /api/admin/reports/lead-distribution?from=ISO-8601&to=ISO-8601

A leitura de notificaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o retorna itens mÃƒÆ’Ã‚Â­nimos e watermark. A confirmaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o atualiza newLeadsSeenAt usando mÃƒÆ’Ã‚Â¡ximo atÃƒÆ’Ã‚Â´mico. O relatÃƒÆ’Ã‚Â³rio retorna period, bySituation e bySeller; nÃƒÆ’Ã‚Â£o retorna telefone, e-mail nem histÃƒÆ’Ã‚Â³rico.

---

### Task 1: SituaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o Potencial e marcador atual reversÃƒÆ’Ã‚Â­vel

**Files:**
- Modify: apps/api/src/gerec_api/domain/operations.py
- Modify: apps/api/src/gerec_api/routes/operations.py
- Modify: apps/api/src/gerec_api/infrastructure/mongo/bootstrap.py
- Modify: apps/api/src/gerec_api/infrastructure/mongo/operations_repository.py
- Modify: apps/api/tests/unit/test_treatment_rules.py
- Modify: apps/api/tests/integration/test_operations_transactions.py

**Consumes:** contratos existentes de TreatmentCommand e TreatmentResult.

**Produces:** CommercialStatus inclui potential; leads.isDisqualified ÃƒÆ’Ã‚Â© exatamente o valor da tratativa mais recente, enquanto lead_treatments permanece imutÃƒÆ’Ã‚Â¡vel.

- [ ] **Step 1: Write the failing tests**

    def test_treatment_accepts_potential_status() -> None:
        result = _service().register_treatment(
            TreatmentCommand("lead-1", "Cliente demonstrou interesse", "potential", False, "potential")
        )
        assert result.commercial_status == "potential"

    def test_later_treatment_removes_current_marker_and_preserves_history() -> None:
        _service(database, seller_id).register_treatment(
            TreatmentCommand(lead_id, "Contato sem aderÃƒÆ’Ã‚Âªncia ÃƒÆ’Ã‚Â  campanha", "undefined", True, "first")
        )
        result = _service(database, seller_id).register_treatment(
            TreatmentCommand(lead_id, "Passou cotaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o e seguirÃƒÆ’Ã‚Â¡ negociaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o", "negotiation", False, "second")
        )
        assert result.is_disqualified is False
        assert database["leads"].find_one({"_id": lead_id})["isDisqualified"] is False
        assert [x["isDisqualified"] for x in database["lead_treatments"].documents] == [True, False]

- [ ] **Step 2: Run red**

Run: python -m pytest apps/api/tests/unit/test_treatment_rules.py apps/api/tests/integration/test_operations_transactions.py -q

Expected: potential is invalid and the old sticky-marker behavior conflicts with the regression.

- [ ] **Step 3: Implement the minimum**

    COMMERCIAL_STATUSES = frozenset({"undefined", "potential", "negotiation", "won"})
    CommercialStatus = Literal["undefined", "potential", "negotiation", "won"]

    update = {
        "commercialStatus": command.commercial_status,
        "isDisqualified": command.is_disqualified,
        "commentCount": comment_count,
        "lastCommentAt": now,
        "updatedAt": now,
    }

Expand the Pydantic literal and Mongo validator enum. Remove only the prior assertion that requires a later false value to remain true.

- [ ] **Step 4: Run green**

Run: python -m pytest apps/api/tests/unit/test_treatment_rules.py apps/api/tests/integration/test_operations_transactions.py -q

Expected: all selected tests pass.

- [ ] **Step 5: Commit**

    git add apps/api/src/gerec_api/domain/operations.py apps/api/src/gerec_api/routes/operations.py apps/api/src/gerec_api/infrastructure/mongo/bootstrap.py apps/api/src/gerec_api/infrastructure/mongo/operations_repository.py apps/api/tests/unit/test_treatment_rules.py apps/api/tests/integration/test_operations_transactions.py
    git commit -m "feat(api): adiciona potencial e marcador reversÃƒÆ’Ã‚Â­vel"

### Task 2: Cursor persistente e API de notificaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o interna

**Files:**
- Create: apps/api/src/gerec_api/domain/lead_notifications.py
- Create: apps/api/src/gerec_api/infrastructure/mongo/lead_notification_repository.py
- Create: apps/api/src/gerec_api/routes/lead_notifications.py
- Create: apps/api/src/gerec_api/infrastructure/mongo/migrations/20260914_initialize_new_lead_notification_cursor.py
- Modify: apps/api/src/gerec_api/infrastructure/mongo/migrations/runner.py
- Modify: apps/api/src/gerec_api/infrastructure/mongo/bootstrap.py
- Modify: apps/api/src/gerec_api/infrastructure/mongo/indexes.py
- Modify: apps/api/src/gerec_api/main.py
- Test: apps/api/tests/integration/test_lead_notifications.py
- Test: apps/api/tests/unit/test_migration_runner.py

**Consumes:** CurrentUser, users, leads and assignedAt from existing assignment/transfer transactions.

**Produces:** NewLeadNotification, NewLeadNotificationSnapshot, LeadNotificationService and the two protected routes.

- [ ] **Step 1: Write the failing tests**

    def test_cursor_migration_initializes_only_missing_sellers_once() -> None:
        apply(database, session=None, now=lambda: NOW)
        apply(database, session=None, now=lambda: NOW + timedelta(days=1))
        assert missing_cursor_seller["newLeadsSeenAt"] == NOW
        assert existing_cursor_seller["newLeadsSeenAt"] == EXISTING

    def test_seller_sees_only_current_leads_after_cursor_and_acknowledges() -> None:
        snapshot = service.for_seller(seller)
        assert [item.lead_id for item in snapshot.items] == [str(new_lead)]
        assert service.acknowledge(seller, snapshot.watermark) == snapshot.watermark

    def test_transfer_is_visible_to_new_owner_and_later_assignment_survives_ack() -> None:
        snapshot = service.for_seller(new_owner)
        assign_lead(new_owner, at=snapshot.watermark + timedelta(seconds=1))
        service.acknowledge(new_owner, snapshot.watermark)
        assert [item.lead_id for item in service.for_seller(new_owner).items] == [str(later_lead)]

    def test_notification_routes_deny_admin_and_other_seller() -> None:
        assert admin_client.get("/api/lead-notifications/new").status_code == 403

- [ ] **Step 2: Run red**

Run: python -m pytest apps/api/tests/integration/test_lead_notifications.py apps/api/tests/unit/test_migration_runner.py -q

Expected: modules and routes are unavailable.

- [ ] **Step 3: Implement the boundary**

    @dataclass(frozen=True)
    class NewLeadNotificationSnapshot:
        items: tuple[NewLeadNotification, ...]
        watermark: datetime

    class LeadNotificationService:
        def for_seller(self, user: CurrentUser) -> NewLeadNotificationSnapshot: ...
        def acknowledge(self, user: CurrentUser, watermark: datetime) -> datetime: ...

Repository query: current assigneeId equals authenticated seller, assignedAt is greater than newLeadsSeenAt and no later than watermark, sorted assignedAt then _id. Acknowledge uses Mongo $max. Reject invalid or future watermark. Migration initializes only absent seller cursors using injectable now; register it after 20260904 migration. Add optional date|null validator field and index (assigneeId, assignedAt) named leads_assignee_assigned_at. Wire service/router in main.py. It must not write queue, assignments, outbox or FIFO state.

- [ ] **Step 4: Run green**

Run: python -m pytest apps/api/tests/integration/test_lead_notifications.py apps/api/tests/unit/test_migration_runner.py apps/api/tests/integration/test_indexes.py -q

Expected: selected tests pass, including descending concurrent acknowledgements.

- [ ] **Step 5: Commit**

    git add apps/api/src/gerec_api/domain/lead_notifications.py apps/api/src/gerec_api/infrastructure/mongo/lead_notification_repository.py apps/api/src/gerec_api/routes/lead_notifications.py apps/api/src/gerec_api/infrastructure/mongo/migrations/20260914_initialize_new_lead_notification_cursor.py apps/api/src/gerec_api/infrastructure/mongo/migrations/runner.py apps/api/src/gerec_api/infrastructure/mongo/bootstrap.py apps/api/src/gerec_api/infrastructure/mongo/indexes.py apps/api/src/gerec_api/main.py apps/api/tests/integration/test_lead_notifications.py apps/api/tests/unit/test_migration_runner.py apps/api/tests/integration/test_indexes.py
    git commit -m "feat(api): adiciona notificaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Âµes internas de leads"

### Task 3: Filtro, ordenaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o e relatÃƒÆ’Ã‚Â³rio administrativo no backend

**Files:**
- Create: apps/api/src/gerec_api/routes/reports.py
- Modify: apps/api/src/gerec_api/auth/permissions.py
- Modify: apps/api/src/gerec_api/routes/dashboard.py
- Modify: apps/api/src/gerec_api/main.py
- Test: apps/api/tests/integration/test_operational_read_models.py
- Test: apps/api/tests/integration/test_reports.py

**Consumes:** Task 1 commercial status; current assigneeId and assignedAt on leads.

**Produces:** DashboardService.for_user accepts assignee_id and sort; lead_distribution is admin-only.

- [ ] **Step 1: Write the failing tests**

    def test_admin_filters_by_current_assignee_and_sorts_by_status() -> None:
        response = service.for_user(admin, assignee_id=str(sandra), sort="situation")
        assert [x["sellerName"] for x in response["leads"]["items"]] == ["Sandra", "Sandra"]
        assert [x["commercialStatus"] for x in response["leads"]["items"]] == ["negotiation", "potential"]

    def test_seller_cannot_override_scope_with_assignee_id() -> None:
        response = service.for_user(seller, assignee_id=str(other_seller), sort="situation")
        assert {x["sellerName"] for x in response["leads"]["items"]} == {"Sandra"}

    def test_report_uses_current_owner_and_transfer_assignment_date() -> None:
        report = service.lead_distribution(admin, from_at=TRANSFER_AT, to_at=TRANSFER_AT + timedelta(days=1))
        assert report["bySeller"] == [{"sellerId": str(new_owner), "sellerName": "Jessica", "count": 1}]

    def test_report_route_denies_seller() -> None:
        assert seller_client.get("/api/admin/reports/lead-distribution").status_code == 403

- [ ] **Step 2: Run red**

Run: python -m pytest apps/api/tests/integration/test_operational_read_models.py apps/api/tests/integration/test_reports.py -q

Expected: dashboard arguments, report method and route do not exist.

- [ ] **Step 3: Implement server-side reads**

Add optional assigneeId and sort query parameters to routes/dashboard.py. In DashboardService, only administrator can compose a valid seller assignee filter; seller always receives PermissionService.scope_query(current, "leads"). sort=situation orders commercialStatus ascending, then createdAt descending and _id ascending; other sort values are rejected with 422.

Implement routes/reports.py and DashboardService.lead_distribution. Validate admin and from < to. Query assignedAt in [from, to), group current commercialStatus and assigneeId, enrich names in one users query, and serialize UTC bounds. Response includes only period, bySituation and bySeller.

- [ ] **Step 4: Run green**

Run: python -m pytest apps/api/tests/integration/test_operational_read_models.py apps/api/tests/integration/test_reports.py apps/api/tests/integration/test_permissions.py -q

Expected: selected tests pass; seller sees neither other seller leads nor report data.

- [ ] **Step 5: Commit**

    git add apps/api/src/gerec_api/routes/reports.py apps/api/src/gerec_api/auth/permissions.py apps/api/src/gerec_api/routes/dashboard.py apps/api/src/gerec_api/main.py apps/api/tests/integration/test_operational_read_models.py apps/api/tests/integration/test_reports.py apps/api/tests/integration/test_permissions.py
    git commit -m "feat(api): filtra leads e agrega relatÃƒÆ’Ã‚Â³rios"

### Task 4: Contratos web, Potencial, destaque e controles de lista

**Files:**
- Create: apps/web/src/components/lead-list-controls.tsx
- Modify: apps/web/src/lib/api/types.ts
- Modify: apps/web/src/lib/api/client.ts
- Modify: apps/web/src/lib/dashboard/queries.ts
- Modify: apps/web/src/lib/dashboard/format.ts
- Modify: apps/web/src/components/lead-table.tsx
- Modify: apps/web/src/components/lead-treatment-modal.tsx
- Modify: apps/web/src/app/dashboard/page.tsx
- Modify: apps/web/src/app/fila/page.tsx
- Modify: apps/web/src/app/globals.css
- Test: apps/web/src/components/lead-table.test.tsx
- Test: apps/web/src/components/lead-treatment-modal.dom.test.tsx
- Test: apps/web/src/lib/dashboard/queries.test.ts

**Consumes:** Task 3 dashboard query parameters.

**Produces:** potential UI label, row class lead-row--awaiting-treatment and LeadListControls.

- [ ] **Step 1: Write failing tests**

    it("shows Potencial in the treatment selector", () => {
      render(<LeadTreatmentModal lead={{ ...lead, commercialStatus: "potential" }} mode="write" />);
      expect(screen.getByRole("option", { name: "Potencial" })).toBeInTheDocument();
    });

    it("highlights only leads without treatment", () => {
      render(<LeadTable role="seller" leads={[{ ...lead, commentCount: 0 }, { ...lead, id: "treated", contactName: "Tratado", commentCount: 1 }]} />);
      expect(screen.getByText(lead.contactName).closest("tr")).toHaveClass("lead-row--awaiting-treatment");
      expect(screen.getByText("Tratado").closest("tr")).not.toHaveClass("lead-row--awaiting-treatment");
    });

    it("renders the assignee filter only for admin", () => {
      render(<LeadListControls role="admin" sellers={[seller]} current={{ assigneeId: null, sort: "situation" }} />);
      expect(screen.getByLabelText("ResponsÃƒÆ’Ã‚Â¡vel")).toBeInTheDocument();
    });

- [ ] **Step 2: Run red**

Run: npm run test -- src/components/lead-table.test.tsx src/components/lead-treatment-modal.dom.test.tsx src/lib/dashboard/queries.test.ts

Expected: potential, controls and row class are absent.

- [ ] **Step 3: Implement minimal UI**

Extend TypeScript CommercialStatus and formatter with potential/Potencial. Add option value potential in LeadTreatmentModal. In LeadTable, use class lead-row--awaiting-treatment only for commentCount === 0.

LeadListControls uses usePathname, useRouter and URLSearchParams; it preserves page, lets administrator set/remove assigneeId, and lets both roles set/remove sort=situation. Dashboard and fila pages read searchParams and pass valid values to getDashboardData. CSS uses a yellow row background, sufficient text contrast and readable hover state.

- [ ] **Step 4: Run green**

Run: npm run test -- src/components/lead-table.test.tsx src/components/lead-treatment-modal.dom.test.tsx src/lib/dashboard/queries.test.ts; npm run typecheck; npm run lint

Expected: focused tests and typecheck pass; lint has no new error.

- [ ] **Step 5: Commit**

    git add apps/web/src/components/lead-list-controls.tsx apps/web/src/lib/api/types.ts apps/web/src/lib/api/client.ts apps/web/src/lib/dashboard/queries.ts apps/web/src/lib/dashboard/format.ts apps/web/src/components/lead-table.tsx apps/web/src/components/lead-treatment-modal.tsx apps/web/src/app/dashboard/page.tsx apps/web/src/app/fila/page.tsx apps/web/src/app/globals.css apps/web/src/components/lead-table.test.tsx apps/web/src/components/lead-treatment-modal.dom.test.tsx apps/web/src/lib/dashboard/queries.test.ts
    git commit -m "feat(web): adiciona filtros e destaque de tratativa"

### Task 5: Janela web de novos leads

**Files:**
- Create: apps/web/src/lib/notifications/actions.ts
- Create: apps/web/src/lib/notifications/queries.ts
- Create: apps/web/src/components/new-leads-notification-modal.tsx
- Modify: apps/web/src/lib/api/client.ts
- Modify: apps/web/src/lib/api/types.ts
- Modify: apps/web/src/app/dashboard/page.tsx
- Modify: apps/web/src/app/globals.css
- Test: apps/web/src/components/new-leads-notification-modal.dom.test.tsx
- Test: apps/web/src/lib/notifications/actions.test.ts

**Consumes:** Task 2 snapshot and acknowledgement routes.

**Produces:** NewLeadsNotificationModal, displayed only to seller and acknowledged only on close.

- [ ] **Step 1: Write failing tests**

    it("acknowledges the watermark only when closing", async () => {
      render(<NewLeadsNotificationModal snapshot={snapshot} />);
      expect(acknowledgeNewLeadsAction).not.toHaveBeenCalled();
      await user.click(screen.getByRole("button", { name: "Fechar" }));
      expect(acknowledgeNewLeadsAction).toHaveBeenCalledWith(snapshot.watermark);
    });

    it("keeps dialog open after acknowledgement failure", async () => {
      vi.mocked(acknowledgeNewLeadsAction).mockResolvedValue({ ok: false, message: "NÃƒÆ’Ã‚Â£o foi possÃƒÆ’Ã‚Â­vel confirmar os novos leads." });
      render(<NewLeadsNotificationModal snapshot={snapshot} />);
      await user.keyboard("{Escape}");
      expect(screen.getByRole("alert")).toHaveTextContent("NÃƒÆ’Ã‚Â£o foi possÃƒÆ’Ã‚Â­vel confirmar os novos leads.");
      expect(screen.getByRole("dialog", { name: "Novos leads" })).toBeVisible();
    });

- [ ] **Step 2: Run red**

Run: npm run test -- src/components/new-leads-notification-modal.dom.test.tsx src/lib/notifications/actions.test.ts

Expected: notification modules are absent.

- [ ] **Step 3: Implement query, action and modal**

queries.ts fetches GET /api/lead-notifications/new with server session cookie and cache no-store. actions.ts is a server action that reads the session, posts watermark and returns { ok, message }. The modal has role dialog, aria-modal, title, focus return, Escape and close button. It does not create mailto, tel or external links. dashboard/page.tsx queries only for seller, tolerates service unavailability without breaking the dashboard, and renders nothing for empty snapshot.

- [ ] **Step 4: Run green**

Run: npm run test -- src/components/new-leads-notification-modal.dom.test.tsx src/lib/notifications/actions.test.ts; npm run typecheck; npm run lint

Expected: tests and typecheck pass; lint has no new error.

- [ ] **Step 5: Commit**

    git add apps/web/src/lib/notifications/actions.ts apps/web/src/lib/notifications/queries.ts apps/web/src/components/new-leads-notification-modal.tsx apps/web/src/lib/api/client.ts apps/web/src/lib/api/types.ts apps/web/src/app/dashboard/page.tsx apps/web/src/app/globals.css apps/web/src/components/new-leads-notification-modal.dom.test.tsx apps/web/src/lib/notifications/actions.test.ts
    git commit -m "feat(web): exibe novos leads em janela interna"

### Task 6: PÃƒÆ’Ã‚Â¡gina administrativa de relatÃƒÆ’Ã‚Â³rios

**Files:**
- Create: apps/web/src/app/relatorios/page.tsx
- Create: apps/web/src/components/reports-dashboard.tsx
- Create: apps/web/src/lib/reports/queries.ts
- Modify: apps/web/src/components/app-shell.tsx
- Modify: apps/web/src/lib/api/types.ts
- Modify: apps/web/src/app/globals.css
- Test: apps/web/src/components/reports-dashboard.test.tsx
- Test: apps/web/src/components/app-shell.test.tsx
- Test: apps/web/src/lib/reports/queries.test.ts

**Consumes:** Task 3 lead distribution response.

**Produces:** /relatorios, admin-only navigation and two accessible bar charts.

- [ ] **Step 1: Write failing tests**

    it("renders situation and seller distributions with text equivalents", () => {
      render(<ReportsDashboard report={report} />);
      expect(screen.getByRole("heading", { name: "Por situaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o" })).toBeVisible();
      expect(screen.getByText("Potencial: 3")).toBeVisible();
      expect(screen.getByRole("heading", { name: "Por vendedor" })).toBeVisible();
    });

    it("shows RelatÃƒÆ’Ã‚Â³rios only to admin", () => {
      expect(renderShell(admin).getByRole("link", { name: "RelatÃƒÆ’Ã‚Â³rios" })).toBeVisible();
      expect(renderShell(seller).queryByRole("link", { name: "RelatÃƒÆ’Ã‚Â³rios" })).toBeNull();
    });

- [ ] **Step 2: Run red**

Run: npm run test -- src/components/reports-dashboard.test.tsx src/components/app-shell.test.tsx src/lib/reports/queries.test.ts

Expected: reports files and navigation link are absent.

- [ ] **Step 3: Implement server-rendered report page**

The route gets session and redirects seller to /dashboard. It parses all-history default, current month, last 30 days and custom from/to. queries.ts calls the administrative report endpoint with session cookie. AppShell receives /relatorios in its activePath union and renders the link only for administrator.

ReportsDashboard uses a GET form and CSS bars whose width is count / maximum ÃƒÆ’Ã¢â‚¬â€ 100. Every visual bar has visible text Name: N, and both groups have a zero-data empty state. Do not add a chart dependency.

- [ ] **Step 4: Run green**

Run: npm run test -- src/components/reports-dashboard.test.tsx src/components/app-shell.test.tsx src/lib/reports/queries.test.ts; npm run typecheck; npm run lint

Expected: focused suite passes and seller has no report navigation.

- [ ] **Step 5: Commit**

    git add apps/web/src/app/relatorios/page.tsx apps/web/src/components/reports-dashboard.tsx apps/web/src/lib/reports/queries.ts apps/web/src/components/app-shell.tsx apps/web/src/lib/api/types.ts apps/web/src/app/globals.css apps/web/src/components/reports-dashboard.test.tsx apps/web/src/components/app-shell.test.tsx apps/web/src/lib/reports/queries.test.ts
    git commit -m "feat(web): adiciona relatÃƒÆ’Ã‚Â³rios administrativos"

### Task 7: E2E, capturas e evidÃƒÆ’Ã‚Âªncias

**Files:**
- Create or Modify: apps/web/e2e/operacao-notificacoes-relatorios.spec.ts
- Create: docs/evidencias/2026-09-14-notificacoes-internas-tratativas-relatorios.md
- Modify: docs/CONTEXTO_MESTRE_GERENCIADOR_DE_LEADS.md only through its generator

**Consumes:** Tasks 1ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“6.

**Produces:** acceptance evidence, screenshots 1440ÃƒÆ’Ã¢â‚¬â€900 and final quality gates.

- [ ] **Step 1: Write E2E acceptance tests**

    test("seller sees new lead, records Potencial and clears current marker", async ({ page }) => {
      await signInAs(page, "sandra@wtgseguros.com.br");
      await expect(page.getByRole("dialog", { name: "Novos leads" })).toBeVisible();
      await page.getByRole("button", { name: "Fechar" }).click();
      await page.getByRole("button", { name: /Registrar tratativa/ }).first().click();
      await page.getByLabel("SituaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o comercial").selectOption("potential");
      await page.getByLabel("Marcar como Desqualificado").uncheck();
      await page.getByLabel("ComentÃƒÆ’Ã‚Â¡rio").fill("Cliente pediu nova proposta comercial");
      await page.getByRole("button", { name: "Salvar tratativa" }).click();
      await expect(page.getByText("Desqualificado")).not.toBeVisible();
    });

    test("admin filters leads and views reports", async ({ page }) => {
      await signInAs(page, "yago@wtgseguros.com.br");
      await page.getByLabel("ResponsÃƒÆ’Ã‚Â¡vel").selectOption({ label: "Sandra" });
      await page.getByRole("link", { name: "RelatÃƒÆ’Ã‚Â³rios" }).click();
      await expect(page.getByRole("heading", { name: "Por situaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o" })).toBeVisible();
    });

- [ ] **Step 2: Run the E2E test and correct only fixture/selector gaps**

Run: npm run test:e2e -- operacao-notificacoes-relatorios.spec.ts

Expected: test passes after Tasks 1ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“6. Preserve authorization assertions; do not weaken them to make a fixture pass.

- [ ] **Step 3: Capture visual evidence**

Capture seller-new-leads-1440x900.png, admin-lead-filter-1440x900.png and admin-reports-1440x900.png after asserted visible states. Use a 1440ÃƒÆ’Ã¢â‚¬â€900 viewport and agent-browser or the existing Playwright screenshot fixture.

- [ ] **Step 4: Run all gates**

    python -m pytest apps/api/tests -q
    npm run test
    npm run lint
    npm run typecheck
    npm run build
    npm run test:e2e
    git diff --check

Expected: no failure, no lint error, successful build and E2E. Record any pre-existing warning separately.

- [ ] **Step 5: Record evidence and regenerate context**

Create the evidence table with actual command totals, E2E result, screenshots and authorization result. Then run:

    powershell -NoProfile -ExecutionPolicy Bypass -File scripts/generate-master-context.ps1
    git diff --check

- [ ] **Step 6: Commit**

    git add apps/web/e2e/operacao-notificacoes-relatorios.spec.ts docs/evidencias/2026-09-14-notificacoes-internas-tratativas-relatorios.md docs/CONTEXTO_MESTRE_GERENCIADOR_DE_LEADS.md
    git commit -m "test: valida notificaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Âµes internas e relatÃƒÆ’Ã‚Â³rios"

## Plan self-review

| Requisito aprovado | Tarefa |
| --- | --- |
| Potencial | 1, 4 |
| Desqualificado reflete a ÃƒÆ’Ã‚Âºltima tratativa, com histÃƒÆ’Ã‚Â³rico preservado | 1, 7 |
| Destaque amarelo sem efeito operacional | 4, 7 |
| Cursor persistente, atribuiÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o/transferÃƒÆ’Ã‚Âªncia futura e sem e-mail | 2, 5, 7 |
| Filtro administrativo e ordenaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o para ambos | 3, 4, 7 |
| RelatÃƒÆ’Ã‚Â³rios admin por situaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o/proprietÃƒÆ’Ã‚Â¡rio atual e perÃƒÆ’Ã‚Â­odo por atribuiÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o atual | 3, 6, 7 |
| AutorizaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o, concorrÃƒÆ’Ã‚Âªncia, FIFO e validaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o visual | 2, 3, 5, 7 |

A ordem dos contratos ÃƒÆ’Ã‚Â© consistente: Task 1 introduz potential; Task 2 produz a API que Task 5 consome; Task 3 produz a API que Task 6 consome. Nenhuma tarefa cria e-mail ou modifica o cursor FIFO.

## Plano histórico ou executável: `docs/superpowers/plans/2026-09-22-cadastro-manual-fila-alternativa-exportacoes.md`

# Cadastro manual, fila alternativa e exportações — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permitir que administradores cadastrem leads manuais em uma fila alternativa independente, que vendedores recebam/tratem esses leads e que administradores exportem todos os leads em Excel com histórico de exportações separado.

**Architecture:** O backend criará um comando transacional para lead manual e reutilizará o motor FIFO com `queueKind=manual`, mantendo cursor e auditoria separados de `queueKind=automatic`. A web consumirá rotas administrativas para cadastro, exportação e histórico; a geração do `.xlsx` permanecerá no backend. Os dois gráficos de relatórios serão convertidos em colunas verticais, um por linha completa.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, MongoDB/Motor, pytest; Next.js 16, React 19, TypeScript, Vitest, Playwright, `openpyxl` para Excel.

**Spec:** `docs/superpowers/specs/2026-09-22-cadastro-manual-fila-alternativa-exportacoes-design.md`

## Global Constraints

- Somente administradores podem criar leads manuais, exportar leads e consultar o histórico de exportações.
- O vendedor não escolhe o responsável; a fila alternativa usa a mesma ordem da fila principal e um cursor independente.
- Vendedores Pausados ou indisponíveis são pulados; o próximo vendedor Ativo elegível recebe o lead.
- A fila alternativa não altera cursor, posição, créditos ou atribuições da fila automática.
- Situação inicial de todo lead manual: `Indefinido`.
- Todo lead manual recebe `manualQueueLeadId` único, gerado pelo backend; não reutiliza `sourceLeadId`.
- Leads manuais atribuídos geram a notificação interna já existente; não criar envio de e-mail.
- O download é exclusivamente um arquivo Excel `.xlsx` contendo leads; tratativas e histórico de exportações não são baixados.
- Datas exportadas usam `America/Sao_Paulo`; telefones e identificadores são células de texto.
- O histórico de exportações mostra data/hora, administrador responsável, quantidade, filtros e status.
- O frontend nunca é fonte de autorização; comandos críticos e escopo vivem na API/domínio.
- Toda alteração de banco usa migração versionada; não editar migrações aplicadas.
- Testes de concorrência, idempotência, rollback, escopo e falha de exportação são obrigatórios.
- Preservar os arquivos preexistentes `D apps/api/.env.example` e `?? tools/google-sheets-diagnostic/`.

## Mapa de arquivos e interfaces

### Backend

- `apps/api/src/gerec_api/domain/manual_leads.py`: comando e tipos do cadastro manual.
- `apps/api/src/gerec_api/domain/queue.py`: seleção com `queueKind` e cursor alternativo.
- `apps/api/src/gerec_api/domain/exportations.py`: contrato e geração de exportação.
- `apps/api/src/gerec_api/routes/admin.py`: rotas administrativas de criação, exportação e histórico.
- `apps/api/src/gerec_api/auth/permissions.py`: leituras administrativas e escopo.
- `apps/api/src/gerec_api/infrastructure/mongo/lead_repository.py`: persistência do lead manual.
- `apps/api/src/gerec_api/infrastructure/mongo/queue_repository.py`: estado/cursor por tipo de fila.
- `apps/api/src/gerec_api/infrastructure/mongo/exportation_repository.py`: histórico de exportações.
- `apps/api/src/gerec_api/infrastructure/mongo/migrations/20260922_manual_queue_exportations.py`: migração versionada.
- `apps/api/tests/integration/test_manual_leads.py`: comandos, autorização, fila e notificações.
- `apps/api/tests/integration/test_exportations.py`: Excel, histórico e falhas.

### Web

- `apps/web/src/app/usuarios/page.tsx` ou shell administrativo: ação “Adicionar leads”.
- `apps/web/src/components/manual-lead-form.tsx`: formulário administrativo.
- `apps/web/src/components/exportations-panel.tsx`: download e histórico.
- `apps/web/src/lib/admin/manual-lead-actions.ts`: Server Action de criação.
- `apps/web/src/lib/admin/exportation-queries.ts`: consulta do histórico.
- `apps/web/src/app/exportacoes/download/route.ts`: Route Handler autenticado que transmite o `.xlsx`.
- `apps/web/src/lib/api/types.ts` e `client.ts`: contratos HTTP.
- `apps/web/src/app/relatorios/page.tsx`, `reports-dashboard.tsx`, `globals.css`: colunas em linhas completas.
- Testes DOM/unitários correspondentes em `apps/web/src/components/*test.tsx` e `apps/web/src/lib/admin/*test.ts`.

## Task 1: Modelo de dados, ID manual e cursor alternativo

**Files:**
- Create: `apps/api/src/gerec_api/domain/manual_leads.py`
- Modify: `apps/api/src/gerec_api/domain/queue.py`
- Modify: `apps/api/src/gerec_api/infrastructure/mongo/lead_repository.py`
- Modify: `apps/api/src/gerec_api/infrastructure/mongo/queue_repository.py`
- Create: `apps/api/src/gerec_api/infrastructure/mongo/migrations/20260922_manual_queue_exportations.py`
- Test: `apps/api/tests/integration/test_manual_leads.py`

**Interfaces:**
- Produces `ManualLeadCommand(name, email, phone, campaign?, source?, idempotency_key)`.
- Produces `create_manual_lead(actor, command, now) -> ManualLeadResult`.
- Produces `select_next_seller(queue_kind: Literal["automatic", "manual"], now) -> SellerSelection`.
- `manualQueueLeadId` é texto `MAN-` + UUID4, com índice único.

- [ ] Escrever testes vermelhos para criação, situação inicial, ID único, cursor independente, salto de Pausado, herança de campanha e idempotência.
- [ ] Rodar `python -m pytest apps/api/tests/integration/test_manual_leads.py -q`; confirmar falhas por interfaces ausentes.
- [ ] Implementar o comando transacional e migração sem alterar o cursor automático.
- [ ] Rodar o teste focado e a suíte de filas; confirmar verde.
- [ ] Commit: `feat(api): adiciona fila alternativa para leads manuais`.

## Task 2: Rotas administrativas de criação e notificação

**Files:**
- Modify: `apps/api/src/gerec_api/routes/admin.py`
- Modify: `apps/api/src/gerec_api/main.py`
- Modify: `apps/api/src/gerec_api/domain/lead_notifications.py`
- Test: `apps/api/tests/integration/test_manual_leads.py`

**Interfaces:**
- `POST /api/admin/leads/manual` recebe nome, e-mail, telefone, campanha/origem opcional e `Idempotency-Key`.
- Retorna `201` com `leadId`, `manualQueueLeadId`, `assigneeId`, `assignedAt`, `commercialStatus="undefined"` e `source="manual"`.
- Vendedor recebe `403` em criação; campos inválidos retornam `422`.
- A atribuição publica a mesma sequência/cursor de notificação já consumida pelo dashboard.

- [ ] Escrever testes vermelhos de autorização, validação, resposta, notificação e rollback.
- [ ] Rodar testes e confirmar falhas esperadas.
- [ ] Implementar rota fina, delegando ao comando transacional.
- [ ] Rodar integração focada e permissões; confirmar verde.
- [ ] Commit: `feat(api): expõe cadastro manual de leads`.

## Task 3: Exportação Excel e histórico administrativo

**Files:**
- Create: `apps/api/src/gerec_api/domain/exportations.py`
- Create: `apps/api/src/gerec_api/infrastructure/mongo/exportation_repository.py`
- Modify: `apps/api/src/gerec_api/routes/admin.py`
- Modify: `apps/api/src/gerec_api/main.py`
- Test: `apps/api/tests/integration/test_exportations.py`

**Interfaces:**
- `GET /api/admin/exportations` retorna histórico paginado com `createdAt`, `administratorName`, `leadCount`, `filters` e `status`.
- `GET /api/admin/exportations/leads` retorna `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` e cria registro de sucesso/erro.
- `ExportationService.export_leads(actor, filters, now) -> ExportationResult`.
- Datas no workbook são formatadas em `America/Sao_Paulo`; IDs/telefones são texto.

- [ ] Escrever testes vermelhos para Excel com cabeçalhos, exportação vazia, histórico, vendedor proibido e falha sem falso sucesso.
- [ ] Rodar testes focados e confirmar falhas esperadas.
- [ ] Implementar geração com `openpyxl`, auditoria de status e tratamento seguro de erro.
- [ ] Rodar testes de exportação e validar MIME, colunas, timezone e conteúdo.
- [ ] Commit: `feat(api): adiciona exportação administrativa de leads`.

## Task 4: Formulário web de lead manual

**Files:**
- Create: `apps/web/src/components/manual-lead-form.tsx`
- Create: `apps/web/src/lib/admin/manual-lead-actions.ts`
- Modify: `apps/web/src/lib/api/types.ts`
- Modify: `apps/web/src/lib/api/client.ts`
- Modify: `apps/web/src/app/usuarios/page.tsx`
- Test: `apps/web/src/components/manual-lead-form.test.tsx`
- Test: `apps/web/src/lib/admin/manual-lead-actions.test.ts`

**Interfaces:**
- `ManualLeadForm` aceita `latestCampaignDefaults` e não renderiza seletor de responsável.
- Server Action `createManualLeadAction(input) -> { ok: boolean; message: string; lead? }`.
- Campos name/email/phone obrigatórios; status é exibido como `Indefinido` e não editável.

- [ ] Escrever testes vermelhos para campos, status fixo, ausência de responsável, sucesso, erro e seller sem acesso.
- [ ] Rodar Vitest focado e confirmar falhas esperadas.
- [ ] Implementar modal/painel e Server Action com revalidação de dashboard/fila/notificações.
- [ ] Rodar Vitest, typecheck e lint.
- [ ] Commit: `feat(web): adiciona cadastro manual de leads`.

## Task 5: Guia de exportações e histórico

**Files:**
- Create: `apps/web/src/components/exportations-panel.tsx`
- Create: `apps/web/src/lib/admin/exportation-queries.ts`
- Create: `apps/web/src/app/exportacoes/download/route.ts`
- Modify: `apps/web/src/components/app-shell.tsx`
- Modify: `apps/web/src/lib/api/types.ts`
- Modify: `apps/web/src/app/globals.css`
- Test: `apps/web/src/components/exportations-panel.test.tsx`
- Test: `apps/web/src/lib/admin/exportation-queries.test.ts`
- Test: `apps/web/src/components/app-shell.test.tsx`

**Interfaces:**
- Rota `/exportacoes` somente para administrador.
- `getExportationHistory()` chama `GET /api/admin/exportations`.
- `GET /exportacoes/download` no Route Handler web repassa a autenticação e transmite o `.xlsx` sem converter bytes em string ou expor credenciais.
- A tela mostra data/hora, administrador responsável, quantidade, filtros e status; não mostra botão para baixar histórico.

- [ ] Escrever testes vermelhos de navegação admin/seller, download apenas de leads, histórico, loading, erro e retry.
- [ ] Rodar Vitest focado e confirmar falhas esperadas.
- [ ] Implementar guia e integração no shell mantendo o shell em erro.
- [ ] Rodar Vitest, typecheck e lint.
- [ ] Commit: `feat(web): adiciona guia de exportações`.

## Task 6: Layout dos relatórios em colunas

**Files:**
- Modify: `apps/web/src/components/reports-dashboard.tsx`
- Modify: `apps/web/src/app/globals.css`
- Test: `apps/web/src/components/reports-dashboard.test.tsx`

**Interfaces:**
- Mantém somente os grupos `bySituation` e `bySeller` já existentes.
- Cada grupo renderiza colunas verticais em um container de largura total.
- Cada coluna possui texto acessível `Nome: N` e altura proporcional ao maior valor do próprio grupo.

- [ ] Escrever teste vermelho que exija dois containers em linhas distintas, classes de coluna e texto equivalente.
- [ ] Rodar o teste e confirmar falha com o layout atual.
- [ ] Implementar CSS/markup sem dependência de biblioteca de gráficos.
- [ ] Rodar testes, typecheck, lint e screenshot local 1440x900.
- [ ] Commit: `feat(web): reorganiza relatórios em colunas`.

## Task 7: E2E, evidências e contexto mestre

**Files:**
- Create or Modify: `apps/web/e2e/cadastro-manual-exportacoes.spec.ts`
- Create: `docs/evidencias/2026-09-22-cadastro-manual-fila-alternativa-exportacoes.md`
- Modify: `docs/CONTEXTO_MESTRE_GERENCIADOR_DE_LEADS.md` only through generator
- Modify: `.github/workflows/gerec-leads-ci.yml` only if the existing contract tests require the new route/build gate

**Interfaces:**
- E2E admin cria lead manual, confirma ID/Indefinido, aguarda notificação do vendedor e verifica tratativa.
- E2E admin baixa `.xlsx`, valida nome/MIME/colunas e confere uma linha no arquivo.
- E2E admin consulta histórico; seller não vê `/exportacoes` nem acessa endpoints.
- E2E confirma fila automática sem alteração e relatórios com duas linhas completas de colunas.

- [ ] Escrever os fluxos E2E antes da implementação final da integração.
- [ ] Rodar `npm run test:e2e -- cadastro-manual-exportacoes.spec.ts` e corrigir somente fixture/selector/contrato legítimo.
- [ ] Capturar telas 1440x900 de cadastro, exportação e relatórios.
- [ ] Rodar gates: `python -m pytest apps/api/tests -q`, `npm run test`, `npm run lint`, `npm run typecheck`, `npm run build`, `npm run test:e2e`, `git diff --check`.
- [ ] Registrar totais, screenshots, permissões e limitações reais na evidência.
- [ ] Regenerar contexto com `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/generate-master-context.ps1`.
- [ ] Commit: `test: valida cadastro manual e exportações`.

## Execution order and review gates

Tasks 1–3 são backend e devem ser revisadas antes de Tasks 4–5. Task 6 pode
rodar em paralelo com Task 4–5 porque usa apenas o contrato já existente de
relatórios. Task 7 só começa após todas as integrações anteriores.

Cada task exige implementador separado, pacote de revisão, revisor independente,
correção e re-revisão até não haver findings críticos/importantes. Nenhuma task
é marcada como concluída sem testes recentes e registro no ledger SDD.

## Documento complementar: `apps/web/README.md`

# Aplicação web

Consulte o [README do projeto](../../README.md) para instalação, execução, verificação e encerramento.

Execute todos os comandos a partir da raiz `gerec_leads/`. A página inicial está em `src/app/page.tsx`.

## Documento complementar: `infra/railway/README.md`

# Serviços Railway

`railway.json` contém apenas o build compartilhado. Como cada serviço Railway possui seu próprio comando de início, configure os três processos abaixo no painel do ambiente correspondente.

| Serviço | Tipo | Comando | Agenda |
| --- | --- | --- | --- |
| `api` | persistente/web | `uvicorn gerec_api.main:create_app --factory --host 0.0.0.0 --port ${PORT:-8000}` via `apps/api/Dockerfile` | — |
| `outbox-worker` | persistente/worker | `python -m gerec_api.automation.outbox_worker` | — |
| `google-sheets-sync` | cron | `python -m gerec_api.automation.scheduler` | `*/5 * * * *` |

Defina `MONGODB_URI`, `MONGODB_DATABASE` e `APP_SECRET` em cada serviço no painel Railway. Para o cron, defina `GOOGLE_SHEETS_SPREADSHEET_ID`, `GOOGLE_SHEETS_RANGE` e `GOOGLE_SERVICE_ACCOUNT_JSON`; para o worker, `OUTBOX_DELIVERY_WEBHOOK_URL` e, se necessário, `OUTBOX_DELIVERY_TOKEN`. Todos os valores ficam exclusivamente nas variáveis Railway; não registre valores no repositório. O cron deve finalizar após cada execução e retornar erro quando a sincronização falhar.

Os jobs usam a mesma camada de domínio da API. O sincronizador só finaliza o snapshot após importar todas as linhas e mantém lease com geração/token; uma geração antiga não arquiva um snapshot novo. O worker reivindica cada evento com claim token, aplica fencing no ack/retry e encaminha a chave de idempotência ao provedor.

## Documento complementar: `integrations/n8n/README.md`

# Integração removida

O sistema novo não usa n8n. Sincronizações, consumo da outbox, retries e agendas são processos Python publicados na Railway e usam os serviços de domínio da API.

Configuração operacional: `infra/railway/README.md`.

## Documento complementar: `tests/contracts/README.md`

# Testes de contrato

Este diretório abrigará contratos de integrações externas a partir da Etapa 4.
Não há integração real habilitada na Etapa 1.

## Evidência: `docs/evidencias/2026-08-28-reconstrucao-operacional.md`

# Evidências da reconstrução operacional — Gerenciador de Leads WTG

Data da verificação: 31/08/2026
Worktree: `.worktrees/migracao-mongodb-vercel-railway`
Branch: `feat/migracao-mongodb-vercel-railway`

## Escopo validado

Este registro fecha o gate operacional das Tasks 1–16 do plano de reconstrução. A validação cobre o núcleo Python/MongoDB, contratos HTTP, cliente Next.js, permissões administrativas e de vendedor, tratativas comerciais, fila FIFO dinâmica, paginação, usuários, SLA de 24 horas úteis e os fluxos E2E em desktop.

## Comandos e resultados

| Comando | Resultado observado |
| --- | --- |
| `python -m pytest apps/api/tests -q` | **151 passed, 8 skipped** em 20,82 s |
| `npm run test --workspace=@wtg/web -- --run` | **16 arquivos, 78 testes aprovados** |
| `npm run lint --workspace=@wtg/web` | **0 erros, 2 avisos** preexistentes: uso de `<img>` e import não usado em teste |
| `npm run typecheck --workspace=@wtg/web` | **Aprovado**, `tsc --noEmit` sem saída de erro |
| `npm run build --workspace=@wtg/web` | **Aprovado**, Next.js 16.3.3 compilou e gerou as rotas |
| `node --test tests/contracts/*.test.mjs` | **5 testes aprovados** |
| `npx playwright test --project=chromium` | **12 testes aprovados** em 18,1 s |
| `powershell -ExecutionPolicy Bypass -File scripts/generate-master-context.ps1` | **Aprovado**, contexto mestre regenerado com 19.521 linhas |
| `git diff --check` | Executado no gate; nenhuma falha de whitespace registrada |

## E2E e referências visuais

Os fluxos foram executados com fixture local determinística, sem produção, Google Sheets ou MongoDB real. A suíte Chromium usa viewport 1440×900 e cobre:

- autenticação válida e inválida;
- redirecionamento e isolamento por perfil;
- criação de vendedor no fim da fila, pausa, ativação e redefinição de senha;
- leitura administrativa sem controles de edição de tratativas;
- paginação semântica de fila e histórico;
- tratativa do vendedor com comentário mínimo, status, contador e desqualificação;
- snapshots do dashboard administrativo, usuários/modal, fila/histórico e dashboard/modal do vendedor.

## Limitações conhecidas

- O escopo continua exclusivamente desktop (largura mínima de 1280 px).
- Os oito skips da suíte API correspondem aos testes condicionados à disponibilidade de replica set MongoDB.
- O lint mantém dois avisos não bloqueantes listados acima; não há erros.
- A suíte visual é uma referência determinística do fixture e não substitui validação com dados reais da operação.
- Integração definitiva com a planilha, e-mail, WhatsApp e operação de produção permanecem fora deste gate.

## Correção necessária encontrada no gate

O contrato HTTP controlado ainda não preenchia `last_updated_at` ao criar seu `TreatmentResult`, embora o domínio já exigisse o carimbo persistido autoritativo. O fixture foi atualizado para usar um timestamp fixo de 28/08/2026; após a correção, os cinco contratos HTTP passaram. Nenhuma regra de negócio de produção foi alterada.

## Integridade e arquivos protegidos

Não foram feitos push, merge, deploy ou ações externas. Os arquivos preexistentes protegidos foram preservados sem inclusão:

- `apps/api/.env.example` permanece uma exclusão preexistente;
- `tools/google-sheets-diagnostic/` permanece não rastreado e fora da alteração.

Segredos, credenciais e acesso direto ao MongoDB não foram expostos ao navegador nem adicionados à evidência.

## Evidência: `docs/evidencias/2026-09-14-notificacoes-internas-tratativas-relatorios.md`

# Evidências — notificações internas, tratativas e relatórios

Data da validação: 15/09/2026.

## Aceitação E2E

| Cenário | Resultado | Evidência |
| --- | --- | --- |
| Vendedora Sandra recebe a janela de novos leads, registra `Potencial` e remove o marcador atual | Aprovado | `tests/e2e/operacao-notificacoes-relatorios.spec.ts` |
| Administrador filtra a lista pelo responsável Sandra e acessa os dois agrupamentos de relatórios | Aprovado | `tests/e2e/operacao-notificacoes-relatorios.spec.ts` |
| Vendedora é redirecionada de `/relatorios` para `/dashboard` sem requisição a `/api/admin/reports/lead-distribution` | Aprovado | Asserção direta de URL, navegação e requisições no spec de aceitação |
| Referências visuais integradas | Aprovado | 15 cenários E2E, incluindo 2 snapshots visuais, aprovados |

O briefing indicava `apps/web/e2e`, mas o `playwright.config.ts` executa exclusivamente `tests/e2e`. O spec foi criado em `tests/e2e/operacao-notificacoes-relatorios.spec.ts` para permanecer coberto pela gate oficial, sem alterar a configuração do runner.

## Capturas visuais — 1440×900

| Estado validado | Arquivo |
| --- | --- |
| Janela interna de novos leads para Sandra | [seller-new-leads-1440x900.png](seller-new-leads-1440x900.png) |
| Dashboard administrativo filtrado por Sandra | [admin-lead-filter-1440x900.png](admin-lead-filter-1440x900.png) |
| Relatórios administrativos por situação e vendedor | [admin-reports-1440x900.png](admin-reports-1440x900.png) |

As capturas foram produzidas com `agent-browser`, sessão isolada `task7-a5e9fbb32f66`, viewport 1440×900 e estados confirmados pela árvore de acessibilidade. As referências Playwright foram atualizadas para a composição aprovada após as Tasks 1–6.

## Gates finais

| Comando | Resultado real |
| --- | --- |
| `python -m pytest apps/api/tests -q` | 187 aprovados, 9 ignorados, em 20,73 s |
| `npm run test` | 25 arquivos, 105 testes aprovados, em 11,42 s |
| `npm run lint` | 0 erros; 1 aviso preexistente |
| `npm run typecheck` | Aprovado |
| `npm run build` | Aprovado; build otimizado concluído |
| `npm run test:e2e` | 15 testes aprovados, em 26,1 s |
| `git diff --check` | Aprovado após regeneração do contexto |

## Aviso preexistente

`apps/web/src/components/login-form.tsx:13:38` mantém o aviso `@next/next/no-img-element` para `<img>`. Não foi introduzido nem alterado nesta tarefa; o lint terminou sem erros.

## Escopo da correção de fixture

A fixture local E2E passou a representar a janela pendente somente para Sandra, adicionou os contratos de notificação/acknowledgement, filtro administrativo e agregação de relatórios. Também acompanha `potential` e o marcador de desqualificação da última tratativa. Nenhum arquivo de produção ou backend foi modificado.

## Evidência: `docs/evidencias/etapa-1.md`

# Evidência histórica da Etapa 1

Data: 25 de agosto de 2026.

Esta etapa registrou a fundação anterior, baseada em Supabase local. Ela foi substituída pela arquitetura MongoDB, API Python na Railway e cliente Next.js na Vercel, aprovada em 27 de agosto de 2026. Nenhum comando, configuração ou dependência dessa fundação permanece operacional; a remoção física foi concluída na Tarefa 12 da migração.

O fixture `WTG - Leads.xlsx` não foi alterado. SHA-256 registrado: `83238297C3460E25D938142E5248F33039F02F75720C9E8BE690B4DC98D72CF4`.

## Evidência: `docs/evidencias/migracao-mongodb-vercel-railway.md`

# Evidência operacional da migração MongoDB, Vercel e Railway

## Arquitetura operacional

- MongoDB é a única persistência, no database `gerec_leads`, com replica set obrigatório.
- API e worker Python recebem `MONGODB_URI`, `MONGODB_DATABASE` e `APP_SECRET` somente no ambiente do processo ou no painel Railway.
- A Vercel recebe somente `NEXT_PUBLIC_API_URL`; MongoDB e segredos nunca são enviados ao cliente web.
- Os artefatos Supabase e seu tooling foram removidos após cobertura equivalente por API, contratos e E2E.

## Reprodução local

```powershell
npm ci
cd apps/api
python -m pip install -e ".[dev]"
cd ../..
$env:MONGODB_URI = "mongodb://127.0.0.1:27017/?replicaSet=rs0"
$env:MONGODB_DATABASE = "gerec_leads"
$env:APP_SECRET = "replace-with-a-local-secret"
$env:NEXT_PUBLIC_API_URL = "http://127.0.0.1:8000"
npm run mongodb:start
npm run mongodb:bootstrap
npm run api:start
npm run web:start
npm run worker:start
```

Os comandos Railway e as variáveis adicionais para Google Sheets e entrega de notificações estão em `infra/railway/README.md`.

## Verificação

Os resultados da verificação final e as limitações locais estão registrados em `task-12-report.md`.

## Relatório histórico: `task-10-report.md`

# Relatório da Tarefa 10 — Automações Python Railway

## Entrega

- Criados `sync_job.py`, `outbox_worker.py` e `scheduler.py` no pacote Python da API.
- `run_sync(source, run_id)` usa somente `LeadService`: processa o snapshot completo, fixa `source_snapshot_id` no `run_id`, usa uma chave estável por linha e só chama o arquivamento depois de todas as importações concluírem.
- `process_outbox(batch_size)` é composto sobre uma outbox Mongo com claim atômico, claim token/fencing, tentativas limitadas, retry e dead-letter. Cada evento leva sua chave de idempotência ao webhook configurado na Railway; `notification_incidents` recebe no máximo um incidente por evento terminal. Sem URL do provedor, o worker falha antes de reivindicar eventos.
- `run_due_jobs(now)` serializa o sync pelo slot UTC de cinco minutos em `automation_job_locks`; falhas liberam o lock sem marcar o slot como concluído e o entrypoint retorna código não zero.
- `GoogleSheetsAdapter` consulta a API Values do Google Sheets com `GOOGLE_SHEETS_SPREADSHEET_ID`, `GOOGLE_SHEETS_RANGE` e `GOOGLE_SHEETS_ACCESS_TOKEN` exclusivamente no ambiente Railway, mantendo a validação exata do contrato A–Q.
- O sync usa lease com token e geração, renovado antes de cada linha e antes do arquivamento. Ao perder a geração, aborta sem chamar `archive_missing`.
- Índices únicos protegem `notification_outbox.idempotencyKey` e `notification_incidents.outboxEventId`. A coleção de locks entrou no bootstrap Mongo. Essa extensão de `test_indexes.py` registra precisamente esses novos invariantes, sem alterar regra existente.
- Eventos de operações agora sempre iniciam `attempts: 0`; lembretes com `status: scheduled` tornam-se elegíveis somente em `scheduledFor`.
- Adicionados `railway.json` e `infra/railway/README.md` com os processos `api`, `outbox-worker` e cron de sync `*/5 * * * *`, além das variáveis server-side obrigatórias `MONGODB_URI`, `MONGODB_DATABASE` e `APP_SECRET`.
- `integrations/n8n/README.md` agora registra a remoção da integração: o novo sistema não usa n8n.

## Cobertura

- Replay de snapshot completo com chaves de linha estáveis.
- Retry do worker e entrega única após sucesso.
- Exclusão mútua do scheduler no mesmo slot e execução no slot seguinte.
- Contrato de deploy Railway sem credenciais versionadas.
- Eventos de feedback com contador de tentativas inicial.
- Fencing de outbox contra worker com lease vencido; provider recebe `Idempotency-Key`; sync antigo não arquiva snapshot novo; cron falho retorna exit code 1.
- Payloads reais da outbox com `ObjectId` e `datetime` são projetados para strings JSON antes do POST, sem alterar sua chave de idempotência.

## Verificação

```text
pytest -q
95 passed, 5 skipped in 15.83s

python -m compileall -q src
passed

python -m json.tool railway.json
passed
```

Os cinco skips continuam exigindo MongoDB local em replica set.

## Composição externa

O worker usa um webhook configurado no ambiente Railway e encaminha `Idempotency-Key`; o provedor final deve respeitar essa chave. Não há credenciais no repositório.

## Relatório histórico: `task-11-report.md`

# Relatório da Tarefa 11 — Deploy Vercel, contratos e E2E

## Entrega

- Criado `vercel.json` para o deploy do workspace Next.js sem segredos versionados. A única variável necessária na Vercel permanece `NEXT_PUBLIC_API_URL`.
- A API Railway agora envia `X-Gerec-API-Contract-Version: 1` em todas as respostas. Os contratos iniciam um processo FastAPI controlado, com banco em memória, e verificam health, login, sessão, erros e payloads mínimos de auth, imports/leads, queue, operations e admin.
- A resposta administrativa agora remove `passwordHash` e `tokenHash`. A alteração em `admin.py` foi necessária porque o contrato controlado expôs que `GET /api/admin/users` retornava o hash de senha, contrariando a exigência de não expor segredos.
- A suíte Playwright cobre o visitante sem sessão, login, usuário desativado, navegação de administrador, isolamento do vendedor, interação de tentativa pela interface, ciclo contato → qualificado → ganho idempotente, nova venda com chave distinta rejeitada e cinco tentativas antes da desqualificação manual.
- O workflow GitHub Actions inicia MongoDB em replica set, API Python e Next.js, cria dados isolados de E2E, executa Python, verificações web escopadas, contratos e E2E; o encerramento de processos e volumes ocorre com `if: always()`. Somente `npm run format:check` é informativo com `continue-on-error`; lint, typecheck, Vitest, contratos e E2E permanecem bloqueantes.
- `APP_SECRET` e a senha E2E são gerados pelo runner com `openssl` e persistidos apenas no ambiente efêmero do job. O servidor de contratos recebe segredo e senha aleatórios do processo Node, sem valores de credencial literais no repositório.

## Verificação

```text
python -m pytest apps/api/tests -q
95 passed, 5 skipped

npm run typecheck
passed

npm run lint
passed

npm run test
6 files / 18 tests passed

npm run test:e2e
1 passed, 6 skipped sem API, credenciais e fixture E2E locais

node --test tests/contracts/api-contracts.test.mjs
2 passed

node --test tooling/tests/ci-contract.test.mjs
1 passed
```

`npm run check` continua bloqueado por formatação pré-existente: o Prettier lista 42 arquivos fora do escopo desta tarefa, inclusive arquivos não modificados. Todos os arquivos TypeScript/JSON/YAML alterados nesta tarefa foram verificados individualmente com Prettier.

## Limitações locais

Os cinco skips Python exigem MongoDB local em replica set. Os seis E2E de autenticação, papéis e ciclo exigem API ativa, usuários/dados E2E e `API_CONTRACT_BASE_URL`; o CI fornece esses pré-requisitos. O teste de fundação continua executável localmente sem a API.

## Relatório histórico: `task-12-report.md`

# Relatório da Tarefa 12 — Remoção Supabase e fechamento operacional

## Entrega

- Removidos `supabase/`, `tooling/supabase/`, o teste dependente desse tooling e o pacote `supabase` do workspace.
- Substituídos scripts Supabase por comandos PowerShell versionados para iniciar e encerrar o replica set MongoDB, aplicar bootstrap, iniciar API, web e worker.
- Criado `apps/api/.env.example` com somente `MONGODB_URI`, `MONGODB_DATABASE` e `APP_SECRET`. O exemplo web e a documentação operacional mantêm somente `NEXT_PUBLIC_API_URL` no cliente.
- Atualizados README, tarefa de inicialização, instruções de agente e evidências operacionais. Menções restantes a Supabase/PostgreSQL são registros históricos classificados no SPEC, roadmap, decisões ou relatórios de tarefas anteriores.
- Adicionado teste estrutural que exige os novos scripts e impede a volta dos diretórios e dependências removidos.
- O launcher local inicia API e web com `ProcessStartInfo` e ambiente isolado por processo; URI MongoDB e segredo de aplicação não aparecem nos argumentos de processos filhos. O processo web parte de allowlist de ambiente e recebe somente `NEXT_PUBLIC_API_URL`; API recebe as variáveis server-side. Saída e erro de cada processo são reunidos em `.local/logs/api.log` e `.local/logs/web.log` sem abrir janela.

## Verificação

```text
git diff --check
passed

node --test tooling/tests/workspace-structure.test.mjs
1 passed

PowerShell parser para os oito scripts operacionais
passed

node --test tooling/tests/local-stack-launcher.test.mjs
1 passed

O teste do launcher confirma allowlist pública, ambiente server-side isolado, ausência de segredos nos argumentos, caminhos de log e `CreateNoWindow`.

scripts/start-local-stack.ps1 sem variáveis obrigatórias
falha controlada antes de iniciar Docker ou processos filhos

python -m pytest apps/api/tests -q
95 passed, 5 skipped

npm run lint
passed with 3 pre-existing warnings

npm run typecheck
passed

npm run test
6 files / 18 tests passed

npm run test:contracts
2 passed

npm run build
passed

npm run test:e2e
1 passed, 6 skipped
```

`npm run format:check` continua falhando por 24 arquivos pré-existentes fora desta tarefa. Os arquivos formatáveis modificados nesta tarefa foram verificados com Prettier individualmente.

## Limitações locais

Os cinco skips Python requerem MongoDB real em replica set. Os seis E2E de autenticação, papéis e ciclo de vida requerem API ativa, dados E2E e `API_CONTRACT_BASE_URL`; o CI configura esses pré-requisitos. O E2E de redirecionamento do visitante permanece executável localmente.

## Relatório histórico: `task-6-report.md`

# Relatório da Tarefa 6 — fila transacional MongoDB

## Entrega

- Regras puras de rodízio global, elegibilidade, perda de vez e consumo de créditos em `domain/queue.py`.
- `QueueService` com as quatro interfaces exigidas: distribuição normal, recorrência, atribuição temporária e transferência permanente.
- Repositório MongoDB com idempotência por comando e transação única para cursor versionado, crédito, assignment, lead, owner, auditoria e outbox.
- Primeiro assignment efetivo define `companies.ownerId`; recorrência e temporário preservam o owner e não movem o cursor.
- FIFO impede que um lead normal novo ultrapasse lead normal já parado.
- FIFO compara todos os leads normais elegíveis, tanto `ready` quanto `parked`, e usa espera limitada para permitir que uma transação concorrente mais antiga confirme primeiro.
- Índice único parcial protege um assignment atual por lead; índice único e validator protegem saldo único e não negativo por vendedor.
- Rotas internas autenticadas por chave para distribuição/recorrência e rotas administrativas autenticadas para temporário/transferência.
- Atribuição temporária aceita somente recorrência parada por `owner_unavailable`, exige owner prévio e nunca reivindica propriedade para um lead normal.
- Créditos criados e consumidos geram auditoria e outbox próprios com saldo anterior/posterior e `actorId`; rotas administrativas propagam o usuário autenticado e comandos internos registram o ator `system`.
- Transferência permanente pela API exige `confirmed: true` antes de executar o comando.

## Critérios cobertos

- AC-01 a AC-06: rotação, atraso, perda de vez, bloqueio por um atraso, estacionamento e FIFO.
- AC-06 inclui teste de dois leads `ready`, estacionamento por bloqueio total, regularização de Sandra e liberação FIFO sem restaurar vez perdida.
- AC-07 a AC-08: recorrência sem movimento de cursor, crédito e consumo através de rotações.
- AC-08 inclui três recorrências, três consumos em rotações distintas, saldo final zero e seis eventos auditáveis de crédito.
- AC-09 a AC-11: owner bloqueado espera; temporário assume o lead, recebe crédito e o owner original permanece. O registro de venda será criado pela Tarefa 7, mas a fronteira exigida pelo AC-11 fica preservada por `assigneeId` temporário + `ownerId` original.
- Transferência permanente: altera somente owner futuro, preservando assignments históricos e auditando antes/depois.
- AC-29: teste concorrente em replica set valida assignments únicos, cursor equivalente ao sequencial e saldos não negativos.

## Evidências

Executado em `apps/api`:

```text
python -m pytest tests/unit/test_queue_rules.py tests/integration/test_queue_transactions.py tests/integration/test_queue_concurrency.py -q
18 passed, 1 skipped

python -m pytest -q
55 passed, 5 skipped in 12.64s
```

O skip adicional da Tarefa 6 é explícito: `test_queue_concurrency.py` requer um MongoDB real acessível como replica set. Os outros quatro skips preexistentes da suíte também dependem do MongoDB real. A cobertura transacional com adapter controlado roda sempre; a prova de conflito real fica ativa automaticamente quando `MONGODB_URI` aponta para um replica set.

Também executados com sucesso:

```text
python -m compileall -q src tests
git diff --check
```

## Relatório histórico: `task-7-report.md`

# Relatório da Tarefa 7 — calendário útil, SLA e operações

## Resultado

Foram implementados o calendário útil de São Paulo, o SLA inicial e periódico, feedbacks, notas administrativas, tentativas de WhatsApp e resultados comerciais transacionais no MongoDB.

As interfaces entregues são:

- `BusinessClock.add_business_hours(start, hours)`;
- `OperationsService.register_feedback(command)`;
- `OperationsService.register_attempt(command)`;
- `OperationsService.register_outcome(command)`.

## Regras cobertas

- AC-18: atribuição cria ciclo de 24 horas úteis e lembrete após 20 horas úteis; fins de semana e feriados nacionais/SP são ignorados integralmente.
- AC-19/AC-20: comentário exige 6 caracteres após `trim`; feedback exige contato explícito, fecha o ciclo anterior e abre o seguinte.
- AC-21: somente WhatsApp, uma tentativa por data útil, máximo de cinco datas distintas e desqualificação sempre por comando manual.
- AC-22: encerramento sem conversão mantém o lead qualificado e não o classifica como desqualificado.
- AC-23: Estado fora de SP não altera o lead automaticamente; a desqualificação exige decisão explícita.
- AC-24/AC-28: `won` fecha o SLA, cria evento/venda única, credita o responsável atual, marca a empresa cliente e preserva o proprietário.
- AC-30: nota administrativa é histórica, mas não fecha/renova ciclo nem altera o atraso do vendedor.

## Persistência e integração

Cada comando usa sessão e `with_transaction`, grava recibo idempotente em `command_results` e mantém lead, ciclo, histórico, auditoria, outbox, venda e empresa na mesma transação.

As mudanças adicionais ao conjunto mínimo de arquivos são necessárias para integrar as regras:

- `queue_repository.py`: cria o SLA inicial dentro da mesma transação da atribuição. Sem essa integração, um lead recém-atribuído não teria o prazo exigido pelo AC-18.
- `indexes.py`: protege uma tentativa por `leadId + businessDate` e um único ciclo aberto por lead, inclusive sob concorrência.
- `main.py`: injeta calendário, relógio, adapter transacional e registra as rotas.
- `test_queue_transactions.py`: comprova que a atribuição cria ciclo, lembrete e vencimento no mesmo commit.

## Evidência TDD e verificação

Os testes foram observados em RED antes da implementação: módulos ausentes, métodos `NotImplementedError`, rota 404 e índice inexistente. Depois, os ciclos GREEN focados foram executados.

Comando focado:

```text
python -m pytest tests/unit/test_business_time.py tests/unit/test_operations.py tests/integration/test_operations_transactions.py -q
33 passed in 4.58s (inclui regressões da fila e das operações)
```

Suíte completa da API:

```text
python -m pytest -q
77 passed, 5 skipped in 19.55s
```

Os cinco testes pulados já dependiam de um replica set MongoDB externo não configurado no ambiente local; a baseline anterior registrava os mesmos cinco skips.

`git diff --check` terminou sem erros; os avisos exibidos referem-se somente à conversão LF/CRLF configurada no worktree.

## Correção da revisão — rodada 1

- O outbox agora recebe `lead.feedback_due_soon` com `cycleId`, `scheduledFor`, `dueAt` e chave determinística `leadId:ciclo:feedback_due_soon`; o índice lógico e o recibo idempotente impedem duplicação no replay. Atribuições iniciais e renovações por feedback usam o mesmo evento agendável.
- `qualified_follow_up` e `qualified_closed_no_conversion` exigem `response_confirmed=True`, comprovando devolutiva real antes da qualificação. Resultados de desqualificação e ganho não exigem essa confirmação.
- `MongoOperationsRepository` aceita um `Clock` de sessão e obtém o instante dentro de `with_transaction`; o SLA e timestamps persistidos são recalculados com esse instante. A aplicação usa `MongoClock`, baseado no horário do servidor MongoDB, em vez de `SystemClock` de processo.
- `DuplicateKeyError` sem recibo idempotente é convertido em `OperationsStateError`, permitindo resposta HTTP 409 para colisões concorrentes.

## Relatório histórico: `task-8-report.md`

# Tarefa 8 — autorização, leituras e auditoria

## Entregas

- `PermissionService` exige usuário ativo/autenticado, restringe comandos administrativos a `admin` e gera filtros seller-scoped para leads, histórico, fila e saldo. O identificador vem exclusivamente de `CurrentUser`; não há parâmetro de `sellerId` nas leituras.
- `DashboardService.for_user` aplica o filtro antes de cada leitura e retorna páginas de leads, histórico, fila e saldo.
- Rotas autenticadas: `GET /api/dashboard`; administrativas: `GET /api/admin/users` e `GET /api/admin/audit`.
- Comandos críticos existentes de fila/operações continuam usando os serviços de domínio e gravando auditoria transacional com ator, ação, entidade, before/after, timestamp e correlation ID.
- Sessões antigas de usuários desativados já são rejeitadas por `AuthService.current_user`.

## Correções do round 1

- Leads de seller usam apenas `assigneeId`; histórico permanece em consulta própria.
- Dashboard e administração aceitam `page`/`limit`, calculam `skip` e validam limites.
- Toda leitura administrativa recebe `CurrentUser` e filtro explícito; filtro ausente é rejeitado.
- Auditoria operacional captura snapshots `before`/`after` de lead, ciclo e empresa dentro da transação.
- Fakes e testes cobrem paginação página 2 e isolamento seller A/B.
- Notas administrativas também registram snapshots reais do lead/ciclo (sem mutar SLA), e chamadas diretas do dashboard rejeitam `limit=0`.
- Rotas administrativas têm teste HTTP de `403` para seller; testes cobrem snapshots de tentativa, outcome, nota administrativa, histórico, fila e saldo.

## Testes

```text
pytest -q
85 passed, 5 skipped in 17.03s
```

Os 5 skips dependem de MongoDB em replica set local.

## Commit

Commit inicial: `743c068 feat(gerec-leads): aplica autorização e auditoria no backend`

Commit de correção: `fix(gerec-leads): fecha escopos, paginação e snapshots de auditoria`

Commit round 2: `fix(gerec-leads): completa auditoria e valida paginação`

## Relatório histórico: `task-9-report.md`

# Relatório da Tarefa 9 — Site Next.js via API Python

## Entregue

- Criado `apps/web/src/lib/api/client.ts` com `apiFetch<T>(path, init?)`, tratamento de erros HTTP, 401, 403 e validação.
- Criado contrato de tipos HTTP em `apps/web/src/lib/api/types.ts` e testes unitários do cliente.
- Autenticação web agora chama `/auth/login`, `/auth/me` e `/auth/logout` da API Python. O token HTTP-only da resposta de login é retransmitido como cookie `gerec_session` do domínio web e encaminhado nas chamadas server-side.
- Leituras das páginas dashboard, fila, histórico e usuários usam somente endpoints paginados da API Python.
- Dashboard, fila, histórico e usuários recebem `page` pela URL, validada como inteiro finito maior ou igual a 1, e expõem controles Anterior/Próxima a partir dos metadados da API.
- As ações de tentativa usam o endpoint Python com chave de idempotência. Arquivamento, simulação e gestão de usuários aparecem desabilitados e identificados como indisponíveis até a API expor seus comandos de domínio.
- O cookie web copia o `Max-Age` retornado no `Set-Cookie` da API; não replica a regra de expiração de 8 horas. Logout apaga o cookie local em `finally`, ignora falha remota e redireciona ao login.
- Removidos os adaptadores web que acessavam Supabase e variáveis de Supabase; `.env.example` expõe somente `NEXT_PUBLIC_API_URL`.

## Verificação

- `npm --workspace @wtg/web run test`: aprovado (inclui cliente HTTP, cookies, login/logout, sessão e paginação).
- `npm --workspace @wtg/web run typecheck`: aprovado.
- `npm --workspace @wtg/web run lint`: aprovado.
- `npm --workspace @wtg/web run build`: aprovado.

## Limitações conhecidas

- A API atual não expõe comandos para CRUD de usuários, arquivamento ou simulação; os controles exibem indisponibilidade explícita até que os endpoints de domínio sejam adicionados.
- A API de identidade não fornece nome completo. Enquanto o contrato não for ampliado, a interface exibe o e-mail como identificação do usuário.

## Configuração técnica: `package.json`

````json
{
  "name": "@wtg/gerenciador-de-leads",
  "version": "0.1.0",
  "private": true,
  "workspaces": [
    "apps/*"
  ],
  "engines": {
    "node": ">=24 <25"
  },
  "scripts": {
    "dev": "npm --workspace @wtg/web run dev",
    "build": "npm --workspace @wtg/web run build",
    "lint": "npm --workspace @wtg/web run lint",
    "typecheck": "npm --workspace @wtg/web run typecheck",
    "mongodb:start": "powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start-mongodb.ps1",
    "mongodb:stop": "powershell -NoProfile -ExecutionPolicy Bypass -File scripts/stop-mongodb.ps1",
    "mongodb:bootstrap": "powershell -NoProfile -ExecutionPolicy Bypass -File scripts/mongodb-bootstrap.ps1",
    "api:start": "powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start-api.ps1",
    "web:start": "powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start-web.ps1",
    "worker:start": "powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start-worker.ps1",
    "start:local": "powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start-local-stack.ps1",
    "test:ci-contract": "node --test tooling/tests/ci-contract.test.mjs",
    "test:structure": "node --test tooling/tests/workspace-structure.test.mjs",
    "test:launcher": "node --test tooling/tests/local-stack-launcher.test.mjs",
    "test:e2e": "node tooling/playwright/run-e2e.mjs",
    "test:contracts": "node --test tests/contracts/*.test.mjs",
    "test:e2e:install": "playwright install chromium",
    "test:e2e:install:ci": "playwright install --with-deps chromium",
    "test:playwright-tooling": "node --test tooling/playwright/*.test.mjs",
    "test": "npm --workspace @wtg/web run test",
    "format": "prettier --write .",
    "format:check": "prettier --check .",
    "check": "npm run format:check && npm run lint && npm run typecheck && npm run test && npm run test:structure && npm run test:launcher && npm run test:playwright-tooling && npm run test:ci-contract && npm run build"
  },
  "devDependencies": {
    "@playwright/test": "^1.62.1",
    "prettier": "3.9.6",
    "yaml": "^2.8.1"
  }
}
````

## Configuração técnica: `apps/api/pyproject.toml`

````toml
[build-system]
requires = ["setuptools>=75"]
build-backend = "setuptools.build_meta"

[project]
name = "gerec-api"
version = "0.1.0"
description = "Backend Python do Gerenciador de Leads WTG"
requires-python = ">=3.12,<3.14"
dependencies = [
  "argon2-cffi>=23.1,<26",
  "fastapi>=0.115,<1",
  "google-auth>=2.35,<3",
  "openpyxl>=3.1,<4",
  "pydantic-settings>=2.6,<3",
  "pymongo>=4.10,<5",
  "requests>=2.32,<3",
  "uvicorn[standard]>=0.30,<1",
]

[project.optional-dependencies]
dev = [
  "httpx>=0.28,<1",
  "pytest>=8.3,<9",
]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]

[tool.setuptools.packages.find]
where = ["src"]
namespaces = true
````

## Configuração técnica: `apps/api/Dockerfile`

````text
FROM python:3.12-slim

WORKDIR /app

COPY apps/api/pyproject.toml ./apps/api/pyproject.toml
COPY apps/api/src ./apps/api/src

RUN pip install --no-cache-dir ./apps/api

EXPOSE 8000

CMD ["sh", "-c", "uvicorn gerec_api.main:create_app --factory --host 0.0.0.0 --port ${PORT:-8000}"]
````

## Configuração técnica: `apps/web/package.json`

````json
{
  "name": "@wtg/web",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "eslint",
    "typecheck": "tsc --noEmit",
    "test": "vitest run --passWithNoTests"
  },
  "dependencies": {
    "next": "16.3.3",
    "react": "19.2.8",
    "react-dom": "19.2.8"
  },
  "devDependencies": {
    "@tailwindcss/postcss": "^4",
    "@testing-library/react": "^16.3.3",
    "@testing-library/user-event": "^14.6.6",
    "@types/node": "^20",
    "@types/react": "^19",
    "@types/react-dom": "^19",
    "eslint": "^9",
    "eslint-config-next": "16.3.3",
    "jsdom": "^30.0.1",
    "tailwindcss": "^4",
    "typescript": "^5",
    "vitest": "4.1.11"
  }
}
````

## Configuração técnica: `railway.json`

````json
{
  "$schema": "https://railway.com/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "apps/api/Dockerfile"
  },
  "deploy": {
    "healthcheckPath": "/health",
    "healthcheckTimeout": 120,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
````

## Configuração técnica: `vercel.json`

````json
{
  "framework": "nextjs",
  "installCommand": "npm ci",
  "buildCommand": "npm run build",
  "devCommand": "npm run dev"
}
````

## Configuração técnica: `infra/railway/README.md`

# Serviços Railway

`railway.json` contém apenas o build compartilhado. Como cada serviço Railway possui seu próprio comando de início, configure os três processos abaixo no painel do ambiente correspondente.

| Serviço | Tipo | Comando | Agenda |
| --- | --- | --- | --- |
| `api` | persistente/web | `uvicorn gerec_api.main:create_app --factory --host 0.0.0.0 --port ${PORT:-8000}` via `apps/api/Dockerfile` | — |
| `outbox-worker` | persistente/worker | `python -m gerec_api.automation.outbox_worker` | — |
| `google-sheets-sync` | cron | `python -m gerec_api.automation.scheduler` | `*/5 * * * *` |

Defina `MONGODB_URI`, `MONGODB_DATABASE` e `APP_SECRET` em cada serviço no painel Railway. Para o cron, defina `GOOGLE_SHEETS_SPREADSHEET_ID`, `GOOGLE_SHEETS_RANGE` e `GOOGLE_SERVICE_ACCOUNT_JSON`; para o worker, `OUTBOX_DELIVERY_WEBHOOK_URL` e, se necessário, `OUTBOX_DELIVERY_TOKEN`. Todos os valores ficam exclusivamente nas variáveis Railway; não registre valores no repositório. O cron deve finalizar após cada execução e retornar erro quando a sincronização falhar.

Os jobs usam a mesma camada de domínio da API. O sincronizador só finaliza o snapshot após importar todas as linhas e mantém lease com geração/token; uma geração antiga não arquiva um snapshot novo. O worker reivindica cada evento com claim token, aplica fencing no ack/retry e encaminha a chave de idempotência ao provedor.

## Snapshot de código: `apps/api/src/gerec_api/__init__.py`

````python
"""Backend do Gerenciador de Leads WTG."""
````

## Snapshot de código: `apps/api/src/gerec_api/auth/__init__.py`

````python
"""Authentication and current-user boundaries for the API."""
````

## Snapshot de código: `apps/api/src/gerec_api/auth/dependencies.py`

````python
"""FastAPI dependencies for resolving the authenticated user."""

from fastapi import HTTPException, Request, status

from gerec_api.auth.sessions import AuthService, CurrentUser, InvalidSessionError


SESSION_COOKIE_NAME = "gerec_session"


def get_auth_service(request: Request) -> AuthService:
    """Return the request application's configured authentication service."""
    service = getattr(request.app.state, "auth_service", None)
    if not isinstance(service, AuthService):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        )
    return service


def get_current_user(request: Request) -> CurrentUser:
    """Resolve the current active user from the HTTP-only opaque-session cookie."""
    raw_token = request.cookies.get(SESSION_COOKIE_NAME)
    try:
        return get_auth_service(request).current_user(raw_token or "")
    except InvalidSessionError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        ) from error
````

## Snapshot de código: `apps/api/src/gerec_api/auth/passwords.py`

````python
"""Password hashing backed by Argon2id."""

from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHashError, VerificationError


_PASSWORD_HASHER = PasswordHasher(type=Type.ID)
_DUMMY_PASSWORD_DIGEST = _PASSWORD_HASHER.hash("invalid-password-used-to-equalize-login-work")


def hash_password(password: str) -> str:
    """Return an Argon2id digest; callers must persist only this value."""
    return _PASSWORD_HASHER.hash(password)


def verify_password(password: str, digest: str) -> bool:
    """Return whether a candidate password matches a valid Argon2 digest."""
    try:
        return _PASSWORD_HASHER.verify(digest, password)
    except (InvalidHashError, VerificationError):
        return False


def verify_unknown_password(password: str) -> None:
    """Consume equivalent Argon2 work when an account cannot authenticate."""
    verify_password(password, _DUMMY_PASSWORD_DIGEST)
````

## Snapshot de código: `apps/api/src/gerec_api/auth/permissions.py`

````python
"""Centralized authorization and role-specific operational read models."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Mapping

from bson import ObjectId

from gerec_api.auth.sessions import CurrentUser
from gerec_api.domain.queue import QueueSnapshot
from gerec_api.infrastructure.mongo.collections import MongoCollections
from gerec_api.infrastructure.mongo.queue_repository import QueueRepository
from gerec_api.infrastructure.mongo.serialization import serialize_bson


NOT_INFORMED = "Não informado"


class PermissionDenied(PermissionError):
    """Raised when a command or query is outside the current user's scope."""


class PermissionService:
    """Pure policy boundary; callers must provide the authenticated user."""

    @staticmethod
    def require_current_user(user: CurrentUser | None) -> CurrentUser:
        if not isinstance(user, CurrentUser) or not user.id or user.role not in {"admin", "seller"}:
            raise PermissionDenied("authenticated user is required")
        return user

    @classmethod
    def require_admin(cls, user: CurrentUser | None) -> None:
        current = cls.require_current_user(user)
        if current.role != "admin":
            raise PermissionDenied("administrator role is required")

    @classmethod
    def scope_query(cls, user: CurrentUser | None, resource: str) -> dict[str, Any]:
        """Return a server-side Mongo filter; seller identity only comes from session."""
        current = cls.require_current_user(user)
        if resource not in {
            "leads", "history", "queue", "skip_balance", "companies", "campaigns",
            "users", "audit", "treatments",
        }:
            raise ValueError(f"unknown protected resource: {resource}")
        if current.role == "admin":
            return {}
        ids = _identity_values(current.id)
        if resource == "leads":
            return {"assigneeId": {"$in": ids}}
        if resource in {"history", "treatments"}:
            return {"sellerId": {"$in": ids}}
        if resource in {"queue", "skip_balance"}:
            return {"sellerId": {"$in": ids}}
        raise PermissionDenied(f"seller cannot read {resource}")

    @classmethod
    def dashboard_lead_scope(
        cls, user: CurrentUser | None, *, assignee_id: str | None = None
    ) -> dict[str, Any]:
        """Build the dashboard lead scope without accepting a seller's override."""
        current = cls.require_current_user(user)
        if current.role != "admin":
            return cls.scope_query(current, "leads")
        if assignee_id is None:
            return {}
        requested_id = assignee_id.strip()
        if not requested_id:
            raise ValueError("assigneeId must not be empty")
        return {"assigneeId": {"$in": _identity_values(requested_id)}}


class DashboardService:
    """Read-model boundary with intentionally different contracts for each role.

    The service contains no command logic. Queue availability is delegated to the
    Task 5 repository snapshot so the read model cannot invent an eligibility rule.
    """

    def __init__(
        self,
        database: Any,
        *,
        page_size: int = 50,
        queue_snapshot: Any | None = None,
    ) -> None:
        self._database = database
        self._page_size = max(1, min(page_size, 200))
        self._queue_snapshot = queue_snapshot or QueueRepository(database).snapshot

    def for_user(
        self,
        user: CurrentUser | None,
        *,
        page: int = 1,
        limit: int | None = None,
        assignee_id: str | None = None,
        sort: str | None = None,
    ) -> dict[str, Any]:
        current = PermissionService.require_current_user(user)
        return (
            self.for_admin(
                current,
                page=page,
                limit=limit,
                assignee_id=assignee_id,
                sort=sort,
            )
            if current.role == "admin"
            else self.for_seller(
                current,
                page=page,
                limit=limit,
                assignee_id=assignee_id,
                sort=sort,
            )
        )

    def for_admin(
        self,
        user: CurrentUser | None,
        *,
        page: int = 1,
        limit: int | None = None,
        assignee_id: str | None = None,
        sort: str | None = None,
    ) -> dict[str, Any]:
        PermissionService.require_admin(user)
        current = PermissionService.require_current_user(user)
        page, page_size = self._pagination(page, limit)
        return {
            "user": _public_user(current),
            "leads": self._lead_page(
                PermissionService.dashboard_lead_scope(current, assignee_id=assignee_id),
                page,
                page_size,
                sort=sort,
            ),
            "history": self._treatment_page({}, page, page_size, include_lead_name=True),
            "queue": self._admin_queue(),
        }

    def for_seller(
        self,
        user: CurrentUser | None,
        *,
        page: int = 1,
        limit: int | None = None,
        assignee_id: str | None = None,
        sort: str | None = None,
    ) -> dict[str, Any]:
        current = PermissionService.require_current_user(user)
        if current.role != "seller":
            raise PermissionDenied("seller role is required")
        page, page_size = self._pagination(page, limit)
        return {
            "user": _public_user(current),
            "leads": self._lead_page(
                PermissionService.dashboard_lead_scope(current, assignee_id=assignee_id),
                page,
                page_size,
                sort=sort,
            ),
            "history": self._treatment_page(
                self._seller_history_query(current),
                page,
                page_size,
                include_lead_name=True,
            ),
            "queue": self._seller_queue(current),
        }

    def _seller_history_query(self, user: CurrentUser) -> dict[str, Any]:
        """Limit seller history to leads they currently own after transfers."""
        lead_ids = [
            lead.get("_id")
            for lead in self._database[MongoCollections.LEADS].find(
                PermissionService.scope_query(user, "leads")
            )
            if lead.get("_id") is not None
        ]
        return {
            "sellerId": {"$in": _identity_values(user.id)},
            "leadId": {"$in": lead_ids},
        }

    def queue_for_user(self, user: CurrentUser | None) -> dict[str, Any]:
        current = PermissionService.require_current_user(user)
        return self._admin_queue() if current.role == "admin" else self._seller_queue(current)

    def lead_treatments_for_user(
        self,
        lead_id: str,
        user: CurrentUser | None,
        *,
        page: int = 1,
        limit: int | None = None,
    ) -> dict[str, Any]:
        current = PermissionService.require_current_user(user)
        page, page_size = self._pagination(page, limit)
        lead = self._find_by_id(MongoCollections.LEADS, lead_id)
        if lead is None:
            raise PermissionDenied("lead is outside current user scope")

        query: dict[str, Any] = {"leadId": {"$in": _identity_values(lead_id)}}
        if current.role == "seller":
            seller_query = PermissionService.scope_query(current, "treatments")
            current_owner = lead.get("assigneeId") in _identity_values(current.id)
            if not current_owner:
                raise PermissionDenied("lead is outside current user scope")
            query.update(seller_query)
        return self._treatment_page(query, page, page_size, include_lead_name=False)

    def _pagination(self, page: int, limit: int | None) -> tuple[int, int]:
        return _page_number(page), _page_limit(self._page_size if limit is None else limit)

    def lead_distribution(
        self,
        user: CurrentUser | None,
        *,
        from_at: datetime,
        to_at: datetime,
    ) -> dict[str, Any]:
        """Aggregate current lead ownership by situation in an assignment interval."""
        PermissionService.require_admin(user)
        from_utc = _as_utc(from_at, name="fromAt")
        to_utc = _as_utc(to_at, name="toAt")
        if from_utc >= to_utc:
            raise ValueError("fromAt must be earlier than toAt")
        leads = list(
            self._database[MongoCollections.LEADS].find(
                {"assignedAt": {"$gte": from_utc, "$lt": to_utc}}
            )
        )
        by_situation: dict[str, int] = {}
        by_seller: dict[str, dict[str, Any]] = {}
        seller_ids: list[Any] = []
        for lead in leads:
            situation = _commercial_status(lead)
            by_situation[situation] = by_situation.get(situation, 0) + 1
            assignee_id = lead.get("assigneeId")
            if assignee_id is None:
                continue
            seller_id = str(assignee_id)
            by_seller[seller_id] = {
                "sellerId": seller_id,
                "sellerName": NOT_INFORMED,
                "count": by_seller.get(seller_id, {}).get("count", 0) + 1,
            }
            seller_ids.extend(_identity_values(assignee_id))

        users = self._database[MongoCollections.USERS].find(
            {"_id": {"$in": list(dict.fromkeys(seller_ids))}}
        ) if seller_ids else []
        names = {
            str(candidate): _name_or_fallback(document)
            for document in users
            for candidate in _identity_values(document.get("_id"))
        }
        for seller in by_seller.values():
            seller["sellerName"] = names.get(seller["sellerId"], NOT_INFORMED)

        return {
            "period": {"from": from_utc.isoformat(), "to": to_utc.isoformat()},
            "bySituation": [
                {"commercialStatus": situation, "count": count}
                for situation, count in sorted(by_situation.items())
            ],
            "bySeller": sorted(
                by_seller.values(), key=lambda item: (item["sellerName"], item["sellerId"])
            ),
        }

    def _lead_page(
        self,
        query: Mapping[str, Any],
        page: int,
        page_size: int,
        *,
        sort: str | None = None,
    ) -> dict[str, Any]:
        collection = self._database[MongoCollections.LEADS]
        cursor = collection.find(dict(query))
        if sort == "situation":
            leads = list(cursor)
            leads.sort(key=lambda lead: str(lead.get("_id") or ""))
            leads.sort(key=_lead_created_at_sort_value, reverse=True)
            leads.sort(key=lambda lead: _situation_sort_rank(_commercial_status(lead)))
            leads = leads[(page - 1) * page_size : page * page_size]
        else:
            if hasattr(cursor, "sort"):
                cursor = cursor.sort(_lead_sort(sort))
            if hasattr(cursor, "skip"):
                cursor = cursor.skip((page - 1) * page_size)
            if hasattr(cursor, "limit"):
                cursor = cursor.limit(page_size)
            leads = list(cursor)
        references = self._lead_references(leads)
        items = [self._lead_projection(lead, references=references) for lead in leads]
        total = collection.count_documents(dict(query)) if hasattr(collection, "count_documents") else len(items)
        return {"items": items, "page": page, "pageSize": page_size, "total": total}

    def _lead_references(self, leads: list[Mapping[str, Any]]) -> dict[str, dict[str, Mapping[str, Any]]]:
        """Load all lead enrichment references with one query per collection."""
        ids_by_collection: dict[str, list[Any]] = {
            MongoCollections.USERS: [],
            MongoCollections.COMPANIES: [],
            MongoCollections.CAMPAIGNS: [],
        }
        for lead in leads:
            for collection_name, field in (
                (MongoCollections.USERS, "assigneeId"),
                (MongoCollections.COMPANIES, "companyId"),
                (MongoCollections.CAMPAIGNS, "campaignId"),
            ):
                value = lead.get(field)
                if value is not None:
                    ids_by_collection[collection_name].extend(_identity_values(value))

        references: dict[str, dict[str, Mapping[str, Any]]] = {}
        for collection_name, values in ids_by_collection.items():
            unique_values = list(dict.fromkeys(values))
            if not unique_values:
                references[collection_name] = {}
                continue
            collection = self._database[collection_name]
            documents = collection.find({"_id": {"$in": unique_values}})
            references[collection_name] = {
                str(candidate): document
                for document in documents
                for candidate in _identity_values(document.get("_id"))
            }
        return references

    def _treatment_page(
        self,
        query: Mapping[str, Any],
        page: int,
        page_size: int,
        *,
        include_lead_name: bool,
    ) -> dict[str, Any]:
        collection = self._database[MongoCollections.LEAD_TREATMENTS]
        cursor = collection.find(dict(query))
        if hasattr(cursor, "sort"):
            cursor = cursor.sort("createdAt", -1)
        if hasattr(cursor, "skip"):
            cursor = cursor.skip((page - 1) * page_size)
        if hasattr(cursor, "limit"):
            cursor = cursor.limit(page_size)
        treatments = list(cursor)
        references = self._treatment_references(treatments)
        items = [
            self._treatment_projection(
                treatment,
                include_lead_name=include_lead_name,
                references=references,
            )
            for treatment in treatments
        ]
        total = collection.count_documents(dict(query)) if hasattr(collection, "count_documents") else len(items)
        return {"items": items, "page": page, "pageSize": page_size, "total": total}

    def _treatment_references(self, treatments: list[Mapping[str, Any]]) -> dict[str, dict[str, Mapping[str, Any]]]:
        ids_by_collection: dict[str, list[Any]] = {
            MongoCollections.USERS: [],
            MongoCollections.LEADS: [],
        }
        for treatment in treatments:
            ids_by_collection[MongoCollections.USERS].extend(_identity_values(treatment.get("sellerId")))
            ids_by_collection[MongoCollections.LEADS].extend(_identity_values(treatment.get("leadId")))

        references: dict[str, dict[str, Mapping[str, Any]]] = {}
        for collection_name, values in ids_by_collection.items():
            unique_values = list(dict.fromkeys(value for value in values if value is not None))
            if not unique_values:
                references[collection_name] = {}
                continue
            documents = self._database[collection_name].find({"_id": {"$in": unique_values}})
            references[collection_name] = {
                str(candidate): document
                for document in documents
                for candidate in _identity_values(document.get("_id"))
            }
        return references

    def _page(
        self,
        collection_name: str,
        query: Mapping[str, Any],
        page: int,
        page_size: int,
        projection: Any,
    ) -> dict[str, Any]:
        collection = self._database[collection_name]
        cursor = collection.find(dict(query))
        if hasattr(cursor, "sort"):
            cursor = cursor.sort("createdAt", -1)
        if hasattr(cursor, "skip"):
            cursor = cursor.skip((page - 1) * page_size)
        if hasattr(cursor, "limit"):
            cursor = cursor.limit(page_size)
        items = [projection(item) for item in cursor]
        total = collection.count_documents(dict(query)) if hasattr(collection, "count_documents") else len(items)
        return {"items": items, "page": page, "pageSize": page_size, "total": total}

    def _lead_projection(
        self,
        lead: Mapping[str, Any],
        *,
        references: dict[str, dict[str, Mapping[str, Any]]] | None = None,
    ) -> dict[str, Any]:
        if references is None:
            references = self._lead_references([lead])
        company = references[MongoCollections.COMPANIES].get(str(lead.get("companyId")))
        campaign = references[MongoCollections.CAMPAIGNS].get(str(lead.get("campaignId")))
        seller = references[MongoCollections.USERS].get(str(lead.get("assigneeId")))
        return _serialize_read_model(
            {
                "id": str(lead["_id"]),
                "contactName": _text_or_fallback(lead.get("contactName")),
                "sellerName": _name_or_fallback(seller),
                "companyName": _company_name(company),
                "campaignName": _campaign_name(campaign),
                "phoneDisplay": _phone_without_country_code(self._lead_phone_value(lead)),
                "email": _text_or_fallback(lead.get("email") or lead.get("emailNormalized")),
                "commercialStatus": _commercial_status(lead),
                "isDisqualified": bool(lead.get("isDisqualified", False)),
                "commentCount": int(lead.get("commentCount", 0)),
                "assignedAt": lead.get("assignedAt"),
                "lastUpdatedAt": lead.get("lastCommentAt")
                or lead.get("updatedAt")
                or lead.get("assignedAt"),
            }
        )

    def _treatment_projection(
        self,
        treatment: Mapping[str, Any],
        *,
        include_lead_name: bool,
        references: dict[str, dict[str, Mapping[str, Any]]] | None = None,
    ) -> dict[str, Any]:
        references = references or self._treatment_references([treatment])
        seller = references[MongoCollections.USERS].get(str(treatment.get("sellerId")))
        lead = references[MongoCollections.LEADS].get(str(treatment.get("leadId")))
        result: dict[str, Any] = {
            "leadId": str(treatment.get("leadId")),
            "sellerName": _name_or_fallback(seller),
            "comment": _text_or_fallback(treatment.get("comment")),
            "commercialStatus": _commercial_status(treatment),
            "isDisqualified": bool(treatment.get("isDisqualified", False)),
            "assignedAt": (lead or {}).get("assignedAt"),
            "createdAt": treatment.get("createdAt"),
            "lastUpdatedAt": (
                (lead or {}).get("lastCommentAt")
                or (lead or {}).get("updatedAt")
                or (lead or {}).get("assignedAt")
            ),
        }
        if include_lead_name:
            result["leadName"] = _text_or_fallback((lead or {}).get("contactName"))
        return _serialize_read_model(result)

    def _admin_queue(self) -> dict[str, Any]:
        snapshot = self._snapshot()
        entries = []
        for position, entry in enumerate(snapshot.entries, start=1):
            seller = self._find_by_id(MongoCollections.USERS, entry.seller_id)
            entries.append(
                {
                    "sellerName": _name_or_fallback(seller),
                    "position": position,
                    "availability": entry.availability.status,
                    "reason": entry.availability.reason,
                    "skipBalance": entry.skip_balance,
                }
            )
        return {
            "items": entries,
            "total": len(entries),
            "nextSellerName": entries[0]["sellerName"] if entries else NOT_INFORMED,
            "cursorSellerName": _name_or_fallback(
                self._find_by_id(MongoCollections.USERS, snapshot.cursor_seller_id)
            ),
        }

    def _seller_queue(self, user: CurrentUser) -> dict[str, Any]:
        for position, entry in enumerate(self._snapshot().entries, start=1):
            if entry.seller_id in _identity_values(user.id):
                return {
                    "position": position,
                    "availability": entry.availability.status,
                    "skipBalance": entry.skip_balance,
                }
        # A seller can remain authenticated while an administrative migration or
        # deactivation has removed it from the queue. This is its own state, not
        # a reason to disclose the global queue or fail the complete dashboard.
        return {"position": None, "availability": "paused", "skipBalance": 0}

    def _snapshot(self) -> QueueSnapshot:
        return self._queue_snapshot()

    def _find_by_id(self, collection_name: str, value: Any) -> Mapping[str, Any] | None:
        if value is None:
            return None
        collection = self._database[collection_name]
        for candidate in _identity_values(value):
            item = collection.find_one({"_id": candidate})
            if item is not None:
                return item
        return None

    def _lead_phone_value(self, lead: Mapping[str, Any]) -> Any:
        """Read the canonical phone, tolerating source records from older imports.

        Current imports persist ``phoneNormalized`` on the lead.  Some already
        persisted snapshots retain the original value only in ``source_records``;
        reading those fields keeps the read model useful without changing the
        source contract or mutating data during a GET.
        """
        value = _phone_from_mapping(lead)
        if value is not None:
            return value

        source_records = self._database[MongoCollections.SOURCE_RECORDS]
        source = _find_source_record(source_records, lead)
        if source is None:
            return None
        return _phone_from_mapping(source)


def _identity_values(value: Any) -> list[Any]:
    values: list[Any] = [value]
    if isinstance(value, str) and ObjectId.is_valid(value):
        values.append(ObjectId(value))
    elif isinstance(value, ObjectId):
        values.append(str(value))
    return values


_PHONE_FIELDS = ("phoneNormalized", "phoneNumber", "phone_number", "phone", "telefone")
_PHONE_CONTAINERS = (
    "sourceProjection",
    "sourcePayload",
    "sellerProjection",
    "payload",
    "projection",
    "source_projection",
    "source_payload",
    "row",
    "data",
    "fields",
)
_SOURCE_LINK_FIELDS = ("leadId", "lead_id", "sourceLeadId", "source_lead_id")


def _phone_from_mapping(value: Any, *, depth: int = 0) -> Any:
    """Extract only known phone aliases from known persisted containers."""
    if not isinstance(value, Mapping) or depth > 4:
        return None
    for field in _PHONE_FIELDS:
        candidate = value.get(field)
        if candidate is not None and str(candidate).strip():
            return candidate
    for field in _PHONE_CONTAINERS:
        candidate = value.get(field)
        found = _phone_from_mapping(candidate, depth=depth + 1)
        if found is not None:
            return found
    return None


def _find_source_record(collection: Any, lead: Mapping[str, Any]) -> Mapping[str, Any] | None:
    """Resolve source records across current and legacy link field names."""
    lead_values: list[Any] = []
    for field in ("_id", "id", "sourceLeadId", "source_lead_id"):
        candidate = lead.get(field)
        if candidate is not None:
            lead_values.extend(_identity_values(candidate))
    seen: set[str] = set()
    for link_field in _SOURCE_LINK_FIELDS:
        for candidate in lead_values:
            marker = f"{link_field}:{candidate!r}"
            if marker in seen:
                continue
            seen.add(marker)
            source = collection.find_one({link_field: candidate})
            if source is not None:
                return source
    return None


def _public_user(user: CurrentUser) -> dict[str, str]:
    return {"id": user.id, "email": user.email, "role": user.role}


def _text_or_fallback(value: Any) -> str:
    text = str(value).strip() if value is not None else ""
    return text or NOT_INFORMED


def _name_or_fallback(document: Mapping[str, Any] | None) -> str:
    value = (document or {}).get("fullName") or (document or {}).get("name") or (document or {}).get("email")
    return _text_or_fallback(value)


def _company_name(document: Mapping[str, Any] | None) -> str:
    return _text_or_fallback((document or {}).get("name") or (document or {}).get("legalName"))


def _campaign_name(document: Mapping[str, Any] | None) -> str:
    return _text_or_fallback(
        (document or {}).get("displayName")
        or (document or {}).get("sourceName")
        or (document or {}).get("name")
    )


def _phone_without_country_code(value: Any) -> str:
    digits = "".join(character for character in str(value or "") if character.isdigit())
    if digits.startswith("55") and len(digits) in {12, 13}:
        digits = digits[2:]
    return digits or NOT_INFORMED


def _commercial_status(document: Mapping[str, Any]) -> str:
    direct = document.get("commercialStatus")
    if direct in {"undefined", "potential", "negotiation", "won"}:
        return str(direct)
    if document.get("conversionStatus") == "won":
        return "won"
    if document.get("qualificationStatus") in {"qualified", "in_negotiation", "negotiation"}:
        return "negotiation"
    return "undefined"


def _lead_sort(sort: str | None) -> list[tuple[str, int]]:
    if sort is None:
        return [("createdAt", -1)]
    if sort != "situation":
        raise ValueError("sort must be situation")
    return [("createdAt", -1), ("_id", 1)]


_SITUATION_SORT_ORDER = {"won": 0, "undefined": 1, "negotiation": 2, "potential": 3}


def _situation_sort_rank(status: str) -> int:
    return _SITUATION_SORT_ORDER[status]


def _lead_created_at_sort_value(lead: Mapping[str, Any]) -> float:
    value = lead.get("createdAt")
    if isinstance(value, datetime):
        return value.replace(tzinfo=UTC).timestamp() if value.tzinfo is None else value.timestamp()
    return float("-inf")


def _as_utc(value: datetime, *, name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must include a timezone")
    return value.astimezone(UTC)


def _page_number(value: int) -> int:
    if value < 1:
        raise ValueError("page must be at least 1")
    return value


def _page_limit(value: int) -> int:
    if value < 1 or value > 200:
        raise ValueError("limit must be between 1 and 200")
    return value


def _serialize_read_model(value: Mapping[str, Any]) -> dict[str, Any]:
    return serialize_bson(
        {
            key: item.isoformat() if isinstance(item, datetime) else item
            for key, item in value.items()
        }
    )
````

## Snapshot de código: `apps/api/src/gerec_api/auth/sessions.py`

````python
"""Opaque MongoDB-backed authentication sessions."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import token_urlsafe
from typing import Any

from gerec_api.auth.passwords import verify_password, verify_unknown_password
from gerec_api.infrastructure.mongo.collections import MongoCollections


SESSION_DURATION = timedelta(hours=8)


class InvalidCredentialsError(ValueError):
    """Login failed without revealing whether the account exists."""


class InvalidSessionError(ValueError):
    """A session token is missing, expired, revoked, or belongs to an inactive user."""


@dataclass(frozen=True)
class CurrentUser:
    """The public identity resolved from an active persisted session."""

    id: str
    email: str
    role: str


@dataclass(frozen=True)
class SessionResult:
    """Server-side login result; the raw token is for the HTTP-only cookie only."""

    raw_token: str
    expires_at: datetime
    user: CurrentUser


class AuthService:
    """Owns password verification and the opaque-session lifecycle."""

    def __init__(
        self,
        database: Any,
        *,
        now: Callable[[], datetime] | None = None,
        session_duration: timedelta = SESSION_DURATION,
    ) -> None:
        self._users = database[MongoCollections.USERS]
        self._sessions = database[MongoCollections.SESSIONS]
        self._now = now or _utcnow
        self._session_duration = session_duration

    def login(self, email: str, password: str) -> SessionResult:
        """Authenticate an active user and persist only the token SHA-256 digest."""
        user = self._users.find_one(
            {"emailNormalized": _normalize_email(email), "active": True}
        )
        digest = user.get("passwordHash") if user is not None else None
        if not isinstance(digest, str):
            verify_unknown_password(password)
            raise InvalidCredentialsError("Invalid credentials")
        if not verify_password(password, digest):
            raise InvalidCredentialsError("Invalid credentials")

        now = _as_utc(self._now())
        raw_token = token_urlsafe(32)
        expires_at = now + self._session_duration
        self._sessions.insert_one(
            {
                "tokenHash": _token_hash(raw_token),
                "userId": user["_id"],
                "expiresAt": expires_at,
                "revokedAt": None,
                "createdAt": now,
                "updatedAt": now,
            }
        )
        return SessionResult(
            raw_token=raw_token,
            expires_at=expires_at,
            user=_current_user_from_document(user),
        )

    def logout(self, raw_token: str) -> None:
        """Idempotently revoke the server-side session identified by an opaque token."""
        if not raw_token:
            return
        now = _as_utc(self._now())
        self._sessions.update_one(
            {"tokenHash": _token_hash(raw_token), "revokedAt": None},
            {"$set": {"revokedAt": now, "updatedAt": now}},
        )

    def revoke_all_for_user(self, user_id: Any) -> None:
        """Invalidate every currently active session for one account."""
        revoke_sessions_for_user(self._sessions, user_id, now=_as_utc(self._now()))

    def current_user(self, raw_token: str) -> CurrentUser:
        """Resolve a current user only from an unrevoked, unexpired opaque session."""
        if not raw_token:
            raise InvalidSessionError("Invalid session")
        now = _as_utc(self._now())
        token_hash = _token_hash(raw_token)
        session = self._sessions.find_one(
            {
                "tokenHash": token_hash,
                "revokedAt": None,
                "expiresAt": {"$gt": now},
            }
        )
        if session is None:
            raise InvalidSessionError("Invalid session")

        user = self._users.find_one({"_id": session["userId"], "active": True})
        if user is None:
            self._sessions.update_one(
                {"tokenHash": token_hash, "revokedAt": None},
                {"$set": {"revokedAt": now, "updatedAt": now}},
            )
            raise InvalidSessionError("Invalid session")
        return _current_user_from_document(user)


def _normalize_email(email: str) -> str:
    return email.strip().casefold()


def _token_hash(raw_token: str) -> str:
    return sha256(raw_token.encode("utf-8")).hexdigest()


def revoke_sessions_for_user(
    sessions: Any,
    user_id: Any,
    *,
    now: datetime,
    session: Any | None = None,
) -> None:
    """Revoke all active sessions, optionally in the caller's Mongo transaction."""
    options = {} if session is None else {"session": session}
    sessions.update_many(
        {"userId": user_id, "revokedAt": None},
        {"$set": {"revokedAt": now, "updatedAt": now}},
        **options,
    )


def _current_user_from_document(user: Mapping[str, Any]) -> CurrentUser:
    return CurrentUser(
        id=str(user["_id"]),
        email=str(user["emailNormalized"]),
        role=str(user.get("role", "seller")),
    )


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
````

## Snapshot de código: `apps/api/src/gerec_api/automation/__init__.py`

````python
"""Server-side automation adapters."""
````

## Snapshot de código: `apps/api/src/gerec_api/automation/google_sheets_adapter.py`

````python
"""Read the definitive Google Sheets source without exposing credentials to clients."""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Iterable
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen

from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2 import service_account

from gerec_api.automation.workbook_adapter import EXPECTED_HEADERS, InvalidWorkbookError
from gerec_api.domain.normalization import NormalizedSourceRow, normalize_source_row


class GoogleSheetsAdapter:
    """Read one complete `Leads!A:Q` snapshot through the Sheets Values API."""

    def __init__(
        self,
        spreadsheet_id: str,
        range_name: str,
        access_token: str,
        *,
        skip_source_ids: set[str] | None = None,
        fetch: Callable[[str], dict[str, Any]] | None = None,
    ) -> None:
        if not spreadsheet_id or not range_name or not access_token:
            raise ValueError("Google Sheets spreadsheet, range and access token are required")
        self._spreadsheet_id = spreadsheet_id
        self._range_name = range_name
        self._access_token = access_token
        self._fetch = fetch or self._fetch_json
        self._skip_source_ids = skip_source_ids or set()

    @classmethod
    def from_env(cls) -> "GoogleSheetsAdapter":
        service_account_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
        access_token = os.environ.get("GOOGLE_SHEETS_ACCESS_TOKEN", "")
        skip_ids = {item.strip() for item in os.environ.get("GOOGLE_SHEETS_SKIP_SOURCE_LEAD_IDS", "").split(",") if item.strip()}
        if service_account_json:
            credentials = service_account.Credentials.from_service_account_info(
                json.loads(service_account_json),
                scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
            )
            credentials.refresh(GoogleAuthRequest())
            access_token = credentials.token or ""
        return cls(
            os.environ.get("GOOGLE_SHEETS_SPREADSHEET_ID", ""),
            os.environ.get("GOOGLE_SHEETS_RANGE", "Leads!A:Q"),
            access_token,
            skip_source_ids=skip_ids,
        )

    def read(self) -> Iterable[NormalizedSourceRow]:
        values = self._fetch(self._url).get("values")
        if not isinstance(values, list) or not values:
            raise InvalidWorkbookError("Google Sheets response has no headers")
        if tuple(values[0]) != EXPECTED_HEADERS:
            raise InvalidWorkbookError("Google Sheets headers do not match the exact A-Q contract")
        for source_values in values[1:]:
            row = [*source_values, *([None] * (len(EXPECTED_HEADERS) - len(source_values)))]
            row = row[: len(EXPECTED_HEADERS)]
            if str(row[0]).strip() in self._skip_source_ids:
                continue
            if any(value is not None and str(value).strip() for value in row):
                yield normalize_source_row(
                    dict(zip(EXPECTED_HEADERS, row, strict=True)),
                    required_fields={"contact_name", "phone", "email"},
                )

    @property
    def _url(self) -> str:
        return f"https://sheets.googleapis.com/v4/spreadsheets/{quote(self._spreadsheet_id, safe='')}/values/{quote(self._range_name, safe='')}"

    def _fetch_json(self, url: str) -> dict[str, Any]:
        request = Request(url, headers={"Authorization": f"Bearer {self._access_token}"})
        with urlopen(request, timeout=15) as response:  # nosec B310: fixed Google endpoint.
            return json.loads(response.read().decode("utf-8"))
````

## Snapshot de código: `apps/api/src/gerec_api/automation/outbox_worker.py`

````python
"""Retry-safe notification outbox worker for the Railway worker service."""

from __future__ import annotations

import logging
import os
import json
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from time import sleep
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from bson import ObjectId
from pymongo import ReturnDocument

from gerec_api.config import Settings
from gerec_api.infrastructure.mongo.client import MongoClientFactory
from gerec_api.infrastructure.mongo.collections import MongoCollections


LOGGER = logging.getLogger(__name__)


def _json_value(value: Any) -> str:
    """Project only transport-safe representations to the external provider."""
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"unsupported notification payload value: {type(value).__name__}")


@dataclass(frozen=True)
class OutboxEvent:
    event_id: Any
    event_type: str
    idempotency_key: str
    payload: dict[str, Any]
    attempts: int = 0
    status: str = "pending"
    claim_token: str | None = None

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> "OutboxEvent":
        return cls(
            event_id=document["_id"],
            event_type=str(document["eventType"]),
            idempotency_key=str(document["idempotencyKey"]),
            payload=dict(document.get("payload", {})),
            attempts=int(document.get("attempts", 0)),
            status=str(document.get("status", "pending")),
            claim_token=str(document["claimToken"]) if document.get("claimToken") else None,
        )


class OutboxRepository(Protocol):
    def claim(self, batch_size: int, now: datetime, max_attempts: int) -> Iterable[OutboxEvent]: ...

    def mark_sent(self, event: OutboxEvent, now: datetime) -> bool: ...

    def mark_retry(
        self, event: OutboxEvent, error: Exception, now: datetime, max_attempts: int
    ) -> bool: ...

    def cancel(self, event: OutboxEvent, now: datetime) -> bool: ...


class MongoOutboxRepository:
    """Use atomic Mongo claims so concurrent workers cannot deliver an event twice."""

    def __init__(self, database: Any, *, lock_for: timedelta = timedelta(minutes=5)) -> None:
        self._outbox = database[MongoCollections.NOTIFICATION_OUTBOX]
        self._incidents = database[MongoCollections.NOTIFICATION_INCIDENTS]
        self._lock_for = lock_for

    def claim(self, batch_size: int, now: datetime, max_attempts: int) -> list[OutboxEvent]:
        claimed: list[OutboxEvent] = []
        for _ in range(batch_size):
            claim_token = uuid4().hex
            document = self._outbox.find_one_and_update(
                {
                    "attempts": {"$lt": max_attempts},
                    "$or": [
                        {"status": {"$in": ["pending", "retry"]}},
                        {"status": "scheduled", "scheduledFor": {"$lte": now}},
                        {"status": "processing", "lockedUntil": {"$lte": now}},
                    ],
                },
                {
                    "$set": {
                        "status": "processing",
                        "lockedUntil": now + self._lock_for,
                        "claimToken": claim_token,
                    },
                    "$inc": {"attempts": 1},
                },
                sort=[("createdAt", 1), ("_id", 1)],
                return_document=ReturnDocument.AFTER,
            )
            if document is None:
                break
            claimed.append(OutboxEvent.from_document(document))
        return claimed

    def mark_sent(self, event: OutboxEvent, now: datetime) -> bool:
        if not event.claim_token:
            return False
        result = self._outbox.update_one(
            {"_id": event.event_id, "status": "processing", "claimToken": event.claim_token},
            {
                "$set": {"status": "sent", "sentAt": now},
                "$unset": {"lockedUntil": "", "claimToken": ""},
            },
        )
        return result.matched_count == 1

    def mark_retry(
        self, event: OutboxEvent, error: Exception, now: datetime, max_attempts: int
    ) -> bool:
        if not event.claim_token:
            return False
        message = str(error)[:500]
        terminal = event.attempts >= max_attempts
        result = self._outbox.update_one(
            {"_id": event.event_id, "status": "processing", "claimToken": event.claim_token},
            {
                "$set": {
                    "status": "dead_letter" if terminal else "retry",
                    "lastError": message,
                    "lastFailedAt": now,
                },
                "$unset": {"lockedUntil": "", "claimToken": ""},
            },
        )
        if result.matched_count != 1:
            return False
        if terminal:
            self._incidents.update_one(
                {"outboxEventId": event.event_id},
                {
                    "$setOnInsert": {
                        "outboxEventId": event.event_id,
                        "idempotencyKey": event.idempotency_key,
                        "eventType": event.event_type,
                        "createdAt": now,
                    },
                    "$set": {"lastError": message, "updatedAt": now},
                },
                upsert=True,
            )
        return True

    def cancel(self, event: OutboxEvent, now: datetime) -> bool:
        if not event.claim_token:
            return False
        result = self._outbox.update_one(
            {"_id": event.event_id, "status": "processing", "claimToken": event.claim_token},
            {
                "$set": {
                    "status": "cancelled",
                    "cancelledAt": now,
                    "cancelledByMigration": "20260904_remove_operational_sla",
                },
                "$unset": {"lockedUntil": "", "claimToken": ""},
            },
        )
        return result.matched_count == 1


class OutboxWorker:
    """Deliver only claimed events and leave domain data untouched on delivery errors."""

    def __init__(
        self,
        repository: OutboxRepository,
        deliver: Callable[[OutboxEvent], None],
        *,
        max_attempts: int = 3,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be positive")
        self._repository = repository
        self._deliver = deliver
        self._max_attempts = max_attempts

    def process(self, batch_size: int, *, now: datetime | None = None) -> int:
        if batch_size < 1:
            raise ValueError("batch_size must be positive")
        timestamp = now or datetime.now(UTC)
        delivered = 0
        for event in self._repository.claim(batch_size, timestamp, self._max_attempts):
            if event.event_type == "lead.feedback_due_soon":
                self._repository.cancel(event, timestamp)
                continue
            try:
                self._deliver(event)
            except Exception as error:  # external providers are retried; domain commits remain intact
                LOGGER.warning("outbox delivery failed: event=%s type=%s", event.event_id, event.event_type)
                self._repository.mark_retry(event, error, timestamp, self._max_attempts)
                continue
            if self._repository.mark_sent(event, timestamp):
                delivered += 1
            else:
                LOGGER.warning("outbox acknowledgement fenced: event=%s", event.event_id)
        return delivered


class WebhookDeliveryAdapter:
    """Provider-neutral Railway delivery hook; provider receives idempotency key."""

    def __init__(self, url: str, token: str | None, *, open_request: Callable[..., Any] = urlopen) -> None:
        if not url:
            raise ValueError("OUTBOX_DELIVERY_WEBHOOK_URL must be configured in Railway")
        self._url = url
        self._token = token
        self._open_request = open_request

    @classmethod
    def from_env(cls, *, open_request: Callable[..., Any] = urlopen) -> "WebhookDeliveryAdapter":
        return cls(os.environ.get("OUTBOX_DELIVERY_WEBHOOK_URL", ""), os.environ.get("OUTBOX_DELIVERY_TOKEN"), open_request=open_request)

    def deliver(self, event: OutboxEvent) -> None:
        headers = {"Content-Type": "application/json", "Idempotency-Key": event.idempotency_key}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        body = json.dumps(
            {"eventType": event.event_type, "idempotencyKey": event.idempotency_key, "payload": event.payload},
            default=_json_value,
        ).encode("utf-8")
        request = Request(self._url, data=body, headers=headers, method="POST")
        try:
            with self._open_request(request, timeout=10):
                return
        except (HTTPError, URLError) as error:
            raise RuntimeError(f"notification provider failed: {error}") from error


def process_outbox(batch_size: int) -> int:
    """Railway entry point. A deployment injects its delivery adapter at composition time."""
    settings = Settings.from_env()
    database = MongoClientFactory.create(settings)
    delivery = WebhookDeliveryAdapter.from_env()
    return OutboxWorker(MongoOutboxRepository(database), delivery.deliver).process(batch_size)


def run_forever(*, batch_size: int = 100, poll_seconds: float = 5) -> None:
    """Persistent Railway worker loop; logs only event metadata, never lead payloads."""
    while True:
        processed = process_outbox(batch_size)
        if processed == 0:
            sleep(poll_seconds)


if __name__ == "__main__":
    run_forever(batch_size=int(os.environ.get("OUTBOX_BATCH_SIZE", "100")))
````

## Snapshot de código: `apps/api/src/gerec_api/automation/scheduler.py`

````python
"""Railway cron coordination backed by persistent MongoDB job locks."""

from __future__ import annotations

import os
import logging
import traceback
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from gerec_api.automation.google_sheets_adapter import GoogleSheetsAdapter
from gerec_api.automation.sync_job import run_sync
from gerec_api.config import Settings
from gerec_api.infrastructure.mongo.client import MongoClientFactory
from gerec_api.infrastructure.mongo.collections import MongoCollections


SYNC_JOB_NAME = "google_sheets_sync"
SYNC_INTERVAL_MINUTES = 5


@dataclass(frozen=True)
class JobResult:
    sync_runs: int
    skipped: int
    failed: int


class JobLockRepository(Protocol):
    def claim(self, job_name: str, slot: str, now: datetime) -> bool: ...

    def finish(self, job_name: str, slot: str, now: datetime, *, succeeded: bool) -> None: ...


class MongoJobLockRepository:
    """Allow one successful run per time slot, with expired leases recoverable after crashes."""

    def __init__(self, database: Any, *, lease_for: timedelta = timedelta(minutes=10)) -> None:
        self._jobs = database[MongoCollections.AUTOMATION_JOB_LOCKS]
        self._lease_for = lease_for

    def claim(self, job_name: str, slot: str, now: datetime) -> bool:
        try:
            document = self._jobs.find_one_and_update(
                {
                    "_id": job_name,
                    "$and": [
                        {
                            "$or": [
                                {"lastSuccessfulSlot": {"$ne": slot}},
                                {"lastSuccessfulSlot": {"$exists": False}},
                            ]
                        },
                        {
                            "$or": [
                                {"lockedUntil": {"$lte": now}},
                                {"lockedUntil": {"$exists": False}},
                            ]
                        },
                    ],
                },
                {
                    "$set": {"lockedSlot": slot, "lockedUntil": now + self._lease_for},
                    "$setOnInsert": {"createdAt": now},
                },
                upsert=True,
                return_document=ReturnDocument.AFTER,
            )
        except DuplicateKeyError:
            return False
        return document is not None and document.get("lockedSlot") == slot

    def finish(self, job_name: str, slot: str, now: datetime, *, succeeded: bool) -> None:
        update: dict[str, Any] = {
            "$set": {"lastRunAt": now, "lastStatus": "succeeded" if succeeded else "failed"},
            "$unset": {"lockedSlot": "", "lockedUntil": ""},
        }
        if succeeded:
            update["$set"]["lastSuccessfulSlot"] = slot
        self._jobs.update_one({"_id": job_name, "lockedSlot": slot}, update)


class InMemoryJobLockRepository:
    """Small deterministic lock repository for unit tests."""

    def __init__(self) -> None:
        self._successful_slots: set[tuple[str, str]] = set()
        self._locked: set[tuple[str, str]] = set()

    def claim(self, job_name: str, slot: str, now: datetime) -> bool:
        key = (job_name, slot)
        if key in self._successful_slots or key in self._locked:
            return False
        self._locked.add(key)
        return True

    def finish(self, job_name: str, slot: str, now: datetime, *, succeeded: bool) -> None:
        key = (job_name, slot)
        self._locked.discard(key)
        if succeeded:
            self._successful_slots.add(key)


class Scheduler:
    """Run the sync once per five-minute slot without embedding domain decisions."""

    def __init__(self, locks: JobLockRepository, run_sync_job: Callable[[str], None]) -> None:
        self._locks = locks
        self._run_sync_job = run_sync_job

    def run_due_jobs(self, now: datetime) -> JobResult:
        timestamp = now.astimezone(UTC)
        slot_time = timestamp.replace(
            minute=timestamp.minute - timestamp.minute % SYNC_INTERVAL_MINUTES,
            second=0,
            microsecond=0,
        )
        slot = slot_time.isoformat()
        if not self._locks.claim(SYNC_JOB_NAME, slot, timestamp):
            return JobResult(sync_runs=0, skipped=1, failed=0)
        try:
            self._run_sync_job(f"sync:{slot}")
        except Exception:
            logging.exception("google_sheets_sync job failed")
            self._locks.finish(SYNC_JOB_NAME, slot, timestamp, succeeded=False)
            return JobResult(sync_runs=0, skipped=0, failed=1)
        self._locks.finish(SYNC_JOB_NAME, slot, timestamp, succeeded=True)
        return JobResult(sync_runs=1, skipped=0, failed=0)


def _configured_sync(run_id: str) -> None:
    result = run_sync(GoogleSheetsAdapter.from_env(), run_id)
    if result.skipped:
        raise RuntimeError("source synchronization lease is already held")


def run_due_jobs(now: datetime) -> JobResult:
    """Railway cron entry point for the five-minute Google Sheets sync slot."""
    settings = Settings.from_env()
    database = MongoClientFactory.create(settings)
    return Scheduler(MongoJobLockRepository(database), _configured_sync).run_due_jobs(now)


def scheduler_exit_code(result: JobResult) -> int:
    """Make a failed cron execution visible to Railway for retry/alerting."""
    return 1 if result.failed else 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.info("google_sheets_sync starting")
    try:
        result = run_due_jobs(datetime.now(UTC))
        logging.info("google_sheets_sync finished: %s", result)
        raise SystemExit(scheduler_exit_code(result))
    except Exception:
        logging.error("google_sheets_sync failed")
        traceback.print_exc()
        raise
````

## Snapshot de código: `apps/api/src/gerec_api/automation/sync_job.py`

````python
"""Idempotent full-snapshot synchronization for Railway jobs."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4
from bson import ObjectId

from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from gerec_api.automation.workbook_adapter import WorkbookAdapter
from gerec_api.config import Settings
from gerec_api.domain.leads import LeadService
from gerec_api.domain.queue import QueueService
from gerec_api.domain.normalization import NormalizedSourceRow, normalize_source_row
from gerec_api.infrastructure.mongo.client import MongoClientFactory
from gerec_api.infrastructure.mongo.lead_repository import LeadRepository
from gerec_api.infrastructure.mongo.queue_repository import QueueRepository
from gerec_api.infrastructure.mongo.collections import MongoCollections


@dataclass(frozen=True)
class SyncResult:
    """Observable summary of one complete, replay-safe source snapshot."""

    run_id: str
    read_rows: int
    created: int
    updated: int
    ignored: int
    pending: int
    archived_source_records: int
    archived_leads: int
    skipped: bool = False


@dataclass(frozen=True)
class SyncLease:
    run_id: str
    claim_token: str
    generation: int


class SyncLeaseLostError(RuntimeError):
    """Raised when a newer synchronization owns the source fence."""


class SyncLeaseRepository:
    def claim(self, run_id: str, now: datetime) -> SyncLease | None: ...

    def heartbeat(self, lease: SyncLease, now: datetime) -> bool: ...

    def finish(self, lease: SyncLease, now: datetime, *, succeeded: bool) -> bool: ...


class InMemorySyncLeaseRepository(SyncLeaseRepository):
    """Deterministic fence for tests; Railway composes the Mongo implementation."""

    def __init__(self) -> None:
        self._current: SyncLease | None = None
        self._generation = 0

    def claim(self, run_id: str, now: datetime) -> SyncLease | None:
        if self._current is not None:
            return None
        self._generation += 1
        self._current = SyncLease(run_id, uuid4().hex, self._generation)
        return self._current

    def heartbeat(self, lease: SyncLease, now: datetime) -> bool:
        return self._current == lease

    def finish(self, lease: SyncLease, now: datetime, *, succeeded: bool) -> bool:
        if self._current != lease:
            return False
        self._current = None
        return True

    def invalidate_current(self) -> None:
        self._current = None


class MongoSyncLeaseRepository(SyncLeaseRepository):
    """Generation fence for full snapshots, persisted with Railway scheduler locks."""

    _LEASE_ID = "source_sync"

    def __init__(self, database: Any, *, lease_seconds: int = 600) -> None:
        self._locks = database[MongoCollections.AUTOMATION_JOB_LOCKS]
        self._lease_seconds = lease_seconds

    def claim(self, run_id: str, now: datetime) -> SyncLease | None:
        token = uuid4().hex
        try:
            document = self._locks.find_one_and_update(
                {
                    "_id": self._LEASE_ID,
                    "$or": [{"lockedUntil": {"$lte": now}}, {"lockedUntil": {"$exists": False}}],
                },
                {
                    "$set": {"runId": run_id, "claimToken": token, "lockedUntil": now + timedelta(seconds=self._lease_seconds)},
                    "$inc": {"generation": 1},
                    "$setOnInsert": {"createdAt": now},
                },
                upsert=True,
                return_document=ReturnDocument.AFTER,
            )
        except DuplicateKeyError:
            return None
        if document is None:
            return None
        return SyncLease(run_id, token, int(document["generation"]))

    def heartbeat(self, lease: SyncLease, now: datetime) -> bool:
        result = self._locks.update_one(
            {"_id": self._LEASE_ID, "claimToken": lease.claim_token, "generation": lease.generation},
            {"$set": {"lockedUntil": now + timedelta(seconds=self._lease_seconds)}},
        )
        return result.matched_count == 1

    def finish(self, lease: SyncLease, now: datetime, *, succeeded: bool) -> bool:
        result = self._locks.update_one(
            {"_id": self._LEASE_ID, "claimToken": lease.claim_token, "generation": lease.generation},
            {
                "$set": {"lastRunAt": now, "lastStatus": "succeeded" if succeeded else "failed"},
                "$unset": {"runId": "", "claimToken": "", "lockedUntil": ""},
            },
        )
        return result.matched_count == 1


class SyncJob:
    """Keep ingestion in the existing domain service; never assign leads directly."""

    def __init__(
        self,
        lead_service: LeadService,
        *,
        queue_service: QueueService | Any | None = None,
        leases: SyncLeaseRepository | None = None,
    ) -> None:
        self._lead_service = lead_service
        self._queue_service = queue_service
        self._leases = leases

    def run(self, source: Any, run_id: str) -> SyncResult:
        snapshot_id = run_id.strip()
        if not snapshot_id:
            raise ValueError("run_id is required")

        lease = self._leases.claim(snapshot_id, datetime.now(UTC)) if self._leases else None
        if self._leases is not None and lease is None:
            return SyncResult(snapshot_id, 0, 0, 0, 0, 0, 0, 0, skipped=True)
        counts = {"created": 0, "updated": 0, "ignored": 0, "pending": 0}
        read_rows = 0
        try:
            for raw_row in self._rows(source):
                self._heartbeat(lease)
                row = raw_row if isinstance(raw_row, NormalizedSourceRow) else normalize_source_row(raw_row)
                row = replace(row, source_snapshot_id=snapshot_id)
                result = self._lead_service.import_row(row, f"sync:{snapshot_id}:{row.source_lead_id}")
                read_rows += 1
                if result.status in counts:
                    counts[result.status] += 1
            if self._queue_service is not None:
                self._queue_service.reconcile_pending(f"sync:{snapshot_id}:reconcile")
            self._heartbeat(lease)
            archive = self._lead_service.archive_missing(snapshot_id)
        except Exception:
            self._finish(lease, succeeded=False)
            raise
        self._finish(lease, succeeded=True)
        return SyncResult(
            run_id=snapshot_id,
            read_rows=read_rows,
            created=counts["created"],
            updated=counts["updated"],
            ignored=counts["ignored"],
            pending=counts["pending"],
            archived_source_records=archive.archived_source_records,
            archived_leads=archive.archived_leads,
        )

    def _heartbeat(self, lease: SyncLease | None) -> None:
        if lease is not None and self._leases is not None:
            if not self._leases.heartbeat(lease, datetime.now(UTC)):
                raise SyncLeaseLostError("sync lease lost to a newer generation")

    def _finish(self, lease: SyncLease | None, *, succeeded: bool) -> None:
        if lease is not None and self._leases is not None:
            self._leases.finish(lease, datetime.now(UTC), succeeded=succeeded)

    @staticmethod
    def _rows(source: Any) -> Iterable[NormalizedSourceRow | dict[str, Any]]:
        if isinstance(source, (str, Path)):
            return WorkbookAdapter().read(Path(source))
        if hasattr(source, "read"):
            return source.read()
        return source


def run_sync(source: Any, run_id: str) -> SyncResult:
    """Railway entry point; credentials stay in the Python process environment."""
    settings = Settings.from_env()
    database = MongoClientFactory.create(settings)
    return SyncJob(
        LeadService(LeadRepository(database)),
        queue_service=QueueService(
            QueueRepository(database), actor_id="google-sheets-sync"
        ),
        leases=MongoSyncLeaseRepository(database),
    ).run(source, run_id)


def _mongo_id(value: str) -> Any:
    return ObjectId(value) if ObjectId.is_valid(value) else value
````

## Snapshot de código: `apps/api/src/gerec_api/automation/workbook_adapter.py`

````python
"""Read-only adapter for the provisional A-Q workbook contract."""

from collections.abc import Iterable
from pathlib import Path

from openpyxl import load_workbook

from gerec_api.domain.normalization import NormalizedSourceRow, normalize_source_row


EXPECTED_HEADERS = (
    "id",
    "created_time",
    "ad_id",
    "ad_name",
    "adset_id",
    "adset_name",
    "campaign_id",
    "campaign_name",
    "form_id",
    "form_name",
    "is_organic",
    "platform",
    "voc\u00ea_tem_cnpj_ou_mei?",
    "full_name",
    "phone_number",
    "email",
    "lead_status",
)


class InvalidWorkbookError(ValueError):
    """The workbook cannot safely represent a complete source snapshot."""


class WorkbookAdapter:
    """Validate the physical mock once, then yield normalized rows without writing it."""

    def read(self, path: Path) -> Iterable[NormalizedSourceRow]:
        workbook = load_workbook(filename=path, read_only=True, data_only=True)
        try:
            if "Leads" not in workbook.sheetnames:
                raise InvalidWorkbookError("workbook must contain the Leads sheet")
            sheet = workbook["Leads"]
            rows = sheet.iter_rows(values_only=True)
            try:
                headers = tuple(next(rows))
            except StopIteration as error:
                raise InvalidWorkbookError("workbook has no headers") from error
            if headers != EXPECTED_HEADERS:
                raise InvalidWorkbookError("workbook headers do not match the exact A-Q contract")
            for values in rows:
                if not any(value is not None and str(value).strip() for value in values):
                    continue
                yield normalize_source_row(dict(zip(EXPECTED_HEADERS, values, strict=True)))
        finally:
            workbook.close()
````

## Snapshot de código: `apps/api/src/gerec_api/config.py`

````python
"""Configura\u00e7\u00e3o exclusiva do processo Python do backend."""

from pydantic import Field, SecretStr, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Valores obrigat\u00f3rios fornecidos pelo ambiente do servidor."""

    mongodb_uri: str = Field(validation_alias="MONGODB_URI")
    mongodb_database: str = Field(validation_alias="MONGODB_DATABASE")
    app_secret: SecretStr = Field(validation_alias="APP_SECRET")

    model_config = SettingsConfigDict(extra="ignore")

    @classmethod
    def from_env(cls) -> "Settings":
        """Carrega a configura\u00e7\u00e3o sem inventar URI ou banco padr\u00e3o."""
        try:
            return cls()
        except ValidationError as error:
            missing = sorted(
                str(item["loc"][0])
                for item in error.errors()
                if item["type"] == "missing"
            )
            if missing:
                raise ValueError(
                    f"Missing required configuration: {', '.join(missing)}"
                ) from error
            raise
````

## Snapshot de código: `apps/api/src/gerec_api/domain/__init__.py`

````python
"""Regras de dom\u00ednio do Gerenciador de Leads."""
````

## Snapshot de código: `apps/api/src/gerec_api/domain/business_time.py`

````python
"""Business-time calculations for the São Paulo operating calendar."""

from datetime import date, datetime, time, timedelta
from typing import Protocol
from zoneinfo import ZoneInfo


SAO_PAULO = ZoneInfo("America/Sao_Paulo")
BUSINESS_DAY_START = time(9)
BUSINESS_DAY_END = time(18)


class HolidayRepository(Protocol):
    def is_holiday(self, day: date) -> bool: ...


class MongoHolidayRepository:
    """Adapt configured national/SP holiday documents to the calendar interface."""

    def __init__(self, collection) -> None:
        self._collection = collection

    def is_holiday(self, day: date) -> bool:
        return (
            self._collection.find_one(
                {"date": day.isoformat(), "scope": {"$in": ["national", "sp"]}}
            )
            is not None
        )


class BusinessClock:
    def __init__(self, holidays: HolidayRepository) -> None:
        self._holidays = holidays

    def add_business_hours(self, start: datetime, hours: int) -> datetime:
        if start.tzinfo is None or start.utcoffset() is None:
            raise ValueError("start datetime must include a timezone")
        if hours < 0:
            raise ValueError("hours must be non-negative")

        current = self._normalize_forward(start.astimezone(SAO_PAULO))
        remaining = timedelta(hours=hours)

        while remaining:
            business_day_end = self._at_business_day_end(current.date())
            available = business_day_end - current
            if remaining <= available:
                return current + remaining
            remaining -= available
            current = self._next_business_day_start(current.date())

        return current

    def subtract_business_hours(self, deadline: datetime, hours: int) -> datetime:
        if deadline.tzinfo is None or deadline.utcoffset() is None:
            raise ValueError("deadline datetime must include a timezone")
        if hours < 0:
            raise ValueError("hours must be non-negative")

        current = self._normalize_backward(deadline.astimezone(SAO_PAULO))
        remaining = timedelta(hours=hours)

        while remaining:
            business_day_start = self._at_business_day_start(current.date())
            available = current - business_day_start
            if remaining <= available:
                return current - remaining
            remaining -= available
            current = self._previous_business_day_end(current.date())

        return current

    def is_business_day(self, day: date) -> bool:
        return day.weekday() < 5 and not self._holidays.is_holiday(day)

    def _normalize_forward(self, value: datetime) -> datetime:
        if not self.is_business_day(value.date()):
            return self._next_business_day_start(value.date())
        if value.time() < BUSINESS_DAY_START:
            return self._at_business_day_start(value.date())
        if value.time() >= BUSINESS_DAY_END:
            return self._next_business_day_start(value.date())
        return value

    def _normalize_backward(self, value: datetime) -> datetime:
        if not self.is_business_day(value.date()):
            return self._previous_business_day_end(value.date())
        if value.time() < BUSINESS_DAY_START:
            return self._previous_business_day_end(value.date())
        if value.time() > BUSINESS_DAY_END:
            return self._at_business_day_end(value.date())
        return value

    def _next_business_day_start(self, day: date) -> datetime:
        next_day = day + timedelta(days=1)
        while not self.is_business_day(next_day):
            next_day += timedelta(days=1)
        return self._at_business_day_start(next_day)

    def _previous_business_day_end(self, day: date) -> datetime:
        previous_day = day - timedelta(days=1)
        while not self.is_business_day(previous_day):
            previous_day -= timedelta(days=1)
        return self._at_business_day_end(previous_day)

    @staticmethod
    def _at_business_day_start(day: date) -> datetime:
        return datetime.combine(day, BUSINESS_DAY_START, tzinfo=SAO_PAULO)

    @staticmethod
    def _at_business_day_end(day: date) -> datetime:
        return datetime.combine(day, BUSINESS_DAY_END, tzinfo=SAO_PAULO)
````

## Snapshot de código: `apps/api/src/gerec_api/domain/documents.py`

````python
"""Valida\u00e7\u00e3o de CPF e CNPJ antes da persist\u00eancia de empresas."""

from collections.abc import Iterable, Mapping
from typing import Any


class InvalidDocumentError(ValueError):
    """Documento ausente, malformado ou com d\u00edgitos verificadores inv\u00e1lidos."""


def normalize_document(value: str) -> str:
    """Conserva somente os d\u00edgitos usados pela identidade da empresa/contato."""
    return "".join(character for character in value if character.isdigit())


def require_valid_document(value: str) -> str:
    """Normaliza e devolve apenas CPF ou CNPJ com d\u00edgitos verificadores v\u00e1lidos."""
    normalized = normalize_document(value)
    if len(normalized) == 11 and _is_valid_cpf(normalized):
        return normalized
    if len(normalized) == 14 and _is_valid_cnpj(normalized):
        return normalized
    raise InvalidDocumentError("CPF ou CNPJ inv\u00e1lido para persist\u00eancia")


def prepare_company_for_persistence(company: Mapping[str, Any]) -> dict[str, Any]:
    """Devolve uma c\u00f3pia, validando CPF/CNPJ somente quando ele foi informado."""
    value = company.get("documentNormalized")
    if not isinstance(value, str):
        if "documentNormalized" not in company:
            return dict(company)
        raise InvalidDocumentError("CPF ou CNPJ obrigat\u00f3rio para persist\u00eancia")
    prepared = dict(company)
    prepared["documentNormalized"] = require_valid_document(value)
    return prepared


def _is_valid_cpf(value: str) -> bool:
    if len(set(value)) == 1:
        return False
    return _check_digit(value[:9], (10, 9, 8, 7, 6, 5, 4, 3, 2)) == int(value[9]) and _check_digit(
        value[:10], (11, 10, 9, 8, 7, 6, 5, 4, 3, 2)
    ) == int(value[10])


def _is_valid_cnpj(value: str) -> bool:
    if len(set(value)) == 1:
        return False
    first = _check_digit(value[:12], (5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2))
    second = _check_digit(value[:12] + str(first), (6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2))
    return first == int(value[12]) and second == int(value[13])


def _check_digit(value: str, weights: Iterable[int]) -> int:
    total = sum(int(digit) * weight for digit, weight in zip(value, weights, strict=True))
    remainder = total % 11
    return 0 if remainder < 2 else 11 - remainder
````

## Snapshot de código: `apps/api/src/gerec_api/domain/lead_notifications.py`

````python
"""Seller-scoped, persistent notification windows for newly assigned leads."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from hmac import compare_digest, new as hmac_new
from typing import Any, Callable, Protocol

from gerec_api.auth.sessions import CurrentUser


@dataclass(frozen=True)
class NewLeadNotification:
    """Minimal lead data that can be shown in the seller's notification window."""

    lead_id: str
    contact_name: str
    assigned_at: datetime

    def to_document(self) -> dict[str, str]:
        return {
            "leadId": self.lead_id,
            "contactName": self.contact_name,
            "assignedAt": self.assigned_at.isoformat(),
        }


@dataclass(frozen=True)
class NewLeadNotificationSnapshot:
    """A stable notification window and its server-issued closing watermark."""

    items: tuple[NewLeadNotification, ...]
    watermark: datetime
    acknowledgement_token: str
    watermark_sequence: int = 0

    def to_document(self) -> dict[str, Any]:
        return {
            "items": [item.to_document() for item in self.items],
            "watermark": self.watermark.isoformat(),
            "acknowledgementToken": self.acknowledgement_token,
            "watermarkSequence": self.watermark_sequence,
        }


class LeadNotificationPersistence(Protocol):
    def watermark_sequence(self) -> int: ...

    def for_seller(self, seller_id: str, watermark: datetime, watermark_sequence: int) -> tuple[NewLeadNotification, ...]: ...

    def acknowledge(self, seller_id: str, watermark: datetime, watermark_sequence: int) -> datetime: ...


class LeadNotificationService:
    """Owns authorization and time validation; persistence owns the atomic cursor update."""

    def __init__(
        self,
        persistence: LeadNotificationPersistence,
        *,
        signing_key: str,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._persistence = persistence
        self._signing_key = signing_key.encode("utf-8")
        self._now = now or (lambda: datetime.now(UTC))

    def for_seller(self, user: CurrentUser, session_token: str) -> NewLeadNotificationSnapshot:
        self._require_seller(user)
        watermark = self._timestamp(self._now(), label="clock")
        watermark_sequence = self._persistence.watermark_sequence()
        return NewLeadNotificationSnapshot(
            items=self._persistence.for_seller(user.id, watermark, watermark_sequence),
            watermark=watermark,
            acknowledgement_token=self._receipt(user, session_token, watermark, watermark_sequence),
            watermark_sequence=watermark_sequence,
        )

    def acknowledge(
        self,
        user: CurrentUser,
        watermark: datetime,
        acknowledgement_token: str,
        session_token: str,
        watermark_sequence: int = 0,
    ) -> datetime:
        self._require_seller(user)
        received = self._timestamp(watermark, label="notification watermark")
        if not isinstance(watermark_sequence, int) or isinstance(watermark_sequence, bool) or watermark_sequence < 0:
            raise ValueError("notification watermark sequence is invalid")
        if received > self._timestamp(self._now(), label="clock"):
            raise ValueError("notification watermark cannot be in the future")
        if not isinstance(acknowledgement_token, str) or not compare_digest(
            acknowledgement_token,
            self._receipt(user, session_token, received, watermark_sequence),
        ):
            raise ValueError("notification watermark was not issued for this session")
        return self._persistence.acknowledge(user.id, received, watermark_sequence)

    def _receipt(self, user: CurrentUser, session_token: str, watermark: datetime, watermark_sequence: int = 0) -> str:
        message = "\n".join((user.id, session_token, watermark.isoformat(), str(watermark_sequence))).encode("utf-8")
        return hmac_new(self._signing_key, message, sha256).hexdigest()

    @staticmethod
    def _require_seller(user: CurrentUser) -> None:
        if not isinstance(user, CurrentUser) or user.role != "seller" or not user.id:
            raise PermissionError("seller role is required")

    @staticmethod
    def _timestamp(value: datetime, *, label: str) -> datetime:
        if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{label} must be timezone-aware")
        return value.astimezone(UTC)
````

## Snapshot de código: `apps/api/src/gerec_api/domain/leads.py`

````python
"""Small domain interface for idempotent lead ingestion and source snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol

from gerec_api.domain.normalization import NormalizedSourceRow, normalize_source_row


@dataclass(frozen=True)
class ImportResult:
    status: str
    source_record_id: str
    lead_id: str | None
    pending_reasons: tuple[str, ...] = ()
    assignment_status: str | None = None

    def to_document(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "sourceRecordId": self.source_record_id,
            "leadId": self.lead_id,
            "pendingReasons": list(self.pending_reasons),
            "assignmentStatus": self.assignment_status,
        }

    @classmethod
    def from_document(cls, value: Mapping[str, Any]) -> "ImportResult":
        return cls(
            status=str(value["status"]),
            source_record_id=str(value["sourceRecordId"]),
            lead_id=str(value["leadId"]) if value.get("leadId") is not None else None,
            pending_reasons=tuple(str(item) for item in value.get("pendingReasons", [])),
            assignment_status=(
                str(value["assignmentStatus"])
                if value.get("assignmentStatus") is not None
                else None
            ),
        )


@dataclass(frozen=True)
class ArchiveResult:
    source_snapshot_id: str
    archived_source_records: int
    archived_leads: int

    def to_document(self) -> dict[str, Any]:
        return {
            "sourceSnapshotId": self.source_snapshot_id,
            "archivedSourceRecords": self.archived_source_records,
            "archivedLeads": self.archived_leads,
        }

    @classmethod
    def from_document(cls, value: Mapping[str, Any]) -> "ArchiveResult":
        return cls(
            source_snapshot_id=str(value["sourceSnapshotId"]),
            archived_source_records=int(value["archivedSourceRecords"]),
            archived_leads=int(value["archivedLeads"]),
        )


class LeadPersistence(Protocol):
    def import_row(self, row: NormalizedSourceRow, idempotency_key: str) -> ImportResult: ...

    def archive_missing(self, source_snapshot_id: str) -> ArchiveResult: ...


class LeadService:
    """Expose the complete ingestion workflow through two commands."""

    def __init__(self, persistence: LeadPersistence) -> None:
        self._persistence = persistence

    def import_row(
        self,
        row: NormalizedSourceRow | Mapping[str, Any],
        idempotency_key: str,
    ) -> ImportResult:
        normalized = row if isinstance(row, NormalizedSourceRow) else normalize_source_row(row)
        if not idempotency_key.strip():
            raise ValueError("idempotency key is required")
        return self._persistence.import_row(normalized, idempotency_key.strip())

    def archive_missing(self, source_snapshot_id: str) -> ArchiveResult:
        if not source_snapshot_id.strip():
            raise ValueError("source snapshot id is required")
        return self._persistence.archive_missing(source_snapshot_id.strip())
````

## Snapshot de código: `apps/api/src/gerec_api/domain/normalization.py`

````python
"""Normalize source rows into the stable ingestion contract."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from hashlib import sha256
import json
import re
from typing import Any, Mapping
from zoneinfo import ZoneInfo

from gerec_api.domain.documents import InvalidDocumentError, require_valid_document


SAO_PAULO = ZoneInfo("America/Sao_Paulo")
MOCK_QUESTION_HEADER = "voc\u00ea_tem_cnpj_ou_mei?"
MOCK_PROJECTION_HEADERS = (MOCK_QUESTION_HEADER, "full_name", "phone_number", "email")


class SourceRowValidationError(ValueError):
    """The row lacks the stable source identity required for idempotency."""


@dataclass(frozen=True)
class NormalizedSourceRow:
    """Versioned internal shape shared by workbook and future source adapters."""

    source_lead_id: str
    source_entered_at: datetime | None
    source_snapshot_id: str | None
    campaign_external_id: str | None
    campaign_name: str | None
    company_name: str | None
    document_normalized: str | None
    state: str | None
    contact_name: str | None
    phone_normalized: str | None
    email_normalized: str | None
    ad_external_id: str | None
    ad_name: str | None
    source_projection: dict[str, Any]
    source_payload: dict[str, Any]
    data_issues: tuple[str, ...]
    row_hash: str


def normalize_source_row(
    row: Mapping[str, Any], *, required_fields: set[str] | None = None
) -> NormalizedSourceRow:
    """Normalize one source row without making commercial decisions or inventing identity."""
    source_lead_id = _text(_first(row, "source_lead_id", "sourceLeadId", "id"))
    if source_lead_id is None:
        raise SourceRowValidationError("source lead id is required")

    source_entered_at = normalize_datetime(
        _first(row, "source_entered_at", "sourceEnteredAt", "created_time", "entry_date")
    )
    campaign_external_id = _text(_first(row, "campaign_external_id", "campaignExternalId", "campaign_id"))
    campaign_name = _text(_first(row, "campaign_name", "campaignName"))
    company_name = _text(_first(row, "company_name", "companyName"))
    document_normalized = normalize_valid_document(
        _first(row, "document", "document_number", "documentNormalized", "cnpj", "cpf_cnpj")
    )
    state = normalize_state(_first(row, "state", "estado", "uf"))
    contact_name = _text(_first(row, "contact_name", "contactName", "full_name", "name"))
    phone_normalized = normalize_phone(_first(row, "phone", "phone_number", "phoneNormalized"))
    email_normalized = normalize_email(_first(row, "email", "email_normalized", "emailNormalized"))
    source_snapshot_id = _text(_first(row, "source_snapshot_id", "sourceSnapshotId"))

    required_fields = required_fields or {
        "source_entered_at", "document", "state", "contact_name", "phone", "email"
    }
    issues: list[str] = []
    for field, value in (
        ("source_entered_at", source_entered_at),
        ("document", document_normalized),
        ("state", state),
        ("contact_name", contact_name),
        ("phone", phone_normalized),
        ("email", email_normalized),
    ):
        if value is None and field in required_fields:
            issues.append(field)
    if campaign_external_id is None and campaign_name is None:
        issues.append("campaign")

    source_projection = {
        header: _json_safe(row.get(header))
        for header in MOCK_PROJECTION_HEADERS
        if header in row
    }
    source_payload = {
        str(key): _json_safe(value)
        for key, value in row.items()
        if key not in {"source_snapshot_id", "sourceSnapshotId"}
    }
    hash_payload = {
        "sourceLeadId": source_lead_id,
        "sourceEnteredAt": _json_safe(source_entered_at),
        "campaignExternalId": campaign_external_id,
        "campaignName": campaign_name,
        "companyName": company_name,
        "documentNormalized": document_normalized,
        "state": state,
        "contactName": contact_name,
        "phoneNormalized": phone_normalized,
        "emailNormalized": email_normalized,
        "adExternalId": _text(_first(row, "ad_external_id", "adExternalId", "ad_id")),
        "adName": _text(_first(row, "ad_name", "adName")),
        "sourceProjection": source_projection,
        "sourcePayload": source_payload,
    }
    row_hash = sha256(
        json.dumps(hash_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return NormalizedSourceRow(
        source_lead_id=source_lead_id,
        source_entered_at=source_entered_at,
        source_snapshot_id=source_snapshot_id,
        campaign_external_id=campaign_external_id,
        campaign_name=campaign_name,
        company_name=company_name,
        document_normalized=document_normalized,
        state=state,
        contact_name=contact_name,
        phone_normalized=phone_normalized,
        email_normalized=email_normalized,
        ad_external_id=hash_payload["adExternalId"],
        ad_name=hash_payload["adName"],
        source_projection=source_projection,
        source_payload=source_payload,
        data_issues=tuple(issues),
        row_hash=row_hash,
    )


def normalize_valid_document(value: Any) -> str | None:
    text = _text(value)
    if text is None:
        return None
    try:
        return require_valid_document(text)
    except InvalidDocumentError:
        return None


def normalize_phone(value: Any) -> str | None:
    text = _text(value)
    if text is None:
        return None
    digits = "".join(character for character in text if character.isdigit())
    if len(digits) in (10, 11):
        digits = f"55{digits}"
    if len(digits) not in (12, 13) or not digits.startswith("55"):
        return None
    return digits


def normalize_email(value: Any) -> str | None:
    text = _text(value)
    if text is None:
        return None
    normalized = text.casefold()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", normalized):
        return None
    return normalized


def normalize_state(value: Any) -> str | None:
    text = _text(value)
    if text is None:
        return None
    candidate = text.casefold()
    if len(text) == 2:
        abbreviation = text.upper()
        return abbreviation if abbreviation in _STATE_NAMES.values() else None
    return _STATE_NAMES.get(candidate)


def normalize_datetime(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    parsed: datetime
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, date):
        parsed = datetime.combine(value, datetime.min.time())
    else:
        text = str(value).strip()
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            parsed = _parse_local_datetime(text)
            if parsed is None:
                return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=SAO_PAULO)
    return parsed.astimezone(UTC)


def _parse_local_datetime(value: str) -> datetime | None:
    for pattern in ("%d/%m/%Y %H:%M", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, pattern)
        except ValueError:
            continue
    return None


def _first(row: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in row:
            return row[key]
    return None


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _json_safe(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value


_STATE_NAMES = {
    "acre": "AC",
    "alagoas": "AL",
    "amap\u00e1": "AP",
    "amazonas": "AM",
    "bahia": "BA",
    "cear\u00e1": "CE",
    "distrito federal": "DF",
    "esp\u00edrito santo": "ES",
    "goi\u00e1s": "GO",
    "maranh\u00e3o": "MA",
    "mato grosso": "MT",
    "mato grosso do sul": "MS",
    "minas gerais": "MG",
    "par\u00e1": "PA",
    "para\u00edba": "PB",
    "paran\u00e1": "PR",
    "pernambuco": "PE",
    "piau\u00ed": "PI",
    "rio de janeiro": "RJ",
    "rio grande do norte": "RN",
    "rio grande do sul": "RS",
    "rond\u00f4nia": "RO",
    "roraima": "RR",
    "santa catarina": "SC",
    "s\u00e3o paulo": "SP",
    "sergipe": "SE",
    "tocantins": "TO",
}
````

## Snapshot de código: `apps/api/src/gerec_api/domain/operations.py`

````python
"""Domain interface for feedback, contact attempts and commercial outcomes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any, Literal, Mapping, Protocol
from zoneinfo import ZoneInfo

from gerec_api.domain.business_time import BusinessClock


SAO_PAULO = ZoneInfo("America/Sao_Paulo")
OUTCOMES = frozenset(
    {"qualified_follow_up", "qualified_closed_no_conversion", "disqualified", "won"}
)
DISQUALIFICATION_REASONS = frozenset({"no_answer_after_5_attempts", "no_cnpj", "outside_sp"})
COMMERCIAL_STATUSES = frozenset({"undefined", "potential", "negotiation", "won"})
CommercialStatus = Literal["undefined", "potential", "negotiation", "won"]


@dataclass(frozen=True)
class FeedbackCommand:
    lead_id: Any
    comment: str
    contact_started: bool
    idempotency_key: str
    administrative_note: bool = False


@dataclass(frozen=True)
class AttemptCommand:
    lead_id: Any
    comment: str
    idempotency_key: str
    business_date: date | None = None
    channel: str = "whatsapp"


@dataclass(frozen=True)
class OutcomeCommand:
    lead_id: Any
    outcome: str
    comment: str
    idempotency_key: str
    disqualification_reason: str | None = None
    response_confirmed: bool = False


@dataclass(frozen=True)
class TreatmentCommand:
    lead_id: Any
    comment: str
    commercial_status: CommercialStatus
    is_disqualified: bool
    idempotency_key: str


@dataclass(frozen=True)
class FeedbackResult:
    lead_id: str
    feedback_id: str
    status: str

    def to_document(self) -> dict[str, Any]:
        return {
            "leadId": self.lead_id,
            "feedbackId": self.feedback_id,
            "status": self.status,
        }

    @classmethod
    def from_document(cls, value: Mapping[str, Any]) -> "FeedbackResult":
        return cls(
            lead_id=str(value["leadId"]),
            feedback_id=str(value["feedbackId"]),
            status=str(value["status"]),
        )


@dataclass(frozen=True)
class AttemptResult:
    lead_id: str
    attempt_id: str
    sequence: int
    business_date: date
    may_disqualify_no_answer: bool
    status: str

    def to_document(self) -> dict[str, Any]:
        return {
            "leadId": self.lead_id,
            "attemptId": self.attempt_id,
            "sequence": self.sequence,
            "businessDate": self.business_date.isoformat(),
            "mayDisqualifyNoAnswer": self.may_disqualify_no_answer,
            "status": self.status,
        }

    @classmethod
    def from_document(cls, value: Mapping[str, Any]) -> "AttemptResult":
        raw_date = value["businessDate"]
        business_date = raw_date if isinstance(raw_date, date) else date.fromisoformat(str(raw_date))
        return cls(
            lead_id=str(value["leadId"]),
            attempt_id=str(value["attemptId"]),
            sequence=int(value["sequence"]),
            business_date=business_date,
            may_disqualify_no_answer=bool(value["mayDisqualifyNoAnswer"]),
            status=str(value["status"]),
        )


@dataclass(frozen=True)
class OutcomeResult:
    lead_id: str
    outcome_event_id: str
    outcome: str
    sale_id: str | None
    status: str

    def to_document(self) -> dict[str, Any]:
        return {
            "leadId": self.lead_id,
            "outcomeEventId": self.outcome_event_id,
            "outcome": self.outcome,
            "saleId": self.sale_id,
            "status": self.status,
        }

    @classmethod
    def from_document(cls, value: Mapping[str, Any]) -> "OutcomeResult":
        return cls(
            lead_id=str(value["leadId"]),
            outcome_event_id=str(value["outcomeEventId"]),
            outcome=str(value["outcome"]),
            sale_id=str(value["saleId"]) if value.get("saleId") is not None else None,
            status=str(value["status"]),
        )


@dataclass(frozen=True)
class TreatmentResult:
    lead_id: str
    treatment_id: str
    status: str
    commercial_status: CommercialStatus
    is_disqualified: bool
    comment_count: int
    last_updated_at: datetime

    def to_document(self) -> dict[str, Any]:
        return {
            "leadId": self.lead_id,
            "treatmentId": self.treatment_id,
            "status": self.status,
            "commercialStatus": self.commercial_status,
            "isDisqualified": self.is_disqualified,
            "commentCount": self.comment_count,
            "lastUpdatedAt": self.last_updated_at,
        }

    @classmethod
    def from_document(cls, value: Mapping[str, Any]) -> "TreatmentResult":
        return cls(
            lead_id=str(value["leadId"]),
            treatment_id=str(value["treatmentId"]),
            status=str(value["status"]),
            commercial_status=str(value["commercialStatus"]),  # type: ignore[arg-type]
            is_disqualified=bool(value["isDisqualified"]),
            comment_count=int(value["commentCount"]),
            last_updated_at=value["lastUpdatedAt"],
        )


class Clock(Protocol):
    def now(self, session: Any | None = None) -> datetime: ...


class SystemClock:
    def now(self, session: Any | None = None) -> datetime:
        return datetime.now(UTC)


class OperationsPersistence(Protocol):
    def register_treatment(
        self,
        command: TreatmentCommand,
        *,
        actor_id: Any,
        actor_role: str,
        now: datetime,
    ) -> TreatmentResult: ...

    def register_feedback(
        self,
        command: FeedbackCommand,
        *,
        actor_id: Any,
        actor_role: str,
        now: datetime,
    ) -> FeedbackResult: ...

    def register_attempt(
        self,
        command: AttemptCommand,
        *,
        actor_id: Any,
        actor_role: str,
        now: datetime,
        business_date: date,
    ) -> AttemptResult: ...

    def register_outcome(
        self,
        command: OutcomeCommand,
        *,
        actor_id: Any,
        actor_role: str,
        now: datetime,
    ) -> OutcomeResult: ...


class OperationsService:
    def __init__(
        self,
        persistence: OperationsPersistence,
        *,
        business_clock: BusinessClock,
        clock: Clock,
        actor_id: Any = "system",
        actor_role: str = "system",
    ) -> None:
        self._persistence = persistence
        self._business_clock = business_clock
        self._clock = clock
        self._actor_id = actor_id
        self._actor_role = actor_role

    def with_actor(self, actor_id: Any, actor_role: str) -> "OperationsService":
        if actor_id is None or (isinstance(actor_id, str) and not actor_id.strip()):
            raise ValueError("actor id is required")
        if actor_role not in {"admin", "seller", "system"}:
            raise ValueError("actor role is invalid")
        return OperationsService(
            self._persistence,
            business_clock=self._business_clock,
            clock=self._clock,
            actor_id=actor_id,
            actor_role=actor_role,
        )

    def register_feedback(self, command: FeedbackCommand) -> FeedbackResult:
        command = FeedbackCommand(
            command.lead_id,
            _comment(command.comment),
            command.contact_started,
            _required(command.idempotency_key, "idempotency key"),
            command.administrative_note,
        )
        now = self._aware_now()
        if command.administrative_note:
            if self._actor_role != "admin":
                raise ValueError("administrative notes require an admin actor")
        else:
            if self._actor_role != "seller":
                raise ValueError("seller feedback requires a seller actor")
            if not command.contact_started:
                raise ValueError("feedback requires an explicit contact action")
        return self._persistence.register_feedback(
            command,
            actor_id=self._actor_id,
            actor_role=self._actor_role,
            now=now,
        )

    def register_treatment(self, command: TreatmentCommand) -> TreatmentResult:
        if self._actor_role != "seller":
            raise ValueError("treatments require a seller actor")
        if command.commercial_status not in COMMERCIAL_STATUSES:
            raise ValueError("commercial status is invalid")
        if not isinstance(command.is_disqualified, bool):
            raise ValueError("is disqualified must be a boolean")
        command = TreatmentCommand(
            command.lead_id,
            _comment(command.comment),
            command.commercial_status,
            command.is_disqualified,
            _required(command.idempotency_key, "idempotency key"),
        )
        now = self._aware_now()
        return self._persistence.register_treatment(
            command,
            actor_id=self._actor_id,
            actor_role=self._actor_role,
            now=now,
        )

    def register_attempt(self, command: AttemptCommand) -> AttemptResult:
        if self._actor_role != "seller":
            raise ValueError("contact attempts require a seller actor")
        now = self._aware_now()
        business_date = command.business_date or now.astimezone(SAO_PAULO).date()
        if business_date > now.astimezone(SAO_PAULO).date():
            raise ValueError("contact attempt cannot use a future date")
        if not self._business_clock.is_business_day(business_date):
            raise ValueError("contact attempt date must be a business day")
        if command.channel != "whatsapp":
            raise ValueError("only whatsapp attempts count in the MVP")
        command = AttemptCommand(
            command.lead_id,
            _comment(command.comment),
            _required(command.idempotency_key, "idempotency key"),
            business_date,
            command.channel,
        )
        return self._persistence.register_attempt(
            command,
            actor_id=self._actor_id,
            actor_role=self._actor_role,
            now=now,
            business_date=business_date,
        )

    def register_outcome(self, command: OutcomeCommand) -> OutcomeResult:
        if self._actor_role != "seller":
            raise ValueError("commercial outcomes require a seller actor")
        if command.outcome not in OUTCOMES:
            raise ValueError("outcome is invalid")
        reason = command.disqualification_reason
        if command.outcome == "disqualified":
            if reason not in DISQUALIFICATION_REASONS:
                raise ValueError("disqualification reason is invalid")
        elif reason is not None:
            raise ValueError("disqualification reason is only valid for disqualified outcomes")
        command = OutcomeCommand(
            command.lead_id,
            command.outcome,
            _comment(command.comment),
            _required(command.idempotency_key, "idempotency key"),
            reason,
            command.response_confirmed,
        )
        if command.outcome in {"qualified_follow_up", "qualified_closed_no_conversion"} and not command.response_confirmed:
            raise ValueError("qualified outcome requires explicit response confirmation")
        return self._persistence.register_outcome(
            command,
            actor_id=self._actor_id,
            actor_role=self._actor_role,
            now=self._aware_now(),
        )

    def _aware_now(self) -> datetime:
        value = self._clock.now()
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("clock must return a timezone-aware datetime")
        return value


def _required(value: str, label: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} is required")
    return normalized


def _comment(value: str) -> str:
    normalized = value.strip()
    if len(normalized) < 6:
        raise ValueError("comment must contain at least 6 useful characters")
    return normalized
````

## Snapshot de código: `apps/api/src/gerec_api/domain/queue.py`

````python
"""Domain rules and narrow command interface for the global lead queue."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping, Protocol, Sequence

from bson import ObjectId


@dataclass(frozen=True)
class SellerState:
    seller_id: Any
    active: bool
    paused: bool
    skip_balance: int
    position: int = 0


@dataclass(frozen=True)
class SellerAvailability:
    status: Literal["active", "paused"]
    reason: str | None


@dataclass(frozen=True)
class QueueEntry:
    seller_id: Any
    position: int
    availability: SellerAvailability
    skip_balance: int


@dataclass(frozen=True)
class QueueSnapshot:
    cursor_seller_id: ObjectId | None
    entries: list[QueueEntry]


@dataclass(frozen=True)
class QueueDecision:
    seller_id: Any | None
    next_seller_id: Any
    consumed_credit_seller_ids: tuple[Any, ...] = ()
    unavailable_seller_ids: tuple[Any, ...] = ()


class QueueRules:
    @staticmethod
    def availability(seller: SellerState) -> SellerAvailability:
        if seller.paused:
            return SellerAvailability("paused", "Pausa manual ativa.")
        if not seller.active:
            return SellerAvailability("paused", "Vendedor inativo.")
        return SellerAvailability("active", None)

    @classmethod
    def snapshot(cls, sellers: Sequence[SellerState], next_seller_id: Any) -> QueueSnapshot:
        if not sellers:
            return QueueSnapshot(cursor_seller_id=None, entries=[])
        decision = cls.select_normal(sellers, next_seller_id)
        start_seller_id = decision.seller_id or next_seller_id
        ordered = cls._circular_from_cursor(sellers, start_seller_id)
        return QueueSnapshot(
            cursor_seller_id=next_seller_id,
            entries=[
                QueueEntry(
                    seller_id=seller.seller_id,
                    position=seller.position,
                    availability=cls.availability(seller),
                    skip_balance=seller.skip_balance,
                )
                for seller in ordered
            ],
        )

    @staticmethod
    def select_normal(sellers: Sequence[SellerState], next_seller_id: Any) -> QueueDecision:
        if not sellers:
            raise ValueError("seller queue cannot be empty")
        cursor = QueueRules._cursor_index(sellers, next_seller_id)

        operational = [
            seller
            for seller in sellers
            if QueueRules.availability(seller).status == "active"
        ]
        if not operational:
            return QueueDecision(seller_id=None, next_seller_id=next_seller_id)

        balances = {seller.seller_id: seller.skip_balance for seller in sellers}
        if any(balance < 0 for balance in balances.values()):
            raise ValueError("skip balance cannot be negative")
        consumed: list[Any] = []
        unavailable: list[Any] = []

        while True:
            seller = sellers[cursor]
            cursor = (cursor + 1) % len(sellers)
            if QueueRules.availability(seller).status != "active":
                unavailable.append(seller.seller_id)
                continue
            if balances[seller.seller_id] > 0:
                balances[seller.seller_id] -= 1
                consumed.append(seller.seller_id)
                continue
            return QueueDecision(
                seller_id=seller.seller_id,
                next_seller_id=QueueRules._next_eligible_seller_id(sellers, cursor),
                consumed_credit_seller_ids=tuple(consumed),
                unavailable_seller_ids=tuple(unavailable),
            )

    @staticmethod
    def _cursor_index(sellers: Sequence[SellerState], seller_id: Any) -> int:
        try:
            return next(
                index for index, seller in enumerate(sellers) if seller.seller_id == seller_id
            )
        except StopIteration as error:
            raise ValueError("queue cursor does not reference a seller") from error

    @classmethod
    def _circular_from_cursor(
        cls, sellers: Sequence[SellerState], next_seller_id: Any
    ) -> list[SellerState]:
        cursor = cls._cursor_index(sellers, next_seller_id)
        return [*sellers[cursor:], *sellers[:cursor]]

    @classmethod
    def _next_eligible_seller_id(cls, sellers: Sequence[SellerState], start_index: int) -> Any:
        for offset in range(len(sellers)):
            seller = sellers[(start_index + offset) % len(sellers)]
            if cls.availability(seller).status == "active":
                return seller.seller_id
        raise ValueError("queue does not have an eligible seller")


@dataclass(frozen=True)
class AssignmentResult:
    lead_id: str
    assignment_id: str | None
    seller_id: str | None
    assignment_type: str | None
    status: str
    owner_id: str | None

    def to_document(self) -> dict[str, Any]:
        return {
            "leadId": self.lead_id,
            "assignmentId": self.assignment_id,
            "sellerId": self.seller_id,
            "assignmentType": self.assignment_type,
            "status": self.status,
            "ownerId": self.owner_id,
        }

    @classmethod
    def from_document(cls, value: Mapping[str, Any]) -> "AssignmentResult":
        return cls(
            lead_id=str(value["leadId"]),
            assignment_id=(
                str(value["assignmentId"]) if value.get("assignmentId") is not None else None
            ),
            seller_id=str(value["sellerId"]) if value.get("sellerId") is not None else None,
            assignment_type=(
                str(value["assignmentType"])
                if value.get("assignmentType") is not None
                else None
            ),
            status=str(value["status"]),
            owner_id=str(value["ownerId"]) if value.get("ownerId") is not None else None,
        )


@dataclass(frozen=True)
class TransferResult:
    company_id: str
    previous_owner_id: str | None
    owner_id: str
    status: str = "transferred"

    def to_document(self) -> dict[str, Any]:
        return {
            "companyId": self.company_id,
            "previousOwnerId": self.previous_owner_id,
            "ownerId": self.owner_id,
            "status": self.status,
        }

    @classmethod
    def from_document(cls, value: Mapping[str, Any]) -> "TransferResult":
        return cls(
            company_id=str(value["companyId"]),
            previous_owner_id=(
                str(value["previousOwnerId"])
                if value.get("previousOwnerId") is not None
                else None
            ),
            owner_id=str(value["ownerId"]),
            status=str(value.get("status", "transferred")),
        )


class QueuePersistence(Protocol):
    def reconcile_pending(self, command_prefix: str, *, actor_id: Any) -> list[AssignmentResult]: ...

    def distribute_ready(
        self, lead_id: Any, command_id: str, *, actor_id: Any
    ) -> AssignmentResult: ...

    def distribute_normal(
        self, lead_id: Any, command_id: str, *, actor_id: Any
    ) -> AssignmentResult: ...

    def assign_recurring(
        self, lead_id: Any, command_id: str, *, actor_id: Any
    ) -> AssignmentResult: ...

    def assign_temporarily(
        self,
        lead_id: Any,
        seller_id: Any,
        reason: str,
        command_id: str,
        *,
        actor_id: Any,
    ) -> AssignmentResult: ...

    def transfer_owner(
        self,
        company_id: Any,
        seller_id: Any,
        reason: str,
        command_id: str,
        *,
        actor_id: Any,
    ) -> TransferResult: ...

    def transfer_lead(
        self,
        lead_id: Any,
        seller_id: Any,
        reason: str,
        command_id: str,
        *,
        actor_id: Any,
    ) -> AssignmentResult: ...


class QueueService:
    """Expose queue mutations without leaking MongoDB details to routes or workers."""

    def __init__(self, persistence: QueuePersistence, *, actor_id: Any = "system") -> None:
        self._persistence = persistence
        self._actor_id = actor_id

    def with_actor(self, actor_id: Any) -> "QueueService":
        if actor_id is None or (isinstance(actor_id, str) and not actor_id.strip()):
            raise ValueError("actor id is required")
        return QueueService(self._persistence, actor_id=actor_id)

    def distribute_normal(self, lead_id: Any, command_id: str) -> AssignmentResult:
        return self._persistence.distribute_normal(
            lead_id,
            _required(command_id, "command id"),
            actor_id=self._actor_id,
        )

    def distribute_ready(self, lead_id: Any, command_id: str) -> AssignmentResult:
        """Assign a ready lead using recurring ownership or the global queue."""
        return self._persistence.distribute_ready(
            lead_id,
            _required(command_id, "command id"),
            actor_id=self._actor_id,
        )

    def reconcile_pending(self, command_prefix: str) -> list[AssignmentResult]:
        """Retry FIFO-safe leads parked before a seller became available."""
        return self._persistence.reconcile_pending(
            _required(command_prefix, "command prefix"), actor_id=self._actor_id
        )

    def assign_recurring(self, lead_id: Any, command_id: str) -> AssignmentResult:
        return self._persistence.assign_recurring(
            lead_id,
            _required(command_id, "command id"),
            actor_id=self._actor_id,
        )

    def assign_temporarily(
        self,
        lead_id: Any,
        seller_id: Any,
        reason: str,
        command_id: str,
    ) -> AssignmentResult:
        return self._persistence.assign_temporarily(
            lead_id,
            seller_id,
            _required(reason, "reason"),
            _required(command_id, "command id"),
            actor_id=self._actor_id,
        )

    def transfer_owner(
        self,
        company_id: Any,
        seller_id: Any,
        reason: str,
        command_id: str,
    ) -> TransferResult:
        return self._persistence.transfer_owner(
            company_id,
            seller_id,
            _required(reason, "reason"),
            _required(command_id, "command id"),
            actor_id=self._actor_id,
        )

    def transfer_lead(
        self,
        lead_id: Any,
        seller_id: Any,
        reason: str,
        command_id: str,
    ) -> AssignmentResult:
        return self._persistence.transfer_lead(
            lead_id,
            seller_id,
            _required(reason, "reason"),
            _required(command_id, "command id"),
            actor_id=self._actor_id,
        )


def _required(value: str, label: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} is required")
    return normalized
````

## Snapshot de código: `apps/api/src/gerec_api/domain/user_administration.py`

````python
"""Application commands for administrative user management."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Protocol

from gerec_api.auth.passwords import hash_password


UserRole = Literal["admin", "seller"]


class UserAdministrationError(RuntimeError):
    """Base error raised when an administrative user command cannot complete."""


class UserAlreadyExistsError(UserAdministrationError):
    """Raised when an e-mail is already owned by an account."""


class UserNotFoundError(UserAdministrationError):
    """Raised when the command target does not exist."""


@dataclass(frozen=True)
class CreateUserCommand:
    full_name: str
    email: str
    role: UserRole
    password: str


@dataclass(frozen=True)
class ManagedUser:
    id: str
    full_name: str
    email: str
    role: UserRole
    active: bool
    paused: bool | None

    def to_public(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.id,
            "fullName": self.full_name,
            "email": self.email,
            "role": self.role,
            "active": self.active,
        }
        if self.paused is not None:
            payload["paused"] = self.paused
        return payload


class UserAdministrationPersistence(Protocol):
    def create_user(
        self,
        command: CreateUserCommand,
        *,
        password_hash: str,
        actor_id: Any,
    ) -> ManagedUser: ...

    def set_manual_pause(
        self, user_id: Any, *, paused: bool, actor_id: Any
    ) -> ManagedUser: ...

    def reset_password(
        self, user_id: Any, *, password_hash: str, actor_id: Any
    ) -> ManagedUser: ...


class UserAdministrationService:
    """Validates commands before delegating every state change to persistence."""

    def __init__(self, persistence: UserAdministrationPersistence, *, actor_id: Any = "system") -> None:
        self._persistence = persistence
        self._actor_id = actor_id

    def with_actor(self, actor_id: Any) -> "UserAdministrationService":
        if actor_id is None or (isinstance(actor_id, str) and not actor_id.strip()):
            raise ValueError("actor id is required")
        return UserAdministrationService(self._persistence, actor_id=actor_id)

    def create_user(self, command: CreateUserCommand) -> ManagedUser:
        normalized = CreateUserCommand(
            full_name=_required(command.full_name, "full name"),
            email=_email(command.email),
            role=_role(command.role),
            password=_password(command.password),
        )
        return self._persistence.create_user(
            normalized,
            password_hash=hash_password(normalized.password),
            actor_id=self._actor_id,
        )

    def set_manual_pause(self, user_id: Any, paused: bool) -> ManagedUser:
        if not isinstance(paused, bool):
            raise ValueError("paused must be a boolean")
        return self._persistence.set_manual_pause(
            user_id,
            paused=paused,
            actor_id=self._actor_id,
        )

    def reset_password(self, user_id: Any, password: str) -> ManagedUser:
        return self._persistence.reset_password(
            user_id,
            password_hash=hash_password(_password(password)),
            actor_id=self._actor_id,
        )


def _required(value: str, label: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} is required")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} is required")
    return normalized


def _email(value: str) -> str:
    return _required(value, "email").casefold()


def _role(value: str) -> UserRole:
    if value not in {"admin", "seller"}:
        raise ValueError("role is invalid")
    return value


def _password(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("password is required")
    return value
````

## Snapshot de código: `apps/api/src/gerec_api/infrastructure/__init__.py`

````python
"""Adaptadores de infraestrutura do backend."""
````

## Snapshot de código: `apps/api/src/gerec_api/infrastructure/mongo/__init__.py`

````python
"""Infraestrutura de persist\u00eancia MongoDB."""
````

## Snapshot de código: `apps/api/src/gerec_api/infrastructure/mongo/bootstrap.py`

````python
"""Bootstrap n\u00e3o destrutivo do schema MongoDB."""

from typing import Any, Final

from pymongo.errors import CollectionInvalid
from pymongo.database import Database

from gerec_api.infrastructure.mongo.collections import MongoCollections, collection
from gerec_api.infrastructure.mongo.indexes import INDEXES
from gerec_api.infrastructure.mongo.migrations.runner import run_migrations


SCHEMA_VALIDATORS: Final[dict[str, dict[str, Any]]] = {
    MongoCollections.USERS: {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["emailNormalized"],
            "properties": {
                "emailNormalized": {"bsonType": "string", "minLength": 1},
                "newLeadsSeenAt": {"bsonType": ["date", "null"]},
                "newLeadsSeenAssignmentSequence": {"bsonType": ["int", "null"], "minimum": 0},
            },
        }
    },
    MongoCollections.SOURCE_RECORDS: {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["sourceLeadId"],
            "properties": {"sourceLeadId": {"bsonType": "string", "minLength": 1}},
        }
    },
    MongoCollections.COMPANIES: {
        "$jsonSchema": {
            "bsonType": "object",
            "properties": {
                "documentNormalized": {"bsonType": "string", "pattern": "^(?:[0-9]{11}|[0-9]{14})$"}
            },
        }
    },
    MongoCollections.SKIP_BALANCES: {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["sellerId", "balance"],
            "properties": {
                "sellerId": {"bsonType": "objectId"},
                "balance": {"bsonType": "int", "minimum": 0},
            },
        }
    },
    MongoCollections.LEADS: {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["companyId", "campaignId", "archivedAt"],
            "properties": {
                "companyId": {"bsonType": "objectId"},
                "campaignId": {"bsonType": "objectId"},
                "archivedAt": {"bsonType": ["date", "null"]},
                "commercialStatus": {"enum": ["undefined", "potential", "negotiation", "won"]},
                "isDisqualified": {"bsonType": "bool"},
                "commentCount": {"bsonType": "int", "minimum": 0},
                "lastCommentAt": {"bsonType": ["date", "null"]},
                "assignmentSequence": {"bsonType": "int", "minimum": 1},
            },
        }
    },
    MongoCollections.LEAD_TREATMENTS: {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["leadId", "comment", "createdAt", "idempotencyKey"],
            "properties": {
                "leadId": {"bsonType": "objectId"},
                "comment": {"bsonType": "string", "minLength": 6},
                "createdAt": {"bsonType": "date"},
                "idempotencyKey": {"bsonType": "string", "minLength": 1},
            },
        }
    },
    MongoCollections.SALES: {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["leadId", "reversedAt"],
            "properties": {
                "leadId": {"bsonType": "objectId"},
                "reversedAt": {"bsonType": ["date", "null"]},
            },
        }
    },
    MongoCollections.SESSIONS: {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["tokenHash"],
            "properties": {"tokenHash": {"bsonType": "string", "minLength": 1}},
        }
    },
    MongoCollections.COMMAND_RESULTS: {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["commandName", "idempotencyKey", "result", "createdAt"],
            "properties": {
                "commandName": {"bsonType": "string", "minLength": 1},
                "idempotencyKey": {"bsonType": "string", "minLength": 1},
                "result": {"bsonType": "object"},
                "createdAt": {"bsonType": "date"},
            },
        }
    },
}


def ensure_schema(db: Database) -> None:
    """Cria cole\u00e7\u00f5es, valida\u00e7\u00f5es e \u00edndices de modo idempotente e sem exclus\u00f5es."""
    for name in MongoCollections.ALL:
        validator = SCHEMA_VALIDATORS.get(name)
        if validator is None:
            _ensure_collection(db, name)
        else:
            _ensure_collection_validator(db, name, validator)

    run_migrations(db)
    _drop_retired_indexes(db)

    for index in INDEXES:
        index.apply(collection(db, index.collection_name))


def _drop_retired_indexes(db: Database) -> None:
    """Remove índices legados fora da transação de migração, onde Mongo permite DDL."""
    cycles = collection(db, MongoCollections.FEEDBACK_CYCLES)
    if "feedback_cycles_open_lead_unique" in cycles.index_information():
        cycles.drop_index("feedback_cycles_open_lead_unique")


def _ensure_collection_validator(db: Database, name: str, validator: dict[str, Any]) -> None:
    try:
        db.create_collection(
            name,
            validator=validator,
            validationLevel="strict",
            validationAction="error",
        )
    except CollectionInvalid:
        db.command(
            {
                "collMod": name,
                "validator": validator,
                "validationLevel": "strict",
                "validationAction": "error",
            }
        )


def _ensure_collection(db: Database, name: str) -> None:
    try:
        db.create_collection(name)
    except CollectionInvalid:
        return
````

## Snapshot de código: `apps/api/src/gerec_api/infrastructure/mongo/client.py`

````python
"""F\u00e1brica de clientes MongoDB restrita ao backend."""

from pymongo import MongoClient
from pymongo.database import Database as MongoDatabase

from gerec_api.config import Settings


class MongoClientFactory:
    """Cria o handle de banco sem expor a URI fora do processo servidor."""

    @staticmethod
    def create(settings: Settings) -> MongoDatabase:
        client = MongoClient(settings.mongodb_uri)
        return client[settings.mongodb_database]
````

## Snapshot de código: `apps/api/src/gerec_api/infrastructure/mongo/clock.py`

````python
"""Database-backed clock used for timestamps in transactional commands."""

from datetime import UTC, datetime
from typing import Any


class MongoClock:
    """Read MongoDB's server clock before starting a transaction."""

    def __init__(self, database: Any) -> None:
        self._database = database

    def now(self, session: Any | None = None) -> datetime:
        if session is not None:
            raise RuntimeError("MongoClock must be read before starting a transaction")
        local_time = self._database.command({"hello": 1})["localTime"]
        if local_time.tzinfo is None:
            return local_time.replace(tzinfo=UTC)
        return local_time.astimezone(UTC)
````

## Snapshot de código: `apps/api/src/gerec_api/infrastructure/mongo/collections.py`

````python
"""Nomes can\u00f4nicos das cole\u00e7\u00f5es MongoDB do Gerenciador de Leads."""

from typing import Final

from pymongo.collection import Collection
from pymongo.database import Database


class MongoCollections:
    """Evita que nomes de cole\u00e7\u00f5es sejam repetidos nas queries da aplica\u00e7\u00e3o."""

    USERS: Final = "users"
    SESSIONS: Final = "sessions"
    SELLER_QUEUE: Final = "seller_queue"
    QUEUE_STATE: Final = "queue_state"
    SKIP_BALANCES: Final = "skip_balances"
    CAMPAIGNS: Final = "campaigns"
    COMPANIES: Final = "companies"
    LEADS: Final = "leads"
    SOURCE_RECORDS: Final = "source_records"
    ASSIGNMENTS: Final = "assignments"
    FEEDBACK_CYCLES: Final = "feedback_cycles"
    FEEDBACKS: Final = "feedbacks"
    CONTACT_ATTEMPTS: Final = "contact_attempts"
    QUALIFICATION_EVENTS: Final = "qualification_events"
    SALES: Final = "sales"
    HOLIDAYS: Final = "holidays"
    SOURCE_SNAPSHOTS: Final = "source_snapshots"
    FIELD_OVERRIDES: Final = "field_overrides"
    SOURCE_CONFLICTS: Final = "source_conflicts"
    NOTIFICATION_OUTBOX: Final = "notification_outbox"
    NOTIFICATION_INCIDENTS: Final = "notification_incidents"
    AUTOMATION_JOB_LOCKS: Final = "automation_job_locks"
    AUDIT_LOG: Final = "audit_log"
    SYSTEM_SETTINGS: Final = "system_settings"
    COMMAND_RESULTS: Final = "command_results"
    LEAD_TREATMENTS: Final = "lead_treatments"
    SCHEMA_MIGRATIONS: Final = "schema_migrations"

    ALL: Final = (
        USERS,
        SESSIONS,
        SELLER_QUEUE,
        QUEUE_STATE,
        SKIP_BALANCES,
        CAMPAIGNS,
        COMPANIES,
        LEADS,
        SOURCE_RECORDS,
        ASSIGNMENTS,
        FEEDBACK_CYCLES,
        FEEDBACKS,
        CONTACT_ATTEMPTS,
        QUALIFICATION_EVENTS,
        SALES,
        HOLIDAYS,
        SOURCE_SNAPSHOTS,
        FIELD_OVERRIDES,
        SOURCE_CONFLICTS,
        NOTIFICATION_OUTBOX,
        NOTIFICATION_INCIDENTS,
        AUTOMATION_JOB_LOCKS,
        AUDIT_LOG,
        SYSTEM_SETTINGS,
        COMMAND_RESULTS,
        LEAD_TREATMENTS,
        SCHEMA_MIGRATIONS,
    )


def collection(db: Database, name: str) -> Collection:
    """Retorna uma cole\u00e7\u00e3o pelo nome can\u00f4nico centralizado."""
    return db[name]
````

## Snapshot de código: `apps/api/src/gerec_api/infrastructure/mongo/companies.py`

````python
"""Fronteira de persist\u00eancia das empresas."""

from collections.abc import Mapping
from typing import Any

from pymongo.collection import Collection
from pymongo.results import InsertOneResult

from gerec_api.domain.documents import prepare_company_for_persistence


class CompanyRepository:
    """Persiste empresas somente depois da valida\u00e7\u00e3o de identidade do dom\u00ednio."""

    def __init__(self, companies: Collection) -> None:
        self._companies = companies

    def insert(self, company: Mapping[str, Any]) -> InsertOneResult:
        """Valida checksum, normaliza e persiste a empresa em uma \u00fanica fronteira."""
        return self._companies.insert_one(prepare_company_for_persistence(company))
````

## Snapshot de código: `apps/api/src/gerec_api/infrastructure/mongo/indexes.py`

````python
"""Defini\u00e7\u00f5es idempotentes dos \u00edndices que protegem invariantes MongoDB."""

from dataclasses import dataclass
from typing import Any, Final

from pymongo import ASCENDING
from pymongo.collection import Collection

from gerec_api.infrastructure.mongo.collections import MongoCollections


@dataclass(frozen=True)
class MongoIndex:
    """Contrato declarativo de um \u00edndice que pode ser aplicado repetidamente."""

    collection_name: str
    keys: tuple[tuple[str, int], ...]
    name: str
    unique: bool = False
    partial_filter: dict[str, Any] | None = None

    def apply(self, target: Collection) -> str:
        """Cria ou reconcilia o \u00edndice sem apagar documentos existentes."""
        replacement_name = f"{self.name}__replacement"
        existing = target.index_information().get(self.name)
        if existing is not None and self._matches(existing):
            self._drop_replacement(target, replacement_name)
            return self.name

        if existing is None:
            try:
                return self._create(target, self.name)
            finally:
                self._drop_replacement(target, replacement_name)

        try:
            self._drop_replacement(target, replacement_name)
            self._create(target, replacement_name)
            target.drop_index(self.name)
            return self._create(target, self.name)
        except Exception:
            self._restore(target, self.name, existing)
            raise
        finally:
            self._drop_replacement(target, replacement_name)

    def _create(self, target: Collection, name: str) -> str:
        return target.create_index(self.keys, **self._options(name))

    def _options(self, name: str) -> dict[str, Any]:
        options: dict[str, Any] = {"name": name, "unique": self.unique}
        if self.partial_filter is not None:
            options["partialFilterExpression"] = self.partial_filter
        return options

    def _matches(self, index: dict[str, Any]) -> bool:
        return (
            index.get("key") == list(self.keys)
            and index.get("unique", False) is self.unique
            and index.get("partialFilterExpression") == self.partial_filter
        )

    @staticmethod
    def _drop_replacement(target: Collection, name: str) -> None:
        if name in target.index_information():
            target.drop_index(name)

    @staticmethod
    def _restore(target: Collection, name: str, index: dict[str, Any] | None) -> None:
        if index is None or name in target.index_information():
            return
        options: dict[str, Any] = {"name": name, "unique": index.get("unique", False)}
        if "partialFilterExpression" in index:
            options["partialFilterExpression"] = index["partialFilterExpression"]
        target.create_index(index["key"], **options)


INDEXES: Final[tuple[MongoIndex, ...]] = (
    MongoIndex(
        MongoCollections.USERS,
        (("emailNormalized", ASCENDING),),
        "users_email_normalized_unique",
        unique=True,
    ),
    MongoIndex(
        MongoCollections.SOURCE_RECORDS,
        (("sourceLeadId", ASCENDING),),
        "source_records_source_lead_id_unique",
        unique=True,
    ),
    MongoIndex(
        MongoCollections.CAMPAIGNS,
        (("identityKey", ASCENDING),),
        "campaigns_identity_key_unique",
        unique=True,
    ),
    MongoIndex(
        MongoCollections.COMPANIES,
        (("documentNormalized", ASCENDING),),
        "companies_document_normalized_present_unique",
        unique=True,
        partial_filter={"documentNormalized": {"$exists": True}},
    ),
    MongoIndex(
        MongoCollections.LEADS,
        (("companyId", ASCENDING), ("campaignId", ASCENDING)),
        "leads_active_company_campaign_unique",
        unique=True,
        partial_filter={"archivedAt": None},
    ),
    MongoIndex(
        MongoCollections.LEADS,
        (("assigneeId", ASCENDING), ("createdAt", ASCENDING)),
        "leads_assignee_created_at",
    ),
    MongoIndex(
        MongoCollections.LEADS,
        (("assigneeId", ASCENDING), ("assignedAt", ASCENDING)),
        "leads_assignee_assigned_at",
    ),
    MongoIndex(
        MongoCollections.LEADS,
        (("assigneeId", ASCENDING), ("assignmentSequence", ASCENDING)),
        "leads_assignee_assignment_sequence",
    ),
    MongoIndex(
        MongoCollections.SALES,
        (("leadId", ASCENDING),),
        "sales_active_lead_unique",
        unique=True,
        partial_filter={"reversedAt": None},
    ),
    MongoIndex(
        MongoCollections.CONTACT_ATTEMPTS,
        (("leadId", ASCENDING), ("businessDate", ASCENDING)),
        "contact_attempts_lead_business_date_unique",
        unique=True,
    ),
    MongoIndex(
        MongoCollections.SESSIONS,
        (("tokenHash", ASCENDING),),
        "sessions_token_hash_unique",
        unique=True,
    ),
    MongoIndex(
        MongoCollections.ASSIGNMENTS,
        (("leadId", ASCENDING),),
        "assignments_current_lead_unique",
        unique=True,
        partial_filter={"current": True},
    ),
    MongoIndex(
        MongoCollections.SKIP_BALANCES,
        (("sellerId", ASCENDING),),
        "skip_balances_seller_unique",
        unique=True,
    ),
    MongoIndex(
        MongoCollections.COMMAND_RESULTS,
        (("idempotencyKey", ASCENDING),),
        "command_results_idempotency_key_unique",
        unique=True,
    ),
    MongoIndex(
        MongoCollections.LEAD_TREATMENTS,
        (("leadId", ASCENDING), ("createdAt", ASCENDING)),
        "lead_treatments_lead_created_at",
    ),
    MongoIndex(
        MongoCollections.LEAD_TREATMENTS,
        (("sellerId", ASCENDING), ("createdAt", ASCENDING)),
        "lead_treatments_seller_created_at",
    ),
    MongoIndex(
        MongoCollections.LEAD_TREATMENTS,
        (("leadId", ASCENDING), ("idempotencyKey", ASCENDING)),
        "lead_treatments_lead_idempotency_key_unique",
        unique=True,
    ),
    MongoIndex(
        MongoCollections.SELLER_QUEUE,
        (("sellerId", ASCENDING),),
        "seller_queue_seller_unique",
        unique=True,
    ),
    MongoIndex(
        MongoCollections.SELLER_QUEUE,
        (("position", ASCENDING),),
        "seller_queue_position_present_unique",
        unique=True,
        partial_filter={"position": {"$exists": True}},
    ),
    MongoIndex(
        MongoCollections.NOTIFICATION_OUTBOX,
        (("idempotencyKey", ASCENDING),),
        "notification_outbox_idempotency_key_unique",
        unique=True,
    ),
    MongoIndex(
        MongoCollections.NOTIFICATION_INCIDENTS,
        (("outboxEventId", ASCENDING),),
        "notification_incidents_outbox_event_unique",
        unique=True,
    ),
)
````

## Snapshot de código: `apps/api/src/gerec_api/infrastructure/mongo/lead_notification_repository.py`

````python
"""MongoDB persistence for seller notification windows and cursors."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from pymongo import ASCENDING, ReturnDocument

from gerec_api.domain.lead_notifications import NewLeadNotification
from gerec_api.infrastructure.mongo.collections import MongoCollections


class LeadNotificationStateError(RuntimeError):
    """Raised when a persisted seller lacks a valid notification cursor."""


class MongoLeadNotificationRepository:
    """Read derived notification state without changing assignments, queue, or outbox."""

    def __init__(self, database: Any) -> None:
        self._users = database[MongoCollections.USERS]
        self._leads = database[MongoCollections.LEADS]
        self._queue_state = database[MongoCollections.QUEUE_STATE]

    def watermark_sequence(self) -> int:
        state = self._queue_state.find_one({"_id": "global"})
        value = 0 if state is None else state.get("assignmentSequence", 0)
        return int(value) if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else 0

    def for_seller(
        self,
        seller_id: str,
        watermark: datetime,
        watermark_sequence: int,
    ) -> tuple[NewLeadNotification, ...]:
        seller = self._seller(seller_id)
        seen_at = seller.get("newLeadsSeenAt")
        if not isinstance(seen_at, datetime):
            raise LeadNotificationStateError("seller notification cursor is not initialized")
        if watermark_sequence:
            seen_sequence = seller.get("newLeadsSeenAssignmentSequence", 0)
            seen_sequence = int(seen_sequence) if isinstance(seen_sequence, int) and not isinstance(seen_sequence, bool) else 0
            query = {
                "assigneeId": {"$in": _identity_values(seller_id)},
                "assignmentSequence": {"$gt": seen_sequence, "$lte": watermark_sequence},
            }
            sort = [("assignmentSequence", ASCENDING), ("_id", ASCENDING)]
        else:
            query = {
                "assigneeId": {"$in": _identity_values(seller_id)},
                "assignedAt": {"$gt": seen_at, "$lte": watermark},
            }
            sort = [("assignedAt", ASCENDING), ("_id", ASCENDING)]
        cursor = self._leads.find(query).sort(sort)
        return tuple(
            NewLeadNotification(
                lead_id=str(lead["_id"]),
                contact_name=_contact_name(lead),
                assigned_at=lead["assignedAt"].astimezone(UTC),
            )
            for lead in cursor
        )

    def acknowledge(self, seller_id: str, watermark: datetime, watermark_sequence: int = 0) -> datetime:
        seller = self._users.find_one_and_update(
            {"_id": {"$in": _identity_values(seller_id)}, "role": "seller"},
            {"$max": {"newLeadsSeenAt": watermark, "newLeadsSeenAssignmentSequence": watermark_sequence}},
            return_document=ReturnDocument.AFTER,
        )
        if seller is None or not isinstance(seller.get("newLeadsSeenAt"), datetime):
            raise LeadNotificationStateError("seller notification cursor cannot be acknowledged")
        return seller["newLeadsSeenAt"].astimezone(UTC)

    def _seller(self, seller_id: str) -> dict[str, Any]:
        seller = self._users.find_one({"_id": {"$in": _identity_values(seller_id)}, "role": "seller"})
        if seller is None:
            raise LeadNotificationStateError("seller notification cursor is unavailable")
        return seller


def _identity_values(value: str) -> list[Any]:
    values: list[Any] = [value]
    if ObjectId.is_valid(value):
        values.append(ObjectId(value))
    return values


def _contact_name(lead: dict[str, Any]) -> str:
    value = lead.get("contactName")
    return str(value).strip() if value is not None and str(value).strip() else "Não informado"
````

## Snapshot de código: `apps/api/src/gerec_api/infrastructure/mongo/lead_repository.py`

````python
"""Transactional MongoDB implementation of the lead-ingestion interface."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Callable

from pymongo.errors import DuplicateKeyError

from gerec_api.domain.documents import prepare_company_for_persistence
from gerec_api.domain.leads import ArchiveResult, ImportResult
from gerec_api.domain.normalization import NormalizedSourceRow
from gerec_api.infrastructure.mongo.collections import MongoCollections


IMPORT_COMMAND = "lead.import"
ARCHIVE_COMMAND = "lead.archive_missing"


class LeadRepository:
    """Keep deduplication, pending-state and snapshot lifecycle local to one adapter."""

    def __init__(self, database: Any, *, now: Callable[[], datetime] | None = None) -> None:
        self._database = database
        self._now = now or (lambda: datetime.now(UTC))

    def import_row(self, row: NormalizedSourceRow, idempotency_key: str) -> ImportResult:
        try:
            return self._with_transaction(
                lambda session: self._import_in_transaction(row, idempotency_key, session)
            )
        except DuplicateKeyError:
            receipt = self._command_results.find_one({"idempotencyKey": idempotency_key})
            if receipt is None or receipt.get("commandName") != IMPORT_COMMAND:
                raise
            return ImportResult.from_document(receipt["result"])

    def archive_missing(self, source_snapshot_id: str) -> ArchiveResult:
        idempotency_key = f"{ARCHIVE_COMMAND}:{source_snapshot_id}"
        try:
            return self._with_transaction(
                lambda session: self._archive_in_transaction(
                    source_snapshot_id,
                    idempotency_key,
                    session,
                )
            )
        except DuplicateKeyError:
            receipt = self._command_results.find_one({"idempotencyKey": idempotency_key})
            if receipt is None or receipt.get("commandName") != ARCHIVE_COMMAND:
                raise
            return ArchiveResult.from_document(receipt["result"])

    def _with_transaction(self, operation: Callable[[Any], Any]) -> Any:
        with self._database.client.start_session() as session:
            with session.start_transaction():
                return operation(session)

    def _import_in_transaction(
        self,
        row: NormalizedSourceRow,
        idempotency_key: str,
        session: Any,
    ) -> ImportResult:
        receipt = self._command_results.find_one(
            {"idempotencyKey": idempotency_key},
            session=session,
        )
        if receipt is not None:
            if receipt.get("commandName") != IMPORT_COMMAND:
                raise ValueError("idempotency key already belongs to another command")
            return ImportResult.from_document(receipt["result"])

        now = self._now()
        existing_source = self._source_records.find_one(
            {"sourceLeadId": row.source_lead_id},
            session=session,
        )
        campaign = (
            None
            if "campaign" in row.data_issues
            else self._resolve_campaign(row, now, session)
        )
        identical = (
            existing_source is not None
            and existing_source.get("rowHash") == row.row_hash
            and existing_source.get("present") is True
            and (existing_source.get("leadId") is not None or bool(row.data_issues))
        )

        if identical:
            source_id = existing_source["_id"]
            lead_id = existing_source.get("leadId")
            lead = (
                self._leads.find_one({"_id": lead_id}, session=session)
                if lead_id is not None
                else None
            )
            self._mark_source_seen(source_id, row.source_snapshot_id, now, session)
            result = ImportResult(
                status="ignored",
                source_record_id=str(source_id),
                lead_id=str(lead_id) if lead_id is not None else None,
                pending_reasons=tuple(existing_source.get("pendingReasons", [])),
                assignment_status=(lead.get("assignmentStatus") if lead is not None else None),
            )
        else:
            pending_reasons = list(row.data_issues)
            previous_lead_id = existing_source.get("leadId") if existing_source else None
            lead_id = None
            occurrence_created = False
            if not row.data_issues:
                assert campaign is not None
                company = self._resolve_company(row, now, session)
                lead, occurrence_created = self._resolve_lead(row, company, campaign, now, session)
                lead_id = lead["_id"]
                if campaign["status"] != "approved":
                    pending_reasons.append("campaign")
            source_id = self._upsert_source(
                row,
                lead_id,
                pending_reasons,
                existing_source,
                now,
                session,
            )
            if previous_lead_id is not None and previous_lead_id != lead_id:
                self._archive_detached_lead_if_orphaned(
                    previous_lead_id,
                    "source_became_pending" if lead_id is None else "source_relinked",
                    now,
                    session,
                )
            status = "pending" if pending_reasons else ("created" if occurrence_created else "updated")
            result = ImportResult(
                status=status,
                source_record_id=str(source_id),
                lead_id=str(lead_id) if lead_id is not None else None,
                pending_reasons=tuple(pending_reasons),
                assignment_status=(lead.get("assignmentStatus") if lead_id is not None else None),
            )

        self._command_results.insert_one(
            {
                "commandName": IMPORT_COMMAND,
                "idempotencyKey": idempotency_key,
                "result": result.to_document(),
                "createdAt": now,
            },
            session=session,
        )
        return result

    def _resolve_campaign(
        self,
        row: NormalizedSourceRow,
        now: datetime,
        session: Any,
    ) -> dict[str, Any]:
        identity_key = _campaign_identity(row)
        campaign = self._campaigns.find_one({"identityKey": identity_key}, session=session)
        fields = {
            "externalId": row.campaign_external_id,
            "sourceName": row.campaign_name,
            "updatedAt": now,
        }
        if campaign is None:
            document = {
                "identityKey": identity_key,
                **fields,
                "displayName": row.campaign_name or row.campaign_external_id,
                "status": "approved",
                "approvalMode": "google_sheets_auto",
                "createdAt": now,
            }
            result = self._campaigns.insert_one(document, session=session)
            return {"_id": result.inserted_id, **document}
        if campaign.get("status") == "pending_approval":
            fields["status"] = "approved"
            fields["approvalMode"] = "google_sheets_auto"
        self._campaigns.update_one({"_id": campaign["_id"]}, {"$set": fields}, session=session)
        return {**campaign, **fields}

    def _resolve_company(
        self,
        row: NormalizedSourceRow,
        now: datetime,
        session: Any,
    ) -> dict[str, Any]:
        if row.document_normalized is None:
            identity = f"source:{row.source_lead_id}"
            company = self._companies.find_one({"sourceIdentity": identity}, session=session)
            fields = {"name": row.company_name or row.contact_name, "state": row.state, "updatedAt": now}
            if company is None:
                document = {"sourceIdentity": identity, **fields, "ownerId": None, "clientSince": None, "createdAt": now}
                result = self._companies.insert_one(document, session=session)
                return {"_id": result.inserted_id, **document}
            self._companies.update_one({"_id": company["_id"]}, {"$set": fields}, session=session)
            return {**company, **fields}
        company = self._companies.find_one(
            {"documentNormalized": row.document_normalized},
            session=session,
        )
        fields = {
            "name": row.company_name or row.contact_name,
            "state": row.state,
            "updatedAt": now,
        }
        if company is None:
            document = prepare_company_for_persistence(
                {
                    "documentNormalized": row.document_normalized,
                    **fields,
                    "ownerId": None,
                    "clientSince": None,
                    "createdAt": now,
                }
            )
            result = self._companies.insert_one(document, session=session)
            return {"_id": result.inserted_id, **document}
        self._companies.update_one({"_id": company["_id"]}, {"$set": fields}, session=session)
        return {**company, **fields}

    def _resolve_lead(
        self,
        row: NormalizedSourceRow,
        company: dict[str, Any],
        campaign: dict[str, Any],
        now: datetime,
        session: Any,
    ) -> tuple[dict[str, Any], bool]:
        query = {
            "companyId": company["_id"],
            "campaignId": campaign["_id"],
            "archivedAt": None,
        }
        lead = self._leads.find_one(query, session=session)
        source_fields = {
            "sourceEnteredAt": row.source_entered_at,
            "contactName": row.contact_name,
            "phoneNormalized": row.phone_normalized,
            "emailNormalized": row.email_normalized,
            "state": row.state,
            "adExternalId": row.ad_external_id,
            "adName": row.ad_name,
            "updatedAt": now,
        }
        if lead is None:
            document = {
                **query,
                **source_fields,
                "assignmentStatus": "ready" if campaign["status"] == "approved" else "pending_campaign",
                "qualificationStatus": "pending",
                "conversionStatus": "active",
                "createdAt": now,
            }
            result = self._leads.insert_one(document, session=session)
            return {"_id": result.inserted_id, **document}, True
        operational_fields: dict[str, Any] = {}
        if lead.get("assignmentStatus") == "pending_campaign" and campaign["status"] == "approved":
            operational_fields["assignmentStatus"] = "ready"
        fields = {**source_fields, **operational_fields}
        self._leads.update_one({"_id": lead["_id"]}, {"$set": fields}, session=session)
        return {**lead, **fields}, False

    def _upsert_source(
        self,
        row: NormalizedSourceRow,
        lead_id: Any | None,
        pending_reasons: list[str],
        existing_source: dict[str, Any] | None,
        now: datetime,
        session: Any,
    ) -> Any:
        fields = {
            "leadId": lead_id,
            "sourceEnteredAt": row.source_entered_at,
            "lastSeenSnapshotId": row.source_snapshot_id,
            "rowHash": row.row_hash,
            "payload": row.source_payload,
            "sellerProjection": row.source_projection,
            "pendingReasons": pending_reasons,
            "present": True,
            "archivedAt": None,
            "archiveReason": None,
            "updatedAt": now,
        }
        if existing_source is None:
            result = self._source_records.insert_one(
                {
                    "sourceLeadId": row.source_lead_id,
                    **fields,
                    "createdAt": now,
                },
                session=session,
            )
            return result.inserted_id
        self._source_records.update_one(
            {"_id": existing_source["_id"]},
            {"$set": fields},
            session=session,
        )
        return existing_source["_id"]

    def _archive_detached_lead_if_orphaned(
        self,
        lead_id: Any,
        reason: str,
        now: datetime,
        session: Any,
    ) -> None:
        another_active = self._source_records.find_one(
            {"leadId": lead_id, "present": True},
            session=session,
        )
        if another_active is not None:
            return
        self._leads.update_one(
            {"_id": lead_id, "archivedAt": None},
            {
                "$set": {
                    "archivedAt": now,
                    "archiveReason": reason,
                    "assignmentStatus": "archived",
                    "updatedAt": now,
                }
            },
            session=session,
        )

    def _mark_source_seen(
        self,
        source_id: Any,
        source_snapshot_id: str | None,
        now: datetime,
        session: Any,
    ) -> None:
        self._source_records.update_one(
            {"_id": source_id},
            {
                "$set": {
                    "lastSeenSnapshotId": source_snapshot_id,
                    "updatedAt": now,
                }
            },
            session=session,
        )

    def _archive_in_transaction(
        self,
        source_snapshot_id: str,
        idempotency_key: str,
        session: Any,
    ) -> ArchiveResult:
        receipt = self._command_results.find_one(
            {"idempotencyKey": idempotency_key},
            session=session,
        )
        if receipt is not None:
            if receipt.get("commandName") != ARCHIVE_COMMAND:
                raise ValueError("idempotency key already belongs to another command")
            return ArchiveResult.from_document(receipt["result"])

        now = self._now()
        missing = list(
            self._source_records.find(
                {
                    "present": True,
                    "lastSeenSnapshotId": {"$ne": source_snapshot_id},
                },
                session=session,
            )
        )
        archived_leads = 0
        for source in missing:
            self._source_records.update_one(
                {"_id": source["_id"]},
                {
                    "$set": {
                        "present": False,
                        "archivedAt": now,
                        "archiveReason": "removed_from_source",
                        "updatedAt": now,
                    }
                },
                session=session,
            )
            lead_id = source.get("leadId")
            if lead_id is None:
                continue
            another_active = self._source_records.find_one(
                {
                    "leadId": lead_id,
                    "present": True,
                    "_id": {"$ne": source["_id"]},
                },
                session=session,
            )
            if another_active is None:
                lead = self._leads.find_one({"_id": lead_id, "archivedAt": None}, session=session)
                if lead is not None:
                    self._leads.update_one(
                        {"_id": lead_id},
                        {
                            "$set": {
                                "archivedAt": now,
                                "archiveReason": "removed_from_source",
                                "assignmentStatus": "archived",
                                "updatedAt": now,
                            }
                        },
                        session=session,
                    )
                    archived_leads += 1

        result = ArchiveResult(
            source_snapshot_id=source_snapshot_id,
            archived_source_records=len(missing),
            archived_leads=archived_leads,
        )
        self._command_results.insert_one(
            {
                "commandName": ARCHIVE_COMMAND,
                "idempotencyKey": idempotency_key,
                "result": result.to_document(),
                "createdAt": now,
            },
            session=session,
        )
        return result

    @property
    def _campaigns(self):
        return self._database[MongoCollections.CAMPAIGNS]

    @property
    def _companies(self):
        return self._database[MongoCollections.COMPANIES]

    @property
    def _leads(self):
        return self._database[MongoCollections.LEADS]

    @property
    def _source_records(self):
        return self._database[MongoCollections.SOURCE_RECORDS]

    @property
    def _command_results(self):
        return self._database[MongoCollections.COMMAND_RESULTS]


def _campaign_identity(row: NormalizedSourceRow) -> str:
    if row.campaign_external_id is not None:
        return f"external:{row.campaign_external_id}"
    assert row.campaign_name is not None
    return f"name:{' '.join(row.campaign_name.casefold().split())}"
````

## Snapshot de código: `apps/api/src/gerec_api/infrastructure/mongo/migrations/__init__.py`

````python
"""Versioned, idempotent MongoDB schema migrations."""
````

## Snapshot de código: `apps/api/src/gerec_api/infrastructure/mongo/migrations/20260828_operacao_comercial.py`

````python
"""Materialize GOV-004 commercial-operation projections from immutable legacy history."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from gerec_api.domain.business_time import BusinessClock, MongoHolidayRepository, SAO_PAULO
from gerec_api.infrastructure.mongo.collections import MongoCollections


VERSION = "20260828_operacao_comercial"
_COMMERCIAL_STATUSES = frozenset({"undefined", "negotiation", "won"})


def apply(database: Any, *, session: Any | None = None) -> None:
    """Rebuild mutable lead projections without altering legacy events or sessions."""
    options = _session_options(session)
    business_clock = BusinessClock(
        MongoHolidayRepository(database[MongoCollections.HOLIDAYS])
    )
    _rebuild_queue_positions(database, session)
    for lead in database[MongoCollections.LEADS].find({}, **options):
        _migrate_lead(database, lead, business_clock, session)


def _migrate_lead(
    database: Any,
    lead: dict[str, Any],
    business_clock: BusinessClock,
    session: Any | None,
) -> None:
    options = _session_options(session)
    lead_id = lead["_id"]
    feedbacks = _valid_feedbacks(database, lead_id, options)
    outcomes = list(
        database[MongoCollections.QUALIFICATION_EVENTS].find({"leadId": lead_id}, **options)
    )
    commercial_status = _commercial_status(lead, outcomes)
    is_disqualified = _is_disqualified(lead, outcomes)
    last_comment_at = _legacy_datetime(feedbacks[-1].get("createdAt")) if feedbacks else None

    _copy_legacy_feedbacks_as_treatments(
        database,
        lead_id,
        feedbacks,
        session,
    )
    update: dict[str, Any] = {
        "commercialStatus": commercial_status,
        "isDisqualified": is_disqualified,
        "commentCount": len(feedbacks),
        "lastCommentAt": last_comment_at,
    }
    if is_disqualified:
        closed_at = _disqualification_closed_at(outcomes, feedbacks, lead)
        database[MongoCollections.FEEDBACK_CYCLES].update_many(
            {"leadId": lead_id, "closedAt": None},
            {"$set": {"closedAt": closed_at, "closedByMigration": VERSION}},
            **options,
        )
        update.update({"feedbackDueAt": None, "feedbackReminderAt": None})
    else:
        due_at, reminder_at = _recalculate_open_cycles(
            database, lead, business_clock, session
        )
        update.update({"feedbackDueAt": due_at, "feedbackReminderAt": reminder_at})
    database[MongoCollections.LEADS].update_one({"_id": lead_id}, {"$set": update}, **options)


def _valid_feedbacks(database: Any, lead_id: Any, options: dict[str, Any]) -> list[dict[str, Any]]:
    feedbacks = database[MongoCollections.FEEDBACKS].find({"leadId": lead_id}, **options)
    valid = [
        feedback
        for feedback in feedbacks
        if feedback.get("kind") == "seller_feedback"
        and feedback.get("contactStarted") is True
        and len(str(feedback.get("comment", "")).strip()) >= 6
    ]
    return sorted(
        valid,
        key=lambda feedback: (
            _legacy_datetime(feedback.get("createdAt")) or _EPOCH,
            str(feedback["_id"]),
        ),
    )


def _copy_legacy_feedbacks_as_treatments(
    database: Any,
    lead_id: Any,
    feedbacks: list[dict[str, Any]],
    session: Any | None,
) -> None:
    options = _session_options(session)
    treatments = database[MongoCollections.LEAD_TREATMENTS]
    for feedback in feedbacks:
        legacy_id = feedback["_id"]
        treatment_status, treatment_disqualification, status_unavailable = _legacy_treatment_status(
            feedback
        )
        treatments.update_one(
            {"leadId": lead_id, "idempotencyKey": f"legacy-feedback:{legacy_id}"},
            {
                "$setOnInsert": {
                    "leadId": lead_id,
                    "sellerId": feedback.get("sellerId"),
                    "comment": str(feedback["comment"]).strip(),
                    "commercialStatus": treatment_status,
                    "isDisqualified": treatment_disqualification,
                    "legacyStatusUnavailable": status_unavailable,
                    "createdAt": _legacy_datetime(feedback.get("createdAt")) or _EPOCH,
                    "idempotencyKey": f"legacy-feedback:{legacy_id}",
                    "legacyFeedbackId": legacy_id,
                }
            },
            upsert=True,
            **options,
        )


def _legacy_treatment_status(feedback: dict[str, Any]) -> tuple[str, bool, bool]:
    status = feedback.get("commercialStatus")
    if status in _COMMERCIAL_STATUSES:
        return str(status), bool(feedback.get("isDisqualified")), False
    return "undefined", False, True


def _rebuild_queue_positions(database: Any, session: Any | None) -> None:
    options = _session_options(session)
    entries = list(database[MongoCollections.SELLER_QUEUE].find({}, **options))
    entries.sort(key=_queue_position_sort_key)
    for position, entry in enumerate(entries, start=1):
        database[MongoCollections.SELLER_QUEUE].update_one(
            {"_id": entry["_id"]}, {"$set": {"position": position}}, **options
        )


def _queue_position_sort_key(entry: dict[str, Any]) -> tuple[int, int, datetime, str]:
    position = entry.get("position")
    valid_position = isinstance(position, int) and not isinstance(position, bool) and position > 0
    created_at = _legacy_datetime(entry.get("createdAt"))
    return (
        0 if valid_position else 1,
        int(position) if valid_position else 0,
        created_at if isinstance(created_at, datetime) else _EPOCH,
        str(entry["_id"]),
    )


def _recalculate_open_cycles(
    database: Any,
    lead: dict[str, Any],
    business_clock: BusinessClock,
    session: Any | None,
) -> tuple[datetime | None, datetime | None]:
    options = _session_options(session)
    cycles = list(
        database[MongoCollections.FEEDBACK_CYCLES].find(
            {"leadId": lead["_id"], "closedAt": None}, **options
        )
    )
    recalculated: list[dict[str, Any]] = []
    for cycle in cycles:
        start_at = _legacy_datetime(cycle.get("startAt")) or _legacy_datetime(lead.get("assignedAt"))
        if not isinstance(start_at, datetime):
            continue
        due_at = business_clock.add_business_hours(start_at, 24)
        reminder_at = business_clock.subtract_business_hours(due_at, 4)
        database[MongoCollections.FEEDBACK_CYCLES].update_one(
            {"_id": cycle["_id"], "closedAt": None},
            {"$set": {"startAt": start_at, "dueAt": due_at, "reminderAt": reminder_at}},
            **options,
        )
        recalculated.append({"startAt": start_at, "dueAt": due_at, "reminderAt": reminder_at})
    if not recalculated:
        return None, None
    latest = max(recalculated, key=lambda cycle: (cycle["startAt"], cycle["dueAt"]))
    return latest["dueAt"], latest["reminderAt"]


def _commercial_status(lead: dict[str, Any], outcomes: list[dict[str, Any]]) -> str:
    if lead.get("conversionStatus") == "won" or any(
        outcome.get("outcome") == "won" for outcome in outcomes
    ):
        return "won"
    existing = lead.get("commercialStatus")
    if existing in _COMMERCIAL_STATUSES:
        return str(existing)
    if lead.get("qualificationStatus") in {"qualified", "in_negotiation", "negotiation"} or any(
        outcome.get("outcome") in {"qualified_follow_up", "negotiation"} for outcome in outcomes
    ):
        return "negotiation"
    return "undefined"


def _is_disqualified(lead: dict[str, Any], outcomes: list[dict[str, Any]]) -> bool:
    return bool(
        lead.get("isDisqualified")
        or lead.get("qualificationStatus") == "disqualified"
        or lead.get("conversionStatus") == "disqualified"
        or any(outcome.get("outcome") == "disqualified" for outcome in outcomes)
    )


def _disqualification_closed_at(
    outcomes: list[dict[str, Any]], feedbacks: list[dict[str, Any]], lead: dict[str, Any]
) -> datetime:
    timestamps = [
        _legacy_datetime(event.get("createdAt"))
        for event in outcomes
        if event.get("outcome") == "disqualified" and isinstance(event.get("createdAt"), datetime)
    ]
    timestamps.extend(
        _legacy_datetime(feedback.get("createdAt"))
        for feedback in feedbacks
        if isinstance(feedback.get("createdAt"), datetime)
    )
    assigned_at = _legacy_datetime(lead.get("assignedAt"))
    if assigned_at is not None:
        timestamps.append(assigned_at)
    return max(timestamps, default=_EPOCH)


def _session_options(session: Any | None) -> dict[str, Any]:
    return {} if session is None else {"session": session}


def _legacy_datetime(value: Any) -> datetime | None:
    """Normalize legacy Mongo timestamps before business-calendar operations.

    Historical records may contain naive datetimes because older Mongo clients
    did not persist timezone metadata. The canonical interpretation for those
    values is local São Paulo time; aware values are converted to that zone.
    """
    if not isinstance(value, datetime):
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=SAO_PAULO)
    return value.astimezone(SAO_PAULO)


_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
````

## Snapshot de código: `apps/api/src/gerec_api/infrastructure/mongo/migrations/20260904_remove_operational_sla.py`

````python
"""Disable legacy SLA projections without deleting historical audit records."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from gerec_api.infrastructure.mongo.collections import MongoCollections


VERSION = "20260904_remove_operational_sla"


def apply(database: Any, *, session: Any | None = None) -> None:
    """Clear active deadline state and cancel every nonterminal legacy reminder."""
    options = {} if session is None else {"session": session}
    now = datetime.now(UTC)
    database[MongoCollections.LEADS].update_many(
        {},
        {
            "$unset": {
                "feedbackCycleId": "",
                "feedbackDueAt": "",
                "feedbackReminderAt": "",
            }
        },
        **options,
    )
    database[MongoCollections.FEEDBACK_CYCLES].update_many(
        {"closedAt": None},
        {"$set": {"closedAt": now, "closedByMigration": VERSION}},
        **options,
    )
    database[MongoCollections.NOTIFICATION_OUTBOX].update_many(
        {
            "eventType": "lead.feedback_due_soon",
            "status": {"$nin": ["sent", "dead_letter", "cancelled"]},
        },
        {"$set": {"status": "cancelled", "cancelledAt": now, "cancelledByMigration": VERSION}},
        **options,
    )
````

## Snapshot de código: `apps/api/src/gerec_api/infrastructure/mongo/migrations/20260914_initialize_new_lead_notification_cursor.py`

````python
"""Initialize seller notification cursors without rewriting existing acknowledgements."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Callable

from gerec_api.infrastructure.mongo.collections import MongoCollections


VERSION = "20260914_initialize_new_lead_notification_cursor"


def apply(
    database: Any,
    *,
    session: Any | None = None,
    now: Callable[[], datetime] | None = None,
) -> None:
    """Set the first-window baseline only for sellers whose cursor is absent."""
    timestamp = (now or (lambda: datetime.now(UTC)))()
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("migration clock must return a timezone-aware datetime")
    options = {} if session is None else {"session": session}
    database[MongoCollections.USERS].update_many(
        {"role": "seller", "newLeadsSeenAt": {"$exists": False}},
        {"$set": {"newLeadsSeenAt": timestamp.astimezone(UTC)}},
        **options,
    )
````

## Snapshot de código: `apps/api/src/gerec_api/infrastructure/mongo/migrations/runner.py`

````python
"""Transactional runner for versioned MongoDB migrations."""

from __future__ import annotations

from importlib import import_module
from typing import Any, Callable, Final

from pymongo.errors import DuplicateKeyError

from gerec_api.infrastructure.mongo.collections import MongoCollections


Migration = tuple[str, Callable[..., None]]

_operacao_comercial = import_module(
    "gerec_api.infrastructure.mongo.migrations.20260828_operacao_comercial"
)
_remove_operational_sla = import_module(
    "gerec_api.infrastructure.mongo.migrations.20260904_remove_operational_sla"
)
_initialize_new_lead_notification_cursor = import_module(
    "gerec_api.infrastructure.mongo.migrations.20260914_initialize_new_lead_notification_cursor"
)
MIGRATIONS: Final[tuple[Migration, ...]] = (
    (_operacao_comercial.VERSION, _operacao_comercial.apply),
    (_remove_operational_sla.VERSION, _remove_operational_sla.apply),
    (_initialize_new_lead_notification_cursor.VERSION, _initialize_new_lead_notification_cursor.apply),
)


class ReplicaSetRequiredError(RuntimeError):
    """Raised when a migration cannot be protected by a MongoDB transaction."""


def run_migrations(database: Any) -> list[str]:
    """Apply each pending migration once, preserving historical documents on replay."""
    applied: list[str] = []
    for version, migration in MIGRATIONS:
        if database[MongoCollections.SCHEMA_MIGRATIONS].find_one({"_id": version}) is not None:
            continue
        if _apply_once(database, version, migration):
            applied.append(version)
    return applied


def _apply_once(database: Any, version: str, migration: Callable[..., None]) -> bool:
    def operation(session: Any | None) -> bool:
        migrations = database[MongoCollections.SCHEMA_MIGRATIONS]
        if migrations.find_one({"_id": version}, **_session_options(session)) is not None:
            return False
        migration(database, session=session)
        migrations.insert_one({"_id": version}, **_session_options(session))
        return True

    _require_replica_set(database)
    try:
        with database.client.start_session() as session:
            return session.with_transaction(operation)
    except DuplicateKeyError:
        if database[MongoCollections.SCHEMA_MIGRATIONS].find_one({"_id": version}) is not None:
            return False
        raise


def _require_replica_set(database: Any) -> None:
    """Reject standalone MongoDB before a migration can mutate data without a transaction."""
    hello = database.client.admin.command("hello")
    if not hello.get("setName"):
        raise ReplicaSetRequiredError(
            "MongoDB replica set is required to apply schema migrations transactionally"
        )


def _session_options(session: Any | None) -> dict[str, Any]:
    return {} if session is None else {"session": session}
````

## Snapshot de código: `apps/api/src/gerec_api/infrastructure/mongo/operations_repository.py`

````python
"""MongoDB transaction adapter for feedback, attempts and outcomes."""

from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime
from typing import Any, Callable, TypeVar

from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from gerec_api.domain.operations import (
    AttemptCommand,
    AttemptResult,
    FeedbackCommand,
    FeedbackResult,
    OutcomeCommand,
    OutcomeResult,
    TreatmentCommand,
    TreatmentResult,
    Clock,
    SystemClock,
)
from gerec_api.infrastructure.mongo.collections import MongoCollections


FEEDBACK_COMMAND = "operations.register_feedback"
ATTEMPT_COMMAND = "operations.register_attempt"
OUTCOME_COMMAND = "operations.register_outcome"
TREATMENT_COMMAND = "operations.register_treatment"
TERMINAL_CONVERSIONS = frozenset({"closed_no_conversion", "won"})
ResultT = TypeVar("ResultT", FeedbackResult, AttemptResult, OutcomeResult, TreatmentResult)


class OperationsStateError(RuntimeError):
    """Raised when an operations command would violate a domain invariant."""


class OperationsPermissionError(OperationsStateError, PermissionError):
    """Raised when an authenticated actor is outside a command's allowed scope."""


class MongoOperationsRepository:
    """Commit each operational command and all its effects in one Mongo transaction."""

    def __init__(
        self,
        database: Any,
        *,
        clock: Clock | None = None,
    ) -> None:
        self._database = database
        self._clock = clock or SystemClock()

    def register_feedback(
        self,
        command: FeedbackCommand,
        *,
        actor_id: Any,
        actor_role: str,
        now: datetime,
    ) -> FeedbackResult:
        return self._execute(
            FEEDBACK_COMMAND,
            command.idempotency_key,
            FeedbackResult,
            now,
            lambda session, transaction_now: self._register_feedback(
                command,
                actor_id,
                actor_role,
                transaction_now,
                session,
            ),
        )

    def register_treatment(
        self,
        command: TreatmentCommand,
        *,
        actor_id: Any,
        actor_role: str,
        now: datetime,
    ) -> TreatmentResult:
        return self._execute(
            TREATMENT_COMMAND,
            command.idempotency_key,
            TreatmentResult,
            now,
            lambda session, transaction_now: self._register_treatment(
                command,
                actor_id,
                actor_role,
                transaction_now,
                session,
            ),
            actor_id=actor_id,
            aggregate_id=command.lead_id,
        )

    def register_attempt(
        self,
        command: AttemptCommand,
        *,
        actor_id: Any,
        actor_role: str,
        now: datetime,
        business_date: date,
    ) -> AttemptResult:
        return self._execute(
            ATTEMPT_COMMAND,
            command.idempotency_key,
            AttemptResult,
            now,
            lambda session, transaction_now: self._register_attempt(
                command, actor_id, actor_role, transaction_now, business_date, session
            ),
        )

    def register_outcome(
        self,
        command: OutcomeCommand,
        *,
        actor_id: Any,
        actor_role: str,
        now: datetime,
    ) -> OutcomeResult:
        return self._execute(
            OUTCOME_COMMAND,
            command.idempotency_key,
            OutcomeResult,
            now,
            lambda session, transaction_now: self._register_outcome(
                command, actor_id, actor_role, transaction_now, session
            ),
        )

    def _execute(
        self,
        command_name: str,
        idempotency_key: str,
        result_type: type[ResultT],
        now: datetime,
        operation: Callable[[Any, datetime], ResultT],
        *,
        actor_id: Any | None = None,
        aggregate_id: Any | None = None,
    ) -> ResultT:
        receipt = self._receipt(command_name, idempotency_key)
        if receipt is not None:
            return self._replay_result(
                receipt,
                result_type,
                actor_id=actor_id,
                aggregate_id=aggregate_id,
            )

        def callback(session: Any) -> ResultT:
            existing = self._receipt(command_name, idempotency_key, session=session)
            if existing is not None:
                return self._replay_result(
                    existing,
                    result_type,
                    actor_id=actor_id,
                    aggregate_id=aggregate_id,
                )
            # `now` is MongoDB server time captured once before the transaction.
            # Reusing it avoids the forbidden `hello` command inside a transaction
            # and gives retryable callbacks one stable timestamp.
            transaction_now = now
            result = operation(session, transaction_now)
            self._command_results.insert_one(
                {
                    "commandName": command_name,
                    "idempotencyKey": idempotency_key,
                    "result": result.to_document(),
                    "createdAt": transaction_now,
                    **({"actorId": actor_id} if actor_id is not None else {}),
                    **({"aggregateId": aggregate_id} if aggregate_id is not None else {}),
                },
                session=session,
            )
            return result

        try:
            with self._database.client.start_session() as session:
                return session.with_transaction(callback)
        except DuplicateKeyError:
            receipt = self._receipt(command_name, idempotency_key)
            if receipt is None:
                raise OperationsStateError("operation conflicted with a concurrent command") from None
            return self._replay_result(
                receipt,
                result_type,
                actor_id=actor_id,
                aggregate_id=aggregate_id,
            )

    @staticmethod
    def _replay_result(
        receipt: dict[str, Any],
        result_type: type[ResultT],
        *,
        actor_id: Any | None,
        aggregate_id: Any | None,
    ) -> ResultT:
        if actor_id is not None:
            if "actorId" not in receipt or "aggregateId" not in receipt:
                raise OperationsStateError("idempotency receipt lacks actor binding")
            if receipt["actorId"] != actor_id:
                raise OperationsPermissionError("idempotency receipt belongs to another actor")
            if receipt["aggregateId"] != aggregate_id:
                raise OperationsStateError("idempotency key belongs to another aggregate")
        return result_type.from_document(receipt["result"])

    def _receipt(
        self,
        command_name: str,
        idempotency_key: str,
        *,
        session: Any | None = None,
    ) -> dict[str, Any] | None:
        options = {} if session is None else {"session": session}
        receipt = self._command_results.find_one(
            {"idempotencyKey": idempotency_key}, **options
        )
        if receipt is not None and receipt.get("commandName") != command_name:
            raise OperationsStateError("idempotency key already belongs to another command")
        return receipt

    def _register_feedback(
        self,
        command: FeedbackCommand,
        actor_id: Any,
        actor_role: str,
        now: datetime,
        session: Any,
    ) -> FeedbackResult:
        lead = self._lead(command.lead_id, session)
        lead_before = deepcopy(lead)
        feedback_id = ObjectId()
        if command.administrative_note:
            if actor_role != "admin":
                raise OperationsStateError("administrative note requires admin")
            self._feedbacks.insert_one(
                {
                    "_id": feedback_id,
                    "leadId": command.lead_id,
                    "actorId": actor_id,
                    "comment": command.comment,
                    "kind": "administrative_note",
                    "createdAt": now,
                },
                session=session,
            )
            self._audit_log.insert_one(
                self._audit_document(
                    actor_id,
                    "lead.administrative_note_added",
                    command.lead_id,
                    command.idempotency_key,
                    {"lead": lead_before},
                    {
                        "lead": self._leads.find_one({"_id": command.lead_id}, session=session),
                        "feedbackId": feedback_id,
                    },
                    now,
                ),
                session=session,
            )
            return FeedbackResult(str(command.lead_id), str(feedback_id), "administrative_note")

        self._require_current_seller(lead, actor_id, actor_role)
        self._require_active(lead)
        self._feedbacks.insert_one(
            {
                "_id": feedback_id,
                "leadId": command.lead_id,
                "sellerId": actor_id,
                "comment": command.comment,
                "kind": "seller_feedback",
                "contactStarted": True,
                "createdAt": now,
            },
            session=session,
        )
        updated = self._leads.update_one(
            {"_id": command.lead_id},
            {"$set": {"updatedAt": now}},
            session=session,
        )
        if updated.matched_count != 1:
            raise OperationsStateError("lead changed concurrently")
        self._record_event(
            "lead.feedback_recorded",
            command.lead_id,
            actor_id,
            command.idempotency_key,
            {"lead": lead_before},
            {"lead": self._leads.find_one({"_id": command.lead_id}, session=session)},
            now,
            session,
        )
        return FeedbackResult(str(command.lead_id), str(feedback_id), "recorded")

    def _register_treatment(
        self,
        command: TreatmentCommand,
        actor_id: Any,
        actor_role: str,
        now: datetime,
        session: Any,
    ) -> TreatmentResult:
        lead = self._lead(command.lead_id, session)
        self._require_current_seller(lead, actor_id, actor_role)
        lead_before = deepcopy(lead)
        treatment_id = ObjectId()
        comment_count = int(lead.get("commentCount", 0)) + 1

        self._lead_treatments.insert_one(
            {
                "_id": treatment_id,
                "leadId": command.lead_id,
                "sellerId": actor_id,
                "comment": command.comment,
                "commercialStatus": command.commercial_status,
                "isDisqualified": command.is_disqualified,
                "idempotencyKey": command.idempotency_key,
                "createdAt": now,
            },
            session=session,
        )

        update: dict[str, Any] = {
            "commercialStatus": command.commercial_status,
            "isDisqualified": command.is_disqualified,
            "commentCount": comment_count,
            "lastCommentAt": now,
            "updatedAt": now,
        }
        changed = self._leads.update_one(
            {
                "_id": command.lead_id
            },
            {"$set": update},
            session=session,
        )
        if changed.matched_count != 1:
            raise OperationsStateError("lead changed concurrently")
        lead_after = self._leads.find_one({"_id": command.lead_id}, session=session)
        self._record_event(
            "lead.treatment_recorded",
            command.lead_id,
            actor_id,
            command.idempotency_key,
            {"lead": lead_before},
            {"lead": lead_after, "treatmentId": treatment_id},
            now,
            session,
        )
        return TreatmentResult(
            str(command.lead_id),
            str(treatment_id),
            "recorded",
            command.commercial_status,
            command.is_disqualified,
            comment_count,
            lead_after["updatedAt"],
        )

    def _register_attempt(
        self,
        command: AttemptCommand,
        actor_id: Any,
        actor_role: str,
        now: datetime,
        business_date: date,
        session: Any,
    ) -> AttemptResult:
        lead = self._lead(command.lead_id, session)
        lead_before = deepcopy(lead)
        self._require_current_seller(lead, actor_id, actor_role)
        self._require_active(lead)
        date_key = business_date.isoformat()
        if self._contact_attempts.find_one(
            {"leadId": command.lead_id, "businessDate": date_key}, session=session
        ) is not None:
            raise OperationsStateError("only one attempt may count on the same business date")
        attempts = self._contact_attempts.count_documents(
            {"leadId": command.lead_id}, session=session
        )
        if attempts >= 5:
            raise OperationsStateError("contact attempt limit is five")

        attempt_id = ObjectId()
        sequence = attempts + 1
        self._contact_attempts.insert_one(
            {
                "_id": attempt_id,
                "leadId": command.lead_id,
                "sellerId": actor_id,
                "channel": "whatsapp",
                "comment": command.comment,
                "businessDate": date_key,
                "sequence": sequence,
                "createdAt": now,
            },
            session=session,
        )
        self._audit_log.insert_one(
            self._audit_document(
                actor_id,
                "lead.contact_attempt_recorded",
                command.lead_id,
                command.idempotency_key,
                {"lead": lead_before},
                {"lead": self._leads.find_one({"_id": command.lead_id}, session=session), "attempt": {"attempts": sequence, "businessDate": date_key}},
                now,
            ),
            session=session,
        )
        return AttemptResult(
            str(command.lead_id),
            str(attempt_id),
            sequence,
            business_date,
            sequence == 5,
            "recorded",
        )

    def _register_outcome(
        self,
        command: OutcomeCommand,
        actor_id: Any,
        actor_role: str,
        now: datetime,
        session: Any,
    ) -> OutcomeResult:
        lead = self._lead(command.lead_id, session)
        lead_before = deepcopy(lead)
        if actor_role == "seller":
            self._require_current_seller(lead, actor_id, actor_role)
        elif actor_role != "admin":
            raise OperationsStateError("outcome actor is not authorized")
        self._require_active(lead)
        if command.disqualification_reason == "no_answer_after_5_attempts":
            attempts = self._contact_attempts.count_documents(
                {"leadId": command.lead_id}, session=session
            )
            if attempts < 5:
                raise OperationsStateError("no-answer disqualification requires five attempts")
        elif command.disqualification_reason == "outside_sp":
            if str(lead.get("state", "")).strip().upper() == "SP":
                raise OperationsStateError("outside SP reason requires a lead outside SP")
        elif command.disqualification_reason == "no_cnpj":
            company = self._companies.find_one({"_id": lead["companyId"]}, session=session)
            document = "" if company is None else str(company.get("documentNormalized", ""))
            if len(document) == 14:
                raise OperationsStateError("company already has CNPJ")

        outcome_event_id = ObjectId()
        qualification_status, conversion_status = self._statuses(command.outcome, lead)
        update: dict[str, Any] = {
            "qualificationStatus": qualification_status,
            "conversionStatus": conversion_status,
            "qualificationDecidedAt": now,
            "outcomeEventId": outcome_event_id,
            "updatedAt": now,
        }

        sale_id: ObjectId | None = None
        company_before = None
        if command.outcome == "won":
            company = self._companies.find_one({"_id": lead["companyId"]}, session=session)
            if company is None:
                raise OperationsStateError("lead company does not exist")
            company_before = deepcopy(company)
            sale_id = ObjectId()
            self._companies.update_one(
                {"_id": lead["companyId"], "clientSince": None},
                {"$set": {"clientSince": now, "updatedAt": now}},
                session=session,
            )
            self._sales.insert_one(
                {
                    "_id": sale_id,
                    "leadId": command.lead_id,
                    "creditedSellerId": lead["assigneeId"],
                    "wonAt": now,
                    "comment": command.comment,
                    "reversedAt": None,
                },
                session=session,
            )
            update["wonAt"] = now

        changed = self._leads.update_one(
            {
                "_id": command.lead_id
            },
            {"$set": update},
            session=session,
        )
        if changed.matched_count != 1:
            raise OperationsStateError("lead changed concurrently")
        self._qualification_events.insert_one(
            {
                "_id": outcome_event_id,
                "leadId": command.lead_id,
                "actorId": actor_id,
                "outcome": command.outcome,
                "reason": command.disqualification_reason,
                "comment": command.comment,
                "createdAt": now,
            },
            session=session,
        )
        self._record_event(
            self._event_type(command.outcome),
            command.lead_id,
            actor_id,
            command.idempotency_key,
            {"lead": lead_before, "company": company_before},
            {"lead": self._leads.find_one({"_id": command.lead_id}, session=session), "company": (self._companies.find_one({"_id": lead["companyId"]}, session=session) if company_before is not None else None), "outcomeEventId": outcome_event_id, "saleId": sale_id},
            now,
            session,
        )
        return OutcomeResult(
            str(command.lead_id),
            str(outcome_event_id),
            command.outcome,
            str(sale_id) if sale_id is not None else None,
            "recorded",
        )

    def _lead(self, lead_id: Any, session: Any) -> dict[str, Any]:
        lead = self._leads.find_one({"_id": lead_id}, session=session)
        if lead is None or lead.get("archivedAt") is not None:
            raise OperationsStateError("active lead does not exist")
        return lead

    @staticmethod
    def _require_current_seller(lead: dict[str, Any], actor_id: Any, actor_role: str) -> None:
        if actor_role != "seller" or lead.get("assigneeId") != actor_id:
            raise OperationsPermissionError("seller is not the current lead assignee")
        if lead.get("assignmentStatus") != "assigned":
            raise OperationsStateError("lead is not currently assigned")

    @staticmethod
    def _require_active(lead: dict[str, Any]) -> None:
        if lead.get("qualificationStatus") == "disqualified" or lead.get(
            "conversionStatus"
        ) in TERMINAL_CONVERSIONS:
            raise OperationsStateError("lead already has a final outcome")

    @staticmethod
    def _statuses(outcome: str, lead: dict[str, Any]) -> tuple[str, str]:
        if outcome == "qualified_follow_up":
            return "qualified", "qualified_follow_up"
        if outcome == "qualified_closed_no_conversion":
            return "qualified", "closed_no_conversion"
        if outcome == "disqualified":
            return "disqualified", str(lead.get("conversionStatus", "active"))
        return "qualified", "won"

    @staticmethod
    def _event_type(outcome: str) -> str:
        return {
            "qualified_follow_up": "lead.qualified",
            "qualified_closed_no_conversion": "lead.closed_without_conversion",
            "disqualified": "lead.disqualified",
            "won": "lead.won",
        }[outcome]

    @staticmethod
    def _audit_document(
        actor_id: Any,
        action: str,
        lead_id: Any,
        command_id: str,
        before: dict[str, Any],
        after: dict[str, Any],
        now: datetime,
    ) -> dict[str, Any]:
        return {
            "actorId": actor_id,
            "action": action,
            "entityType": "lead",
            "entityId": lead_id,
            "before": before,
            "after": after,
            "createdAt": now,
            "correlationId": command_id,
        }

    def _record_event(
        self,
        event_type: str,
        lead_id: Any,
        actor_id: Any,
        command_id: str,
        before: dict[str, Any],
        after: dict[str, Any],
        now: datetime,
        session: Any,
    ) -> None:
        self._audit_log.insert_one(
            self._audit_document(actor_id, event_type, lead_id, command_id, before, after, now),
            session=session,
        )
        self._notification_outbox.insert_one(
            {
                "_id": ObjectId(),
                "eventType": event_type,
                "aggregateId": lead_id,
                "actorId": actor_id,
                "idempotencyKey": f"{command_id}:{event_type}",
                "payload": after,
                "status": "pending",
                "attempts": 0,
                "createdAt": now,
            },
            session=session,
        )


    @property
    def _leads(self):
        return self._database[MongoCollections.LEADS]

    @property
    def _companies(self):
        return self._database[MongoCollections.COMPANIES]

    @property
    def _feedbacks(self):
        return self._database[MongoCollections.FEEDBACKS]

    @property
    def _contact_attempts(self):
        return self._database[MongoCollections.CONTACT_ATTEMPTS]

    @property
    def _qualification_events(self):
        return self._database[MongoCollections.QUALIFICATION_EVENTS]

    @property
    def _sales(self):
        return self._database[MongoCollections.SALES]

    @property
    def _notification_outbox(self):
        return self._database[MongoCollections.NOTIFICATION_OUTBOX]

    @property
    def _audit_log(self):
        return self._database[MongoCollections.AUDIT_LOG]

    @property
    def _command_results(self):
        return self._database[MongoCollections.COMMAND_RESULTS]

    @property
    def _lead_treatments(self):
        return self._database[MongoCollections.LEAD_TREATMENTS]
````

## Snapshot de código: `apps/api/src/gerec_api/infrastructure/mongo/queue_repository.py`

````python
"""MongoDB transaction adapter for queue rotation, ownership and skip credits."""

from __future__ import annotations

from datetime import UTC, datetime
from time import sleep
from typing import Any, Callable, TypeVar

from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from gerec_api.domain.queue import (
    AssignmentResult,
    QueueSnapshot,
    QueueRules,
    SellerAvailability,
    SellerState,
    TransferResult,
)
from gerec_api.infrastructure.mongo.collections import MongoCollections


NORMAL_COMMAND = "queue.distribute_normal"
READY_COMMAND = "queue.distribute_ready"
RECURRING_COMMAND = "queue.assign_recurring"
TEMPORARY_COMMAND = "queue.assign_temporarily"
TRANSFER_COMMAND = "queue.transfer_owner"
TRANSFER_LEAD_COMMAND = "queue.transfer_lead"
QUEUE_STATE_ID = "global"

ResultT = TypeVar("ResultT", AssignmentResult, TransferResult)


class QueueStateError(RuntimeError):
    """Raised when a queue command cannot preserve a domain invariant."""


class _FifoPredecessorPending(QueueStateError):
    """Allows a concurrent older lead a bounded window to commit first."""


class QueueRepository:
    """Commit every queue side effect in one retryable MongoDB transaction."""

    def __init__(
        self,
        database: Any,
        *,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._database = database
        self._now = now or (lambda: datetime.now(UTC))

    def distribute_normal(
        self, lead_id: Any, command_id: str, *, actor_id: Any
    ) -> AssignmentResult:
        pending_error: _FifoPredecessorPending | None = None
        for attempt in range(100):
            try:
                return self._execute(
                    NORMAL_COMMAND,
                    command_id,
                    AssignmentResult,
                    lambda session: self._distribute_normal(
                        lead_id, command_id, actor_id, session
                    ),
                )
            except _FifoPredecessorPending as error:
                pending_error = error
                if attempt < 99:
                    sleep(0.01)
        raise QueueStateError(str(pending_error))

    def snapshot(self) -> QueueSnapshot:
        queue_state = self._queue_state.find_one({"_id": QUEUE_STATE_ID})
        if queue_state is None:
            return QueueSnapshot(cursor_seller_id=None, entries=[])
        return QueueRules.snapshot(
            self._seller_states(self._now(), None), queue_state["nextSellerId"]
        )

    def distribute_ready(
        self, lead_id: Any, command_id: str, *, actor_id: Any
    ) -> AssignmentResult:
        return self._execute(
            READY_COMMAND,
            command_id,
            AssignmentResult,
            lambda session: self._distribute_ready(lead_id, command_id, actor_id, session),
        )

    def reconcile_pending(self, command_prefix: str, *, actor_id: Any) -> list[AssignmentResult]:
        """Retry unassigned FIFO leads after availability changes or a sync replay."""
        candidates = list(
            self._leads.find(
                {
                    "assignmentStatus": {"$in": ["ready", "parked"]},
                    "assigneeId": None,
                    "currentAssignmentId": None,
                    "archivedAt": None,
                }
            )
        )
        candidates = [
            lead
            for lead in candidates
            if lead.get("parkReason") in (None, "no_eligible_seller")
        ]
        candidates.sort(
            key=lambda lead: (
                lead.get("sourceEnteredAt") or datetime.max.replace(tzinfo=UTC),
                lead.get("sourceLeadId") or str(lead["_id"]),
            )
        )
        results: list[AssignmentResult] = []
        for lead in candidates:
            result = self.distribute_ready(
                lead["_id"], f"{command_prefix}:{lead['_id']}", actor_id=actor_id
            )
            if result.status == "parked" and result.assignment_type == "normal":
                break
            results.append(result)
        return results

    def assign_recurring(
        self, lead_id: Any, command_id: str, *, actor_id: Any
    ) -> AssignmentResult:
        return self._execute(
            RECURRING_COMMAND,
            command_id,
            AssignmentResult,
            lambda session: self._assign_recurring(lead_id, command_id, actor_id, session),
        )

    def assign_temporarily(
        self,
        lead_id: Any,
        seller_id: Any,
        reason: str,
        command_id: str,
        *,
        actor_id: Any,
    ) -> AssignmentResult:
        return self._execute(
            TEMPORARY_COMMAND,
            command_id,
            AssignmentResult,
            lambda session: self._assign_temporarily(
                lead_id,
                seller_id,
                reason,
                command_id,
                actor_id,
                session,
            ),
        )

    def transfer_owner(
        self,
        company_id: Any,
        seller_id: Any,
        reason: str,
        command_id: str,
        *,
        actor_id: Any,
    ) -> TransferResult:
        return self._execute(
            TRANSFER_COMMAND,
            command_id,
            TransferResult,
            lambda session: self._transfer_owner(
                company_id,
                seller_id,
                reason,
                command_id,
                actor_id,
                session,
            ),
        )

    def transfer_lead(
        self,
        lead_id: Any,
        seller_id: Any,
        reason: str,
        command_id: str,
        *,
        actor_id: Any,
    ) -> AssignmentResult:
        return self._execute(
            TRANSFER_LEAD_COMMAND,
            command_id,
            AssignmentResult,
            lambda session: self._transfer_lead(
                lead_id, seller_id, reason, command_id, actor_id, session
            ),
        )

    def _execute(
        self,
        command_name: str,
        command_id: str,
        result_type: type[ResultT],
        operation: Callable[[Any], ResultT],
    ) -> ResultT:
        receipt = self._receipt(command_name, command_id)
        if receipt is not None:
            return result_type.from_document(receipt["result"])

        def callback(session: Any) -> ResultT:
            existing = self._receipt(command_name, command_id, session=session)
            if existing is not None:
                return result_type.from_document(existing["result"])
            result = operation(session)
            self._command_results.insert_one(
                {
                    "commandName": command_name,
                    "idempotencyKey": command_id,
                    "result": result.to_document(),
                    "createdAt": self._now(),
                },
                session=session,
            )
            return result

        try:
            with self._database.client.start_session() as session:
                return session.with_transaction(callback)
        except DuplicateKeyError:
            receipt = self._receipt(command_name, command_id)
            if receipt is None:
                raise
            return result_type.from_document(receipt["result"])

    def _receipt(
        self,
        command_name: str,
        command_id: str,
        *,
        session: Any | None = None,
    ) -> dict[str, Any] | None:
        options = {} if session is None else {"session": session}
        receipt = self._command_results.find_one({"idempotencyKey": command_id}, **options)
        if receipt is not None and receipt.get("commandName") != command_name:
            raise QueueStateError("idempotency key already belongs to another command")
        return receipt

    def _distribute_normal(
        self,
        lead_id: Any,
        command_id: str,
        actor_id: Any,
        session: Any,
    ) -> AssignmentResult:
        now = self._now()
        lead = self._available_lead(lead_id, session)
        self._require_fifo(lead, session)
        queue_state = self._queue_state.find_one({"_id": QUEUE_STATE_ID}, session=session)
        if queue_state is None:
            raise QueueStateError("global queue state is not initialized")
        sellers = self._seller_states(now, session)
        decision = QueueRules.select_normal(sellers, queue_state["nextSellerId"])
        if (
            decision.seller_id is None
            and lead.get("assignmentStatus") == "parked"
            and lead.get("parkReason") == "no_eligible_seller"
        ):
            return AssignmentResult(
                lead_id=str(lead_id),
                assignment_id=None,
                seller_id=None,
                assignment_type="normal",
                status="parked",
                owner_id=self._owner_id(lead, session),
            )

        state_update = self._queue_state.update_one(
            {"_id": QUEUE_STATE_ID, "version": queue_state["version"]},
            {
                "$set": {"nextSellerId": decision.next_seller_id, "updatedAt": now},
                "$inc": {"version": 1},
            },
            session=session,
        )
        if state_update.matched_count != 1:
            raise QueueStateError("queue state changed concurrently")
        for credit_index, seller_id in enumerate(decision.consumed_credit_seller_ids):
            previous_balance = self._balance(seller_id, session)
            consumed = self._skip_balances.update_one(
                {"sellerId": seller_id, "balance": {"$gte": 1}},
                {"$inc": {"balance": -1}, "$set": {"updatedAt": now}},
                session=session,
            )
            if consumed.matched_count != 1:
                raise QueueStateError("skip balance changed concurrently")
            self._record_event(
                event_type="seller.skip_consumed",
                entity_type="seller",
                entity_id=seller_id,
                action="seller.skip_consumed",
                command_id=command_id,
                actor_id=actor_id,
                before={"balance": previous_balance},
                after={"balance": previous_balance - 1},
                now=now,
                session=session,
                event_key=f"{command_id}:seller.skip_consumed:{credit_index}",
            )

        if decision.seller_id is None:
            self._leads.update_one(
                {"_id": lead_id, "currentAssignmentId": None},
                {
                    "$set": {
                        "assignmentStatus": "parked",
                        "parkReason": "no_eligible_seller",
                        "updatedAt": now,
                    }
                },
                session=session,
            )
            result = AssignmentResult(
                lead_id=str(lead_id),
                assignment_id=None,
                seller_id=None,
                assignment_type=None,
                status="parked",
                owner_id=self._owner_id(lead, session),
            )
            self._record_event(
                event_type="lead.parked",
                entity_type="lead",
                entity_id=lead_id,
                action="queue.parked",
                command_id=command_id,
                actor_id=actor_id,
                before={"assignmentStatus": lead.get("assignmentStatus")},
                after={"assignmentStatus": "parked", "parkReason": "no_eligible_seller"},
                now=now,
                session=session,
            )
            return result

        return self._assign_effective(
            lead,
            decision.seller_id,
            "normal",
            None,
            command_id,
            actor_id,
            now,
            session,
        )

    def _distribute_ready(
        self,
        lead_id: Any,
        command_id: str,
        actor_id: Any,
        session: Any,
    ) -> AssignmentResult:
        lead = self._available_lead(lead_id, session)
        company = self._companies.find_one({"_id": lead["companyId"]}, session=session)
        if company is not None and company.get("ownerId") is not None:
            return self._assign_recurring(lead_id, command_id, actor_id, session)
        return self._distribute_normal(lead_id, command_id, actor_id, session)

    def _assign_recurring(
        self,
        lead_id: Any,
        command_id: str,
        actor_id: Any,
        session: Any,
    ) -> AssignmentResult:
        now = self._now()
        lead = self._available_lead(lead_id, session)
        company = self._companies.find_one({"_id": lead["companyId"]}, session=session)
        owner_id = None if company is None else company.get("ownerId")
        if owner_id is None:
            raise QueueStateError("recurring company does not have an owner")
        if self._seller_availability(owner_id, now, session).status != "active":
            self._leads.update_one(
                {"_id": lead_id, "currentAssignmentId": None},
                {
                    "$set": {
                        "assignmentStatus": "parked",
                        "parkReason": "owner_unavailable",
                        "updatedAt": now,
                    }
                },
                session=session,
            )
            result = AssignmentResult(
                lead_id=str(lead_id),
                assignment_id=None,
                seller_id=None,
                assignment_type="recurring",
                status="parked",
                owner_id=str(owner_id),
            )
            self._record_event(
                event_type="lead.parked",
                entity_type="lead",
                entity_id=lead_id,
                action="queue.recurring_parked",
                command_id=command_id,
                actor_id=actor_id,
                before={"assignmentStatus": lead.get("assignmentStatus")},
                after={"assignmentStatus": "parked", "parkReason": "owner_unavailable"},
                now=now,
                session=session,
            )
            return result
        self._credit(owner_id, command_id, actor_id, now, session)
        return self._assign_effective(
            lead,
            owner_id,
            "recurring",
            None,
            command_id,
            actor_id,
            now,
            session,
        )

    def _assign_temporarily(
        self,
        lead_id: Any,
        seller_id: Any,
        reason: str,
        command_id: str,
        actor_id: Any,
        session: Any,
    ) -> AssignmentResult:
        now = self._now()
        lead = self._available_lead(lead_id, session)
        if lead.get("assignmentStatus") != "parked" or lead.get("parkReason") != "owner_unavailable":
            raise QueueStateError("temporary assignment requires a recurring parked lead")
        company = self._companies.find_one({"_id": lead["companyId"]}, session=session)
        owner_id = None if company is None else company.get("ownerId")
        if owner_id is None:
            raise QueueStateError("temporary assignment requires a previous owner")
        if owner_id == seller_id:
            raise QueueStateError("temporary seller must differ from the company owner")
        if self._seller_availability(seller_id, now, session).status != "active":
            raise QueueStateError("temporary seller is not operational")
        self._credit(seller_id, command_id, actor_id, now, session)
        return self._assign_effective(
            lead,
            seller_id,
            "temporary",
            reason,
            command_id,
            actor_id,
            now,
            session,
        )

    def _transfer_owner(
        self,
        company_id: Any,
        seller_id: Any,
        reason: str,
        command_id: str,
        actor_id: Any,
        session: Any,
    ) -> TransferResult:
        now = self._now()
        company = self._companies.find_one({"_id": company_id}, session=session)
        if company is None:
            raise QueueStateError("company not found")
        user = self._users.find_one({"_id": seller_id, "active": True}, session=session)
        if user is None:
            raise QueueStateError("new owner is not an active seller")
        previous_owner_id = company.get("ownerId")
        self._companies.update_one(
            {"_id": company_id, "ownerId": previous_owner_id},
            {"$set": {"ownerId": seller_id, "updatedAt": now}},
            session=session,
        )
        self._record_event(
            event_type="company.owner_transferred",
            entity_type="company",
            entity_id=company_id,
            action="company.owner_transferred",
            command_id=command_id,
            actor_id=actor_id,
            before={"ownerId": previous_owner_id},
            after={"ownerId": seller_id},
            now=now,
            session=session,
            reason=reason,
        )
        return TransferResult(
            company_id=str(company_id),
            previous_owner_id=(str(previous_owner_id) if previous_owner_id is not None else None),
            owner_id=str(seller_id),
        )

    def _transfer_lead(
        self,
        lead_id: Any,
        seller_id: Any,
        reason: str,
        command_id: str,
        actor_id: Any,
        session: Any,
    ) -> AssignmentResult:
        now = self._now()
        lead = self._leads.find_one({"_id": lead_id, "archivedAt": None}, session=session)
        if lead is None or lead.get("assigneeId") is None:
            raise QueueStateError("assigned lead not found")
        if lead.get("assigneeId") == seller_id:
            raise QueueStateError("new seller must differ from current seller")
        user = self._users.find_one({"_id": seller_id, "active": True}, session=session)
        if user is None:
            raise QueueStateError("new seller is not active")
        current_assignment_id = lead.get("currentAssignmentId")
        if current_assignment_id is not None:
            ended = self._assignments.update_one(
                {"_id": current_assignment_id, "current": True},
                {"$set": {"current": False, "endedAt": now}},
                session=session,
            )
            if ended.matched_count != 1:
                raise QueueStateError("current assignment changed concurrently")
        cleared = self._leads.update_one(
            {"_id": lead_id, "currentAssignmentId": current_assignment_id},
            {"$set": {"currentAssignmentId": None}},
            session=session,
        )
        if cleared.matched_count != 1:
            raise QueueStateError("lead changed concurrently")
        result = self._assign_effective(
            lead,
            seller_id,
            "permanent_transfer",
            reason,
            command_id,
            actor_id,
            now,
            session,
        )
        self._record_event(
            event_type="lead.owner_transferred",
            entity_type="lead",
            entity_id=lead_id,
            action="lead.owner_transferred",
            command_id=command_id,
            actor_id=actor_id,
            before={"assigneeId": lead.get("assigneeId")},
            after={"assigneeId": seller_id},
            now=now,
            session=session,
            reason=reason,
        )
        return result

    def _assign_effective(
        self,
        lead: dict[str, Any],
        seller_id: Any,
        assignment_type: str,
        reason: str | None,
        command_id: str,
        actor_id: Any,
        now: datetime,
        session: Any,
    ) -> AssignmentResult:
        company = self._companies.find_one({"_id": lead["companyId"]}, session=session)
        if company is None:
            raise QueueStateError("lead company not found")
        owner_id = company.get("ownerId")
        if assignment_type == "temporary" and owner_id is None:
            raise QueueStateError("temporary assignment cannot claim company ownership")
        assignment = {
            "leadId": lead["_id"],
            "sellerId": seller_id,
            "type": assignment_type,
            "reason": reason,
            "current": True,
            "startedAt": now,
            "endedAt": None,
            "commandId": command_id,
        }
        assignment_id = self._assignments.insert_one(assignment, session=session).inserted_id
        assignment_sequence = self._next_assignment_sequence(session)
        lead_update = {
            "assignmentStatus": "assigned",
            "assigneeId": seller_id,
            "currentAssignmentId": assignment_id,
            "assignmentType": assignment_type,
            "parkReason": None,
            "assignedAt": now,
            "assignmentSequence": assignment_sequence,
            "updatedAt": now,
        }
        updated = self._leads.update_one(
            {"_id": lead["_id"], "currentAssignmentId": None},
            {"$set": lead_update},
            session=session,
        )
        if updated.matched_count != 1:
            raise QueueStateError("lead already has a current assignment")

        if owner_id is None:
            claimed = self._companies.update_one(
                {"_id": lead["companyId"], "ownerId": None},
                {"$set": {"ownerId": seller_id, "updatedAt": now}},
                session=session,
            )
            if claimed.matched_count == 1:
                owner_id = seller_id
            else:
                owner_id = self._companies.find_one(
                    {"_id": lead["companyId"]}, session=session
                ).get("ownerId")

        self._record_event(
            event_type="lead.assigned",
            entity_type="lead",
            entity_id=lead["_id"],
            action="queue.assigned",
            command_id=command_id,
            actor_id=actor_id,
            before={
                "assignmentStatus": lead.get("assignmentStatus"),
                "assigneeId": lead.get("assigneeId"),
            },
            after={
                "assignmentStatus": "assigned",
                "assigneeId": seller_id,
                "assignmentType": assignment_type,
            },
            now=now,
            session=session,
            reason=reason,
        )
        return AssignmentResult(
            lead_id=str(lead["_id"]),
            assignment_id=str(assignment_id),
            seller_id=str(seller_id),
            assignment_type=assignment_type,
            status="assigned",
            owner_id=str(owner_id) if owner_id is not None else None,
        )

    def _next_assignment_sequence(self, session: Any) -> int:
        state = self._queue_state.find_one_and_update(
            {"_id": QUEUE_STATE_ID},
            {"$inc": {"assignmentSequence": 1}},
            return_document=ReturnDocument.AFTER,
            session=session,
        )
        if state is None or not isinstance(state.get("assignmentSequence"), int):
            raise QueueStateError("global queue state is not initialized")
        return int(state["assignmentSequence"])

    def _seller_states(self, now: datetime, session: Any) -> list[SellerState]:
        queue_documents = sorted(
            self._seller_queue.find({}, session=session),
            key=lambda value: value["position"],
        )
        return [
            self._seller_state(item, now, session)
            for item in queue_documents
        ]

    def _seller_state(self, queue: dict[str, Any], now: datetime, session: Any) -> SellerState:
        seller_id = queue["sellerId"]
        return SellerState(
            seller_id=seller_id,
            active=self._users.find_one({"_id": seller_id, "active": True}, session=session)
            is not None,
            paused=bool(queue.get("paused", False)),
            skip_balance=self._balance(seller_id, session),
            position=int(queue["position"]),
        )

    def _seller_availability(
        self, seller_id: Any, now: datetime, session: Any
    ) -> SellerAvailability:
        queue = self._seller_queue.find_one({"sellerId": seller_id}, session=session)
        if queue is None:
            return SellerAvailability("paused", "Vendedor não participa da fila.")
        return QueueRules.availability(self._seller_state(queue, now, session))

    def _balance(self, seller_id: Any, session: Any) -> int:
        document = self._skip_balances.find_one({"sellerId": seller_id}, session=session)
        balance = 0 if document is None else int(document.get("balance", 0))
        if balance < 0:
            raise QueueStateError("skip balance cannot be negative")
        return balance

    def _credit(
        self,
        seller_id: Any,
        command_id: str,
        actor_id: Any,
        now: datetime,
        session: Any,
    ) -> None:
        previous_balance = self._balance(seller_id, session)
        self._skip_balances.update_one(
            {"sellerId": seller_id},
            {
                "$inc": {"balance": 1},
                "$set": {"updatedAt": now},
                "$setOnInsert": {"sellerId": seller_id},
            },
            upsert=True,
            session=session,
        )
        self._record_event(
            event_type="seller.skip_credited",
            entity_type="seller",
            entity_id=seller_id,
            action="seller.skip_credited",
            command_id=command_id,
            actor_id=actor_id,
            before={"balance": previous_balance},
            after={"balance": previous_balance + 1},
            now=now,
            session=session,
        )

    def _available_lead(self, lead_id: Any, session: Any) -> dict[str, Any]:
        lead = self._leads.find_one({"_id": lead_id, "archivedAt": None}, session=session)
        if lead is None:
            raise QueueStateError("lead not found")
        if lead.get("currentAssignmentId") is not None or lead.get("assigneeId") is not None:
            raise QueueStateError("lead already has a current assignment")
        if lead.get("assignmentStatus") not in {"ready", "parked"}:
            raise QueueStateError("lead is not ready for assignment")
        return lead

    def _require_fifo(self, lead: dict[str, Any], session: Any) -> None:
        candidates = []
        for candidate in self._leads.find(
            {
                "assignmentStatus": {"$in": ["ready", "parked"]},
                "assigneeId": None,
                "archivedAt": None,
            },
            session=session,
        ):
            if candidate.get("parkReason") not in (None, "no_eligible_seller"):
                continue
            candidates.append(candidate)
        if not candidates:
            return
        first = min(
            candidates,
            key=lambda value: (
                value.get("sourceEnteredAt") or datetime.max.replace(tzinfo=UTC),
                value.get("sourceLeadId") or str(value["_id"]),
            ),
        )
        if first["_id"] != lead["_id"]:
            raise _FifoPredecessorPending("normal lead would bypass FIFO order")

    def _owner_id(self, lead: dict[str, Any], session: Any) -> str | None:
        company = self._companies.find_one({"_id": lead["companyId"]}, session=session)
        owner_id = None if company is None else company.get("ownerId")
        return str(owner_id) if owner_id is not None else None

    def _record_event(
        self,
        *,
        event_type: str,
        entity_type: str,
        entity_id: Any,
        action: str,
        command_id: str,
        actor_id: Any,
        before: dict[str, Any],
        after: dict[str, Any],
        now: datetime,
        session: Any,
        reason: str | None = None,
        event_key: str | None = None,
    ) -> None:
        self._audit_log.insert_one(
            {
                "actorId": actor_id,
                "action": action,
                "entityType": entity_type,
                "entityId": entity_id,
                "before": before,
                "after": after,
                "reason": reason,
                "createdAt": now,
                "correlationId": command_id,
            },
            session=session,
        )
        self._notification_outbox.insert_one(
            {
                "eventType": event_type,
                "aggregateId": entity_id,
                "actorId": actor_id,
                "idempotencyKey": event_key or f"{command_id}:{event_type}",
                "status": "pending",
                "attempts": 0,
                "payload": after,
                "createdAt": now,
            },
            session=session,
        )

    @property
    def _users(self):
        return self._database[MongoCollections.USERS]

    @property
    def _seller_queue(self):
        return self._database[MongoCollections.SELLER_QUEUE]

    @property
    def _queue_state(self):
        return self._database[MongoCollections.QUEUE_STATE]

    @property
    def _skip_balances(self):
        return self._database[MongoCollections.SKIP_BALANCES]

    @property
    def _companies(self):
        return self._database[MongoCollections.COMPANIES]

    @property
    def _leads(self):
        return self._database[MongoCollections.LEADS]

    @property
    def _assignments(self):
        return self._database[MongoCollections.ASSIGNMENTS]

    @property
    def _audit_log(self):
        return self._database[MongoCollections.AUDIT_LOG]

    @property
    def _notification_outbox(self):
        return self._database[MongoCollections.NOTIFICATION_OUTBOX]

    @property
    def _command_results(self):
        return self._database[MongoCollections.COMMAND_RESULTS]
````

## Snapshot de código: `apps/api/src/gerec_api/infrastructure/mongo/serialization.py`

````python
"""JSON-safe projection for values returned by PyMongo."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from bson import ObjectId


def serialize_bson(value: Any) -> Any:
    """Recursively stringify BSON identifiers while preserving JSON-native values."""
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): serialize_bson(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [serialize_bson(item) for item in value]
    return value
````

## Snapshot de código: `apps/api/src/gerec_api/infrastructure/mongo/user_repository.py`

````python
"""Transactional MongoDB persistence for administrative user commands."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Callable

from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from gerec_api.auth.sessions import revoke_sessions_for_user
from gerec_api.domain.user_administration import (
    CreateUserCommand,
    ManagedUser,
    UserAdministrationError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from gerec_api.infrastructure.mongo.collections import MongoCollections


QUEUE_STATE_ID = "global"


class _ConcurrentQueueChange(UserAdministrationError):
    """Abort a transaction whose queue version changed before the insert committed."""


class UserRepository:
    """Keep user, queue, audit and session changes inside one Mongo transaction."""

    def __init__(self, database: Any, *, now: Callable[[], datetime] | None = None) -> None:
        self._database = database
        self._now = now or (lambda: datetime.now(UTC))

    def create_user(
        self,
        command: CreateUserCommand,
        *,
        password_hash: str,
        actor_id: Any,
    ) -> ManagedUser:
        for _ in range(3):
            try:
                return self._run_transaction(
                    lambda session: self._create_user(command, password_hash, actor_id, session)
                )
            except _ConcurrentQueueChange:
                continue
            except DuplicateKeyError as error:
                if self._users.find_one({"emailNormalized": command.email}) is not None:
                    raise UserAlreadyExistsError("email is already registered") from error
                raise
        raise UserAdministrationError("queue changed concurrently; retry user creation")

    def set_manual_pause(
        self, user_id: Any, *, paused: bool, actor_id: Any
    ) -> ManagedUser:
        return self._run_transaction(
            lambda session: self._set_manual_pause(user_id, paused, actor_id, session)
        )

    def reset_password(self, user_id: Any, *, password_hash: str, actor_id: Any) -> ManagedUser:
        return self._run_transaction(
            lambda session: self._reset_password(user_id, password_hash, actor_id, session)
        )

    def _create_user(
        self,
        command: CreateUserCommand,
        password_hash: str,
        actor_id: Any,
        session: Any,
    ) -> ManagedUser:
        if self._users.find_one({"emailNormalized": command.email}, session=session) is not None:
            raise UserAlreadyExistsError("email is already registered")
        now = self._aware_now()
        user_id = ObjectId()
        document = {
            "_id": user_id,
            "fullName": command.full_name,
            "emailNormalized": command.email,
            "passwordHash": password_hash,
            "role": command.role,
            "active": True,
            "createdAt": now,
            "updatedAt": now,
        }
        if command.role == "seller":
            document["newLeadsSeenAt"] = now
            state = self._queue_state.find_one({"_id": QUEUE_STATE_ID}, session=session)
            document["newLeadsSeenAssignmentSequence"] = int((state or {}).get("assignmentSequence", 0))
        self._users.insert_one(document, session=session)
        paused: bool | None = None
        if command.role == "seller":
            position = self._append_seller(user_id, now, session)
            paused = False
            self._seller_queue.insert_one(
                {
                    "sellerId": user_id,
                    "position": position,
                    "paused": False,
                    "createdAt": now,
                    "updatedAt": now,
                },
                session=session,
            )
            self._skip_balances.update_one(
                {"sellerId": user_id},
                {
                    "$setOnInsert": {
                        "sellerId": user_id,
                        "balance": 0,
                        "createdAt": now,
                    },
                    "$set": {"updatedAt": now},
                },
                upsert=True,
                session=session,
            )
        result = ManagedUser(
            id=str(user_id),
            full_name=command.full_name,
            email=command.email,
            role=command.role,
            active=True,
            paused=paused,
        )
        self._audit(
            action="user.created",
            actor_id=actor_id,
            entity_id=user_id,
            before=None,
            after=result.to_public(),
            now=now,
            session=session,
        )
        return result

    def _set_manual_pause(
        self, user_id: Any, paused: bool, actor_id: Any, session: Any
    ) -> ManagedUser:
        user = self._user_or_error(user_id, session)
        if user.get("role") != "seller":
            raise UserAdministrationError("only sellers have manual availability")
        queue = self._seller_queue.find_one({"sellerId": user["_id"]}, session=session)
        if queue is None:
            raise UserAdministrationError("seller is not in the queue")
        now = self._aware_now()
        self._seller_queue.update_one(
            {"_id": queue["_id"]},
            {"$set": {"paused": paused, "updatedAt": now}},
            session=session,
        )
        result = _managed_user(user, paused=paused)
        self._audit(
            action="user.availability_changed",
            actor_id=actor_id,
            entity_id=user["_id"],
            before={"paused": bool(queue.get("paused", False))},
            after={"paused": paused},
            now=now,
            session=session,
        )
        return result

    def _reset_password(
        self, user_id: Any, password_hash: str, actor_id: Any, session: Any
    ) -> ManagedUser:
        user = self._user_or_error(user_id, session)
        now = self._aware_now()
        self._users.update_one(
            {"_id": user["_id"]},
            {"$set": {"passwordHash": password_hash, "updatedAt": now}},
            session=session,
        )
        revoke_sessions_for_user(self._sessions, user["_id"], now=now, session=session)
        queue = self._seller_queue.find_one({"sellerId": user["_id"]}, session=session)
        result = _managed_user(user, paused=(bool(queue.get("paused", False)) if queue else None))
        self._audit(
            action="user.password_reset",
            actor_id=actor_id,
            entity_id=user["_id"],
            before={"passwordChanged": False},
            after={"passwordChanged": True},
            now=now,
            session=session,
        )
        return result

    def _append_seller(self, user_id: ObjectId, now: datetime, session: Any) -> int:
        """Reserve a final queue position while holding the queue-state version."""
        state = self._queue_state.find_one({"_id": QUEUE_STATE_ID}, session=session)
        entries = self._seller_queue.find({}, session=session)
        positions = [
            int(entry["position"])
            for entry in entries
            if isinstance(entry.get("position"), int) and not isinstance(entry["position"], bool)
        ]
        position = max(positions, default=0) + 1
        if state is None:
            self._queue_state.insert_one(
                {
                    "_id": QUEUE_STATE_ID,
                    "nextSellerId": user_id,
                    "version": 0,
                    "assignmentSequence": 0,
                    "createdAt": now,
                    "updatedAt": now,
                },
                session=session,
            )
            return position
        updated = self._queue_state.update_one(
            {"_id": QUEUE_STATE_ID, "version": state.get("version", 0)},
            {"$set": {"updatedAt": now}, "$inc": {"version": 1}},
            session=session,
        )
        if updated.matched_count != 1:
            raise _ConcurrentQueueChange("queue changed while appending seller")
        return position

    def _user_or_error(self, user_id: Any, session: Any) -> dict[str, Any]:
        candidate_ids = [user_id]
        if isinstance(user_id, str) and ObjectId.is_valid(user_id):
            candidate_ids.append(ObjectId(user_id))
        for candidate in candidate_ids:
            user = self._users.find_one({"_id": candidate}, session=session)
            if user is not None:
                return user
        raise UserNotFoundError("user not found")

    def _run_transaction(self, callback: Callable[[Any], ManagedUser]) -> ManagedUser:
        with self._database.client.start_session() as session:
            return session.with_transaction(callback)

    def _audit(
        self,
        *,
        action: str,
        actor_id: Any,
        entity_id: Any,
        before: dict[str, Any] | None,
        after: dict[str, Any],
        now: datetime,
        session: Any,
    ) -> None:
        self._audit_log.insert_one(
            {
                "actorId": actor_id,
                "action": action,
                "entityType": "user",
                "entityId": entity_id,
                "before": before,
                "after": after,
                "createdAt": now,
            },
            session=session,
        )

    def _aware_now(self) -> datetime:
        value = self._now()
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)

    @property
    def _users(self):
        return self._database[MongoCollections.USERS]

    @property
    def _seller_queue(self):
        return self._database[MongoCollections.SELLER_QUEUE]

    @property
    def _queue_state(self):
        return self._database[MongoCollections.QUEUE_STATE]

    @property
    def _skip_balances(self):
        return self._database[MongoCollections.SKIP_BALANCES]

    @property
    def _sessions(self):
        return self._database[MongoCollections.SESSIONS]

    @property
    def _audit_log(self):
        return self._database[MongoCollections.AUDIT_LOG]


def _managed_user(user: dict[str, Any], *, paused: bool | None) -> ManagedUser:
    role = str(user.get("role", "seller"))
    if role not in {"admin", "seller"}:
        raise UserAdministrationError("user role is invalid")
    return ManagedUser(
        id=str(user["_id"]),
        full_name=str(user.get("fullName") or user.get("name") or user["emailNormalized"]),
        email=str(user["emailNormalized"]),
        role=role,  # type: ignore[arg-type]
        active=bool(user.get("active", True)),
        paused=paused,
    )
````

## Snapshot de código: `apps/api/src/gerec_api/main.py`

````python
"""Ponto de entrada da API HTTP."""

from typing import Any

from fastapi import FastAPI, Request

from gerec_api.auth.sessions import AuthService
from gerec_api.auth.permissions import DashboardService
from gerec_api.config import Settings
from gerec_api.domain.business_time import BusinessClock, MongoHolidayRepository
from gerec_api.domain.leads import LeadService
from gerec_api.domain.lead_notifications import LeadNotificationService
from gerec_api.domain.operations import OperationsService
from gerec_api.domain.queue import QueueService
from gerec_api.domain.user_administration import UserAdministrationService
from gerec_api.infrastructure.mongo.client import MongoClientFactory
from gerec_api.infrastructure.mongo import bootstrap
from gerec_api.infrastructure.mongo.clock import MongoClock
from gerec_api.infrastructure.mongo.collections import MongoCollections
from gerec_api.infrastructure.mongo.lead_repository import LeadRepository
from gerec_api.infrastructure.mongo.lead_notification_repository import MongoLeadNotificationRepository
from gerec_api.infrastructure.mongo.operations_repository import MongoOperationsRepository
from gerec_api.infrastructure.mongo.queue_repository import QueueRepository
from gerec_api.infrastructure.mongo.user_repository import UserRepository
from gerec_api.routes.auth import router as auth_router
from gerec_api.routes.leads import router as leads_router
from gerec_api.routes.operations import router as operations_router
from gerec_api.routes.queue import router as queue_router
from gerec_api.routes.dashboard import router as dashboard_router
from gerec_api.routes.admin import router as admin_router
from gerec_api.routes.lead_notifications import router as lead_notifications_router
from gerec_api.routes.reports import router as reports_router


API_CONTRACT_VERSION = "1"


def create_app(
    *,
    settings: Settings | None = None,
    database: Any | None = None,
    auth_service: AuthService | None = None,
) -> FastAPI:
    """Create the HTTP app with a lazily connected MongoDB handle and auth service."""
    settings = settings or Settings.from_env()
    owns_database = database is None
    if owns_database:
        database = MongoClientFactory.create(settings)
        bootstrap.ensure_schema(database)
    app = FastAPI(title="Gerenciador de Leads WTG API")
    app.state.settings = settings
    app.state.schema_ready = True
    app.state.database = database
    app.state.auth_service = auth_service if auth_service is not None else AuthService(database)
    app.state.dashboard_service = DashboardService(database)
    app.state.lead_service = LeadService(LeadRepository(database))
    database_clock = MongoClock(database)
    app.state.lead_notification_service = LeadNotificationService(
        MongoLeadNotificationRepository(database),
        signing_key=settings.app_secret.get_secret_value(),
        now=database_clock.now,
    )
    business_clock = BusinessClock(
        MongoHolidayRepository(database[MongoCollections.HOLIDAYS])
    )
    app.state.queue_service = QueueService(
        QueueRepository(database)
    )
    app.state.operations_service = OperationsService(
        MongoOperationsRepository(
            database,
            clock=database_clock,
        ),
        business_clock=business_clock,
        clock=database_clock,
    )
    app.state.user_administration_service = UserAdministrationService(
        UserRepository(database)
    )

    @app.middleware("http")
    async def add_contract_version(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Gerec-API-Contract-Version"] = API_CONTRACT_VERSION
        return response

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "database": settings.mongodb_database}

    app.include_router(auth_router)
    app.include_router(leads_router)
    app.include_router(queue_router)
    app.include_router(operations_router)
    app.include_router(dashboard_router)
    app.include_router(admin_router)
    app.include_router(lead_notifications_router)
    app.include_router(reports_router)
    return app
````

## Snapshot de código: `apps/api/src/gerec_api/routes/__init__.py`

````python
"""HTTP route modules for the backend API."""
````

## Snapshot de código: `apps/api/src/gerec_api/routes/admin.py`

````python
"""Administrative read endpoints and thin user-command HTTP boundaries."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from gerec_api.auth.dependencies import get_current_user
from gerec_api.auth.permissions import PermissionDenied, PermissionService
from gerec_api.auth.sessions import CurrentUser
from gerec_api.infrastructure.mongo.collections import MongoCollections
from gerec_api.infrastructure.mongo.serialization import serialize_bson
from gerec_api.domain.user_administration import (
    CreateUserCommand,
    ManagedUser,
    UserAdministrationError,
    UserAdministrationService,
    UserAlreadyExistsError,
    UserNotFoundError,
)


router = APIRouter(prefix="/api/admin", tags=["admin"])
SENSITIVE_FIELDS = frozenset({"passwordHash", "tokenHash"})


def _admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    try:
        PermissionService.require_admin(user)
    except PermissionDenied as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden") from error
    return user


class CreateUserRequest(BaseModel):
    full_name: str = Field(alias="fullName", min_length=1, max_length=200)
    email: str = Field(min_length=1, max_length=320)
    role: str
    password: str


class AvailabilityRequest(BaseModel):
    paused: bool


class PasswordResetRequest(BaseModel):
    password: str


class ManagedUserResponse(BaseModel):
    id: str
    full_name: str = Field(alias="fullName")
    email: str
    role: str
    active: bool
    paused: bool | None = None

    model_config = {"populate_by_name": True}


def _user_administration_service(request: Request) -> UserAdministrationService:
    service = getattr(request.app.state, "user_administration_service", None)
    if not isinstance(service, UserAdministrationService):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="User administration unavailable",
        )
    return service


def _response(user: ManagedUser) -> ManagedUserResponse:
    return ManagedUserResponse.model_validate(user.to_public())


def _command_error(error: UserAdministrationError | ValueError) -> HTTPException:
    if isinstance(error, UserAlreadyExistsError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    if isinstance(error, UserNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error))


def _page(request: Request, current_user: CurrentUser, collection_name: str, query: dict[str, Any], page: int, limit: int) -> dict[str, Any]:
    PermissionService.require_admin(current_user)
    if query is None:
        raise PermissionDenied("scoped query is required")
    collection = request.app.state.database[collection_name]
    cursor = collection.find(query)
    if hasattr(cursor, "sort"):
        cursor = cursor.sort("createdAt", -1)
    if hasattr(cursor, "limit"):
        cursor = cursor.skip((page - 1) * limit).limit(limit)
    items = []
    for item in cursor:
        item = dict(item)
        if "_id" in item:
            item["id"] = str(item.pop("_id"))
        for field in SENSITIVE_FIELDS:
            item.pop(field, None)
        items.append(serialize_bson(item))
    total = collection.count_documents(query) if hasattr(collection, "count_documents") else len(items)
    return {"items": items, "page": page, "pageSize": limit, "total": total}


@router.get("/users")
def users(request: Request, current_user: CurrentUser = Depends(_admin), page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=200)) -> dict[str, Any]:
    return _page(request, current_user, MongoCollections.USERS, PermissionService.scope_query(current_user, "users"), page, limit)


@router.post("/users", response_model=ManagedUserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: CreateUserRequest,
    request: Request,
    current_user: CurrentUser = Depends(_admin),
) -> ManagedUserResponse:
    try:
        user = _user_administration_service(request).with_actor(current_user.id).create_user(
            CreateUserCommand(payload.full_name, payload.email, payload.role, payload.password)
        )
    except (UserAdministrationError, ValueError) as error:
        raise _command_error(error) from error
    return _response(user)


@router.patch("/users/{user_id}/availability", response_model=ManagedUserResponse)
def set_user_availability(
    user_id: str,
    payload: AvailabilityRequest,
    request: Request,
    current_user: CurrentUser = Depends(_admin),
) -> ManagedUserResponse:
    try:
        user = _user_administration_service(request).with_actor(current_user.id).set_manual_pause(
            user_id, payload.paused
        )
    except (UserAdministrationError, ValueError) as error:
        raise _command_error(error) from error
    return _response(user)


@router.patch("/users/{user_id}/password", response_model=ManagedUserResponse)
def reset_user_password(
    user_id: str,
    payload: PasswordResetRequest,
    request: Request,
    current_user: CurrentUser = Depends(_admin),
) -> ManagedUserResponse:
    try:
        user = _user_administration_service(request).with_actor(current_user.id).reset_password(
            user_id, payload.password
        )
    except (UserAdministrationError, ValueError) as error:
        raise _command_error(error) from error
    return _response(user)


@router.get("/audit")
def audit(request: Request, current_user: CurrentUser = Depends(_admin), page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=200)) -> dict[str, Any]:
    return _page(request, current_user, MongoCollections.AUDIT_LOG, PermissionService.scope_query(current_user, "audit"), page, limit)
````

## Snapshot de código: `apps/api/src/gerec_api/routes/auth.py`

````python
"""HTTP endpoints for login, logout, and current-session identity."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from gerec_api.auth.dependencies import SESSION_COOKIE_NAME, get_auth_service, get_current_user
from gerec_api.auth.sessions import AuthService, CurrentUser, InvalidCredentialsError, SESSION_DURATION


router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str = Field(min_length=1, max_length=320)
    password: str = Field(min_length=1, max_length=1024)


class CurrentUserResponse(BaseModel):
    id: str
    email: str
    role: str


class LoginResponse(BaseModel):
    user: CurrentUserResponse


def _public_user(user: CurrentUser) -> CurrentUserResponse:
    return CurrentUserResponse(id=user.id, email=user.email, role=user.role)


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    """Set a secure HTTP-only cookie after a successful credentials check."""
    try:
        result = service.login(payload.email, payload.password)
    except InvalidCredentialsError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        ) from error

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=result.raw_token,
        max_age=int(SESSION_DURATION.total_seconds()),
        expires=result.expires_at,
        path="/",
        secure=True,
        httponly=True,
        samesite="lax",
    )
    return LoginResponse(user=_public_user(result.user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response, service: AuthService = Depends(get_auth_service)) -> None:
    """Revoke the server session and remove the browser cookie, even if it is already invalid."""
    raw_token = request.cookies.get(SESSION_COOKIE_NAME)
    if raw_token:
        service.logout(raw_token)
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
        secure=True,
        httponly=True,
        samesite="lax",
    )


@router.get("/me", response_model=CurrentUserResponse)
def me(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUserResponse:
    """Return only the public identity associated with the active session."""
    return _public_user(current_user)
````

## Snapshot de código: `apps/api/src/gerec_api/routes/dashboard.py`

````python
"""Authenticated, paginated dashboard read endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from gerec_api.auth.dependencies import get_current_user
from gerec_api.auth.permissions import DashboardService, PermissionDenied
from gerec_api.auth.sessions import CurrentUser


router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def get_dashboard_service(request: Request) -> DashboardService:
    service = getattr(request.app.state, "dashboard_service", None)
    if not isinstance(service, DashboardService):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Dashboard service unavailable")
    return service


@router.get("")
def dashboard(
    current_user: CurrentUser = Depends(get_current_user),
    service: DashboardService = Depends(get_dashboard_service),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    assignee_id: str | None = Query(None, alias="assigneeId"),
    sort: str | None = Query(None),
) -> dict[str, Any]:
    try:
        return service.for_user(
            current_user,
            page=page,
            limit=limit,
            assignee_id=assignee_id,
            sort=sort,
        )
    except PermissionDenied as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden") from error
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
````

## Snapshot de código: `apps/api/src/gerec_api/routes/lead_notifications.py`

````python
"""Seller-only HTTP boundaries for internal new-lead notification windows."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from gerec_api.auth.dependencies import SESSION_COOKIE_NAME, get_current_user
from gerec_api.auth.sessions import CurrentUser
from gerec_api.domain.lead_notifications import LeadNotificationService
from gerec_api.infrastructure.mongo.lead_notification_repository import LeadNotificationStateError


router = APIRouter(tags=["lead-notifications"])


class AcknowledgeNewLeadNotificationsRequest(BaseModel):
    watermark: datetime
    acknowledgement_token: str = Field(alias="acknowledgementToken", min_length=1, max_length=200)
    watermark_sequence: int = Field(alias="watermarkSequence", ge=0)


def get_lead_notification_service(request: Request) -> LeadNotificationService:
    service = getattr(request.app.state, "lead_notification_service", None)
    if not isinstance(service, LeadNotificationService):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Lead notification service unavailable",
        )
    return service


@router.get("/api/lead-notifications/new")
def new_lead_notifications(
    request: Request,
    service: LeadNotificationService = Depends(get_lead_notification_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, object]:
    return _snapshot(service, current_user, _session_token(request))


@router.post("/api/lead-notifications/new/acknowledge")
def acknowledge_new_lead_notifications(
    request: Request,
    payload: AcknowledgeNewLeadNotificationsRequest,
    service: LeadNotificationService = Depends(get_lead_notification_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, str]:
    _require_seller(current_user)
    try:
        watermark = service.acknowledge(
            current_user,
            payload.watermark,
            payload.acknowledgement_token,
            _session_token(request),
            payload.watermark_sequence,
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    except LeadNotificationStateError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    return {"watermark": watermark.isoformat()}


def _snapshot(
    service: LeadNotificationService,
    current_user: CurrentUser,
    session_token: str,
) -> dict[str, object]:
    _require_seller(current_user)
    try:
        return service.for_seller(current_user, session_token).to_document()
    except LeadNotificationStateError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


def _require_seller(user: CurrentUser) -> None:
    if user.role != "seller":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


def _session_token(request: Request) -> str:
    return request.cookies.get(SESSION_COOKIE_NAME, "")
````

## Snapshot de código: `apps/api/src/gerec_api/routes/leads.py`

````python
"""Internal authenticated routes for source-row ingestion and snapshot finalization."""

from dataclasses import replace
from hmac import compare_digest
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from gerec_api.auth.dependencies import get_current_user
from gerec_api.auth.permissions import DashboardService, PermissionDenied
from gerec_api.auth.sessions import CurrentUser
from gerec_api.domain.leads import LeadService
from gerec_api.domain.normalization import normalize_source_row


router = APIRouter(tags=["lead-imports", "lead-read"])
internal_router = APIRouter(prefix="/api/internal/imports/google-sheets", tags=["lead-imports"])


class SyncRequest(BaseModel):
    source_snapshot_id: str = Field(min_length=1, max_length=200)
    idempotency_key: str = Field(min_length=1, max_length=200)
    rows: list[dict[str, Any]]


def get_lead_service(request: Request) -> LeadService:
    service = getattr(request.app.state, "lead_service", None)
    if not isinstance(service, LeadService):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Lead import service unavailable",
        )
    return service


def require_internal_key(
    request: Request,
    x_internal_key: str = Header(alias="X-Internal-Key"),
) -> None:
    expected = request.app.state.settings.app_secret.get_secret_value()
    if not compare_digest(x_internal_key, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")


@internal_router.post("/sync", dependencies=[Depends(require_internal_key)])
def sync_rows(
    payload: SyncRequest,
    service: LeadService = Depends(get_lead_service),
) -> dict[str, Any]:
    """Import every row before finalizing the complete snapshot and archiving absences."""
    results = []
    for raw_row in payload.rows:
        row = replace(
            normalize_source_row(raw_row),
            source_snapshot_id=payload.source_snapshot_id,
        )
        results.append(
            service.import_row(
                row,
                f"{payload.idempotency_key}:{row.source_lead_id}",
            ).to_document()
        )
    archive = service.archive_missing(payload.source_snapshot_id)
    return {"rows": results, "archive": archive.to_document()}


def get_dashboard_service(request: Request) -> DashboardService:
    service = getattr(request.app.state, "dashboard_service", None)
    if not isinstance(service, DashboardService):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Operational read model unavailable",
        )
    return service


@router.get("/api/leads/{lead_id}/treatments")
def lead_treatments(
    lead_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: DashboardService = Depends(get_dashboard_service),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
) -> dict[str, Any]:
    """Return immutable treatments visible to the authenticated role only."""
    try:
        return service.lead_treatments_for_user(lead_id, current_user, page=page, limit=limit)
    except PermissionDenied as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden") from error


router.include_router(internal_router)
````

## Snapshot de código: `apps/api/src/gerec_api/routes/operations.py`

````python
"""HTTP boundaries for seller operational commands."""

from datetime import date
from typing import Any, Callable, Literal

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from gerec_api.auth.dependencies import get_current_user
from gerec_api.auth.sessions import CurrentUser
from gerec_api.domain.operations import (
    AttemptCommand,
    FeedbackCommand,
    OperationsService,
    OutcomeCommand,
    TreatmentCommand,
)
from gerec_api.infrastructure.mongo.operations_repository import OperationsStateError


router = APIRouter(tags=["operations"])


class FeedbackRequest(BaseModel):
    comment: str = Field(min_length=1, max_length=2_000)
    contact_started: bool
    idempotency_key: str = Field(min_length=1, max_length=200)


class AttemptRequest(BaseModel):
    comment: str = Field(min_length=1, max_length=2_000)
    idempotency_key: str = Field(min_length=1, max_length=200)
    business_date: date | None = None


class OutcomeRequest(BaseModel):
    outcome: str
    comment: str = Field(min_length=1, max_length=2_000)
    idempotency_key: str = Field(min_length=1, max_length=200)
    disqualification_reason: str | None = None
    response_confirmed: bool = False


class TreatmentRequest(BaseModel):
    comment: str = Field(min_length=6, max_length=2_000)
    commercial_status: Literal["undefined", "potential", "negotiation", "won"] = Field(
        alias="commercialStatus"
    )
    is_disqualified: bool = Field(alias="isDisqualified")
    idempotency_key: str = Field(alias="idempotencyKey", min_length=1, max_length=200)


def get_operations_service(request: Request) -> OperationsService:
    service = getattr(request.app.state, "operations_service", None)
    if not isinstance(service, OperationsService):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Operations service unavailable",
        )
    return service


@router.post("/api/leads/{lead_id}/feedbacks")
def register_feedback(
    lead_id: str,
    payload: FeedbackRequest,
    service: OperationsService = Depends(get_operations_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    return _run(
        lambda: service.with_actor(_object_id(current_user.id), current_user.role).register_feedback(
            FeedbackCommand(
                _object_id(lead_id),
                payload.comment,
                payload.contact_started,
                payload.idempotency_key,
            )
        )
    )


@router.post("/api/leads/{lead_id}/attempts")
def register_attempt(
    lead_id: str,
    payload: AttemptRequest,
    service: OperationsService = Depends(get_operations_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    return _run(
        lambda: service.with_actor(_object_id(current_user.id), current_user.role).register_attempt(
            AttemptCommand(
                _object_id(lead_id),
                payload.comment,
                payload.idempotency_key,
                payload.business_date,
            )
        )
    )


@router.post(
    "/api/leads/{lead_id}/treatments",
    status_code=status.HTTP_201_CREATED,
)
def register_treatment(
    lead_id: str,
    payload: TreatmentRequest,
    service: OperationsService = Depends(get_operations_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    """Record the current seller's immutable commercial treatment only."""
    if current_user.role != "seller":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return _run_treatment(
        lambda: service.with_actor(
            _object_id(current_user.id), current_user.role
        ).register_treatment(
            TreatmentCommand(
                _object_id(lead_id),
                payload.comment,
                payload.commercial_status,
                payload.is_disqualified,
                payload.idempotency_key,
            )
        )
    )


@router.post("/api/leads/{lead_id}/outcome")
def register_outcome(
    lead_id: str,
    payload: OutcomeRequest,
    service: OperationsService = Depends(get_operations_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    return _run(
        lambda: service.with_actor(_object_id(current_user.id), current_user.role).register_outcome(
            OutcomeCommand(
                _object_id(lead_id),
                payload.outcome,
                payload.comment,
                payload.idempotency_key,
                payload.disqualification_reason,
                payload.response_confirmed,
            )
        )
    )


def _object_id(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except InvalidId as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid object id",
        ) from error


def _run(operation: Callable[[], Any]) -> dict[str, Any]:
    try:
        return operation().to_document()
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error
    except OperationsStateError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


def _run_treatment(operation: Callable[[], Any]) -> dict[str, Any]:
    try:
        return operation().to_document()
    except PermissionError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden") from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error
    except OperationsStateError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
````

## Snapshot de código: `apps/api/src/gerec_api/routes/queue.py`

````python
"""HTTP boundaries for internal distribution and administrative queue commands."""

from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from gerec_api.auth.dependencies import get_current_user
from gerec_api.auth.permissions import DashboardService, PermissionDenied
from gerec_api.auth.sessions import CurrentUser
from gerec_api.domain.queue import QueueService
from gerec_api.infrastructure.mongo.queue_repository import QueueStateError
from gerec_api.routes.leads import require_internal_key


router = APIRouter(tags=["queue"])


class CommandRequest(BaseModel):
    command_id: str = Field(min_length=1, max_length=200)


class TemporaryAssignmentRequest(CommandRequest):
    seller_id: str
    reason: str = Field(min_length=1, max_length=2_000)


class TransferOwnerRequest(CommandRequest):
    seller_id: str
    reason: str = Field(min_length=1, max_length=2_000)
    confirmed: bool


class TransferLeadRequest(CommandRequest):
    seller_id: str
    reason: str = Field(min_length=1, max_length=2_000)
    confirmed: bool


def get_queue_service(request: Request) -> QueueService:
    service = getattr(request.app.state, "queue_service", None)
    if not isinstance(service, QueueService):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Queue service unavailable",
        )
    return service


def get_dashboard_service(request: Request) -> DashboardService:
    service = getattr(request.app.state, "dashboard_service", None)
    if not isinstance(service, DashboardService):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Operational read model unavailable",
        )
    return service


def require_admin(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return current_user


@router.get("/api/queue")
def queue_snapshot(
    current_user: CurrentUser = Depends(get_current_user),
    service: DashboardService = Depends(get_dashboard_service),
) -> dict[str, Any]:
    """Expose global queue only to admin and the caller's own state to sellers."""
    try:
        return service.queue_for_user(current_user)
    except PermissionDenied as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden") from error


@router.post(
    "/api/internal/queue/leads/{lead_id}/distribute-normal",
    dependencies=[Depends(require_internal_key)],
)
def distribute_normal(
    lead_id: str,
    payload: CommandRequest,
    service: QueueService = Depends(get_queue_service),
) -> dict[str, Any]:
    return _run(
        lambda: service.with_actor("system").distribute_normal(
            _object_id(lead_id), payload.command_id
        )
    )


@router.post(
    "/api/internal/queue/leads/{lead_id}/assign-recurring",
    dependencies=[Depends(require_internal_key)],
)
def assign_recurring(
    lead_id: str,
    payload: CommandRequest,
    service: QueueService = Depends(get_queue_service),
) -> dict[str, Any]:
    return _run(
        lambda: service.with_actor("system").assign_recurring(
            _object_id(lead_id), payload.command_id
        )
    )


@router.post(
    "/api/admin/leads/{lead_id}/temporary-assignment",
)
def assign_temporarily(
    lead_id: str,
    payload: TemporaryAssignmentRequest,
    service: QueueService = Depends(get_queue_service),
    current_user: CurrentUser = Depends(require_admin),
) -> dict[str, Any]:
    return _run(
        lambda: service.with_actor(_object_id(current_user.id)).assign_temporarily(
            _object_id(lead_id),
            _object_id(payload.seller_id),
            payload.reason,
            payload.command_id,
        )
    )


@router.post(
    "/api/admin/companies/{company_id}/transfer-owner",
)
def transfer_owner(
    company_id: str,
    payload: TransferOwnerRequest,
    service: QueueService = Depends(get_queue_service),
    current_user: CurrentUser = Depends(require_admin),
) -> dict[str, Any]:
    if payload.confirmed is not True:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Permanent owner transfer requires explicit confirmation",
        )
    return _run(
        lambda: service.with_actor(_object_id(current_user.id)).transfer_owner(
            _object_id(company_id),
            _object_id(payload.seller_id),
            payload.reason,
            payload.command_id,
        )
    )


@router.post(
    "/api/admin/leads/{lead_id}/transfer-owner",
)
def transfer_lead_owner(
    lead_id: str,
    payload: TransferLeadRequest,
    service: QueueService = Depends(get_queue_service),
    current_user: CurrentUser = Depends(require_admin),
) -> dict[str, Any]:
    if payload.confirmed is not True:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Lead transfer requires explicit confirmation",
        )
    return _run(
        lambda: service.with_actor(_object_id(current_user.id)).transfer_lead(
            _object_id(lead_id),
            _object_id(payload.seller_id),
            payload.reason,
            payload.command_id,
        )
    )


def _object_id(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except InvalidId as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid object id",
        ) from error


def _run(operation):
    try:
        return operation().to_document()
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    except QueueStateError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
````

## Snapshot de código: `apps/api/src/gerec_api/routes/reports.py`

````python
"""Administrative report endpoints backed by the protected dashboard service."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from gerec_api.auth.dependencies import get_current_user
from gerec_api.auth.permissions import DashboardService, PermissionDenied
from gerec_api.auth.sessions import CurrentUser


router = APIRouter(prefix="/api/admin/reports", tags=["reports"])


def get_dashboard_service(request: Request) -> DashboardService:
    service = getattr(request.app.state, "dashboard_service", None)
    if not isinstance(service, DashboardService):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Dashboard service unavailable",
        )
    return service


def _admin(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return current_user


@router.get("/lead-distribution")
def lead_distribution(
    current_user: CurrentUser = Depends(_admin),
    service: DashboardService = Depends(get_dashboard_service),
    from_at: datetime = Query(alias="fromAt"),
    to_at: datetime = Query(alias="toAt"),
) -> dict[str, Any]:
    try:
        return service.lead_distribution(current_user, from_at=from_at, to_at=to_at)
    except PermissionDenied as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden") from error
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
````

## Snapshot de código: `apps/web/src/app/dashboard/page.tsx`

````tsx
import { redirect } from "next/navigation";
import type { ManagedUser } from "../../lib/api/types";

import { AdminDashboard } from "../../components/admin-dashboard";
import { AppShell } from "../../components/app-shell";
import { LeadListControls } from "../../components/lead-list-controls";
import { SellerDashboard } from "../../components/seller-dashboard";
import { NewLeadsNotificationModal } from "../../components/new-leads-notification-modal";
import { getManagedUsers } from "../../lib/api/client";
import { getSessionContext } from "../../lib/auth/session";
import {
  dashboardListFilters,
  getDashboardData,
  isAdminDashboard,
  pageNumber,
  type DashboardSearchParams,
} from "../../lib/dashboard/queries";
import { getNewLeadNotifications } from "../../lib/notifications/queries";

export const dynamic = "force-dynamic";

export default async function DashboardPage({
  searchParams,
}: {
  searchParams: Promise<DashboardSearchParams>;
}) {
  const session = await getSessionContext();
  if (session.status !== "authenticated") redirect("/login");

  const params = await searchParams;
  const page = pageNumber(typeof params.page === "string" ? params.page : "1");
  const filters = dashboardListFilters(params);
  let dashboard: Awaited<ReturnType<typeof getDashboardData>> | null = null;
  try {
    dashboard = await getDashboardData(session.sessionToken, page, filters);
  } catch {
    // A tela não expõe detalhes internos da falha da API.
  }

  if (dashboard === null) {
    return (
      <AppShell profile={session.profile} activePath="/dashboard" heading="Visão geral">
        <section className="dashboard-panel unavailable-state" aria-live="polite">
          <p className="eyebrow">Dados indisponíveis</p>
          <h2>Não foi possível carregar a visão geral.</h2>
          <p className="dashboard-copy">Tente atualizar a página em alguns instantes.</p>
        </section>
      </AppShell>
    );
  }

  let transferTargets: ManagedUser[] = [];
  const isAdmin = isAdminDashboard(dashboard);
  let newLeadsSnapshot: Awaited<ReturnType<typeof getNewLeadNotifications>> | null = null;
  if (isAdmin) {
    try {
      transferTargets = (await getManagedUsers(session.sessionToken, 1, 200)).items;
    } catch {
      // The dashboard remains readable if the optional transfer target list is unavailable.
    }
  } else {
    try {
      newLeadsSnapshot = await getNewLeadNotifications(session.sessionToken);
    } catch {
      // Falha opcional de notificação não pode impedir o uso do dashboard do vendedor.
    }
  }

  return (
    <AppShell profile={session.profile} activePath="/dashboard" heading="Visão geral">
      {isAdminDashboard(dashboard) ? (
        <>
          <LeadListControls role="admin" sellers={transferTargets} current={filters} />
          <AdminDashboard dashboard={dashboard} transferTargets={transferTargets} />
        </>
      ) : (
        <>
          <LeadListControls role="seller" sellers={[]} current={filters} />
          <SellerDashboard dashboard={dashboard} />
        </>
      )}
      {!isAdminDashboard(dashboard) && newLeadsSnapshot && newLeadsSnapshot.items.length > 0 ? (
        <NewLeadsNotificationModal snapshot={newLeadsSnapshot} />
      ) : null}
    </AppShell>
  );
}
````

## Snapshot de código: `apps/web/src/app/fila/page.tsx`

````tsx
import { redirect } from "next/navigation";
import type { ManagedUser } from "../../lib/api/types";

import { AppShell } from "../../components/app-shell";
import { LeadListControls } from "../../components/lead-list-controls";
import { LeadTable } from "../../components/lead-table";
import { Pagination } from "../../components/pagination";
import { QueueTable } from "../../components/queue-table";
import { SellerQueueTable } from "../../components/seller-queue-table";
import { getSessionContext } from "../../lib/auth/session";
import {
  dashboardListFilters,
  getDashboardData,
  isAdminDashboard,
  pageNumber,
  type DashboardSearchParams,
} from "../../lib/dashboard/queries";
import { getManagedUsers } from "../../lib/api/client";

export const dynamic = "force-dynamic";

export default async function QueuePage({
  searchParams,
}: {
  searchParams: Promise<DashboardSearchParams>;
}) {
  const params = await searchParams;
  const session = await getSessionContext();
  if (session.status !== "authenticated") redirect("/login");
  const page = pageNumber(typeof params.page === "string" ? params.page : "1");
  const filters = dashboardListFilters(params);
  const data = await getDashboardData(session.sessionToken, page, filters);
  if (!isAdminDashboard(data)) {
    return (
      <AppShell
        profile={session.profile}
        activePath="/fila"
        eyebrow="Minha distribuição"
        heading="Minha fila"
      >
        <LeadListControls role="seller" sellers={[]} current={filters} />
        <SellerQueueTable queue={data.queue} leads={data.leads.items} />
        <Pagination href="/fila" page={data.leads} searchParams={params} />
      </AppShell>
    );
  }

  let transferTargets: ManagedUser[] = [];
  try {
    transferTargets = (await getManagedUsers(session.sessionToken, 1, 200)).items;
  } catch {
    // Keep the read-only queue available if target loading fails.
  }

  return (
    <AppShell
      profile={session.profile}
      activePath="/fila"
      eyebrow="Fila comercial"
      heading="Fila de leads"
    >
      <QueueTable queue={data.queue} />
      <LeadListControls role="admin" sellers={transferTargets} current={filters} />
      <LeadTable leads={data.leads.items} role="admin" transferTargets={transferTargets} />
      <Pagination href="/fila" page={data.leads} searchParams={params} />
    </AppShell>
  );
}
````

## Snapshot de código: `apps/web/src/app/globals.css`

````css
@import "tailwindcss";

:root {
  --wtg-navy: #082b5b;
  --wtg-navy-strong: #061e43;
  --wtg-blue: #1458d4;
  --wtg-blue-hover: #0f47af;
  --wtg-blue-soft: #e9f0ff;
  --page: #f4f7f6;
  --surface: #ffffff;
  --surface-muted: #f7f9fb;
  --text-strong: #0d1b2a;
  --text: #1f2d3d;
  --muted: #5e6d7a;
  --line: #d7e0e5;
  --line-strong: #becbd4;
  --focus: #e89b1d;
  --status-undefined-bg: #fde8e7;
  --status-undefined-text: #9d2420;
  --status-negotiation-bg: #fff0c8;
  --status-negotiation-text: #7a4c00;
  --status-won-bg: #ddf3e6;
  --status-won-text: #075d3f;
  --status-disqualified-bg: #e7eaed;
  --status-disqualified-text: #414a54;
  --status-active-bg: #e7f2ff;
  --status-active-text: #174c9e;
  --status-paused-bg: #fde8e7;
  --status-paused-text: #9d2420;
  --shadow-modal: 0 20px 60px rgb(9 29 53 / 28%);
}

* {
  box-sizing: border-box;
}

html {
  min-width: 1280px;
  background: var(--page);
}

body {
  min-height: 100vh;
  margin: 0;
  background: var(--page);
  color: var(--text);
  font-family: Arial, Helvetica, sans-serif;
  font-size: 14px;
  line-height: 1.45;
}

button,
input,
select,
textarea {
  font: inherit;
}
button {
  cursor: pointer;
}
button:disabled {
  cursor: not-allowed;
  opacity: 0.52;
}
:focus-visible {
  outline: 3px solid var(--focus);
  outline-offset: 3px;
}

.app-shell {
  display: grid;
  grid-template-columns: 252px minmax(0, 1fr);
  min-height: 100vh;
}

.sidebar {
  display: flex;
  flex-direction: column;
  padding: 32px 22px 26px;
  background: var(--wtg-navy);
  color: #eaf1ff;
}
.brand {
  display: flex;
  align-items: center;
}
.brand-logo {
  position: relative;
  display: block;
  width: 180px;
  height: 132px;
  overflow: hidden;
}
.brand-logo img {
  position: absolute;
  top: -106px;
  left: -78px;
  display: block;
  width: 343px;
  height: 343px;
  max-width: none;
}
.sidebar nav {
  display: grid;
  gap: 6px;
  margin-top: 52px;
}
.sidebar nav a {
  padding: 13px 15px;
  border-radius: 9px;
  color: #c9d8f7;
  font-weight: 700;
  text-decoration: none;
}
.sidebar nav a:hover,
.sidebar nav a:focus-visible,
.sidebar .nav-active {
  background: #2254a5;
  color: #fff;
}
.sidebar-foot {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-top: auto;
  color: #c9d8f7;
  font-size: 12px;
}
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #5ed499;
}

.workspace {
  width: 100%;
  max-width: 1680px;
  padding: 32px 42px 60px;
}
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 88px;
  padding-bottom: 28px;
  border-bottom: 1px solid var(--line);
}
.eyebrow {
  margin: 0 0 8px;
  color: var(--wtg-blue);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}
.topbar h1,
.page-heading h1 {
  margin: 0;
  color: var(--text-strong);
  font-size: 34px;
  font-weight: 650;
  letter-spacing: -0.045em;
}
.user-menu {
  display: flex;
  align-items: center;
  gap: 10px;
}
.avatar {
  display: grid;
  width: 40px;
  height: 40px;
  place-items: center;
  border-radius: 50%;
  background: var(--wtg-blue);
  color: #fff;
  font-weight: 800;
}
.user-menu strong,
.user-menu small {
  display: block;
}
.user-menu strong {
  color: var(--text-strong);
}
.user-menu small {
  margin-top: 2px;
  color: var(--muted);
  font-size: 12px;
}
.logout {
  margin-left: 12px;
  padding: 8px 10px;
  border: 0;
  border-radius: 7px;
  background: transparent;
  color: var(--muted);
}
.logout:hover {
  background: var(--wtg-blue-soft);
  color: var(--wtg-navy);
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin: 26px 0;
}
.metric-card {
  min-height: 116px;
  padding: 19px 20px;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: var(--surface);
}
.metric-card span {
  display: block;
  color: var(--muted);
  font-size: 12px;
}
.metric-card strong {
  display: block;
  margin-top: 16px;
  color: var(--text-strong);
  font-size: 30px;
  letter-spacing: -0.05em;
}
.metric-card--accent strong {
  color: var(--wtg-blue);
}
.metric-card--next {
  border-top: 3px solid var(--wtg-blue);
}
.metric-card--next strong,
.metric-card__text {
  font-size: 17px !important;
  letter-spacing: -0.025em !important;
  line-height: 1.3;
}

.dashboard-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.16fr) minmax(420px, 0.84fr);
  gap: 16px;
  margin-bottom: 18px;
}
.dashboard-layout--seller {
  grid-template-columns: minmax(320px, 0.7fr) minmax(520px, 1.3fr);
}
.dashboard-panel,
.panel-card {
  min-width: 0;
  padding: 24px;
  border: 1px solid var(--line);
  border-radius: 13px;
  background: var(--surface);
}
.dashboard-panel h2,
.panel-head h2 {
  margin: 0;
  color: var(--text-strong);
  font-size: 21px;
  letter-spacing: -0.035em;
}
.dashboard-panel__header,
.panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}
.text-link,
.inline-link {
  color: var(--wtg-blue);
  font-size: 13px;
  font-weight: 750;
  text-decoration: none;
}
.text-link:hover,
.inline-link:hover {
  text-decoration: underline;
}
.queue-cursor {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  margin: -2px 0 16px;
  padding: 7px 10px;
  border-radius: 7px;
  background: var(--wtg-blue-soft);
  color: #163d86;
  font-size: 12px;
}

.queue-list,
.activity-list,
.user-list,
.treatment-history ol {
  display: grid;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}
.queue-list {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}
.queue-card {
  display: block;
  min-height: 126px;
  padding: 15px;
  border: 1px solid #dfe7ed;
  border-radius: 10px;
  background: var(--surface-muted);
}
.queue-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 17px;
}
.queue-card__position {
  color: var(--wtg-blue);
  font-size: 25px;
  font-weight: 800;
  letter-spacing: -0.06em;
}
.queue-card strong,
.queue-card small {
  display: block;
}
.queue-card small {
  margin-top: 6px;
  color: var(--muted);
  font-size: 12px;
}

.status-badge,
.commercial-status,
.disqualification-marker,
.pill {
  display: inline-flex;
  align-items: center;
  min-height: 25px;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 800;
  line-height: 1.2;
  white-space: nowrap;
}
.status-badge--active {
  background: var(--status-active-bg);
  color: var(--status-active-text);
}
.status-badge--paused {
  background: var(--status-paused-bg);
  color: var(--status-paused-text);
}
.commercial-status.undefined {
  background: var(--status-undefined-bg);
  color: var(--status-undefined-text);
}
.commercial-status.negotiation {
  background: var(--status-negotiation-bg);
  color: var(--status-negotiation-text);
}
.commercial-status.won {
  background: var(--status-won-bg);
  color: var(--status-won-text);
}
.commercial-status.potential {
  background: #fff0b8;
  color: #604500;
}
.disqualification-marker,
.commercial-status.disqualified,
.pill.disqualified {
  background: var(--status-disqualified-bg);
  color: var(--status-disqualified-text);
}
.pill.won {
  background: var(--status-won-bg);
  color: var(--status-won-text);
}

.activity-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  padding: 14px 0;
  border-top: 1px solid #e5ebef;
}
.activity-item:first-child {
  padding-top: 0;
  border-top: 0;
}
.activity-item strong,
.activity-item small,
.activity-item__meta span {
  display: block;
}
.activity-item strong {
  color: var(--text-strong);
  font-size: 14px;
}
.activity-item small {
  margin-top: 5px;
  color: var(--muted);
  font-size: 11px;
  line-height: 1.4;
}
.activity-item__meta {
  min-width: 145px;
  text-align: right;
}
.activity-item__meta span {
  color: var(--text-strong);
  font-size: 13px;
  font-weight: 700;
}
.activity-item__meta .commercial-status,
.activity-item__meta .disqualification-marker {
  display: inline-flex;
  margin-left: auto;
}
.dashboard-copy {
  margin: 13px 0 0;
  color: var(--muted);
  font-size: 13px;
}
.empty,
.empty-state {
  margin: 0;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.55;
}
.empty {
  padding: 48px 24px;
  text-align: center;
}
.unavailable-state {
  border-left: 4px solid var(--status-paused-text);
}

.table-card {
  margin-top: 18px;
  overflow: auto;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: var(--surface);
}
.table-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  padding: 22px 24px 18px;
}
.table-head h2 {
  margin: 0;
  color: var(--text-strong);
  font-size: 20px;
  letter-spacing: -0.03em;
}
.lead-list-controls {
  display: flex;
  align-items: end;
  gap: 12px;
  margin: 18px 0;
}
.lead-list-controls label {
  display: grid;
  gap: 6px;
  color: var(--muted);
  font-size: 12px;
  font-weight: 750;
}
.lead-list-controls select {
  min-width: 190px;
  padding: 9px 10px;
  border: 1px solid var(--line-strong);
  border-radius: 7px;
  background: var(--surface);
  color: var(--text-strong);
}
.lead-list-controls select:focus-visible {
  border-color: var(--wtg-blue);
  outline: 2px solid #bad0ff;
  outline-offset: 1px;
}
.table-card table {
  width: 100%;
  min-width: 1100px;
  border-collapse: collapse;
  text-align: left;
  font-size: 13px;
}
.table-card th {
  position: sticky;
  top: 0;
  z-index: 1;
  padding: 12px 24px;
  border-top: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
  background: var(--surface-muted);
  color: var(--muted);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.table-card td {
  padding: 15px 24px;
  border-bottom: 1px solid #e7edf1;
  vertical-align: middle;
}
.table-card tbody tr:last-child td {
  border-bottom: 0;
}
.table-card tbody tr:hover {
  background: var(--wtg-blue-soft);
  color: var(--text-strong);
}
.table-card tbody tr.lead-row--awaiting-treatment {
  background: #fff6cf;
  color: #3f3100;
}
.table-card tbody tr.lead-row--awaiting-treatment:hover {
  background: #ffea9f;
  color: #3f3100;
}
.table-card td strong {
  color: var(--text-strong);
}
.lead-table-card {
  max-height: calc(100vh - 210px);
  overflow-x: hidden;
  overflow-y: auto;
}
.seller-queue-card table {
  min-width: 0;
  table-layout: fixed;
}
.seller-queue-card th,
.seller-queue-card td {
  padding: 12px 14px;
  overflow-wrap: anywhere;
}
.seller-queue-card th:nth-child(1),
.seller-queue-card td:nth-child(1) {
  width: 30%;
}
.seller-queue-card th:nth-child(2),
.seller-queue-card td:nth-child(2) {
  width: 23%;
}
.seller-queue-card th:nth-child(3),
.seller-queue-card td:nth-child(3) {
  width: 23%;
}
.seller-queue-card th:nth-child(4),
.seller-queue-card td:nth-child(4) {
  width: 24%;
}
.lead-table-card table {
  min-width: 0;
  table-layout: fixed;
}
.lead-table-card th,
.lead-table-card td {
  padding: 12px 14px;
  overflow-wrap: anywhere;
  word-break: normal;
}
.lead-table-card td:last-child,
.lead-table-card td:last-child .table-action {
  white-space: nowrap;
}
.lead-table-card td:nth-last-child(2) {
  white-space: nowrap;
}
.lead-table-card--admin th:nth-child(1),
.lead-table-card--admin td:nth-child(1) {
  width: 12%;
}
.lead-table-card--admin th:nth-child(2),
.lead-table-card--admin td:nth-child(2) {
  width: 9%;
}
.lead-table-card--admin th:nth-child(3),
.lead-table-card--admin td:nth-child(3) {
  width: 10%;
}
.lead-table-card--admin th:nth-child(4),
.lead-table-card--admin td:nth-child(4) {
  width: 7%;
}
.lead-table-card--admin th:nth-child(5),
.lead-table-card--admin td:nth-child(5) {
  width: 7%;
}
.lead-table-card--admin th:nth-child(6),
.lead-table-card--admin td:nth-child(6) {
  width: 8%;
}
.lead-table-card--admin th:nth-child(7),
.lead-table-card--admin td:nth-child(7) {
  width: 8%;
}
.lead-table-card--admin th:nth-child(8),
.lead-table-card--admin td:nth-child(8) {
  width: 12%;
}
.lead-table-card--admin th:nth-child(9),
.lead-table-card--admin td:nth-child(9) {
  width: 12%;
}
.lead-table-card--admin th:nth-child(10),
.lead-table-card--admin td:nth-child(10) {
  width: 13%;
}
.lead-table-card--admin td:nth-child(9) {
  white-space: normal;
  line-height: 1.35;
}
.lead-actions {
  display: grid;
  gap: 6px;
}
.inline-transfer {
  min-width: 230px;
  padding: 10px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
}
.inline-transfer form,
.inline-transfer label {
  display: grid;
  gap: 5px;
}
.inline-transfer label {
  margin-bottom: 8px;
  color: var(--muted);
  font-size: 11px;
}
.inline-transfer input,
.inline-transfer select {
  min-width: 0;
  padding: 6px 8px;
  border: 1px solid var(--line-strong);
  border-radius: 5px;
  background: var(--surface);
}
.inline-transfer__actions {
  display: flex;
  justify-content: flex-end;
  gap: 6px;
}
.route-loading {
  display: grid;
  gap: 12px;
  place-items: center;
  min-height: 180px;
  color: var(--muted);
  font-size: 13px;
}
.route-loading__bar {
  display: block;
  width: 220px;
  height: 4px;
  overflow: hidden;
  border-radius: 99px;
  background: var(--line);
}
.route-loading__bar::after {
  display: block;
  width: 42%;
  height: 100%;
  border-radius: inherit;
  background: var(--wtg-blue);
  content: "";
  animation: route-loading-progress 1.1s ease-in-out infinite;
}
@keyframes route-loading-progress {
  from {
    transform: translateX(-100%);
  }
  to {
    transform: translateX(240%);
  }
}
.lead-table-card--seller th:nth-child(1),
.lead-table-card--seller td:nth-child(1) {
  width: 13%;
}
.lead-table-card--seller th:nth-child(2),
.lead-table-card--seller td:nth-child(2) {
  width: 10%;
}
.lead-table-card--seller th:nth-child(3),
.lead-table-card--seller td:nth-child(3) {
  width: 9%;
}
.lead-table-card--seller th:nth-child(4),
.lead-table-card--seller td:nth-child(4) {
  width: 8%;
}
.lead-table-card--seller th:nth-child(5),
.lead-table-card--seller td:nth-child(5) {
  width: 10%;
}
.lead-table-card--seller th:nth-child(6),
.lead-table-card--seller td:nth-child(6) {
  width: 10%;
}
.lead-table-card--seller th:nth-child(7),
.lead-table-card--seller td:nth-child(7) {
  width: 11%;
}
.lead-table-card--seller th:nth-child(8),
.lead-table-card--seller td:nth-child(8) {
  width: 13%;
}
.lead-table-card--seller th:nth-child(9),
.lead-table-card--seller td:nth-child(9) {
  width: 14%;
}
.queue-table-summary {
  display: grid;
  grid-template-columns: repeat(2, minmax(120px, 1fr));
  gap: 18px;
  margin: 0;
}
.queue-table-summary dt {
  color: var(--muted);
  font-size: 11px;
}
.queue-table-summary dd {
  margin: 4px 0 0;
  color: var(--text-strong);
  font-weight: 750;
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding: 14px 2px 4px;
  color: var(--muted);
  font-size: 13px;
}
.pagination form {
  margin: 0;
}
.pagination button {
  padding: 7px 10px;
  border: 1px solid var(--line);
  border-radius: 7px;
  background: var(--surface);
  color: var(--wtg-blue);
  font-weight: 700;
}
.pagination button:not(:disabled):hover {
  border-color: var(--wtg-blue);
  background: var(--wtg-blue-soft);
}
.pagination strong {
  color: var(--text-strong);
  font-weight: 750;
}

.panel-head .muted {
  max-width: 620px;
  margin: 8px 0 0;
}
.reports-dashboard {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin-top: 22px;
}
.report-filters {
  display: flex;
  grid-column: 1 / -1;
  align-items: end;
  gap: 12px;
  padding: 18px;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: var(--surface);
}
.report-filters label {
  display: grid;
  gap: 6px;
  color: var(--muted);
  font-size: 12px;
  font-weight: 750;
}
.report-filters input,
.report-filters select {
  min-width: 150px;
  padding: 9px 10px;
  border: 1px solid var(--line-strong);
  border-radius: 7px;
  background: var(--surface);
  color: var(--text-strong);
}
.report-card {
  padding: 22px;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: var(--surface);
}
.report-card h2 {
  margin: 0 0 18px;
  color: var(--text-strong);
  font-size: 20px;
}
.report-bars {
  display: grid;
  gap: 14px;
  margin: 0;
  padding: 0;
  list-style: none;
}
.report-bar {
  display: grid;
  gap: 6px;
}
.report-bar__label {
  color: var(--text-strong);
  font-weight: 750;
}
.report-bar__track {
  display: block;
  height: 12px;
  overflow: hidden;
  border-radius: 99px;
  background: #e7edf1;
}
.report-bar__fill {
  display: block;
  min-width: 2px;
  height: 100%;
  border-radius: inherit;
  background: var(--wtg-blue);
}
.muted {
  color: var(--muted);
  font-size: 12px;
  line-height: 1.45;
}
.user-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 17px;
  border: 1px solid #dfe7ed;
  border-radius: 10px;
  background: var(--surface-muted);
}
.user-card > div:first-child > strong {
  display: block;
  color: var(--text-strong);
}
.user-card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 14px;
  margin-top: 5px;
  color: var(--muted);
  font-size: 12px;
}
.user-card-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}
.table-action,
.secondary-button {
  min-height: 34px;
  padding: 8px 11px;
  border-radius: 7px;
  font-size: 12px;
  font-weight: 800;
}
.table-action {
  border: 1px solid var(--wtg-blue);
  background: var(--wtg-blue);
  color: #fff;
}
.table-action:not(:disabled):hover {
  border-color: var(--wtg-blue-hover);
  background: var(--wtg-blue-hover);
  color: #fff;
}
.secondary-button {
  border: 1px solid var(--line-strong);
  background: var(--surface);
  color: var(--text-strong);
}
.secondary-button:not(:disabled):hover {
  border-color: var(--wtg-blue);
  color: var(--wtg-blue);
}

.modal-backdrop {
  position: fixed;
  z-index: 20;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 32px;
  background: rgb(6 30 67 / 52%);
}
.modal-card {
  width: min(560px, calc(100vw - 64px));
  max-height: calc(100vh - 64px);
  overflow: auto;
  padding: 24px;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: var(--surface);
  box-shadow: var(--shadow-modal);
}
.modal-card h3 {
  margin: 0;
  color: var(--text-strong);
  font-size: 22px;
  letter-spacing: -0.03em;
}
.modal-card h4 {
  margin: 0;
  color: var(--text-strong);
  font-size: 15px;
}
.modal-card label {
  display: flex;
  flex-direction: column;
  gap: 7px;
  margin: 14px 0;
  color: var(--text-strong);
  font-size: 12px;
  font-weight: 750;
}
.modal-card input,
.modal-card select,
.modal-card textarea {
  width: 100%;
  padding: 10px 11px;
  border: 1px solid var(--line-strong);
  border-radius: 7px;
  background: #fff;
  color: var(--text-strong);
}
.modal-card textarea {
  min-height: 116px;
  resize: vertical;
}
.modal-card input:focus,
.modal-card select:focus,
.modal-card textarea:focus {
  border-color: var(--wtg-blue);
  outline: 2px solid #bad0ff;
  outline-offset: 1px;
}
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 18px;
}
.new-leads-notification-modal {
  width: min(620px, calc(100vw - 64px));
}
.new-leads-notification-modal > .muted {
  margin: 10px 0 0;
}
.new-leads-notification-modal__list {
  display: grid;
  gap: 9px;
  margin: 20px 0 0;
  padding: 0;
  list-style: none;
}
.new-leads-notification-modal__list li {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 14px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface-muted);
}
.new-leads-notification-modal__list strong {
  color: var(--text-strong);
}
.new-leads-notification-modal__list span {
  color: var(--muted);
  font-size: 12px;
  text-align: right;
}
.contact-modal__details {
  display: grid;
  gap: 12px;
  margin: 24px 0 0;
}
.contact-modal__details > div {
  padding: 14px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface-muted);
}
.contact-modal__details dt {
  color: var(--muted);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.contact-modal__details dd {
  margin: 5px 0 0;
  color: var(--text-strong);
  font-size: 15px;
  font-weight: 700;
  overflow-wrap: anywhere;
}
.treatment-modal__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
}
.treatment-history {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid var(--line);
}
.treatment-conversations {
  display: grid;
  gap: 14px;
  padding: 0 24px 24px;
}
.treatment-conversation-card {
  padding: 18px;
  border: 1px solid #dfe7ed;
  border-radius: 10px;
  background: var(--surface-muted);
}
.treatment-conversation-card h3 {
  margin: 0;
  color: var(--text-strong);
  font-size: 18px;
  letter-spacing: -0.03em;
}
.treatment-conversation-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
}
.treatment-conversation-card__meta {
  display: grid;
  grid-template-columns: repeat(3, minmax(120px, 1fr));
  gap: 16px;
  margin: 0;
}
.treatment-conversation-card__meta dt {
  color: var(--muted);
  font-size: 11px;
}
.treatment-conversation-card__meta dd {
  margin: 4px 0 0;
  color: var(--text-strong);
  font-weight: 700;
}
.treatment-history ol {
  margin-top: 14px;
}
.treatment-history__item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding-top: 13px;
  border-top: 1px solid #e7edf1;
}
.treatment-history__item:first-child {
  padding-top: 0;
  border-top: 0;
}
.treatment-history__item strong {
  color: var(--text-strong);
}
.treatment-history__item p {
  margin: 4px 0 0;
  color: var(--text);
  white-space: pre-wrap;
}
.treatment-history__meta {
  min-width: 135px;
  text-align: right;
}
.treatment-history__meta .commercial-status,
.treatment-history__meta .disqualification-marker {
  margin-left: auto;
}
.treatment-history__meta small {
  display: block;
  margin-top: 6px;
  color: var(--muted);
  font-size: 11px;
}
.check-row {
  flex-direction: row !important;
  align-items: center;
  gap: 8px !important;
  color: var(--text) !important;
  font-weight: 650 !important;
}
.check-row input {
  width: auto;
  margin: 0;
  accent-color: var(--wtg-blue);
}
.form-error,
.form-success {
  margin: 14px 0 0;
  padding: 10px 12px;
  border-radius: 7px;
  font-size: 12px;
  line-height: 1.4;
}
.form-error {
  background: var(--status-undefined-bg);
  color: var(--status-undefined-text);
}
.form-success {
  background: var(--status-won-bg);
  color: var(--status-won-text);
}

.login-shell {
  display: grid;
  min-height: 100vh;
  place-items: center;
  background: var(--wtg-navy);
}
.login-card {
  width: 430px;
  padding: 42px;
  border: 1px solid #d2dce6;
  border-radius: 14px;
  background: var(--surface);
  box-shadow: var(--shadow-modal);
}
.login-logo {
  position: relative;
  display: block;
  width: 210px;
  height: 154px;
  overflow: hidden;
  margin-bottom: 8px;
  border-radius: 10px;
  background: var(--wtg-navy);
}
.login-logo img {
  position: absolute;
  top: -124px;
  left: -91px;
  width: 400px;
  height: 400px;
  max-width: none;
}
.login-card h1 {
  margin: 0;
  color: var(--text-strong);
  font-size: 42px;
  line-height: 1;
  letter-spacing: -0.06em;
}
.login-copy {
  margin: 18px 0 30px;
  color: var(--muted);
  line-height: 1.55;
}
.login-card label {
  display: block;
  margin-top: 16px;
  color: var(--text-strong);
  font-size: 12px;
  font-weight: 750;
}
.login-card input {
  display: block;
  width: 100%;
  margin-top: 7px;
  padding: 12px;
  border: 1px solid var(--line-strong);
  border-radius: 7px;
}
.login-card button {
  width: 100%;
  min-height: 42px;
  margin-top: 24px;
  border: 1px solid var(--wtg-blue);
  border-radius: 7px;
  background: var(--wtg-blue);
  color: #fff;
  font-weight: 800;
}
.login-card button:not(:disabled):hover {
  background: var(--wtg-blue-hover);
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    scroll-behavior: auto !important;
    transition-duration: 0.01ms !important;
    animation-duration: 0.01ms !important;
  }
}
````

## Snapshot de código: `apps/web/src/app/globals.test.ts`

````typescript
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const stylesheetPath = fileURLToPath(new URL("./globals.css", import.meta.url));

describe("tokens visuais da operação", () => {
  it("define tokens contrastantes para os quatro estados comerciais", async () => {
    const stylesheet = await readFile(stylesheetPath, "utf8");

    expect(stylesheet).toContain("--status-undefined-bg:");
    expect(stylesheet).toContain("--status-negotiation-bg:");
    expect(stylesheet).toContain("--status-won-bg:");
    expect(stylesheet).toContain("--status-disqualified-bg:");
  });

  it("mantém a superfície desktop, tabelas, modais e controles indisponíveis estilizados", async () => {
    const stylesheet = await readFile(stylesheetPath, "utf8");

    expect(stylesheet).toContain("min-width: 1280px");
    expect(stylesheet).toContain(".table-card table");
    expect(stylesheet).toContain(".modal-backdrop");
    expect(stylesheet).toContain("button:disabled");
    expect(stylesheet).toContain(".empty-state");
  });

  it("preserva badges de situação nas atividades resumidas", async () => {
    const stylesheet = await readFile(stylesheetPath, "utf8");

    expect(stylesheet).toContain(".activity-item__meta .commercial-status");
  });
});
````

## Snapshot de código: `apps/web/src/app/historico/page.tsx`

````tsx
import { redirect } from "next/navigation";
import { AppShell } from "../../components/app-shell";
import { Pagination } from "../../components/pagination";
import { TreatmentHistoryTable } from "../../components/treatment-history-table";
import { getSessionContext } from "../../lib/auth/session";
import { getDashboardData, pageNumber } from "../../lib/dashboard/queries";

export const dynamic = "force-dynamic";
export default async function HistoryPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const session = await getSessionContext();
  if (session.status !== "authenticated") redirect("/login");
  const params = await searchParams;
  const page = pageNumber(typeof params.page === "string" ? params.page : "1");
  const data = await getDashboardData(session.sessionToken, page);
  return (
    <AppShell
      profile={session.profile}
      activePath="/historico"
      eyebrow={session.profile.role === "admin" ? "Histórico auditável" : "Minha atividade"}
      heading={session.profile.role === "admin" ? "Histórico" : "Minhas tratativas"}
    >
      <TreatmentHistoryTable treatments={data.history.items} />
      <Pagination href="/historico" page={data.history} searchParams={params} />
    </AppShell>
  );
}
````

## Snapshot de código: `apps/web/src/app/hover-contrast.test.ts`

````typescript
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const stylesheetPath = fileURLToPath(new URL("./globals.css", import.meta.url));

describe("contraste dos estados de interação", () => {
  it("preserva contraste no hover da ação primária", async () => {
    const stylesheet = await readFile(stylesheetPath, "utf8");
    const start = stylesheet.indexOf(".table-action:not(:disabled):hover {");
    const block = stylesheet.slice(start, stylesheet.indexOf("}", start) + 1);

    expect(block).toContain("color: #fff;");
  });

  it("preserva contraste no hover das linhas da tabela", async () => {
    const stylesheet = await readFile(stylesheetPath, "utf8");
    const start = stylesheet.indexOf(".table-card tbody tr:hover {");
    const block = stylesheet.slice(start, stylesheet.indexOf("}", start) + 1);

    expect(block).toContain("color: var(--text-strong);");
  });
});
````

## Snapshot de código: `apps/web/src/app/layout.tsx`

````tsx
import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import type { ReactNode } from "react";

import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Gerenciador de Leads WTG",
  description: "Fundação local do Gerenciador de Leads WTG",
};

export const viewport: Viewport = {
  themeColor: "#f3f5f4",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="pt-BR">
      <body className={`${geistSans.variable} ${geistMono.variable}`}>{children}</body>
    </html>
  );
}
````

## Snapshot de código: `apps/web/src/app/loading.tsx`

````tsx
export default function Loading() {
  return (
    <main className="route-loading" aria-live="polite" aria-busy="true">
      <div className="route-loading__bar" />
      <p>Carregando dados da operação…</p>
    </main>
  );
}
````

## Snapshot de código: `apps/web/src/app/login/page.tsx`

````tsx
import { LoginForm } from "../../components/login-form";

export default function LoginPage() {
  return <LoginForm />;
}
````

## Snapshot de código: `apps/web/src/app/page.tsx`

````tsx
import { redirect } from "next/navigation";

export default function Home() {
  redirect("/dashboard");
}
````

## Snapshot de código: `apps/web/src/app/relatorios/page.test.tsx`

````tsx
import { describe, expect, it, vi } from "vitest";

const { getLeadDistributionReport, getSessionContext, isReportPeriod, redirect } = vi.hoisted(() => ({
  getLeadDistributionReport: vi.fn(),
  getSessionContext: vi.fn(),
  isReportPeriod: vi.fn(),
  redirect: vi.fn(),
}));

vi.mock("next/navigation", () => ({ redirect }));
vi.mock("../../lib/auth/session", () => ({ getSessionContext }));
vi.mock("../../lib/reports/queries", () => ({
  getLeadDistributionReport,
  isReportPeriod,
  reportPeriod: vi.fn(),
}));

import ReportsPage from "./page";

describe("ReportsPage", () => {
  it("redireciona vendedor para o dashboard antes de consultar o relat\u00f3rio", async () => {
    getSessionContext.mockResolvedValue({
      status: "authenticated",
      sessionToken: "seller-session",
      profile: {
        id: "seller-1",
        userId: "seller-1",
        fullName: "Jessica",
        email: "jessica@wtgseguros.com.br",
        role: "seller",
      },
    });
    redirect.mockImplementation((path: string) => {
      throw new Error(`REDIRECT:${path}`);
    });

    await expect(ReportsPage({ searchParams: Promise.resolve({}) })).rejects.toThrow("REDIRECT:/dashboard");
    expect(redirect).toHaveBeenCalledWith("/dashboard");
    expect(getLeadDistributionReport).not.toHaveBeenCalled();
  });
});
````

## Snapshot de código: `apps/web/src/app/relatorios/page.tsx`

````tsx
import { redirect } from "next/navigation";

import { AppShell } from "../../components/app-shell";
import { ReportsDashboard } from "../../components/reports-dashboard";
import { getSessionContext } from "../../lib/auth/session";
import {
  getLeadDistributionReport,
  isReportPeriod,
  reportPeriod,
  type ReportSearchParams,
} from "../../lib/reports/queries";

export const dynamic = "force-dynamic";

export default async function ReportsPage({ searchParams }: { searchParams: Promise<ReportSearchParams> }) {
  const session = await getSessionContext();
  if (session.status !== "authenticated" || session.profile.role !== "admin") redirect("/dashboard");

  const period = reportPeriod(await searchParams);
  let report = null;
  let error: string | null = null;
  if (isReportPeriod(period)) {
    try {
      report = await getLeadDistributionReport(session.sessionToken, period);
    } catch {
      error = "Não foi possível carregar os relatórios. Tente novamente.";
    }
  } else {
    error = period.error;
  }

  return (
    <AppShell profile={session.profile} activePath="/relatorios" eyebrow="Leitura gerencial" heading="Relatórios">
      <ReportsDashboard
        report={report}
        period={period.key}
        error={error}
        from={isReportPeriod(period) ? undefined : period.from}
        to={isReportPeriod(period) ? undefined : period.to}
        interval={isReportPeriod(period) ? { from: period.fromAt, to: period.toAt } : undefined}
      />
    </AppShell>
  );
}
````

## Snapshot de código: `apps/web/src/app/relatorios/page-regression.test.tsx`

````tsx
import { beforeEach, describe, expect, it, vi } from "vitest";

const { AppShell, ReportsDashboard, getLeadDistributionReport, getSessionContext, isReportPeriod, reportPeriod } = vi.hoisted(() => ({
  AppShell: vi.fn(),
  ReportsDashboard: vi.fn(),
  getLeadDistributionReport: vi.fn(),
  getSessionContext: vi.fn(),
  isReportPeriod: vi.fn((period) => "fromAt" in period),
  reportPeriod: vi.fn(),
}));

vi.mock("../../components/app-shell", () => ({ AppShell }));
vi.mock("../../components/reports-dashboard", () => ({ ReportsDashboard }));
vi.mock("../../lib/auth/session", () => ({ getSessionContext }));
vi.mock("../../lib/reports/queries", () => ({ getLeadDistributionReport, isReportPeriod, reportPeriod }));

import ReportsPage from "./page";

describe("recuperação da página de relatórios", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getSessionContext.mockResolvedValue({
      status: "authenticated",
      sessionToken: "admin-session",
      profile: { id: "admin-1", userId: "admin-1", fullName: "Yago", email: "yago@wtg.test", role: "admin" },
    });
    reportPeriod.mockReturnValue({
      key: "custom",
      fromAt: "2026-09-01T03:00:00.000Z",
      toAt: "2026-09-15T03:00:00.000Z",
    });
  });

  it("preserva shell e nova tentativa quando a consulta falha", async () => {
    getLeadDistributionReport.mockRejectedValue(new Error("indisponível"));

    const page = await ReportsPage({ searchParams: Promise.resolve({ period: "custom" }) });

    expect(page.type).toBe(AppShell);
    expect(page.props.children.type).toBe(ReportsDashboard);
    expect(page.props.children.props).toMatchObject({
      report: null,
      interval: {
        from: "2026-09-01T03:00:00.000Z",
        to: "2026-09-15T03:00:00.000Z",
      },
      error: "Não foi possível carregar os relatórios. Tente novamente.",
    });
  });
});
````

## Snapshot de código: `apps/web/src/app/route-access.test.ts`

````typescript
import { renderToStaticMarkup } from "react-dom/server";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { getDashboardData, getSessionContext, redirect } = vi.hoisted(() => ({
  getDashboardData: vi.fn(),
  getSessionContext: vi.fn(),
  redirect: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  redirect,
  usePathname: () => "/fila",
  useRouter: () => ({ push: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
}));
vi.mock("../lib/auth/session", () => ({ getSessionContext }));
vi.mock("../lib/dashboard/queries", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../lib/dashboard/queries")>()),
  getDashboardData,
}));

import DashboardPage from "./dashboard/page";
import QueuePage from "./fila/page";
import HistoryPage from "./historico/page";

const sellerSession = {
  status: "authenticated" as const,
  sessionToken: "seller-session",
  profile: {
    id: "seller-1",
    userId: "seller-1",
    fullName: "Jessica",
    email: "jessica@wtgseguros.com.br",
    role: "seller" as const,
  },
};

describe("proteção das rotas operacionais", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    redirect.mockImplementation((target: string) => {
      throw new Error(`REDIRECT:${target}`);
    });
  });

  it("permite ao vendedor abrir suas próprias tratativas por URL", async () => {
    getSessionContext.mockResolvedValue(sellerSession);
    getDashboardData.mockResolvedValue({
      user: { id: "seller-1", email: sellerSession.profile.email, role: "seller" },
      leads: { items: [], page: 1, pageSize: 50, total: 0 },
      history: { items: [], page: 1, pageSize: 50, total: 0 },
      queue: { position: 2, availability: "active", skipBalance: 0 },
    });

    const markup = renderToStaticMarkup(await HistoryPage({ searchParams: Promise.resolve({}) }));
    expect(markup).toContain("Minhas tratativas");
    expect(markup).toContain("Nenhuma tratativa registrada.");
    expect(redirect).not.toHaveBeenCalled();
  });

  it("permite ao vendedor abrir sua fila por URL sem dados globais", async () => {
    getSessionContext.mockResolvedValue(sellerSession);
    getDashboardData.mockResolvedValue({
      user: { id: "seller-1", email: sellerSession.profile.email, role: "seller" },
      leads: { items: [], page: 1, pageSize: 50, total: 0 },
      history: { items: [], page: 1, pageSize: 50, total: 0 },
      queue: { position: 3, availability: "active", skipBalance: 0 },
    });

    const markup = renderToStaticMarkup(await QueuePage({ searchParams: Promise.resolve({}) }));
    expect(markup).toContain("Minha fila");
    expect(markup).toContain("Posição 3");
    expect(markup).not.toContain("Fila comercial");
    expect(redirect).not.toHaveBeenCalled();
  });

  it("renderiza um estado seguro quando a API não disponibiliza o dashboard", async () => {
    getSessionContext.mockResolvedValue({
      ...sellerSession,
      profile: { ...sellerSession.profile, role: "admin" as const },
    });
    getDashboardData.mockRejectedValue(new Error("INTERNAL_DETAIL_X"));

    const markup = renderToStaticMarkup(await DashboardPage({ searchParams: Promise.resolve({}) }));

    expect(markup).toContain("Não foi possível carregar a visão geral.");
    expect(markup).toContain("Tente atualizar a página em alguns instantes.");
    expect(markup).not.toContain("INTERNAL_DETAIL_X");
  });
});
````

## Snapshot de código: `apps/web/src/app/usuarios/page.tsx`

````tsx
import { redirect } from "next/navigation";

import { AppShell } from "../../components/app-shell";
import { Pagination } from "../../components/pagination";
import { UserManagement } from "../../components/user-management";
import { getManagedUsers } from "../../lib/api/client";
import { getSessionContext } from "../../lib/auth/session";
import { pageNumber } from "../../lib/dashboard/queries";

export const dynamic = "force-dynamic";

export default async function UsersPage({
  searchParams,
}: {
  searchParams: Promise<{ page?: string }>;
}) {
  const session = await getSessionContext();
  if (session.status !== "authenticated" || session.profile.role !== "admin") redirect("/dashboard");

  const page = pageNumber((await searchParams).page ?? "1");
  const users = await getManagedUsers(session.sessionToken, page);

  return (
    <AppShell profile={session.profile} activePath="/usuarios" eyebrow="Administração" heading="Usuários">
      <UserManagement key={`users-page-${users.page}`} users={users.items} page={users.page} />
      <Pagination href="/usuarios" page={users} />
    </AppShell>
  );
}
````

## Snapshot de código: `apps/web/src/components/admin-dashboard.tsx`

````tsx
import Link from "next/link";
import type {
  AdminDashboard as AdminDashboardData,
  ManagedUser,
  QueueEntry,
  Treatment,
} from "../lib/api/types";
import {
  formatCommercialStatus,
  formatDateTime,
  formatDisqualificationMarker,
} from "../lib/dashboard/format";
import { LeadTable } from "./lead-table";

function availabilityLabel(availability: QueueEntry["availability"]): string {
  return availability === "paused" ? "Pausado" : "Ativo";
}

function QueueCard({ item, currentPosition }: { item: QueueEntry; currentPosition: number }) {
  const normalizedAvailability = item.availability === "paused" ? "paused" : "active";
  const label = availabilityLabel(normalizedAvailability);
  return (
    <li className="queue-card">
      <div className="queue-card__header">
        <span className="queue-card__position">#{currentPosition}</span>
        <span className={`status-badge status-badge--${normalizedAvailability}`}>{label}</span>
      </div>
      <strong>{item.sellerName}</strong>
      <small>
        Ordem base {item.position}. {normalizedAvailability === "paused" ? "Pausado manualmente" : "Disponível para novas atribuições"}
      </small>
    </li>
  );
}

function TreatmentPreview({ item }: { item: Treatment }) {
  return (
    <li className="activity-item">
      <div>
        <strong>{item.leadName ?? "Lead não informado"}</strong>
        <small>Vendedor responsável: {item.sellerName}</small>
      </div>
      <div className="activity-item__meta">
        <span className={`commercial-status ${item.commercialStatus}`}>
          {formatCommercialStatus(item.commercialStatus)}
        </span>
        <small>{formatDateTime(item.createdAt)}</small>
        {item.isDisqualified ? (
          <span className="disqualification-marker">{formatDisqualificationMarker(true)}</span>
        ) : null}
      </div>
    </li>
  );
}

export function AdminDashboard({
  dashboard,
  transferTargets = [],
}: {
  dashboard: AdminDashboardData;
  transferTargets?: ManagedUser[];
}) {
  return (
    <>
      <section className="metric-grid" aria-label="Resumo operacional administrativo">
        <article className="metric-card metric-card--accent">
          <span>Total de leads</span>
          <strong>{dashboard.leads.total}</strong>
        </article>
        <article className="metric-card">
          <span>Atribuições</span>
          <strong>{dashboard.history.total}</strong>
        </article>
        <article className="metric-card">
          <span>Posições na fila</span>
          <strong>{dashboard.queue.total}</strong>
        </article>
        <article className="metric-card metric-card--next">
          <span>Próximo vendedor</span>
          <strong>{dashboard.queue.nextSellerName}</strong>
        </article>
      </section>

      <section className="dashboard-layout" aria-label="Distribuição e atividade recente">
        <section className="dashboard-panel dashboard-panel--queue">
          <header className="dashboard-panel__header">
            <div>
              <p className="eyebrow">Distribuição</p>
              <h2>Fila comercial</h2>
            </div>
            <Link prefetch={false} className="text-link" href="/fila">
              Ver fila completa
            </Link>
          </header>
          {dashboard.queue.items.length === 0 ? (
            <p className="empty-state">
              Nenhum vendedor disponível na fila. Cadastre ou ative um vendedor para retomar a
              distribuição.
            </p>
          ) : (
            <>
              <p className="queue-cursor">
                Próxima vez: <strong>{dashboard.queue.cursorSellerName}</strong>
              </p>
              <ol className="queue-list" aria-label="Fila comercial completa">
                {dashboard.queue.items.map((item, index) => (
                  <QueueCard item={item} currentPosition={index + 1} key={item.sellerName} />
                ))}
              </ol>
            </>
          )}
        </section>

        <section className="dashboard-panel">
          <header className="dashboard-panel__header">
            <div>
              <p className="eyebrow">Atividade</p>
              <h2>Últimas tratativas</h2>
            </div>
            <Link prefetch={false} className="text-link" href="/historico">
              Ver histórico
            </Link>
          </header>
          {dashboard.history.items.length === 0 ? (
            <p className="empty-state">Nenhuma tratativa registrada.</p>
          ) : (
            <ol className="activity-list">
              {dashboard.history.items.slice(0, 5).map((item, index) => (
                <TreatmentPreview item={item} key={`${item.createdAt}-${index}`} />
              ))}
            </ol>
          )}
        </section>
      </section>

      <LeadTable leads={dashboard.leads.items} role="admin" transferTargets={transferTargets} />
    </>
  );
}
````

## Snapshot de código: `apps/web/src/components/app-shell.test.tsx`

````tsx
// @vitest-environment jsdom

import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("next/image", () => ({
  default: () => <span />,
}));
vi.mock("../lib/auth/actions", () => ({ signOutAction: vi.fn() }));

import { AppShell } from "./app-shell";

const admin = {
  id: "admin-1",
  userId: "admin-1",
  fullName: "Yago",
  email: "yago@wtgseguros.com.br",
  role: "admin" as const,
};

const seller = { ...admin, id: "seller-1", userId: "seller-1", fullName: "Jessica", role: "seller" as const };

function renderShell(profile: typeof admin | typeof seller) {
  return render(
    <AppShell profile={profile}>
      <p>Conte\u00fado</p>
    </AppShell>,
  );
}

afterEach(cleanup);

describe("navega\u00e7\u00e3o do AppShell", () => {
  it("mostra Relat\u00f3rios somente para administrador", () => {
    expect(renderShell(admin).getByRole("link", { name: "Relat\u00f3rios" })).toBeTruthy();
    cleanup();
    expect(renderShell(seller).queryByRole("link", { name: "Relat\u00f3rios" })).toBeNull();
  });
});
````

## Snapshot de código: `apps/web/src/components/app-shell.tsx`

````tsx
import Image from "next/image";
import Link from "next/link";

import { signOutAction } from "../lib/auth/actions";
import type { SessionProfile } from "../lib/auth/session";

export function AppShell({
  profile,
  activePath = "/dashboard",
  eyebrow,
  heading = "Visão geral",
  children,
}: {
  profile: SessionProfile;
  activePath?: "/dashboard" | "/fila" | "/historico" | "/usuarios" | "/relatorios";
  eyebrow?: string;
  heading?: string;
  children: React.ReactNode;
}) {
  const isAdmin = profile.role === "admin";

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-logo">
            <Image
              src="/logo-wtg.png"
              alt="WTG Corretora de Seguros e Benefícios"
              width={343}
              height={343}
              priority
            />
          </span>
        </div>
        <nav aria-label="Navegação principal">
          <Link
            prefetch={false}
            className={activePath === "/dashboard" ? "nav-active" : ""}
            href="/dashboard"
          >
            {isAdmin ? "Visão geral" : "Minha operação"}
          </Link>
          {isAdmin ? (
            <>
              <Link
                prefetch={false}
                className={activePath === "/relatorios" ? "nav-active" : ""}
                href="/relatorios"
              >
                Relatórios
              </Link>
              <Link
                prefetch={false}
                className={activePath === "/fila" ? "nav-active" : ""}
                href="/fila"
              >
                Fila de leads
              </Link>
              <Link
                prefetch={false}
                className={activePath === "/historico" ? "nav-active" : ""}
                href="/historico"
              >
                Histórico
              </Link>
              <Link
                prefetch={false}
                className={activePath === "/usuarios" ? "nav-active" : ""}
                href="/usuarios"
              >
                Usuários
              </Link>
            </>
          ) : (
            <>
              <Link
                prefetch={false}
                className={activePath === "/fila" ? "nav-active" : ""}
                href="/fila"
              >
                Minha fila
              </Link>
              <Link
                prefetch={false}
                className={activePath === "/historico" ? "nav-active" : ""}
                href="/historico"
              >
                Minhas tratativas
              </Link>
            </>
          )}
        </nav>
        <div className="sidebar-foot">
          <span className="status-dot" />
          Sistema conectado
        </div>
      </aside>
      <main className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">
              {eyebrow ?? (isAdmin ? "Painel administrativo" : "Minha operação")}
            </p>
            <h1>{heading}</h1>
          </div>
          <div className="user-menu">
            <span className="avatar" aria-hidden="true">
              {profile.fullName.slice(0, 1)}
            </span>
            <span>
              <strong>{profile.fullName}</strong>
              <small>{isAdmin ? "Administrador" : "Vendedor"}</small>
            </span>
            <form action={signOutAction}>
              <button className="logout" type="submit">
                Sair
              </button>
            </form>
          </div>
        </header>
        {children}
      </main>
    </div>
  );
}
````

## Snapshot de código: `apps/web/src/components/confirm-action-modal.tsx`

````tsx
"use client";

import { useEffect, useRef } from "react";

export function ConfirmActionModal({ title, description, confirmLabel, pending, onConfirm, onCancel }: {
  title: string;
  description: string;
  confirmLabel: string;
  pending: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  const confirmRef = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    confirmRef.current?.focus();
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !pending) onCancel();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onCancel, pending]);

  return <div className="modal-backdrop" role="presentation" onMouseDown={(event) => {
    if (event.target === event.currentTarget && !pending) onCancel();
  }}>
    <section className="modal-card" role="dialog" aria-modal="true" aria-labelledby="confirm-action-title">
      <h3 id="confirm-action-title">{title}</h3>
      <p className="muted">{description}</p>
      <div className="modal-actions">
        <button type="button" className="secondary-button" disabled={pending} onClick={onCancel}>Cancelar</button>
        <button ref={confirmRef} type="button" className="table-action" disabled={pending} onClick={onConfirm}>{pending ? "Salvando…" : confirmLabel}</button>
      </div>
    </section>
  </div>;
}
````

## Snapshot de código: `apps/web/src/components/dashboard-components.test.ts`

````typescript
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { AdminDashboard } from "./admin-dashboard";
import { AppShell } from "./app-shell";
import { SellerDashboard } from "./seller-dashboard";

const adminDashboard = {
  user: { id: "admin-1", email: "yago@wtgseguros.com.br", role: "admin" as const },
  leads: {
    items: [],
    page: 1,
    pageSize: 50,
    total: 6,
  },
  history: {
    items: [
      {
        leadId: "lead-admin-1",
        leadName: "Débora Souza",
        sellerName: "Renato",
        comment: "Primeiro contato realizado.",
        commercialStatus: "negotiation" as const,
        isDisqualified: false,
        assignedAt: "2026-08-28T15:30:00.000Z",
        createdAt: "2026-08-28T16:03:04.876Z",
        lastUpdatedAt: "2026-08-28T16:03:04.876Z",
      },
    ],
    page: 1,
    pageSize: 50,
    total: 4,
  },
  queue: {
    items: [
      {
        sellerName: "Jessica",
        position: 1,
        availability: "active" as const,
        reason: null,
        skipBalance: 0,
      },
      {
        sellerName: "Nelma",
        position: 2,
        availability: "active" as const,
        reason: null,
        skipBalance: 0,
      },
    ],
    total: 2,
    nextSellerName: "Jessica",
    cursorSellerName: "Jessica",
  },
};

const sellerDashboard = {
  user: { id: "seller-1", email: "jessica@wtgseguros.com.br", role: "seller" as const },
  leads: {
    items: [
      {
        id: "lead-1",
        contactName: "Débora Souza",
        sellerName: "Jessica",
        companyName: "Débora Souza",
        campaignName: "WTG formulário",
        phoneDisplay: "(11) 98830-8029",
        email: "debora@example.com",
        commercialStatus: "undefined" as const,
        isDisqualified: false,
        commentCount: 2,
        assignedAt: "2026-08-28T15:30:00.000Z",
        lastUpdatedAt: "2026-08-28T16:03:04.876Z",
      },
    ],
    page: 1,
    pageSize: 50,
    total: 1,
  },
  history: {
    items: [
      {
        leadId: "lead-seller-1",
        leadName: "Débora Souza",
        sellerName: "Jessica",
        comment: "Primeiro contato realizado.",
        commercialStatus: "negotiation" as const,
        isDisqualified: false,
        assignedAt: "2026-08-28T15:30:00.000Z",
        createdAt: "2026-08-28T16:03:04.876Z",
        lastUpdatedAt: "2026-08-28T16:03:04.876Z",
      },
    ],
    page: 1,
    pageSize: 50,
    total: 2,
  },
  queue: { position: 3, availability: "active" as const, skipBalance: 0 },
};

describe("dashboards por papel", () => {
  it("renderiza os indicadores administrativos e a fila completa devolvida pela API", () => {
    const markup = renderToStaticMarkup(
      createElement(AdminDashboard, { dashboard: adminDashboard }),
    );

    expect(markup).toContain("Total de leads");
    expect(markup).toContain("Atribuições");
    expect(markup).toContain("Posições na fila");
    expect(markup).toContain("Próximo vendedor");
    expect(markup).toContain("Fila comercial");
    expect(markup).toContain("Jessica");
    expect(markup).toContain("Nelma");
  });

  it("orienta o administrador quando não há vendedores disponíveis na fila", () => {
    const markup = renderToStaticMarkup(
      createElement(AdminDashboard, {
        dashboard: {
          ...adminDashboard,
          queue: {
            items: [],
            total: 0,
            nextSellerName: "Não informado",
            cursorSellerName: "Não informado",
          },
        },
      }),
    );

    expect(markup).toContain("Nenhum vendedor disponível na fila.");
    expect(markup).toContain("Cadastre ou ative um vendedor para retomar a distribuição.");
  });

  it("renderiza a operação própria do vendedor sem nomes ou indicadores dos colegas", () => {
    const markup = renderToStaticMarkup(
      createElement(SellerDashboard, { dashboard: sellerDashboard }),
    );

    expect(markup).toContain("Meus leads");
    expect(markup).toContain("Meus comentários");
    expect(markup).toContain("Minha posição na fila");
    expect(markup).toContain("Posição 3");
    expect(markup).toContain("Débora Souza");
    expect(markup).not.toContain("Renato");
    expect(markup).not.toContain("Nelma");
    expect(markup).not.toContain("Próximo vendedor");
  });

  it("trata uma posição ausente na resposta da API sem renderizar undefined", () => {
    const markup = renderToStaticMarkup(
      createElement(SellerDashboard, {
        dashboard: {
          ...sellerDashboard,
          queue: { ...sellerDashboard.queue, position: undefined },
        } as unknown as typeof sellerDashboard,
      }),
    );

    expect(markup).toContain("Não informado");
    expect(markup).not.toContain("Posição undefined");
  });

  it("limita a navegação do vendedor à própria operação", () => {
    const markup = renderToStaticMarkup(
      AppShell({
        profile: {
          id: "seller-1",
          userId: "seller-1",
          fullName: "Jessica",
          email: "jessica@wtgseguros.com.br",
          role: "seller",
        },
        children: createElement("p", null, "Conteúdo"),
      }),
    );

    expect(markup).toContain("Minha operação");
    expect(markup).not.toContain("Fila de leads");
    expect(markup).not.toContain("Histórico");
    expect(markup).not.toContain("Usuários");
  });
});
````

## Snapshot de código: `apps/web/src/components/lead-contact-modal.tsx`

````tsx
"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import type { OperationalLead } from "../lib/api/types";
import { formatPhone, formatText } from "../lib/dashboard/format";

export function LeadContactModal({ lead }: { lead: OperationalLead }) {
  const [open, setOpen] = useState(false);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const closeRef = useRef<HTMLButtonElement>(null);
  const wasOpenRef = useRef(false);
  const titleId = `lead-contact-title-${lead.id}`;
  const close = useCallback(() => setOpen(false), []);

  useEffect(() => {
    if (open) {
      closeRef.current?.focus();
    } else if (wasOpenRef.current) {
      triggerRef.current?.focus();
    }
    wasOpenRef.current = open;
  }, [open]);

  return (
    <>
      <button
        ref={triggerRef}
        type="button"
        className="table-action"
        aria-label={`Ver contato de ${lead.contactName}`}
        onClick={() => setOpen(true)}
      >
        Ver contato
      </button>
      {open ? (
        <div
          className="modal-backdrop"
          role="presentation"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) close();
          }}
        >
          <section
            className="modal-card contact-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby={titleId}
            onKeyDown={(event) => {
              if (event.key === "Escape") close();
            }}
          >
            <header className="treatment-modal__header">
              <div>
                <p className="eyebrow">Contato</p>
                <h3 id={titleId}>Contato de {lead.contactName}</h3>
              </div>
              <button
                ref={closeRef}
                type="button"
                className="secondary-button"
                aria-label="Fechar contato"
                onClick={close}
              >
                Fechar
              </button>
            </header>
            <dl className="contact-modal__details">
              <div>
                <dt>Telefone</dt>
                <dd>{formatPhone(lead.phoneDisplay)}</dd>
              </div>
              <div>
                <dt>E-mail</dt>
                <dd>{formatText(lead.email)}</dd>
              </div>
            </dl>
          </section>
        </div>
      ) : null}
    </>
  );
}
````

## Snapshot de código: `apps/web/src/components/lead-list-controls.tsx`

````tsx
"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";

import type { ManagedUser, UserRole } from "../lib/api/types";
import type { DashboardListFilters } from "../lib/dashboard/queries";

type LeadListControlsProps = {
  role: UserRole;
  sellers: ManagedUser[];
  current: DashboardListFilters;
};

/** URL-backed list controls keep pagination and unrelated query parameters intact. */
export function LeadListControls({ role, sellers, current }: LeadListControlsProps) {
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const sellerOptions = sellers.filter((seller) => seller.role === "seller");

  function updateFilter(key: "assigneeId" | "sort", value: string) {
    const next = new URLSearchParams(searchParams.toString());
    if (value) next.set(key, value);
    else next.delete(key);
    const query = next.toString();
    router.push(query ? `${pathname}?${query}` : pathname);
  }

  return (
    <section className="lead-list-controls" aria-label="Controles da lista de leads">
      {role === "admin" ? (
        <label>
          {"Respons\u00e1vel"}
          <select
            aria-label={"Respons\u00e1vel"}
            value={current.assigneeId ?? ""}
            onChange={(event) => updateFilter("assigneeId", event.target.value)}
          >
            <option value="">{"Todos os respons\u00e1veis"}</option>
            {sellerOptions.map((seller) => (
              <option key={seller.id} value={seller.id}>
                {seller.fullName}
              </option>
            ))}
          </select>
        </label>
      ) : null}
      <label>
        Ordenar por
        <select
          aria-label="Ordenar por"
          value={current.sort ?? ""}
          onChange={(event) => updateFilter("sort", event.target.value)}
        >
          <option value="">{"Ordem padr\u00e3o"}</option>
          <option value="situation">{"Situa\u00e7\u00e3o"}</option>
        </select>
      </label>
    </section>
  );
}
````

## Snapshot de código: `apps/web/src/components/lead-table.test.tsx`

````tsx
// @vitest-environment jsdom

import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

const navigation = vi.hoisted(() => ({
  pathname: "/fila",
  push: vi.fn(),
  searchParams: new URLSearchParams("page=2"),
}));

vi.mock("next/navigation", () => ({
  usePathname: () => navigation.pathname,
  useRouter: () => ({ push: navigation.push }),
  useSearchParams: () => navigation.searchParams,
}));

import { LeadListControls } from "./lead-list-controls";
import { LeadTable } from "./lead-table";

const lead = {
  id: "lead-1",
  contactName: "D\u00e9bora Souza",
  sellerName: "Jessica",
  companyName: "Empresa da D\u00e9bora",
  campaignName: "Campanha WTG",
  phoneDisplay: "(11) 98830-8029",
  email: "debora@example.com",
  commercialStatus: "undefined" as const,
  isDisqualified: false,
  commentCount: 0,
  assignedAt: "2026-08-28T12:00:00.000Z",
  lastUpdatedAt: "2026-08-28T12:00:00.000Z",
};

const seller = {
  id: "seller-1",
  fullName: "Jessica",
  email: "jessica@wtgseguros.com.br",
  role: "seller" as const,
  active: true,
  paused: false,
};

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("lista operacional de leads", () => {
  it("destaca somente leads sem tratativa", () => {
    render(
      <LeadTable
        role="seller"
        leads={[lead, { ...lead, id: "treated", contactName: "Tratado", commentCount: 1 }]}
      />,
    );

    expect(screen.getByText(lead.contactName).closest("tr")?.classList.contains(
      "lead-row--awaiting-treatment",
    )).toBe(true);
    expect(screen.getByText("Tratado").closest("tr")?.classList.contains(
      "lead-row--awaiting-treatment",
    )).toBe(false);
  });

  it("renderiza o filtro de respons\u00e1vel apenas para administrador", () => {
    render(
      <LeadListControls
        role="admin"
        sellers={[seller]}
        current={{ assigneeId: null, sort: "situation" }}
      />,
    );

    expect(screen.getByLabelText("Respons\u00e1vel")).toBeTruthy();
  });
});
````

## Snapshot de código: `apps/web/src/components/lead-table.tsx`

````tsx
"use client";

import { useCallback, useState } from "react";

import type { ManagedUser, OperationalLead, TreatmentSubmission, UserRole } from "../lib/api/types";
import {
  formatCommentCount,
  formatCommercialStatus,
  formatDateTime,
  formatDisqualificationMarker,
} from "../lib/dashboard/format";
import { LeadContactModal } from "./lead-contact-modal";
import { LeadTreatmentModal } from "./lead-treatment-modal";
import { LeadTransferModal } from "./lead-transfer-modal";

type LeadTableProps = { leads: OperationalLead[]; role: UserRole; transferTargets?: ManagedUser[] };

/** Render Brazilian numbers consistently, whether the source includes +55 or not. */
export function formatBrazilianPhone(value: string | null | undefined): string {
  const digits = String(value ?? "").replace(/\D/g, "");
  const national =
    digits.startsWith("55") && [12, 13].includes(digits.length) ? digits.slice(2) : digits;
  if (national.length === 11) {
    return `(${national.slice(0, 2)}) ${national.slice(2, 7)}-${national.slice(7)}`;
  }
  if (national.length === 10) {
    return `(${national.slice(0, 2)}) ${national.slice(2, 6)}-${national.slice(6)}`;
  }
  return national || "Não informado";
}

export function commentCountsAfterSubmission(
  current: Record<string, number>,
  submission: TreatmentSubmission,
): Record<string, number> {
  return { ...current, [submission.leadId]: submission.commentCount };
}

export function applySubmissionToLead(
  lead: OperationalLead,
  submission: TreatmentSubmission,
): OperationalLead {
  if (lead.id !== submission.leadId) return lead;
  return {
    ...lead,
    commercialStatus: submission.commercialStatus,
    isDisqualified: submission.isDisqualified,
    commentCount: submission.commentCount,
    lastUpdatedAt: submission.lastUpdatedAt,
  };
}

function statusClass(status: OperationalLead["commercialStatus"]): string {
  return `commercial-status ${status}`;
}

export function LeadTable({ leads, role, transferTargets = [] }: LeadTableProps) {
  const [leadOverrides, setLeadOverrides] = useState<Record<string, OperationalLead>>({});
  const onSubmitted = useCallback(
    (submission: TreatmentSubmission) => {
      setLeadOverrides((current) => {
        const original =
          current[submission.leadId] ?? leads.find((lead) => lead.id === submission.leadId);
        if (!original) return current;
        return { ...current, [submission.leadId]: applySubmissionToLead(original, submission) };
      });
    },
    [leads],
  );

  return (
    <section
      className={`table-card lead-table-card lead-table-card--${role}`}
      aria-labelledby="lead-table-title"
    >
      <div className="table-head">
        <div>
          <p className="eyebrow">Dados ao vivo</p>
          <h2 id="lead-table-title">Leads</h2>
        </div>
      </div>
      {leads.length === 0 ? (
        <p className="empty">Nenhum lead disponível.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Nome</th>
              {role === "admin" ? <th>Responsável</th> : null}
              <th>Contato</th>
              <th>Situação</th>
              <th>Marcador</th>
              <th>Atribuído em</th>
              <th>Última atualização</th>
              <th>Comentários</th>
              <th>Ação</th>
            </tr>
          </thead>
          <tbody>
            {leads.map((lead) => {
              const currentLead = leadOverrides[lead.id] ?? lead;
              return (
                <tr
                  key={lead.id}
                  className={currentLead.commentCount === 0 ? "lead-row--awaiting-treatment" : undefined}
                >
                  <td>
                    <strong>{currentLead.contactName}</strong>
                  </td>
                  {role === "admin" ? <td>{currentLead.sellerName}</td> : null}
                  <td><LeadContactModal lead={currentLead} /></td>
                  <td>
                    <span className={statusClass(currentLead.commercialStatus)}>
                      {formatCommercialStatus(currentLead.commercialStatus)}
                    </span>
                  </td>
                  <td>
                    {currentLead.isDisqualified ? (
                      <span className="disqualification-marker">
                        {formatDisqualificationMarker(true)}
                      </span>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td>{formatDateTime(currentLead.assignedAt)}</td>
                  <td>{formatDateTime(currentLead.lastUpdatedAt)}</td>
                  <td>{formatCommentCount(currentLead.commentCount)}</td>
                  <td>
                    <div className="lead-actions">
                      <LeadTreatmentModal
                        lead={currentLead}
                        mode={role === "seller" ? "write" : "read"}
                        onSubmitted={role === "seller" ? onSubmitted : undefined}
                      />
                      {role === "admin" ? (
                        <LeadTransferModal
                          lead={currentLead}
                          targets={transferTargets}
                          onSuccess={(sellerName) => {
                            setLeadOverrides((current) => ({
                              ...current,
                              [currentLead.id]: { ...currentLead, sellerName },
                            }));
                          }}
                        />
                      ) : null}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </section>
  );
}
````

## Snapshot de código: `apps/web/src/components/lead-transfer-modal.tsx`

````tsx
"use client";

import { useActionState, useEffect, useState } from "react";

import type { ManagedUser, OperationalLead } from "../lib/api/types";
import {
  transferLeadOwnershipAction,
} from "../lib/operations/transfer-actions";
import { initialTransferActionState } from "../lib/operations/transfer-state";

export function LeadTransferModal({
  lead,
  targets,
  onSuccess,
}: {
  lead: OperationalLead;
  targets: ManagedUser[];
  onSuccess?: (sellerName: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const [selectedSellerName, setSelectedSellerName] = useState("");
  const [state, formAction, pending] = useActionState(
    transferLeadOwnershipAction,
    initialTransferActionState,
  );
  useEffect(() => {
    if (state.status === "success") {
      const timer = window.setTimeout(() => {
        setOpen(false);
        onSuccess?.(selectedSellerName);
      }, 0);
      return () => window.clearTimeout(timer);
    }
  }, [onSuccess, selectedSellerName, state.status]);
  if (!open) {
    return (
      <button type="button" className="table-action secondary-button" onClick={() => setOpen(true)}>
        Transferir propriedade
      </button>
    );
  }
  return (
    <div className="inline-transfer" role="dialog" aria-label={`Transferir ${lead.contactName}`}>
      <form action={formAction}>
        <input type="hidden" name="leadId" value={lead.id} />
        <label>
          Novo responsável
          <select
            name="sellerId"
            defaultValue=""
            required
            onChange={(event) => {
              setSelectedSellerName(event.currentTarget.selectedOptions[0]?.text ?? "");
            }}
          >
            <option value="" disabled>
              Selecione
            </option>
            {targets
              .filter((target) => target.active && target.role === "seller")
              .map((target) => (
                <option key={target.id} value={target.id}>
                  {target.fullName}
                </option>
              ))}
          </select>
        </label>
        <label>
          Motivo
          <input name="reason" required maxLength={2000} placeholder="Motivo da transferência" />
        </label>
        {state.status === "error" ? (
          <p className="form-error" role="status">
            {state.message}
          </p>
        ) : null}
        <div className="inline-transfer__actions">
          <button type="button" className="secondary-button" onClick={() => setOpen(false)}>
            Cancelar
          </button>
          <button type="submit" className="table-action" disabled={pending}>
            {pending ? "Transferindo…" : "Confirmar"}
          </button>
        </div>
      </form>
    </div>
  );
}
````

## Snapshot de código: `apps/web/src/components/lead-treatment-modal.dom.test.tsx`

````tsx
// @vitest-environment jsdom

import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Treatment } from "../lib/api/types";

const actions = vi.hoisted(() => ({
  loadHistory: vi.fn(async () => ({ status: "success" as const, items: [] as Treatment[] })),
  submit: vi.fn(),
}));

vi.mock("../lib/operations/treatment-actions", () => ({
  initialTreatmentActionState: { status: "idle", message: null, submission: null },
  loadLeadTreatmentHistoryAction: actions.loadHistory,
  submitLeadTreatmentAction: actions.submit,
}));

import { LeadTable } from "./lead-table";
import { LeadTreatmentModal } from "./lead-treatment-modal";

const lead = {
  id: "lead-1",
  contactName: "Débora Souza",
  sellerName: "Jessica",
  companyName: "Empresa da Débora",
  campaignName: "Campanha WTG",
  phoneDisplay: "(11) 98830-8029",
  email: "debora@example.com",
  commercialStatus: "undefined" as const,
  isDisqualified: false,
  commentCount: 2,
  assignedAt: "2026-08-28T12:00:00.000Z",
  lastUpdatedAt: "2026-08-28T12:00:00.000Z",
};

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("acessibilidade e interação do modal de tratativa", () => {
  it("abre os dados de contato do lead pela coluna Contato", async () => {
    const user = userEvent.setup();
    render(<LeadTable leads={[lead]} role="seller" />);

    expect(screen.getByRole("columnheader", { name: "Contato" })).toBeTruthy();
    const trigger = screen.getByRole("button", { name: "Ver contato de Débora Souza" });
    await user.click(trigger);

    expect(screen.getByRole("dialog", { name: "Contato de Débora Souza" })).toBeTruthy();
    expect(screen.getByText("(11) 98830-8029")).toBeTruthy();
    expect(screen.getByText("debora@example.com")).toBeTruthy();

    await user.click(screen.getByRole("button", { name: "Fechar contato" }));
    expect(screen.queryByRole("dialog", { name: "Contato de Débora Souza" })).toBeNull();
    expect(document.activeElement).toBe(trigger);
  });

  it("foca o primeiro controle de leitura, prende Tab e devolve foco após Escape", async () => {
    const user = userEvent.setup();
    render(<LeadTreatmentModal lead={lead} mode="read" />);
    const trigger = screen.getByRole("button", { name: "Ver histórico" });

    await user.click(trigger);
    const close = screen.getByRole("button", { name: "Fechar janela" });
    await waitFor(() => expect(document.activeElement).toBe(close));
    await user.tab();
    expect(document.activeElement).toBe(close);
    await user.tab({ shift: true });
    expect(document.activeElement).toBe(close);
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(document.activeElement).toBe(trigger);
  });

  it("bloqueia a submissão com comentário menor que seis caracteres", async () => {
    const user = userEvent.setup();
    render(<LeadTreatmentModal lead={lead} mode="write" />);

    await user.click(screen.getByRole("button", { name: "Registrar tratativa" }));
    await user.type(screen.getByLabelText("Comentário"), "curto");

    expect(
      (screen.getByRole("button", { name: "Salvar tratativa" }) as HTMLButtonElement).disabled,
    ).toBe(true);
    expect(actions.submit).not.toHaveBeenCalled();
  });

  it("shows Potencial in the treatment selector", () => {
    render(
      <LeadTreatmentModal
        lead={{ ...lead, commercialStatus: "potential" }}
        mode="write"
        defaultOpen
      />,
    );

    expect(screen.getByRole("option", { name: "Potencial" })).toBeTruthy();
  });

  it("gera a chave de idempotência depois da hidratação, sem aleatoriedade no HTML inicial", async () => {
    const user = userEvent.setup();
    render(<LeadTreatmentModal lead={lead} mode="write" />);

    await user.click(screen.getByRole("button", { name: "Registrar tratativa" }));
    await waitFor(() => {
      const input = document.querySelector('input[name="idempotencyKey"]') as HTMLInputElement;
      expect(input?.value).toBeTruthy();
    });
  });

  it("mantém Tab e Shift+Tab dentro do formulário com múltiplos controles", async () => {
    const user = userEvent.setup();
    render(<LeadTreatmentModal lead={lead} mode="write" />);

    await user.click(screen.getByRole("button", { name: "Registrar tratativa" }));
    await user.type(screen.getByLabelText("Comentário"), "Contato realizado por telefone.");
    const close = screen.getByRole("button", { name: "Fechar janela" });
    const submit = screen.getByRole("button", { name: "Salvar tratativa" });
    const comment = screen.getByLabelText("Comentário");
    close.focus();

    await user.tab({ shift: true });
    expect(document.activeElement).toBe(submit);
    await user.tab();
    expect(document.activeElement).toBe(close);
    await user.tab();
    expect(document.activeElement).toBe(comment);
  });

  it("mostra carregamento e depois renderiza o histórico devolvido pela API", async () => {
    let resolveHistory: ((value: { status: "success"; items: Treatment[] }) => void) | undefined;
    actions.loadHistory.mockImplementation(
      () =>
        new Promise<{ status: "success"; items: Treatment[] }>((resolve) => {
          resolveHistory = resolve;
        }),
    );
    const user = userEvent.setup();
    render(<LeadTreatmentModal lead={lead} mode="read" />);

    await user.click(screen.getByRole("button", { name: "Ver histórico" }));
    expect(screen.getByText("Carregando histórico…")).toBeTruthy();
    resolveHistory?.({
      status: "success",
      items: [
        {
          leadName: "Débora Souza",
          sellerName: "Jessica",
          comment: "Histórico carregado da API.",
          commercialStatus: "negotiation",
          isDisqualified: false,
          createdAt: "2026-08-29T12:00:00.000Z",
        },
      ] as Treatment[],
    });

    expect(await screen.findByText("Histórico carregado da API.")).toBeTruthy();
  });

  it("exibe carregamento, atualiza contador/histórico e confirma após sucesso", async () => {
    let resolveSubmission: ((value: unknown) => void) | undefined;
    actions.submit.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveSubmission = resolve;
        }),
    );
    actions.loadHistory
      .mockResolvedValueOnce({ status: "success", items: [] })
      .mockResolvedValueOnce({
        status: "success",
        items: [
          {
            leadName: "Débora Souza",
            sellerName: "Jessica",
            comment: "Contato registrado com sucesso.",
            commercialStatus: "negotiation",
            isDisqualified: false,
            createdAt: "2026-08-29T12:00:00.000Z",
          },
        ] as Treatment[],
      })
      .mockResolvedValue({
        status: "success",
        items: [
          {
            leadName: "Débora Souza",
            sellerName: "Jessica",
            comment: "Contato registrado com sucesso.",
            commercialStatus: "negotiation",
            isDisqualified: false,
            createdAt: "2026-08-29T12:00:00.000Z",
          },
        ] as Treatment[],
      });
    const user = userEvent.setup();
    render(<LeadTable leads={[lead]} role="seller" />);

    await user.click(screen.getByRole("button", { name: "Registrar tratativa" }));
    await user.type(screen.getByLabelText("Comentário"), "Contato registrado com sucesso.");
    await user.click(screen.getByRole("button", { name: "Salvar tratativa" }));
    expect(screen.getByRole("button", { name: "Salvando…" })).toBeTruthy();

    resolveSubmission?.({
      status: "success",
      message: "Tratativa registrada.",
      submission: {
        leadId: "lead-1",
        treatmentId: "treatment-1",
        status: "created",
        commercialStatus: "negotiation",
        isDisqualified: false,
        commentCount: 3,
        lastUpdatedAt: "2026-08-29T15:00:00.000Z",
      },
    });

    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
    expect(screen.getByRole("status").textContent).toContain("Tratativa registrada.");
    expect(screen.getByText("3 comentários")).toBeTruthy();
    expect(screen.getByText("Negociação")).toBeTruthy();
    await waitFor(() => expect(actions.loadHistory).toHaveBeenCalledTimes(2));
    expect(document.activeElement).toBe(
      screen.getByRole("button", { name: "Registrar tratativa" }),
    );

    await user.click(screen.getByRole("button", { name: "Registrar tratativa" }));
    expect(await screen.findByText("Contato registrado com sucesso.")).toBeTruthy();
  });

  it("mostra o erro 422 seguro no formulário", async () => {
    actions.submit.mockResolvedValue({
      status: "error",
      message: "Revise os dados informados e tente novamente.",
      submission: null,
    });
    const user = userEvent.setup();
    render(<LeadTreatmentModal lead={lead} mode="write" />);

    await user.click(screen.getByRole("button", { name: "Registrar tratativa" }));
    await user.type(screen.getByLabelText("Comentário"), "Contato registrado com sucesso.");
    await user.click(screen.getByRole("button", { name: "Salvar tratativa" }));

    expect(await screen.findByText("Revise os dados informados e tente novamente.")).toBeTruthy();
    expect(screen.getByRole("dialog")).toBeTruthy();
  });

  it("atualiza a situação e o marcador ao desqualificar uma tratativa", async () => {
    actions.submit.mockResolvedValue({
      status: "success",
      message: "Tratativa registrada.",
      submission: {
        leadId: "lead-1",
        treatmentId: "treatment-2",
        status: "created",
        commercialStatus: "won",
        isDisqualified: true,
        commentCount: 3,
        lastUpdatedAt: "2026-08-29T15:00:00.000Z",
      },
    });
    actions.loadHistory
      .mockResolvedValueOnce({ status: "success", items: [] })
      .mockResolvedValueOnce({
        status: "success",
        items: [
          {
            leadName: "Débora Souza",
            sellerName: "Jessica",
            comment: "Fora do escopo, mas com fechamento excepcional.",
            commercialStatus: "won",
            isDisqualified: true,
            createdAt: "2026-08-29T13:00:00.000Z",
          },
        ] as Treatment[],
      });
    const user = userEvent.setup();
    render(
      <LeadTable leads={[lead]} role="seller" />,
    );

    await user.click(screen.getByRole("button", { name: "Registrar tratativa" }));
    await user.type(
      screen.getByLabelText("Comentário"),
      "Fora do escopo, mas com fechamento excepcional.",
    );
    await user.click(screen.getByLabelText("Marcar como Desqualificado"));
    await user.click(screen.getByRole("button", { name: "Salvar tratativa" }));

    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
    expect(screen.getByText("Desqualificado")).toBeTruthy();
    expect(screen.queryByText("Não informado")).toBeNull();
  });
});
````

## Snapshot de código: `apps/web/src/components/lead-treatment-modal.test.ts`

````typescript
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

import {
  applySubmissionToLead,
  commentCountsAfterSubmission,
  formatBrazilianPhone,
  LeadTable,
} from "./lead-table";
import { LeadTreatmentModal, validateTreatmentDraft } from "./lead-treatment-modal";

const lead = {
  id: "lead-1",
  contactName: "Débora Souza",
  sellerName: "Renato",
  companyName: "Empresa da Débora",
  campaignName: "Campanha WTG",
  phoneDisplay: "(11) 98830-8029",
  email: "debora@example.com",
  commercialStatus: "negotiation" as const,
  isDisqualified: false,
  commentCount: 2,
  assignedAt: "2026-08-28T16:03:04.876Z",
  lastUpdatedAt: "2026-08-28T16:03:04.876Z",
};

describe("tabela de leads e tratativa", () => {
  it("mostra responsável somente na visão administrativa", () => {
    const admin = renderToStaticMarkup(createElement(LeadTable, { leads: [lead], role: "admin" }));
    const seller = renderToStaticMarkup(
      createElement(LeadTable, { leads: [lead], role: "seller" }),
    );

    expect(admin).toContain("Responsável");
    expect(admin).toContain("Renato");
    expect(admin).not.toContain("Empresa da Débora");
    expect(admin).not.toContain("Campanha WTG");
    expect(admin).not.toContain("E-mail");
    expect(admin).toContain("Contato");
    expect(admin).toContain("Ver contato de Débora Souza");
    expect(admin).not.toContain("(11) 98830-8029");
    expect(admin).toContain("2 comentários");
    expect(admin).not.toContain("Registrar tratativa");
    expect(seller).not.toContain("Responsável");
    expect(seller).toContain("Registrar tratativa");
  });

  it("normaliza telefones brasileiros com ou sem o código 55", () => {
    expect(formatBrazilianPhone("+55 (11) 98830-8029")).toBe("(11) 98830-8029");
    expect(formatBrazilianPhone("11988308029")).toBe("(11) 98830-8029");
    expect(formatBrazilianPhone("5511998765432")).toBe("(11) 99876-5432");
    expect(formatBrazilianPhone("telefone ausente")).toBe("Não informado");
  });

  it("exibe somente os campos comerciais e o histórico em modo leitura", () => {
    const markup = renderToStaticMarkup(
      createElement(LeadTreatmentModal, {
        lead,
        mode: "read",
        defaultOpen: true,
        treatments: [
          {
            leadId: "lead-1",
            leadName: "Débora Souza",
            sellerName: "Renato",
            comment: "Primeiro contato por telefone.",
            commercialStatus: "negotiation",
            isDisqualified: false,
            assignedAt: "2026-08-28T15:30:00.000Z",
            createdAt: "2026-08-28T16:03:04.876Z",
            lastUpdatedAt: "2026-08-28T16:03:04.876Z",
          },
        ],
      }),
    );

    expect(markup).toContain("Histórico de tratativas");
    expect(markup).toContain("Primeiro contato por telefone.");
    expect(markup).not.toContain("Salvar tratativa");
    expect(markup).not.toContain("<textarea");
  });

  it("oferece as três situações, marcador adicional e bloqueia comentário curto", () => {
    const markup = renderToStaticMarkup(
      createElement(LeadTreatmentModal, {
        lead,
        mode: "write",
        treatments: [],
        defaultOpen: true,
      }),
    );

    expect(markup).toContain("Indefinido");
    expect(markup).toContain("Negociação");
    expect(markup).toContain("Ganho");
    expect(markup).toContain("Desqualificado");
    expect(markup).toContain("Salvar tratativa");
    expect(
      validateTreatmentDraft({
        comment: "curto",
        commercialStatus: "undefined",
        isDisqualified: false,
      }),
    ).toEqual({
      ok: false,
      message: "Escreva um comentário com ao menos 6 caracteres.",
    });
  });

  it("atualiza o contador exibido com o total devolvido pela API", () => {
    expect(
      commentCountsAfterSubmission(
        { "outro-lead": 1 },
        {
          leadId: "lead-1",
          treatmentId: "treatment-1",
          status: "created",
          commercialStatus: "won",
          isDisqualified: false,
          commentCount: 3,
          lastUpdatedAt: "2026-08-29T15:00:00.000Z",
        },
      ),
    ).toEqual({ "outro-lead": 1, "lead-1": 3 });
  });

  it("reflete a tratativa salva na própria linha do lead", () => {
    expect(
      applySubmissionToLead(lead, {
        leadId: "lead-1",
        treatmentId: "treatment-1",
        status: "created",
        commercialStatus: "won",
        isDisqualified: true,
        commentCount: 3,
        lastUpdatedAt: "2026-08-29T15:00:00.000Z",
      }),
    ).toMatchObject({
      commercialStatus: "won",
      isDisqualified: true,
      commentCount: 3,
    });
  });

  it("exibe a última atualização persistida mesmo quando o relógio do navegador diverge", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2030-01-01T00:00:00.000Z"));
    try {
      const updatedLead = applySubmissionToLead(lead, {
        leadId: "lead-1",
        treatmentId: "treatment-1",
        status: "created",
        commercialStatus: "negotiation",
        isDisqualified: false,
        commentCount: 3,
        lastUpdatedAt: "2026-08-29T15:00:00.000Z",
      });
      const markup = renderToStaticMarkup(
        createElement(LeadTable, { leads: [updatedLead], role: "seller" }),
      );

      expect(markup).toContain("29/08/2026, 12:00");
      expect(markup).not.toContain("31/12/2029");
    } finally {
      vi.useRealTimers();
    }
  });
});
````

## Snapshot de código: `apps/web/src/components/lead-treatment-modal.tsx`

````tsx
"use client";

import { useActionState, useCallback, useEffect, useId, useRef, useState } from "react";

import type {
  CommercialStatus,
  OperationalLead,
  Treatment,
  TreatmentSubmission,
} from "../lib/api/types";
import {
  formatCommercialStatus,
  formatDateTime,
  formatDisqualificationMarker,
} from "../lib/dashboard/format";
import {
  loadLeadTreatmentHistoryAction,
  submitLeadTreatmentAction,
} from "../lib/operations/treatment-actions";
import { initialTreatmentActionState } from "../lib/operations/treatment-state";

export type TreatmentDraft = {
  comment: string;
  commercialStatus: CommercialStatus;
  isDisqualified: boolean;
};

export function validateTreatmentDraft(
  draft: TreatmentDraft,
): { ok: true } | { ok: false; message: string } {
  if (draft.comment.trim().length < 6) {
    return { ok: false, message: "Escreva um comentário com ao menos 6 caracteres." };
  }
  return { ok: true };
}

function historyItem(item: Treatment, index: number) {
  return (
    <li className="treatment-history__item" key={`${item.createdAt}-${index}`}>
      <div>
        <strong>{item.sellerName}</strong>
        <p>{item.comment}</p>
      </div>
      <div className="treatment-history__meta">
        <span className={`commercial-status ${item.commercialStatus}`}>
          {formatCommercialStatus(item.commercialStatus)}
        </span>
        {item.isDisqualified ? (
          <span className="disqualification-marker">{formatDisqualificationMarker(true)}</span>
        ) : null}
        <small>{formatDateTime(item.createdAt)}</small>
      </div>
    </li>
  );
}

function TreatmentForm({
  lead,
  onSuccess,
  sessionNumber,
}: {
  lead: OperationalLead;
  onSuccess: (submission: TreatmentSubmission) => void;
  sessionNumber: number;
}) {
  const [state, formAction, pending] = useActionState(
    submitLeadTreatmentAction,
    initialTreatmentActionState,
  );
  // React IDs are stable between SSR and hydration. The session number makes
  // a new idempotency key whenever the modal is opened again.
  const reactId = useId();
  const idempotencyKey = `tratativa-${lead.id}-${sessionNumber}-${reactId}`;
  const [comment, setComment] = useState("");
  const draftIsValid = validateTreatmentDraft({
    comment,
    commercialStatus: lead.commercialStatus,
    isDisqualified: false,
  }).ok;

  useEffect(() => {
    if (state.status === "success") onSuccess(state.submission);
  }, [onSuccess, state]);

  return (
    <form action={formAction} className="treatment-form">
      <input type="hidden" name="leadId" value={lead.id} />
      <input type="hidden" name="idempotencyKey" value={idempotencyKey} />
      <label htmlFor={`treatment-comment-${lead.id}`}>
        Comentário
        <textarea
          id={`treatment-comment-${lead.id}`}
          name="comment"
          required
          minLength={6}
          maxLength={2000}
          autoFocus
          value={comment}
          onChange={(event) => setComment(event.target.value)}
          placeholder="Descreva o contato ou a evolução da negociação."
        />
      </label>
      <label htmlFor={`treatment-status-${lead.id}`}>
        Situação comercial
        <select
          id={`treatment-status-${lead.id}`}
          name="commercialStatus"
          defaultValue={lead.commercialStatus}
        >
          <option value="undefined">Indefinido</option>
          <option value="negotiation">Negociação</option>
          <option value="potential">Potencial</option>
          <option value="won">Ganho</option>
        </select>
      </label>
      <label className="check-row" htmlFor={`treatment-disqualified-${lead.id}`}>
        <input id={`treatment-disqualified-${lead.id}`} name="isDisqualified" type="checkbox" />
        Marcar como Desqualificado
      </label>
      <p className="muted">Desqualificar exige o comentário registrado nesta tratativa.</p>
      {state.status !== "idle" ? (
        <p className={`form-${state.status}`} role="status" aria-live="polite">
          {state.message}
        </p>
      ) : null}
      <div className="modal-actions">
        <button type="submit" className="table-action" disabled={pending || !draftIsValid}>
          {pending ? "Salvando…" : "Salvar tratativa"}
        </button>
      </div>
    </form>
  );
}

export function LeadTreatmentModal({
  lead,
  mode,
  treatments: initialTreatments = [],
  defaultOpen = false,
  onSubmitted,
}: {
  lead: OperationalLead;
  mode: "read" | "write";
  treatments?: Treatment[];
  defaultOpen?: boolean;
  onSubmitted?: (submission: TreatmentSubmission) => void;
}) {
  const [open, setOpen] = useState(defaultOpen);
  const [treatments, setTreatments] = useState(initialTreatments);
  const [historyMessage, setHistoryMessage] = useState<string | null>(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [treatmentSession, setTreatmentSession] = useState(0);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const dialogRef = useRef<HTMLElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const wasOpenRef = useRef(open);
  const refreshHistory = useCallback(() => {
    setHistoryLoading(true);
    setHistoryMessage(null);
    void loadLeadTreatmentHistoryAction(lead.id).then((result) => {
      setHistoryLoading(false);
      if (result.status === "success") {
        setTreatments(result.items);
      } else {
        setHistoryMessage(result.message);
      }
    });
  }, [lead.id]);
  const openModal = useCallback(() => {
    setSuccessMessage(null);
    setTreatmentSession((current) => current + 1);
    setOpen(true);
    refreshHistory();
  }, [refreshHistory]);
  const onSuccess = useCallback(
    (submission: TreatmentSubmission) => {
      onSubmitted?.(submission);
      refreshHistory();
      setSuccessMessage("Tratativa registrada.");
      setOpen(false);
    },
    [onSubmitted, refreshHistory],
  );
  const closeModal = useCallback(() => setOpen(false), []);

  useEffect(() => {
    if (open) {
      closeButtonRef.current?.focus();
    } else if (wasOpenRef.current) {
      triggerRef.current?.focus();
    }
    wasOpenRef.current = open;
  }, [open]);

  const trapKeyboard = useCallback(
    (event: React.KeyboardEvent<HTMLElement>) => {
      if (event.key === "Escape") {
        event.preventDefault();
        closeModal();
        return;
      }
      if (event.key !== "Tab" || !dialogRef.current) return;
      const focusable = Array.from(
        dialogRef.current.querySelectorAll<HTMLElement>(
          'button:not([disabled]), [href], input:not([type="hidden"]):not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
        ),
      ).filter((element) => !element.hidden);
      if (focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    },
    [closeModal],
  );

  const titleId = `lead-treatment-title-${lead.id}`;
  const triggerLabel = mode === "write" ? "Registrar tratativa" : "Ver histórico";

  return (
    <>
      <button ref={triggerRef} type="button" className="table-action" onClick={openModal}>
        {triggerLabel}
      </button>
      {successMessage ? (
        <p className="form-success" role="status" aria-live="polite">
          {successMessage}
        </p>
      ) : null}
      {open ? (
        <div
          className="modal-backdrop"
          role="presentation"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) closeModal();
          }}
        >
          <section
            ref={dialogRef}
            className="modal-card treatment-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby={titleId}
            onKeyDown={trapKeyboard}
          >
            <header className="treatment-modal__header">
              <div>
                <p className="eyebrow">Lead</p>
                <h3 id={titleId}>{lead.contactName}</h3>
              </div>
              <button
                ref={closeButtonRef}
                type="button"
                className="secondary-button"
                onClick={closeModal}
                aria-label="Fechar janela"
              >
                Fechar
              </button>
            </header>

            {mode === "write" ? (
              <TreatmentForm lead={lead} onSuccess={onSuccess} sessionNumber={treatmentSession} />
            ) : null}

            <section className="treatment-history" aria-label="Histórico de tratativas">
              <h4>Histórico de tratativas</h4>
              {historyLoading ? (
                <p className="muted" aria-live="polite">
                  Carregando histórico…
                </p>
              ) : null}
              {historyMessage ? (
                <p className="form-error" role="status">
                  {historyMessage}
                </p>
              ) : null}
              {!historyLoading && !historyMessage && treatments.length === 0 ? (
                <p className="muted">Nenhuma tratativa registrada.</p>
              ) : null}
              {treatments.length > 0 ? <ol>{treatments.map(historyItem)}</ol> : null}
            </section>
          </section>
        </div>
      ) : null}
    </>
  );
}
````

## Snapshot de código: `apps/web/src/components/login-form.tsx`

````tsx
"use client";

import { useActionState } from "react";
import { loginAction, type LoginState } from "../lib/auth/actions";

const initialState: LoginState = {};

export function LoginForm() {
  const [state, action, pending] = useActionState(loginAction, initialState);
  return (
    <main className="login-shell">
      <form className="login-card" action={action}>
        <span className="login-logo"><img src="/logo-wtg.png" alt="WTG Corretora" /></span>
        <p className="eyebrow">WTG · operação comercial</p>
        <h1>
          Gerenciador
          <br />
          de Leads
        </h1>
        <p className="login-copy">Entre para acompanhar sua fila e resultados.</p>
        <label>
          E-mail
          <input name="email" type="email" placeholder="voce@gerec.local" required />
        </label>
        <label>
          Senha
          <input name="password" type="password" required />
        </label>
        {state.error && (
          <p className="form-error" role="alert">
            {state.error}
          </p>
        )}
        <button type="submit" disabled={pending}>
          {pending ? "Entrando…" : "Entrar no sistema"}
        </button>
        <small>Ambiente local · America/Sao_Paulo</small>
      </form>
    </main>
  );
}
````

## Snapshot de código: `apps/web/src/components/new-leads-notification-modal.dom.test.tsx`

````tsx
// @vitest-environment jsdom

import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

const { acknowledge } = vi.hoisted(() => ({ acknowledge: vi.fn() }));

vi.mock("../lib/notifications/actions", () => ({
  acknowledgeNewLeadsAction: acknowledge,
}));

import { NewLeadsNotificationModal } from "./new-leads-notification-modal";

const snapshot = {
  items: [
    {
      leadId: "lead-1",
      contactName: "Ana Souza",
      assignedAt: "2026-09-15T12:00:00.000Z",
    },
  ],
  watermark: "2026-09-15T12:01:00.000Z",
  acknowledgementToken: "token-assinado",
  watermarkSequence: 8,
};

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("janela de novos leads", () => {
  it("confirma o watermark somente ao fechar", async () => {
    acknowledge.mockResolvedValue({ ok: true, message: "Novos leads confirmados." });
    const user = userEvent.setup();
    render(<NewLeadsNotificationModal snapshot={snapshot} />);

    expect(acknowledge).not.toHaveBeenCalled();
    await user.click(screen.getByRole("button", { name: "Fechar" }));

    await waitFor(() => expect(acknowledge).toHaveBeenCalledWith(snapshot));
    expect(screen.queryByRole("dialog", { name: "Novos leads" })).toBeNull();
  });

  it("abre a nova janela quando a revalidação entrega outro snapshot", async () => {
    acknowledge.mockResolvedValue({ ok: true, message: "Novos leads confirmados." });
    const user = userEvent.setup();
    const { rerender } = render(<NewLeadsNotificationModal snapshot={snapshot} />);

    await user.click(screen.getByRole("button", { name: "Fechar" }));
    await waitFor(() => expect(screen.queryByRole("dialog", { name: "Novos leads" })).toBeNull());

    rerender(
      <NewLeadsNotificationModal
        snapshot={{
          ...snapshot,
          items: [{ ...snapshot.items[0], leadId: "lead-2", contactName: "Beatriz Lima" }],
          watermark: "2026-09-15T12:02:00.000Z",
          acknowledgementToken: "outro-token-assinado",
          watermarkSequence: 9,
        }}
      />,
    );

    expect(await screen.findByRole("dialog", { name: "Novos leads" })).toBeTruthy();
    expect(screen.getByText("Beatriz Lima")).toBeTruthy();
  });

  it("mantém a janela aberta após falha de confirmação", async () => {
    acknowledge.mockResolvedValue({
      ok: false,
      message: "Não foi possível confirmar os novos leads.",
    });
    const user = userEvent.setup();
    render(<NewLeadsNotificationModal snapshot={snapshot} />);

    await user.keyboard("{Escape}");

    expect((await screen.findByRole("alert")).textContent).toContain(
      "Não foi possível confirmar os novos leads.",
    );
    expect(screen.getByRole("dialog", { name: "Novos leads" })).toBeTruthy();
  });

  it("permite nova tentativa quando a confirmação remota é rejeitada", async () => {
    acknowledge.mockRejectedValue(new Error("falha de transporte"));
    const user = userEvent.setup();
    render(<NewLeadsNotificationModal snapshot={snapshot} />);

    await user.click(screen.getByRole("button", { name: "Fechar" }));

    expect((await screen.findByRole("alert")).textContent).toContain(
      "Não foi possível confirmar os novos leads.",
    );
    expect(screen.getByRole("dialog", { name: "Novos leads" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Fechar" }).hasAttribute("disabled")).toBe(false);
  });

  it("devolve o foco anterior depois de fechar", async () => {
    acknowledge.mockResolvedValue({ ok: true, message: "Novos leads confirmados." });
    const user = userEvent.setup();
    const trigger = document.createElement("button");
    trigger.textContent = "Origem";
    document.body.append(trigger);
    trigger.focus();

    render(<NewLeadsNotificationModal snapshot={snapshot} />);
    await user.click(screen.getByRole("button", { name: "Fechar" }));

    await waitFor(() => expect(document.activeElement).toBe(trigger));
    trigger.remove();
  });
});
````

## Snapshot de código: `apps/web/src/components/new-leads-notification-modal.tsx`

````tsx
"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import type { NewLeadNotificationSnapshot } from "../lib/api/types";
import { formatDateTime } from "../lib/dashboard/format";
import { acknowledgeNewLeadsAction } from "../lib/notifications/actions";

export function NewLeadsNotificationModal({
  snapshot,
}: {
  snapshot: NewLeadNotificationSnapshot;
}) {
  const [open, setOpen] = useState(true);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const closeRef = useRef<HTMLButtonElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);
  const wasOpenRef = useRef(true);
  const snapshotIdentity = `${snapshot.watermarkSequence}:${snapshot.acknowledgementToken}`;
  const previousSnapshotIdentityRef = useRef(snapshotIdentity);
  const titleId = "new-leads-notification-title";

  useEffect(() => {
    if (previousSnapshotIdentityRef.current === snapshotIdentity) return;
    previousSnapshotIdentityRef.current = snapshotIdentity;
    setOpen(true);
    setPending(false);
    setError(null);
  }, [snapshotIdentity]);

  useEffect(() => {
    if (open) {
      previousFocusRef.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
      closeRef.current?.focus();
    } else if (wasOpenRef.current) {
      previousFocusRef.current?.focus();
    }
    wasOpenRef.current = open;
  }, [open]);

  const close = useCallback(async () => {
    if (pending) return;
    setPending(true);
    setError(null);
    try {
      const result = await acknowledgeNewLeadsAction(snapshot);
      if (result.ok) {
        setOpen(false);
        return;
      }
      setError(result.message);
    } catch {
      setError("Não foi possível confirmar os novos leads.");
    } finally {
      setPending(false);
    }
  }, [pending, snapshot]);

  if (!open) return null;

  return (
    <div
      className="modal-backdrop"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) void close();
      }}
    >
      <section
        className="modal-card new-leads-notification-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onKeyDown={(event) => {
          if (event.key === "Escape") {
            event.preventDefault();
            void close();
          }
          if (event.key === "Tab") event.preventDefault();
        }}
      >
        <p className="eyebrow">Novas atribuições</p>
        <h3 id={titleId}>Novos leads</h3>
        <p className="muted">Confira os leads recebidos desde sua última confirmação.</p>
        <ol className="new-leads-notification-modal__list" aria-label="Leads recebidos">
          {snapshot.items.map((lead) => (
            <li key={lead.leadId}>
              <strong>{lead.contactName}</strong>
              <span>Recebido em {formatDateTime(lead.assignedAt)}</span>
            </li>
          ))}
        </ol>
        {error ? (
          <p className="form-error" role="alert">
            {error}
          </p>
        ) : null}
        <div className="modal-actions">
          <button
            ref={closeRef}
            type="button"
            className="table-action"
            disabled={pending}
            onClick={() => void close()}
          >
            {pending ? "Confirmando…" : "Fechar"}
          </button>
        </div>
      </section>
    </div>
  );
}
````

## Snapshot de código: `apps/web/src/components/pagination.test.tsx`

````tsx
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { Pagination } from "./pagination";

describe("Pagination", () => {
  it("usa botões acessíveis, mantém a query e desabilita limites", () => {
    const markup = renderToStaticMarkup(
      createElement(Pagination, {
        href: "/historico",
        page: { items: [], page: 1, pageSize: 10, total: 20 },
        searchParams: { campaign: "campanha-1", page: "1" },
      }),
    );

    expect(markup).toMatch(
      /<button[^>]*disabled=""[^>]*aria-label="Página anterior"[^>]*name="page"/,
    );
    expect(markup).toMatch(/<button[^>]*value="2"[^>]*aria-label="Próxima página"[^>]*name="page"/);
    expect(markup).toContain('name="campaign" value="campanha-1"');
    expect(markup).toContain("Página 1 de 2");
    expect(markup).not.toContain("AnteriorPágina");
  });

  it("desabilita a próxima página no fim da coleção", () => {
    const markup = renderToStaticMarkup(
      createElement(Pagination, {
        href: "/historico",
        page: { items: [], page: 2, pageSize: 10, total: 20 },
      }),
    );

    expect(markup).toMatch(
      /<button[^>]*value="2"[^>]*disabled=""[^>]*aria-label="Próxima página"[^>]*name="page"/,
    );
  });
});
````

## Snapshot de código: `apps/web/src/components/pagination.tsx`

````tsx
import type { Page } from "../lib/api/types";

type SearchParams = Record<string, string | string[] | undefined>;

function preservedParams(searchParams: SearchParams): Array<[string, string]> {
  return Object.entries(searchParams).flatMap(([key, value]) => {
    if (key === "page" || value === undefined) return [];
    return Array.isArray(value)
      ? value.map((entry) => [key, entry] as [string, string])
      : [[key, value]];
  });
}

export function Pagination({
  href,
  page,
  searchParams = {},
}: {
  href: string;
  page: Page<unknown>;
  searchParams?: SearchParams;
}) {
  const lastPage = Math.max(1, Math.ceil(page.total / page.pageSize));
  const previousPage = Math.max(1, page.page - 1);
  const nextPage = Math.min(lastPage, page.page + 1);
  const params = preservedParams(searchParams);
  return (
    <nav className="pagination" aria-label="Paginação">
      <form action={href} method="get">
        {params.map(([key, value], index) => (
          <input key={`${key}-${index}`} type="hidden" name={key} value={value} />
        ))}
        <button
          type="submit"
          name="page"
          value={previousPage}
          disabled={page.page <= 1}
          aria-label="Página anterior"
        >
          Anterior
        </button>
      </form>
      <strong>
        Página {page.page} de {lastPage}
      </strong>
      <form action={href} method="get">
        {params.map(([key, value], index) => (
          <input key={`${key}-${index}`} type="hidden" name={key} value={value} />
        ))}
        <button
          type="submit"
          name="page"
          value={nextPage}
          disabled={page.page >= lastPage}
          aria-label="Próxima página"
        >
          Próxima
        </button>
      </form>
    </nav>
  );
}
````

## Snapshot de código: `apps/web/src/components/queue-table.test.tsx`

````tsx
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { QueueTable } from "./queue-table";

describe("QueueTable", () => {
  it("exibe a ordem operacional atual em vez da posição fixa do cadastro", () => {
    const markup = renderToStaticMarkup(
      createElement(QueueTable, {
        queue: {
          cursorSellerName: "Renato",
          nextSellerName: "Jessica",
          total: 3,
          items: [
            {
              sellerName: "Jessica",
              position: 3,
              availability: "active",
              reason: null,
              skipBalance: 0,
            },
            {
              sellerName: "Nelma",
              position: 4,
              availability: "active",
              reason: null,
              skipBalance: 0,
            },
            {
              sellerName: "Renato",
              position: 1,
              availability: "paused",
              reason: "Pausado manualmente",
              skipBalance: 1,
            },
          ],
        },
      }),
    );

    expect(markup).toContain("Cursor atual");
    expect(markup).toContain("Renato");
    expect(markup).toContain("Próximo elegível");
    expect(markup).toContain("Jessica");
    expect(markup).toContain("Ordem atual");
    expect(markup).toContain("Posição base");
    expect(markup).toContain("<td>1</td>");
    expect(markup).toContain("<td>3</td>");
    expect(markup).toContain("Pausado");
    expect(markup).toContain("Créditos de pulo");
  });
});
````

## Snapshot de código: `apps/web/src/components/queue-table.tsx`

````tsx
import type { AdminQueue, QueueEntry } from "../lib/api/types";

function availabilityLabel(availability: QueueEntry["availability"]): string {
  return availability === "paused" ? "Pausado" : "Ativo";
}

function availabilityReason(item: QueueEntry): string {
  return item.reason ?? "Disponível para novas atribuições";
}

export function QueueTable({ queue }: { queue: AdminQueue }) {
  return (
    <section className="table-card queue-table-card" aria-labelledby="queue-table-title">
      <div className="table-head">
        <div>
          <p className="eyebrow">Dados ao vivo</p>
          <h2 id="queue-table-title">Fila comercial</h2>
        </div>
        <dl className="queue-table-summary">
          <div>
            <dt>Cursor atual</dt>
            <dd>{queue.cursorSellerName}</dd>
          </div>
          <div>
            <dt>Próximo elegível</dt>
            <dd>{queue.nextSellerName}</dd>
          </div>
        </dl>
      </div>
      {queue.items.length === 0 ? (
        <p className="empty">Nenhum vendedor cadastrado na fila.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Ordem atual</th>
              <th>Posição base</th>
              <th>Vendedor</th>
              <th>Disponibilidade</th>
              <th>Motivo</th>
              <th>Créditos de pulo</th>
            </tr>
          </thead>
          <tbody>
            {queue.items.map((item, index) => (
              <tr key={`${item.position}-${item.sellerName}`}>
                <td>{index + 1}</td>
                <td>{item.position}</td>
                <td>
                  <strong>{item.sellerName}</strong>
                </td>
                <td>
                  <span className={`status-badge status-badge--${item.availability === "paused" ? "paused" : "active"}`}>
                    {availabilityLabel(item.availability)}
                  </span>
                </td>
                <td>{availabilityReason(item)}</td>
                <td>{item.skipBalance}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
````

## Snapshot de código: `apps/web/src/components/reports-dashboard.test.tsx`

````tsx
// @vitest-environment jsdom

import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { ReportsDashboard } from "./reports-dashboard";

const report = {
  period: { from: "2026-09-01T00:00:00.000Z", to: "2026-09-15T00:00:00.000Z" },
  bySituation: [
    { commercialStatus: "potential" as const, count: 3 },
    { commercialStatus: "won" as const, count: 1 },
  ],
  bySeller: [{ sellerId: "seller-1", sellerName: "Jessica", count: 4 }],
};

afterEach(cleanup);

describe("ReportsDashboard", () => {
  it("renderiza distribui\u00e7\u00f5es por situa\u00e7\u00e3o e vendedor com equivalentes textuais", () => {
    render(<ReportsDashboard report={report} period="all" />);

    expect(screen.getByRole("heading", { name: "Por situa\u00e7\u00e3o" })).toBeTruthy();
    expect(screen.getByText("Potencial: 3")).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Por vendedor" })).toBeTruthy();
    expect(screen.getByText("Jessica: 4")).toBeTruthy();
  });

  it("mostra estado vazio para ambas as distribui\u00e7\u00f5es", () => {
    render(<ReportsDashboard report={{ ...report, bySituation: [], bySeller: [] }} period="all" />);

    expect(screen.getAllByText("Nenhum dado para o per\u00edodo selecionado.")).toHaveLength(2);
  });
});
````

## Snapshot de código: `apps/web/src/components/reports-dashboard.tsx`

````tsx
import type { LeadDistributionReport } from "../lib/api/types";
import { formatCommercialStatus } from "../lib/dashboard/format";
import type { ReportPeriodKey } from "../lib/reports/queries";

const SAO_PAULO_TIME_ZONE = "America/Sao_Paulo";

function DistributionBars({
  items,
  label,
}: {
  items: Array<{ name: string; count: number }>;
  label: string;
}) {
  if (items.length === 0) return <p className="empty-state">Nenhum dado para o período selecionado.</p>;
  const maximum = Math.max(...items.map((item) => item.count), 1);
  return (
    <ul className="report-bars" aria-label={label}>
      {items.map((item) => (
        <li key={item.name} className="report-bar">
          <span className="report-bar__label">{item.name}: {item.count}</span>
          <span className="report-bar__track" aria-hidden="true">
            <span className="report-bar__fill" style={{ width: `${(item.count / maximum) * 100}%` }} />
          </span>
        </li>
      ))}
    </ul>
  );
}

function saoPauloDateInputValue(value: string | null | undefined): string {
  if (!value) return "";
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: SAO_PAULO_TIME_ZONE,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(new Date(value));
  const fields = Object.fromEntries(
    parts.filter((part) => part.type !== "literal").map((part) => [part.type, part.value]),
  );
  return `${fields.year}-${fields.month}-${fields.day}`;
}

export function ReportsDashboard({
  report,
  period,
  error,
  from,
  to,
  interval,
}: {
  report: LeadDistributionReport | null;
  period: ReportPeriodKey;
  error?: string | null;
  from?: string | null;
  to?: string | null;
  interval?: { from: string; to: string };
}) {
  const reportPeriod = report?.period ?? interval;
  const customFrom = from ?? (period === "custom" ? saoPauloDateInputValue(reportPeriod?.from) : "");
  const customTo = to ?? (period === "custom" ? saoPauloDateInputValue(reportPeriod?.to) : "");
  const periodFrom = reportPeriod?.from ?? (customFrom ? `${customFrom}T00:00:00` : null);
  const periodTo = reportPeriod?.to ?? (customTo ? `${customTo}T00:00:00` : null);

  return (
    <section className="reports-dashboard">
      <form className="report-filters" action="/relatorios" method="get">
        <label>
          Período
          <select name="period" defaultValue={period}>
            <option value="all">Todo o histórico</option>
            <option value="month">Mês atual</option>
            <option value="last30">Últimos 30 dias</option>
            <option value="custom">Personalizado</option>
          </select>
        </label>
        <label>De<input name="from" type="date" defaultValue={customFrom} /></label>
        <label>Até<input name="to" type="date" defaultValue={customTo} /></label>
        <button className="table-action" type="submit">{error ? "Tentar novamente" : "Atualizar relatório"}</button>
      </form>
      {periodFrom && periodTo ? (
        <p className="muted">Período baseado na atribuição atual: {periodFrom} até {periodTo}.</p>
      ) : null}
      {error ? <p className="form-error" role="alert">{error}</p> : null}
      {report ? (
        <>
          <section className="report-card" aria-labelledby="report-by-situation">
            <h2 id="report-by-situation">Por situação</h2>
            <DistributionBars label="Distribuição por situação" items={report.bySituation.map((item) => ({ name: formatCommercialStatus(item.commercialStatus), count: item.count }))} />
          </section>
          <section className="report-card" aria-labelledby="report-by-seller">
            <h2 id="report-by-seller">Por vendedor</h2>
            <DistributionBars label="Distribuição por vendedor" items={report.bySeller.map((item) => ({ name: item.sellerName, count: item.count }))} />
          </section>
        </>
      ) : null}
    </section>
  );
}
````

## Snapshot de código: `apps/web/src/components/reports-dashboard-regression.test.tsx`

````tsx
// @vitest-environment jsdom

import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { ReportsDashboard } from "./reports-dashboard";

afterEach(cleanup);

describe("regressões do painel de relatórios", () => {
  it("mantém datas e contexto do intervalo personalizado no formulário", () => {
    render(
      <ReportsDashboard
        report={{
          period: { from: "2026-09-01T03:00:00.000Z", to: "2026-09-15T03:00:00.000Z" },
          bySituation: [],
          bySeller: [],
        }}
        period="custom"
      />,
    );

    expect(screen.getByLabelText("De").getAttribute("value")).toBe("2026-09-01");
    expect(screen.getByLabelText("Até").getAttribute("value")).toBe("2026-09-15");
    expect(screen.getByText(/baseado na atribuição atual/i)).toBeTruthy();
  });

  it("mantem datas personalizadas quando a consulta falha", () => {
    render(
      <ReportsDashboard
        report={null}
        period="custom"
        error="Erro ao carregar relatorio."
        interval={{
          from: "2026-09-01T03:00:00.000Z",
          to: "2026-09-15T03:00:00.000Z",
        }}
      />,
    );

    expect(screen.getByLabelText("De").getAttribute("value")).toBe("2026-09-01");
    expect(screen.getByRole("alert")).toBeTruthy();
  });
});
````

## Snapshot de código: `apps/web/src/components/seller-dashboard.tsx`

````tsx
import type {
  SellerAvailability,
  SellerDashboard as SellerDashboardData,
  Treatment,
} from "../lib/api/types";
import {
  formatCommentCount,
  formatCommercialStatus,
  formatDateTime,
  formatDisqualificationMarker,
} from "../lib/dashboard/format";
import { LeadTable } from "./lead-table";

function availabilityLabel(availability: SellerAvailability): string {
  return availability === "paused" ? "Pausado pelo administrador" : "Disponível para novas atribuições";
}

function TreatmentPreview({ item }: { item: Treatment }) {
  return (
    <li className="activity-item">
      <div>
        <strong>{item.leadName ?? "Lead não informado"}</strong>
        <small>{item.comment}</small>
      </div>
      <div className="activity-item__meta">
        <span className={`commercial-status ${item.commercialStatus}`}>
          {formatCommercialStatus(item.commercialStatus)}
        </span>
        <small>{formatDateTime(item.createdAt)}</small>
        {item.isDisqualified ? (
          <span className="disqualification-marker">{formatDisqualificationMarker(true)}</span>
        ) : null}
      </div>
    </li>
  );
}

export function SellerDashboard({ dashboard }: { dashboard: SellerDashboardData }) {
  const queuePosition =
    typeof dashboard.queue.position === "number" && Number.isFinite(dashboard.queue.position)
      ? dashboard.queue.position
      : null;

  return (
    <>
      <section className="metric-grid metric-grid--seller" aria-label="Resumo da minha operação">
        <article className="metric-card metric-card--accent">
          <span>Meus leads</span>
          <strong>{dashboard.leads.total}</strong>
        </article>
        <article className="metric-card">
          <span>Meus comentários</span>
          <strong>{formatCommentCount(dashboard.history.total)}</strong>
        </article>
        <article className="metric-card metric-card--next">
          <span>Minha posição na fila</span>
          <strong className="metric-card__text">
            {queuePosition === null
              ? "Não informado"
              : `Posição ${queuePosition}`}
          </strong>
        </article>
      </section>

      <section
        className="dashboard-layout dashboard-layout--seller"
        aria-label="Minha atividade recente"
      >
        <section className="dashboard-panel">
          <p className="eyebrow">Minha disponibilidade</p>
          <h2>{availabilityLabel(dashboard.queue.availability)}</h2>
          <p className="dashboard-copy">Saldo de pulos: {dashboard.queue.skipBalance}</p>
        </section>
        <section className="dashboard-panel">
          <header className="dashboard-panel__header">
            <div>
              <p className="eyebrow">Minha atividade</p>
              <h2>Últimas tratativas</h2>
            </div>
          </header>
          {dashboard.history.items.length === 0 ? (
            <p className="empty-state">Você ainda não registrou tratativas.</p>
          ) : (
            <ol className="activity-list">
              {dashboard.history.items.slice(0, 5).map((item, index) => (
                <TreatmentPreview item={item} key={`${item.createdAt}-${index}`} />
              ))}
            </ol>
          )}
        </section>
      </section>

      <LeadTable leads={dashboard.leads.items} role="seller" />
    </>
  );
}
````

## Snapshot de código: `apps/web/src/components/seller-queue-table.test.tsx`

````tsx
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { SellerQueueTable } from "./seller-queue-table";

describe("SellerQueueTable", () => {
  it("mostra a posição e disponibilidade do vendedor sem dados globais da fila", () => {
    const markup = renderToStaticMarkup(
      createElement(SellerQueueTable, {
        queue: { position: 3, availability: "active", skipBalance: 0 },
        leads: [],
      }),
    );

    expect(markup).toContain("Minha fila");
    expect(markup).toContain("Posição 3");
    expect(markup).toContain("Disponível para novas atribuições");
    expect(markup).not.toContain("Renato");
    expect(markup).not.toContain("Jessica");
  });

  it("informa quando a posição não está disponível", () => {
    const markup = renderToStaticMarkup(
      createElement(SellerQueueTable, {
        queue: { position: null, availability: "paused", skipBalance: 2 },
        leads: [],
      }),
    );

    expect(markup).toContain("Posição não informada");
    expect(markup).toContain("Pausado pelo administrador");
    expect(markup).toContain("Saldo de pulos: 2");
  });
});
````

## Snapshot de código: `apps/web/src/components/seller-queue-table.tsx`

````tsx
import type { OperationalLead, SellerAvailability, SellerQueue } from "../lib/api/types";
import { formatDateTime } from "../lib/dashboard/format";

function availabilityLabel(availability: SellerAvailability): string {
  return availability === "paused" ? "Pausado pelo administrador" : "Disponível para novas atribuições";
}

export function SellerQueueTable({
  queue,
  leads,
}: {
  queue: SellerQueue;
  leads: OperationalLead[];
}) {
  return (
    <section className="table-card seller-queue-card" aria-labelledby="seller-queue-title">
      <div className="table-head">
        <div>
          <p className="eyebrow">Minha distribuição</p>
          <h2 id="seller-queue-title">Minha fila</h2>
        </div>
        <dl className="queue-table-summary">
          <div>
            <dt>Minha posição</dt>
            <dd>
              {queue.position === null ? "Posição não informada" : `Posição ${queue.position}`}
            </dd>
          </div>
          <div>
            <dt>Disponibilidade</dt>
            <dd>
              <span className={`status-badge status-badge--${queue.availability === "paused" ? "paused" : "active"}`}>
                {availabilityLabel(queue.availability)}
              </span>
            </dd>
          </div>
          <div>
            <dt>Saldo</dt>
            <dd>Saldo de pulos: {queue.skipBalance}</dd>
          </div>
        </dl>
      </div>
      {leads.length === 0 ? (
        <p className="empty">Nenhum lead atribuído a você.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Lead</th>
              <th>Atribuído em</th>
              <th>Última atualização</th>
            </tr>
          </thead>
          <tbody>
            {leads.map((lead) => (
              <tr key={lead.id}>
                <td>
                  <strong>{lead.contactName}</strong>
                </td>
                <td>{formatDateTime(lead.assignedAt)}</td>
                <td>{formatDateTime(lead.lastUpdatedAt)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
````

## Snapshot de código: `apps/web/src/components/treatment-history-table.test.tsx`

````tsx
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { TreatmentHistoryTable } from "./treatment-history-table";

describe("TreatmentHistoryTable", () => {
  it("agrupa a conversa por lead com vendedor, início, última atualização e comentários", () => {
    const markup = renderToStaticMarkup(
      createElement(TreatmentHistoryTable, {
        treatments: [
          {
            leadId: "lead-1",
            leadName: "Débora Souza",
            sellerName: "Renato",
            comment: "Primeiro contato realizado por telefone.",
            commercialStatus: "won",
            isDisqualified: true,
            assignedAt: "2026-08-28T15:30:00.000Z",
            lastUpdatedAt: "2026-08-28T16:03:04.876Z",
            createdAt: "2026-08-28T16:03:04.876Z",
          },
          {
            leadId: "lead-1",
            leadName: "Débora Souza",
            sellerName: "Renato",
            comment: "Cliente pediu retorno com proposta.",
            commercialStatus: "negotiation",
            isDisqualified: false,
            assignedAt: "2026-08-28T15:30:00.000Z",
            lastUpdatedAt: "2026-08-28T16:10:00.000Z",
            createdAt: "2026-08-28T15:40:00.000Z",
          },
        ],
      }),
    );

    expect(markup).toContain("Tratativas");
    expect(markup).toContain("Débora Souza");
    expect(markup).toContain("Renato");
    expect(markup).toContain("Início");
    expect(markup).toContain("Última atualização");
    expect(markup).toContain("Primeiro contato realizado por telefone.");
    expect(markup).toContain("Cliente pediu retorno com proposta.");
    expect(markup).toContain("Ganho");
    expect(markup).toContain("Desqualificado");
    expect(markup).toContain("28/08/2026");
    expect(markup).not.toContain("Atribuições");
  });
});
````

## Snapshot de código: `apps/web/src/components/treatment-history-table.tsx`

````tsx
import type { Treatment } from "../lib/api/types";
import {
  formatCommercialStatus,
  formatDateTime,
  formatDisqualificationMarker,
  formatText,
} from "../lib/dashboard/format";

type LeadConversation = {
  leadId: string;
  leadName: string;
  sellerName: string;
  assignedAt: string | null;
  lastUpdatedAt: string | null;
  items: Treatment[];
};

export function groupTreatmentsByLead(treatments: Treatment[]): LeadConversation[] {
  const groups = new Map<string, LeadConversation>();
  for (const treatment of treatments) {
    const current = groups.get(treatment.leadId);
    if (current) {
      current.items.push(treatment);
      current.lastUpdatedAt = treatment.lastUpdatedAt ?? current.lastUpdatedAt;
      continue;
    }
    groups.set(treatment.leadId, {
      leadId: treatment.leadId,
      leadName: formatText(treatment.leadName),
      sellerName: formatText(treatment.sellerName),
      assignedAt: treatment.assignedAt,
      lastUpdatedAt: treatment.lastUpdatedAt,
      items: [treatment],
    });
  }
  return Array.from(groups.values());
}

export function TreatmentHistoryTable({ treatments }: { treatments: Treatment[] }) {
  const conversations = groupTreatmentsByLead(treatments);
  return (
    <section
      className="table-card treatment-history-table"
      aria-labelledby="treatment-history-title"
    >
      <div className="table-head">
        <div>
          <p className="eyebrow">Dados ao vivo</p>
          <h2 id="treatment-history-title">Tratativas</h2>
        </div>
      </div>
      {conversations.length === 0 ? (
        <p className="empty">Nenhuma tratativa registrada.</p>
      ) : (
        <div className="treatment-conversations">
          {conversations.map((conversation) => (
            <article className="treatment-conversation-card" key={conversation.leadId}>
              <header className="treatment-conversation-card__header">
                <div>
                  <p className="eyebrow">Lead</p>
                  <h3>{conversation.leadName}</h3>
                </div>
                <dl className="treatment-conversation-card__meta">
                  <div>
                    <dt>Vendedor</dt>
                    <dd>{conversation.sellerName}</dd>
                  </div>
                  <div>
                    <dt>Início</dt>
                    <dd>{formatDateTime(conversation.assignedAt)}</dd>
                  </div>
                  <div>
                    <dt>Última atualização</dt>
                    <dd>{formatDateTime(conversation.lastUpdatedAt)}</dd>
                  </div>
                </dl>
              </header>
              <ol className="treatment-history">
                {conversation.items.map((treatment, index) => (
                  <li className="treatment-history__item" key={`${treatment.createdAt}-${index}`}>
                    <div>
                      <strong>{formatDateTime(treatment.createdAt)}</strong>
                      <p>{formatText(treatment.comment)}</p>
                    </div>
                    <div className="treatment-history__meta">
                      <span className={`commercial-status ${treatment.commercialStatus}`}>
                        {formatCommercialStatus(treatment.commercialStatus)}
                      </span>
                      {treatment.isDisqualified ? (
                        <span className="disqualification-marker">
                          {formatDisqualificationMarker(true)}
                        </span>
                      ) : null}
                    </div>
                  </li>
                ))}
              </ol>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
````

## Snapshot de código: `apps/web/src/components/user-form-modal.tsx`

````tsx
"use client";

import { useEffect, useRef, useState } from "react";

import type { CreateManagedUserInput, ManagedUser, UserRole } from "../lib/api/types";
import type { UserMutationResult } from "../lib/users/actions";

export function UserFormModal({ onClose, onCreated, onSubmit }: {
  onClose: () => void;
  onCreated: (user: ManagedUser, message: string) => void;
  onSubmit: (input: CreateManagedUserInput) => Promise<UserMutationResult>;
}) {
  const initialInput = useRef<HTMLInputElement>(null);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<UserRole>("seller");
  const [password, setPassword] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const canSubmit = Boolean(fullName.trim() && email.trim() && password.trim() && !pending);

  useEffect(() => {
    initialInput.current?.focus();
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !pending) onClose();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose, pending]);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmit) return;
    setPending(true);
    setError(null);
    try {
      const result = await onSubmit({ fullName: fullName.trim(), email: email.trim(), role, password });
      if (result.status === "success") {
        setPassword("");
        onCreated(result.user, result.message);
      } else setError(result.message);
    } catch {
      setError("Não foi possível concluir a ação. Tente novamente.");
    } finally {
      setPending(false);
    }
  }

  return <div className="modal-backdrop" role="presentation" onMouseDown={(event) => {
    if (event.target === event.currentTarget && !pending) onClose();
  }}>
    <section className="modal-card" role="dialog" aria-modal="true" aria-labelledby="new-user-title">
      <h3 id="new-user-title">Novo usuário</h3>
      <form onSubmit={submit}>
        <label htmlFor="new-user-name">Nome completo
          <input ref={initialInput} id="new-user-name" value={fullName} onChange={(event) => setFullName(event.target.value)} autoComplete="name" required />
        </label>
        <label htmlFor="new-user-email">E-mail
          <input id="new-user-email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" required />
        </label>
        <label htmlFor="new-user-role">Papel
          <select id="new-user-role" value={role} onChange={(event) => setRole(event.target.value as UserRole)}>
            <option value="seller">Vendedor</option>
            <option value="admin">Administrador</option>
          </select>
        </label>
        <label htmlFor="new-user-password">Senha inicial
          <input id="new-user-password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="new-password" required />
        </label>
        {error ? <p className="form-error" role="status">{error}</p> : null}
        <div className="modal-actions">
          <button type="button" className="secondary-button" disabled={pending} onClick={onClose}>Cancelar</button>
          <button type="submit" className="table-action" disabled={!canSubmit}>{pending ? "Criando…" : "Criar usuário"}</button>
        </div>
      </form>
    </section>
  </div>;
}
````

## Snapshot de código: `apps/web/src/components/user-management.test.tsx`

````tsx
// @vitest-environment jsdom

import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { ManagedUser } from "../lib/api/types";

const actions = vi.hoisted(() => ({
  create: vi.fn(),
  availability: vi.fn(),
  resetPassword: vi.fn(),
}));

const navigation = vi.hoisted(() => ({ push: vi.fn(), refresh: vi.fn() }));

vi.mock("../lib/users/actions", () => ({
  createManagedUserAction: actions.create,
  setManagedUserAvailabilityAction: actions.availability,
  resetManagedUserPasswordAction: actions.resetPassword,
}));

vi.mock("next/navigation", () => ({ useRouter: () => navigation }));

import { UserManagement } from "./user-management";

const users: ManagedUser[] = [
  { id: "admin-1", fullName: "Yago", email: "yago@wtgseguros.com.br", role: "admin", active: true, paused: null },
  { id: "seller-1", fullName: "Renato", email: "renato@wtgseguros.com.br", role: "seller", active: true, paused: false },
];

const createdSeller: ManagedUser = {
  id: "seller-2",
  fullName: "Sandra",
  email: "sandra@wtgseguros.com.br",
  role: "seller",
  active: true,
  paused: false,
};

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("gestão operacional de usuários", () => {
  it("abre o cadastro com foco inicial e exige uma senha não vazia", async () => {
    const user = userEvent.setup();
    render(<UserManagement users={users} />);

    const trigger = screen.getByRole("button", { name: "Novo usuário" });
    await user.click(trigger);

    expect(screen.getByRole("dialog", { name: "Novo usuário" })).toBeTruthy();
    expect(document.activeElement).toBe(screen.getByLabelText("Nome completo"));
    expect((screen.getByRole("button", { name: "Criar usuário" }) as HTMLButtonElement).disabled).toBe(true);

    await user.type(screen.getByLabelText("Nome completo"), "Sandra");
    await user.type(screen.getByLabelText("E-mail"), "sandra@wtgseguros.com.br");
    await user.type(screen.getByLabelText("Senha inicial"), "   ");
    expect((screen.getByRole("button", { name: "Criar usuário" }) as HTMLButtonElement).disabled).toBe(true);

    await user.clear(screen.getByLabelText("Senha inicial"));
    await user.type(screen.getByLabelText("Senha inicial"), "senha inicial");
    expect((screen.getByRole("button", { name: "Criar usuário" }) as HTMLButtonElement).disabled).toBe(false);
  });

  it("cria usuário, atualiza a lista e nunca apresenta a senha salva", async () => {
    actions.create.mockResolvedValue({ status: "success", message: "Usuário criado.", user: createdSeller });
    const user = userEvent.setup();
    render(<UserManagement users={users} />);

    await user.click(screen.getByRole("button", { name: "Novo usuário" }));
    await user.type(screen.getByLabelText("Nome completo"), "Sandra");
    await user.type(screen.getByLabelText("E-mail"), "sandra@wtgseguros.com.br");
    await user.type(screen.getByLabelText("Senha inicial"), "senha confidencial");
    await user.click(screen.getByRole("button", { name: "Criar usuário" }));

    await waitFor(() => expect(actions.create).toHaveBeenCalledWith({
      fullName: "Sandra",
      email: "sandra@wtgseguros.com.br",
      role: "seller",
      password: "senha confidencial",
    }));
    expect((await screen.findByRole("status")).textContent).toContain("Usuário criado.");
    expect(screen.getByText("Sandra")).toBeTruthy();
    expect(screen.queryByText("senha confidencial")).toBeNull();
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("mostra carregamento enquanto o cadastro aguarda a resposta", async () => {
    let resolveCreation: ((value: unknown) => void) | undefined;
    actions.create.mockImplementation(() => new Promise((resolve) => { resolveCreation = resolve; }));
    const user = userEvent.setup();
    render(<UserManagement users={users} />);

    await user.click(screen.getByRole("button", { name: "Novo usuário" }));
    await user.type(screen.getByLabelText("Nome completo"), "Sandra");
    await user.type(screen.getByLabelText("E-mail"), "sandra@wtgseguros.com.br");
    await user.type(screen.getByLabelText("Senha inicial"), "senha inicial");
    await user.click(screen.getByRole("button", { name: "Criar usuário" }));
    expect(screen.getByRole("button", { name: "Criando…" })).toBeTruthy();

    resolveCreation?.({ status: "success", message: "Usuário criado.", user: createdSeller });
    await screen.findByRole("status");
  });

  it("confirma a pausa de vendedor e atualiza seu estado visível", async () => {
    actions.availability.mockResolvedValue({
      status: "success",
      message: "Vendedor pausado.",
      user: { ...users[1], paused: true },
    });
    const user = userEvent.setup();
    render(<UserManagement users={users} />);

    await user.click(screen.getByRole("button", { name: "Pausar Renato" }));
    expect(screen.getByRole("dialog", { name: "Confirmar pausa" })).toBeTruthy();
    await user.click(screen.getByRole("button", { name: "Confirmar pausa" }));

    await waitFor(() => expect(actions.availability).toHaveBeenCalledWith("seller-1", true));
    expect((await screen.findByRole("status")).textContent).toContain("Vendedor pausado.");
    expect(screen.getByText("Pausado")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Ativar Renato" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Pausar Yago" })).toBeNull();
  });

  it("mostra conta inativa sem oferecer uma pausa manual inválida", () => {
    render(<UserManagement users={[...users, {
      id: "seller-3",
      fullName: "Nelma",
      email: "nelma@wtgseguros.com.br",
      role: "seller",
      active: false,
      paused: false,
    }]} />);

    expect(screen.getByText("Inativo")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Pausar Nelma" })).toBeNull();
  });

  it("exige senha nova e confirma a redefinição sem expor seu conteúdo", async () => {
    actions.resetPassword.mockResolvedValue({ status: "success", message: "Senha redefinida.", user: users[1] });
    const user = userEvent.setup();
    render(<UserManagement users={users} />);

    await user.click(screen.getByRole("button", { name: "Redefinir senha de Renato" }));
    expect(screen.getByRole("dialog", { name: "Redefinir senha" })).toBeTruthy();
    expect((screen.getByRole("button", { name: "Salvar nova senha" }) as HTMLButtonElement).disabled).toBe(true);
    await user.type(screen.getByLabelText("Nova senha"), "nova senha secreta");
    await user.click(screen.getByRole("button", { name: "Salvar nova senha" }));
    expect(screen.getByRole("dialog", { name: "Confirmar redefinição de senha" })).toBeTruthy();
    await user.click(screen.getByRole("button", { name: "Confirmar redefinição" }));

    await waitFor(() => expect(actions.resetPassword).toHaveBeenCalledWith("seller-1", "nova senha secreta"));
    expect((await screen.findByRole("status")).textContent).toContain("Senha redefinida.");
    expect(screen.queryByText("nova senha secreta")).toBeNull();
  });

  it("cancela e fecha modais com Escape devolvendo foco ao acionador", async () => {
    const user = userEvent.setup();
    render(<UserManagement users={users} />);
    const trigger = screen.getByRole("button", { name: "Novo usuário" });

    await user.click(trigger);
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(document.activeElement).toBe(trigger);
  });

  it("mantém o modal aberto e apresenta erro seguro quando a ação falha", async () => {
    actions.create.mockResolvedValue({ status: "error", message: "Revise os dados informados e tente novamente.", user: null });
    const user = userEvent.setup();
    render(<UserManagement users={users} />);

    await user.click(screen.getByRole("button", { name: "Novo usuário" }));
    await user.type(screen.getByLabelText("Nome completo"), "Sandra");
    await user.type(screen.getByLabelText("E-mail"), "sandra@wtgseguros.com.br");
    await user.type(screen.getByLabelText("Senha inicial"), "senha inicial");
    await user.click(screen.getByRole("button", { name: "Criar usuário" }));

    expect(await screen.findByText("Revise os dados informados e tente novamente.")).toBeTruthy();
    expect(screen.getByRole("dialog", { name: "Novo usuário" })).toBeTruthy();
  });

  it("recupera rejeição do cadastro sem manter o botão em carregamento", async () => {
    actions.create.mockRejectedValue(new Error("segredo técnico"));
    const user = userEvent.setup();
    render(<UserManagement users={users} />);

    await user.click(screen.getByRole("button", { name: "Novo usuário" }));
    await user.type(screen.getByLabelText("Nome completo"), "Sandra");
    await user.type(screen.getByLabelText("E-mail"), "sandra@wtgseguros.com.br");
    await user.type(screen.getByLabelText("Senha inicial"), "senha inicial");
    await user.click(screen.getByRole("button", { name: "Criar usuário" }));

    expect(await screen.findByText("Não foi possível concluir a ação. Tente novamente.")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Criar usuário" })).toBeTruthy();
  });

  it("recupera rejeição da pausa sem deixar a confirmação bloqueada", async () => {
    actions.availability.mockRejectedValue(new Error("segredo técnico"));
    const user = userEvent.setup();
    render(<UserManagement users={users} />);

    await user.click(screen.getByRole("button", { name: "Pausar Renato" }));
    await user.click(screen.getByRole("button", { name: "Confirmar pausa" }));

    expect((await screen.findByRole("status")).textContent).toContain("Não foi possível concluir a ação. Tente novamente.");
    expect(screen.queryByRole("button", { name: "Salvando…" })).toBeNull();
  });

  it("recupera rejeição da redefinição de senha no formulário", async () => {
    actions.resetPassword.mockRejectedValue(new Error("segredo técnico"));
    const user = userEvent.setup();
    render(<UserManagement users={users} />);

    await user.click(screen.getByRole("button", { name: "Redefinir senha de Renato" }));
    await user.type(screen.getByLabelText("Nova senha"), "nova senha secreta");
    await user.click(screen.getByRole("button", { name: "Salvar nova senha" }));
    await user.click(screen.getByRole("button", { name: "Confirmar redefinição" }));

    expect(await screen.findByText("Não foi possível concluir a ação. Tente novamente.")).toBeTruthy();
    expect(screen.getByRole("dialog", { name: "Redefinir senha" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Salvar nova senha" })).toBeTruthy();
  });

  it("troca para os dados reais da primeira página após criar em uma página posterior", async () => {
    actions.create.mockResolvedValue({ status: "success", message: "Usuário criado.", user: createdSeller });
    const user = userEvent.setup();
    const pageTwoUsers = [users[1]];
    const pageOneUsers = [users[0], createdSeller];
    const view = render(<UserManagement key="users-page-2" users={pageTwoUsers} page={2} />);

    await user.click(screen.getByRole("button", { name: "Novo usuário" }));
    await user.type(screen.getByLabelText("Nome completo"), "Sandra");
    await user.type(screen.getByLabelText("E-mail"), "sandra@wtgseguros.com.br");
    await user.type(screen.getByLabelText("Senha inicial"), "senha inicial");
    await user.click(screen.getByRole("button", { name: "Criar usuário" }));

    await waitFor(() => expect(navigation.push).toHaveBeenCalledWith("/usuarios"));
    view.rerender(<UserManagement key="users-page-1" users={pageOneUsers} page={1} />);
    expect(screen.getByText("Sandra")).toBeTruthy();
    expect(screen.queryByText("Renato")).toBeNull();
  });
});
````

## Snapshot de código: `apps/web/src/components/user-management.tsx`

````tsx
"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";

import type { ManagedUser } from "../lib/api/types";
import {
  createManagedUserAction,
  resetManagedUserPasswordAction,
  setManagedUserAvailabilityAction,
} from "../lib/users/actions";

import { ConfirmActionModal } from "./confirm-action-modal";
import { UserFormModal } from "./user-form-modal";
import { UserPasswordModal } from "./user-password-modal";

type AvailabilityConfirmation = { user: ManagedUser; paused: boolean };

function roleLabel(role: ManagedUser["role"]): string {
  return role === "admin" ? "Administrador" : "Vendedor";
}

function availabilityLabel(user: ManagedUser): string {
  if (!user.active) return "Inativo";
  return user.role === "seller" && user.paused ? "Pausado" : "Ativo";
}

function replaceUser(users: ManagedUser[], updated: ManagedUser): ManagedUser[] {
  return users.map((user) => (user.id === updated.id ? updated : user));
}

export function UserManagement({ users: initialUsers, page = 1 }: { users: ManagedUser[]; page?: number }) {
  const router = useRouter();
  const [users, setUsers] = useState(initialUsers);
  const [newUserOpen, setNewUserOpen] = useState(false);
  const [passwordUser, setPasswordUser] = useState<ManagedUser | null>(null);
  const [availabilityConfirmation, setAvailabilityConfirmation] = useState<AvailabilityConfirmation | null>(null);
  const [pendingAvailability, setPendingAvailability] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const newUserTrigger = useRef<HTMLButtonElement>(null);

  function closeNewUser() {
    setNewUserOpen(false);
    newUserTrigger.current?.focus();
  }

  async function confirmAvailability() {
    if (!availabilityConfirmation) return;
    setPendingAvailability(true);
    try {
      const result = await setManagedUserAvailabilityAction(
        availabilityConfirmation.user.id,
        availabilityConfirmation.paused,
      );
      if (result.status === "success") setUsers((current) => replaceUser(current, result.user));
      setNotice(result.message);
    } catch {
      setNotice("Não foi possível concluir a ação. Tente novamente.");
    } finally {
      setPendingAvailability(false);
      setAvailabilityConfirmation(null);
    }
  }

  return (
    <section className="panel-card" aria-labelledby="user-management-title">
      <div className="panel-head">
        <div>
          <p className="eyebrow">Administração</p>
          <h2 id="user-management-title">Usuários</h2>
          <p className="muted">Crie acessos, pause vendedores e redefina senhas com confirmação.</p>
        </div>
        <button ref={newUserTrigger} type="button" className="table-action" onClick={() => setNewUserOpen(true)}>Novo usuário</button>
      </div>
      {notice ? <p className="form-success" role="status" aria-live="polite">{notice}</p> : null}
      <div className="user-list">
        {users.map((user) => {
          const paused = user.role === "seller" && user.paused === true;
          const availabilityAction = paused ? "Ativar" : "Pausar";
          return (
            <article className="user-card" key={user.id}>
              <div>
                <strong>{user.fullName}</strong>
                <div className="user-card-meta">
                  <span>{user.email}</span>
                  <span className={`pill ${paused ? "disqualified" : "won"}`}>{availabilityLabel(user)}</span>
                  <span>{roleLabel(user.role)}</span>
                </div>
              </div>
              <div className="user-card-actions">
                {user.role === "seller" && user.active ? <button
                  type="button"
                  className="secondary-button"
                  aria-label={`${availabilityAction} ${user.fullName}`}
                  onClick={() => setAvailabilityConfirmation({ user, paused: !paused })}
                >{availabilityAction}</button> : null}
                <button type="button" className="secondary-button" aria-label={`Redefinir senha de ${user.fullName}`} onClick={() => setPasswordUser(user)}>Redefinir senha</button>
              </div>
            </article>
          );
        })}
      </div>
      {newUserOpen ? <UserFormModal
        onClose={closeNewUser}
        onSubmit={createManagedUserAction}
        onCreated={(user, message) => {
          setNotice(message);
          closeNewUser();
          if (page > 1) {
            router.push("/usuarios");
            return;
          }
          setUsers((current) => [...current, user]);
        }}
      /> : null}
      {passwordUser ? <UserPasswordModal
        user={passwordUser}
        onClose={() => setPasswordUser(null)}
        onReset={resetManagedUserPasswordAction}
        onSuccess={(updated, message) => {
          setUsers((current) => replaceUser(current, updated));
          setNotice(message);
          setPasswordUser(null);
        }}
      /> : null}
      {availabilityConfirmation ? <ConfirmActionModal
        title={availabilityConfirmation.paused ? "Confirmar pausa" : "Confirmar ativação"}
        description={availabilityConfirmation.paused
          ? `Pausar ${availabilityConfirmation.user.fullName} para novas atribuições? Os leads atuais permanecem com o vendedor.`
          : `Ativar ${availabilityConfirmation.user.fullName} para voltar a receber novas atribuições.`}
        confirmLabel={availabilityConfirmation.paused ? "Confirmar pausa" : "Confirmar ativação"}
        pending={pendingAvailability}
        onConfirm={() => void confirmAvailability()}
        onCancel={() => setAvailabilityConfirmation(null)}
      /> : null}
    </section>
  );
}
````

## Snapshot de código: `apps/web/src/components/user-password-modal.tsx`

````tsx
"use client";

import { useEffect, useRef, useState } from "react";

import type { ManagedUser } from "../lib/api/types";
import type { UserMutationResult } from "../lib/users/actions";

import { ConfirmActionModal } from "./confirm-action-modal";

export function UserPasswordModal({ user, onClose, onReset, onSuccess }: {
  user: ManagedUser;
  onClose: () => void;
  onReset: (userId: string, password: string) => Promise<UserMutationResult>;
  onSuccess: (updated: ManagedUser, message: string) => void;
}) {
  const passwordRef = useRef<HTMLInputElement>(null);
  const [password, setPassword] = useState("");
  const [confirming, setConfirming] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const canContinue = Boolean(password.trim() && !pending);

  useEffect(() => {
    passwordRef.current?.focus();
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !pending) onClose();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose, pending]);

  async function resetPassword() {
    setPending(true);
    setError(null);
    try {
      const result = await onReset(user.id, password);
      if (result.status === "success") {
        setPassword("");
        onSuccess(result.user, result.message);
        return;
      }
      setConfirming(false);
      setError(result.message);
    } catch {
      setConfirming(false);
      setError("Não foi possível concluir a ação. Tente novamente.");
    } finally {
      setPending(false);
    }
  }

  return <>
    {!confirming ? <div className="modal-backdrop" role="presentation" onMouseDown={(event) => {
      if (event.target === event.currentTarget && !pending) onClose();
    }}>
      <section className="modal-card" role="dialog" aria-modal="true" aria-labelledby="reset-password-title">
        <h3 id="reset-password-title">Redefinir senha</h3>
        <p className="muted">Defina a nova senha de {user.fullName}. As sessões atuais desse usuário serão encerradas.</p>
        <label htmlFor="reset-user-password">Nova senha
          <input ref={passwordRef} id="reset-user-password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="new-password" required />
        </label>
        {error ? <p className="form-error" role="status">{error}</p> : null}
        <div className="modal-actions">
          <button type="button" className="secondary-button" disabled={pending} onClick={onClose}>Cancelar</button>
          <button type="button" className="table-action" disabled={!canContinue} onClick={() => setConfirming(true)}>Salvar nova senha</button>
        </div>
      </section>
    </div> : <ConfirmActionModal
      title="Confirmar redefinição de senha"
      description={`Salvar a nova senha de ${user.fullName} e encerrar as sessões atuais?`}
      confirmLabel="Confirmar redefinição"
      pending={pending}
      onConfirm={() => void resetPassword()}
      onCancel={() => setConfirming(false)}
    />}
  </>;
}
````

## Snapshot de código: `apps/web/src/lib/api/client.test.ts`

````typescript
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  apiFetch,
  createManagedUser,
  getManagedUsers,
  getLeadTreatments,
  resetManagedUserPassword,
  setManagedUserAvailability,
  submitLeadTreatment,
} from "./client";

describe("cliente HTTP operacional", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
  });

  it("chama a API Python pela URL pública e inclui cookies", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "https://api.wtg.example/");
    const request = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify({ status: "ok" }), { status: 200 }));
    vi.stubGlobal("fetch", request);

    await expect(apiFetch<{ status: string }>("/health")).resolves.toEqual({ status: "ok" });
    expect(request).toHaveBeenCalledWith(
      "https://api.wtg.example/health",
      expect.objectContaining({ credentials: "include" }),
    );
  });

  it("não devolve detalhes arbitrários de validação", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "https://api.wtg.example");
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(new Response(JSON.stringify({ detail: "Lead inválido" }), { status: 422 })),
    );

    await expect(apiFetch("/api/leads/inválido/attempts")).rejects.toMatchObject({
      status: 422,
      message: "Revise os dados informados e tente novamente.",
    });
  });

  it.each([
    [401, "Sessão expirada. Entre novamente."],
    [403, "Você não tem permissão para esta ação."],
    [409, "A operação conflita com o estado atual. Atualize os dados e tente novamente."],
    [422, "Revise os dados informados e tente novamente."],
  ])("traduz HTTP %i para erro legível", async (status, message) => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "https://api.wtg.example");
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(null, { status })));

    await expect(apiFetch("/api/dashboard")).rejects.toMatchObject({ status, message });
  });

  it.each([
    [401, "Unauthorized", "Sessão expirada. Entre novamente."],
    [403, "Forbidden", "Você não tem permissão para esta ação."],
    [409, "Email already registered", "A operação conflita com o estado atual. Atualize os dados e tente novamente."],
    [422, "Invalid object id", "Revise os dados informados e tente novamente."],
  ])("não expõe detalhe técnico HTTP %i", async (status, detail, message) => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "https://api.wtg.example");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail }), { status })),
    );

    await expect(apiFetch("/api/dashboard")).rejects.toMatchObject({ status, message });
  });

  it.each([
    [409, "queue changed concurrently", "A operação conflita com o estado atual. Atualize os dados e tente novamente."],
    [409, "retry user creation", "A operação conflita com o estado atual. Atualize os dados e tente novamente."],
    [422, "password is required", "Revise os dados informados e tente novamente."],
    [422, "paused must be a boolean", "Revise os dados informados e tente novamente."],
    [422, "MONGODB_URI=mongodb://internal-secret", "Revise os dados informados e tente novamente."],
  ])("nunca expõe detalhe operacional ou segredo HTTP %i", async (status, detail, message) => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "https://api.wtg.example");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail }), { status })),
    );

    await expect(apiFetch("/api/dashboard")).rejects.toMatchObject({ status, message });
  });

  it("normaliza a listagem persistida de usuários para o contrato público", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "https://api.wtg.example");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            items: [
              {
                id: "seller-1",
                fullName: "Sandra",
                emailNormalized: "sandracristina@wtgseguros.com.br",
                role: "seller",
                active: true,
                paused: false,
                passwordHash: "never-expose",
                tokenHash: "never-expose",
              },
            ],
            page: 1,
            pageSize: 50,
            total: 1,
          }),
          { status: 200 },
        ),
      ),
    );

    await expect(getManagedUsers("sessao")).resolves.toEqual({
      items: [
        {
          id: "seller-1",
          fullName: "Sandra",
          email: "sandracristina@wtgseguros.com.br",
          role: "seller",
          active: true,
          paused: false,
        },
      ],
      page: 1,
      pageSize: 50,
      total: 1,
    });
  });

  it("serializa criação de usuário e não devolve a senha", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "https://api.wtg.example");
    const request = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          id: "seller-1",
          fullName: "Nova Vendedora",
          email: "nova@wtgseguros.com.br",
          role: "seller",
          active: true,
          paused: false,
        }),
        { status: 201 },
      ),
    );
    vi.stubGlobal("fetch", request);

    const user = await createManagedUser(
      {
        fullName: "Nova Vendedora",
        email: "nova@wtgseguros.com.br",
        role: "seller",
        password: "senha inicial",
      },
      "sessao",
    );

    expect(user).toEqual({
      id: "seller-1",
      fullName: "Nova Vendedora",
      email: "nova@wtgseguros.com.br",
      role: "seller",
      active: true,
      paused: false,
    });
    expect(user).not.toHaveProperty("password");
    expect(request).toHaveBeenCalledWith(
      "https://api.wtg.example/api/admin/users",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          fullName: "Nova Vendedora",
          email: "nova@wtgseguros.com.br",
          role: "seller",
          password: "senha inicial",
        }),
        headers: expect.objectContaining({
          "Content-Type": "application/json",
          Cookie: "gerec_session=sessao",
        }),
      }),
    );
  });

  it("envia disponibilidade e redefinição de senha sem expor a senha na resposta", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "https://api.wtg.example");
    const response = {
      id: "seller-1",
      fullName: "Nova Vendedora",
      email: "nova@wtgseguros.com.br",
      role: "seller" as const,
      active: true,
      paused: true,
    };
    const request = vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify(response), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(response), { status: 200 }));
    vi.stubGlobal("fetch", request);

    await expect(setManagedUserAvailability("seller-1", true, "sessao")).resolves.toEqual(response);
    await expect(resetManagedUserPassword("seller-1", "nova senha", "sessao")).resolves.toEqual(
      response,
    );
    expect(request).toHaveBeenNthCalledWith(
      1,
      "https://api.wtg.example/api/admin/users/seller-1/availability",
      expect.objectContaining({ body: JSON.stringify({ paused: true }) }),
    );
    expect(request).toHaveBeenNthCalledWith(
      2,
      "https://api.wtg.example/api/admin/users/seller-1/password",
      expect.objectContaining({ body: JSON.stringify({ password: "nova senha" }) }),
    );
  });

  it("serializa tratativa e consulta histórico sem decidir o estado no navegador", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "https://api.wtg.example");
    const request = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            leadId: "lead-1",
            treatmentId: "treatment-1",
            status: "ok",
            commercialStatus: "negotiation",
            isDisqualified: false,
            commentCount: 2,
          }),
          { status: 201 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ items: [], page: 1, pageSize: 50, total: 0 }), {
          status: 200,
        }),
      );
    vi.stubGlobal("fetch", request);

    await expect(
      submitLeadTreatment(
        "lead-1",
        {
          comment: "Cliente pediu uma nova cotação.",
          commercialStatus: "negotiation",
          isDisqualified: false,
          idempotencyKey: "treatment-1",
        },
        "sessao",
      ),
    ).resolves.toMatchObject({ commentCount: 2, commercialStatus: "negotiation" });
    await expect(getLeadTreatments("lead-1", "sessao")).resolves.toEqual({
      items: [],
      page: 1,
      pageSize: 50,
      total: 0,
    });
    expect(request).toHaveBeenNthCalledWith(
      1,
      "https://api.wtg.example/api/leads/lead-1/treatments",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          comment: "Cliente pediu uma nova cotação.",
          commercialStatus: "negotiation",
          isDisqualified: false,
          idempotencyKey: "treatment-1",
        }),
      }),
    );
    expect(request).toHaveBeenNthCalledWith(
      2,
      "https://api.wtg.example/api/leads/lead-1/treatments?page=1&limit=50",
      expect.objectContaining({ headers: expect.objectContaining({ Cookie: "gerec_session=sessao" }) }),
    );
  });
});
````

## Snapshot de código: `apps/web/src/lib/api/client.ts`

````typescript
import type {
  CreateManagedUserInput,
  ManagedUser,
  NewLeadNotificationSnapshot,
  Page,
  Treatment,
  TreatmentInput,
  TreatmentSubmission,
} from "./types";

export class ApiRequestError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiRequestError";
  }
}

function apiUrl(path: string): string {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "");
  if (!baseUrl) {
    throw new ApiRequestError("API do Gerenciador de Leads não configurada.", 503);
  }
  return `${baseUrl}/${path.replace(/^\//, "")}`;
}

function messageForStatus(status: number): string {
  switch (status) {
    case 401:
      return "Sessão expirada. Entre novamente.";
    case 403:
      return "Você não tem permissão para esta ação.";
    case 409:
      return "A operação conflita com o estado atual. Atualize os dados e tente novamente.";
    case 422:
      return "Revise os dados informados e tente novamente.";
    default:
      return "Não foi possível concluir a solicitação.";
  }
}

async function errorMessage(response: Response): Promise<string> {
  // O corpo de erro é um contrato técnico da API. Nunca o exponha ao usuário:
  // pode conter termos internos, texto em outro idioma ou dados sensíveis.
  return messageForStatus(response.status);
}

export async function apiRequest(path: string, init: RequestInit = {}): Promise<Response> {
  const response = await fetch(apiUrl(path), {
    ...init,
    credentials: "include",
    headers: {
      Accept: "application/json",
      ...init.headers,
    },
  });
  if (!response.ok) throw new ApiRequestError(await errorMessage(response), response.status);
  return response;
}

/** Único ponto de entrada HTTP da interface; as regras permanecem na API. */
export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await apiRequest(path, init);
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

function sessionHeaders(sessionToken: string, headers: HeadersInit = {}): HeadersInit {
  return {
    "Content-Type": "application/json",
    Cookie: `gerec_session=${sessionToken}`,
    ...headers,
  };
}

function managedUser(value: unknown): ManagedUser {
  if (typeof value !== "object" || value === null) {
    throw new ApiRequestError("A resposta de usuários é inválida.", 502);
  }
  const record = value as Record<string, unknown>;
  const email = text(record.email) ?? text(record.emailNormalized);
  const fullName = text(record.fullName);
  const id = text(record.id);
  const role = record.role;
  if (
    !id ||
    !fullName ||
    !email ||
    (role !== "admin" && role !== "seller") ||
    typeof record.active !== "boolean"
  ) {
    throw new ApiRequestError("A resposta de usuários é inválida.", 502);
  }
  return {
    id,
    fullName,
    email,
    role,
    active: record.active,
    paused: typeof record.paused === "boolean" ? record.paused : null,
  };
}

function text(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function managedUserPage(value: unknown): Page<ManagedUser> {
  if (typeof value !== "object" || value === null) {
    throw new ApiRequestError("A resposta de usuários é inválida.", 502);
  }
  const page = value as Record<string, unknown>;
  if (
    !Array.isArray(page.items) ||
    typeof page.page !== "number" ||
    !Number.isInteger(page.page) ||
    typeof page.pageSize !== "number" ||
    !Number.isInteger(page.pageSize) ||
    typeof page.total !== "number" ||
    !Number.isInteger(page.total)
  ) {
    throw new ApiRequestError("A resposta de usuários é inválida.", 502);
  }
  return {
    items: page.items.map(managedUser),
    page: page.page,
    pageSize: page.pageSize,
    total: page.total,
  };
}

export async function getManagedUsers(
  sessionToken: string,
  page = 1,
  limit = 50,
): Promise<Page<ManagedUser>> {
  return managedUserPage(
    await apiFetch<unknown>(`/api/admin/users?page=${page}&limit=${limit}`, {
      cache: "no-store",
      headers: { Cookie: `gerec_session=${sessionToken}` },
    }),
  );
}

export async function createManagedUser(
  input: CreateManagedUserInput,
  sessionToken: string,
): Promise<ManagedUser> {
  return managedUser(
    await apiFetch<unknown>("/api/admin/users", {
      method: "POST",
      headers: sessionHeaders(sessionToken),
      body: JSON.stringify(input),
    }),
  );
}

export async function setManagedUserAvailability(
  userId: string,
  paused: boolean,
  sessionToken: string,
): Promise<ManagedUser> {
  return managedUser(
    await apiFetch<unknown>(`/api/admin/users/${encodeURIComponent(userId)}/availability`, {
      method: "PATCH",
      headers: sessionHeaders(sessionToken),
      body: JSON.stringify({ paused }),
    }),
  );
}

export async function resetManagedUserPassword(
  userId: string,
  password: string,
  sessionToken: string,
): Promise<ManagedUser> {
  return managedUser(
    await apiFetch<unknown>(`/api/admin/users/${encodeURIComponent(userId)}/password`, {
      method: "PATCH",
      headers: sessionHeaders(sessionToken),
      body: JSON.stringify({ password }),
    }),
  );
}

export async function submitLeadTreatment(
  leadId: string,
  input: TreatmentInput,
  sessionToken: string,
): Promise<TreatmentSubmission> {
  return apiFetch<TreatmentSubmission>(`/api/leads/${encodeURIComponent(leadId)}/treatments`, {
    method: "POST",
    headers: sessionHeaders(sessionToken),
    body: JSON.stringify(input),
  });
}

export async function getLeadTreatments(
  leadId: string,
  sessionToken: string,
  page = 1,
  limit = 50,
): Promise<Page<Treatment>> {
  return apiFetch<Page<Treatment>>(
    `/api/leads/${encodeURIComponent(leadId)}/treatments?page=${page}&limit=${limit}`,
    {
      cache: "no-store",
      headers: { Cookie: `gerec_session=${sessionToken}` },
    },
  );
}

export async function transferLeadOwnership(
  leadId: string,
  sellerId: string,
  reason: string,
  commandId: string,
  sessionToken: string,
): Promise<{ leadId: string; sellerId: string; status: string }> {
  return apiFetch(`/api/admin/leads/${encodeURIComponent(leadId)}/transfer-owner`, {
    method: "POST",
    headers: sessionHeaders(sessionToken),
    body: JSON.stringify({ seller_id: sellerId, reason, command_id: commandId, confirmed: true }),
  });
}

export async function acknowledgeNewLeadNotifications(
  snapshot: NewLeadNotificationSnapshot,
  sessionToken: string,
): Promise<{ watermark: string }> {
  return apiFetch<{ watermark: string }>("/api/lead-notifications/new/acknowledge", {
    method: "POST",
    headers: sessionHeaders(sessionToken),
    body: JSON.stringify({
      watermark: snapshot.watermark,
      acknowledgementToken: snapshot.acknowledgementToken,
      watermarkSequence: snapshot.watermarkSequence,
    }),
  });
}
````

## Snapshot de código: `apps/web/src/lib/api/types.ts`

````typescript
export type UserRole = "admin" | "seller";

export type CommercialStatus = "undefined" | "negotiation" | "potential" | "won";

export type SellerAvailability = "active" | "paused";

export type ApiUser = { id: string; email: string; role: UserRole };

export type Page<T> = { items: T[]; page: number; pageSize: number; total: number };

/**
 * Identificadores são chaves técnicas para mutações e nunca rótulos da interface.
 * O backend já resolve nomes e status autorizados para cada perfil.
 */
export type OperationalLead = {
  id: string;
  contactName: string;
  sellerName: string;
  companyName: string;
  campaignName: string;
  phoneDisplay: string;
  email: string;
  commercialStatus: CommercialStatus;
  isDisqualified: boolean;
  commentCount: number;
  assignedAt: string | null;
  lastUpdatedAt: string | null;
};

export type Treatment = {
  leadId: string;
  leadName?: string;
  sellerName: string;
  comment: string;
  commercialStatus: CommercialStatus;
  isDisqualified: boolean;
  assignedAt: string | null;
  createdAt: string;
  lastUpdatedAt: string | null;
};

export type QueueEntry = {
  sellerName: string;
  position: number;
  availability: SellerAvailability;
  reason: string | null;
  skipBalance: number;
};

export type AdminQueue = {
  items: QueueEntry[];
  total: number;
  nextSellerName: string;
  cursorSellerName: string;
};

export type SellerQueue = {
  position: number | null;
  availability: SellerAvailability;
  skipBalance: number;
};

export type AdminDashboard = {
  user: ApiUser & { role: "admin" };
  leads: Page<OperationalLead>;
  history: Page<Treatment>;
  queue: AdminQueue;
};

export type SellerDashboard = {
  user: ApiUser & { role: "seller" };
  leads: Page<OperationalLead>;
  history: Page<Treatment>;
  queue: SellerQueue;
};

export type ApiDashboard = AdminDashboard | SellerDashboard;

/** Resposta pública dos comandos administrativos; não contém password ou hash. */
export type ManagedUser = {
  id: string;
  fullName: string;
  email: string;
  role: UserRole;
  active: boolean;
  paused: boolean | null;
};

export type CreateManagedUserInput = {
  fullName: string;
  email: string;
  role: UserRole;
  password: string;
};

export type ResetManagedUserPasswordInput = { password: string };

export type TreatmentInput = {
  comment: string;
  commercialStatus: CommercialStatus;
  isDisqualified: boolean;
  idempotencyKey: string;
};

export type TreatmentSubmission = {
  leadId: string;
  treatmentId: string;
  status: string;
  commercialStatus: CommercialStatus;
  isDisqualified: boolean;
  commentCount: number;
  lastUpdatedAt: string;
};

export type NewLeadNotification = {
  leadId: string;
  contactName: string;
  assignedAt: string;
};

export type NewLeadNotificationSnapshot = {
  items: NewLeadNotification[];
  watermark: string;
  acknowledgementToken: string;
  watermarkSequence: number;
};

export type LeadDistributionReport = {
  period: { from: string; to: string };
  bySituation: Array<{ commercialStatus: CommercialStatus; count: number }>;
  bySeller: Array<{ sellerId: string; sellerName: string; count: number }>;
};
````

## Snapshot de código: `apps/web/src/lib/auth/actions.test.ts`

````typescript
import { beforeEach, describe, expect, it, vi } from "vitest";

const { cookieStore, apiRequest, redirect } = vi.hoisted(() => ({
  cookieStore: { get: vi.fn(), set: vi.fn(), delete: vi.fn() },
  apiRequest: vi.fn(),
  redirect: vi.fn(),
}));

vi.mock("next/headers", () => ({ cookies: vi.fn(async () => cookieStore) }));
vi.mock("next/navigation", () => ({ redirect }));
vi.mock("../api/client", () => ({ apiRequest }));

import { loginAction, signOutAction } from "./actions";

describe("ações de sessão", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("propaga cookie HTTP da API e conserva o Max-Age dela", async () => {
    apiRequest.mockResolvedValue(
      new Response(null, {
        headers: { "set-cookie": "gerec_session=opaque; Max-Age=28800; Path=/; HttpOnly" },
      }),
    );
    const form = new FormData();
    form.set("email", "yago@wtg.com");
    form.set("password", "segura");

    await loginAction({}, form);

    expect(cookieStore.set).toHaveBeenCalledWith(
      "gerec_session",
      "opaque",
      expect.objectContaining({ maxAge: 28800, httpOnly: true }),
    );
    expect(redirect).toHaveBeenCalledWith("/dashboard");
  });

  it("apaga cookie e volta ao login quando logout remoto falha", async () => {
    cookieStore.get.mockReturnValue({ value: "opaque" });
    apiRequest.mockRejectedValue(new Error("indisponível"));

    await signOutAction();
    expect(cookieStore.delete).toHaveBeenCalledWith("gerec_session");
    expect(redirect).toHaveBeenCalledWith("/login");
  });
});
````

## Snapshot de código: `apps/web/src/lib/auth/actions.ts`

````typescript
"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { apiRequest } from "../api/client";
import { SESSION_COOKIE } from "./session";

export type LoginState = { error?: string };
const cookieOptions = {
  httpOnly: true,
  sameSite: "lax" as const,
  secure: process.env.NODE_ENV === "production",
  path: "/",
};

function apiSessionCookie(setCookie: string | null): { token: string; maxAge: number } | null {
  const token = setCookie?.match(/gerec_session=([^;]+)/)?.[1];
  const maxAge = Number(setCookie?.match(/max-age=(\d+)/i)?.[1]);
  return token && Number.isSafeInteger(maxAge) && maxAge > 0 ? { token, maxAge } : null;
}

export async function loginAction(_state: LoginState, formData: FormData): Promise<LoginState> {
  const email = String(formData.get("email") ?? "").trim();
  const password = String(formData.get("password") ?? "");
  if (!email || !password) return { error: "Informe e-mail e senha para entrar." };
  try {
    const response = await apiRequest("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const session = apiSessionCookie(response.headers.get("set-cookie"));
    if (!session) throw new Error("A API não retornou uma sessão válida.");
    (await cookies()).set(SESSION_COOKIE, session.token, {
      ...cookieOptions,
      maxAge: session.maxAge,
    });
  } catch (error) {
    return { error: error instanceof Error ? error.message : "Não foi possível autenticar." };
  }
  redirect("/dashboard");
}

export async function signOutAction() {
  const cookieStore = await cookies();
  const token = cookieStore.get(SESSION_COOKIE)?.value;
  try {
    if (token)
      await apiRequest("/auth/logout", {
        method: "POST",
        headers: { Cookie: `${SESSION_COOKIE}=${token}` },
      });
  } catch {
    // A sessão local deve encerrar mesmo se a API estiver indisponível.
  } finally {
    cookieStore.delete(SESSION_COOKIE);
  }
  redirect("/login");
}
````

## Snapshot de código: `apps/web/src/lib/auth/session.test.ts`

````typescript
import { beforeEach, describe, expect, it, vi } from "vitest";

const { cookieStore, apiFetch } = vi.hoisted(() => ({
  cookieStore: { get: vi.fn() },
  apiFetch: vi.fn(),
}));
vi.mock("next/headers", () => ({ cookies: vi.fn(async () => cookieStore) }));
vi.mock("../api/client", () => ({
  ApiRequestError: class ApiRequestError extends Error {
    constructor(
      message: string,
      readonly status: number,
    ) {
      super(message);
    }
  },
  apiFetch,
}));

import { getSessionContext } from "./session";

describe("getSessionContext", () => {
  beforeEach(() => vi.clearAllMocks());

  it("encaminha apenas o cookie de sessão à API", async () => {
    cookieStore.get.mockReturnValue({ value: "opaque" });
    apiFetch.mockResolvedValue({ id: "u1", email: "vendedor@wtg.com", role: "seller" });

    await expect(getSessionContext()).resolves.toMatchObject({
      status: "authenticated",
      sessionToken: "opaque",
      profile: { userId: "u1" },
    });
    expect(apiFetch).toHaveBeenCalledWith(
      "/auth/me",
      expect.objectContaining({ headers: { Cookie: "gerec_session=opaque" } }),
    );
  });
});
````

## Snapshot de código: `apps/web/src/lib/auth/session.ts`

````typescript
import { cookies } from "next/headers";

import { apiFetch, ApiRequestError } from "../api/client";
import type { ApiUser } from "../api/types";

export const SESSION_COOKIE = "gerec_session";
export type SessionProfile = ApiUser & { userId: string; fullName: string };
export type SessionContext =
  | { status: "authenticated"; sessionToken: string; profile: SessionProfile }
  | { status: "missing" | "unavailable"; message: string };

export async function getSessionContext(): Promise<SessionContext> {
  const token = (await cookies()).get(SESSION_COOKIE)?.value;
  if (!token) return { status: "missing", message: "Entre para acessar o sistema." };
  try {
    const user = await apiFetch<ApiUser>("/auth/me", {
      cache: "no-store",
      headers: { Cookie: `${SESSION_COOKIE}=${token}` },
    });
    return { status: "authenticated", sessionToken: token, profile: { ...user, userId: user.id, fullName: user.email } };
  } catch (error) {
    if (error instanceof ApiRequestError && error.status === 401) {
      return { status: "missing", message: "Sua sessão expirou. Entre novamente." };
    }
    return { status: "unavailable", message: error instanceof Error ? error.message : "API indisponível." };
  }
}
````

## Snapshot de código: `apps/web/src/lib/dashboard/format.test.ts`

````typescript
import { describe, expect, it } from "vitest";

import {
  NOT_INFORMED,
  formatCommercialStatus,
  formatCommentCount,
  formatDateTime,
  formatDisqualificationMarker,
  formatPhone,
  formatText,
} from "./format";

describe("formatDateTime", () => {
  it("formata horários no fuso de São Paulo", () => {
    expect(formatDateTime("2026-08-26T15:30:00.000Z")).toBe("26/08/2026, 12:30");
  });

  it("retorna fallback para valor ausente", () => {
    expect(formatDateTime(null)).toBe(NOT_INFORMED);
  });
});

describe("formatação de projeção operacional", () => {
  it("traduz situação comercial e marcador sem decidir regras de negócio", () => {
    expect(formatCommercialStatus("undefined")).toBe("Indefinido");
    expect(formatCommercialStatus("negotiation")).toBe("Negociação");
    expect(formatCommercialStatus("won")).toBe("Ganho");
    expect(formatDisqualificationMarker(true)).toBe("Desqualificado");
    expect(formatDisqualificationMarker(false)).toBe("Não desqualificado");
  });

  it("formata contador, prazo, telefone e texto ausente para o operador", () => {
    expect(formatCommentCount(1)).toBe("1 comentário");
    expect(formatCommentCount(2)).toBe("2 comentários");
    expect(formatPhone("5511988308029")).toBe("(11) 98830-8029");
    expect(formatText("   ")).toBe(NOT_INFORMED);
  });
});
````

## Snapshot de código: `apps/web/src/lib/dashboard/format.ts`

````typescript
import type { CommercialStatus } from "../api/types";

export const NOT_INFORMED = "Não informado";

const SAO_PAULO_TIME_ZONE = "America/Sao_Paulo";

const dateTimeFormatter = new Intl.DateTimeFormat("pt-BR", {
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
  month: "2-digit",
  timeZone: SAO_PAULO_TIME_ZONE,
  year: "numeric",
});

export function formatText(value: string | null | undefined): string {
  return value?.trim() || NOT_INFORMED;
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value || Number.isNaN(new Date(value).getTime())) return NOT_INFORMED;
  return dateTimeFormatter.format(new Date(value));
}

export function formatCommercialStatus(value: CommercialStatus): string {
  return {
    undefined: "Indefinido",
    negotiation: "Negociação",
    potential: "Potencial",
    won: "Ganho",
  }[value];
}

export function formatDisqualificationMarker(isDisqualified: boolean): string {
  return isDisqualified ? "Desqualificado" : "Não desqualificado";
}

export function formatCommentCount(value: number): string {
  const count = Number.isInteger(value) && value >= 0 ? value : 0;
  return `${count} ${count === 1 ? "comentário" : "comentários"}`;
}

export function formatPhone(value: string | null | undefined): string {
  let digits = String(value ?? "").replace(/\D/g, "");
  if (digits.startsWith("55") && (digits.length === 12 || digits.length === 13)) digits = digits.slice(2);
  if (digits.length === 11) return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7)}`;
  if (digits.length === 10) return `(${digits.slice(0, 2)}) ${digits.slice(2, 6)}-${digits.slice(6)}`;
  return digits || NOT_INFORMED;
}
````

## Snapshot de código: `apps/web/src/lib/dashboard/queries.test.ts`

````typescript
import { beforeEach, describe, expect, it, vi } from "vitest";

const { apiFetch } = vi.hoisted(() => ({ apiFetch: vi.fn() }));
vi.mock("../api/client", () => ({ apiFetch }));

import { getDashboardData, isAdminDashboard, pageNumber } from "./queries";

describe("getDashboardData", () => {
  beforeEach(() => vi.clearAllMocks());

  it("solicita a página pedida e encaminha cookie de sessão", async () => {
    apiFetch.mockResolvedValue({});
    await getDashboardData("opaque", 3, { assigneeId: "seller-1", sort: "situation" });
    expect(apiFetch).toHaveBeenCalledWith(
      "/api/dashboard?page=3&limit=50&assigneeId=seller-1&sort=situation",
      expect.objectContaining({ headers: { Cookie: "gerec_session=opaque" } }),
    );
  });

  it.each(["0", "-1", "1.5", "Infinity", "não-numero"])("recusa página inválida: %s", (value) => {
    expect(() => pageNumber(value)).toThrow("Página inválida");
  });

  it("separa a projeção administrativa pelo papel devolvido pela API", () => {
    expect(
      isAdminDashboard({
        user: { id: "admin-1", email: "admin@wtgseguros.com.br", role: "admin" },
        leads: { items: [], page: 1, pageSize: 50, total: 0 },
        history: { items: [], page: 1, pageSize: 50, total: 0 },
        queue: { items: [], total: 0, nextSellerName: "Não informado", cursorSellerName: "Não informado" },
      }),
    ).toBe(true);
  });

  it("mantém a fila do vendedor sem dados globais", () => {
    const dashboard = {
      user: { id: "seller-1", email: "seller@wtgseguros.com.br", role: "seller" as const },
      leads: { items: [], page: 1, pageSize: 50, total: 0 },
      history: { items: [], page: 1, pageSize: 50, total: 0 },
      queue: { position: 2, availability: "active" as const, skipBalance: 0 },
    };

    expect(isAdminDashboard(dashboard)).toBe(false);
    expect(dashboard.queue).not.toHaveProperty("items");
    expect(dashboard.queue).not.toHaveProperty("nextSellerName");
  });
});
````

## Snapshot de código: `apps/web/src/lib/dashboard/queries.ts`

````typescript
import { apiFetch } from "../api/client";
import type { AdminDashboard, ApiDashboard } from "../api/types";
import { SESSION_COOKIE } from "../auth/session";

export type DashboardSort = "situation";

export type DashboardListFilters = {
  assigneeId: string | null;
  sort: DashboardSort | null;
};

export type DashboardSearchParams = Record<string, string | string[] | undefined>;

function singleValue(value: string | string[] | undefined): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

/** Only recognized query values are forwarded to the API read model. */
export function dashboardListFilters(searchParams: DashboardSearchParams): DashboardListFilters {
  const sort = singleValue(searchParams.sort);
  return {
    assigneeId: singleValue(searchParams.assigneeId),
    sort: sort === "situation" ? sort : null,
  };
}

export function pageNumber(value: string | undefined): number {
  const page = Number(value);
  if (!Number.isFinite(page) || !Number.isInteger(page) || page < 1) {
    throw new Error("Página inválida.");
  }
  return page;
}

export async function getDashboardData(
  sessionToken: string,
  page = 1,
  filters: Partial<DashboardListFilters> = {},
): Promise<ApiDashboard> {
  const searchParams = new URLSearchParams({ page: String(page), limit: "50" });
  if (filters.assigneeId) searchParams.set("assigneeId", filters.assigneeId);
  if (filters.sort === "situation") searchParams.set("sort", filters.sort);
  return apiFetch<ApiDashboard>(`/api/dashboard?${searchParams.toString()}`, {
    cache: "no-store",
    headers: { Cookie: `${SESSION_COOKIE}=${sessionToken}` },
  });
}

/** A API define o papel; a web apenas escolhe a composição de apresentação. */
export function isAdminDashboard(dashboard: ApiDashboard): dashboard is AdminDashboard {
  return dashboard.user.role === "admin";
}
````

## Snapshot de código: `apps/web/src/lib/notifications/actions.test.ts`

````typescript
import { beforeEach, describe, expect, it, vi } from "vitest";

const { acknowledgeRequest, getSessionContext, revalidatePath } = vi.hoisted(() => ({
  acknowledgeRequest: vi.fn(),
  getSessionContext: vi.fn(),
  revalidatePath: vi.fn(),
}));

vi.mock("next/cache", () => ({ revalidatePath }));
vi.mock("../api/client", () => {
  class ApiRequestError extends Error {
    constructor(
      message: string,
      readonly status: number,
    ) {
      super(message);
    }
  }
  return { acknowledgeNewLeadNotifications: acknowledgeRequest, ApiRequestError };
});
vi.mock("../auth/session", () => ({ getSessionContext }));

import { acknowledgeNewLeadsAction } from "./actions";

const snapshot = {
  items: [],
  watermark: "2026-09-15T12:01:00.000Z",
  acknowledgementToken: "token-assinado",
  watermarkSequence: 8,
};

describe("ação de confirmação de novos leads", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("encaminha o recibo emitido pela API somente para a sessão do vendedor", async () => {
    getSessionContext.mockResolvedValue({
      status: "authenticated",
      sessionToken: "sessao-segura",
      profile: { id: "seller-1", userId: "seller-1", fullName: "Sandra", email: "sandra@example.test", role: "seller" },
    });
    acknowledgeRequest.mockResolvedValue({ watermark: snapshot.watermark });

    await expect(acknowledgeNewLeadsAction(snapshot)).resolves.toEqual({
      ok: true,
      message: "Novos leads confirmados.",
    });
    expect(acknowledgeRequest).toHaveBeenCalledWith(snapshot, "sessao-segura");
    expect(revalidatePath).toHaveBeenCalledWith("/dashboard");
  });

  it("não envia confirmação quando a sessão não é de vendedor", async () => {
    getSessionContext.mockResolvedValue({
      status: "authenticated",
      sessionToken: "sessao-admin",
      profile: { id: "admin-1", userId: "admin-1", fullName: "Yago", email: "yago@example.test", role: "admin" },
    });

    await expect(acknowledgeNewLeadsAction(snapshot)).resolves.toEqual({
      ok: false,
      message: "Sessão expirada ou sem permissão.",
    });
    expect(acknowledgeRequest).not.toHaveBeenCalled();
  });

  it("converte indisponibilidade da sessão em erro seguro da janela", async () => {
    getSessionContext.mockRejectedValue(new Error("falha interna"));

    await expect(acknowledgeNewLeadsAction(snapshot)).resolves.toEqual({
      ok: false,
      message: "Não foi possível confirmar os novos leads.",
    });
    expect(acknowledgeRequest).not.toHaveBeenCalled();
  });
});
````

## Snapshot de código: `apps/web/src/lib/notifications/actions.ts`

````typescript
"use server";

import { revalidatePath } from "next/cache";

import {
  acknowledgeNewLeadNotifications,
  ApiRequestError,
} from "../api/client";
import type { NewLeadNotificationSnapshot } from "../api/types";
import { getSessionContext } from "../auth/session";

export type NewLeadAcknowledgementResult =
  | { ok: true; message: string }
  | { ok: false; message: string };

function actionError(error: unknown): string {
  if (error instanceof ApiRequestError) return error.message;
  return "Não foi possível confirmar os novos leads.";
}

export async function acknowledgeNewLeadsAction(
  snapshot: NewLeadNotificationSnapshot,
): Promise<NewLeadAcknowledgementResult> {
  try {
    const session = await getSessionContext();
    if (session.status !== "authenticated" || session.profile.role !== "seller") {
      return { ok: false, message: "Sessão expirada ou sem permissão." };
    }
    await acknowledgeNewLeadNotifications(snapshot, session.sessionToken);
    revalidatePath("/dashboard");
    return { ok: true, message: "Novos leads confirmados." };
  } catch (error) {
    return { ok: false, message: actionError(error) };
  }
}
````

## Snapshot de código: `apps/web/src/lib/notifications/queries.ts`

````typescript
import { apiFetch } from "../api/client";
import type { NewLeadNotificationSnapshot } from "../api/types";
import { SESSION_COOKIE } from "../auth/session";

/** Consulta uma janela estável; a confirmação acontece somente em uma ação separada. */
export async function getNewLeadNotifications(
  sessionToken: string,
): Promise<NewLeadNotificationSnapshot> {
  return apiFetch<NewLeadNotificationSnapshot>("/api/lead-notifications/new", {
    cache: "no-store",
    headers: { Cookie: `${SESSION_COOKIE}=${sessionToken}` },
  });
}
````

## Snapshot de código: `apps/web/src/lib/operations/transfer-actions.test.ts`

````typescript
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../auth/session", () => ({ getSessionContext: vi.fn() }));
vi.mock("../api/client", () => {
  class ApiRequestError extends Error {
    constructor(
      message: string,
      readonly status: number,
    ) {
      super(message);
    }
  }
  return { ApiRequestError, transferLeadOwnership: vi.fn() };
});

import { getSessionContext } from "../auth/session";
import { transferLeadOwnership } from "../api/client";
import { transferLeadOwnershipAction } from "./transfer-actions";
import { initialTransferActionState } from "./transfer-state";

function formData(values: Record<string, string>): FormData {
  const form = new FormData();
  Object.entries(values).forEach(([key, value]) => form.set(key, value));
  return form;
}

describe("ação de transferência de propriedade", () => {
  beforeEach(() => vi.clearAllMocks());

  it("converte falha inesperada ao carregar sessão em erro do formulário", async () => {
    vi.mocked(getSessionContext).mockRejectedValue(new Error("API indisponível"));

    await expect(
      transferLeadOwnershipAction(
        initialTransferActionState,
        formData({ leadId: "lead-1", sellerId: "seller-2", reason: "Cobertura" }),
      ),
    ).resolves.toEqual({
      status: "error",
      message: "Não foi possível transferir a propriedade.",
    });
  });

  it("envia confirmação explícita ao backend", async () => {
    vi.mocked(getSessionContext).mockResolvedValue({
      status: "authenticated",
      sessionToken: "sessao",
      profile: {
        id: "admin-1",
        userId: "admin-1",
        fullName: "Yago",
        email: "yago@example.com",
        role: "admin",
      },
    });
    vi.mocked(transferLeadOwnership).mockResolvedValue({
      leadId: "lead-1",
      sellerId: "seller-2",
      status: "assigned",
    });

    const result = await transferLeadOwnershipAction(
      initialTransferActionState,
      formData({ leadId: "lead-1", sellerId: "seller-2", reason: "Cobertura" }),
    );

    expect(result.status).toBe("success");
    expect(transferLeadOwnership).toHaveBeenCalledWith(
      "lead-1",
      "seller-2",
      "Cobertura",
      expect.any(String),
      "sessao",
    );
  });
});
````

## Snapshot de código: `apps/web/src/lib/operations/transfer-actions.ts`

````typescript
"use server";

import { randomUUID } from "node:crypto";

import { ApiRequestError, transferLeadOwnership } from "../api/client";
import { getSessionContext } from "../auth/session";

import type { TransferActionState } from "./transfer-state";

export type { TransferActionState } from "./transfer-state";

export async function transferLeadOwnershipAction(
  _previous: TransferActionState,
  formData: FormData,
): Promise<TransferActionState> {
  const leadId = String(formData.get("leadId") ?? "").trim();
  const sellerId = String(formData.get("sellerId") ?? "").trim();
  const reason = String(formData.get("reason") ?? "").trim();
  if (!leadId || !sellerId || reason.length < 1) {
    return { status: "error", message: "Selecione um vendedor e informe o motivo." };
  }
  try {
    const session = await getSessionContext();
    if (session.status !== "authenticated" || session.profile.role !== "admin") {
      return { status: "error", message: "Sessão expirada ou sem permissão." };
    }
    await transferLeadOwnership(leadId, sellerId, reason, randomUUID(), session.sessionToken);
    return { status: "success", message: "Propriedade transferida." };
  } catch (error) {
    return {
      status: "error",
      message:
        error instanceof ApiRequestError
          ? error.message
          : "Não foi possível transferir a propriedade.",
    };
  }
}
````

## Snapshot de código: `apps/web/src/lib/operations/transfer-state.ts`

````typescript
export type TransferActionState = {
  status: "idle" | "success" | "error";
  message: string;
};

export const initialTransferActionState: TransferActionState = { status: "idle", message: "" };
````

## Snapshot de código: `apps/web/src/lib/operations/treatment-actions.test.ts`

````typescript
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("next/cache", () => ({ revalidatePath: vi.fn() }));
vi.mock("../auth/session", () => ({ getSessionContext: vi.fn() }));
vi.mock("../api/client", () => {
  class ApiRequestError extends Error {
    constructor(
      message: string,
      readonly status: number,
    ) {
      super(message);
    }
  }
  return { ApiRequestError, getLeadTreatments: vi.fn(), submitLeadTreatment: vi.fn() };
});

import { revalidatePath } from "next/cache";

import { ApiRequestError, submitLeadTreatment } from "../api/client";
import { getSessionContext } from "../auth/session";
import { submitLeadTreatmentAction } from "./treatment-actions";
import { initialTreatmentActionState } from "./treatment-state";

const authenticatedSession = {
  status: "authenticated" as const,
  sessionToken: "sessao-segura",
  profile: {
    id: "seller-1",
    userId: "seller-1",
    fullName: "Jessica",
    email: "jessica@wtgseguros.com.br",
    role: "seller" as const,
  },
};

function formData(values: Record<string, string>): FormData {
  const form = new FormData();
  Object.entries(values).forEach(([key, value]) => form.set(key, value));
  return form;
}

describe("ação de tratativa", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getSessionContext).mockResolvedValue(authenticatedSession);
  });

  it("mantém o erro 422 legível para o formulário", async () => {
    vi.mocked(submitLeadTreatment).mockRejectedValue(
      new ApiRequestError("Revise os dados informados e tente novamente.", 422),
    );

    await expect(
      submitLeadTreatmentAction(
        initialTreatmentActionState,
        formData({
          leadId: "lead-1",
          comment: "Contato realizado por telefone.",
          commercialStatus: "negotiation",
          idempotencyKey: "key-1",
        }),
      ),
    ).resolves.toEqual({
      status: "error",
      message: "Revise os dados informados e tente novamente.",
      submission: null,
    });
  });

  it("envia o status atual e atualiza a consulta após sucesso", async () => {
    vi.mocked(submitLeadTreatment).mockResolvedValue({
      leadId: "lead-1",
      treatmentId: "treatment-1",
      status: "created",
      commercialStatus: "won",
      isDisqualified: true,
      commentCount: 3,
      lastUpdatedAt: "2026-08-29T15:00:00.000Z",
    });

    const result = await submitLeadTreatmentAction(
      initialTreatmentActionState,
      formData({
        leadId: "lead-1",
        comment: "Seguro contratado e escopo confirmado.",
        commercialStatus: "won",
        isDisqualified: "on",
        idempotencyKey: "key-2",
      }),
    );

    expect(submitLeadTreatment).toHaveBeenCalledWith(
      "lead-1",
      {
        comment: "Seguro contratado e escopo confirmado.",
        commercialStatus: "won",
        isDisqualified: true,
        idempotencyKey: "key-2",
      },
      "sessao-segura",
    );
    expect(revalidatePath).toHaveBeenCalledWith("/dashboard");
    expect(result).toMatchObject({ status: "success", submission: { commentCount: 3 } });
  });

  it("encaminha Potencial para a API", async () => {
    vi.mocked(submitLeadTreatment).mockResolvedValue({
      leadId: "lead-1",
      treatmentId: "treatment-2",
      status: "created",
      commercialStatus: "potential",
      isDisqualified: false,
      commentCount: 3,
      lastUpdatedAt: "2026-09-15T12:00:00.000Z",
    });

    await submitLeadTreatmentAction(
      initialTreatmentActionState,
      formData({
        leadId: "lead-1",
        comment: "Oportunidade com potencial confirmado.",
        commercialStatus: "potential",
        idempotencyKey: "key-potential",
      }),
    );

    expect(submitLeadTreatment).toHaveBeenCalledWith(
      "lead-1",
      expect.objectContaining({ commercialStatus: "potential" }),
      "sessao-segura",
    );
  });
});
````

## Snapshot de código: `apps/web/src/lib/operations/treatment-actions.ts`

````typescript
"use server";

import { randomUUID } from "node:crypto";
import { revalidatePath } from "next/cache";

import { ApiRequestError, getLeadTreatments, submitLeadTreatment } from "../api/client";
import type { CommercialStatus, Treatment } from "../api/types";
import { getSessionContext } from "../auth/session";
import type { TreatmentActionState } from "./treatment-state";

export type { TreatmentActionState } from "./treatment-state";

type TreatmentHistoryResult =
  | { status: "success"; items: Treatment[] }
  | { status: "error"; message: string; items: Treatment[] };

function commercialStatus(value: FormDataEntryValue | null): CommercialStatus | null {
  return value === "undefined" || value === "negotiation" || value === "potential" || value === "won"
    ? value
    : null;
}

function actionError(error: unknown): string {
  if (error instanceof ApiRequestError) return error.message;
  return "Não foi possível concluir a tratativa. Tente novamente.";
}

export async function submitLeadTreatmentAction(
  _previous: TreatmentActionState,
  formData: FormData,
): Promise<TreatmentActionState> {
  const leadId = String(formData.get("leadId") ?? "").trim();
  const comment = String(formData.get("comment") ?? "").trim();
  const status = commercialStatus(formData.get("commercialStatus"));
  const isDisqualified = formData.get("isDisqualified") === "on";

  if (!leadId || !status || comment.length < 6) {
    return {
      status: "error",
      message: "Escreva um comentário com ao menos 6 caracteres.",
      submission: null,
    };
  }

  const session = await getSessionContext();
  if (session.status !== "authenticated") {
    return { status: "error", message: "Sessão expirada. Entre novamente.", submission: null };
  }

  try {
    const submission = await submitLeadTreatment(
      leadId,
      {
        comment,
        commercialStatus: status,
        isDisqualified,
        idempotencyKey: String(formData.get("idempotencyKey") ?? "").trim() || randomUUID(),
      },
      session.sessionToken,
    );
    revalidatePath("/dashboard");
    revalidatePath("/historico");
    return { status: "success", message: "Tratativa registrada.", submission };
  } catch (error) {
    return { status: "error", message: actionError(error), submission: null };
  }
}

export async function loadLeadTreatmentHistoryAction(
  leadId: string,
): Promise<TreatmentHistoryResult> {
  const session = await getSessionContext();
  if (session.status !== "authenticated") {
    return { status: "error", message: "Sessão expirada. Entre novamente.", items: [] };
  }

  try {
    const history = await getLeadTreatments(leadId, session.sessionToken);
    return { status: "success", items: history.items };
  } catch (error) {
    return { status: "error", message: actionError(error), items: [] };
  }
}
````

## Snapshot de código: `apps/web/src/lib/operations/treatment-state.ts`

````typescript
import type { TreatmentSubmission } from "../api/types";

export type TreatmentActionState =
  | { status: "idle"; message: null; submission: null }
  | { status: "error"; message: string; submission: null }
  | { status: "success"; message: string; submission: TreatmentSubmission };

export const initialTreatmentActionState: TreatmentActionState = {
  status: "idle",
  message: null,
  submission: null,
};
````

## Snapshot de código: `apps/web/src/lib/reports/queries.test.ts`

````typescript
import { beforeEach, describe, expect, it, vi } from "vitest";

const { apiFetch } = vi.hoisted(() => ({ apiFetch: vi.fn() }));
vi.mock("../api/client", () => ({ apiFetch }));

import { getLeadDistributionReport, reportPeriod } from "./queries";

describe("consultas de relat\u00f3rios", () => {
  beforeEach(() => vi.clearAllMocks());

  it("usa todo o hist\u00f3rico desde o marco UTC aprovado", () => {
    expect(reportPeriod({}, new Date("2026-09-15T15:30:00.000Z"))).toEqual({
      key: "all",
      fromAt: "1970-01-01T00:00:00.000Z",
      toAt: "2026-09-15T15:30:00.000Z",
    });
  });

  it("calcula o m\u00eas atual a partir do primeiro dia UTC", () => {
    expect(reportPeriod({ period: "month" }, new Date("2026-10-01T01:00:00.000Z"))).toEqual({
      key: "month",
      fromAt: "2026-09-01T03:00:00.000Z",
      toAt: "2026-10-01T01:00:00.000Z",
    });
  });

  it("calcula os \u00faltimos 30 dias a partir do rel\u00f3gio informado", () => {
    expect(reportPeriod({ period: "last30" }, new Date("2026-09-15T15:30:00.000Z"))).toEqual({
      key: "last30",
      fromAt: "2026-08-16T15:30:00.000Z",
      toAt: "2026-09-15T15:30:00.000Z",
    });
  });

  it("preserva um intervalo personalizado v\u00e1lido", () => {
    expect(
      reportPeriod(
        { period: "custom", from: "2026-09-01", to: "2026-09-15" },
        new Date("2026-09-15T15:30:00.000Z"),
      ),
    ).toEqual({
      key: "custom",
      fromAt: "2026-09-01T03:00:00.000Z",
      toAt: "2026-09-15T03:00:00.000Z",
    });
  });

  it("encaminha o intervalo e a sess\u00e3o ao endpoint administrativo", async () => {
    apiFetch.mockResolvedValue({});
    await getLeadDistributionReport("sessao", {
      key: "all",
      fromAt: "1970-01-01T00:00:00.000Z",
      toAt: "2026-09-15T15:30:00.000Z",
    });

    expect(apiFetch).toHaveBeenCalledWith(
      "/api/admin/reports/lead-distribution?fromAt=1970-01-01T00%3A00%3A00.000Z&toAt=2026-09-15T15%3A30%3A00.000Z",
      expect.objectContaining({ headers: { Cookie: "gerec_session=sessao" } }),
    );
  });
});
````

## Snapshot de código: `apps/web/src/lib/reports/queries.ts`

````typescript
import { apiFetch } from "../api/client";
import type { LeadDistributionReport } from "../api/types";
import { SESSION_COOKIE } from "../auth/session";

export type ReportPeriodKey = "all" | "month" | "last30" | "custom";
export type ReportPeriod = { key: ReportPeriodKey; fromAt: string; toAt: string };
export type InvalidCustomReportPeriod = {
  key: "custom";
  from: string | null;
  to: string | null;
  error: string;
};
export type ReportPeriodResolution = ReportPeriod | InvalidCustomReportPeriod;
export type ReportSearchParams = Record<string, string | string[] | undefined>;

const ALL_HISTORY_FROM = "1970-01-01T00:00:00.000Z";
const SAO_PAULO_TIME_ZONE = "America/Sao_Paulo";
const dateTimeFormatter = new Intl.DateTimeFormat("en-US", {
  timeZone: SAO_PAULO_TIME_ZONE,
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
  hourCycle: "h23",
  timeZoneName: "longOffset",
});

function valueOf(value: string | string[] | undefined): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function dateParts(date: Date): Record<string, string> {
  return Object.fromEntries(
    dateTimeFormatter
      .formatToParts(date)
      .filter((part) => part.type !== "literal")
      .map((part) => [part.type, part.value]),
  );
}

function saoPauloOffsetMilliseconds(date: Date): number {
  const offset = dateParts(date).timeZoneName;
  const match = /^GMT([+-])(\d{2}):(\d{2})$/.exec(offset ?? "");
  if (!match) throw new Error("Não foi possível determinar o fuso de São Paulo.");
  const milliseconds = (Number(match[2]) * 60 + Number(match[3])) * 60 * 1000;
  return match[1] === "+" ? milliseconds : -milliseconds;
}

function saoPauloDate(value: string | null): Date | null {
  if (!value || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return null;
  const [year, month, day] = value.split("-").map(Number);
  const localMidnight = Date.UTC(year, month - 1, day);
  if (Number.isNaN(localMidnight)) return null;
  const calendarDate = new Date(localMidnight);
  if (
    calendarDate.getUTCFullYear() !== year
    || calendarDate.getUTCMonth() !== month - 1
    || calendarDate.getUTCDate() !== day
  ) return null;
  let instant = localMidnight - saoPauloOffsetMilliseconds(new Date(localMidnight));
  instant = localMidnight - saoPauloOffsetMilliseconds(new Date(instant));
  return new Date(instant);
}

function saoPauloMonthStart(now: Date): Date {
  const parts = dateParts(now);
  return saoPauloDate(`${parts.year}-${parts.month}-01`) as Date;
}

function allHistory(now: Date): ReportPeriod {
  return { key: "all", fromAt: ALL_HISTORY_FROM, toAt: now.toISOString() };
}

export function isReportPeriod(period: ReportPeriodResolution): period is ReportPeriod {
  return "fromAt" in period;
}

/** Converts São Paulo calendar controls into the explicit UTC interval required by the API. */
export function reportPeriod(searchParams: ReportSearchParams, now = new Date()): ReportPeriodResolution {
  const key = valueOf(searchParams.period);
  if (key === "last30") {
    return { key, fromAt: new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString(), toAt: now.toISOString() };
  }
  if (key === "month") {
    return { key, fromAt: saoPauloMonthStart(now).toISOString(), toAt: now.toISOString() };
  }
  if (key === "custom") {
    const fromValue = valueOf(searchParams.from);
    const toValue = valueOf(searchParams.to);
    const from = saoPauloDate(fromValue);
    const to = saoPauloDate(toValue);
    if (from && to && from < to) {
      return { key, fromAt: from.toISOString(), toAt: to.toISOString() };
    }
    return {
      key,
      from: fromValue,
      to: toValue,
      error: "Informe as duas datas de um período personalizado válido.",
    };
  }
  return allHistory(now);
}

export async function getLeadDistributionReport(
  sessionToken: string,
  period: ReportPeriod,
): Promise<LeadDistributionReport> {
  const searchParams = new URLSearchParams({ fromAt: period.fromAt, toAt: period.toAt });
  return apiFetch<LeadDistributionReport>(
    `/api/admin/reports/lead-distribution?${searchParams.toString()}`,
    { cache: "no-store", headers: { Cookie: `${SESSION_COOKIE}=${sessionToken}` } },
  );
}
````

## Snapshot de código: `apps/web/src/lib/reports/queries-regression.test.ts`

````typescript
import { describe, expect, it } from "vitest";

import { reportPeriod } from "./queries";

describe("regressões de período de relatórios", () => {
  it("rejeita dia e mês inexistentes sem normalizar o intervalo personalizado", () => {
    for (const searchParams of [
      { period: "custom", from: "2026-02-30", to: "2026-03-05" },
      { period: "custom", from: "2026-13-01", to: "2026-13-02" },
    ]) {
      expect(reportPeriod(searchParams, new Date("2026-09-15T15:30:00.000Z"))).toEqual({
        key: "custom",
        from: searchParams.from,
        to: searchParams.to,
        error: "Informe as duas datas de um período personalizado válido.",
      });
    }
  });

  it("mantém período personalizado inválido fora do histórico inteiro", () => {
    expect(
      reportPeriod(
        { period: "custom", from: "2026-09-01", to: "" },
        new Date("2026-09-15T15:30:00.000Z"),
      ),
    ).toEqual({
      key: "custom",
      from: "2026-09-01",
      to: null,
      error: "Informe as duas datas de um período personalizado válido.",
    });
  });
});
````

## Snapshot de código: `apps/web/src/lib/users/actions.ts`

````typescript
"use server";

import { revalidatePath } from "next/cache";

import {
  ApiRequestError,
  createManagedUser,
  resetManagedUserPassword,
  setManagedUserAvailability,
} from "../api/client";
import type { CreateManagedUserInput, ManagedUser } from "../api/types";
import { getSessionContext } from "../auth/session";

export type UserMutationResult =
  | { status: "success"; message: string; user: ManagedUser }
  | { status: "error"; message: string; user: null };

function actionError(error: unknown): string {
  if (error instanceof ApiRequestError) return error.message;
  return "Não foi possível concluir a ação. Tente novamente.";
}

async function sessionToken(): Promise<string | null> {
  const session = await getSessionContext();
  return session.status === "authenticated" && session.profile.role === "admin" ? session.sessionToken : null;
}

function refreshUsers(): void {
  revalidatePath("/usuarios");
  revalidatePath("/dashboard");
  revalidatePath("/fila");
}

export async function createManagedUserAction(input: CreateManagedUserInput): Promise<UserMutationResult> {
  if (!input.fullName.trim() || !input.email.trim() || !input.password.trim()) {
    return { status: "error", message: "Preencha nome, e-mail e senha para criar o usuário.", user: null };
  }
  const token = await sessionToken();
  if (!token) return { status: "error", message: "Sessão expirada. Entre novamente.", user: null };
  try {
    const user = await createManagedUser({ ...input, fullName: input.fullName.trim(), email: input.email.trim() }, token);
    refreshUsers();
    return { status: "success", message: "Usuário criado.", user };
  } catch (error) {
    return { status: "error", message: actionError(error), user: null };
  }
}

export async function setManagedUserAvailabilityAction(userId: string, paused: boolean): Promise<UserMutationResult> {
  const token = await sessionToken();
  if (!token) return { status: "error", message: "Sessão expirada. Entre novamente.", user: null };
  try {
    const user = await setManagedUserAvailability(userId, paused, token);
    refreshUsers();
    return { status: "success", message: paused ? "Vendedor pausado." : "Vendedor ativado.", user };
  } catch (error) {
    return { status: "error", message: actionError(error), user: null };
  }
}

export async function resetManagedUserPasswordAction(userId: string, password: string): Promise<UserMutationResult> {
  if (!password.trim()) return { status: "error", message: "Informe uma nova senha.", user: null };
  const token = await sessionToken();
  if (!token) return { status: "error", message: "Sessão expirada. Entre novamente.", user: null };
  try {
    const user = await resetManagedUserPassword(userId, password, token);
    refreshUsers();
    return { status: "success", message: "Senha redefinida.", user };
  } catch (error) {
    return { status: "error", message: actionError(error), user: null };
  }
}
````
