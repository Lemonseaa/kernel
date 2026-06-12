# Examples

Examples are grouped by product responsibility.

## Evidence Mainline

```text
examples/evidence/
```

Contains external workflow run JSON examples used by the Evidence Harness.

```bash
checkpointai evidence ingest examples/evidence/quant_baseline_run.json
checkpointai evidence ingest examples/evidence/quant_candidate_run.json
checkpointai evidence compare --baseline quant_baseline_001 --candidate quant_candidate_001
```

## Support Examples

```text
examples/support/
```

Small examples for currently supported package entry points.

```bash
python examples/support/quickstart.py
```

