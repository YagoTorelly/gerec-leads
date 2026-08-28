import { registerContactAttemptAction } from "../lib/operations/actions";

const labels: Record<string, string> = { contactName: "Nome", phoneNormalized: "Telefone", email: "E-mail", sellerName: "Vendedor", position: "Posição", paused: "Status", leadName: "Lead", companyName: "Empresa", campaignName: "Campanha", type: "Tipo", startedAt: "Início", assignmentStatus: "Situação" };
function display(key: string, value: unknown) {
  if (value == null || value === "") return "—";
  if (key === "phoneNormalized") { const digits = String(value).replace(/\D/g, "").replace(/^55(?=\d{10,11}$)/, ""); return digits.length === 11 ? `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7)}` : digits; }
  if (key === "paused") return value ? "Pausado" : "Ativo";
  if (key.endsWith("At") || key.endsWith("Date")) { const date = new Date(String(value)); return Number.isNaN(date.getTime()) ? "—" : date.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" }); }
  return String(value);
}
export function ResourceTable({ title, items, allowAttempts = false }: { title: string; items: Record<string, unknown>[]; allowAttempts?: boolean }) {
  const columns = title === "Fila" ? ["sellerName", "paused", "position"] : title.includes("Atrib") ? ["leadName", "sellerName", "type", "startedAt"] : ["contactName", "sellerName", "companyName", "campaignName", "phoneNormalized", "email", "assignmentStatus"];
  return <section className="table-card"><div className="table-head"><div><p className="eyebrow">Dados ao vivo</p><h2>{title}</h2></div></div>{items.length === 0 ? <p className="empty">Nenhum registro disponível.</p> : <table><thead><tr>{columns.map((key) => <th key={key}>{labels[key] ?? key}</th>)}{allowAttempts && <th>Ação</th>}</tr></thead><tbody>{items.map((item, index) => <tr key={String(item.id ?? index)}>{columns.map((key) => <td key={key}>{display(key, item[key])}</td>)}{allowAttempts && <td><form action={registerContactAttemptAction} className="attempt-form"><input type="hidden" name="leadId" value={String(item.id ?? "")} /><input name="comment" required minLength={6} placeholder="Comentário" /><button type="submit">Registrar tentativa</button></form></td>}</tr>)}</tbody></table>}</section>;
}
