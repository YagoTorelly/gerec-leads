import { createHash } from "node:crypto";
import { restPatch, restSelect, restUpsert } from "./admin-client.mjs";

const DEMO_IMPORT_RUN_KEY = "demo-local-workspace-2026-08-26-v3";
const DEMO_CORRELATION_ID = "9c6c6b4b-0a2a-4c65-8b7b-20de20260002";

const DEMO_CAMPAIGNS = [
  {
    external_id: "demo-campaign-main",
    source_name: "WTG - Planilha Mock",
    display_name: "WTG - Planilha Mock",
    status: "approved",
  },
  {
    external_id: "demo-campaign-follow-up",
    source_name: "WTG - Follow Up",
    display_name: "WTG - Follow Up",
    status: "approved",
  },
  {
    external_id: "demo-campaign-pending",
    source_name: "Campanha pendente",
    display_name: "Campanha pendente",
    status: "pending_approval",
  },
];

const DEMO_LEADS = [
  {
    sourceLeadId: "demo-lead-101",
    campaignExternalId: "demo-campaign-main",
    sellerEmail: "renato@gerec.local",
    company: {
      document_type: "cnpj",
      document_normalized: "00000000000191",
      document_display: "00.000.000/0001-91",
      legal_name: "Meta Servicos Integrados",
      state: "SP",
    },
    lead: {
      assignment_status: "assigned",
      qualification_status: "pending",
      conversion_status: "active",
      source_entered_at: "2026-08-25T12:15:00.000Z",
      feedback_due_at: "2026-08-26T19:00:00.000Z",
      updated_at: "2026-08-26T10:40:00.000Z",
    },
    source: {
      source_row: 2,
      source_entered_at: "2026-08-25T12:15:00.000Z",
      campaign_name: "WTG - Planilha Mock",
      mock_has_cnpj_or_mei: "Possui CNPJ ativo",
      full_name: "Marina Costa",
      phone: "(11) 98888-0101",
      email: "marina@meta.com",
    },
    assignment: {
      assignment_type: "normal",
      started_at: "2026-08-25T12:30:00.000Z",
      reason: "Distribuição inicial",
      actorEmail: "admin@gerec.local",
    },
    feedbackCycles: [
      {
        cycle_number: 1,
        starts_at: "2026-08-25T12:30:00.000Z",
        reminder_at: "2026-08-26T15:00:00.000Z",
        due_at: "2026-08-26T19:00:00.000Z",
        close_reason: null,
        closed_at: null,
      },
    ],
    feedbacks: [
      {
        comment: "Cliente pediu retorno com proposta formal.",
        created_at: "2026-08-25T17:45:00.000Z",
      },
    ],
    attempts: [
      {
        business_date: "2026-08-25",
        comment: "Primeiro contato enviado via WhatsApp.",
        created_at: "2026-08-25T15:00:00.000Z",
      },
      {
        business_date: "2026-08-26",
        comment: "Follow-up enviado com apresentação da WTG.",
        created_at: "2026-08-26T10:40:00.000Z",
      },
    ],
  },
  {
    sourceLeadId: "demo-lead-102",
    campaignExternalId: "demo-campaign-main",
    sellerEmail: "sandra@gerec.local",
    company: {
      document_type: "cnpj",
      document_normalized: "00000000000272",
      document_display: "00.000.000/0002-72",
      legal_name: "Rafael Nunes Studio",
      state: "SP",
    },
    lead: {
      assignment_status: "assigned",
      qualification_status: "pending",
      conversion_status: "active",
      source_entered_at: "2026-08-26T11:00:00.000Z",
      feedback_due_at: "2026-08-26T13:30:00.000Z",
      updated_at: "2026-08-26T11:05:00.000Z",
    },
    source: {
      source_row: 3,
      source_entered_at: "2026-08-26T11:00:00.000Z",
      campaign_name: "WTG - Planilha Mock",
      mock_has_cnpj_or_mei: "MEI em abertura",
      full_name: "Rafael Nunes",
      phone: "(11) 97777-0202",
      email: "rafael@exemplo.com",
    },
    assignment: {
      assignment_type: "normal",
      started_at: "2026-08-26T11:00:00.000Z",
      reason: "Distribuição inicial",
      actorEmail: "admin@gerec.local",
    },
    feedbackCycles: [
      {
        cycle_number: 1,
        starts_at: "2026-08-26T11:00:00.000Z",
        reminder_at: "2026-08-26T12:30:00.000Z",
        due_at: "2026-08-26T13:30:00.000Z",
        close_reason: null,
        closed_at: null,
      },
    ],
    attempts: [
      {
        business_date: "2026-08-26",
        comment: "Primeiro contato enviado via WhatsApp.",
        created_at: "2026-08-26T11:05:00.000Z",
      },
    ],
  },
  {
    sourceLeadId: "demo-lead-103",
    campaignExternalId: "demo-campaign-follow-up",
    sellerEmail: "jessica@gerec.local",
    company: {
      document_type: "cnpj",
      document_normalized: "00000000000353",
      document_display: "00.000.000/0003-53",
      legal_name: "Bianca Ramos Consultoria",
      state: "SP",
    },
    lead: {
      assignment_status: "assigned",
      qualification_status: "qualified",
      conversion_status: "qualified_follow_up",
      source_entered_at: "2026-08-24T14:00:00.000Z",
      feedback_due_at: "2026-08-27T17:00:00.000Z",
      updated_at: "2026-08-26T09:30:00.000Z",
    },
    source: {
      source_row: 4,
      source_entered_at: "2026-08-24T14:00:00.000Z",
      campaign_name: "WTG - Follow Up",
      mock_has_cnpj_or_mei: "Sem CNPJ",
      full_name: "Bianca Ramos",
      phone: "(11) 96666-0303",
      email: "bianca@exemplo.com",
    },
    assignment: {
      assignment_type: "recurring",
      started_at: "2026-08-24T14:20:00.000Z",
      reason: "Retorno do relacionamento",
      actorEmail: "admin@gerec.local",
    },
    feedbackCycles: [
      {
        cycle_number: 1,
        starts_at: "2026-08-24T14:20:00.000Z",
        reminder_at: "2026-08-26T13:00:00.000Z",
        due_at: "2026-08-27T17:00:00.000Z",
        close_reason: null,
        closed_at: null,
      },
    ],
    feedbacks: [
      {
        comment: "Lead segue em acompanhamento com interesse real.",
        created_at: "2026-08-26T09:30:00.000Z",
      },
    ],
    attempts: [
      {
        business_date: "2026-08-24",
        comment: "Contato inicial enviado via WhatsApp.",
        created_at: "2026-08-24T15:00:00.000Z",
      },
      {
        business_date: "2026-08-25",
        comment: "Follow-up com proposta preliminar.",
        created_at: "2026-08-25T16:00:00.000Z",
      },
      {
        business_date: "2026-08-26",
        comment: "Retorno confirmado pelo cliente.",
        created_at: "2026-08-26T09:00:00.000Z",
      },
    ],
    qualificationEvents: [
      {
        outcome: "qualified_follow_up",
        reason: null,
        comment: "Lead qualificado e segue em acompanhamento.",
        created_at: "2026-08-26T09:30:00.000Z",
      },
    ],
  },
  {
    sourceLeadId: "demo-lead-104",
    campaignExternalId: "demo-campaign-follow-up",
    sellerEmail: "nelma@gerec.local",
    company: {
      document_type: "cnpj",
      document_normalized: "00000000000434",
      document_display: "00.000.000/0004-34",
      legal_name: "Pereira Comercio",
      state: "SP",
    },
    lead: {
      assignment_status: "assigned",
      qualification_status: "qualified",
      conversion_status: "won",
      source_entered_at: "2026-08-22T09:40:00.000Z",
      feedback_due_at: null,
      updated_at: "2026-08-25T20:10:00.000Z",
    },
    source: {
      source_row: 5,
      source_entered_at: "2026-08-22T09:40:00.000Z",
      campaign_name: "WTG - Follow Up",
      mock_has_cnpj_or_mei: "CNPJ com interesse",
      full_name: "Lucas Pereira",
      phone: "(11) 95555-0404",
      email: "lucas@exemplo.com",
    },
    assignment: {
      assignment_type: "normal",
      started_at: "2026-08-22T10:00:00.000Z",
      reason: "Distribuição inicial",
      actorEmail: "admin@gerec.local",
    },
    feedbackCycles: [
      {
        cycle_number: 1,
        starts_at: "2026-08-22T10:00:00.000Z",
        reminder_at: "2026-08-25T13:00:00.000Z",
        due_at: "2026-08-25T17:00:00.000Z",
        close_reason: "won",
        closed_at: "2026-08-25T20:10:00.000Z",
      },
    ],
    feedbacks: [
      {
        comment: "Cliente aprovou a proposta e pediu fechamento.",
        created_at: "2026-08-25T18:00:00.000Z",
      },
    ],
    attempts: [
      {
        business_date: "2026-08-22",
        comment: "Contato inicial enviado via WhatsApp.",
        created_at: "2026-08-22T11:00:00.000Z",
      },
      {
        business_date: "2026-08-23",
        comment: "Apresentação comercial compartilhada.",
        created_at: "2026-08-23T15:00:00.000Z",
      },
      {
        business_date: "2026-08-25",
        comment: "Confirmação final do aceite da proposta.",
        created_at: "2026-08-25T17:40:00.000Z",
      },
    ],
    qualificationEvents: [
      {
        outcome: "won",
        reason: null,
        comment: "Venda confirmada pelo responsável.",
        created_at: "2026-08-25T20:10:00.000Z",
      },
    ],
    sale: {
      comment: "Venda confirmada e crédito atribuído à Nelma.",
      won_at: "2026-08-25T20:10:00.000Z",
    },
  },
  {
    sourceLeadId: "demo-lead-105",
    campaignExternalId: "demo-campaign-pending",
    sellerEmail: null,
    company: {
      document_type: "cnpj",
      document_normalized: "00000000000515",
      document_display: "00.000.000/0005-15",
      legal_name: "Rocha Solucoes",
      state: "SP",
    },
    lead: {
      assignment_status: "parked",
      qualification_status: "pending",
      conversion_status: "active",
      source_entered_at: "2026-08-26T08:20:00.000Z",
      feedback_due_at: null,
      updated_at: "2026-08-26T08:20:00.000Z",
      parked_reason: "campaign_pending",
    },
    source: {
      source_row: 6,
      source_entered_at: "2026-08-26T08:20:00.000Z",
      campaign_name: "Campanha pendente",
      mock_has_cnpj_or_mei: "Aguardando definição",
      full_name: "Priscila Rocha",
      phone: "(11) 94444-0505",
      email: "priscila@exemplo.com",
    },
  },
];

