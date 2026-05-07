"use client";

import type { ExperimentOut, Metric } from "@/lib/types";

interface LeaderboardProps {
  rows: ExperimentOut[];
  // Q5-ML-04 widened: classification can rank by accuracy / f1_macro /
  // roc_auc; regression keeps r2.
  primaryMetric: Metric;
  onSelect?: (row: ExperimentOut) => void;
  selectedId?: string | null;
}

function getMetric(metrics: Record<string, unknown> | null, key: string): number | null {
  if (!metrics) return null;
  const v = metrics[key];
  return typeof v === "number" ? v : null;
}

function formatMetric(v: number | null): string {
  if (v === null) return "—";
  if (Math.abs(v) >= 1000 || (Math.abs(v) > 0 && Math.abs(v) < 0.001)) {
    return v.toExponential(2);
  }
  return v.toFixed(4);
}

export function Leaderboard({
  rows,
  primaryMetric,
  onSelect,
  selectedId,
}: LeaderboardProps) {
  if (rows.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No experiments yet. Hit "Train all models" to populate.
      </p>
    );
  }

  // Sort by primaryMetric desc; rows with the metric come first.
  const sorted = [...rows].sort((a, b) => {
    const av = getMetric(a.metrics, primaryMetric) ?? -Infinity;
    const bv = getMetric(b.metrics, primaryMetric) ?? -Infinity;
    return bv - av;
  });

  return (
    <div className="overflow-x-auto rounded-md border">
      <table className="w-full text-sm">
        <thead className="bg-muted/50 text-left text-xs uppercase text-muted-foreground">
          <tr>
            <th className="px-3 py-2">#</th>
            <th className="px-3 py-2">Model</th>
            <th className="px-3 py-2 text-right">{primaryMetric}</th>
            <th className="px-3 py-2 text-right">CV ± std</th>
            <th className="px-3 py-2 text-right">Train (s)</th>
            <th className="px-3 py-2">Artifact</th>
            <th className="px-3 py-2">Run at</th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {sorted.map((row, idx) => {
            const primary = getMetric(row.metrics, primaryMetric);
            const cvMean = getMetric(row.metrics, "cv_mean");
            const cvStd = getMetric(row.metrics, "cv_std");
            const trainTime = getMetric(row.metrics, "train_time_sec");
            const isSelected = selectedId === row.id;
            return (
              <tr
                key={row.id}
                onClick={onSelect ? () => onSelect(row) : undefined}
                className={[
                  onSelect ? "cursor-pointer hover:bg-accent/50" : "",
                  isSelected ? "bg-accent" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
              >
                <td className="px-3 py-2 font-mono text-muted-foreground">
                  {idx + 1}
                </td>
                <td className="px-3 py-2 font-medium">{row.model_type}</td>
                <td className="px-3 py-2 text-right font-mono">
                  {formatMetric(primary)}
                </td>
                <td className="px-3 py-2 text-right font-mono text-xs">
                  {cvMean !== null
                    ? `${formatMetric(cvMean)} ± ${formatMetric(cvStd)}`
                    : "—"}
                </td>
                <td className="px-3 py-2 text-right font-mono">
                  {formatMetric(trainTime)}
                </td>
                <td className="px-3 py-2 text-xs">
                  {row.artifact_path ? (
                    <span className="rounded bg-emerald-100 px-1.5 py-0.5 text-emerald-700">
                      saved
                    </span>
                  ) : (
                    <span className="text-muted-foreground">—</span>
                  )}
                </td>
                <td className="px-3 py-2 text-xs text-muted-foreground whitespace-nowrap">
                  {new Date(row.created_at).toLocaleString()}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
