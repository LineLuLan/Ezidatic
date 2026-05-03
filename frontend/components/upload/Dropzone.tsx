"use client";

import { useRef, useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { useUploadDataset } from "@/lib/hooks/useDatasets";

const ACCEPT = ".csv,.tsv,.xlsx,.xls";

export function Dropzone() {
  const upload = useUploadDataset();
  const [over, setOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = (file: File) => {
    upload.mutate(file);
  };

  return (
    <div className="space-y-3">
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setOver(true);
        }}
        onDragLeave={() => setOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setOver(false);
          const file = e.dataTransfer.files?.[0];
          if (file) handleFile(file);
        }}
        disabled={upload.isPending}
        className={
          "flex h-48 w-full cursor-pointer items-center justify-center rounded-md border-2 border-dashed text-sm transition-colors disabled:cursor-not-allowed disabled:opacity-60 " +
          (over
            ? "border-primary bg-accent text-foreground"
            : "border-border text-muted-foreground hover:bg-accent/50")
        }
      >
        {upload.isPending ? (
          <span>Uploading… (parsing + profiling)</span>
        ) : (
          <span>
            Drop a CSV / TSV / Excel file here, or <span className="underline">browse</span>
          </span>
        )}
      </button>
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPT}
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
          e.target.value = "";
        }}
      />
      {upload.isError && (
        <Alert variant="destructive">
          <AlertDescription>{upload.error?.message ?? "Upload failed"}</AlertDescription>
        </Alert>
      )}
    </div>
  );
}
