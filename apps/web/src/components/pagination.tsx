import type { Page } from "../lib/api/types";

export function Pagination({ href, page }: { href: string; page: Page<unknown> }) {
  const query = (number: number) => `${href}?page=${number}`;
  const lastPage = Math.max(1, Math.ceil(page.total / page.pageSize));
  return (
    <nav className="pagination" aria-label="Paginação">
      {page.page > 1 ? <a href={query(page.page - 1)}>Anterior</a> : <span>Anterior</span>}
      <span>
        Página {page.page} de {lastPage}
      </span>
      {page.page < lastPage ? <a href={query(page.page + 1)}>Próxima</a> : <span>Próxima</span>}
    </nav>
  );
}
