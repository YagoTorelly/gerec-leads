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
