export function AdminControls() {
  return (
    <div className="admin-controls" aria-describedby="admin-actions-unavailable">
      <button type="button" disabled>
        Simular entrada de leads
      </button>
      <button className="ghost danger" type="button" disabled>
        Arquivar lead
      </button>
      <p className="muted" id="admin-actions-unavailable">
        Ações administrativas indisponíveis até a API Python expor os comandos correspondentes.
      </p>
    </div>
  );
}
