"use client";

import { useState } from "react";

interface Props {
  onFile?: (file: File) => void;
}

export function Dropzone({ onFile }: Props) {
  const [over, setOver] = useState(false);

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setOver(true);
      }}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setOver(false);
        const file = e.dataTransfer.files?.[0];
        if (file) onFile?.(file);
      }}
      className={
        "flex h-48 cursor-pointer items-center justify-center rounded-md border-2 border-dashed text-sm text-muted-foreground transition-colors " +
        (over ? "border-primary bg-accent" : "border-border")
      }
    >
      TODO Sprint 1 / M1_INGESTION — drop a CSV here or click to browse.
    </div>
  );
}
