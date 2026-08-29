"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";

import type { ManagedUser } from "../lib/api/types";
import {
  createManagedUserAction,
  resetManagedUserPasswordAction,
  setManagedUserAvailabilityAction,
} from "../lib/users/actions";

import { ConfirmActionModal } from "./confirm-action-modal";
import { UserFormModal } from "./user-form-modal";
import { UserPasswordModal } from "./user-password-modal";

type AvailabilityConfirmation = { user: ManagedUser; paused: boolean };

function roleLabel(role: ManagedUser["role"]): string {
  return role === "admin" ? "Administrador" : "Vendedor";
}

function availabilityLabel(user: ManagedUser): string {
  if (!user.active) return "Inativo";
  return user.role === "seller" && user.paused ? "Pausado" : "Ativo";
}

function replaceUser(users: ManagedUser[], updated: ManagedUser): ManagedUser[] {
  return users.map((user) => (user.id === updated.id ? updated : user));
}

export function UserManagement({ users: initialUsers, page = 1 }: { users: ManagedUser[]; page?: number }) {
  const router = useRouter();
  const [users, setUsers] = useState(initialUsers);
  const [newUserOpen, setNewUserOpen] = useState(false);
  const [passwordUser, setPasswordUser] = useState<ManagedUser | null>(null);
  const [availabilityConfirmation, setAvailabilityConfirmation] = useState<AvailabilityConfirmation | null>(null);
  const [pendingAvailability, setPendingAvailability] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const newUserTrigger = useRef<HTMLButtonElement>(null);

  function closeNewUser() {
    setNewUserOpen(false);
    newUserTrigger.current?.focus();
  }

  async function confirmAvailability() {
    if (!availabilityConfirmation) return;
    setPendingAvailability(true);
    try {
      const result = await setManagedUserAvailabilityAction(
        availabilityConfirmation.user.id,
        availabilityConfirmation.paused,
      );
      if (result.status === "success") setUsers((current) => replaceUser(current, result.user));
      setNotice(result.message);
    } catch {
      setNotice("Não foi possível concluir a ação. Tente novamente.");
    } finally {
      setPendingAvailability(false);
      setAvailabilityConfirmation(null);
    }
  }

  return (
    <section className="panel-card" aria-labelledby="user-management-title">
      <div className="panel-head">
        <div>
          <p className="eyebrow">Administração</p>
          <h2 id="user-management-title">Usuários</h2>
          <p className="muted">Crie acessos, pause vendedores e redefina senhas com confirmação.</p>
        </div>
        <button ref={newUserTrigger} type="button" className="table-action" onClick={() => setNewUserOpen(true)}>Novo usuário</button>
      </div>
      {notice ? <p className="form-success" role="status" aria-live="polite">{notice}</p> : null}
      <div className="user-list">
        {users.map((user) => {
          const paused = user.role === "seller" && user.paused === true;
          const availabilityAction = paused ? "Ativar" : "Pausar";
          return (
            <article className="user-card" key={user.id}>
              <div>
                <strong>{user.fullName}</strong>
                <div className="user-card-meta">
                  <span>{user.email}</span>
                  <span className={`pill ${paused ? "disqualified" : "won"}`}>{availabilityLabel(user)}</span>
                  <span>{roleLabel(user.role)}</span>
                </div>
              </div>
              <div className="user-card-actions">
                {user.role === "seller" && user.active ? <button
                  type="button"
                  className="secondary-button"
                  aria-label={`${availabilityAction} ${user.fullName}`}
                  onClick={() => setAvailabilityConfirmation({ user, paused: !paused })}
                >{availabilityAction}</button> : null}
                <button type="button" className="secondary-button" aria-label={`Redefinir senha de ${user.fullName}`} onClick={() => setPasswordUser(user)}>Redefinir senha</button>
              </div>
            </article>
          );
        })}
      </div>
      {newUserOpen ? <UserFormModal
        onClose={closeNewUser}
        onSubmit={createManagedUserAction}
        onCreated={(user, message) => {
          setNotice(message);
          closeNewUser();
          if (page > 1) {
            router.push("/usuarios");
            return;
          }
          setUsers((current) => [...current, user]);
        }}
      /> : null}
      {passwordUser ? <UserPasswordModal
        user={passwordUser}
        onClose={() => setPasswordUser(null)}
        onReset={resetManagedUserPasswordAction}
        onSuccess={(updated, message) => {
          setUsers((current) => replaceUser(current, updated));
          setNotice(message);
          setPasswordUser(null);
        }}
      /> : null}
      {availabilityConfirmation ? <ConfirmActionModal
        title={availabilityConfirmation.paused ? "Confirmar pausa" : "Confirmar ativação"}
        description={availabilityConfirmation.paused
          ? `Pausar ${availabilityConfirmation.user.fullName} para novas atribuições? Os leads atuais permanecem com o vendedor.`
          : `Ativar ${availabilityConfirmation.user.fullName} para voltar a receber novas atribuições.`}
        confirmLabel={availabilityConfirmation.paused ? "Confirmar pausa" : "Confirmar ativação"}
        pending={pendingAvailability}
        onConfirm={() => void confirmAvailability()}
        onCancel={() => setAvailabilityConfirmation(null)}
      /> : null}
    </section>
  );
}
