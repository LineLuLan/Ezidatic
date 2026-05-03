export default function MlPage({ params }: { params: { id: string } }) {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">AutoML — {params.id}</h1>
      <p className="text-sm text-muted-foreground">
        TODO Sprint 3 / M4_AUTOML — submit train, render leaderboard +
        feature importance.
      </p>
    </div>
  );
}
