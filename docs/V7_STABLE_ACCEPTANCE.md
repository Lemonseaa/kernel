# V7 Stable Acceptance

V7 implements the Proposal Generation Loop. It is not an unattended execution system.

## What V7 Can Do

- Store scoped blackboard observations, safety findings, and validation summaries.
- Observe run summaries and decision logs.
- Aggregate observations before proposal generation.
- Generate patch-first prompt and parameter proposal candidates.
- Rank candidates and remove same-target conflicts.
- Run safety checks before shadow/replay scheduling.
- Schedule shadow/replay jobs without applying changes.
- Validate schema-aware comparison output.
- Store config versions, lock good versions, branch from locked versions, and roll back to locked versions.
- Manage internal Agent config per business line and role.
- Manage external Agent connection metadata.
- Keep formal user preferences separate from Hermes draft notes.

## Hard Boundaries

- V7 does not apply live changes directly.
- V7 does not use Hermes draft notes as formal constraints.
- V7 does not rewrite whole prompts by default.
- V7 does not merge observations across scenarios unless caller explicitly does so outside the V7 stores.
- Synthetic and historical validation results remain advisory.

## Acceptance Evidence

Primary test:

```bash
python -m unittest tests.test_v71_v78_learning_loop -v
```

Deterministic data drill:

```bash
python scripts/v7_learning_loop_drill.py
```

The drill seeds historical quant-like backtest summaries, runs one learning-loop tick, and prints an auditable JSON summary.
