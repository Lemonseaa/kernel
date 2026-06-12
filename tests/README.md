# Test Layout

Tests are grouped by product responsibility.

```text
evidence/              Mainline Evidence Harness tests.
business_lines/quant/  Quant business-line validation and drills.
support/               Support modules used by reports, API, console, metrics, and safety.
legacy/                Historical compatibility tests for old platform modules.
```

The full regression command stays the same:

```bash
python -m unittest discover -s tests -q
```

Mainline evidence checks can be run separately:

```bash
python -m unittest discover -s tests/evidence -q
python -m unittest discover -s tests/business_lines/quant -q
```

