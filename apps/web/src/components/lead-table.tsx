"use client";

import { useCallback, useEffect, useState } from "react";

import type { OperationalLead, TreatmentSubmission, UserRole } from "../lib/api/types";
import {
  formatCommentCount,
  formatCommercialStatus,
  formatDisqualificationMarker,
  formatSlaDeadline,
  getSlaState,
} from "../lib/dashboard/format";
import { LeadTreatmentModal } from "./lead-treatment-modal";

type LeadTableProps = { leads: OperationalLead[]; role: UserRole };

/** Render Brazilian numbers consistently, whether the source includes +55 or not. */
export function formatBrazilianPhone(value: string | null | undefined): string {
  const digits = String(value ?? "").replace(/\D/g, "");
  const national =
    digits.startsWith("55") && [12, 13].includes(digits.length) ? digits.slice(2) : digits;
  if (national.length === 11) {
    return `(${national.slice(0, 2)}) ${national.slice(2, 7)}-${national.slice(7)}`;
  }
  if (national.length === 10) {
    return `(${national.slice(0, 2)}) ${national.slice(2, 6)}-${national.slice(6)}`;
  }
  return national || "Não informado";
}

export function commentCountsAfterSubmission(
  current: Record<string, number>,
  submission: TreatmentSubmission,
): Record<string, number> {
  return { ...current, [submission.leadId]: submission.commentCount };
}

export function applySubmissionToLead(
  lead: OperationalLead,
  submission: TreatmentSubmission,
): OperationalLead {
  if (lead.id !== submission.leadId) return lead;
  return {
    ...lead,
    commercialStatus: submission.commercialStatus,
    isDisqualified: submission.isDisqualified,
    commentCount: submission.commentCount,
    feedbackDueAt: submission.dueAt,
    lastUpdatedAt: submission.lastUpdatedAt,
  };
}

function statusClass(status: OperationalLead["commercialStatus"]): string {
  return `commercial-status ${status}`;
}

export function LeadTable({ leads, role }: LeadTableProps) {
  const [leadOverrides, setLeadOverrides] = useState<Record<string, OperationalLead>>({});
  // Do not read the wall clock during SSR and hydration: the same lead can
  // otherwise receive different SLA classes across those two renders.
  const [hydratedAt, setHydratedAt] = useState<Date | null>(null);
  useEffect(() => setHydratedAt(new Date()), []);
  const onSubmitted = useCallback(
    (submission: TreatmentSubmission) => {
      setLeadOverrides((current) => {
        const original =
          current[submission.leadId] ?? leads.find((lead) => lead.id === submission.leadId);
        if (!original) return current;
        return { ...current, [submission.leadId]: applySubmissionToLead(original, submission) };
      });
    },
    [leads],
  );

  return (
    <section
      className={`table-card lead-table-card lead-table-card--${role}`}
      aria-labelledby="lead-table-title"
    >
      <div className="table-head">
        <div>
          <p className="eyebrow">Dados ao vivo</p>
          <h2 id="lead-table-title">Leads</h2>
        </div>
      </div>
      {leads.length === 0 ? (
        <p className="empty">Nenhum lead disponível.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Nome</th>
              {role === "admin" ? <th>Responsável</th> : null}
              <th>Telefone</th>
              <th>Situação</th>
              <th>Marcador</th>
              <th>Atribuído em</th>
              <th>Última atualização</th>
              <th>Prazo</th>
              <th>Comentários</th>
              <th>Ação</th>
            </tr>
          </thead>
          <tbody>
            {leads.map((lead) => {
              const currentLead = leadOverrides[lead.id] ?? lead;
              const sla = hydratedAt ? getSlaState(currentLead.feedbackDueAt, hydratedAt) : "none";
              return (
                <tr key={lead.id}>
                  <td>
                    <strong>{currentLead.contactName}</strong>
                  </td>
                  {role === "admin" ? <td>{currentLead.sellerName}</td> : null}
                  <td>{formatBrazilianPhone(currentLead.phoneDisplay)}</td>
                  <td>
                    <span className={statusClass(currentLead.commercialStatus)}>
                      {formatCommercialStatus(currentLead.commercialStatus)}
                    </span>
                  </td>
                  <td>
                    {currentLead.isDisqualified ? (
                      <span className="disqualification-marker">
                        {formatDisqualificationMarker(true)}
                      </span>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td>{formatSlaDeadline(currentLead.assignedAt)}</td>
                  <td>{formatSlaDeadline(currentLead.lastUpdatedAt)}</td>
                  <td>
                    <span className={`sla ${sla}`}>
                      {formatSlaDeadline(currentLead.feedbackDueAt)}
                    </span>
                  </td>
                  <td>{formatCommentCount(currentLead.commentCount)}</td>
                  <td>
                    <LeadTreatmentModal
                      lead={currentLead}
                      mode={role === "seller" ? "write" : "read"}
                      onSubmitted={role === "seller" ? onSubmitted : undefined}
                    />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </section>
  );
}
