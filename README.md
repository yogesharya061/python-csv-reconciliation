# CSV delivery validator and reconciliation report

**Client outcome:** replace repetitive spreadsheet comparisons with a repeatable, auditable check.

Uses only the Python standard library. Validates required columns, keys, decimal amounts and status values; identifies missing/extra orders and field changes; writes JSON and an HTML report. Original inputs are read-only. Output writes are atomic per file, and a SHA-256 fingerprint identifies the compared input pair.

## Demo
From this directory:

```bash
python reconcile.py --source data/source.csv --target data/target.csv --out output
# Expected exit code 2 means data findings, not a program crash.
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Open `output/report.html`. Expected: 6 source rows, 3 target rows, 3 source validation issues, A3 missing in target, A5 extra in target, A2 amount mismatch. A1 matches. The valid unique source total is 195.50 and target total is 201.00. These are raw amount sums, not accounting net revenue; refund sign handling is not inferred.

Exit codes: 0 clean, 2 data findings, 1 input/schema/runtime error. Schedule the command with cron, Windows Task Scheduler or your existing orchestrator and route code 2 to manual review.

## Rules

- Required columns: `order_id`, `amount`, `status`; extra columns are ignored.
- Status: paid, refunded or pending.
- Nonnegative finite decimal amount, at most two decimal places.
- Duplicate keys are flagged; only the first valid row is included. Findings make the report fail even if totals match. A first invalid row reserves its key and later occurrences are duplicates: investigate rather than silently repairing.
- Missing and changed comparisons use validated unique rows only. Invalid rows are separately visible.
- Uses memory proportional to distinct order count. For millions of keys, use a database or Spark instead.

## Suggested first-client scope

One source CSV and one target CSV, one agreed key, up to five agreed validation/comparison rules, an HTML/JSON report, installation instructions and one handover session. Confirm sample file shape, volume, locale and handling of refunds/duplicates before pricing. Excel, APIs, email notifications and scheduling setup are separate scope items.

## 90-second demo

1. Show the two input files and the intentional mismatch.
2. Run the command and explain exit code 2.
3. Open the report; point to missing, extra, changed and invalid rows.
4. Rerun to show identical output and unchanged input files.
5. Explain how the same checks would fit a client's daily delivery process.

## Validation and provenance

Self-directed portfolio demonstration using synthetic data. Four local tests passed on Python 3.12.14. A sample report is included in [evidence/report.html](evidence/report.html); download it and open it in a browser. No client engagement or measured customer savings are claimed.
