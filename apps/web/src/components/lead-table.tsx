"use client";

import { useCallback, useState } from "react";

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

export function commentCountsAfterSubmission(
  current: Record<string, number>,
  submission: TreatmentSubmission,
): Record<string, number> {
  return { ...current, [submission.leadId]: submission.commentCount };
}

function statusClass(status: OperationalLead["commercialStatus"]): string {
  return `commercial-status ${status}`;
}

export function LeadTable({ leads, role }: LeadTableProps) {
  const [commentCounts, setCommentCounts] = useState<Record<string, number>>({});
  const onSubmitted = useCallback((submission: TreatmentSubmission) => {
    setCommentCounts((current) => commentCountsAfterSubmission(current, submission));
  }, []);

  return (
    <section className="table-card lead-table-card" aria-labelledby="lead-table-title">
      <div className="table-head"><div><p className="eyebrow">Dados ao vivo</p><h2 id="lead-table-title">Leads</h2></div></div>
      {leads.length === 0 ? <p className="empty">Nenhum lead disponível.</p> : (
        <table>
          <thead>
            <tr>
              <th>Nome</th>
              {role === "admin" ? <th>Responsável</th> : null}
              <th>Empresa</th>
              <th>Campanha</th>
              <th>Telefone</th>
              <th>E-mail</th>
              <th>Situação</th>
              <th>Marcador</th>
              <th>Prazo</th>
              <th>Comentários</th>
              <th>Ação</th>
            </tr>
          </thead>
          <tbody>
            {leads.map((lead) => {
              const commentCount = commentCounts[lead.id] ?? lead.commentCount;
              const sla = getSlaState(lead.feedbackDueAt);
              return (
                <tr key={lead.id}>
                  <td><strong>{lead.contactName}</strong></td>
                  {role === "admin" ? <td>{lead.sellerName}</td> : null}
                  <td>{lead.companyName}</td>
                  <td>{lead.campaignName}</td>
                  <td>{lead.phoneDisplay}</td>
                  <td>{lead.email}</td>
                  <td><span className={statusClass(lead.commercialStatus)}>{formatCommercialStatus(lead.commercialStatus)}</span></td>
                  <td>{lead.isDisqualified ? <span className="disqualification-marker">{formatDisqualificationMarker(true)}</span> : "—"}</td>
                  <td><span className={`sla ${sla}`}>{formatSlaDeadline(lead.feedbackDueAt)}</span></td>
                  <td>{formatCommentCount(commentCount)}</td>
                  <td><LeadTreatmentModal lead={lead} mode={role === "seller" ? "write" : "read"} onSubmitted={role === "seller" ? onSubmitted : undefined} /></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </section>
  );
}
