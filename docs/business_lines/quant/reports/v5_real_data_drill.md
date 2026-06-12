# V5 Real Data Drill

V5 的目标不是新增算法，而是让控制台能用真实或半真实数据证明系统状态。每次进入 V6 前，至少跑一次这个演练。

## 演练目标

1. 生成一批带 `run_kind` 的量化 demo runs。
2. 验证 raw logs、summary logs、proposals、shadow results 都能落库。
3. 验证 Web API 能读到 runs、reports、shadows、approvals。
4. 验证恢复操作有 safety backup，审批操作有 comment。

## 命令

```bash
cd /Users/lemonsea/Desktop/mas/checkpointAI

python scripts/business_lines/quant/run_v29_quant_data.py \
  --db .runtime/v5_quant_drill.db \
  --report docs/V5_REAL_DATA_DRILL_REPORT.md \
  --runs 30

checkpointai --db .runtime/v5_quant_drill.db demo seed-console \
  --backup-dir .runtime/v5_backups

CHECKPOINTAI_API_TOKENS=dev-token \
  checkpointai --db .runtime/v5_quant_drill.db api serve \
  --host 127.0.0.1 --port 8000
```

前端启动：

```bash
cd /Users/lemonsea/Desktop/mas/checkpointAI/web
npm run dev -- --host 127.0.0.1
```

浏览器里填入 token：`dev-token`。

## 人工验收清单

- Dashboard 能看到 scenario、recent runs、pending approvals。
- Approvals 详情能看到 patch before/after，approve/reject 前必须写 comment。
- Runs 能打开最近一次 run detail。
- Reports 能查看 latest run 和 proposal report。
- Shadows 能对 demo proposal 跑 shadow，并能看到 shadow history。
- Backup restore 必须输入 `RESTORE`，恢复后 API 返回 `pre_restore_backup_id`。

## 进入 V6 前的判断

可以进入 V6 的条件：

- 30 次量化 demo run 能完成。
- 控制台 API 和 Web UI 验证通过。
- 报告能回答“为什么运行、发生了什么、改变了什么、比 baseline 好还是差”。

不能进入 V6 的条件：

- run/shadow/proposal 任一类证据查不到。
- 审批或恢复没有二次确认。
- metric comparison 又混入 system metrics，导致业务判断不干净。
