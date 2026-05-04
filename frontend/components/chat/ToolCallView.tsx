"use client";

import { useState } from "react";

import { ChartRenderer } from "@/components/charts/ChartRenderer";
import type { ChartSpec, ChatToolCall } from "@/lib/types";

function isChartSpec(v: unknown): v is ChartSpec {
  if (!v || typeof v !== "object") return false;
  const o = v as Record<string, unknown>;
  return (
    typeof o.type === "string" &&
    typeof o.title === "string" &&
    Array.isArray(o.series)
  );
}

export function ToolCallView({ call }: { call: ChatToolCall }) {
  const [open, setOpen] = useState(false);

  // plot_chart returns a ChartSpec directly as the result.
  if (call.name === "plot_chart" && isChartSpec(call.result)) {
    return (
      <div className="rounded-md border bg-muted/30 p-3 space-y-2">
        <div className="flex items-center justify-between text-xs">
          <span className="font-mono text-muted-foreground">
            tool: {call.name}
          </span>
        </div>
        <ChartRenderer spec={call.result} />
      </div>
    );
  }

  return (
    <div className="rounded-md border bg-muted/30 p-3">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between text-left text-xs"
      >
        <span className="font-mono text-muted-foreground">
          tool: {call.name}
          {call.error ? " — failed" : ""}
        </span>
        <span className="text-muted-foreground">{open ? "▾" : "▸"}</span>
      </button>
      {open && (
        <div className="mt-2 space-y-2">
          {call.args !== undefined && (
            <details>
              <summary className="cursor-pointer text-xs font-medium uppercase text-muted-foreground">
                args
              </summary>
              <pre className="overflow-x-auto whitespace-pre-wrap rounded bg-background p-2 text-xs">
                {JSON.stringify(call.args, null, 2)}
              </pre>
            </details>
          )}
          {call.result !== undefined && !call.error && (
            <details>
              <summary className="cursor-pointer text-xs font-medium uppercase text-muted-foreground">
                result
              </summary>
              <pre className="overflow-x-auto whitespace-pre-wrap rounded bg-background p-2 text-xs">
                {JSON.stringify(call.result, null, 2)}
              </pre>
            </details>
          )}
          {call.error && (
            <p className="text-xs text-destructive">{call.error}</p>
          )}
        </div>
      )}
    </div>
  );
}
