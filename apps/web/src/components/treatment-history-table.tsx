import type { Treatment } from "../lib/api/types";
import {
  formatCommercialStatus,
  formatDateTime,
  formatDisqualificationMarker,
  formatText,
} from "../lib/dashboard/format";

type LeadConversation = {
  leadId: string;
  leadName: string;
  sellerName: string;
  assignedAt: string | null;
  lastUpdatedAt: string | null;
  items: Treatment[];
};

export function groupTreatmentsByLead(treatments: Treatment[]): LeadConversation[] {
  const groups = new Map<string, LeadConversation>();
  for (const treatment of treatments) {
    const current = groups.get(treatment.leadId);
    if (current) {
      current.items.push(treatment);
      current.lastUpdatedAt = treatment.lastUpdatedAt ?? current.lastUpdatedAt;
      continue;
    }
    groups.set(treatment.leadId, {
      leadId: treatment.leadId,
      leadName: formatText(treatment.leadName),
      sellerName: formatText(treatment.sellerName),
      assignedAt: treatment.assignedAt,
      lastUpdatedAt: treatment.lastUpdatedAt,
      items: [treatment],
    });
  }
  return Array.from(groups.values());
}

export function TreatmentHistoryTable({ treatments }: { treatments: Treatment[] }) {
  const conversations = groupTreatmentsByLead(treatments);
  return (
    <section
      className="table-card treatment-history-table"
      aria-labelledby="treatment-history-title"
    >
      <div className="table-head">
        <div>
          <p className="eyebrow">Dados ao vivo</p>
          <h2 id="treatment-history-title">Tratativas</h2>
        </div>
      </div>
      {conversations.length === 0 ? (
        <p className="empty">Nenhuma tratativa registrada.</p>
      ) : (
        <div className="treatment-conversations">
          {conversations.map((conversation) => (
            <article className="treatment-conversation-card" key={conversation.leadId}>
              <header className="treatment-conversation-card__header">
                <div>
                  <p className="eyebrow">Lead</p>
                  <h3>{conversation.leadName}</h3>
                </div>
                <dl className="treatment-conversation-card__meta">
                  <div>
                    <dt>Vendedor</dt>
                    <dd>{conversation.sellerName}</dd>
                  </div>
                  <div>
                    <dt>Início</dt>
                    <dd>{formatDateTime(conversation.assignedAt)}</dd>
                  </div>
                  <div>
                    <dt>Última atualização</dt>
                    <dd>{formatDateTime(conversation.lastUpdatedAt)}</dd>
                  </div>
                </dl>
              </header>
              <ol className="treatment-history">
                {conversation.items.map((treatment, index) => (
                  <li className="treatment-history__item" key={`${treatment.createdAt}-${index}`}>
                    <div>
                      <strong>{formatDateTime(treatment.createdAt)}</strong>
                      <p>{formatText(treatment.comment)}</p>
                    </div>
                    <div className="treatment-history__meta">
                      <span className={`commercial-status ${treatment.commercialStatus}`}>
                        {formatCommercialStatus(treatment.commercialStatus)}
                      </span>
                      {treatment.isDisqualified ? (
                        <span className="disqualification-marker">
                          {formatDisqualificationMarker(true)}
                        </span>
                      ) : null}
                    </div>
                  </li>
                ))}
              </ol>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
