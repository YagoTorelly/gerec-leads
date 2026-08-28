export function UserManagement({ users }: { users: Record<string, unknown>[] }) {
  return (
    <section className="panel-card" aria-describedby="user-management-unavailable">
      <div className="panel-head">
        <div>
          <p className="eyebrow">Administração</p>
          <h2>Usuários</h2>
        </div>
      </div>
      <p className="muted" id="user-management-unavailable">
        Gestão de usuários indisponível até a API Python expor os comandos correspondentes.
      </p>
      {users.map((user, index) => (
        <article className="user-card" key={String(user.id ?? index)}>
          <strong>{String(user.fullName ?? user.email ?? user.id ?? "Usuário")}</strong>
          <div className="user-card-meta"><span>{String(user.email ?? "")}</span><span className={`pill ${user.active === false ? "disqualified" : "won"}`}>{user.active === false ? "Inativo" : "Ativo"}</span><span>{user.role === "admin" ? "Administrador" : "Vendedor"}</span></div>
          <div className="user-card-actions">
            <button type="button" disabled>
              Desativar
            </button>
            <button type="button" disabled>
              Reativar
            </button>
          </div>
        </article>
      ))}
    </section>
  );
}
