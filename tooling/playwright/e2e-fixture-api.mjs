import { createServer } from "node:http";

const FIXTURE_PASSWORD = "teste-local-wtg";
const FIXTURE_NOW = "2026-08-28T15:00:00.000Z";
const QUEUE_CURSOR_SELLER_ID = "seller-jessica";

function fixtureState() {
  const users = [
    { id: "admin-yago", fullName: "Yago", email: "yago.e2e@wtg.test", role: "admin", active: true, paused: null },
    { id: "admin-andre", fullName: "André", email: "andre.e2e@wtg.test", role: "admin", active: true, paused: null },
    { id: "seller-renato", fullName: "Renato", email: "renato.e2e@wtg.test", role: "seller", active: true, paused: false },
    { id: "seller-sandra", fullName: "Sandra", email: "sandra.e2e@wtg.test", role: "seller", active: true, paused: false },
    { id: "seller-jessica", fullName: "Jessica", email: "jessica.e2e@wtg.test", role: "seller", active: true, paused: false },
    { id: "seller-nelma", fullName: "Nelma", email: "nelma.e2e@wtg.test", role: "seller", active: true, paused: false },
  ];
  const leads = [
    ["lead-renato-1", "Débora Souza", "seller-renato"],
    ["lead-renato-2", "Ana Silva", "seller-renato"],
    ["lead-sandra-1", "Wesley Souza", "seller-sandra"],
    ["lead-sandra-2", "Jussara Nadja da Silva", "seller-sandra"],
    ["lead-jessica-1", "Lead Jessica 1", "seller-jessica"],
    ["lead-nelma-1", "Lead Nelma 1", "seller-nelma"],
  ].map(([id, contactName, sellerId], index) => ({
    id,
    contactName,
    sellerId,
    companyName: `${contactName} LTDA`,
    campaignName: "Seguro empresarial - Agosto",
    phoneDisplay: `(11) 98830-80${20 + index}`,
    email: `${id}@wtg.test`,
    commercialStatus: "undefined",
    isDisqualified: false,
    commentCount: 0,
    assignedAt: `2026-08-28T1${index}:00:00.000Z`,
    lastUpdatedAt: `2026-08-28T1${index}:00:00.000Z`,
    feedbackDueAt: index === 0 ? "2026-08-27T18:00:00.000Z" : "2026-08-29T18:00:00.000Z",
  }));
  const nelmaLead = leads.find((lead) => lead.sellerId === "seller-nelma");
  if (nelmaLead) {
    nelmaLead.isDisqualified = true;
    nelmaLead.commercialStatus = "won";
    nelmaLead.commentCount = 1;
    nelmaLead.lastUpdatedAt = FIXTURE_NOW;
    nelmaLead.feedbackDueAt = null;
  }
  return {
    users,
    leads,
    treatments: nelmaLead
      ? [
          {
            leadId: nelmaLead.id,
            leadName: nelmaLead.contactName,
            sellerId: nelmaLead.sellerId,
            sellerName: "Nelma",
            comment: "Cliente atendido fora do escopo, com fechamento excepcional.",
            commercialStatus: "won",
            isDisqualified: true,
            assignedAt: nelmaLead.assignedAt,
            lastUpdatedAt: nelmaLead.lastUpdatedAt,
            createdAt: FIXTURE_NOW,
          },
        ]
      : [],
    sessions: new Map(),
    nextUser: 1,
    nextTreatment: 1,
  };
}

function json(response, status, body, headers = {}) {
  response.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "x-gerec-api-contract-version": "1",
    ...headers,
  });
  response.end(JSON.stringify(body));
}

function empty(response, status = 204, headers = {}) {
  response.writeHead(status, { "x-gerec-api-contract-version": "1", ...headers });
  response.end();
}

function cookie(request) {
  return request.headers.cookie?.match(/(?:^|;\s*)gerec_session=([^;]+)/)?.[1] ?? null;
}

async function body(request) {
  const chunks = [];
  for await (const chunk of request) chunks.push(chunk);
  try {
    return JSON.parse(Buffer.concat(chunks).toString("utf8") || "{}");
  } catch {
    return null;
  }
}

function publicUser(user) {
  return {
    id: user.id,
    fullName: user.fullName,
    email: user.email,
    role: user.role,
    active: user.active,
    paused: user.paused,
  };
}

