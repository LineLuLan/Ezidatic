"use client";

import { ChartRenderer } from "@/components/charts/ChartRenderer";
import type { ChartSpec, ExperimentOut } from "@/lib/types";

function buildImportanceSpec(
  modelType: string,
  importance: Record<string, number>,
): ChartSpec {
  const sorted = Object.entries(importance)
    .filter(([, v]) => Number.isFinite(v))
    .sort(([, a], [, b]) => b - a)
    .slice(0, 25);
  return {
    type: "bar",
    title: `Feature importance — ${modelType}`,
    x_axis: { key: "feature", label: "feature", type: "category" },
    y_axis: { key: "importance", label: "importance", type: "numeric" },
    series: [
      {
        name: "importance",
        data: sorted.map(([feature, importance]) => ({
          feature,
          importance,
        })),
      },
    ],
  };
}

export function ExperimentDrawer({
  experiment,
  onClose,
}: {
  experiment: ExperimentOut;
  onClose: () => void;
}) {
  const metrics = experiment.metrics ?? {};
  const fi = (metrics.feature_importance ?? null) as
    | Record<string, number>
    | null;
  const numericMetrics = Object.entries(metrics).filter(
    ([key, value]) =>
      typeof value === "number" &&
      key !== "train_time_sec" &&
      key !== "feature_importance",
  ) as Array<[string, number]>;
  const trainTime =
    typeof metrics.train_time_sec === "number" ? metrics.train_time_sec : null;

  return (
    <aside className="rounded-md border bg-card">
      <div className="flex items-start justify-between border-b p-4">
        <div>
          <p className="text-xs uppercase text-muted-foreground">Experiment</p>
          <h3 className="text-lg font-semibold">{experiment.model_type}</h3>
          <p className="text-xs text-muted-foreground">
            {experiment.task_type} · target = {experiment.target_column}
          </p>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="text-xs text-muted-foreground hover:underline"
        >
          Close
        </button>
      </div>
      <div className="space-y-4 p-4">
        <dl className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
          {numericMetrics.map(([k, v]) => (
            <div key={k}>
              <dt className="text-xs uppercase text-muted-foreground">{k}</dt>
              <dd className="font-mono">{v.toFixed(4)}</dd>
            </div>
          ))}
          {trainTime !== null && (
            <div>
              <dt className="text-xs uppercase text-muted-foreground">
                train_time_sec
              </dt>
              <dd className="font-mono">{trainTime.toFixed(2)}</dd>
            </div>
          )}
          {experiment.artifact_path && (
            <div className="col-span-2 sm:col-span-4">
              <dt className="text-xs uppercase text-muted-foreground">
                artifact
              </dt>
              <dd className="break-all font-mono text-xs">
                {experiment.artifact_path}
              </dd>
            </div>
          )}
        </dl>
        {fi && Object.keys(fi).length > 0 ? (
          <ChartRenderer spec={buildImportanceSpec(experiment.model_type, fi)} />
        ) : (
          <p className="text-sm text-muted-foreground">
            No feature importance recorded for this model
            {experiment.model_type.includes("logistic")
              ? " — coefficients are scale-dependent."
              : "."}
          </p>
        )}
      </div>
    </aside>
  );
}
