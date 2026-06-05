# V6 Stable Acceptance

## Scope

V6 stable means CheckpointAI has a visible, auditable, low-risk autonomy control layer.

It does not mean full autonomous trading, publishing, or production deployment.

## Acceptance Checklist

- [ ] V6.1 DecisionLog records approval, rejection, restore, shadow error, and queue outcomes.
- [ ] V6.2 autonomy actions require `checkpoint_id`.
- [ ] V6.3 eligibility rejects synthetic evidence, missing checkpoints, guardrail violations, unsupported safe apply, and high risk.
- [ ] V6.4 queue can pause, resume, list actions, inspect one action, and process audit-only drills.
- [ ] V6.4 Web Console exposes the Autonomy page.
- [ ] V6.5 operator feedback creates reviewable `policy_proposal` items, not automatic policy changes.
- [ ] V6.6 risk review documents explicit non-goals and residual risks.

## Verification Commands

```bash
cd /Users/lemonsea/Desktop/mas/checkpointAI
python -m unittest discover -s tests -v
python -m ruff check checkpoint_ai tests scripts examples
python -m mypy checkpoint_ai --show-error-codes --no-incremental
python -m compileall checkpoint_ai
cd web
npm run lint
npm run format:check
npm run build
npm run e2e
cd ..
git diff --check
```

## Operator Evidence Required Before V7

Before adding any real safe-apply backend in V7, run at least:

- 20 mixed synthetic/historical eligibility checks
- 5 audit-only queue drills
- 5 operator approve/reject decisions that feed `OperatorFeedbackAnalyzer`
- 1 backup restore safety drill

The output must be reviewable from the Web Console and DecisionLog.
