export default function ChatPage({ params }: { params: { sessionId: string } }) {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Chat — {params.sessionId}</h1>
      <p className="text-sm text-muted-foreground">
        TODO Sprint 4 / M5_AGENTIC_CHAT — wire up SSE stream from{" "}
        <code>/api/v1/chat/sessions/:id/messages</code>.
      </p>
    </div>
  );
}
