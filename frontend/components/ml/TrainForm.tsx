"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import type { ColumnProfile, Metric, TaskType } from "@/lib/types";

type ClassificationMetric = "accuracy" | "f1_macro" | "roc_auc";

interface TrainFormProps {
  columns: ColumnProfile[];
  onSubmit: (input: {
    target_column: string;
    task_type: TaskType;
    background: boolean;
    metric?: Metric;
  }) => void;
  isPending: boolean;
  // Q5-ML-04: when the latest training response surfaces
  // `extras.class_balance.imbalanced=true`, render a hint suggesting a
  // non-accuracy metric.
  imbalanceHint?: boolean;
}

export function TrainForm({
  columns,
  onSubmit,
  isPending,
  imbalanceHint = false,
}: TrainFormProps) {
  const [target, setTarget] = useState<string>(columns[0]?.name ?? "");
  const [task, setTask] = useState<TaskType>("classification");
  const [background, setBackground] = useState(false);
  const [classifMetric, setClassifMetric] =
    useState<ClassificationMetric>("accuracy");

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        if (!target) return;
        onSubmit({
          target_column: target,
          task_type: task,
          background,
          // Regression always uses r2; classification picks the radio choice.
          metric: task === "classification" ? classifMetric : "r2",
        });
      }}
      className="space-y-4"
    >
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="space-y-1">
          <Label htmlFor="target">Target column</Label>
          <select
            id="target"
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            className="w-full rounded-md border bg-background px-3 py-2 text-sm"
          >
            {columns.map((c) => (
              <option key={c.name} value={c.name}>
                {c.name} ({c.dtype})
              </option>
            ))}
          </select>
        </div>
        <div className="space-y-1">
          <Label>Task</Label>
          <div className="flex gap-3 pt-1">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="radio"
                name="task"
                value="classification"
                checked={task === "classification"}
                onChange={() => setTask("classification")}
              />
              Classification
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="radio"
                name="task"
                value="regression"
                checked={task === "regression"}
                onChange={() => setTask("regression")}
              />
              Regression
            </label>
          </div>
        </div>
      </div>
      {task === "classification" && (
        <div className="space-y-1">
          <Label>Ranking metric</Label>
          <div className="flex flex-wrap gap-3 pt-1 text-sm">
            <label className="flex items-center gap-2">
              <input
                type="radio"
                name="metric"
                value="accuracy"
                checked={classifMetric === "accuracy"}
                onChange={() => setClassifMetric("accuracy")}
              />
              accuracy
            </label>
            <label className="flex items-center gap-2">
              <input
                type="radio"
                name="metric"
                value="f1_macro"
                checked={classifMetric === "f1_macro"}
                onChange={() => setClassifMetric("f1_macro")}
              />
              f1_macro
            </label>
            <label className="flex items-center gap-2">
              <input
                type="radio"
                name="metric"
                value="roc_auc"
                checked={classifMetric === "roc_auc"}
                onChange={() => setClassifMetric("roc_auc")}
              />
              roc_auc
            </label>
          </div>
          {imbalanceHint && classifMetric === "accuracy" && (
            <p className="pt-1 text-xs text-amber-600 dark:text-amber-400">
              This dataset looks imbalanced — accuracy can be misleading.
              Consider <strong>f1_macro</strong> or <strong>roc_auc</strong>.
            </p>
          )}
        </div>
      )}
      <label className="flex items-center gap-2 text-sm text-muted-foreground">
        <input
          type="checkbox"
          checked={background}
          onChange={(e) => setBackground(e.target.checked)}
        />
        Run in background (poll the leaderboard for updates)
      </label>
      <Button type="submit" disabled={isPending || !target}>
        {isPending ? "Training…" : "Train all models"}
      </Button>
    </form>
  );
}
