import Image from "next/image";
import Link from "next/link";

import { signOutAction } from "../lib/auth/actions";
import type { SessionProfile } from "../lib/auth/session";

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
  const isAdmin = profile.role === "admin";

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-logo">
            <Image
              src="/logo-wtg.png"
              alt="WTG Corretora de Seguros e Benefícios"
              width={343}
              height={343}
              priority
            />
          </span>
        </div>
        <nav aria-label="Navegação principal">
          <Link prefetch className={activePath === "/dashboard" ? "nav-active" : ""} href="/dashboard">
            {isAdmin ? "Visão geral" : "Minha operação"}
          </Link>
          {isAdmin ? (
            <>
              <Link prefetch className={activePath === "/fila" ? "nav-active" : ""} href="/fila">
                Fila de leads
              </Link>
              <Link prefetch className={activePath === "/historico" ? "nav-active" : ""} href="/historico">
                Histórico
              </Link>
              <Link prefetch className={activePath === "/usuarios" ? "nav-active" : ""} href="/usuarios">
                Usuários
              </Link>
            </>
          ) : (
            <>
              <Link prefetch className={activePath === "/fila" ? "nav-active" : ""} href="/fila">
                Minha fila
              </Link>
              <Link prefetch className={activePath === "/historico" ? "nav-active" : ""} href="/historico">
                Minhas tratativas
              </Link>
            </>
          )}
        </nav>
        <div className="sidebar-foot">
          <span className="status-dot" />
          Sistema conectado
        </div>
      </aside>
      <main className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">
              {eyebrow ?? (isAdmin ? "Painel administrativo" : "Minha operação")}
            </p>
            <h1>{heading}</h1>
          </div>
          <div className="user-menu">
            <span className="avatar" aria-hidden="true">
              {profile.fullName.slice(0, 1)}
            </span>
            <span>
              <strong>{profile.fullName}</strong>
              <small>{isAdmin ? "Administrador" : "Vendedor"}</small>
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
