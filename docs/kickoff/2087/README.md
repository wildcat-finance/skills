# Wildcat withdrawal-batch specification

## Source bundle

This bundle preserves the receipted #2087 study, runbook and selected design record as exact byte copies, with the 32 selection reports, the four retained-closure observation files and the two probes that produced them. `study.md` has SHA-256 `2726baaa8e4cb92b24ecb0c53041d81d524543e76a124d0781556a53845b3a8b`, `runbook.md` `73ddc0fbc7683689f92c743b8ab4d7e9ab72c1e36b34ebabaa65eec3b7bcf415` and `design-evidence.json` `d13ace405808ba920cc911b4578ef133b88d7103244cbb9cf1c794478432bc6a`. Each report under `design-reports/` carries the digest the design record declares for it. The controller state stays local and is not in this bundle.

## Selection evidence

`design/batch_join_probe.py` models the four pairing rules over transactions constructed from the pinned V1 and V2 market source emission order. `design/retained_join_probe.py` rebuilt both retained raw releases in a private temporary directory and reported one boolean per candidate with raw release identifiers and canonical digests. Both are models of the pairing rule, not product conformance. The reports keep their original command identities, which name `.hexaemeron/design/`; to reproduce one, stage the probe under that path in a fresh worktree at Skills `50d71a2e8c1777f8eb26db32dd8adeadb34063bd` and run the report's command. The retained probe needs the two staging trees named by `ALEXANDRIA_WILDCAT_V1_STAGING` and `ALEXANDRIA_WILDCAT_V2_STAGING`, which are not distributed.

## Scaffold and limits

Run from the repository root with Python `3.14.6`:

```sh
python3 plugins/tabularium/tests/emit_wildcat_batch_report.py --step 1 --report .hexaemeron/steps/1/focused.json
python3 plugins/tabularium/tests/prove_wildcat_batches.py --candidate adjacent-burn --criterion semantic-conformance --report .hexaemeron/design-reports/adjacent-burn-semantic-conformance.json
```

Step 1 adds the two registered interfaces, the implementation module `plugins/tabularium/tests/wildcat_batch_reports.py`, the focused scaffold tests in `plugins/tabularium/tests/test_wildcat_batch_scaffold.py` and this bundle. The first command runs the Step 1 classes in process, with no subprocess, and writes `unittest-json-v1` with actual test, failure, error and skip counts to a fresh path under `.elenchus/` or `.hexaemeron/`. The second accepts the twelve candidate and criterion pairs the design record leaves pending and, at Step 1, refuses each with exit 2 and no report, because no criterion is implemented yet.

Not implemented at Step 1: the native mapping of `WithdrawalBatchCreated`, `WithdrawalBatchPayment`, `WithdrawalBatchExpired` and `WithdrawalBatchClosed`, the adjacent burn join, the schema branches, the constructed batch specimens and the retained-conformance check. On this tree the four signatures still carry the disposition `unsupported-canonical-meaning`. A passing scaffold establishes report truth and refusal behaviour only.

## Evidence limits

The public record of this run carries retained-release digests and pass or refuse results only. No count of logs, rows, burns or joins from the retained captures appears here, in a committed report or in a pull request body; those stay in private local reports that are never committed. No staging path, raw payload or credential is in this bundle.

The selected decision and the three rejected candidates are recorded in `adr/give-wildcat-withdrawal-batch-events-native-meaning`, numberless until integration assigns it. `runbook.md` defines the remaining Step gates.
