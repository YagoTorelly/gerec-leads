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