// Complemento determinístico para o cenário local: 20 leads distribuídos
// entre os vendedores, com variedade suficiente para exercitar a operação.
const DEMO_SELLERS = [
  "renato@gerec.local",
  "sandra@gerec.local",
  "jessica@gerec.local",
  "nelma@gerec.local",
];

for (let index = 6; index <= 26; index += 1) {
  const isJessicaStalled = index === 7;
  const sellerEmail = isJessicaStalled
    ? "jessica@gerec.local"
    : DEMO_SELLERS[(index - 6) % DEMO_SELLERS.length];
  const isWon = index % 6 === 0;
  const date = `2026-08-${String(10 + (index % 16)).padStart(2, "0")}`;
  const dueAt = isJessicaStalled
    ? "2026-08-26T10:00:00.000Z"
    : `2026-08-${String(26 + (index % 2)).padStart(2, "0")}T17:00:00.000Z`;

  DEMO_LEADS.push({
    sourceLeadId: `demo-lead-${100 + index}`,
    campaignExternalId: index % 4 === 0 ? "demo-campaign-follow-up" : "demo-campaign-main",
    sellerEmail,
    company: {
      document_type: "cnpj",
      document_normalized: `0000000000${String(100 + index).padStart(4, "0")}`,
      document_display: `00.000.000/00${String(index).padStart(2, "0")}-${String((index * 7) % 100).padStart(2, "0")}`,
      legal_name: `Empresa Demo ${index}`,
      state: "SP",
    },
    lead: {
      assignment_status: "assigned",
      qualification_status: isWon ? "qualified" : "pending",
      conversion_status: isWon ? "won" : "active",
      source_entered_at: `${date}T10:00:00.000Z`,
      feedback_due_at: dueAt,
      updated_at: `${date}T10:30:00.000Z`,
    },
    source: {
      source_row: index + 1,
      source_entered_at: `${date}T10:00:00.000Z`,
      campaign_name: index % 4 === 0 ? "WTG - Follow Up" : "WTG - Planilha Mock",
      mock_has_cnpj_or_mei: index % 3 === 0 ? "MEI ativo" : "Possui CNPJ ativo",
      full_name: `Contato Demo ${index}`,
      phone: `(11) 9${String(7000 + index).padStart(4, "0")}-${String(1000 + index).slice(-4)}`,
      email: `contato${index}@demo.wtg.local`,
    },
    assignment: {
      assignment_type: index % 4 === 0 ? "recurring" : "normal",
      started_at: `${date}T10:15:00.000Z`,
      reason: "Distribuição inicial",
      actorEmail: "admin@gerec.local",
    },
    feedbackCycles: [
      {
        cycle_number: 1,
        starts_at: `${date}T10:15:00.000Z`,
        reminder_at: `${date}T14:00:00.000Z`,
        due_at: dueAt,
        close_reason: isWon ? "won" : null,
        closed_at: isWon ? `${date}T18:00:00.000Z` : null,
      },
    ],
    // A Jessica (lead 107) permanece sem feedback para simular tratativa parada.
    feedbacks: isJessicaStalled || isWon ? [] : [{
      comment: "Contato realizado; aguardando próximo retorno.",
      created_at: `${date}T13:30:00.000Z`,
    }],
    attempts: isJessicaStalled ? [] : [{
      business_date: date,
      comment: "Primeiro contato enviado via WhatsApp.",
      created_at: `${date}T11:00:00.000Z`,
    }],
    qualificationEvents: isWon ? [{
      outcome: "won",
      reason: null,
      comment: "Venda demonstrativa confirmada.",
      created_at: `${date}T18:00:00.000Z`,
    }] : undefined,
    sale: isWon ? {
      comment: "Venda demonstrativa para validação do painel.",
      won_at: `${date}T18:00:00.000Z`,
    } : undefined,
  });
}

