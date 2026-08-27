import { runSupabaseStatusEnv } from "./write-web-env.mjs";

export function parseLocalRuntimeEnv(source) {
  const values = Object.fromEntries(
    source
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter((line) => line && !line.startsWith("#") && line.includes("="))
      .map((line) => {
        const separator = line.indexOf("=");
        return [line.slice(0, separator), line.slice(separator + 1).replace(/^"|"$/g, "")];
      }),
  );

  const publishableKey = values.PUBLISHABLE_KEY ?? values.ANON_KEY;
  if (!values.API_URL || !publishableKey || !values.SERVICE_ROLE_KEY) {
    throw new Error("Supabase local sem configuração administrativa completa.");
  }

  return {
    apiUrl: values.API_URL,
    publishableKey,
    serviceRoleKey: values.SERVICE_ROLE_KEY,
  };
}

export function readLocalSupabaseRuntime({ cwd }) {
  return parseLocalRuntimeEnv(runSupabaseStatusEnv({ cwd }));
}
