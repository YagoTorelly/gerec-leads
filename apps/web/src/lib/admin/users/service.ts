import { randomBytes } from "node:crypto";

import {
  supabaseAdminRequest,
  supabaseAdminRestPatch,
  supabaseAdminRestSelect,
  supabaseAdminRestUpsert,
} from "../../supabase/admin";

const PASSWORD_ALPHABET = "abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789!@#$%^&*";
const MAX_QUEUE_POSITION = 4;

type ProfileRow = {
  user_id: string;
  full_name: string;
  email: string;
  role: "admin" | "seller";
  is_active: boolean;
};

type QueueRow = {
  seller_id: string;
  position: number;
  is_paused: boolean;
};

type SaveSellerInput = {
  userId?: string;
  fullName: string;
  email: string;
  position: number;
  password?: string;
  isActive: boolean;
  isPaused: boolean;
};

function generatePassword(length = 20) {
  const required = ["a", "A", "2", "!"];
  const rest = Array.from(
    randomBytes(Math.max(0, length - required.length)),
    (value) => PASSWORD_ALPHABET[value % PASSWORD_ALPHABET.length],
  );
  return [...required, ...rest].sort(() => randomBytes(1)[0] - 128).join("");
}

function normalizeEmail(email: string) {
  return email.trim().toLowerCase();
}

function normalizePosition(position: number) {
  if (!Number.isInteger(position) || position < 1 || position > MAX_QUEUE_POSITION) {
    throw new Error(`A posição deve ficar entre 1 e ${MAX_QUEUE_POSITION}.`);
  }

  return position;
}

async function loadAdminState() {
  const [profiles, queue] = await Promise.all([
    supabaseAdminRestSelect<ProfileRow>(
      "profiles?select=user_id,full_name,email,role,is_active&order=full_name.asc",
    ),
    supabaseAdminRestSelect<QueueRow>("seller_queue?select=seller_id,position,is_paused"),
  ]);

  return { profiles, queue };
}

async function upsertProfile(profile: ProfileRow) {
  await supabaseAdminRestUpsert(
    "profiles?on_conflict=user_id",
    profile,
    "resolution=merge-duplicates,return=minimal",
  );
}

async function upsertQueue(queue: QueueRow) {
  await supabaseAdminRestUpsert(
    "seller_queue?on_conflict=seller_id",
    queue,
    "resolution=merge-duplicates,return=minimal",
  );
}

async function upsertSkipBalance(sellerId: string) {
  await supabaseAdminRestUpsert(
    "seller_skip_balances?on_conflict=seller_id",
    { seller_id: sellerId, balance: 0 },
    "resolution=merge-duplicates,return=minimal",
  );
}

function assertSellerSlotAvailable(queue: QueueRow[], input: SaveSellerInput) {
  const taken = queue.find(
    (entry) => entry.position === input.position && entry.seller_id !== input.userId,
  );

  if (taken) {
    throw new Error("A posição da fila já está ocupada por outro vendedor.");
  }
}

export async function saveSeller(input: SaveSellerInput) {
  const email = normalizeEmail(input.email);
  const position = normalizePosition(input.position);
  const { profiles, queue } = await loadAdminState();
  const password = input.password?.trim() || generatePassword();

  const duplicatedEmail = profiles.find(
    (profile) => profile.email.toLowerCase() === email && profile.user_id !== input.userId,
  );
  if (duplicatedEmail) {
    throw new Error("Já existe um usuário com este e-mail.");
  }

  assertSellerSlotAvailable(queue, { ...input, position, email });

  if (!input.userId) {
    const created = await supabaseAdminRequest<{ id: string }>("/auth/v1/admin/users", {
      method: "POST",
      body: JSON.stringify({
        email,
        password,
        email_confirm: true,
        user_metadata: { full_name: input.fullName, role: "seller" },
      }),
    });

    await upsertProfile({
      user_id: created.id,
      full_name: input.fullName.trim(),
      email,
      role: "seller",
      is_active: input.isActive,
    });
    await upsertQueue({
      seller_id: created.id,
      position,
      is_paused: !input.isActive || input.isPaused,
    });
    await upsertSkipBalance(created.id);
    return;
  }

  await supabaseAdminRequest(`/auth/v1/admin/users/${input.userId}`, {
    method: "PUT",
    body: JSON.stringify({
      email,
      ...(input.password?.trim() ? { password } : {}),
      email_confirm: true,
      user_metadata: { full_name: input.fullName, role: "seller" },
    }),
  });

  await supabaseAdminRestPatch(`profiles?user_id=eq.${encodeURIComponent(input.userId)}`, {
    full_name: input.fullName.trim(),
    email,
    is_active: input.isActive,
  });
  await upsertQueue({
    seller_id: input.userId,
    position,
    is_paused: !input.isActive || input.isPaused,
  });
  await upsertSkipBalance(input.userId);
}

export async function setSellerActiveState(userId: string, isActive: boolean) {
  const { queue } = await loadAdminState();
  const queueRow = queue.find((entry) => entry.seller_id === userId);

  await supabaseAdminRestPatch(`profiles?user_id=eq.${encodeURIComponent(userId)}`, {
    is_active: isActive,
  });

  if (queueRow) {
    await upsertQueue({
      seller_id: queueRow.seller_id,
      position: queueRow.position,
      is_paused: isActive ? queueRow.is_paused : true,
    });
  }
}