function only(values) {
  return values[0] ?? null;
}

async function ensureImportRun(runtime) {
  const existing = await restSelect(
    runtime,
    `import_runs?select=id&idempotency_key=eq.${DEMO_IMPORT_RUN_KEY}&limit=1`,
  );

  if (existing.length > 0) {
    return existing[0];
  }

  return only(
    await restUpsert(runtime, "import_runs?on_conflict=idempotency_key", {
      source_type: "mock_workbook",
      mode: "bootstrap",
      idempotency_key: DEMO_IMPORT_RUN_KEY,
      correlation_id: DEMO_CORRELATION_ID,
      status: "completed",
      rows_read: DEMO_LEADS.length,
      rows_created: DEMO_LEADS.length,
      rows_updated: 0,
      rows_ignored: 0,
      rows_pending: 0,
      rows_failed: 0,
      started_at: "2026-08-26T08:00:00.000Z",
      finished_at: "2026-08-26T08:05:00.000Z",
    }),
  );
}

async function ensureCampaignMap(runtime) {
  for (const campaign of DEMO_CAMPAIGNS) {
    const existing = await restSelect(
      runtime,
      `campaigns?select=id&external_id=eq.${encodeURIComponent(campaign.external_id)}&limit=1`,
    );
    if (existing.length > 0) {
      await restPatch(runtime, `campaigns?id=eq.${existing[0].id}`, campaign);
    } else {
      await restUpsert(runtime, "campaigns", campaign);
    }
  }

  const campaigns = await restSelect(
    runtime,
    "campaigns?select=id,external_id&external_id=in.(demo-campaign-main,demo-campaign-follow-up,demo-campaign-pending)",
  );

  return new Map(campaigns.map((campaign) => [campaign.external_id, campaign.id]));
}

