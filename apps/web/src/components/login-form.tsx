"use client";

import { useActionState } from "react";
import { loginAction, type LoginState } from "../lib/auth/actions";

const initialState: LoginState = {};

export function LoginForm() {
  const [state, action, pending] = useActionState(loginAction, initialState);
  return (
    <main className="login-shell">
      <form className="login-card" action={action}>
        <span className="login-logo"><img src="/logo-wtg.png" alt="WTG Corretora" /></span>
        <p className="eyebrow">WTG · operação comercial</p>
        <h1>
          Gerenciador
          <br />
          de Leads
        </h1>
        <p className="login-copy">Entre para acompanhar sua fila, prazos e resultados.</p>
        <label>
          E-mail
          <input name="email" type="email" placeholder="voce@gerec.local" required />
        </label>
        <label>
          Senha
          <input name="password" type="password" required />
        </label>
        {state.error && (
          <p className="form-error" role="alert">
            {state.error}
          </p>
        )}
        <button type="submit" disabled={pending}>
          {pending ? "Entrando…" : "Entrar no sistema"}
        </button>
        <small>Ambiente local · America/Sao_Paulo</small>
      </form>
    </main>
  );
}
