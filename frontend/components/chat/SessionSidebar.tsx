"use client";

import Link from "next/link";

import { Button } from "@/components/ui/button";
import type { ChatSession } from "@/lib/types";

interface Props {
  sessions: ChatSession[];
  activeId: string | null;
  onNewChat: () => void;
  isCreating: boolean;
}

export function SessionSidebar({
  sessions,
  activeId,
  onNewChat,
  isCreating,
}: Props) {
  return (
    <aside className="w-64 shrink-0 space-y-3 border-r pr-4">
      <Button
        type="button"
        onClick={onNewChat}
        disabled={isCreating}
        variant="outline"
        className="w-full justify-start"
      >
        {isCreating ? "Creating…" : "+ New chat"}
      </Button>
      {sessions.length === 0 ? (
        <p className="text-xs text-muted-foreground">No chats yet.</p>
      ) : (
        <ul className="space-y-1">
          {sessions.map((s) => {
            const active = s.id === activeId;
            return (
              <li key={s.id}>
                <Link
                  href={`/chat/${s.id}`}
                  className={[
                    "block truncate rounded-md px-3 py-2 text-sm",
                    active
                      ? "bg-accent font-medium"
                      : "hover:bg-accent/60",
                  ].join(" ")}
                >
                  {s.title || "Untitled"}
                  <div className="text-[10px] text-muted-foreground">
                    {new Date(s.created_at).toLocaleString()}
                  </div>
                </Link>
              </li>
            );
          })}
        </ul>
      )}
    </aside>
  );
}
