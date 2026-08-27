export type UserRole = "admin" | "seller";

export type SessionProfile = {
  userId: string;
  fullName: string;
  email: string;
  role: UserRole;
};

export type LeadStage = "overdue" | "today" | "scheduled" | "none";
export type CommercialStatus = "undefined" | "negotiation" | "won" | "disqualified";

export type DashboardLead = {
  id: number;
  contactAnswer: string;
  contactName: string;
  phone: string;
  email: string;
  companyName: string;
  campaignName: string;
  sellerName: string;
  assignmentStatus: string;
  qualificationStatus: string;
  conversionStatus: string;
  commercialStatus: CommercialStatus;
  sourceEnteredAt: string;
  feedbackDueAt: string | null;
  lastActivityAt: string;
  attemptsCount: number;
  stage: LeadStage;
  isBlockedBySla: boolean;
};

export type DashboardSummary = {
  total: number;
  queued: number;
  overdue: number;
  pending: number;
  won: number;
  feedbacksToday: number;
  attempts: number;
};

export type SellerQueueItem = {
  sellerId: string;
  sellerName: string;
  email: string;
  position: number;
  isPaused: boolean;
  blockedBySla?: boolean;
  isEligible?: boolean;
  skipBalance: number;
  activeLeads: number;
  overdueLeads: number;
  nextDueAt: string | null;
};

export type HistoryEventType = "attempt" | "feedback" | "qualification" | "sale";

export type HistoryEvent = {
  id: string;
  leadId: number;
  eventType: HistoryEventType;
  sellerName: string;
  contactName: string;
  companyName: string;
  happenedAt: string;
  comment: string;
  label: string;
};

export type UserRecord = {
  userId: string;
  fullName: string;
  email: string;
  role: UserRole;
  isActive: boolean;
  isPaused: boolean;
  queuePosition: number | null;
  skipBalance: number;
  activeLeads: number;
  overdueLeads: number;
};

export type DashboardData = {
  leads: DashboardLead[];
  summary: DashboardSummary;
  queue: SellerQueueItem[];
  history: HistoryEvent[];
  users: UserRecord[];
  generatedAt: string;
  source: "supabase" | "demo";
  warning?: string;
};
