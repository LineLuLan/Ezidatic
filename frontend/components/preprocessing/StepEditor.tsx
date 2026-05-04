"use client";

import type { StepRequest } from "@/lib/types";

const KNOWN_STEPS: ReadonlyArray<{
  name: string;
  label: string;
  defaultParams: string;
  hint: string;
}> = [
  {
    name: "handle_missing",
    label: "Handle missing values",
    defaultParams: '{\n  "strategy": "mean"\n}',
    hint: 'strategy: "mean" or "median". Non-numeric columns get "Unknown".',
  },
  {
    name: "remove_outliers",
    label: "Remove outliers (IQR)",
    defaultParams: '{\n  "iqr_factor": 1.5\n}',
    hint: "iqr_factor controls Tukey fences. Pass columns: [...] to scope.",
  },
  {
    name: "encode_categorical",
    label: "Encode categorical",
    defaultParams: '{\n  "strategy": "one_hot"\n}',
    hint: 'strategy: "one_hot" expands columns; "label" replaces with codes.',
  },
];

interface StepEditorProps {
  index: number;
  step: StepRequest;
  paramsText: string;
  onChange: (step: StepRequest, paramsText: string) => void;
  onRemove: () => void;
  parseError: string | null;
}

export function StepEditor({
  index,
  step,
  paramsText,
  onChange,
  onRemove,
  parseError,
}: StepEditorProps) {
  const known = KNOWN_STEPS.find((s) => s.name === step.step);

  return (
    <div className="rounded-md border bg-card p-4 space-y-3">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-muted-foreground">
            #{index + 1}
          </span>
          <select
            value={step.step}
            onChange={(e) => {
              const next = KNOWN_STEPS.find((s) => s.name === e.target.value);
              onChange(
                { step: e.target.value, params: step.params },
                next?.defaultParams ?? "{}",
              );
            }}
            className="rounded-md border bg-background px-2 py-1 text-sm"
          >
            {KNOWN_STEPS.map((s) => (
              <option key={s.name} value={s.name}>
                {s.label}
              </option>
            ))}
          </select>
        </div>
        <button
          type="button"
          onClick={onRemove}
          className="text-xs text-muted-foreground hover:text-destructive hover:underline"
        >
          Remove
        </button>
      </div>

      {known && (
        <p className="text-xs text-muted-foreground">{known.hint}</p>
      )}

      <div>
        <label className="mb-1 block text-xs font-medium uppercase text-muted-foreground">
          Params (JSON)
        </label>
        <textarea
          value={paramsText}
          onChange={(e) => {
            const text = e.target.value;
            try {
              const parsed = text.trim() ? JSON.parse(text) : {};
              onChange({ step: step.step, params: parsed }, text);
            } catch {
              // Keep the raw text but mark error via parseError prop;
              // committer pulls latest text and re-parses on submit.
              onChange({ step: step.step, params: step.params }, text);
            }
          }}
          rows={4}
          spellCheck={false}
          className="w-full rounded-md border bg-background p-2 font-mono text-xs"
        />
        {parseError && (
          <p className="mt-1 text-xs text-destructive">{parseError}</p>
        )}
      </div>
    </div>
  );
}

export const STEP_OPTIONS = KNOWN_STEPS;
