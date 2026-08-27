export function parseSupabaseStatusEnv(source) {
  const values = Object.fromEntries(
    source
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter((line) => line && !line.startsWith("#") && line.includes("="))
      .map((line) => {
        const separator = line.indexOf("=");
        const key = line.slice(0, separator);
        const value = line.slice(separator + 1).replace(/^"|"$/g, "");
        return [key, value];
      }),
  );

  const publicKey = values.PUBLISHABLE_KEY ?? values.ANON_KEY;

  if (!values.API_URL || !publicKey) {
    throw new Error("Supabase local sem URL ou chave pública disponível.");
  }

  return {
    NEXT_PUBLIC_SUPABASE_URL: values.API_URL,
    NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY: publicKey,
    SUPABASE_SERVICE_ROLE_KEY: values.SERVICE_ROLE_KEY ?? "",
  };
}

export function renderNextEnv(values) {
  return `${Object.entries(values)
    .map(([key, value]) => `${key}=${value}`)
    .join("\n")}\n`;
}
