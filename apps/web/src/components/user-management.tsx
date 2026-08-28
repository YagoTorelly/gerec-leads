import {
  deactivateSellerAction,
  reactivateSellerAction,
  saveSellerAction,
} from "../lib/admin/actions";

export function UserManagement({ users }: { users: Record<string, unknown>[] }) {
  return (
    <section className="panel-card">
      <div className="panel-head">
        <div>
          <p className="eyebrow">Administração</p>
          <h2>Usuários</h2>
        </div>
      </div>
      <form action={saveSellerAction} className="admin-form">
        <input name="fullName" placeholder="Nome completo" required />
        <input name="email" type="email" placeholder="E-mail" required />
        <button type="submit">Salvar usuário</button>
      </form>
      {users.map((user, index) => (
        <article className="user-card" key={String(user.id ?? index)}>
          <strong>{String(user.email ?? user.id ?? "Usuário")}</strong>
          <div className="user-card-actions">
            <form action={deactivateSellerAction}>
              <input type="hidden" name="userId" value={String(user.id ?? "")} />
              <button type="submit">Desativar</button>
            </form>
            <form action={reactivateSellerAction}>
              <input type="hidden" name="userId" value={String(user.id ?? "")} />
              <button type="submit">Reativar</button>
            </form>
          </div>
        </article>
      ))}
    </section>
  );
}
