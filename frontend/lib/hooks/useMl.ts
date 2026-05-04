"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ApiError, api } from "@/lib/api-client";
import type {
  ExperimentOut,
  TrainRequest,
  TrainResponse,
} from "@/lib/types";

export function useLeaderboard(datasetId: string, pollMs?: number) {
  return useQuery<ExperimentOut[], ApiError>({
    queryKey: ["ml", datasetId, "leaderboard"],
    queryFn: () => api<ExperimentOut[]>(`/api/v1/ml/leaderboard/${datasetId}`),
    enabled: !!datasetId,
    refetchInterval: pollMs ?? false,
  });
}

export function useTrainModel(datasetId: string) {
  const qc = useQueryClient();
  return useMutation<TrainResponse, ApiError, Omit<TrainRequest, "dataset_id">>({
    mutationFn: (input) =>
      api<TrainResponse>(`/api/v1/ml/train`, {
        method: "POST",
        body: JSON.stringify({ dataset_id: datasetId, ...input }),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["ml", datasetId, "leaderboard"] });
    },
  });
}
