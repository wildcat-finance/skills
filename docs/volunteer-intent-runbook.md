# Runbook: distinguish Wave, frontier and maintenance volunteer intent

## Step 1: Record the volunteer-intent boundary

**Goal.** Commit the accepted study and runbook with one standing ADR that fixes volunteer-intent ownership, handoff evidence, public claim recovery and refusal semantics without implementing a selector.

**Entry.** Run branch `fiat/447-distinguish-wave-frontier-and-maintenance-vo` at `ab611eb96a6a9bddecb57bff2416641296e0a21e`, with the study receipt and ready marketplace receipt recorded, no tracked run changes, and `ADR-035` unused in the pinned tree.

**Exit.** `docs/volunteer-intent-study.md` and `docs/volunteer-intent-runbook.md` exactly match their receipted `.hexaemeron/` sources. `docs/decisions/ADR-035-bind-volunteer-selection-to-an-explicit-intent-handoff.md` chooses the two-sided `wildcat-volunteer-intent/v1` handoff, gives named issues precedence, keeps lane selection with Atlas, Kronos or the bounded maintenance caller, makes a structured contributor comment the canonical early claim with explicit release recovery, and demonstrates all four intent kinds plus the required refusal cases. Prove exact copies with `cmp`; prove both specifications with Protasis; prove the standing record with Hypomnema; run Imprimatur and Brevitas on the changed prose; run `python3 -m unittest discover -s tests`; and finish with `git diff --check`.

**Files.** Create `docs/volunteer-intent-study.md`, `docs/volunteer-intent-runbook.md` and `docs/decisions/ADR-035-bind-volunteer-selection-to-an-explicit-intent-handoff.md`.

**Tests.** Add no runtime test because no executable selector ships. Validate that the ADR contains one worked case for `named-issue`, `wave`, `frontier` and `maintenance`, plus explicit refusals for unknown intent, empty or stale Wave evidence, an active claim, mature or parked frontier, unbounded maintenance, missing publication authority and Wave-suffix ordering. The current root suite has 350 tests and must remain green. Elenchus runner contract for this step: test command `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`, report format `unittest-json-v1`, report file `.elenchus/volunteer-intent-step-1.json`.

**Disciplines.** phylax: this documentation specifies future hostile-input and GitHub-write boundaries but opens no executable boundary. ephoros: none, no unattended path ships. metron: none, no runtime or performance claim ships. elenchus: any copy, specification, prose, standing-record or suite failure blocks the step and is corrected at its source. hypomnema: ADR-035 is the one standing home for the cross-repository selection and claim decision.

### Amendment -- 2026-08-25

**What changed.** Complete replacement Tests: Add no runtime test because no executable selector ships. Validate that the ADR contains one worked case for `named-issue`, `wave`, `frontier` and `maintenance`, plus explicit refusals for unknown intent, empty or stale Wave evidence, an active claim, mature or parked frontier, unbounded maintenance, missing publication authority and Wave-suffix ordering. The pinned root suite has 396 tests and must remain green. Elenchus runner contract for this step: test command `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`, report format `unittest-json-v1`, report file `.elenchus/volunteer-intent-step-1.json`.

**Why.** The exact entry command `python3 -m unittest discover -s tests` ran 396 tests on the pinned base; the baseline runbook's count of 350 was stale.

**Steps touched.** Step 1's Tests field.

**Still holding.** Step 1: entry holds; exit holds.

### Amendment -- 2026-08-25

**What changed.** Complete replacement Tests: Add no runtime test because no executable selector ships. Validate that the ADR contains one worked case for `named-issue`, `wave`, `frontier` and `maintenance`, plus explicit refusals for unknown intent, empty or stale Wave evidence, an active claim, mature or parked frontier, unbounded maintenance, missing publication authority and Wave-suffix ordering. The pinned root suite has 396 tests and must remain green. Elenchus runner contract for this step: test command `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`, report format `unittest-json-v1`, report file `.elenchus/volunteer-intent-step-1.json`.

**Why.** The study amendment for `S1-R1-01` changed the current study digest, so Fiat correctly stopped applying the prior runbook amendment bound to the superseded study receipt. The exact entry suite remains 396 tests.

**Steps touched.** Step 1's Tests field.

**Still holding.** Step 1: entry holds; exit holds.
