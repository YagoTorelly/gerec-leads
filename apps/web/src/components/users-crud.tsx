"use client";
import { useState } from "react";
type User = { id: number; name: string; email: string; position: number; active: boolean };
export function UsersCrud() {
  const [users, setUsers] = useState<User[]>([
    { id: 1, name: "Renato", email: "renato@gerec.local", position: 1, active: true },
    { id: 2, name: "Sandra", email: "sandra@gerec.local", position: 2, active: true },
    { id: 3, name: "Jessica", email: "jessica@gerec.local", position: 3, active: true },
    { id: 4, name: "Nelma", email: "nelma@gerec.local", position: 4, active: true },
  ]);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const add = () => {
    if (!name.trim() || !email.trim()) return;
    setUsers((current) => [
      ...current,
      {
        id: Date.now(),
        name: name.trim(),
        email: email.trim(),
        position: current.length + 1,
        active: true,
      },
    ]);
    setName("");
    setEmail("");
  };
  return (
    <section className="users-layout">
      <div className="table-card">
        <div className="table-head">
          <div>
            <p className="eyebrow">Vendedores</p>
            <h2>Contas cadastradas</h2>
          </div>
          <span className="data-badge supabase">4 ativos</span>
        </div>
        <table>
          <thead>
            <tr>
              <th>Nome</th>
              <th>E-mail</th>
              <th>Fila</th>
              <th>Status</th>
              <th>Ação</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id}>
                <td>
                  <strong>{user.name}</strong>
                </td>
                <td>{user.email}</td>
                <td>Posição {user.position}</td>
                <td>
                  <span className={`pill ${user.active ? "won" : "disqualified"}`}>
                    {user.active ? "Ativo" : "Inativo"}
                  </span>
                </td>
                <td>
                  <button
                    className="table-action"
                    onClick={() =>
                      setUsers((current) =>
                        current.map((item) =>
                          item.id === user.id ? { ...item, active: !item.active } : item,
                        ),
                      )
                    }
                  >
                    {user.active ? "Desativar" : "Ativar"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <form
        className="add-user-card"
        onSubmit={(event) => {
          event.preventDefault();
          add();
        }}
      >
        <p className="eyebrow">Novo vendedor</p>
        <h2>Criar acesso</h2>
        <input
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="Nome completo"
        />
        <input
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="e-mail@gerec.local"
          type="email"
        />
        <button type="submit">Adicionar vendedor</button>
        <small>A senha será definida pelo bootstrap local.</small>
      </form>
    </section>
  );
}
