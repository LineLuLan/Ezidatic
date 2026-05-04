"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { ChartRenderer } from "@/components/charts/ChartRenderer";
import { ColumnTable } from "@/components/datasets/ColumnTable";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Card, CardContent } from "@/components/ui/card";
import { useEdaCharts, useEdaProfile } from "@/lib/hooks/useEda";
import type { ChartSpec, ColumnProfile } from "@/lib/types";

function chartMatchesColumn(spec: ChartSpec, column: ColumnProfile): boolean {
  if (spec.type === "heatmap") return false;
  return (
    spec.x_axis.label === column.name ||
    spec.y_axis.label === column.name ||
    spec.title.includes(column.name)
  );
}

export default function EdaPage({ params }: { params: { id: string } }) {
  const profile = useEdaProfile(params.id);
  const charts = useEdaCharts(params.id);
  const [selected, setSelected] = useState<ColumnProfile | null>(null);

  const focusedChart = useMemo(() => {
    if (!selected || !charts.data) return null;
    return charts.data.find((c) => chartMatchesColumn(c, selected)) ?? null;
  }, [selected, charts.data]);

  if (profile.isLoading || charts.isLoading) {
    return <p className="text-sm text-muted-foreground">Loading EDA…</p>;
  }

  const error = profile.error ?? charts.error;
  if (error) {
    return (
      <Alert variant="destructive">
        <AlertDescription>{error.message}</AlertDescription>
      </Alert>
    );
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
        <h1 className="text-2xl font-semibold">EDA</h1>
      </div>

      {profile.data && (
        <Card>
          <CardContent className="grid grid-cols-2 gap-4 p-6 sm:grid-cols-3 text-sm">
            <Stat label="Rows" value={profile.data.row_count} />
            <Stat label="Columns" value={profile.data.column_count} />
            <Stat
              label="Charts"
              value={charts.data?.length ?? 0}
            />
          </CardContent>
        </Card>
      )}

      {profile.data && profile.data.columns.length > 0 && (
        <section className="space-y-2">
          <h2 className="text-sm font-medium text-muted-foreground">
            Columns — click a row for drilldown
          </h2>
          <ColumnTable
            columns={profile.data.columns}
            onSelect={(c) => setSelected(c.name === selected?.name ? null : c)}
            selectedName={selected?.name ?? null}
          />
        </section>
      )}

      {selected && (
        <Card>
          <CardContent className="space-y-4 p-6">
            <div className="flex items-baseline justify-between">
              <h3 className="text-lg font-semibold">{selected.name}</h3>
              <button
                onClick={() => setSelected(null)}
                className="text-xs text-muted-foreground hover:underline"
              >
                Clear selection
              </button>
            </div>
            <dl className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
              <DefStat label="Type" value={selected.dtype} />
              <DefStat label="Nulls" value={selected.null_count} />
              <DefStat label="Unique" value={selected.unique_count} />
              {selected.stats && (
                <>
                  <DefStat label="Min" value={selected.stats.min} />
                  <DefStat label="Max" value={selected.stats.max} />
                  <DefStat label="Mean" value={selected.stats.mean.toFixed(3)} />
                  <DefStat label="Std" value={selected.stats.std.toFixed(3)} />
                </>
              )}
            </dl>
            {focusedChart ? (
              <ChartRenderer spec={focusedChart} />
            ) : (
              <p className="text-sm text-muted-foreground">
                No chart available for this column (likely high-cardinality
                categorical or constant).
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {charts.data && charts.data.length > 0 ? (
        <section className="space-y-2">
          <h2 className="text-sm font-medium text-muted-foreground">
            All charts
          </h2>
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {charts.data.map((spec, idx) => (
              <ChartRenderer key={`${spec.type}-${idx}`} spec={spec} />
            ))}
          </div>
        </section>
      ) : (
        <p className="text-sm text-muted-foreground">
          No charts produced for this dataset yet.
        </p>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <p className="text-xs uppercase text-muted-foreground">{label}</p>
      <p className="font-medium">{value}</p>
    </div>
  );
}

function DefStat({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <dt className="text-xs uppercase text-muted-foreground">{label}</dt>
      <dd className="font-medium">{value}</dd>
    </div>
  );
}
