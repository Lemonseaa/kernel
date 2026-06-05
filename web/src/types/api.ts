export type HealthReport = {
  overall_status: string;
  checks?: Array<{ component: string; status: string; message: string }>;
  recommendations?: string[];
};

export type ConsoleSnapshot = {
  scope: { scenario_id?: string | null; allow_cross_scenario: boolean; reason?: string | null };
  scenario_count: number;
  active_scenario_count: number;
  archived_scenario_count: number;
  recent_run_count: number;
  failed_run_count: number;
  pending_approval_count: number;
  scenarios: ScenarioSummary[];
  latest_runs: RunSummary[];
  pending_items: ApprovalItem[];
  operator_summary: string;
};

export type ScenarioSummary = {
  scenario_id: string;
  name: string;
  status: string;
  adapter_type: string;
  business_line_id?: string | null;
  domain_tags: string[];
};

export type Scenario = {
  id: string;
  name: string;
  description: string;
  adapter_type: string;
  business_line_id?: string | null;
  status: string;
  metadata: Record<string, unknown>;
  created_at?: string;
};

export type ApprovalItem = {
  id: string;
  scenario_id: string;
  item_type: string;
  source_id: string;
  title: string;
  summary: string;
  status: string;
  recommended_action: string;
  created_at: string;
  detail?: Record<string, unknown> | null;
};

export type RunSummary = {
  run_id: string;
  scenario_id: string;
  task: string;
  status: string;
  value_summary?: string;
  failed_summary?: string;
  metrics: Record<string, unknown>;
  created_at: string;
};

export type RunDetail = {
  run_id: string;
  scenario_id: string;
  task: string;
  status: string;
  metrics: Record<string, unknown>;
  value_summary: string;
  core_questions: Record<string, string>;
};

export type AdapterDescription = {
  name: string;
  supported_task_types: string[];
  capabilities: Record<string, unknown>;
};

export type BackupRecord = {
  id: string;
  label: string;
  path: string;
  created_at: string;
};

export type RestoreResult = {
  id: string;
  restored: boolean;
  pre_restore_backup_id?: string | null;
};

export type TriggerRunPayload = {
  scenario_id: string;
  task: string;
  context: Record<string, unknown>;
  config?: Record<string, unknown>;
};

export type TriggerRunResult = {
  scenario_id: string;
  run_id: string;
  task: string;
  status: string;
  metrics: Record<string, unknown>;
  value_summary: string;
  answer: string;
};

export type ReportResponse = {
  report: string;
};

export type ShadowResult = {
  id: string;
  proposal_id: string;
  scenario_id: string;
  agent_id: string;
  run_id: string;
  is_shadow: boolean;
  status: string;
  passed: boolean;
  answer: string;
  value_summary: string;
  baseline_metrics: Record<string, unknown>;
  shadow_metrics: Record<string, unknown>;
  metric_diff: Record<string, number>;
  business_metric_diff: Record<string, number>;
  run_kind: string;
  provenance: Record<string, unknown>;
  error_type?: string | null;
  created_at: string;
};

export type TriggerShadowPayload = {
  proposal_id: string;
  task: string;
  context: Record<string, unknown>;
  config?: Record<string, unknown>;
};
