"use client";

import { useChatStore } from "@/lib/stores/chatStore";

export function MessageList() {
  const messages = useChatStore((s) => s.messages);
  return (
    <div className="space-y-2">
      {messages.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          TODO Sprint 4 / M5_AGENTIC_CHAT — render messages with streaming.
        </p>
      ) : (
        messages.map((m) => (
          <div key={m.id} className="rounded-md border p-3">
            <div className="text-xs uppercase text-muted-foreground">{m.role}</div>
            <div className="text-sm">{m.content}</div>
          </div>
        ))
      )}
    </div>
  );
}
