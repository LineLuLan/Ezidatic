"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { LogViewer } from "@/components/preprocessing/LogViewer";
import { STEP_OPTIONS, StepEditor } from "@/components/preprocessing/StepEditor";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  usePipelineLogs,
  useRunPipeline,
} from "@/lib/hooks/usePreprocessing";
import type { StepRequest } from "@/lib/types";

interface DraftStep {
  step: StepRequest;
  paramsText: string;
}

function makeDraft(stepName: string): DraftStep {
  const known = STEP_OPTIONS.find((s) => s.name === stepName);
  const paramsText = known?.defaultParams ?? "{}";
  return {
    step: { step: stepName, params: safeParse(paramsText) },
    paramsText,
  };
}

function safeParse(text: string): Record<string, unknown> {
  try {
    return text.trim() ? JSON.parse(text) : {};
  } catch {
    return {};
  }
}

export default function PreprocessingPage({
  params,
}: {
  params: { id: string };
}) {
  const [drafts, setDrafts] = useState<DraftStep[]>(() => [
    makeDraft("handle_missing"),
  ]);

  const logs = usePipelineLogs(params.id);
  const run = useRunPipeline(params.id);

  const parseErrors = useMemo(
    () =>
      drafts.map((d) => {
        const text = d.paramsText.trim();
        if (!text) return null;
        try {
          JSON.parse(text);
          return null;
        } catch (e) {
          return e instanceof Error ? e.message : "Invalid JSON";
        }
      }),
    [drafts],
  );

  const hasParseError = parseErrors.some(Boolean);

  function update(idx: number, step: StepRequest, paramsText: string) {
    setDrafts((prev) => {
      const next = [...prev];
      next[idx] = { step, paramsText };
      return next;
    });
  }

  function remove(idx: number) {
    setDrafts((prev) => prev.filter((_, i) => i !== idx));
  }

  function addStep() {
    setDrafts((prev) => [...prev, makeDraft(STEP_OPTIONS[0].name)]);
  }

  async function submit() {
    const payload: StepRequest[] = drafts.map((d) => ({
      step: d.step.step,
      params: safeParse(d.paramsText),
    }));
    await run.mutateAsync(payload);
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
        <h1 className="text-2xl font-semibold">Preprocessing pipeline</h1>
        <p className="text-sm text-muted-foreground">
          Each step runs in order. Output of step #N is the input of step #N+1.
        </p>
      </div>

      <Card>
        <CardContent className="space-y-4 p-6">
          <div className="space-y-3">
            {drafts.map((d, idx) => (
              <StepEditor
                key={idx}
                index={idx}
                step={d.step}
                paramsText={d.paramsText}
                onChange={(step, text) => update(idx, step, text)}
                onRemove={() => remove(idx)}
                parseError={parseErrors[idx]}
              />
            ))}
          </div>

          <div className="flex items-center justify-between">
            <Button type="button" variant="outline" onClick={addStep}>
              + Add step
            </Button>
            <Button
              type="button"
              onClick={submit}
              disabled={run.isPending || drafts.length === 0 || hasParseError}
            >
              {run.isPending ? "Running…" : "Run pipeline"}
            </Button>
          </div>

          {run.isError && (
            <Alert variant="destructive">
              <AlertDescription>{run.error?.message}</AlertDescription>
            </Alert>
          )}

          {run.isSuccess && run.data && (
            <Alert>
              <AlertDescription>
                Pipeline completed. Transformed dataset: {run.data.row_count}{" "}
                rows × {run.data.column_count} columns. Saved to{" "}
                <code className="font-mono text-xs">
                  {run.data.transformed_path}
                </code>
                .
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      <section className="space-y-2">
        <h2 className="text-sm font-medium text-muted-foreground">
          Audit log
        </h2>
        {logs.isLoading && (
          <p className="text-sm text-muted-foreground">Loading logs…</p>
        )}
        {logs.isError && (
          <Alert variant="destructive">
            <AlertDescription>{logs.error?.message}</AlertDescription>
          </Alert>
        )}
        {logs.data && <LogViewer logs={logs.data} />}
      </section>
    </div>
  );
}
