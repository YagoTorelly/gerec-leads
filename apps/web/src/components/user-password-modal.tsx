"use client";

import { useEffect, useRef, useState } from "react";

import type { ManagedUser } from "../lib/api/types";
import type { UserMutationResult } from "../lib/users/actions";

import { ConfirmActionModal } from "./confirm-action-modal";

export function UserPasswordModal({ user, onClose, onReset, onSuccess }: {
  user: ManagedUser;
  onClose: () => void;
  onReset: (userId: string, password: string) => Promise<UserMutationResult>;
  onSuccess: (updated: ManagedUser, message: string) => void;
}) {
  const passwordRef = useRef<HTMLInputElement>(null);
  const [password, setPassword] = useState("");
  const [confirming, setConfirming] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const canContinue = Boolean(password.trim() && !pending);

  useEffect(() => {
    passwordRef.current?.focus();
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !pending) onClose();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose, pending]);

  async function resetPassword() {
    setPending(true);
    setError(null);
    const result = await onReset(user.id, password);
    setPending(false);
    if (result.status === "success") {
      setPassword("");
      onSuccess(result.user, result.message);
    } else {
      setConfirming(false);
      setError(result.message);
    }
  }

  return <>
    {!confirming ? <div className="modal-backdrop" role="presentation" onMouseDown={(event) => {
      if (event.target === event.currentTarget && !pending) onClose();
    }}>
      <section className="modal-card" role="dialog" aria-modal="true" aria-labelledby="reset-password-title">
        <h3 id="reset-password-title">Redefinir senha</h3>
        <p className="muted">Defina a nova senha de {user.fullName}. As sessões atuais desse usuário serão encerradas.</p>
        <label htmlFor="reset-user-password">Nova senha
          <input ref={passwordRef} id="reset-user-password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="new-password" required />
        </label>
        {error ? <p className="form-error" role="status">{error}</p> : null}
        <div className="modal-actions">
          <button type="button" className="secondary-button" disabled={pending} onClick={onClose}>Cancelar</button>
          <button type="button" className="table-action" disabled={!canContinue} onClick={() => setConfirming(true)}>Salvar nova senha</button>
        </div>
      </section>
    </div> : <ConfirmActionModal
      title="Confirmar redefinição de senha"
      description={`Salvar a nova senha de ${user.fullName} e encerrar as sessões atuais?`}
      confirmLabel="Confirmar redefinição"
      pending={pending}
      onConfirm={() => void resetPassword()}
      onCancel={() => setConfirming(false)}
    />}
  </>;
}
