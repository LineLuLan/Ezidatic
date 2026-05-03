export default function EdaPage({ params }: { params: { id: string } }) {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">EDA — {params.id}</h1>
      <p className="text-sm text-muted-foreground">
        TODO Sprint 2 / M3_EDA_CHARTS — fetch profile + chart specs and render
        via <code>ChartRenderer</code>.
      </p>
    </div>
  );
}
