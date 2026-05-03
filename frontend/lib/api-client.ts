/**
 * Typed fetch wrapper. Reads NEXT_PUBLIC_API_URL, attaches JWT from localStorage.
 *
 * Usage:
 *   const ds = await api<Dataset[]>("/api/v1/datasets");
 *   const ds = await api<Dataset>("/api/v1/datasets", { method: "POST", body: form });
 */

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public payload?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function api<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers);
  if (typeof window !== "undefined") {
    const token = window.localStorage.getItem("ezidatic_token");
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }
  if (!(init.body instanceof FormData) && !headers.has("Content-Type") && init.body) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(`${BASE_URL}${path}`, { ...init, headers });
  if (!res.ok) {
    let payload: unknown;
    try {
      payload = await res.json();
    } catch {
      payload = await res.text();
    }
    throw new ApiError(res.status, `${res.status} ${res.statusText}`, payload);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}
