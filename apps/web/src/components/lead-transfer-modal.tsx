"use client";

import { useActionState, useEffect, useState } from "react";

import type { ManagedUser, OperationalLead } from "../lib/api/types";
import {
  transferLeadOwnershipAction,
} from "../lib/operations/transfer-actions";
import { initialTransferActionState } from "../lib/operations/transfer-state";

export function LeadTransferModal({
  lead,
  targets,
  onSuccess,
}: {
  lead: OperationalLead;
  targets: ManagedUser[];
  onSuccess?: (sellerName: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const [selectedSellerName, setSelectedSellerName] = useState("");
  const [state, formAction, pending] = useActionState(
    transferLeadOwnershipAction,
    initialTransferActionState,
  );
  useEffect(() => {
    if (state.status === "success") {
      const timer = window.setTimeout(() => {
        setOpen(false);
        onSuccess?.(selectedSellerName);
      }, 0);
      return () => window.clearTimeout(timer);
    }
  }, [onSuccess, selectedSellerName, state.status]);
  if (!open) {
    return (
      <button type="button" className="table-action secondary-button" onClick={() => setOpen(true)}>
        Transferir propriedade
      </button>
    );
  }
  return (
    <div className="inline-transfer" role="dialog" aria-label={`Transferir ${lead.contactName}`}>
      <form action={formAction}>
        <input type="hidden" name="leadId" value={lead.id} />
        <label>
          Novo responsável
          <select
            name="sellerId"
            defaultValue=""
            required
            onChange={(event) => {
              setSelectedSellerName(event.currentTarget.selectedOptions[0]?.text ?? "");
            }}
          >
            <option value="" disabled>
              Selecione
            </option>
            {targets
              .filter((target) => target.active && target.role === "seller")
              .map((target) => (
                <option key={target.id} value={target.id}>
                  {target.fullName}
                </option>
              ))}
          </select>
        </label>
        <label>
          Motivo
          <input name="reason" required maxLength={2000} placeholder="Motivo da transferência" />
        </label>
        {state.status === "error" ? (
          <p className="form-error" role="status">
            {state.message}
          </p>
        ) : null}
        <div className="inline-transfer__actions">
          <button type="button" className="secondary-button" onClick={() => setOpen(false)}>
            Cancelar
          </button>
          <button type="submit" className="table-action" disabled={pending}>
            {pending ? "Transferindo…" : "Confirmar"}
          </button>
        </div>
      </form>
    </div>
  );
}
