import {
  buildDashboardData,
  type RawAttempt,
  type RawCampaign,
  type RawCompany,
  type RawFeedback,
  type RawLead,
  type RawProfile,
  type RawQualificationEvent,
  type RawQueueEntry,
  type RawQueueState,
  type RawSale,
  type RawSkipBalance,
  type RawSourceRecord,
} from "./build-dashboard-data";
import { getDemoDashboardData } from "./demo-data";
import type { DashboardData, SessionProfile } from "./types";
import { inFilter, supabaseRestSelect } from "../supabase/rest";

async function selectByLeadIds<T>(tablePath: string, leadIds: number[], accessToken: string) {
  if (leadIds.length === 0) return [];
  return supabaseRestSelect<T>(`${tablePath}&lead_id=in.${inFilter(leadIds)}`, accessToken);
}

export async function getDashboardData(
  profile: SessionProfile,
  accessToken: string,
): Promise<DashboardData> {
  try {
    const leads = await supabaseRestSelect<RawLead>(
      [
        "leads?select=id,company_id,campaign_id,current_assignee_id,assignment_status,qualification_status,conversion_status,commercial_status,source_entered_at,feedback_due_at,updated_at",
        "archived_at=is.null",
        "order=feedback_due_at.asc.nullslast",
        "limit=200",
      ].join("&"),
      accessToken,
    );
    const leadIds = leads.map((lead) => lead.id);
    const companyIds = [...new Set(leads.map((lead) => lead.company_id))];
    const campaignIds = [...new Set(leads.map((lead) => lead.campaign_id))];

    const [
      profiles,
      companies,
      campaigns,
      sourceRecords,
      queueEntries,
      queueState,
      skipBalances,
      attempts,
      feedbacks,
      qualificationEvents,
      sales,
    ] = await Promise.all([
      profile.role === "admin"
        ? supabaseRestSelect<RawProfile>(
            "profiles?select=user_id,full_name,email,role,is_active&order=full_name.asc",
            accessToken,
          )
        : Promise.resolve([
            {
              user_id: profile.userId,
              full_name: profile.fullName,
              email: profile.email,
              role: profile.role,
              is_active: true,
            },
          ]),
      companyIds.length === 0
        ? Promise.resolve([])
        : supabaseRestSelect<RawCompany>(
            `companies?select=id,legal_name,document_display&id=in.${inFilter(companyIds)}`,
            accessToken,
          ),
      campaignIds.length === 0
        ? Promise.resolve([])
        : supabaseRestSelect<RawCampaign>(
            `campaigns?select=id,display_name&id=in.${inFilter(campaignIds)}`,
            accessToken,
          ),
      selectByLeadIds<RawSourceRecord>(
        "lead_source_records?select=lead_id,mock_has_cnpj_or_mei,full_name,phone,email",
        leadIds,
        accessToken,
      ),
      supabaseRestSelect<RawQueueEntry>(
        "seller_queue?select=seller_id,position,is_paused&order=position.asc",
        accessToken,
      ),
      supabaseRestSelect<RawQueueState>("queue_state?select=next_seller_id&singleton=eq.true&limit=1", accessToken).then((rows) => rows[0] ?? null),
      supabaseRestSelect<RawSkipBalance>(
        "seller_skip_balances?select=seller_id,balance",
        accessToken,
      ),
      selectByLeadIds<RawAttempt>(
        "contact_attempts?select=id,lead_id,seller_id,comment,created_at",
        leadIds,
        accessToken,
      ),
      selectByLeadIds<RawFeedback>(
        "feedbacks?select=id,lead_id,seller_id,comment,created_at",
        leadIds,
        accessToken,
      ),
      selectByLeadIds<RawQualificationEvent>(
        "qualification_events?select=id,lead_id,actor_id,outcome,reason,comment,created_at",
        leadIds,
        accessToken,
      ),
      selectByLeadIds<RawSale>(
        "sales?select=id,lead_id,credited_seller_id,comment,won_at,reversed_at",
        leadIds,
        accessToken,
      ),
    ]);

    return buildDashboardData({
      leads,
      profiles,
      companies,
      campaigns,
      sourceRecords,
      queueEntries,
      queueState,
      skipBalances,
      attempts,
      feedbacks,
      qualificationEvents,
      sales,
      source: "supabase",
    });
  } catch (error) {
    return {
      ...getDemoDashboardData(profile),
      warning:
        error instanceof Error
          ? `Falha ao consultar Supabase local: ${error.message}`
          : "Falha ao consultar Supabase local.",
    };
  }
}
