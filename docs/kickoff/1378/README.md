# Fiat 1378 specification and scaffold

This bundle records the selected Wildcat V1/V2 canonical adapter design and Step 1's proof/report scaffold. The adapter, schema admission and release reproduction are pending implementation; the selection probes establish only their named dispatch observations.

## Retained specification

`study.md`, `runbook.md`, `design-evidence.json`, the fifteen selection reports and their fifteen observation files are exact copies of the receipted inputs. `audit-reading-index.json` preserves the checked synopsis inventory, findings, qualifications and missing historical records. `bundle.json` inventories every other file below this directory by relative path, SHA-256 and byte count.

`source-pins.json` contains the accepted corpus/tool revisions, fifteen compiler-input digests, partition identities and checked counts. `capture-admission-summary.json` contains the recovered archive/release identities and bounded capture observations. Raw captures, compiler inputs, corpus chunks, quotations and private event ledgers remain outside this bundle. Absolute paths in the frozen study identify the original local admission; they are not distributed input files.

## Run the scaffold

Run these commands from the repository root with Python `3.14.6`:

```bash
python3 plugins/tabularium/tests/prove_wildcat_v3.py --help
python3 plugins/tabularium/tests/emit_wildcat_v3_report.py --step 1 --report .elenchus/fiat-1378-step-1.json
```

The report path must be a fresh JSON file under `.elenchus/` or `.hexaemeron/`. The focused reporter runs the declared Step's tests in process and records actual assertions, errors and skips. The proof interface refuses unavailable semantic-conformance, schema-parity or release-reproduction checks. Its three candidate names and three criterion names are declarations, not passing results. The `wildcat-canonical` build command in the runbook is a proposed Step 2 interface and remains unavailable in Step 1.

## Evidence limits

The retained captures contain 1,941 V1 logs and 74,088 V2 logs. V2 includes fourteen recorded wrapper-factory deployment bindings and 172 market-token transfers with wrapper counterparties, with zero wrapper instance registry entries/epochs and no wrapper-native journal coverage. Neither capture contains a sanctioned-withdrawal routing companion. Source-bound synthetic specimens are required for those absent native contexts; capture absence supplies no semantic clearance.

The historical Lemma `0.2.1` rebuild reproduced 4,209 chunks across ten partitions and checked 3,928 quotation projections and 382 event declarations, including 249 interface declarations. The accepted mixed V1 lens input has no single exact Git commit; current Lemma-schema conformance is unestablished. Archive identity, source agreement and offline reproduction establish neither finality, complete history, settlement, borrower identity nor accounting replay. Issues [#1386](https://github.com/wildcat-finance/skills/issues/1386) and [#1387](https://github.com/wildcat-finance/skills/issues/1387) retain accounting and function-reconciliation work.

The selected decision lives at `adr/keep-wildcat-canonical-events-bound-to-native-roles`. [The runbook](runbook.md) defines the remaining gates and the decision record gives the rejected alternatives.