async function ensureCompany(runtime, definition, ownerId) {
  const rows = await restSelect(
    runtime,
    `companies?select=id&document_normalized=eq.${definition.company.document_normalized}&limit=1`,
  );

  const body = { ...definition.company, owner_id: ownerId };
  if (rows.length > 0) {
    await restPatch(runtime, `companies?id=eq.${rows[0].id}`, body);
  } else {
    await restUpsert(runtime, "companies", body);
  }

  if (rows.length > 0) return rows[0];
  return only(await restSelect(
    runtime,
    `companies?select=id&document_normalized=eq.${definition.company.document_normalized}&limit=1`,
  ));
}

async function ensureLead(runtime, leadBody) {
  const existing = await restSelect(
    runtime,
    `leads?select=id&company_id=eq.${leadBody.company_id}&campaign_id=eq.${leadBody.campaign_id}&archived_at=is.null&limit=1`,
  );

  if (existing.length > 0) {
    await restPatch(runtime, `leads?id=eq.${existing[0].id}`, leadBody);
    return { id: existing[0].id };
  }

  return only(await restUpsert(runtime, "leads", leadBody));
}

async function ensureAssignment(runtime, leadId, sellerId, definition, actorId) {
  if (!sellerId) return null;

  return only(
    await restUpsert(runtime, "assignments?on_conflict=idempotency_key", {
      lead_id: leadId,
      seller_id: sellerId,
      assignment_type: definition.assignment.assignment_type,
      started_at: definition.assignment.started_at,
      actor_id: actorId,
      reason: definition.assignment.reason,
      idempotency_key: `${definition.sourceLeadId}-assignment`,
    }),
  );
}

