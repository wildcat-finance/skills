# Wildcat accrual and state-update specification

## Source bundle

This bundle preserves the receipted #2088 study, runbook and selected design record as exact byte copies, with the 28 selection reports and the probe that wrote them. `study.md` has SHA-256 `86bfb87324bb2e3292de19b6821c11b73292fe07d5d27a31769687342f326d85`, `runbook.md` `3685f911e93084e43e0cc3c93cf2431626f8a56b2b7d842f5995bc98addadb2f` and `design-evidence.json` `0b1f75f607b65713394d90fc75be442bf946e0cf3b0c243c5318550914936bbc`. Each report under `design/reports/` carries the digest the design record declares for it. The controller state stays local and is not in this bundle.

## Selection evidence

`design/accrual_probe.py` runs the four candidate row shapes over logs constructed in the pinned V1 and V2 market emission order with the repository's fixture helpers. It models row shapes and does not establish product conformance. Every report records its command with the probe's original path, `.hexaemeron/design/accrual_probe.py`. To reproduce a report at Skills `1fc995e72cc61267273abd8339a9c1fb2289b068`, run this copy from an empty working directory with the report's own `--candidate`, `--criterion` and `--report` values; the report path is relative to that directory and must not exist.

## Runners and delivered steps

Run from the repository root with Python `3.14.6`:

```sh
python3 plugins/tabularium/tests/emit_wildcat_accrual_report.py --step 2 --report .hexaemeron/steps/2/focused.json
python3 plugins/tabularium/tests/prove_wildcat_accrual.py --candidate abi-named-amounts --criterion semantic-conformance --report .hexaemeron/design/reports/abi-named-amounts-semantic-conformance.json
```

Each interface puts its own directory first on `sys.path` before it imports `plugins/tabularium/tests/wildcat_accrual_reports.py`, so it runs under `python3 -P` and under the `PYTHONSAFEPATH=1` that Elenchus sets. The first command runs one Step's focused classes in process and writes `unittest-json-v1` with actual test, failure, error and skip counts to a fresh path under `.elenchus/` or `.hexaemeron/`. Steps 1 and 2 declare their classes; Steps 3 and 4 refuse until theirs land. The second accepts the twelve candidate and criterion pairs the design record leaves pending. The `abi-named-amounts` `semantic-conformance` and `schema-parity` criteria resolve; the other ten refuse with exit 2 and no report.

Step 1 added the two registered interfaces, that implementation module, the focused tests in `plugins/tabularium/tests/test_wildcat_accrual_scaffold.py` and this bundle. Step 2 gave `InterestAndFeesAccrued(uint256,uint256,uint256,uint256,uint256,uint256)` and `StateUpdated(uint256,bool)` their native meaning in both generations, with the four `.v1` rules and the schema branches. Not implemented yet: the constructed accrual specimens of Step 3 and the retained-conformance check of Step 4.

## Evidence limits

The public record of this run carries retained-release identifiers, digests and pass or refuse results only. No count derived from the retained releases appears here, in a committed report or in a pull request body. No staging path, raw payload or credential is in this bundle.

The selected decision and the three rejected candidates are recorded in `adr/give-wildcat-accrual-and-state-update-events-native-meaning`, numberless until integration assigns it. `runbook.md` defines the remaining Step gates.
