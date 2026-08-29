"use client";

import { useEffect, useRef } from "react";

export function ConfirmActionModal({ title, description, confirmLabel, pending, onConfirm, onCancel }: {
  title: string;
  description: string;
  confirmLabel: string;
  pending: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  const confirmRef = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    confirmRef.current?.focus();
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !pending) onCancel();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onCancel, pending]);

  return <div className="modal-backdrop" role="presentation" onMouseDown={(event) => {
    if (event.target === event.currentTarget && !pending) onCancel();
  }}>
    <section className="modal-card" role="dialog" aria-modal="true" aria-labelledby="confirm-action-title">
      <h3 id="confirm-action-title">{title}</h3>
      <p className="muted">{description}</p>
      <div className="modal-actions">
        <button type="button" className="secondary-button" disabled={pending} onClick={onCancel}>Cancelar</button>
        <button ref={confirmRef} type="button" className="table-action" disabled={pending} onClick={onConfirm}>{pending ? "Salvando…" : confirmLabel}</button>
      </div>
    </section>
  </div>;
}
