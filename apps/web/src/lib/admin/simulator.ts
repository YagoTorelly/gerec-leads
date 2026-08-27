import { randomUUID } from "node:crypto";
import { supabaseAdminRestPatch, supabaseAdminRestSelect, supabaseAdminRestUpsert } from "../supabase/admin";

type Seller = { user_id: string; full_name: string; is_active: boolean };
type QueueRow = { seller_id: string; position: number; is_paused: boolean };
type LeadOwner = { current_assignee_id: string | null };
type QueueState = { next_seller_id: string; version: number };

export async function simulateLeads(quantity: number) {
  const count = Math.min(10, Math.max(1, Math.floor(quantity || 1)));
  const [sellers, queue, overdueLeads, stateRows] = await Promise.all([
    supabaseAdminRestSelect<Seller>("profiles?select=user_id,full_name,is_active&role=eq.seller&is_active=eq.true"),
    supabaseAdminRestSelect<QueueRow>("seller_queue?select=seller_id,position,is_paused&order=position.asc"),
    supabaseAdminRestSelect<LeadOwner>(`leads?select=current_assignee_id&assignment_status=eq.assigned&feedback_due_at=lt.${encodeURIComponent(new Date().toISOString())}&archived_at=is.null`),
    supabaseAdminRestSelect<QueueState>("queue_state?select=next_seller_id,version&singleton=eq.true&limit=1"),
  ]);
  const blocked = new Set(overdueLeads.map((lead) => lead.current_assignee_id).filter(Boolean));
  const activeSellerIds = new Set(sellers.map((seller) => seller.user_id));
  const eligible = queue.filter((entry) => !entry.is_paused && !blocked.has(entry.seller_id) && activeSellerIds.has(entry.seller_id));
  if (eligible.length === 0) throw new Error("Nenhum vendedor elegível para receber o lead.");
  let nextSellerId = stateRows[0]?.next_seller_id ?? queue[0]?.seller_id;
  let stateVersion = stateRows[0]?.version ?? 0;
  const campaign = (await supabaseAdminRestSelect<{ id: number }>("campaigns?select=id&status=eq.approved&limit=1"))[0];
  if (!campaign) throw new Error("Nenhuma campanha aprovada disponível.");

  const runId = randomUUID();
  await supabaseAdminRestUpsert("import_runs", { id: runId, source_type: "mock_workbook", mode: "incremental", idempotency_key: `simulation-${runId}`, correlation_id: runId, status: "completed", rows_read: count, rows_created: count, started_at: new Date().toISOString(), finished_at: new Date().toISOString() });
  for (let index = 0; index < count; index += 1) {
    const now = new Date(Date.now() + index * 1000);
    const start = Math.max(0, queue.findIndex((entry) => entry.seller_id === nextSellerId));
    const seller = Array.from({ length: queue.length }, (_, offset) => queue[(start + offset) % queue.length])
      .find((entry) => eligible.some((candidate) => candidate.seller_id === entry.seller_id));
    if (!seller) throw new Error("Nenhum vendedor elegÃ­vel para receber o lead.");
    const serial = `${Date.now()}${index}`.slice(-12);
    const company = (await supabaseAdminRestUpsert("companies", { document_type: "cnpj", document_normalized: `999${serial}`, document_display: `99.999.999/0001-${String(index + 1).padStart(2, "0")}`, legal_name: `Lead simulado ${serial}`, state: "SP", owner_id: seller.seller_id }, "return=representation") as Array<{ id: number }>)[0];
    const lead = (await supabaseAdminRestUpsert("leads", { company_id: company.id, campaign_id: campaign.id, current_assignee_id: seller.seller_id, assignment_status: "assigned", qualification_status: "pending", conversion_status: "active", source_entered_at: now.toISOString(), feedback_due_at: new Date(now.getTime() + 24 * 60 * 60 * 1000).toISOString(), updated_at: now.toISOString() }, "return=representation") as Array<{ id: number }>)[0];
    await supabaseAdminRestUpsert("lead_source_records", { source_lead_id: `simulation-${runId}-${index}`, import_run_id: runId, lead_id: lead.id, source_row: index + 2, source_entered_at: now.toISOString(), campaign_external_id: "demo-campaign-main", campaign_name: "Simulação local", mock_has_cnpj_or_mei: "Possui CNPJ ativo", full_name: `Contato simulado ${serial}`, phone: `(11) 90000-${String(index).padStart(4, "0")}`, email: `simulado-${serial}@demo.wtg.local`, source_status: "assigned", row_hash: randomUUID().replaceAll("-", "").padEnd(64, "0"), normalized_payload: { simulated: true }, is_present: true }, "return=minimal");
    const assignment = (await supabaseAdminRestUpsert("assignments", { lead_id: lead.id, seller_id: seller.seller_id, assignment_type: "normal", started_at: now.toISOString(), actor_id: seller.seller_id, reason: "Simulação manual da fila", idempotency_key: `simulation-${runId}-${index}` }, "return=representation") as Array<{ id: number }>)[0];
    await supabaseAdminRestUpsert("feedback_cycles", { lead_id: lead.id, assignment_id: assignment.id, cycle_number: 1, starts_at: now.toISOString(), reminder_at: new Date(now.getTime() + 4 * 60 * 60 * 1000).toISOString(), due_at: new Date(now.getTime() + 24 * 60 * 60 * 1000).toISOString() }, "return=minimal");
    const sellerIndex = queue.findIndex((entry) => entry.seller_id === seller.seller_id);
    nextSellerId = queue[(sellerIndex + 1) % queue.length].seller_id;
    stateVersion += 1;
    await supabaseAdminRestPatch("queue_state?singleton=eq.true", { next_seller_id: nextSellerId, version: stateVersion, updated_at: new Date().toISOString() });
  }
  return count;
}
