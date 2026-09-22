"use client";

import { useEffect, useRef, useState } from "react";

import { createManualLeadAction } from "../lib/admin/manual-lead-actions";
import type { ManualLeadInput } from "../lib/api/types";

export type LatestCampaignDefaults = {
  campaign?: string | null;
  source?: string | null;
};

function initialOrigin(defaults: LatestCampaignDefaults | null): Pick<ManualLeadInput, "campaign" | "source"> {
  return {
    campaign: defaults?.campaign?.trim() || "",
    source: defaults?.source?.trim() || "",
  };
}

export function ManualLeadForm({
  latestCampaignDefaults = null,
}: {
  latestCampaignDefaults?: LatestCampaignDefaults | null;
}) {
  const trigger = useRef<HTMLButtonElement>(null);
  const initialInput = useRef<HTMLInputElement>(null);
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [campaign, setCampaign] = useState(() => initialOrigin(latestCampaignDefaults).campaign ?? "");
  const [source, setSource] = useState(() => initialOrigin(latestCampaignDefaults).source ?? "");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const canSubmit = Boolean(name.trim() && email.trim() && phone.trim() && !pending);

  useEffect(() => {
    if (!open) return;
    initialInput.current?.focus();
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !pending) {
        setOpen(false);
        trigger.current?.focus();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, pending]);

  function close() {
    if (pending) return;
    setOpen(false);
    trigger.current?.focus();
  }

  function reset() {
    const defaults = initialOrigin(latestCampaignDefaults);
    setName("");
    setEmail("");
    setPhone("");
    setCampaign(defaults.campaign ?? "");
    setSource(defaults.source ?? "");
  }

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmit) return;
    setPending(true);
    setError(null);
    try {
      const result = await createManualLeadAction({
        name: name.trim(),
        email: email.trim(),
        phone: phone.trim(),
        campaign: campaign.trim() || undefined,
        source: source.trim() || undefined,
      });
      if (!result.ok) {
        setError(result.message);
        return;
      }
      const assignment = result.lead.assigneeId
        ? ` Responsável atribuído (identificador): ${result.lead.assigneeId}.`
        : " O lead aguarda um vendedor ativo.";
      setNotice(`${result.message} ID manual: ${result.lead.manualQueueLeadId}.${assignment}`);
      reset();
      setOpen(false);
      trigger.current?.focus();
    } catch {
      setError("Não foi possível cadastrar o lead. Tente novamente.");
    } finally {
      setPending(false);
    }
  }

  return (
    <section className="panel-card" aria-labelledby="manual-lead-title">
      <div className="panel-head">
        <div>
          <p className="eyebrow">Cadastro manual</p>
          <h2 id="manual-lead-title">Leads</h2>
          <p className="muted">Cadastre um contato na fila alternativa, sem alterar a fila automática.</p>
        </div>
        <button
          ref={trigger}
          type="button"
          className="table-action"
          onClick={() => {
            setError(null);
            setOpen(true);
          }}
        >
          Adicionar leads
        </button>
      </div>
      {notice ? <p className="form-success" role="status" aria-live="polite">{notice}</p> : null}
      {open ? (
        <div
          className="modal-backdrop"
          role="presentation"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) close();
          }}
        >
          <section className="modal-card" role="dialog" aria-modal="true" aria-labelledby="manual-lead-dialog-title">
            <h3 id="manual-lead-dialog-title">Adicionar lead</h3>
            <p className="muted">O responsável será definido automaticamente pela fila alternativa.</p>
            <form onSubmit={submit}>
              <label htmlFor="manual-lead-name">Nome
                <input ref={initialInput} id="manual-lead-name" value={name} onChange={(event) => setName(event.target.value)} autoComplete="name" required />
              </label>
              <label htmlFor="manual-lead-email">E-mail
                <input id="manual-lead-email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" required />
              </label>
              <label htmlFor="manual-lead-phone">Telefone
                <input id="manual-lead-phone" type="tel" value={phone} onChange={(event) => setPhone(event.target.value)} autoComplete="tel" required />
              </label>
              <label htmlFor="manual-lead-campaign">Campanha (opcional)
                <input id="manual-lead-campaign" value={campaign} onChange={(event) => setCampaign(event.target.value)} />
              </label>
              <label htmlFor="manual-lead-source">Origem (opcional)
                <input id="manual-lead-source" value={source} onChange={(event) => setSource(event.target.value)} />
              </label>
              <label htmlFor="manual-lead-status">Situação
                <input id="manual-lead-status" value="Indefinido" readOnly aria-readonly="true" />
              </label>
              {error ? <p className="form-error" role="status">{error}</p> : null}
              <div className="modal-actions">
                <button type="button" className="secondary-button" disabled={pending} onClick={close}>Cancelar</button>
                <button type="submit" className="table-action" disabled={!canSubmit}>{pending ? "Cadastrando…" : "Cadastrar lead"}</button>
              </div>
            </form>
          </section>
        </div>
      ) : null}
    </section>
  );
}