function sessionUser(state, request) {
  const id = state.sessions.get(cookie(request));
  return state.users.find((user) => user.id === id && user.active) ?? null;
}

function sellerName(state, sellerId) {
  return state.users.find((user) => user.id === sellerId)?.fullName ?? "Não informado";
}

function sellerQueueBase(state) {
  return state.users
    .filter((user) => user.role === "seller")
    .map((user, index) => ({
      sellerId: user.id,
      sellerName: user.fullName,
      position: index + 1,
      availability: user.paused ? "paused" : "active",
      reason: user.paused ? "Pausado manualmente pelo administrador" : null,
      skipBalance: 0,
    }));
}

function queue(state) {
  const entries = sellerQueueBase(state);
  const cursor = entries.findIndex((entry) => entry.sellerId === QUEUE_CURSOR_SELLER_ID);
  if (cursor < 0) return entries;
  return [...entries.slice(cursor), ...entries.slice(0, cursor)];
}

function page(items, url) {
  const requested = Number(url.searchParams.get("page") ?? "1");
  const limit = Number(url.searchParams.get("limit") ?? "50");
  const start = (Math.max(1, requested) - 1) * limit;
  return {
    items: items.slice(start, start + limit),
    page: Math.max(1, requested),
    pageSize: limit,
    total: items.length,
  };
}

function dashboard(state, user, url) {
  const allLeads = state.leads.map((lead) => ({
    ...lead,
    sellerName: sellerName(state, lead.sellerId),
  }));
  const allTreatments = state.treatments
    .slice()
    .reverse()
    .map(({ sellerId: _sellerId, ...item }) => item);
  if (user.role === "seller") {
    const ownLeads = allLeads.filter((lead) => lead.sellerId === user.id);
    const ownTreatments = state.treatments
      .filter((item) => item.sellerId === user.id)
      .slice()
      .reverse()
      .map(({ sellerId: _sellerId, ...item }) => item);
    const item = queue(state).find((entry) => entry.sellerName === user.fullName);
    return {
      user: { id: user.id, email: user.email, role: "seller" },
      leads: page(ownLeads, url),
      history: page(ownTreatments, url),
      queue: {
        position: item ? queue(state).findIndex((entry) => entry.sellerId === user.id) + 1 : null,
        availability: item?.availability ?? "blocked_overdue",
        skipBalance: item?.skipBalance ?? 0,
      },
    };
  }
  const entries = queue(state);
  return {
    user: { id: user.id, email: user.email, role: "admin" },
    leads: page(allLeads, url),
    history: page(allTreatments, url),
    queue: {
      items: entries,
      total: entries.length,
      cursorSellerName: "Jessica",
      nextSellerName: "Jessica",
    },
  };
}

