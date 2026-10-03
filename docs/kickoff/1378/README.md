# Fiat 1378 specification and scaffold

This bundle records the selected Wildcat V1/V2 canonical adapter design and Step 1's proof/report scaffold. The adapter, schema admission and release reproduction are pending implementation; the selection probes establish only their named dispatch observations.

## Retained specification

`study.md` and `runbook.md` preserve the earlier receipted specification. `study-current.md` and `runbook-current.md` are separate exact copies of the current amended specification. Each current copy retains its historical file as an exact byte prefix. `design-evidence.json`, the fifteen selection reports and their fifteen observation files remain exact copies of the receipted inputs. `audit-reading-index.json` preserves the checked synopsis inventory, findings, qualifications and missing historical records. `bundle.json` inventories every other file below this directory by relative path, SHA-256 and byte count.

`source-pins.json` contains the accepted corpus/tool revisions, fifteen compiler-input digests, partition identities and checked counts. Its historical/current specification fields bind both snapshots and their append-only relation; it also pins the Step 1 packet used for the fixture repair and unchanged registered reporter interfaces. `capture-admission-summary.json` contains the recovered archive/release identities and bounded capture observations. Raw captures, compiler inputs, corpus chunks, quotations and private event ledgers remain outside this bundle. Absolute paths in the frozen study identify the original local admission; they are not distributed input files.

## Run the scaffold

Run these commands from the repository root with Python `3.14.6`:

```bash
python3 plugins/tabularium/tests/prove_wildcat_v3.py --help
python3 plugins/tabularium/tests/emit_wildcat_v3_report.py --step 1 --report .elenchus/fiat-1378-step-1.json
```

The report path must be a fresh JSON file under `.elenchus/` or `.hexaemeron/`. The focused reporter runs the declared Step's tests in process and records actual assertions, errors and skips. The proof interface refuses unavailable semantic-conformance, schema-parity or release-reproduction checks. Its three candidate names and three criterion names are declarations, not passing results. The `wildcat-canonical` build command in the runbook is a proposed Step 2 interface and remains unavailable in Step 1.

## Fixture recovery

`step-1-fixture-recovery.json` binds six retained native unittest observations to their source and raw-output digests. The unmodified replacement-object positive control fails with inherited `GIT_NO_REPLACE_OBJECTS=1` and passes when that variable is absent. The repair removes the variable only around the fixture observation, restores it, and checks restoration before the native-object and controller reads. The repaired case passes in both environments; all twelve class tests and the separate closed-PATH check pass with inherited protection.

The original controller refusal names one failing test and a `hexaemeron-suite` exit of `1`. Its full buffered suite output was discarded, so the complete original suite totals remain unknown. These focused results establish the fixture recovery described in the current amendment. Full implementation admission and committed-tip Exit remain separate root-owned gates; no production Elenchus guarded result is claimed. Raw regression output and the driver remain local.

## Evidence limits

The retained captures contain 1,941 V1 logs and 74,088 V2 logs. V2 includes fourteen recorded wrapper-factory deployment bindings and 172 market-token transfers with wrapper counterparties, with zero wrapper instance registry entries/epochs and no wrapper-native journal coverage. Neither capture contains a sanctioned-withdrawal routing companion. Source-bound synthetic specimens are required for those absent native contexts; capture absence supplies no semantic clearance.

The historical Lemma `0.2.1` rebuild reproduced 4,209 chunks across ten partitions and checked 3,928 quotation projections and 382 event declarations, including 249 interface declarations. The accepted mixed V1 lens input has no single exact Git commit; current Lemma-schema conformance is unestablished. Archive identity, source agreement and offline reproduction establish neither finality, complete history, settlement, borrower identity nor accounting replay. Issues [#1386](https://github.com/wildcat-finance/skills/issues/1386) and [#1387](https://github.com/wildcat-finance/skills/issues/1387) retain accounting and function-reconciliation work.

The selected decision lives at `adr/keep-wildcat-canonical-events-bound-to-native-roles`. [The current runbook](runbook-current.md) defines the remaining gates and the decision record gives the rejected alternatives.
