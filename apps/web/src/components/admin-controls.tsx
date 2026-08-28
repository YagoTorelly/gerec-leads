import { archiveLeadAction, simulateLeadsAction } from "../lib/admin/actions";

export function AdminControls({ leadId }: { leadId?: string }) {
  return (
    <div className="admin-controls">
      <form action={simulateLeadsAction}>
        <button type="submit">Simular entrada de leads</button>
      </form>
      {leadId ? (
        <form action={archiveLeadAction}>
          <input type="hidden" name="leadId" value={leadId} />
          <button className="ghost danger" type="submit">
            Arquivar lead
          </button>
        </form>
      ) : null}
      <p className="muted">
        Ações administrativas aguardam os comandos correspondentes da API Python.
      </p>
    </div>
  );
}
