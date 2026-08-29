import type { Treatment } from "../lib/api/types";
import {
  formatCommercialStatus,
  formatDateTime,
  formatDisqualificationMarker,
  formatText,
} from "../lib/dashboard/format";

export function TreatmentHistoryTable({ treatments }: { treatments: Treatment[] }) {
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
      {treatments.length === 0 ? (
        <p className="empty">Nenhuma tratativa registrada.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Lead</th>
              <th>Vendedor</th>
              <th>Comentário</th>
              <th>Situação</th>
              <th>Marcador</th>
              <th>Data</th>
            </tr>
          </thead>
          <tbody>
            {treatments.map((treatment, index) => (
              <tr key={`${treatment.createdAt}-${index}`}>
                <td>
                  <strong>{formatText(treatment.leadName)}</strong>
                </td>
                <td>{formatText(treatment.sellerName)}</td>
                <td>{formatText(treatment.comment)}</td>
                <td>
                  <span className={`commercial-status ${treatment.commercialStatus}`}>
                    {formatCommercialStatus(treatment.commercialStatus)}
                  </span>
                </td>
                <td>
                  {treatment.isDisqualified ? (
                    <span className="disqualification-marker">
                      {formatDisqualificationMarker(true)}
                    </span>
                  ) : (
                    "—"
                  )}
                </td>
                <td>{formatDateTime(treatment.createdAt)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
