export default function Loading() {
  return (
    <main className="route-loading" aria-live="polite" aria-busy="true">
      <div className="route-loading__bar" />
      <p>Carregando dados da operação…</p>
    </main>
  );
}
