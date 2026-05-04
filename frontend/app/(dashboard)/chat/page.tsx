"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useRef } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  useChatSessions,
  useCreateChatSession,
} from "@/lib/hooks/useChat";

export default function ChatIndexPage() {
  return (
    <Suspense fallback={<p className="text-sm text-muted-foreground">Loading…</p>}>
      <ChatIndexInner />
    </Suspense>
  );
}

function ChatIndexInner() {
  const router = useRouter();
  const params = useSearchParams();
  const datasetId = params.get("dataset_id");
  const sessions = useChatSessions();
  const create = useCreateChatSession();
  const triggered = useRef(false);

  // Auto-create + redirect when arriving with ?dataset_id=...
  useEffect(() => {
    if (triggered.current || !datasetId || create.isPending) return;
    triggered.current = true;
    create
      .mutateAsync({ dataset_id: datasetId, title: "New chat" })
      .then((s) => router.replace(`/chat/${s.id}`))
      .catch(() => {
        triggered.current = false;
      });
  }, [datasetId, create, router]);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Chat</h1>
      <p className="text-sm text-muted-foreground">
        Talk to your data. The router classifies each question and routes
        to a SQL/ML/EDA worker — answers stream as they arrive.
      </p>

      {create.isError && (
        <Alert variant="destructive">
          <AlertDescription>{create.error?.message}</AlertDescription>
        </Alert>
      )}

      {sessions.isLoading ? (
        <p className="text-sm text-muted-foreground">Loading sessions…</p>
      ) : sessions.data && sessions.data.length > 0 ? (
        <ul className="grid gap-2 sm:grid-cols-2">
          {sessions.data.map((s) => (
            <li key={s.id}>
              <a
                href={`/chat/${s.id}`}
                className="block rounded-md border p-3 hover:bg-accent/50"
              >
                <div className="font-medium">{s.title || "Untitled"}</div>
                <div className="text-xs text-muted-foreground">
                  {new Date(s.created_at).toLocaleString()}
                </div>
              </a>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-muted-foreground">
          No chats yet. Pick a dataset from /datasets and click the Chat
          button to start one.
        </p>
      )}

      <Button
        type="button"
        variant="outline"
        disabled={create.isPending}
        onClick={async () => {
          const s = await create.mutateAsync({});
          router.push(`/chat/${s.id}`);
        }}
      >
        {create.isPending ? "Creating…" : "+ Start dataset-less chat"}
      </Button>
    </div>
  );
}
