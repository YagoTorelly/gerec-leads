"use server";

function unavailable(action: string): never {
  throw new Error(`${action} ainda não está disponível na API Python.`);
}

export async function archiveLeadAction(_formData: FormData) {
  unavailable("Arquivamento de lead");
}
export async function simulateLeadsAction(_formData: FormData) {
  unavailable("Simulação de leads");
}
export async function saveSellerAction(_formData: FormData) {
  unavailable("Gestão de usuários");
}
export async function deactivateSellerAction(_formData: FormData) {
  unavailable("Gestão de usuários");
}
export async function reactivateSellerAction(_formData: FormData) {
  unavailable("Gestão de usuários");
}
