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

  if (spec.type === "boxplot") {
    return renderBoxplot(spec);
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

interface BoxplotRow {
  column: string;
  min: number | null;
  q1: number;
  median: number;
  q3: number;
  whisker_low: number;
  whisker_high: number;
  max: number | null;
  outliers: number[];
  skew: number | null;
}

function renderBoxplot(spec: ChartSpec) {
  const data = spec.series[0]?.data ?? [];
  const row = data[0] as unknown as BoxplotRow | undefined;
  if (!row) {
    return (
      <p className="text-sm text-muted-foreground">no data</p>
    );
  }

  const lo = row.min ?? row.whisker_low;
  const hi = row.max ?? row.whisker_high;
  const span = hi - lo;
  // Guard against zero-span; fall back to 1 so we can still render a
  // marker (degenerate case — single value).
  const denom = span > 0 ? span : 1;
  const scale = (v: number) => ((v - lo) / denom) * 1000;

  const meta = (spec.metadata ?? {}) as {
    n?: number;
    outlier_count_total?: number;
    outlier_count_shown?: number;
    skew?: number | null;
  };

  const xQ1 = scale(row.q1);
  const xQ3 = scale(row.q3);
  const xMedian = scale(row.median);
  const xWLow = scale(row.whisker_low);
  const xWHigh = scale(row.whisker_high);

  const yMid = 70;
  const boxTop = 40;
  const boxBottom = 100;
  const capTop = 55;
  const capBottom = 85;

  const skewLabel =
    typeof meta.skew === "number" ? meta.skew.toFixed(2) : "n/a";

  return (
    <div className="w-full">
      <svg
        viewBox="0 0 1000 140"
        preserveAspectRatio="none"
        className="h-32 w-full"
        role="img"
        aria-label={`Boxplot of ${row.column}`}
      >
        {/* Whisker line */}
        <line
          x1={xWLow}
          x2={xWHigh}
          y1={yMid}
          y2={yMid}
          stroke="hsl(var(--primary))"
          strokeWidth={1}
          vectorEffect="non-scaling-stroke"
        />
        {/* Whisker caps */}
        <line
          x1={xWLow}
          x2={xWLow}
          y1={capTop}
          y2={capBottom}
          stroke="hsl(var(--primary))"
          strokeWidth={1}
          vectorEffect="non-scaling-stroke"
        />
        <line
          x1={xWHigh}
          x2={xWHigh}
          y1={capTop}
          y2={capBottom}
          stroke="hsl(var(--primary))"
          strokeWidth={1}
          vectorEffect="non-scaling-stroke"
        />
        {/* IQR box */}
        <rect
          x={xQ1}
          y={boxTop}
          width={Math.max(xQ3 - xQ1, 1)}
          height={boxBottom - boxTop}
          fill="hsl(var(--primary) / 0.18)"
          stroke="hsl(var(--primary))"
          strokeWidth={1}
          vectorEffect="non-scaling-stroke"
        />
        {/* Median tick */}
        <line
          x1={xMedian}
          x2={xMedian}
          y1={boxTop}
          y2={boxBottom}
          stroke="hsl(var(--primary))"
          strokeWidth={2}
          vectorEffect="non-scaling-stroke"
        />
        {/* Outlier circles */}
        {row.outliers.map((v, i) => (
          <circle
            key={`${v}-${i}`}
            cx={scale(v)}
            cy={yMid}
            r={3}
            fill="hsl(var(--destructive))"
            opacity={0.7}
          />
        ))}
      </svg>
      <p className="mt-1 text-xs text-muted-foreground font-mono">
        {row.column} · n={meta.n ?? "?"} · skew={skewLabel} · q1={row.q1.toFixed(2)} · median={row.median.toFixed(2)} · q3={row.q3.toFixed(2)} · outliers {meta.outlier_count_shown ?? row.outliers.length}/{meta.outlier_count_total ?? row.outliers.length}
      </p>
    </div>
  );
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
