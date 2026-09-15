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
