"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { ExperimentDrawer } from "@/components/ml/ExperimentDrawer";
import { Leaderboard } from "@/components/ml/Leaderboard";
import { TrainForm } from "@/components/ml/TrainForm";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Card, CardContent } from "@/components/ui/card";
import { useDataset } from "@/lib/hooks/useDatasets";
import { useLeaderboard, useTrainModel } from "@/lib/hooks/useMl";
import type { ExperimentOut, TaskType } from "@/lib/types";

const POLL_MS = 5_000;

export default function MlPage({ params }: { params: { id: string } }) {
  const dataset = useDataset(params.id);
  const train = useTrainModel(params.id);
  const [pollUntilCount, setPollUntilCount] = useState<number | null>(null);
  const [selected, setSelected] = useState<ExperimentOut | null>(null);
  const [taskType, setTaskType] = useState<TaskType>("classification");

  const leaderboard = useLeaderboard(
    params.id,
    pollUntilCount !== null ? POLL_MS : undefined,
  );

  // When polling is active and rows.length grew past the snapshot, stop.
  useMemo(() => {
    if (
      pollUntilCount !== null &&
      leaderboard.data &&
      leaderboard.data.length > pollUntilCount
    ) {
      setPollUntilCount(null);
    }
  }, [leaderboard.data, pollUntilCount]);

  const primaryMetric = taskType === "classification" ? "accuracy" : "r2";

  if (dataset.isLoading) {
    return <p className="text-sm text-muted-foreground">Loading dataset…</p>;
  }
  if (dataset.isError || !dataset.data) {
    return (
      <Alert variant="destructive">
        <AlertDescription>
          {dataset.error?.message ?? "Dataset not found"}
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <Link
          href={`/datasets/${params.id}`}
          className="text-xs text-muted-foreground hover:underline"
        >
          ← Back to dataset
        </Link>
        <h1 className="text-2xl font-semibold">AutoML</h1>
        <p className="text-sm text-muted-foreground">
          Pick a target column + task. Every registered estimator trains; the
          best model gets persisted as a joblib artifact.
        </p>
      </div>

      <Card>
        <CardContent className="space-y-4 p-6">
          <TrainForm
            columns={dataset.data.columns}
            isPending={train.isPending}
            onSubmit={async (input) => {
              setTaskType(input.task_type);
              const before = leaderboard.data?.length ?? 0;
              try {
                const result = await train.mutateAsync(input);
                if (input.background) {
                  // Background queued — start polling until rows grow.
                  setPollUntilCount(before);
                } else {
                  // Sync result already populated; refresh the list once.
                  void leaderboard.refetch();
                }
                if (result.best?.feature_importance) {
                  // No-op now; drawer opens on user click.
                }
              } catch {
                // Error surfaces below via train.error.
              }
            }}
          />
          {train.isError && (
            <Alert variant="destructive">
              <AlertDescription>{train.error?.message}</AlertDescription>
            </Alert>
          )}
          {train.data && !pollUntilCount && (
            <Alert>
              <AlertDescription>
                Trained {train.data.leaderboard.length} models. Best:{" "}
                <strong>{train.data.best?.name ?? "—"}</strong>
                {train.data.best
                  ? ` (${primaryMetric}=${(
                      train.data.best.metrics[primaryMetric] ?? 0
                    ).toFixed(4)})`
                  : ""}
                .
              </AlertDescription>
            </Alert>
          )}
          {pollUntilCount !== null && (
            <Alert>
              <AlertDescription>
                Background training queued. Polling leaderboard every{" "}
                {POLL_MS / 1000}s…
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      <section className="space-y-2">
        <h2 className="text-sm font-medium text-muted-foreground">
          Leaderboard — click a row for details
        </h2>
        {leaderboard.isLoading && (
          <p className="text-sm text-muted-foreground">Loading…</p>
        )}
        {leaderboard.isError && (
          <Alert variant="destructive">
            <AlertDescription>{leaderboard.error?.message}</AlertDescription>
          </Alert>
        )}
        {leaderboard.data && (
          <Leaderboard
            rows={leaderboard.data}
            primaryMetric={primaryMetric}
            onSelect={(row) =>
              setSelected(row.id === selected?.id ? null : row)
            }
            selectedId={selected?.id ?? null}
          />
        )}
      </section>

      {selected && (
        <ExperimentDrawer
          experiment={selected}
          onClose={() => setSelected(null)}
        />
      )}
    </div>
  );
}
