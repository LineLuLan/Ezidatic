/**
 * Typed fetch wrapper. Reads NEXT_PUBLIC_API_URL, attaches JWT from localStorage.
 *
 * Usage:
 *   const ds = await api<Dataset[]>("/api/v1/datasets");
 *   const ds = await api<Dataset>("/api/v1/datasets", { method: "POST", body: form });
 */

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const TOKEN_KEY = "ezidatic_token";
const COOKIE_KEY = "ezidatic_token";
const COOKIE_MAX_AGE = 60 * 60 * 24; // 1 day, mirrors backend ACCESS_TOKEN_EXPIRE_MINUTES

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

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

/**
 * Persist the token to localStorage AND a cookie.
 *
 * Why both: Edge middleware (route guard) cannot read localStorage. The
 * cookie lets server-side redirects work without flashing the dashboard.
 * The cookie is intentionally NOT httpOnly so we can clear it on logout
 * from the client. See docs/ARCHITECTURE.md Deviations.
 */
export function setToken(token: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(TOKEN_KEY, token);
  document.cookie = `${COOKIE_KEY}=${token}; path=/; max-age=${COOKIE_MAX_AGE}; SameSite=Lax`;
}

export function clearToken(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(TOKEN_KEY);
  document.cookie = `${COOKIE_KEY}=; path=/; max-age=0; SameSite=Lax`;
}

export async function api<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers);
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
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
    const message =
      typeof payload === "object" && payload && "message" in payload
        ? String((payload as { message: unknown }).message)
        : `${res.status} ${res.statusText}`;
    throw new ApiError(res.status, message, payload);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}
