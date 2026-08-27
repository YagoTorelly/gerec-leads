import type { DashboardData } from "../lib/dashboard/types";
import { deactivateSellerAction, reactivateSellerAction, saveSellerAction } from "../lib/admin/users/actions";

export function UserManagement({
  data,
  notice,
}: {
  data: DashboardData;
  notice?: string;
}) {
  const sellers = data.users.filter((user) => user.role === "seller");

  return (
    <>
      <div className="notice">
        {notice ??
          data.warning ??
          "Gerencie vendedores dentro das quatro posições fixas da fila local."}
      </div>

      <section className="panel-card">
        <div className="panel-head">
          <div>
            <p className="eyebrow">Novo vendedor</p>
            <h2>Criar ou ocupar uma posição livre</h2>
          </div>
        </div>
        <form action={saveSellerAction} className="admin-form">
          <input name="fullName" placeholder="Nome completo" required />
          <input name="email" placeholder="E-mail" required type="email" />
          <input max={4} min={1} name="position" placeholder="Posição" required type="number" />
          <input name="password" placeholder="Senha inicial (opcional)" type="text" />
          <label className="check-row">
            <input defaultChecked name="isActive" type="checkbox" />
            Ativo
          </label>
          <label className="check-row">
            <input name="isPaused" type="checkbox" />
            Iniciar pausado
          </label>
          <button type="submit">Salvar vendedor</button>
        </form>
      </section>

      <section className="panel-card">
        <div className="panel-head">
          <div>
            <p className="eyebrow">Vendedores atuais</p>
            <h2>CRUD operacional</h2>
          </div>
        </div>
        <div className="user-stack">
          {sellers.map((seller) => (
            <article className="user-card" key={seller.userId}>
              <form action={saveSellerAction} className="admin-form compact">
                <input name="userId" type="hidden" value={seller.userId} />
                <input defaultValue={seller.fullName} name="fullName" required />
                <input defaultValue={seller.email} name="email" required type="email" />
                <input
                  defaultValue={seller.queuePosition ?? 1}
                  max={4}
                  min={1}
                  name="position"
                  required
                  type="number"
                />
                <input name="password" placeholder="Nova senha (opcional)" type="text" />
                <label className="check-row">
                  <input defaultChecked={seller.isActive} name="isActive" type="checkbox" />
                  Ativo
                </label>
                <label className="check-row">
                  <input defaultChecked={seller.isPaused} name="isPaused" type="checkbox" />
                  Pausado
                </label>
                <div className="user-card-meta">
                  <span>Leads ativos: {seller.activeLeads}</span>
                  <span>Atrasados: {seller.overdueLeads}</span>
                  <span>Créditos: {seller.skipBalance}</span>
                </div>
                <div className="user-card-actions">
                  <button type="submit">Salvar alterações</button>
                </div>
              </form>
              <div className="user-card-actions split">
                {seller.isActive ? (
                  <form action={deactivateSellerAction}>
                    <input name="userId" type="hidden" value={seller.userId} />
                    <button className="ghost danger" type="submit">
                      Desativar
                    </button>
                  </form>
                ) : (
                  <form action={reactivateSellerAction}>
                    <input name="userId" type="hidden" value={seller.userId} />
                    <button className="ghost" type="submit">
                      Reativar
                    </button>
                  </form>
                )}
              </div>
            </article>
          ))}
        </div>
      </section>
    </>
  );
}
