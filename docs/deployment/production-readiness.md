# Production Readiness

V1.0 production readiness covers automated tests, performance baselines, stress checks, and a small
security audit.

## Final Validation Commands

```bash
python -m ruff check loop_harness tests scripts
python -m mypy loop_harness --show-error-codes --no-incremental
python -m compileall -q loop_harness tests scripts
python -m unittest discover -s tests -v
python scripts/ops/benchmark.py --runs 20
python scripts/ops/stress_test.py --runs 50 --concurrency 5
python scripts/ops/security_audit.py
```

Or run the complete local acceptance suite:

```bash
python scripts/ops/final_acceptance.py
```

## Coverage

Use `coverage` when installed:

```bash
python -m coverage run -m unittest discover -s tests
python -m coverage report
```

The repository keeps the test suite on standard `unittest` so it remains dependency-light.
`python -m unittest discover -s tests -v --coverage` is not a valid standard-library unittest
command; install `coverage` and use the commands above when coverage evidence is required.

## Security Audit Scope

The V1.0 audit checks committed deployment-facing files for obvious secret markers. It is not a full
SAST replacement. Before production, also review:

- API token handling.
- Provider API key storage.
- Tool permissions.
- Shell/file-write tool access boundaries.

## Performance Baseline

`scripts/ops/benchmark.py` measures small workflow latency.

`scripts/ops/stress_test.py` runs concurrent lightweight workflows and reports failures and elapsed time.
