export async function adminRequest(runtime, path, options = {}) {
  const response = await fetch(`${runtime.apiUrl}${path}`, {
    ...options,
    headers: {
      apikey: runtime.serviceRoleKey,
      Authorization: `Bearer ${runtime.serviceRoleKey}`,
      "Content-Type": "application/json",
      ...(options.headers ?? {}),
    },
  });

  if (!response.ok) {
    const details = await response.text();
    throw new Error(`Supabase admin respondeu HTTP ${response.status}: ${details}`);
  }

  const body = await response.text();
  return body ? JSON.parse(body) : null;
}

export async function restSelect(runtime, path) {
  return adminRequest(runtime, `/rest/v1/${path}`, { method: "GET" });
}

export async function restUpsert(runtime, path, body, prefer = "resolution=merge-duplicates,return=representation") {
  return adminRequest(runtime, `/rest/v1/${path}`, {
    method: "POST",
    headers: { Prefer: prefer },
    body: JSON.stringify(body),
  });
}

export async function restPatch(runtime, path, body, prefer = "return=representation") {
  return adminRequest(runtime, `/rest/v1/${path}`, {
    method: "PATCH",
    headers: { Prefer: prefer },
    body: JSON.stringify(body),
  });
}
