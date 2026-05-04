"use client";

import { useCallback, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ApiError, api } from "@/lib/api-client";
import { streamSSE } from "@/lib/sse";
import type {
  ChatMessage,
  ChatSession,
  ChatStreamEvent,
  ChatToolCall,
} from "@/lib/types";

export function useChatSessions() {
  return useQuery<ChatSession[], ApiError>({
    queryKey: ["chat", "sessions"],
    queryFn: () => api<ChatSession[]>("/api/v1/chat/sessions"),
  });
}

export function useCreateChatSession() {
  const qc = useQueryClient();
  return useMutation<
    ChatSession,
    ApiError,
    { dataset_id?: string | null; title?: string | null }
  >({
    mutationFn: (input) =>
      api<ChatSession>("/api/v1/chat/sessions", {
        method: "POST",
        body: JSON.stringify(input),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["chat", "sessions"] });
    },
  });
}

export function useChatMessages(sessionId: string) {
  return useQuery<ChatMessage[], ApiError>({
    queryKey: ["chat", sessionId, "messages"],
    queryFn: () =>
      api<ChatMessage[]>(`/api/v1/chat/sessions/${sessionId}/messages`),
    enabled: !!sessionId,
  });
}

export interface StreamingState {
  active: boolean;
  intent: string | null;
  text: string;
  toolCalls: ChatToolCall[];
  providerUsed: string | null;
  tokenUsage: Record<string, unknown> | null;
  error: string | null;
}

const INITIAL: StreamingState = {
  active: false,
  intent: null,
  text: "",
  toolCalls: [],
  providerUsed: null,
  tokenUsage: null,
  error: null,
};

export function useSendChatMessage(sessionId: string) {
  const qc = useQueryClient();
  const [state, setState] = useState<StreamingState>(INITIAL);

  const send = useCallback(
    async (content: string, datasetId?: string | null) => {
      if (!content.trim()) return;
      setState({ ...INITIAL, active: true });

      // Optimistically append the user message to the cache so it shows
      // up before the stream opens.
      qc.setQueryData<ChatMessage[]>(
        ["chat", sessionId, "messages"],
        (prev) => [
          ...(prev ?? []),
          {
            id: `pending-user-${Date.now()}`,
            session_id: sessionId,
            role: "user",
            content,
            tool_calls: null,
            token_usage: null,
            provider_used: null,
            created_at: new Date().toISOString(),
          },
        ],
      );

      try {
        for await (const event of streamSSE<ChatStreamEvent>(
          `/api/v1/chat/sessions/${sessionId}/messages`,
          { content, dataset_id: datasetId ?? null },
        )) {
          if (event.type === "intent") {
            setState((s) => ({ ...s, intent: event.value }));
          } else if (event.type === "delta") {
            setState((s) => ({ ...s, text: s.text + event.text }));
          } else if (event.type === "tool_calls") {
            setState((s) => ({
              ...s,
              toolCalls: [...s.toolCalls, ...event.data],
            }));
          } else if (event.type === "done") {
            setState((s) => ({
              ...s,
              providerUsed: event.provider_used,
              tokenUsage: event.token_usage,
              toolCalls: event.tool_calls.length
                ? event.tool_calls
                : s.toolCalls,
              text: event.content || s.text,
            }));
          } else if (event.type === "error") {
            setState((s) => ({ ...s, error: event.message }));
          } else if (event.type === "saved") {
            // Stream done. Refetch messages to pick up the persisted
            // assistant row and clear the optimistic user entry.
            await qc.invalidateQueries({
              queryKey: ["chat", sessionId, "messages"],
            });
            setState((s) => ({ ...s, active: false }));
          }
        }
      } catch (e) {
        setState((s) => ({
          ...s,
          active: false,
          error: e instanceof Error ? e.message : String(e),
        }));
      }
    },
    [qc, sessionId],
  );

  const reset = useCallback(() => setState(INITIAL), []);

  return { state, send, reset };
}
