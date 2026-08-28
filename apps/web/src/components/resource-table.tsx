export function ResourceTable({ title, items }: { title: string; items: Record<string, unknown>[] }) {
  return (
    <section className="table-card">
      <div className="table-head"><div><p className="eyebrow">Dados ao vivo</p><h2>{title}</h2></div></div>
      {items.length === 0 ? <p className="empty">Nenhum registro disponível.</p> : (
        <table><thead><tr>{Object.keys(items[0]).slice(0, 6).map((key) => <th key={key}>{key}</th>)}</tr></thead>
          <tbody>{items.map((item, index) => <tr key={String(item.id ?? index)}>{Object.keys(items[0]).slice(0, 6).map((key) => <td key={key}>{String(item[key] ?? "—")}</td>)}</tr>)}</tbody>
        </table>
      )}
    </section>
  );
}
