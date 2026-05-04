"use client";

import { useQuery } from "@tanstack/react-query";

import { ApiError, api } from "@/lib/api-client";
import type { ChartSpec, DatasetProfile } from "@/lib/types";

export function useEdaProfile(id: string) {
  return useQuery<DatasetProfile, ApiError>({
    queryKey: ["eda", id, "profile"],
    queryFn: () => api<DatasetProfile>(`/api/v1/eda/${id}/profile`),
    enabled: !!id,
  });
}

export function useEdaCharts(id: string) {
  return useQuery<ChartSpec[], ApiError>({
    queryKey: ["eda", id, "charts"],
    queryFn: () => api<ChartSpec[]>(`/api/v1/eda/${id}/charts`),
    enabled: !!id,
  });
}
