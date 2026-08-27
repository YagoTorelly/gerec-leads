import { getSlaState } from "./format";
import type { DashboardData, DashboardLead, HistoryEvent } from "./types";

export type RawLead = {
  id: number;
  company_id: number;
  campaign_id: number;
  current_assignee_id: string | null;
  assignment_status: string;
  qualification_status: string;
  conversion_status: string;
  commercial_status?: "undefined" | "negotiation" | "won" | "disqualified";
  source_entered_at: string;
  feedback_due_at: string | null;
  updated_at: string;
};

export type RawProfile = {
  user_id: string;
  full_name: string;
  email: string;
  role?: "admin" | "seller";
  is_active?: boolean;
};

export type RawCompany = {
  id: number;
  legal_name: string | null;
  document_display: string | null;
};

export type RawCampaign = {
  id: number;
  display_name: string;
};

export type RawSourceRecord = {
  lead_id: number | null;
  mock_has_cnpj_or_mei: string | null;
  full_name: string | null;
  phone: string | null;
  email: string | null;
};

export type RawAttempt = {
  id: number;
  lead_id: number;
  seller_id: string;
  comment: string;
  created_at: string;
};

export type RawFeedback = {
  id: number;
  lead_id: number;
  seller_id: string;
  comment: string;
  created_at: string;
};

export type RawQualificationEvent = {
  id: number;
  lead_id: number;
  actor_id: string;
  outcome: string;
  reason: string | null;
  comment: string;
  created_at: string;
};

export type RawQueueEntry = {
  seller_id: string;
  position: number;
  is_paused: boolean;
};

export type RawSkipBalance = {
  seller_id: string;
  balance: number;
};
export type RawQueueState = { next_seller_id: string };

export type RawSale = {
  id: number;
  lead_id: number;
  credited_seller_id: string;
  comment: string | null;
  won_at: string;
  reversed_at: string | null;
};

export type BuildDashboardInput = {
  leads: RawLead[];
  profiles: RawProfile[];
  companies: RawCompany[];
  campaigns: RawCampaign[];
  sourceRecords: RawSourceRecord[];
  queueEntries?: RawQueueEntry[];
  skipBalances?: RawSkipBalance[];
  queueState?: RawQueueState | null;
  attempts: RawAttempt[];
  feedbacks?: RawFeedback[];
  qualificationEvents?: RawQualificationEvent[];
  sales: RawSale[];
  now?: Date;
  source: DashboardData["source"];
  warning?: string;
};

function indexById<T extends { id: number }>(records: T[]) {
  return new Map(records.map((record) => [record.id, record]));
}

function buildHistoryLabel(eventType: HistoryEvent["eventType"], outcome?: string) {
  if (eventType === "attempt") return "Tentativa de contato";
  if (eventType === "feedback") return "Feedback registrado";
  if (eventType === "sale") return "Negócio ganho";

  switch (outcome) {
    case "qualified_follow_up":
      return "Lead qualificado";
    case "qualified_closed_no_conversion":
      return "Encerrado sem conversão";
    case "disqualified":
      return "Lead desqualificado";
    case "won":
      return "Venda confirmada";
    default:
      return "Atualização de qualificação";
  }
}

