"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import type { ColumnProfile, TaskType } from "@/lib/types";

interface TrainFormProps {
  columns: ColumnProfile[];
  onSubmit: (input: {
    target_column: string;
    task_type: TaskType;
    background: boolean;
  }) => void;
  isPending: boolean;
}

export function TrainForm({ columns, onSubmit, isPending }: TrainFormProps) {
  const [target, setTarget] = useState<string>(columns[0]?.name ?? "");
  const [task, setTask] = useState<TaskType>("classification");
  const [background, setBackground] = useState(false);

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        if (!target) return;
        onSubmit({ target_column: target, task_type: task, background });
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
