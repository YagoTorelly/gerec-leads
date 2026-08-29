"use client";

import { useEffect, useRef, useState } from "react";

import type { CreateManagedUserInput, ManagedUser, UserRole } from "../lib/api/types";
import type { UserMutationResult } from "../lib/users/actions";

export function UserFormModal({ onClose, onCreated, onSubmit }: {
  onClose: () => void;
  onCreated: (user: ManagedUser, message: string) => void;
  onSubmit: (input: CreateManagedUserInput) => Promise<UserMutationResult>;
}) {
  const initialInput = useRef<HTMLInputElement>(null);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<UserRole>("seller");
  const [password, setPassword] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const canSubmit = Boolean(fullName.trim() && email.trim() && password.trim() && !pending);

  useEffect(() => {
    initialInput.current?.focus();
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !pending) onClose();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose, pending]);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmit) return;
    setPending(true);
    setError(null);
    try {
      const result = await onSubmit({ fullName: fullName.trim(), email: email.trim(), role, password });
      if (result.status === "success") {
        setPassword("");
        onCreated(result.user, result.message);
      } else setError(result.message);
    } catch {
      setError("Não foi possível concluir a ação. Tente novamente.");
    } finally {
      setPending(false);
    }
  }

  return <div className="modal-backdrop" role="presentation" onMouseDown={(event) => {
    if (event.target === event.currentTarget && !pending) onClose();
  }}>
    <section className="modal-card" role="dialog" aria-modal="true" aria-labelledby="new-user-title">
      <h3 id="new-user-title">Novo usuário</h3>
      <form onSubmit={submit}>
        <label htmlFor="new-user-name">Nome completo
          <input ref={initialInput} id="new-user-name" value={fullName} onChange={(event) => setFullName(event.target.value)} autoComplete="name" required />
        </label>
        <label htmlFor="new-user-email">E-mail
          <input id="new-user-email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" required />
        </label>
        <label htmlFor="new-user-role">Papel
          <select id="new-user-role" value={role} onChange={(event) => setRole(event.target.value as UserRole)}>
            <option value="seller">Vendedor</option>
            <option value="admin">Administrador</option>
          </select>
        </label>
        <label htmlFor="new-user-password">Senha inicial
          <input id="new-user-password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="new-password" required />
        </label>
        {error ? <p className="form-error" role="status">{error}</p> : null}
        <div className="modal-actions">
          <button type="button" className="secondary-button" disabled={pending} onClick={onClose}>Cancelar</button>
          <button type="submit" className="table-action" disabled={!canSubmit}>{pending ? "Criando…" : "Criar usuário"}</button>
        </div>
      </form>
    </section>
  </div>;
}
