export type UserRole = "admin" | "seller";

export type CommercialStatus = "undefined" | "negotiation" | "potential" | "won";

export type SellerAvailability = "active" | "paused";

export type ApiUser = { id: string; email: string; role: UserRole };

export type Page<T> = { items: T[]; page: number; pageSize: number; total: number };

/**
 * Identificadores são chaves técnicas para mutações e nunca rótulos da interface.
 * O backend já resolve nomes e status autorizados para cada perfil.
 */
export type OperationalLead = {
  id: string;
  contactName: string;
  sellerName: string;
  companyName: string;
  campaignName: string;
  phoneDisplay: string;
  email: string;
  commercialStatus: CommercialStatus;
  isDisqualified: boolean;
  commentCount: number;
  assignedAt: string | null;
  lastUpdatedAt: string | null;
};

export type Treatment = {
  leadId: string;
  leadName?: string;
  sellerName: string;
  comment: string;
  commercialStatus: CommercialStatus;
  isDisqualified: boolean;
  assignedAt: string | null;
  createdAt: string;
  lastUpdatedAt: string | null;
};

export type QueueEntry = {
  sellerName: string;
  position: number;
  availability: SellerAvailability;
  reason: string | null;
  skipBalance: number;
};

export type AdminQueue = {
  items: QueueEntry[];
  total: number;
  nextSellerName: string;
  cursorSellerName: string;
};

export type SellerQueue = {
  position: number | null;
  availability: SellerAvailability;
  skipBalance: number;
};

export type AdminDashboard = {
  user: ApiUser & { role: "admin" };
  leads: Page<OperationalLead>;
  history: Page<Treatment>;
  queue: AdminQueue;
};

export type SellerDashboard = {
  user: ApiUser & { role: "seller" };
  leads: Page<OperationalLead>;
  history: Page<Treatment>;
  queue: SellerQueue;
};

export type ApiDashboard = AdminDashboard | SellerDashboard;

/** Resposta pública dos comandos administrativos; não contém password ou hash. */
export type ManagedUser = {
  id: string;
  fullName: string;
  email: string;
  role: UserRole;
  active: boolean;
  paused: boolean | null;
};

export type CreateManagedUserInput = {
  fullName: string;
  email: string;
  role: UserRole;
  password: string;
};

export type ResetManagedUserPasswordInput = { password: string };

export type ManualLeadInput = {
  name: string;
  email: string;
  phone: string;
  campaign?: string;
  source?: string;
};

export type ManualLead = {
  leadId: string;
  manualQueueLeadId: string;
  assigneeId: string | null;
  assignedAt: string | null;
  commercialStatus: "undefined";
  source: "manual";
};

export type TreatmentInput = {
  comment: string;
  commercialStatus: CommercialStatus;
  isDisqualified: boolean;
  idempotencyKey: string;
};

export type TreatmentSubmission = {
  leadId: string;
  treatmentId: string;
  status: string;
  commercialStatus: CommercialStatus;
  isDisqualified: boolean;
  commentCount: number;
  lastUpdatedAt: string;
};

export type NewLeadNotification = {
  leadId: string;
  contactName: string;
  assignedAt: string;
};

export type NewLeadNotificationSnapshot = {
  items: NewLeadNotification[];
  watermark: string;
  acknowledgementToken: string;
  watermarkSequence: number;
};

export type LeadDistributionReport = {
  period: { from: string; to: string };
  bySituation: Array<{ commercialStatus: CommercialStatus; count: number }>;
  bySeller: Array<{ sellerId: string; sellerName: string; count: number }>;
};

export type ExportationStatus = "success" | "error";

export type ExportationHistoryItem = {
  createdAt: string;
  administratorName: string;
  leadCount: number;
  filters: Record<string, unknown>;
  status: ExportationStatus;
};