async function ensureFeedbackCycles(runtime, leadId, assignmentId, definition) {
  if (!assignmentId || !definition.feedbackCycles) return;

  for (const cycle of definition.feedbackCycles) {
    await restUpsert(runtime, "feedback_cycles?on_conflict=lead_id,cycle_number", {
      lead_id: leadId,
      assignment_id: assignmentId,
      cycle_number: cycle.cycle_number,
      starts_at: cycle.starts_at,
      reminder_at: cycle.reminder_at,
      due_at: cycle.due_at,
      close_reason: cycle.close_reason,
      closed_at: cycle.closed_at,
    });
  }
}

async function ensureFeedbacks(runtime, leadId, assignmentId, sellerId, definition) {
  if (!assignmentId || !sellerId || !definition.feedbacks) return;

  for (let index = 0; index < definition.feedbacks.length; index += 1) {
    const feedback = definition.feedbacks[index];
    await restUpsert(runtime, "feedbacks?on_conflict=idempotency_key", {
      lead_id: leadId,
      assignment_id: assignmentId,
      seller_id: sellerId,
      comment: feedback.comment,
      contact_started: true,
      idempotency_key: `${definition.sourceLeadId}-feedback-${index + 1}`,
      created_at: feedback.created_at,
    });
  }
}

async function ensureAttempts(runtime, leadId, assignmentId, sellerId, definition) {
  if (!assignmentId || !sellerId || !definition.attempts) return;

  for (let index = 0; index < definition.attempts.length; index += 1) {
    const attempt = definition.attempts[index];
    await restUpsert(runtime, "contact_attempts?on_conflict=idempotency_key", {
      lead_id: leadId,
      assignment_id: assignmentId,
      seller_id: sellerId,
      channel: "whatsapp",
      business_date: attempt.business_date,
      comment: attempt.comment,
      idempotency_key: `${definition.sourceLeadId}-attempt-${index + 1}`,
      created_at: attempt.created_at,
    });
  }
}

async function ensureQualificationEvents(runtime, leadId, assignmentId, sellerId, definition) {
  if (!assignmentId || !sellerId || !definition.qualificationEvents) return [];

  const created = [];
  for (let index = 0; index < definition.qualificationEvents.length; index += 1) {
    const event = definition.qualificationEvents[index];
    const rows = await restUpsert(runtime, "qualification_events?on_conflict=idempotency_key", {
      lead_id: leadId,
      assignment_id: assignmentId,
      actor_id: sellerId,
      outcome: event.outcome,
      reason: event.reason,
      comment: event.comment,
      idempotency_key: `${definition.sourceLeadId}-qualification-${index + 1}`,
      created_at: event.created_at,
    });
    created.push(only(rows));
  }

  return created;
}

