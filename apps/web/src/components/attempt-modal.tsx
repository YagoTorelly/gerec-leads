"use client";
import { useState } from "react";
import { registerContactAttemptAction } from "../lib/operations/actions";
import type { CommercialStatus } from "../lib/dashboard/types";

export function AttemptModal({ leadId, contactName, attempts, status }: { leadId: number; contactName: string; attempts: number; status: CommercialStatus }) {
  const [open, setOpen] = useState(false);
  return <>
    <button type="button" className="table-action" onClick={() => setOpen(true)}>Comentário</button>
    {open ? <div className="modal-backdrop" role="presentation" onClick={() => setOpen(false)}>
      <div className="modal-card" role="dialog" aria-modal="true" aria-labelledby={`attempt-${leadId}`} onClick={(event) => event.stopPropagation()}>
        <h3 id={`attempt-${leadId}`}>Registrar contato · {contactName}</h3>
        <form action={registerContactAttemptAction} onSubmit={() => setOpen(false)}>
          <input type="hidden" name="leadId" value={leadId} />
          <label>Status comercial<select name="commercialStatus" defaultValue={status}>
            <option value="undefined">Indefinido</option><option value="negotiation">Negociação</option><option value="won">Ganho</option><option value="disqualified">Desqualificado</option>
          </select></label>
          <label>Comentário<textarea name="comment" required minLength={6} autoFocus placeholder="Descreva o contato realizado..." /></label>
          <div className="modal-actions"><button type="button" className="secondary-button" onClick={() => setOpen(false)}>Cancelar</button><button type="submit" className="table-action">Registrar tentativa</button></div>
        </form>
      </div>
    </div> : null}
  </>;
}
