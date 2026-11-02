# Wildcat sanctioned-account routing specification

## Source bundle

[Study](study.md), [runbook](runbook.md) and [design evidence](design-evidence.json) preserve the source-bound #2091 specification. The selected `unique-key` design adds supporting routing to existing queue and market-token transfer rows under adapter `1.3.0`. Product joins and conformance remain due in Steps 2 and 3.

The [decision](../../decisions/drafts/join-wildcat-sanctioned-account-assets.md) records complete native keys, one-to-one matching, unchanged parties and financial units, mapping-only `routing_joins`, preserved existing `join` relations and exact historical version dispatch. The canonical event envelope stays at schema 3.

The [finite selection model](design/sanctions_model.py) recomputes the 15 selection values in `reports/`. Those reports preserve their original `.hexaemeron/design/sanctions_model.py` command strings and exact digests. Run the public copy from the repository root with `--candidate unique-key --criterion exact-pairing --report .hexaemeron/public-model.json`. Model counts establish no production performance result.

## Reports

The [retained study inventory](reports/retained-inventory.json) records identifiers, digests and verified target-absence booleans for the two finite retained inputs. Absence supplies no historical positive join. Constructed positive branch specimens and retained conformance remain due in Step 3; unavailable custody refuses.

Run `python3 plugins/tabularium/tests/emit_wildcat_sanctions_report.py --step 1 --report .hexaemeron/step-1-review.json` from the repository root. The fixed `parser()` interfaces accept the nine pending candidate/criterion pairs and Steps 1, 2 and 3. Helpers own later implementations. A missing criterion refuses with exit 2 and no report. Reports preserve separate assertion, error and skipped-test counters; empty runs refuse. Retained classification distinguishes verified absence, complete exercised joins, unmatched or ambiguous targets and unavailable custody.

## Scaffold checks

The scaffold checks report confinement, occupied leaves, symlink refusals, private-error redaction, imports with reduced search paths and a foreign current directory, and dispatch with process helpers forbidden. Separate direct startup checks use `PYTHONSAFEPATH=1` and isolated Python; the focused suite runs inside the no-child sandbox. It introduces no live network operation or production mapping change.
