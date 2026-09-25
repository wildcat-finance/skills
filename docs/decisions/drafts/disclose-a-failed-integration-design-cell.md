# Decision: Disclose a failed integration design cell instead of amending it

## Status

Accepted, 2026-09-21, for the #1524 study. Step 1 publishes it in the canonical numberless draft home. It has no ADR number. It extends ADR-061 and edits none of its bytes.

## Context

A `protasis-design-evidence/v1` record may carry a conformance cell due at the `integration` transition. The record is digest-pinned at `done study`, re-checked at every later transition, and reachable by no `hexctl amend` subcommand. When the collected data fails such a cell, `design_evidence.py` returns D008 at the final `done merge-step`, `done integrate` is unreachable, and the operator lands the step stack by hand. The skills#1298 run did so on 2026-09-10 with its halt disclosed in pull request #1525. ADR-061 reserved "a separate future design-amendment transition" and required that it "preserve that history rather than weakening this lock".

The same run recorded a second fault: a resolver whose `--report` path equals the path of the closed `protasis-design-report/v1` object overwrites that object when run as written.

## Decision

1. A failed `integration`-due cell of the selected candidate is disclosed, not amended. Protasis owns `protasis-design-disclosure/v1`: one closed object binding the cell to the receipted record digest, the failing report's path and digest, the observed value, and the locked comparator and threshold, with a bounded reason. `design_evidence.py --transition integration --disclosure <path>` withholds that cell's D008, lists it under a receipt field `disclosed`, leaves every other D008 standing, and refuses a malformed, misplaced or mismatched disclosure under D009. Without the flag the checker is unchanged.
2. Fiat receipts the route. `hexctl disclose design --cell <candidate>/<criterion> --report <path> --reason <text>` writes the disclosure below `.hexaemeron/`, appends it to `receipts.study.design_evidence.disclosures`, and commits a `design:disclose` event. The final `done merge-step` passes the recorded disclosures to the checker and receipts the disclosed cells; `verify` replays them; `done integrate` requires a `## Design evidence` section in the run pull request body with exactly one row per disclosed cell and refuses any mismatch. The record bytes, report bytes, runbook `design-lock` block and every earlier receipt are unchanged.
3. A cell due at `step:N` is not disclosable; it keeps the fail-closed behaviour of ADR-061. A threshold is never lowered or tightened inside a run.
4. Protasis ships `design_report.py`, which runs a resolver with a list argv and writes the closed report object to an `--out` path that must not exist and must not equal any argv element.

The reference procedure and its measured results are committed under `plugins/hexaemeron/docs/fiat-design-cell-disclosure/`: `design/probe.py`, `design-evidence.json` and the 28 reports under `design/reports/`, where the record's own report paths resolve; the selection rule is `unique-frontier`.

## Alternatives

- **`halt-as-today`:** the operator halts with a free-text reason and lands the stack by hand. It leaves no structured record of the failed cell and never reaches `done integrate`; it fails `failed-cell-on-ledger` and `integrate-reachable`.
- **`threshold-amendment`:** an append-only sidecar lowers the threshold after the data is seen and the cell is re-resolved. The record bytes hold, but the verdict is computed against a value the study did not lock; it fails `locked-threshold-governs`.
- **`floor-then-tighten`:** the study locks a floor it knows is too low and a later step tightens it. With data 0 the floor fails, with data 1 the tighten fails, and neither verdict uses the locked value; it fails `locked-threshold-governs`, `failed-cell-on-ledger` and `integrate-reachable`.

## Consequences

A run whose integration cell fails on evidence records the failure against the threshold the study locked, reaches `done integrate` through the existing closure receipt, and repeats the disclosure where the next study reads it. The cost measured on the probe fixture is 1,768 bytes of state, ledger and disclosure per disclosed cell against 365 for a halt, and 80 ms against 77 ms. One command, one checker flag, one refusal code, one receipt field, one ledger event and one body section are added; no receipt field is inferred for a run without the contract marker, and `halt` and `reset` are unchanged.

Not covered: a cell due at `step:N`, closure of the task issue on a halted run (skills#1713), the semantics of a `minimise` cell reporting a bare pass (skills#1534), and any relief for the skills#1298 run, whose ledger ended at step 4. Number assignment belongs to integration against the actual base; the standing home until then is `docs/decisions/drafts/disclose-a-failed-integration-design-cell.md`.
