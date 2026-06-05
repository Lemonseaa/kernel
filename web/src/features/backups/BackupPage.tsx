import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { createBackup, listBackups, restoreBackup } from "../../api/client";
import { Card } from "../../components/Card";
import { DataTable } from "../../components/DataTable";
import { EmptyState } from "../../components/EmptyState";
import { PageHeader } from "../../components/PageHeader";
import { formatDate, shortId } from "../../lib/format";
import type { BackupRecord } from "../../types/api";

export function BackupPage() {
  const queryClient = useQueryClient();
  const [label, setLabel] = useState("manual");
  const backups = useQuery({ queryKey: ["backups"], queryFn: listBackups });
  const create = useMutation({
    mutationFn: () => createBackup(label),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["backups"] })
  });
  const restore = useMutation({
    mutationFn: (id: string) => restoreBackup(id),
    onSuccess: () => queryClient.invalidateQueries()
  });

  return (
    <>
      <PageHeader
        title="Backup"
        description="Create and restore SQLite backups with explicit operator action."
      />
      <div className="mb-5">
        <Card title="Create Backup">
          <div className="flex flex-col gap-3 sm:flex-row">
            <input
              value={label}
              onChange={(event) => setLabel(event.target.value)}
              className="h-10 flex-1 rounded-md border border-border px-3 text-sm text-ink outline-none focus:border-accent"
              placeholder="Backup label"
            />
            <button
              className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
              disabled={!label.trim() || create.isPending}
              onClick={() => create.mutate()}
            >
              Create
            </button>
          </div>
        </Card>
      </div>
      <Card title="Backup History">
        {backups.data?.length ? (
          <DataTable<BackupRecord>
            rows={backups.data}
            columns={[
              { key: "id", header: "ID", render: (row) => shortId(row.id) },
              { key: "label", header: "Label", render: (row) => row.label },
              { key: "created", header: "Created", render: (row) => formatDate(row.created_at) },
              {
                key: "path",
                header: "Path",
                render: (row) => <span className="text-xs text-muted">{row.path}</span>
              },
              {
                key: "action",
                header: "Action",
                render: (row) => (
                  <button
                    className="rounded-md border border-border px-3 py-1.5 text-xs font-medium text-ink hover:bg-slate-50 disabled:opacity-50"
                    disabled={restore.isPending}
                    onClick={() => {
                      const confirmation = window.prompt(
                        `Restore backup ${row.label}? Type RESTORE to replace current persisted state.`
                      );
                      if (confirmation === "RESTORE") {
                        restore.mutate(row.id);
                      }
                    }}
                  >
                    Restore
                  </button>
                )
              }
            ]}
          />
        ) : (
          <EmptyState title="No backups" body="Create a backup before making risky changes." />
        )}
      </Card>
    </>
  );
}
