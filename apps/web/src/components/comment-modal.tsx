"use client";
import { useState } from "react";
export function CommentModal({ leadId, action }: { leadId: string; action: (formData: FormData) => void }) {
  const [open, setOpen] = useState(false);
  return <><button type="button" className="table-action" onClick={() => setOpen(true)}>Comentar</button>{open && <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setOpen(false); }}><section className="modal-card" role="dialog" aria-modal="true" aria-labelledby="comment-title"><h3 id="comment-title">Registrar comentário</h3><p className="muted">Descreva o contato realizado com este lead.</p><form action={action} onSubmit={() => setOpen(false)}><input type="hidden" name="leadId" value={leadId} /><label>Comentário<textarea name="comment" required minLength={6} maxLength={2000} autoFocus placeholder="Ex.: Primeiro contato realizado por telefone." /></label><div className="modal-actions"><button type="button" className="secondary-button" onClick={() => setOpen(false)}>Cancelar</button><button type="submit" className="table-action">Salvar comentário</button></div></form></section></div>}</>;
}
