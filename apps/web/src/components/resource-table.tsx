import { registerContactAttemptAction } from "../lib/operations/actions";

export function ResourceTable({
  title,
  items,
  allowAttempts = false,
}: {
  title: string;
  items: Record<string, unknown>[];
  allowAttempts?: boolean;
}) {
  const labels: Record<string, string> = { contactName: "Nome", phoneNormalized: "Telefone", email: "E-mail", document: "CNPJ/MEI", sellerId: "Vendedor", position: "Posição", paused: "Status", leadId: "Lead", type: "Tipo", startedAt: "Início" };
  const format = (key: string, value: unknown) => {
    if (value === null || value === undefined || value === "") return "—";
    if (key === "phoneNormalized") return String(value).replace(/(\d{2})(\d{5})(\d{4})/, "($1) $2-$3");
    if (key === "paused") return value ? "Pausado" : "Ativo";
    if (key.endsWith("At") || key.endsWith("Date")) return new Date(String(value)).toLocaleString("pt-BR");
    return String(value);
  };
  return (
    <section className="table-card">
      <div className="table-head">
        <div>
          <p className="eyebrow">Dados ao vivo</p>
          <h2>{title}</h2>
        </div>
      </div>
      {items.length === 0 ? (
        <p className="empty">Nenhum registro disponível.</p>
      ) : (
        <table>
          <thead>
            <tr>
              {Object.keys(items[0])
                .slice(0, 6)
                .map((key) => (
                  <th key={key}>{labels[key] ?? key}</th>
                ))}
              {allowAttempts ? <th>Ação</th> : null}
            </tr>
          </thead>
          <tbody>
            {items.map((item, index) => (
              <tr key={String(item.id ?? index)}>
                {Object.keys(items[0])
                  .slice(0, 6)
                  .map((key) => (
                    <td key={key}>{format(key, item[key])}</td>
                  ))}
                {allowAttempts ? (
                  <td>
                    <form action={registerContactAttemptAction} className="attempt-form">
                      <input type="hidden" name="leadId" value={String(item.id ?? "")} />
                      <input name="comment" required minLength={6} placeholder="Comentário" />
                      <button type="submit">Registrar tentativa</button>
                    </form>
                  </td>
                ) : null}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
