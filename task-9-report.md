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
