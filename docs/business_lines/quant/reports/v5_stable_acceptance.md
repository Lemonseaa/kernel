# V5 Stable Acceptance

V5 Stable 的定义：CheckpointAI 已经有一个可操作的控制台，能让人处理审批、触发 run、查看报告、跑 shadow、管理备份。它不是代码编辑器，也不是 workflow builder。

## 必须通过

后端：

```bash
python -m unittest discover -s tests -v
python -m ruff check checkpoint_ai tests scripts examples
python -m mypy checkpoint_ai --show-error-codes --no-incremental
```

前端：

```bash
cd web
npm run lint
npm run format:check
npm run build
npm run e2e
```

真实数据演练：

```bash
python scripts/business_lines/quant/run_v29_quant_data.py \
  --db .runtime/v5_quant_drill.db \
  --report docs/V5_REAL_DATA_DRILL_REPORT.md \
  --runs 30
```

## 控制台验收

- Approval 动作必须带 comment。
- Restore 必须输入 `RESTORE`，并返回 `pre_restore_backup_id`。
- Reports 页面能读 run/proposal 报告。
- Shadows 页面能保存 shadow result，并明确 `is_shadow=true`。
- Trigger Run 使用 adapter 声明的 supported_task_types。

## 明确不做

- 不在前端编辑 prompt 全文。
- 不在前端改 policy 规则。
- 不删除历史数据。
- 不做 Dify 式节点编排器。
- 不做 TradingAgents/CrewAI 正式适配。
