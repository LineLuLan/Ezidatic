"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ApiError, api } from "@/lib/api-client";
import type {
  PipelineLog,
  PreprocessingRunResponse,
  StepRequest,
} from "@/lib/types";

export function usePipelineLogs(id: string) {
  return useQuery<PipelineLog[], ApiError>({
    queryKey: ["preprocessing", id, "logs"],
    queryFn: () => api<PipelineLog[]>(`/api/v1/preprocessing/${id}/logs`),
    enabled: !!id,
  });
}

export function useRunPipeline(id: string) {
  const qc = useQueryClient();
  return useMutation<PreprocessingRunResponse, ApiError, StepRequest[]>({
    mutationFn: (steps) =>
      api<PreprocessingRunResponse>(`/api/v1/preprocessing/${id}/run`, {
        method: "POST",
        body: JSON.stringify({ steps }),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["preprocessing", id, "logs"] });
      qc.invalidateQueries({ queryKey: ["eda", id] });
      qc.invalidateQueries({ queryKey: ["datasets", id] });
    },
  });
}
