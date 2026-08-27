import { randomUUID } from "node:crypto";
import { supabaseAdminRestPatch, supabaseAdminRestSelect, supabaseAdminRestUpsert } from "../supabase/admin";
import { nextFeedbackDueAt, toSaoPauloDateKey, validateAttempt } from "./attempt-rules";

type LeadRow = { id: number; current_assignee_id: string | null; feedback_due_at: string | null };
type AssignmentRow = { id: number };
type AttemptRow = { business_date: string };

export async function registerContactAttempt(input: { leadId: number; sellerId: string; comment: string; commercialStatus?: "undefined" | "negotiation" | "won" | "disqualified" }) {
  const leads = await supabaseAdminRestSelect<LeadRow>(`leads?select=id,current_assignee_id,feedback_due_at&id=eq.${input.leadId}&limit=1`);
  const lead = leads[0];
  if (!lead || lead.current_assignee_id !== input.sellerId) throw new Error("Este lead não pertence ao vendedor atual.");

  const assignments = await supabaseAdminRestSelect<AssignmentRow>(`assignments?select=id&lead_id=eq.${input.leadId}&seller_id=eq.${input.sellerId}&ended_at=is.null&limit=1`);
  const assignment = assignments[0];
  if (!assignment) throw new Error("Não existe uma atribuição ativa para este lead.");

  const attempts = await supabaseAdminRestSelect<AttemptRow>(`contact_attempts?select=business_date&lead_id=eq.${input.leadId}&order=business_date.asc`);
  const now = new Date();
  const businessDate = toSaoPauloDateKey(now);
  validateAttempt({
    comment: input.comment,
    attemptCount: attempts.length,
  });

  // Cada envio confirmado representa uma tentativa distinta, inclusive no
  // mesmo dia. A chave não pode mais depender apenas de lead + data.
  const idempotencyKey = randomUUID();
  await supabaseAdminRestUpsert("contact_attempts?on_conflict=idempotency_key", {
    lead_id: input.leadId,
    assignment_id: assignment.id,
    seller_id: input.sellerId,
    channel: "whatsapp",
    business_date: businessDate,
    comment: input.comment.trim(),
    idempotency_key: idempotencyKey,
    created_at: now.toISOString(),
  });

  await supabaseAdminRestPatch(`leads?id=eq.${input.leadId}`, {
    feedback_due_at: nextFeedbackDueAt(now).toISOString(),
    ...(input.commercialStatus ? { commercial_status: input.commercialStatus } : {}),
    updated_at: now.toISOString(),
  });
}
