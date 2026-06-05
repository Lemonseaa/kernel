import axios from "axios";
import type {
  AdapterDescription,
  ApprovalItem,
  BackupRecord,
  ConsoleSnapshot,
  HealthReport,
  RunDetail,
  RunSummary,
  Scenario,
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
  const response = await api.post<{ id: string; restored: boolean }>(`/api/backups/${id}/restore`);
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
