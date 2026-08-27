import { randomBytes } from "node:crypto";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { adminRequest, restSelect, restUpsert } from "./admin-client.mjs";
import { readLocalSupabaseRuntime } from "./local-runtime.mjs";
import { seedLocalDemoData } from "./seed-local-demo-data.mjs";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const PASSWORD_ALPHABET = "abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789!@#$%^&*";

export const LOCAL_ADMIN_PASSWORD = "Wtg@2026!Admin";

export const LOCAL_USERS = [
  { email: "admin@gerec.local", fullName: "Administrador WTG", role: "admin", position: null },
  { email: "renato@gerec.local", fullName: "Renato", role: "seller", position: 1 },
  { email: "sandra@gerec.local", fullName: "Sandra", role: "seller", position: 2 },
  { email: "jessica@gerec.local", fullName: "Jessica", role: "seller", position: 3 },
  { email: "nelma@gerec.local", fullName: "Nelma", role: "seller", position: 4 },
];

export function generatePassword(length = 20) {
  const required = ["a", "A", "2", "!"];
  const rest = Array.from(
    randomBytes(Math.max(0, length - required.length)),
    (value) => PASSWORD_ALPHABET[value % PASSWORD_ALPHABET.length],
  );
  return [...required, ...rest].sort(() => randomBytes(1)[0] - 128).join("");
}

export function resolveUserPassword(user) {
  return user.role === "admin" ? LOCAL_ADMIN_PASSWORD : generatePassword();
}

async function ensureAuthUser(runtime, user, password) {
  const listing = await adminRequest(runtime, "/auth/v1/admin/users?per_page=1000");
  const existing = (listing.users ?? []).find(
    (candidate) => candidate.email?.toLowerCase() === user.email,
  );
  const payload = {
    email: user.email,
    password,
    email_confirm: true,
    user_metadata: { full_name: user.fullName, role: user.role },
  };

  return existing
    ? adminRequest(runtime, `/auth/v1/admin/users/${existing.id}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      })
    : adminRequest(runtime, "/auth/v1/admin/users", {
        method: "POST",
        body: JSON.stringify(payload),
      });
}

export async function bootstrapLocalUsers({
  cwd = ROOT,
  outputPath = resolve(ROOT, "supabase/.temp/local-users.json"),
} = {}) {
  const runtime = readLocalSupabaseRuntime({ cwd });
  const credentials = [];

  for (const user of LOCAL_USERS) {
    const password = resolveUserPassword(user);
    const authUser = await ensureAuthUser(runtime, user, password);
    await restUpsert(
      runtime,
      "profiles?on_conflict=user_id",
      {
        user_id: authUser.id,
        full_name: user.fullName,
        email: user.email,
        role: user.role,
        is_active: true,
      },
      "resolution=merge-duplicates,return=minimal",
    );
    credentials.push({ email: user.email, password, role: user.role, position: user.position });
  }

  const sellerProfiles = credentials.filter((user) => user.role === "seller");
  const profiles = await restSelect(runtime, "profiles?select=user_id,email");
  const profileByEmail = new Map(profiles.map((profile) => [profile.email, profile.user_id]));
  const queue = sellerProfiles.map((seller) => ({
    seller_id: profileByEmail.get(seller.email),
    position: seller.position,
    is_paused: false,
  }));

  await restUpsert(
    runtime,
    "seller_queue?on_conflict=seller_id",
    queue,
    "resolution=merge-duplicates,return=minimal",
  );
  await restUpsert(
    runtime,
    "seller_skip_balances?on_conflict=seller_id",
    queue.map(({ seller_id }) => ({ seller_id, balance: 0 })),
    "resolution=merge-duplicates,return=minimal",
  );
  await restUpsert(
    runtime,
    "queue_state?on_conflict=singleton",
    { singleton: true, next_seller_id: queue[0].seller_id, version: 0 },
    "resolution=merge-duplicates,return=minimal",
  );

  try {
    await seedLocalDemoData(runtime, profileByEmail);
  } catch (error) {
    if (error instanceof Error && error.message.includes("HTTP 403")) {
      throw new Error(
        "O seed demo local precisa das migrations mais recentes. Rode `npm run supabase:reset`, depois `npm run env:local` e `npm run supabase:bootstrap-users` novamente.",
      );
    }
    throw error;
  }

  mkdirSync(dirname(outputPath), { recursive: true });
  writeFileSync(
    outputPath,
    JSON.stringify({ generatedAt: new Date().toISOString(), users: credentials }, null, 2),
    { mode: 0o600 },
  );

  return { outputPath, count: credentials.length };
}

if (resolve(process.argv[1] ?? "") === fileURLToPath(import.meta.url)) {
  const result = await bootstrapLocalUsers();
  console.log(
    `Usuários locais reconciliados: ${result.count}. Credenciais salvas em ${result.outputPath}.`,
  );
}
