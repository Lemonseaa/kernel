# Quant Business Line

The quant line is the first serious validation path because it has historical data, repeatable backtests, explicit metrics, and a clear paper-trading gate.

## Current Direction

```text
historical data
  -> backtest run
  -> workflow evidence
  -> baseline/candidate comparison
  -> evidence report
  -> paper-trading recommendation
```

## Current Drill

```bash
checkpointai evidence quant-drill --candidates 30 --comparisons 5
```

This is a deterministic semi-real drill. It validates the evidence chain; it is not a live trading signal.

## Next Step

R2.1 should connect real historical data through CSV or exported backtest results before adding new framework features.

## Reports

Historical drill and acceptance reports live in [reports/](reports/). They are audit records, not the active roadmap.
