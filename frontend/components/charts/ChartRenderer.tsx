"use client";

import type { ChartSpec } from "@/lib/types";

import { renderRecharts } from "./adapters/recharts";

/**
 * Chart adapter switch. Default = Recharts. Swap to ECharts by replacing the
 * imported renderer (single-line change).
 */
export function ChartRenderer({ spec }: { spec: ChartSpec }) {
  return (
    <div className="rounded-md border p-4">
      <h3 className="mb-2 text-sm font-medium">{spec.title}</h3>
      {renderRecharts(spec)}
    </div>
  );
}
