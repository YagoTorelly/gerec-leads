export function AdminControls() {
  return (
    <div className="admin-controls" aria-describedby="admin-actions-unavailable">
      <div className="admin-actions">
        <button type="button" disabled>Simular entrada de leads</button>
        <button className="ghost danger" type="button" disabled>Arquivar lead</button>
      </div>
      <p className="muted" id="admin-actions-unavailable">Ações administrativas indisponíveis até a API Python expor os comandos correspondentes.</p>
    </div>
  );
}
