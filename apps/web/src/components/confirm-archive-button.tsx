"use client";
import { useEffect, useState } from "react";
import { archiveLeadAction } from "../lib/admin/lead-actions";

export function ConfirmArchiveButton({ leadId, contactName }: { leadId: number; contactName: string }) {
  const [seconds, setSeconds] = useState<number | null>(null);
  useEffect(() => {
    if (seconds === null || seconds <= 0) return;
    const timer = window.setTimeout(() => setSeconds((value) => (value ?? 1) - 1), 1000);
    return () => window.clearTimeout(timer);
  }, [seconds]);
  if (seconds !== null && seconds > 0) return <button type="button" className="danger-button" onClick={() => setSeconds(null)}>Aguarde {seconds}s</button>;
  if (seconds === 0) return <form action={archiveLeadAction}><input type="hidden" name="leadId" value={leadId} /><button className="danger-button" type="submit">Confirmar remoção</button></form>;
  return <button type="button" className="danger-button" onClick={() => setSeconds(5)} aria-label={`Remover ${contactName}`}>Remover</button>;
}
