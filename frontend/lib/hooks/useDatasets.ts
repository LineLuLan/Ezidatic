"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ApiError, api } from "@/lib/api-client";
import type { Dataset, DatasetProfile } from "@/lib/types";

export interface DatasetDetail extends Dataset {
  columns: DatasetProfile["columns"];
  profile: Record<string, unknown> | null;
}

export function useDatasetsList() {
  return useQuery<Dataset[], ApiError>({
    queryKey: ["datasets"],
    queryFn: () => api<Dataset[]>("/api/v1/datasets"),
  });
}

export function useDataset(id: string) {
  return useQuery<DatasetDetail, ApiError>({
    queryKey: ["datasets", id],
    queryFn: () => api<DatasetDetail>(`/api/v1/datasets/${id}`),
    enabled: !!id,
  });
}

export function useUploadDataset() {
  const qc = useQueryClient();
  return useMutation<Dataset, ApiError, File>({
    mutationFn: (file) => {
      const form = new FormData();
      form.append("file", file);
      return api<Dataset>("/api/v1/datasets", { method: "POST", body: form });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["datasets"] });
    },
  });
}
