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
