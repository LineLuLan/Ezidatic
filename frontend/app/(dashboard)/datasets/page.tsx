"use client";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { DatasetCard } from "@/components/datasets/DatasetCard";
import { Dropzone } from "@/components/upload/Dropzone";
import { useDatasetsList } from "@/lib/hooks/useDatasets";

export default function DatasetsPage() {
  const { data, isLoading, isError, error } = useDatasetsList();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Datasets</h1>
        <p className="text-sm text-muted-foreground">
          Upload CSV, TSV, or Excel files. Profile + per-column stats run on the server.
        </p>
      </div>

      <Dropzone />

      {isError && (
        <Alert variant="destructive">
          <AlertDescription>
            {error?.message ?? "Failed to load datasets"}
          </AlertDescription>
        </Alert>
      )}

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading datasets…</p>
      ) : !data || data.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          No datasets yet. Drop a file above to get started.
        </p>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {data.map((d) => (
            <DatasetCard key={d.id} dataset={d} />
          ))}
        </div>
      )}
    </div>
  );
}
