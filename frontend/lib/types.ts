/**
 * Shared types — these MUST mirror the Pydantic schemas in
 * backend/app/schemas/. When backend adds a field, update both.
 */

export type ChartType =
  | "bar"
  | "line"
  | "scatter"
  | "histogram"
  | "heatmap"
  | "pie"
  | "boxplot";

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

export interface PipelineLog {
  id: string;
  dataset_id: string;
  step_name: string;
  step_order: number;
  params: Record<string, unknown> | null;
  applied_changes: Record<string, unknown> | null;
  created_at: string;
}

export interface StepRequest {
  step: string;
  params: Record<string, unknown>;
}

export interface PreprocessingRunResponse {
  dataset_id: string;
  transformed_path: string;
  row_count: number;
  column_count: number;
  logs: PipelineLog[];
}

export type TaskType = "classification" | "regression";
export type ImputationStrategy = "median" | "mean" | "zero";
export type Metric = "accuracy" | "f1_macro" | "roc_auc" | "r2";

export interface TrainRequest {
  dataset_id: string;
  target_column: string;
  task_type: TaskType;
  background?: boolean;
  imputation?: ImputationStrategy;
  // Q5-ML-04: undefined → BE defaults to accuracy/r2 by task.
  metric?: Metric;
}

export interface LeaderboardEntry {
  name: string;
  // Q5-ML-03: metrics dict now carries cv_mean / cv_std plus a
  // `primary_metric` label (string) and `n_splits` (int) alongside the
  // numeric metric values, so the type is loose.
  metrics: Record<string, unknown>;
  train_time_sec: number;
  feature_importance: Record<string, number> | null;
}

export interface TrainResponse {
  dataset_id: string;
  task_type: TaskType;
  target_column: string;
  leaderboard: LeaderboardEntry[];
  best: LeaderboardEntry | null;
  artifact_path: string | null;
  extras: Record<string, unknown>;
}

export interface ExperimentOut {
  id: string;
  dataset_id: string;
  target_column: string;
  task_type: string;
  model_type: string;
  metrics: Record<string, unknown> | null;
  hyperparams: Record<string, unknown> | null;
  artifact_path: string | null;
  created_at: string;
}

export type ChatRole = "user" | "assistant" | "tool" | "system";

export type ChatIntent = "sql" | "ml" | "eda" | "explain" | "small_talk";

export interface ChatSession {
  id: string;
  title: string | null;
  dataset_id: string | null;
  created_at: string;
}

export interface ChatToolCall {
  name: string;
  args?: Record<string, unknown>;
  result?: Record<string, unknown>;
  error?: string;
  provider?: string;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: ChatRole;
  content: string | null;
  tool_calls?: ChatToolCall[] | null;
  token_usage?: Record<string, unknown> | null;
  provider_used?: string | null;
  created_at: string;
}

export type ChatStreamEvent =
  | { type: "intent"; value: ChatIntent }
  | { type: "delta"; text: string }
  | { type: "tool_calls"; data: ChatToolCall[] }
  | {
      type: "done";
      content: string;
      tool_calls: ChatToolCall[];
      provider_used: string | null;
      token_usage: Record<string, unknown> | null;
      intent: ChatIntent;
    }
  | { type: "saved" }
  | { type: "error"; message: string };