async function ensureSale(runtime, leadId, sellerId, qualificationEventId, definition) {
  if (!definition.sale || !sellerId || !qualificationEventId) return;

  await restUpsert(runtime, "sales?on_conflict=qualification_event_id", {
    lead_id: leadId,
    credited_seller_id: sellerId,
    qualification_event_id: qualificationEventId,
    comment: definition.sale.comment,
    won_at: definition.sale.won_at,
    reversed_at: null,
  });
}

async function ensureSourceRecord(runtime, importRunId, leadId, definition) {
  await restUpsert(runtime, "lead_source_records?on_conflict=source_lead_id", {
    source_lead_id: definition.sourceLeadId,
    import_run_id: importRunId,
    lead_id: leadId,
    source_row: definition.source.source_row,
    source_entered_at: definition.source.source_entered_at,
    campaign_external_id: definition.campaignExternalId,
    campaign_name: definition.source.campaign_name,
    mock_has_cnpj_or_mei: definition.source.mock_has_cnpj_or_mei,
    full_name: definition.source.full_name,
    phone: definition.source.phone,
    email: definition.source.email,
    source_status: definition.lead.assignment_status,
    row_hash: createHash("sha256").update(definition.sourceLeadId).digest("hex"),
    normalized_payload: {
      sourceLeadId: definition.sourceLeadId,
      campaignExternalId: definition.campaignExternalId,
      contact: definition.source.full_name,
      phone: definition.source.phone,
      email: definition.source.email,
    },
    is_present: true,
    removed_at: null,
  });
}

export async function seedLocalDemoData(runtime, profileByEmail) {
  const importRun = await ensureImportRun(runtime);
  const campaignIdByExternalId = await ensureCampaignMap(runtime);

  await restUpsert(
    runtime,
    "seller_queue?on_conflict=seller_id",
    [
      { seller_id: profileByEmail.get("renato@gerec.local"), position: 1, is_paused: false },
      { seller_id: profileByEmail.get("sandra@gerec.local"), position: 2, is_paused: false },
      { seller_id: profileByEmail.get("jessica@gerec.local"), position: 3, is_paused: false },
      { seller_id: profileByEmail.get("nelma@gerec.local"), position: 4, is_paused: false },
    ],
  );
  await restUpsert(
    runtime,
    "seller_skip_balances?on_conflict=seller_id",
    [
      { seller_id: profileByEmail.get("renato@gerec.local"), balance: 0 },
      { seller_id: profileByEmail.get("sandra@gerec.local"), balance: 1 },
      { seller_id: profileByEmail.get("jessica@gerec.local"), balance: 0 },
      { seller_id: profileByEmail.get("nelma@gerec.local"), balance: 0 },
    ],
  );

  for (const definition of DEMO_LEADS) {
    const sellerId = definition.sellerEmail ? profileByEmail.get(definition.sellerEmail) : null;
    const actorId = definition.assignment?.actorEmail
      ? profileByEmail.get(definition.assignment.actorEmail)
      : null;
    const company = await ensureCompany(runtime, definition, sellerId);
    const lead = await ensureLead(runtime, {
      company_id: company.id,
      campaign_id: campaignIdByExternalId.get(definition.campaignExternalId),
      current_assignee_id: sellerId,
      assignment_status: definition.lead.assignment_status,
      qualification_status: definition.lead.qualification_status,
      conversion_status: definition.lead.conversion_status,
      source_entered_at: definition.lead.source_entered_at,
      feedback_due_at: definition.lead.feedback_due_at,
      parked_reason: definition.lead.parked_reason ?? null,
      archived_at: null,
      updated_at: definition.lead.updated_at,
    });

    await ensureSourceRecord(runtime, importRun.id, lead.id, definition);
    const assignment = await ensureAssignment(runtime, lead.id, sellerId, definition, actorId);
    await ensureFeedbackCycles(runtime, lead.id, assignment?.id ?? null, definition);
    await ensureFeedbacks(runtime, lead.id, assignment?.id ?? null, sellerId, definition);
    await ensureAttempts(runtime, lead.id, assignment?.id ?? null, sellerId, definition);
    const qualificationEvents = await ensureQualificationEvents(
      runtime,
      lead.id,
      assignment?.id ?? null,
      sellerId,
      definition,
    );
    await ensureSale(
      runtime,
      lead.id,
      sellerId,
      qualificationEvents.at(-1)?.id ?? null,
      definition,
    );
  }
}
