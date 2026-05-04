"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { ChartSpec } from "@/lib/types";

export function renderRecharts(spec: ChartSpec) {
  const data = spec.series[0]?.data ?? [];

  if (spec.type === "histogram" || spec.type === "bar") {
    return (
      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey={spec.x_axis.key} />
          <YAxis />
          <Tooltip />
          <Bar dataKey={spec.y_axis.key} fill="hsl(var(--primary))" />
        </BarChart>
      </ResponsiveContainer>
    );
  }

  if (spec.type === "line") {
    return (
      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey={spec.x_axis.key} />
          <YAxis />
          <Tooltip />
          <Line
            type="monotone"
            dataKey={spec.y_axis.key}
            stroke="hsl(var(--primary))"
          />
        </LineChart>
      </ResponsiveContainer>
    );
  }

  if (spec.type === "scatter") {
    return (
      <ResponsiveContainer width="100%" height={320}>
        <ScatterChart>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey={spec.x_axis.key} />
          <YAxis dataKey={spec.y_axis.key} />
          <Tooltip />
          <Scatter data={data} fill="hsl(var(--primary))" />
        </ScatterChart>
      </ResponsiveContainer>
    );
  }

  if (spec.type === "heatmap") {
    return renderHeatmap(data);
  }

  return (
    <p className="text-sm text-muted-foreground">
      TODO: implement {spec.type} renderer
    </p>
  );
}

interface HeatmapCell {
  x: string;
  y: string;
  value: number | null;
}

function colorForCorrelation(v: number | null): string {
  if (v === null || Number.isNaN(v)) return "rgba(120, 120, 120, 0.08)";
  const alpha = Math.min(1, Math.abs(v));
  // Positive → red (var(--destructive)-ish), negative → blue.
  return v >= 0
    ? `rgba(220, 38, 38, ${alpha.toFixed(3)})`
    : `rgba(37, 99, 235, ${alpha.toFixed(3)})`;
}

function renderHeatmap(data: Array<Record<string, unknown>>) {
  const cells = data as unknown as HeatmapCell[];
  const xLabels: string[] = [];
  const yLabels: string[] = [];
  const cellByKey = new Map<string, number | null>();

  for (const c of cells) {
    if (!xLabels.includes(c.x)) xLabels.push(c.x);
    if (!yLabels.includes(c.y)) yLabels.push(c.y);
    cellByKey.set(`${c.x}::${c.y}`, c.value);
  }

  return (
    <div className="overflow-auto">
      <table className="border-separate border-spacing-0 text-xs">
        <thead>
          <tr>
            <th className="px-2 py-1" />
            {xLabels.map((x) => (
              <th
                key={x}
                className="px-2 py-1 text-left font-medium text-muted-foreground"
              >
                {x}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {yLabels.map((y) => (
            <tr key={y}>
              <th className="px-2 py-1 text-right font-medium text-muted-foreground">
                {y}
              </th>
              {xLabels.map((x) => {
                const value = cellByKey.get(`${x}::${y}`) ?? null;
                const display = value === null ? "—" : value.toFixed(2);
                return (
                  <td
                    key={x}
                    className="h-10 min-w-[3rem] border border-border px-2 py-1 text-center font-mono"
                    style={{ backgroundColor: colorForCorrelation(value) }}
                    title={`${y} × ${x}: ${value ?? "n/a"}`}
                  >
                    {display}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
