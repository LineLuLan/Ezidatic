/**
 * Tiny SSE consumer for the chat endpoint. Yields parsed JSON events
 * from a `text/event-stream` response. The chat endpoint emits one
 * `data: <json>\n\n` line per event (no `event:` field) so the parser
 * stays minimal.
 */

import { getToken } from "@/lib/api-client";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function* streamSSE<T>(
  path: string,
  body: unknown,
  signal?: AbortSignal,
): AsyncGenerator<T, void, unknown> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "text/event-stream",
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
    signal,
  });
  if (!res.ok || !res.body) {
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
    throw new Error(message);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let idx;
    while ((idx = buffer.indexOf("\n\n")) !== -1) {
      const raw = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      for (const line of raw.split("\n")) {
        if (!line.startsWith("data:")) continue;
        const blob = line.slice(5).trim();
        if (!blob) continue;
        try {
          yield JSON.parse(blob) as T;
        } catch {
          // Malformed line — skip rather than crashing the whole stream.
        }
      }
    }
  }
}
