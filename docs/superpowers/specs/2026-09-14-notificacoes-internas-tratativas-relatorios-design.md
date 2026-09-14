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
