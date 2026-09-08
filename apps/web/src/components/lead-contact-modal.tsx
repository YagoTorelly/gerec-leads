"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import type { OperationalLead } from "../lib/api/types";
import { formatPhone, formatText } from "../lib/dashboard/format";

export function LeadContactModal({ lead }: { lead: OperationalLead }) {
  const [open, setOpen] = useState(false);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const closeRef = useRef<HTMLButtonElement>(null);
  const wasOpenRef = useRef(false);
  const titleId = `lead-contact-title-${lead.id}`;
  const close = useCallback(() => setOpen(false), []);

  useEffect(() => {
    if (open) {
      closeRef.current?.focus();
    } else if (wasOpenRef.current) {
      triggerRef.current?.focus();
    }
    wasOpenRef.current = open;
  }, [open]);

  return (
    <>
      <button
        ref={triggerRef}
        type="button"
        className="table-action"
        aria-label={`Ver contato de ${lead.contactName}`}
        onClick={() => setOpen(true)}
      >
        Ver contato
      </button>
      {open ? (
        <div
          className="modal-backdrop"
          role="presentation"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) close();
          }}
        >
          <section
            className="modal-card contact-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby={titleId}
            onKeyDown={(event) => {
              if (event.key === "Escape") close();
            }}
          >
            <header className="treatment-modal__header">
              <div>
                <p className="eyebrow">Contato</p>
                <h3 id={titleId}>Contato de {lead.contactName}</h3>
              </div>
              <button
                ref={closeRef}
                type="button"
                className="secondary-button"
                aria-label="Fechar contato"
                onClick={close}
              >
                Fechar
              </button>
            </header>
            <dl className="contact-modal__details">
              <div>
                <dt>Telefone</dt>
                <dd>{formatPhone(lead.phoneDisplay)}</dd>
              </div>
              <div>
                <dt>E-mail</dt>
                <dd>{formatText(lead.email)}</dd>
              </div>
            </dl>
          </section>
        </div>
      ) : null}
    </>
  );
}
