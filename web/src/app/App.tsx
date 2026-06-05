import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "../layout/Layout";
import { DashboardPage } from "../features/dashboard/DashboardPage";
import { ApprovalDetailPage } from "../features/approvals/ApprovalDetailPage";
import { ApprovalListPage } from "../features/approvals/ApprovalListPage";
import { BackupPage } from "../features/backups/BackupPage";
import { AdapterListPage } from "../features/adapters/AdapterListPage";
import { NewRunPage } from "../features/runs/NewRunPage";
import { RunDetailPage } from "../features/runs/RunDetailPage";
import { RunListPage } from "../features/runs/RunListPage";
import { ScenarioListPage } from "../features/scenarios/ScenarioListPage";

export function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<DashboardPage />} />
        <Route path="approvals" element={<ApprovalListPage />} />
        <Route path="approvals/:id" element={<ApprovalDetailPage />} />
        <Route path="runs" element={<RunListPage />} />
        <Route path="runs/new" element={<NewRunPage />} />
        <Route path="runs/:id" element={<RunDetailPage />} />
        <Route path="backup" element={<BackupPage />} />
        <Route path="scenarios" element={<ScenarioListPage />} />
        <Route path="adapters" element={<AdapterListPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
