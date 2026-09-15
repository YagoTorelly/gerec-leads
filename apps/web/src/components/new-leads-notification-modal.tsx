"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import type { NewLeadNotificationSnapshot } from "../lib/api/types";
import { formatDateTime } from "../lib/dashboard/format";
import { acknowledgeNewLeadsAction } from "../lib/notifications/actions";

export function NewLeadsNotificationModal({
  snapshot,
}: {
  snapshot: NewLeadNotificationSnapshot;
}) {
  const [open, setOpen] = useState(true);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const closeRef = useRef<HTMLButtonElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);
  const wasOpenRef = useRef(true);
  const titleId = "new-leads-notification-title";

  useEffect(() => {
    if (open) {
      previousFocusRef.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
      closeRef.current?.focus();
    } else if (wasOpenRef.current) {
      previousFocusRef.current?.focus();
    }
    wasOpenRef.current = open;
  }, [open]);

  const close = useCallback(async () => {
    if (pending) return;
    setPending(true);
    setError(null);
    const result = await acknowledgeNewLeadsAction(snapshot);
    if (result.ok) {
      setOpen(false);
      return;
    }
    setError(result.message);
    setPending(false);
  }, [pending, snapshot]);

  if (!open) return null;

  return (
    <div
      className="modal-backdrop"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) void close();
      }}
    >
      <section
        className="modal-card new-leads-notification-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onKeyDown={(event) => {
          if (event.key === "Escape") {
            event.preventDefault();
            void close();
          }
          if (event.key === "Tab") event.preventDefault();
        }}
      >
        <p className="eyebrow">Novas atribuições</p>
        <h3 id={titleId}>Novos leads</h3>
        <p className="muted">Confira os leads recebidos desde sua última confirmação.</p>
        <ol className="new-leads-notification-modal__list" aria-label="Leads recebidos">
          {snapshot.items.map((lead) => (
            <li key={lead.leadId}>
              <strong>{lead.contactName}</strong>
              <span>Recebido em {formatDateTime(lead.assignedAt)}</span>
            </li>
          ))}
        </ol>
        {error ? (
          <p className="form-error" role="alert">
            {error}
          </p>
        ) : null}
        <div className="modal-actions">
          <button
            ref={closeRef}
            type="button"
            className="table-action"
            disabled={pending}
            onClick={() => void close()}
          >
            {pending ? "Confirmando…" : "Fechar"}
          </button>
        </div>
      </section>
    </div>
  );
}
