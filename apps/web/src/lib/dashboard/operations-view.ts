import type { SessionProfile } from "./types";
import type { LeadStage } from "./types";

export type QueueSourceEntry = {
  sellerId: string;
  sellerName: string;
  sellerEmail: string;
  position: number;
  isPaused: boolean;
  skipBalance: number;
};
export type HistorySourceLead = {
  id: number;
  contactName: string;
  companyName: string;
  sellerId: string | null;
  sellerName: string;
  stage: LeadStage;
  feedbackDueAt: string | null;
};
export type HistorySourceProfile = { userId: string; fullName: string };
export type HistorySourceAssignment = {
  id: number;
  leadId: number;
  sellerId: string;
  assignmentType: string;
  startedAt: string;
  reason: string | null;
};
export type HistorySourceFeedback = {
  id: number;
  leadId: number;
  sellerId: string;
  comment: string;
  createdAt: string;
};
export type HistorySourceAttempt = {
  id: number;
  leadId: number;
  sellerId: string;
  comment: string;
  createdAt: string;
  businessDate: string;
};
export type HistorySourceQualification = {
  id: number;
  leadId: number;
  actorId: string;
  outcome: string;
  reason: string | null;
  comment: string;
  createdAt: string;
};
export type HistorySourceSale = {
  id: number;
  leadId: number;
  sellerId: string;
  comment: string;
  wonAt: string;
};

export function buildQueueView(input: {
  profile: SessionProfile;
  leads: HistorySourceLead[];
  queueEntries: QueueSourceEntry[];
  source: "supabase" | "demo";
  nextSellerId: string | null;
  now: Date;
}) {
  return {
    entries: input.queueEntries
      .sort((a, b) => a.position - b.position)
      .map((entry) => {
        const assigned = input.leads.filter((lead) => lead.sellerId === entry.sellerId);
        return {
          ...entry,
          activeLeads: assigned.length,
          overdueLeads: assigned.filter((lead) => lead.stage === "overdue").length,
          dueTodayLeads: assigned.filter((lead) => lead.stage === "today").length,
          isNextInLine: entry.sellerId === input.nextSellerId,
        };
      }),
    generatedAt: input.now.toISOString(),
    source: input.source,
  };
}

export function buildHistoryView(input: {
  profile: SessionProfile;
  leads: HistorySourceLead[];
  profiles: HistorySourceProfile[];
  assignments: HistorySourceAssignment[];
  feedbacks: HistorySourceFeedback[];
  attempts: HistorySourceAttempt[];
  qualifications: HistorySourceQualification[];
  sales: HistorySourceSale[];
  source: "supabase" | "demo";
  now: Date;
}) {
  const leadById = new Map(input.leads.map((lead) => [lead.id, lead]));
  const profileById = new Map(input.profiles.map((profile) => [profile.userId, profile.fullName]));
  const items = [
    ...input.assignments.map((event) => ({
      id: `assignment-${event.id}`,
      leadId: event.leadId,
      type: "assignment",
      sellerName: profileById.get(event.sellerId) ?? "Sem vendedor",
      headline: "Lead atribuído",
      tone: "blue",
      at: event.startedAt,
      detail: event.reason ?? event.assignmentType,
    })),
    ...input.feedbacks.map((event) => ({
      id: `feedback-${event.id}`,
      leadId: event.leadId,
      type: "feedback",
      sellerName: profileById.get(event.sellerId) ?? "Sem vendedor",
      headline: "Feedback registrado",
      tone: "amber",
      at: event.createdAt,
      detail: event.comment,
    })),
    ...input.attempts.map((event) => ({
      id: `attempt-${event.id}`,
      leadId: event.leadId,
      type: "attempt",
      sellerName: profileById.get(event.sellerId) ?? "Sem vendedor",
      headline: "Tentativa WhatsApp",
      tone: "gray",
      at: event.createdAt,
      detail: event.comment,
    })),
    ...input.qualifications.map((event) => ({
      id: `qualification-${event.id}`,
      leadId: event.leadId,
      type: "qualification",
      sellerName: profileById.get(event.actorId) ?? "Sem vendedor",
      headline: "Qualificação registrada",
      tone: "purple",
      at: event.createdAt,
      detail: event.comment,
    })),
    ...input.sales.map((event) => ({
      id: `sale-${event.id}`,
      leadId: event.leadId,
      type: "sale",
      sellerName: profileById.get(event.sellerId) ?? "Sem vendedor",
      headline: "Negocio ganho",
      tone: "green",
      at: event.wonAt,
      detail: event.comment,
    })),
  ].sort((a, b) => new Date(b.at).getTime() - new Date(a.at).getTime());
  return {
    items: items.map((item) => ({
      ...item,
      contactName: leadById.get(item.leadId)?.contactName ?? `Lead #${item.leadId}`,
    })),
    generatedAt: input.now.toISOString(),
    source: input.source,
  };
}
