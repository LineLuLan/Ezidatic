"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { ChatInput } from "@/components/chat/ChatInput";
import { MessageList } from "@/components/chat/MessageList";
import { SessionSidebar } from "@/components/chat/SessionSidebar";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  useChatMessages,
  useChatSessions,
  useCreateChatSession,
  useSendChatMessage,
} from "@/lib/hooks/useChat";

export default function ChatSessionPage({
  params,
}: {
  params: { sessionId: string };
}) {
  const router = useRouter();
  const sessions = useChatSessions();
  const messages = useChatMessages(params.sessionId);
  const { state, send } = useSendChatMessage(params.sessionId);
  const create = useCreateChatSession();

  const activeSession = sessions.data?.find((s) => s.id === params.sessionId);

  if (messages.isLoading) {
    return <p className="text-sm text-muted-foreground">Loading session…</p>;
  }
  if (messages.isError) {
    return (
      <Alert variant="destructive">
        <AlertDescription>{messages.error?.message}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="flex gap-6">
      <SessionSidebar
        sessions={sessions.data ?? []}
        activeId={params.sessionId}
        isCreating={create.isPending}
        onNewChat={async () => {
          const s = await create.mutateAsync({
            dataset_id: activeSession?.dataset_id ?? null,
          });
          router.push(`/chat/${s.id}`);
        }}
      />
      <div className="flex-1 space-y-4 overflow-hidden">
        <div className="space-y-1">
          <Link
            href="/chat"
            className="text-xs text-muted-foreground hover:underline"
          >
            ← All chats
          </Link>
          <h1 className="text-2xl font-semibold">
            {activeSession?.title || "Untitled chat"}
          </h1>
          {activeSession?.dataset_id && (
            <p className="text-xs text-muted-foreground">
              dataset:{" "}
              <Link
                href={`/datasets/${activeSession.dataset_id}`}
                className="font-mono hover:underline"
              >
                {activeSession.dataset_id.slice(0, 8)}…
              </Link>
            </p>
          )}
        </div>

        <MessageList
          messages={messages.data ?? []}
          streaming={state}
        />

        <ChatInput
          disabled={state.active}
          onSubmit={(content) =>
            send(content, activeSession?.dataset_id ?? null)
          }
        />
      </div>
    </div>
  );
}
