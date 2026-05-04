"use client";

import { MessageBubble } from "@/components/chat/MessageBubble";
import { ProviderBadge } from "@/components/chat/ProviderBadge";
import { ToolCallView } from "@/components/chat/ToolCallView";
import type { ChatMessage } from "@/lib/types";
import type { StreamingState } from "@/lib/hooks/useChat";

interface Props {
  messages: ChatMessage[];
  streaming: StreamingState;
}

export function MessageList({ messages, streaming }: Props) {
  if (messages.length === 0 && !streaming.active) {
    return (
      <p className="rounded-md border bg-muted/40 p-6 text-center text-sm text-muted-foreground">
        Ask a question about the dataset to get started. Try{" "}
        <code className="rounded bg-background px-1 py-0.5 text-xs">
          How many rows have salary &gt; 50000?
        </code>
      </p>
    );
  }
  return (
    <div className="space-y-3">
      {messages.map((m) => (
        <MessageBubble key={m.id} message={m} />
      ))}
      {streaming.active && (
        <div className="rounded-lg border bg-card p-4 space-y-2">
          <div className="flex items-center gap-2 text-xs">
            <span className="font-medium uppercase text-muted-foreground">
              assistant
            </span>
            <ProviderBadge provider={streaming.providerUsed} />
            {streaming.intent && (
              <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] font-mono uppercase text-muted-foreground">
                {streaming.intent}
              </span>
            )}
            <span className="ml-auto animate-pulse text-muted-foreground">
              streaming…
            </span>
          </div>
          {streaming.text && (
            <p className="whitespace-pre-wrap text-sm leading-6">
              {streaming.text}
            </p>
          )}
          {streaming.toolCalls.length > 0 && (
            <div className="space-y-2">
              {streaming.toolCalls.map((t, idx) => (
                <ToolCallView key={`stream-${t.name}-${idx}`} call={t} />
              ))}
            </div>
          )}
        </div>
      )}
      {streaming.error && (
        <p className="text-sm text-destructive">{streaming.error}</p>
      )}
    </div>
  );
}
