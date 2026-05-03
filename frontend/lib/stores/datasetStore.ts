import { create } from "zustand";

import type { Dataset } from "@/lib/types";

interface DatasetState {
  current: Dataset | null;
  setCurrent: (d: Dataset | null) => void;
}

export const useDatasetStore = create<DatasetState>((set) => ({
  current: null,
  setCurrent: (d) => set({ current: d }),
}));
