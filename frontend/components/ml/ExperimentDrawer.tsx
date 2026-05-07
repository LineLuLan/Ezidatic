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

// Q5-ML-03 / 04: keys we render through dedicated UI affordances rather
// than the generic "every numeric metric" grid below.
const HANDLED_KEYS = new Set([
  "train_time_sec",
  "feature_importance",
  "cv_mean",
  "cv_std",
  "primary_metric",
  "n_splits",
]);

function getNum(v: unknown): number | null {
  return typeof v === "number" && Number.isFinite(v) ? v : null;
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

  // Pair each numeric metric (e.g. accuracy=0.92) with its `_std` companion
  // (accuracy_std=0.03) so the drawer renders "accuracy 0.92 ± 0.03"
  // instead of two separate cells. _std rows themselves are hidden from
  // the generic grid.
  const numericPairs: Array<{ key: string; mean: number; std: number | null }> =
    [];
  for (const [key, value] of Object.entries(metrics)) {
    if (HANDLED_KEYS.has(key)) continue;
    if (key.endsWith("_std")) continue;
    const mean = getNum(value);
    if (mean === null) continue;
    const std = getNum(metrics[`${key}_std`]);
    numericPairs.push({ key, mean, std });
  }

  const trainTime = getNum(metrics.train_time_sec);
  const cvMean = getNum(metrics.cv_mean);
  const cvStd = getNum(metrics.cv_std);
  const nSplits = getNum(metrics.n_splits);
  const primaryMetric =
    typeof metrics.primary_metric === "string"
      ? (metrics.primary_metric as string)
      : null;

  return (
    <aside className="rounded-md border bg-card">
      <div className="flex items-start justify-between border-b p-4">
        <div>
          <p className="text-xs uppercase text-muted-foreground">Experiment</p>
          <h3 className="text-lg font-semibold">{experiment.model_type}</h3>
          <p className="text-xs text-muted-foreground">
            {experiment.task_type} · target = {experiment.target_column}
            {primaryMetric ? ` · ranked by ${primaryMetric}` : ""}
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
        {cvMean !== null && nSplits !== null && (
          <div className="rounded-md border bg-muted/30 px-3 py-2 text-sm">
            <span className="text-xs uppercase text-muted-foreground">
              {Math.round(nSplits)}-fold CV ·{" "}
              {primaryMetric ?? "primary metric"}
            </span>
            <div className="mt-0.5 font-mono text-base">
              μ = {cvMean.toFixed(4)}
              {cvStd !== null ? ` ± ${cvStd.toFixed(4)}` : ""}
            </div>
          </div>
        )}
        <dl className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
          {numericPairs.map(({ key, mean, std }) => (
            <div key={key}>
              <dt className="text-xs uppercase text-muted-foreground">{key}</dt>
              <dd className="font-mono">
                {mean.toFixed(4)}
                {std !== null ? (
                  <span className="text-muted-foreground">
                    {" "}
                    ± {std.toFixed(4)}
                  </span>
                ) : null}
              </dd>
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
