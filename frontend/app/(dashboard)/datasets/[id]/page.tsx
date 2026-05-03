"use client";

import Link from "next/link";

import { ColumnTable } from "@/components/datasets/ColumnTable";
import { StatusBadge } from "@/components/datasets/StatusBadge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Card, CardContent } from "@/components/ui/card";
import { useDataset } from "@/lib/hooks/useDatasets";

export default function DatasetDetailPage({ params }: { params: { id: string } }) {
  const { data, isLoading, isError, error } = useDataset(params.id);

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Loading dataset…</p>;
  }

  if (isError || !data) {
    return (
      <Alert variant="destructive">
        <AlertDescription>{error?.message ?? "Dataset not found"}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <Link href="/datasets" className="text-xs text-muted-foreground hover:underline">
          ← Back to datasets
        </Link>
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-semibold">{data.original_name}</h1>
          <StatusBadge status={data.status} />
        </div>
      </div>

      <Card>
        <CardContent className="grid grid-cols-2 gap-4 p-6 sm:grid-cols-4 text-sm">
          <Stat label="Rows" value={data.row_count ?? "-"} />
          <Stat label="Columns" value={data.column_count ?? "-"} />
          <Stat label="Format" value={data.file_format ?? "-"} />
          <Stat
            label="Uploaded"
            value={new Date(data.created_at).toLocaleString()}
          />
        </CardContent>
      </Card>

      {data.columns.length > 0 ? (
        <ColumnTable columns={data.columns} />
      ) : (
        <p className="text-sm text-muted-foreground">No column profile yet.</p>
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
