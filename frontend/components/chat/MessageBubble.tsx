"use client";

import { ProviderBadge } from "@/components/chat/ProviderBadge";
import { ToolCallView } from "@/components/chat/ToolCallView";
import type { ChatMessage } from "@/lib/types";

export function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  const tools = message.tool_calls ?? [];
  return (
    <div
      className={[
        "rounded-lg border p-4 space-y-2",
        isUser ? "bg-primary/5 border-primary/30" : "bg-card",
      ].join(" ")}
    >
      <div className="flex items-center gap-2 text-xs">
        <span className="font-medium uppercase text-muted-foreground">
          {message.role}
        </span>
        {message.role === "assistant" && (
          <ProviderBadge provider={message.provider_used ?? null} />
        )}
        <span className="ml-auto text-muted-foreground">
          {new Date(message.created_at).toLocaleTimeString()}
        </span>
      </div>
      {message.content && (
        <p className="whitespace-pre-wrap text-sm leading-6">
          {message.content}
        </p>
      )}
      {tools.length > 0 && (
        <div className="space-y-2">
          {tools.map((t, idx) => (
            <ToolCallView key={`${t.name}-${idx}`} call={t} />
          ))}
        </div>
      )}
    </div>
  );
}