export function createE2eFixtureServer() {
  let state = fixtureState();
  return createServer(async (request, response) => {
    const url = new URL(request.url ?? "/", "http://127.0.0.1");
    const method = request.method ?? "GET";
    if (method === "POST" && url.pathname === "/__e2e/reset") {
      state = fixtureState();
      return empty(response);
    }
    if (method === "GET" && url.pathname === "/health") {
      return json(response, 200, { status: "ok", database: "gerec_e2e_fixture" });
    }

    if (method === "POST" && url.pathname === "/auth/login") {
      const input = await body(request);
      const user = state.users.find((item) => item.email === input?.email && item.active);
      if (!user || input?.password !== FIXTURE_PASSWORD) {
        return json(response, 401, { detail: "Invalid credentials" });
      }
      const token = `fixture-${user.id}`;
      state.sessions.set(token, user.id);
      return json(
        response,
        200,
        { user: { id: user.id, email: user.email, role: user.role } },
        { "set-cookie": `gerec_session=${token}; Max-Age=28800; Path=/; HttpOnly; SameSite=Lax` },
      );
    }

    const user = sessionUser(state, request);
    if (!user) return json(response, 401, { detail: "Invalid credentials" });
    if (method === "GET" && url.pathname === "/auth/me") {
      return json(response, 200, { id: user.id, email: user.email, role: user.role });
    }
    if (method === "POST" && url.pathname === "/auth/logout") {
      state.sessions.delete(cookie(request));
      return empty(response, 204, { "set-cookie": "gerec_session=; Max-Age=0; Path=/" });
    }
    if (method === "GET" && url.pathname === "/api/dashboard") {
      return json(response, 200, dashboard(state, user, url));
    }

    if (url.pathname.startsWith("/api/admin/")) {
      if (user.role !== "admin") return json(response, 403, { detail: "Forbidden" });
      if (method === "GET" && url.pathname === "/api/admin/users") {
        return json(response, 200, page(state.users.map(publicUser), url));
      }
      if (method === "POST" && url.pathname === "/api/admin/users") {
        const input = await body(request);
        if (
          !input?.fullName?.trim() ||
          !input?.email?.trim() ||
          !input?.password?.trim() ||
          !["admin", "seller"].includes(input.role)
        ) {
          return json(response, 422, { detail: "Invalid user" });
        }
        const created = {
          id: `fixture-user-${state.nextUser++}`,
          fullName: input.fullName.trim(),
          email: input.email.trim(),
          role: input.role,
          active: true,
          paused: input.role === "seller" ? false : null,
        };
        state.users.push(created);
        return json(response, 201, publicUser(created));
      }
      const match = url.pathname.match(/^\/api\/admin\/users\/([^/]+)\/(availability|password)$/);
      if (method === "PATCH" && match) {
        const target = state.users.find((item) => item.id === decodeURIComponent(match[1]));
        if (!target) return json(response, 404, { detail: "User not found" });
        const input = await body(request);
        if (match[2] === "availability") {
          if (target.role !== "seller" || typeof input?.paused !== "boolean") {
            return json(response, 422, { detail: "Invalid availability" });
          }
          target.paused = input.paused;
        } else if (!input?.password?.trim()) {
          return json(response, 422, { detail: "Invalid password" });
        }
        return json(response, 200, publicUser(target));
      }
    }

    const treatmentPath = url.pathname.match(/^\/api\/leads\/([^/]+)\/treatments$/);
    if (treatmentPath) {
      const lead = state.leads.find((item) => item.id === decodeURIComponent(treatmentPath[1]));
      if (!lead || (user.role === "seller" && lead.sellerId !== user.id)) {
        return json(response, 403, { detail: "Forbidden" });
      }
      if (method === "GET") {
        const treatments = state.treatments
          .filter((item) => item.leadId === lead.id)
          .slice()
          .reverse()
          .map(({ sellerId: _sellerId, ...item }) => item);
        return json(response, 200, page(treatments, url));
      }
      if (method === "POST") {
        if (user.role !== "seller") return json(response, 403, { detail: "Forbidden" });
        const input = await body(request);
        if (
          !input?.comment?.trim() ||
          input.comment.trim().length < 6 ||
          !["undefined", "negotiation", "won"].includes(input.commercialStatus)
        ) {
          return json(response, 422, { detail: "Invalid treatment" });
        }
        lead.commercialStatus = input.commercialStatus;
        lead.isDisqualified = input.isDisqualified === true || lead.isDisqualified;
        lead.commentCount += 1;
        const createdAt = `2026-08-28T15:0${state.nextTreatment}:00.000Z`;
        lead.lastUpdatedAt = createdAt;
        if (lead.isDisqualified) {
          lead.feedbackDueAt = null;
        }
        state.treatments.push({
          leadId: lead.id,
          leadName: lead.contactName,
          sellerId: user.id,
          sellerName: user.fullName,
          comment: input.comment.trim(),
          commercialStatus: lead.commercialStatus,
          isDisqualified: lead.isDisqualified,
          assignedAt: lead.assignedAt,
          lastUpdatedAt: lead.lastUpdatedAt,
          createdAt,
        });
        state.nextTreatment += 1;
        return json(response, 201, {
          leadId: lead.id,
          treatmentId: `treatment-${state.nextTreatment}`,
          status: "recorded",
          commercialStatus: lead.commercialStatus,
          isDisqualified: lead.isDisqualified,
          commentCount: lead.commentCount,
          reminderAt: lead.isDisqualified ? null : "2026-08-29T14:00:00.000Z",
          dueAt: lead.feedbackDueAt,
        });
      }
    }
    return json(response, 404, { detail: "Not found" });
  });
}

if (import.meta.url === `file://${process.argv[1]?.replace(/\\/g, "/")}`) {
  const port = Number(process.env.E2E_FIXTURE_API_PORT ?? "18012");
  createE2eFixtureServer().listen(port, "127.0.0.1", () =>
    console.log(`E2E fixture API at ${port}`),
  );
}
