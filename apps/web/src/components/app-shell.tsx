import { signOutAction } from "../lib/auth/actions";
import type { SessionProfile } from "../lib/dashboard/types";

export function AppShell({
  profile,
  activePath = "/dashboard",
  eyebrow,
  heading = "Visão geral",
  children,
}: {
  profile: SessionProfile;
  activePath?: "/dashboard" | "/fila" | "/historico" | "/usuarios";
  eyebrow?: string;
  heading?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><span className="brand-logo"><img src="/logo-wtg.png" alt="WTG Corretora de Seguros e Benefícios" /></span></div>
        <nav>
          <a className={activePath === "/dashboard" ? "nav-active" : ""} href="/dashboard">
            Visão geral
          </a>
          <a className={activePath === "/fila" ? "nav-active" : ""} href="/fila">
            Fila de leads
          </a>
          <a className={activePath === "/historico" ? "nav-active" : ""} href="/historico">
            Histórico
          </a>
          {profile.role === "admin" ? (
            <a className={activePath === "/usuarios" ? "nav-active" : ""} href="/usuarios">
              Usuários
            </a>
          ) : null}
        </nav>
        <div className="sidebar-foot">
          <span className="status-dot" /> Supabase local
        </div>
      </aside>
      <main className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">
              {eyebrow ?? (profile.role === "admin" ? "Painel administrativo" : "Minha operação")}
            </p>
            <h1>{heading}</h1>
          </div>
          <div className="user-menu">
            <span className="avatar">{profile.fullName.slice(0, 1)}</span>
            <span>
              <strong>{profile.fullName}</strong>
              <small>{profile.role === "admin" ? "Administrador" : "Vendedor"}</small>
            </span>
            <form action={signOutAction}>
              <button className="logout" type="submit">
                Sair
              </button>
            </form>
          </div>
        </header>
        {children}
      </main>
    </div>
  );
}
