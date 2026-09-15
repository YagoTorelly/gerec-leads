"use client";

import { useCallback, useState } from "react";

import type { ManagedUser, OperationalLead, TreatmentSubmission, UserRole } from "../lib/api/types";
import {
  formatCommentCount,
  formatCommercialStatus,
  formatDateTime,
  formatDisqualificationMarker,
} from "../lib/dashboard/format";
import { LeadContactModal } from "./lead-contact-modal";
import { LeadTreatmentModal } from "./lead-treatment-modal";
import { LeadTransferModal } from "./lead-transfer-modal";

type LeadTableProps = { leads: OperationalLead[]; role: UserRole; transferTargets?: ManagedUser[] };

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
    lastUpdatedAt: submission.lastUpdatedAt,
  };
}

function statusClass(status: OperationalLead["commercialStatus"]): string {
  return `commercial-status ${status}`;
}

export function LeadTable({ leads, role, transferTargets = [] }: LeadTableProps) {
  const [leadOverrides, setLeadOverrides] = useState<Record<string, OperationalLead>>({});
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
              <th>Contato</th>
              <th>Situação</th>
              <th>Marcador</th>
              <th>Atribuído em</th>
              <th>Última atualização</th>
              <th>Comentários</th>
              <th>Ação</th>
            </tr>
          </thead>
          <tbody>
            {leads.map((lead) => {
              const currentLead = leadOverrides[lead.id] ?? lead;
              return (
                <tr
                  key={lead.id}
                  className={currentLead.commentCount === 0 ? "lead-row--awaiting-treatment" : undefined}
                >
                  <td>
                    <strong>{currentLead.contactName}</strong>
                  </td>
                  {role === "admin" ? <td>{currentLead.sellerName}</td> : null}
                  <td><LeadContactModal lead={currentLead} /></td>
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
                  <td>{formatDateTime(currentLead.assignedAt)}</td>
                  <td>{formatDateTime(currentLead.lastUpdatedAt)}</td>
                  <td>{formatCommentCount(currentLead.commentCount)}</td>
                  <td>
                    <div className="lead-actions">
                      <LeadTreatmentModal
                        lead={currentLead}
                        mode={role === "seller" ? "write" : "read"}
                        onSubmitted={role === "seller" ? onSubmitted : undefined}
                      />
                      {role === "admin" ? (
                        <LeadTransferModal
                          lead={currentLead}
                          targets={transferTargets}
                          onSuccess={(sellerName) => {
                            setLeadOverrides((current) => ({
                              ...current,
                              [currentLead.id]: { ...currentLead, sellerName },
                            }));
                          }}
                        />
                      ) : null}
                    </div>
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
