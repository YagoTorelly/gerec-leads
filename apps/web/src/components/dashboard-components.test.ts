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
        availability: "blocked_overdue" as const,
        reason: "Feedback vencido",
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
        feedbackDueAt: "2026-08-29T16:03:04.876Z",
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
    expect(markup).toContain("Bloqueado por atraso");
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
    expect(markup).toContain("Prazo de feedback");
    expect(markup).toContain("Minha posição na fila");
    expect(markup).toContain("Posição 3");
    expect(markup).toContain("Débora Souza");
    expect(markup).not.toContain("Renato");
    expect(markup).not.toContain("Nelma");
    expect(markup).not.toContain("Próximo vendedor");
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
