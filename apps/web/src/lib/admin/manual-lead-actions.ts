"use server";

import { randomUUID } from "node:crypto";

import { revalidatePath } from "next/cache";

import { ApiRequestError, createManualLead } from "../api/client";
import type { ManualLeadInput } from "../api/types";
import { getSessionContext } from "../auth/session";

function optionalText(value: string | undefined): string | undefined {
  const normalized = value?.trim();
  return normalized || undefined;
}

function refreshLeadViews(): void {
  revalidatePath("/usuarios");
  revalidatePath("/dashboard");
  revalidatePath("/fila");
  revalidatePath("/notificacoes");
}

export async function createManualLeadAction(input: ManualLeadInput) {
  const name = input.name.trim();
  const email = input.email.trim();
  const phone = input.phone.trim();
  if (!name || !email || !phone) {
    return {
      ok: false as const,
      message: "Preencha nome, e-mail e telefone para cadastrar o lead.",
    };
  }

  try {
    const session = await getSessionContext();
    if (session.status !== "authenticated") {
      return { ok: false as const, message: "Sessão expirada. Entre novamente." };
    }
    if (session.profile.role !== "admin") {
      return { ok: false as const, message: "Você não tem permissão para cadastrar leads." };
    }

    const lead = await createManualLead(
      {
        name,
        email,
        phone,
        campaign: optionalText(input.campaign),
        source: optionalText(input.source),
      },
      randomUUID(),
      session.sessionToken,
    );
    refreshLeadViews();
    return {
      ok: true as const,
      message: lead.assigneeId
        ? "Lead cadastrado e distribuído."
        : "Lead cadastrado e aguardando um vendedor ativo.",
      lead,
    };
  } catch (error) {
    return {
      ok: false as const,
      message:
        error instanceof ApiRequestError
          ? error.message
          : "Não foi possível cadastrar o lead. Tente novamente.",
    };
  }
}
