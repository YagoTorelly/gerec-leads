"use client";

import { useState } from "react";

function filenameFromResponse(response: Response): string {
  const header = response.headers.get("content-disposition") ?? "";
  const match = header.match(/filename="?([^";]+)"?/i);
  return match?.[1] ?? "leads.xlsx";
}

export function ExportLeadsButton() {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function download() {
    if (pending) return;
    setPending(true);
    setError(null);
    try {
      const response = await fetch("/exportacoes/download", { credentials: "same-origin" });
      if (!response.ok) throw new Error("download_failed");
      const objectUrl = URL.createObjectURL(await response.blob());
      const anchor = document.createElement("a");
      anchor.href = objectUrl;
      anchor.download = filenameFromResponse(response);
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(objectUrl);
    } catch {
      setError("Não foi possível exportar os leads. Tente novamente.");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="exportations-download-wrap">
      <button
        type="button"
        className="table-action exportations-download"
        onClick={download}
        disabled={pending}
        aria-busy={pending}
      >
        {pending ? "Processando exportação" : "Exportar leads em Excel"}
      </button>
      {pending ? (
        <div className="exportations-progress" role="progressbar" aria-label="Processando exportação">
          <span />
        </div>
      ) : null}
      {error ? <p className="form-error exportations-download-error" role="alert">{error}</p> : null}
    </div>
  );
}
