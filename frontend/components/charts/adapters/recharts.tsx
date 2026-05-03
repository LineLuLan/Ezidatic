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

  return (
    <p className="text-sm text-muted-foreground">
      TODO: implement {spec.type} renderer
    </p>
  );
}
