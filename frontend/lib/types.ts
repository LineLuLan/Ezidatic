/**
 * Shared types — these MUST mirror the Pydantic schemas in
 * backend/app/schemas/. When backend adds a field, update both.
 */

export type ChartType = "bar" | "line" | "scatter" | "histogram" | "heatmap" | "pie";

export interface AxisSpec {
  key: string;
  label: string;
  type: "category" | "numeric" | "time";
}

export interface SeriesSpec {
  name: string;
  data: Array<Record<string, unknown>>;
}

export interface ChartSpec {
  type: ChartType;
  title: string;
  x_axis: AxisSpec;
  y_axis: AxisSpec;
  series: SeriesSpec[];
  metadata?: Record<string, unknown>;
}

export interface ColumnProfile {
  name: string;
  dtype: string;
  null_count: number;
  unique_count: number;
  sample_values?: unknown[];
  stats?: {
    min: number;
    max: number;
    mean: number;
    std: number;
  };
}

export interface DatasetProfile {
  row_count: number;
  column_count: number;
  columns: ColumnProfile[];
}

export interface Dataset {
  id: string;
  original_name: string;
  file_format: string | null;
  file_size: number | null;
  status: "pending" | "ready" | "failed";
  row_count: number | null;
  column_count: number | null;
  created_at: string;
}

export type ChatRole = "user" | "assistant" | "tool" | "system";

export interface ChatMessage {
  id: string;
  session_id: string;
  role: ChatRole;
  content: string | null;
  tool_calls?: Record<string, unknown>[];
  provider_used?: string | null;
  created_at: string;
}
