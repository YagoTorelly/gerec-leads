# Task 5 — Guia de exportações e histórico

## Resultado

- adicionada a guia administrativa `/exportacoes`, visível somente no shell de administrador;
- vendedor é redirecionado para `/dashboard` pelo layout protegido;
- histórico paginado consulta `GET /api/admin/exportations` com cookie de sessão apenas no servidor;
- tela exibe data/hora em `America/Sao_Paulo`, administrador responsável, quantidade, filtros e status;
- download expõe somente “Exportar leads em Excel”; não há download do histórico ou de tratativas;
- `GET /exportacoes/download` transmite o stream `.xlsx` da API sem converter bytes em texto e preserva MIME/nome do arquivo;
- carregamento e erro/retry são renderizados dentro do `AppShell` da rota;
- respostas inválidas da API e mensagens de falha não expõem detalhes internos.

## TDD

RED confirmado em 2026-09-22:

- `exportations-panel`, `exportation-queries`, página e Route Handler ainda inexistentes;
- navegação do administrador ainda não continha “Exportações”.

GREEN focado:

```text
Test Files  5 passed (5)
Tests       12 passed (12)
```

Cobertura adicionada:

- guia ativa somente para administrador;
- vendedor sem acesso à rota;
- contrato/paginação e validação defensiva do histórico;
- campos e estados do histórico, ausência de download do histórico;
- estado vazio, carregamento, erro seguro e retry mantendo o shell;
- proxy autenticado preservando bytes, MIME e `Content-Disposition`;
- falha do download convertida em resposta segura e recuperável.

## Verificações finais

```text
npm run test --workspace @wtg/web
32 arquivos / 122 testes aprovados

npm run typecheck --workspace @wtg/web
aprovado

npm run lint --workspace @wtg/web
0 erros; 1 aviso preexistente em login-form.tsx sobre <img>

npm run build --workspace @wtg/web
aprovado; /exportacoes e /exportacoes/download reconhecidas como rotas dinâmicas

npx prettier --check <arquivos da tarefa>
aprovado

git diff --check
aprovado
```

O primeiro build foi bloqueado porque o `node_modules` temporário era um junction para outro worktree, que o Turbopack rejeita. O junction foi removido, `npm ci --ignore-scripts` instalou dependências localmente e o build seguinte concluiu com sucesso. Nenhum arquivo de dependência foi alterado.

## Auto-revisão

- nenhuma regra de exportação foi levada para React; a API continua gerando o Excel e auditando a operação;
- o Route Handler encaminha somente a sessão HTTP e o stream retornado pela API;
- a autorização real permanece na API, além da proteção visual e de rota do Next;
- nenhuma credencial ou detalhe técnico é serializado para o navegador;
- o diff está limitado à guia, contratos, estilos e testes desta tarefa.
