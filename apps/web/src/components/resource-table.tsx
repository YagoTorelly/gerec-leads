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
                  <th key={key}>{key}</th>
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
                    <td key={key}>{String(item[key] ?? "—")}</td>
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
