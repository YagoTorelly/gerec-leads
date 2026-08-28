# Relatório da Tarefa 9 — Site Next.js via API Python

## Entregue

- Criado `apps/web/src/lib/api/client.ts` com `apiFetch<T>(path, init?)`, tratamento de erros HTTP, 401, 403 e validação.
- Criado contrato de tipos HTTP em `apps/web/src/lib/api/types.ts` e testes unitários do cliente.
- Autenticação web agora chama `/auth/login`, `/auth/me` e `/auth/logout` da API Python. O token HTTP-only da resposta de login é retransmitido como cookie `gerec_session` do domínio web e encaminhado nas chamadas server-side.
- Leituras das páginas dashboard, fila, histórico e usuários usam somente endpoints paginados da API Python.
- Removidos os adaptadores web que acessavam Supabase e variáveis de Supabase; `.env.example` expõe somente `NEXT_PUBLIC_API_URL`.
- Removidos fluxos de simulação, alteração administrativa de usuários e arquivamento que chamavam diretamente o banco e ainda não possuem endpoint Python equivalente.

## Verificação

- `npm --workspace @wtg/web run test`: aprovado (3 arquivos, 7 testes).
- `npm --workspace @wtg/web run typecheck`: aprovado.
- `npm --workspace @wtg/web run lint`: aprovado.
- `npm --workspace @wtg/web run build`: aprovado.

## Limitações conhecidas

- A API atual não expõe comandos para CRUD de usuários, arquivamento ou simulação; a interface deixa de oferecer esses controles até que os endpoints de domínio sejam adicionados.
- A API de identidade não fornece nome completo. Enquanto o contrato não for ampliado, a interface exibe o e-mail como identificação do usuário.