export function buildDashboardData({
  leads,
  profiles,
  companies,
  campaigns,
  sourceRecords,
  queueEntries = [],
  skipBalances = [],
  queueState = null,
  attempts,
  feedbacks = [],
  qualificationEvents = [],
  sales,
  now = new Date(),
  source,
  warning,
}: BuildDashboardInput): DashboardData {
  const profileById = new Map(profiles.map((profile) => [profile.user_id, profile]));
  const companyById = indexById(companies);
  const campaignById = indexById(campaigns);
  const sourceByLeadId = new Map(
    sourceRecords.flatMap((record) => (record.lead_id === null ? [] : [[record.lead_id, record]])),
  );
  const attemptsByLeadId = attempts.reduce<Map<number, number>>((index, attempt) => {
    index.set(attempt.lead_id, (index.get(attempt.lead_id) ?? 0) + 1);
    return index;
  }, new Map());
  const activeSaleLeadIds = new Set(
    sales.filter((sale) => !sale.reversed_at).map((sale) => sale.lead_id),
  );

  const dashboardLeads: DashboardLead[] = leads.map((lead) => {
    const sourceRecord = sourceByLeadId.get(lead.id);
    const company = companyById.get(lead.company_id);
    const campaign = campaignById.get(lead.campaign_id);
    const seller = lead.current_assignee_id ? profileById.get(lead.current_assignee_id) : undefined;
    const stage = getSlaState(lead.feedback_due_at, now);

    return {
      id: lead.id,
      contactAnswer: sourceRecord?.mock_has_cnpj_or_mei ?? "Nao informado",
      contactName: sourceRecord?.full_name ?? company?.legal_name ?? "Lead sem nome",
      phone: sourceRecord?.phone ?? "Sem telefone",
      email: sourceRecord?.email ?? "Sem e-mail",
      companyName: company?.legal_name ?? company?.document_display ?? "Empresa pendente",
      campaignName: campaign?.display_name ?? "Campanha pendente",
      sellerName: seller?.full_name ?? "Sem vendedor",
      assignmentStatus: lead.assignment_status,
      qualificationStatus: lead.qualification_status,
      conversionStatus: activeSaleLeadIds.has(lead.id) ? "won" : lead.conversion_status,
      commercialStatus: lead.commercial_status ?? (activeSaleLeadIds.has(lead.id) ? "won" : "undefined"),
      sourceEnteredAt: lead.source_entered_at,
      feedbackDueAt: lead.feedback_due_at,
      lastActivityAt: lead.updated_at,
      attemptsCount: attemptsByLeadId.get(lead.id) ?? 0,
      stage,
      isBlockedBySla: stage === "overdue",
    };
  });

  const leadById = new Map(dashboardLeads.map((lead) => [lead.id, lead]));
  const leadOwnerBySellerId = dashboardLeads.reduce<Map<string, DashboardLead[]>>((index, lead) => {
    const sellerId =
      leads.find((candidate) => candidate.id === lead.id)?.current_assignee_id ?? null;
    if (!sellerId) return index;
    const bucket = index.get(sellerId) ?? [];
    bucket.push(lead);
    index.set(sellerId, bucket);
    return index;
  }, new Map());
  const queuePositionBySellerId = new Map(
    queueEntries.map((entry) => [entry.seller_id, entry.position]),
  );
  const skipBalanceBySellerId = new Map(
    skipBalances.map((entry) => [entry.seller_id, entry.balance]),
  );

  const orderedQueue = [...queueEntries].sort((left, right) => left.position - right.position);
  const cursorIndex = queueState?.next_seller_id
    ? orderedQueue.findIndex((entry) => entry.seller_id === queueState.next_seller_id)
    : 0;
  const rotatedQueue = cursorIndex > 0
    ? [...orderedQueue.slice(cursorIndex), ...orderedQueue.slice(0, cursorIndex)]
    : orderedQueue;
  const queue = rotatedQueue
    .map((entry) => {
      const profile = profileById.get(entry.seller_id);
      const sellerLeads = leadOwnerBySellerId.get(entry.seller_id) ?? [];
      const blockedBySla = sellerLeads.some((lead) => lead.isBlockedBySla);
      return {
        sellerId: entry.seller_id,
        sellerName: profile?.full_name ?? "Vendedor sem nome",
        email: profile?.email ?? "sem-email@local",
        position: rotatedQueue.indexOf(entry) + 1,
        // Pausa efetiva combina a pausa manual com o bloqueio automático por SLA.
        isPaused: entry.is_paused || blockedBySla,
        blockedBySla,
        isEligible: !entry.is_paused && !blockedBySla,
        skipBalance: skipBalanceBySellerId.get(entry.seller_id) ?? 0,
        activeLeads: sellerLeads.length,
        overdueLeads: sellerLeads.filter((lead) => lead.stage === "overdue").length,
        nextDueAt:
          sellerLeads
            .map((lead) => lead.feedbackDueAt)
            .filter((value): value is string => Boolean(value))
            .sort()[0] ?? null,
      };
    })
    .sort((left, right) => left.position - right.position);

  const history = [
    ...attempts.map((attempt) => ({
      id: `attempt-${attempt.id}`,
      leadId: attempt.lead_id,
      eventType: "attempt" as const,
      sellerId: attempt.seller_id,
      happenedAt: attempt.created_at,
      comment: attempt.comment,
      outcome: undefined,
    })),
    ...feedbacks.map((feedback) => ({
      id: `feedback-${feedback.id}`,
      leadId: feedback.lead_id,
      eventType: "feedback" as const,
      sellerId: feedback.seller_id,
      happenedAt: feedback.created_at,
      comment: feedback.comment,
      outcome: undefined,
    })),
    ...qualificationEvents.map((event) => ({
      id: `qualification-${event.id}`,
      leadId: event.lead_id,
      eventType: "qualification" as const,
      sellerId: event.actor_id,
      happenedAt: event.created_at,
      comment: event.comment,
      outcome: event.outcome,
    })),
    ...sales
      .filter((sale) => !sale.reversed_at)
      .map((sale) => ({
        id: `sale-${sale.id}`,
        leadId: sale.lead_id,
        eventType: "sale" as const,
        sellerId: sale.credited_seller_id,
        happenedAt: sale.won_at,
        comment: sale.comment ?? "Negócio ganho confirmado.",
        outcome: "won",
      })),
  ]
    .map((event) => {
      const lead = leadById.get(event.leadId);
      const seller = profileById.get(event.sellerId);
      return {
        id: event.id,
        leadId: event.leadId,
        eventType: event.eventType,
        sellerName: seller?.full_name ?? "Sem responsável",
        contactName: lead?.contactName ?? "Lead sem nome",
        companyName: lead?.companyName ?? "Empresa pendente",
        happenedAt: event.happenedAt,
        comment: event.comment,
        label: buildHistoryLabel(event.eventType, event.outcome),
      };
    })
    .sort((left, right) => right.happenedAt.localeCompare(left.happenedAt));

  const users = profiles
    .map((profile) => {
      const sellerLeads = leadOwnerBySellerId.get(profile.user_id) ?? [];
      return {
        userId: profile.user_id,
        fullName: profile.full_name,
        email: profile.email,
        role: profile.role ?? "seller",
        isActive: profile.is_active ?? true,
        isPaused: queue.find((entry) => entry.sellerId === profile.user_id)?.isPaused ?? false,
        queuePosition: queuePositionBySellerId.get(profile.user_id) ?? null,
        skipBalance: skipBalanceBySellerId.get(profile.user_id) ?? 0,
        activeLeads: sellerLeads.length,
        overdueLeads: sellerLeads.filter((lead) => lead.stage === "overdue").length,
      };
    })
    .sort((left, right) => {
      if (left.role !== right.role) return left.role === "admin" ? -1 : 1;
      return left.fullName.localeCompare(right.fullName);
    });

  return {
    leads: dashboardLeads,
    queue,
    history,
    users,
    generatedAt: now.toISOString(),
    source,
    warning,
    summary: {
      total: dashboardLeads.length,
      queued: dashboardLeads.filter((lead) => lead.assignmentStatus === "assigned").length,
      overdue: dashboardLeads.filter((lead) => lead.stage === "overdue").length,
      pending: dashboardLeads.filter((lead) => lead.qualificationStatus === "pending").length,
      won: dashboardLeads.filter((lead) => lead.conversionStatus === "won").length,
      feedbacksToday: dashboardLeads.filter((lead) => lead.stage === "today").length,
      attempts: dashboardLeads.reduce((total, lead) => total + lead.attemptsCount, 0),
    },
  };
}
