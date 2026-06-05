import axios from "axios";
import type {
  AdapterDescription,
  ApiErrorEnvelope,
  ApprovalItem,
  AutonomyAction,
  AutonomyQueueStatus,
  BackupRecord,
  ConsoleSnapshot,
  HealthReport,
  ProcessAutonomyActionResult,
  ReportResponse,
  RestoreResult,
  RunDetail,
  RunSummary,
  Scenario,
  ShadowResult,
  TriggerShadowPayload,
  TriggerRunPayload,
  TriggerRunResult
} from "../types/api";

const api = axios.create({
  baseURL: import.meta.env.VITE_CHECKPOINT_API_BASE_URL ?? ""
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("checkpointai.token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export function setApiToken(token: string) {
  localStorage.setItem("checkpointai.token", token);
}

export function getApiToken() {
  return localStorage.getItem("checkpointai.token") ?? "";
}

export function getApiErrorMessage(error: unknown) {
  if (axios.isAxiosError<ApiErrorEnvelope>(error)) {
    const data = error.response?.data;
    if (data?.message) {
      return data.message;
    }
  }
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return "Request failed.";
}

export async function getSnapshot(scenarioId?: string) {
  const response = await api.get<ConsoleSnapshot>("/api/console/snapshot", {
    params: scenarioId ? { scenario_id: scenarioId } : { all_scenarios: true, reason: "web-console" }
  });
  return response.data;
}

export async function getHealth() {
  const response = await api.get<HealthReport>("/api/health");
  return response.data;
}

export async function listApprovals(scenarioId?: string) {
  const response = await api.get<ApprovalItem[]>("/api/approvals", {
    params: scenarioId ? { scenario_id: scenarioId } : undefined
  });
  return response.data;
}

export async function getApproval(id: string) {
  const response = await api.get<ApprovalItem>(`/api/approvals/${id}`);
  return response.data;
}

export async function approveItem(id: string, comment: string) {
  const response = await api.post<{ id: string; updated: boolean }>(`/api/approvals/${id}/approve`, {
    comment
  });
  return response.data;
}

export async function rejectItem(id: string, comment: string) {
  const response = await api.post<{ id: string; updated: boolean }>(`/api/approvals/${id}/reject`, {
    comment
  });
  return response.data;
}

export async function listRuns(scenarioId?: string) {
  const response = await api.get<RunSummary[]>("/api/runs", {
    params: scenarioId ? { scenario_id: scenarioId } : undefined
  });
  return response.data;
}

export async function getRun(id: string) {
  const response = await api.get<RunDetail>(`/api/runs/${id}`);
  return response.data;
}

export async function triggerRun(payload: TriggerRunPayload) {
  const response = await api.post<TriggerRunResult>("/api/runs", payload);
  return response.data;
}

export async function listBackups() {
  const response = await api.get<BackupRecord[]>("/api/backups");
  return response.data;
}

export async function createBackup(label: string) {
  const response = await api.post<BackupRecord>("/api/backups", { label });
  return response.data;
}

export async function restoreBackup(id: string) {
  const response = await api.post<RestoreResult>(`/api/backups/${id}/restore`, { confirm: "RESTORE" });
  return response.data;
}

export async function listScenarios() {
  const response = await api.get<Scenario[]>("/api/scenarios");
  return response.data;
}

export async function archiveScenario(id: string, reason: string) {
  const response = await api.post<{ id: string; archived: boolean }>(`/api/scenarios/${id}/archive`, {
    reason
  });
  return response.data;
}

export async function listAdapters() {
  const response = await api.get<AdapterDescription[]>("/api/adapters");
  return response.data;
}

export async function getLatestReport(scenarioId?: string) {
  const response = await api.get<ReportResponse>("/api/reports/latest", {
    params: scenarioId ? { scenario_id: scenarioId } : undefined
  });
  return response.data;
}

export async function getRunReport(runId: string) {
  const response = await api.get<ReportResponse>(`/api/reports/runs/${runId}`);
  return response.data;
}

export async function getProposalReport(proposalId: string) {
  const response = await api.get<ReportResponse>(`/api/reports/proposals/${proposalId}`);
  return response.data;
}

export async function listShadows(scenarioId?: string) {
  const response = await api.get<ShadowResult[]>("/api/shadows", {
    params: scenarioId ? { scenario_id: scenarioId } : undefined
  });
  return response.data;
}

export async function getShadow(id: string) {
  const response = await api.get<ShadowResult>(`/api/shadows/${id}`);
  return response.data;
}

export async function triggerShadow(payload: TriggerShadowPayload) {
  const response = await api.post<ShadowResult>("/api/shadows", payload);
  return response.data;
}

export async function listAutonomyActions(scenarioId?: string) {
  const response = await api.get<AutonomyAction[]>("/api/autonomy/actions", {
    params: scenarioId ? { scenario_id: scenarioId } : undefined
  });
  return response.data;
}

export async function getAutonomyQueueStatus() {
  const response = await api.get<AutonomyQueueStatus>("/api/autonomy/queue/status");
  return response.data;
}

export async function pauseAutonomyQueue() {
  const response = await api.post<AutonomyQueueStatus>("/api/autonomy/queue/pause");
  return response.data;
}

export async function resumeAutonomyQueue() {
  const response = await api.post<AutonomyQueueStatus>("/api/autonomy/queue/resume");
  return response.data;
}

export async function processAutonomyAction(actionId: string) {
  const response = await api.post<ProcessAutonomyActionResult>(`/api/autonomy/actions/${actionId}/process`);
  return response.data;
}
