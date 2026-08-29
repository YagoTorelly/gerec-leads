"use client";

import { useActionState, useCallback, useEffect, useState } from "react";

import type { CommercialStatus, OperationalLead, Treatment, TreatmentSubmission } from "../lib/api/types";
import { formatCommercialStatus, formatDateTime, formatDisqualificationMarker } from "../lib/dashboard/format";
import {
  initialTreatmentActionState,
  loadLeadTreatmentHistoryAction,
  submitLeadTreatmentAction,
} from "../lib/operations/treatment-actions";

export type TreatmentDraft = {
  comment: string;
  commercialStatus: CommercialStatus;
  isDisqualified: boolean;
};

export function validateTreatmentDraft(draft: TreatmentDraft): { ok: true } | { ok: false; message: string } {
  if (draft.comment.trim().length < 6) {
    return { ok: false, message: "Escreva um comentário com ao menos 6 caracteres." };
  }
  return { ok: true };
}

function historyItem(item: Treatment, index: number) {
  return (
    <li className="treatment-history__item" key={`${item.createdAt}-${index}`}>
      <div>
        <strong>{item.sellerName}</strong>
        <p>{item.comment}</p>
      </div>
      <div className="treatment-history__meta">
        <span>{formatCommercialStatus(item.commercialStatus)}</span>
        {item.isDisqualified ? <span>{formatDisqualificationMarker(true)}</span> : null}
        <small>{formatDateTime(item.createdAt)}</small>
      </div>
    </li>
  );
}

function newIdempotencyKey(): string {
  return globalThis.crypto?.randomUUID?.() ?? `tratativa-${Date.now()}-${Math.random()}`;
}

function TreatmentForm({
  lead,
  onSuccess,
}: {
  lead: OperationalLead;
  onSuccess: (submission: TreatmentSubmission) => void;
}) {
  const [state, formAction, pending] = useActionState(submitLeadTreatmentAction, initialTreatmentActionState);
  const [idempotencyKey] = useState(newIdempotencyKey);

  useEffect(() => {
    if (state.status === "success") onSuccess(state.submission);
  }, [onSuccess, state]);

  return (
    <form action={formAction} className="treatment-form">
      <input type="hidden" name="leadId" value={lead.id} />
      <input type="hidden" name="idempotencyKey" value={idempotencyKey} />
      <label htmlFor={`treatment-comment-${lead.id}`}>
        Comentário
        <textarea
          id={`treatment-comment-${lead.id}`}
          name="comment"
          required
          minLength={6}
          maxLength={2000}
          autoFocus
          placeholder="Descreva o contato ou a evolução da negociação."
        />
      </label>
      <label htmlFor={`treatment-status-${lead.id}`}>
        Situação comercial
        <select id={`treatment-status-${lead.id}`} name="commercialStatus" defaultValue={lead.commercialStatus}>
          <option value="undefined">Indefinido</option>
          <option value="negotiation">Negociação</option>
          <option value="won">Ganho</option>
        </select>
      </label>
      <label className="check-row" htmlFor={`treatment-disqualified-${lead.id}`}>
        <input id={`treatment-disqualified-${lead.id}`} name="isDisqualified" type="checkbox" />
        Marcar como Desqualificado
      </label>
      <p className="muted">Desqualificar exige o comentário registrado nesta tratativa.</p>
      {state.status !== "idle" ? <p className={`form-${state.status}`} role="status" aria-live="polite">{state.message}</p> : null}
      <div className="modal-actions">
        <button type="submit" className="table-action" disabled={pending}>{pending ? "Salvando…" : "Salvar tratativa"}</button>
      </div>
    </form>
  );
}

export function LeadTreatmentModal({
  lead,
  mode,
  treatments: initialTreatments = [],
  defaultOpen = false,
  onSubmitted,
}: {
  lead: OperationalLead;
  mode: "read" | "write";
  treatments?: Treatment[];
  defaultOpen?: boolean;
  onSubmitted?: (submission: TreatmentSubmission) => void;
}) {
  const [open, setOpen] = useState(defaultOpen);
  const [treatments, setTreatments] = useState(initialTreatments);
  const [historyMessage, setHistoryMessage] = useState<string | null>(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const refreshHistory = useCallback(() => {
    setHistoryLoading(true);
    setHistoryMessage(null);
    void loadLeadTreatmentHistoryAction(lead.id).then((result) => {
      setHistoryLoading(false);
      if (result.status === "success") {
        setTreatments(result.items);
      } else {
        setHistoryMessage(result.message);
      }
    });
  }, [lead.id]);
  const openModal = useCallback(() => {
    setOpen(true);
    refreshHistory();
  }, [refreshHistory]);
  const onSuccess = useCallback((submission: TreatmentSubmission) => {
    onSubmitted?.(submission);
    refreshHistory();
  }, [onSubmitted, refreshHistory]);

  const titleId = `lead-treatment-title-${lead.id}`;
  const triggerLabel = mode === "write" ? "Registrar tratativa" : "Ver histórico";

  return (
    <>
      <button type="button" className="table-action" onClick={openModal}>{triggerLabel}</button>
      {open ? (
        <div
          className="modal-backdrop"
          role="presentation"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) setOpen(false);
          }}
        >
          <section className="modal-card treatment-modal" role="dialog" aria-modal="true" aria-labelledby={titleId}>
            <header className="treatment-modal__header">
              <div>
                <p className="eyebrow">Lead</p>
                <h3 id={titleId}>{lead.contactName}</h3>
              </div>
              <button type="button" className="secondary-button" onClick={() => setOpen(false)} aria-label="Fechar janela">Fechar</button>
            </header>

            {mode === "write" ? <TreatmentForm lead={lead} onSuccess={onSuccess} /> : null}

            <section className="treatment-history" aria-label="Histórico de tratativas">
              <h4>Histórico de tratativas</h4>
              {historyLoading ? <p className="muted" aria-live="polite">Carregando histórico…</p> : null}
              {historyMessage ? <p className="form-error" role="status">{historyMessage}</p> : null}
              {!historyLoading && !historyMessage && treatments.length === 0 ? <p className="muted">Nenhuma tratativa registrada.</p> : null}
              {treatments.length > 0 ? <ol>{treatments.map(historyItem)}</ol> : null}
            </section>
          </section>
        </div>
      ) : null}
    </>
  );
}
