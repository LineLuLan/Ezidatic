import Link from "next/link";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatusBadge } from "@/components/datasets/StatusBadge";
import type { Dataset } from "@/lib/types";

function formatSize(bytes: number | null): string {
  if (!bytes) return "-";
  const units = ["B", "KB", "MB", "GB"];
  let v = bytes;
  let i = 0;
  while (v >= 1024 && i < units.length - 1) {
    v /= 1024;
    i++;
  }
  return `${v.toFixed(1)} ${units[i]}`;
}

export function DatasetCard({ dataset }: { dataset: Dataset }) {
  return (
    <Link href={`/datasets/${dataset.id}`} className="block">
      <Card className="transition-colors hover:bg-accent">
        <CardHeader className="space-y-2 pb-3">
          <div className="flex items-start justify-between gap-2">
            <CardTitle className="text-base truncate">{dataset.original_name}</CardTitle>
            <StatusBadge status={dataset.status} />
          </div>
        </CardHeader>
        <CardContent className="grid grid-cols-2 gap-2 text-sm text-muted-foreground">
          <div>Format: {dataset.file_format ?? "-"}</div>
          <div>Size: {formatSize(dataset.file_size)}</div>
          <div>Rows: {dataset.row_count ?? "-"}</div>
          <div>Cols: {dataset.column_count ?? "-"}</div>
        </CardContent>
      </Card>
    </Link>
  );
}
