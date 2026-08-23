# Observable run record runbook

This runbook implements issue #434 from `main` at
`454bf3c9930c94985e5eb6179f3b01be2bf741c2`. It changes no skill frontier,
package version, manifest, or CI workflow.

## Delivery boundary

- Step 1 publishes the accepted specification and standing decision.
- Step 2 builds, binds, hardens, documents, and demonstrates the complete v1 validator.

Every existing command surface below is checked before this runbook is
receipted. The Horos currency gate is `horos.py check .`; the known invalid
`horos.py scan . --check` spelling is not a runbook command.

## Step 1: Publish the observation specification

**Goal.** Commit byte-identical study and runbook copies, record the root
Promise Machine ownership decision in ADR-014, and refresh Horos.

**Entry.** Run branch `fiat/434-observable-run-record` at
`454bf3c9930c94985e5eb6179f3b01be2bf741c2`, with both artefacts receipted and
the controller returning this Step 1 packet.

- Evidence is limited to the receipted bytes, decision index, old failed-link
  and failed-command specimens, and named gates.

**Exit.** Tracked study and runbook bytes exactly match their receipts;
ADR-014 records the chosen ownership and rejected alternatives; source
pointers remain location-independent; the old five-link specimen yields five
H001 findings and the obsolete Horos spelling exits 2; accepted bytes and the
correct Horos command pass. Protasis, Hypomnema, Imprimatur, Brevitas, root
tests, Horos currency, and diff checks are green.

```bash
cmp .hexaemeron/study.md docs/promise-machine/run-observation-study.md
cmp .hexaemeron/runbook.md docs/promise-machine/run-observation-runbook.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/promise-machine/run-observation-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/promise-machine/run-observation-runbook.md
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/promise-machine/run-observation-study.md docs/promise-machine/run-observation-runbook.md docs/decisions/ADR-014-define-the-promise-machine-run-observation-record.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py docs/promise-machine/run-observation-study.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py docs/promise-machine/run-observation-runbook.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py docs/decisions/ADR-014-define-the-promise-machine-run-observation-record.md
python3 plugins/horos/skills/horos/scripts/horos.py check .
python3 -m unittest discover -s tests
git diff --check
```

**Files.** Create `docs/promise-machine/run-observation-study.md`,
`docs/promise-machine/run-observation-runbook.md`, and
`docs/decisions/ADR-014-define-the-promise-machine-run-observation-record.md`.
Refresh `.horos/boundary.json` only through Horos. Modify no executable,
Promise declaration, version, manifest, or CI file.

**Tests.** Run exact comparisons, both Protasis modes, Hypomnema, Imprimatur,
Brevitas, correct Horos currency, root tests, and `git diff --check`. In a
temporary directory only, reproduce the old five relative links as five H001
findings and the obsolete Horos spelling as exit 2, then remove the specimens.

**Disciplines.** phylax: bounded Markdown and generated boundary only.
ephoros: none, nothing runs unattended. metron: none, no speed claim.
elenchus: the two prior runbook failures are preserved red and their corrected
forms run green. hypomnema: ADR-014 owns the decision; study and runbook own
the accepted specification and delivery order.

## Step 2: Build and demonstrate the v1 validator

**Goal.** Add the closed event schema, bounded standard-library validator,
root Promise declaration and copies, operator documentation, valid and invalid
fixtures, combined hostile probes, and one complete demonstration.

**Entry.** Step 1's stacked branch with the accepted records and ADR published
and every Step 1 gate green.

- Evidence is limited to the accepted study, schema, validator,
  documentation, fixtures, Promise binding, tests, and named checks.

**Exit.** The validator accepts success, refusal, retry, and handoff records.
It emits stable `RO` findings for missing identity, bad order, unbound evidence,
subject/class strengthening, hidden reasoning, unsafe or unbounded input,
duplicate keys, closed-shape violations, lifecycle gaps, unsafe paths, raw
payloads, invalid optional host facts, and invalid token counts. All references
resolve backward within one run; one start and finish bound the record; unknown
facts stay non-authorising; token counts are optional and source-bound. Text
and canonical JSON share one finding model. The root Promise authorises only
structural validation, generated copies are identical, and coverage binds the
exact runtime, schema, fixtures, tests, docs, and transition.

One focused test command demonstrates all valid flows, required refusals, token
recorded/unknown cases, and combined probes: oversized final line, symlinked
input, nested duplicate keys, cross-run retry, changed handoff subject, Boolean
tokens, hidden-reasoning names at depth, truncation, and events after finish.
It does not present fixtures as captured production runs or validation as
truth, completeness, quality, cause, or mutation authority.

```bash
python3 -m unittest tests.test_run_observation -v
python3 scripts/run_observation.py check tests/fixtures/run-observation/valid/success.jsonl
python3 scripts/run_observation.py check tests/fixtures/run-observation/valid/refusal.jsonl
python3 scripts/run_observation.py check tests/fixtures/run-observation/valid/retry.jsonl
python3 scripts/run_observation.py check tests/fixtures/run-observation/valid/handoff.jsonl
python3 -m unittest discover -s tests
python3 scripts/promise_machine.py sync
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins scripts tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins scripts tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs schemas scripts
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py PROMISE_MACHINE.md docs/promise-machine/run-observation-v1.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py docs/promise-machine/run-observation-v1.md
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

Expected-refusal fixture exits are asserted by the focused unittest rather
than chained into this all-green gate list.

**Files.** Create
`schemas/promise-machine-run-observation-v1.schema.json`,
`scripts/run_observation.py`, `docs/promise-machine/run-observation-v1.md`,
`tests/test_run_observation.py`, and fixtures below
`tests/fixtures/run-observation/`. Modify `PROMISE_MACHINE.md`, its generated
plugin copies through `scripts/promise_machine.py sync`,
`tests/promise_machine_coverage.json`, and
`tests/test_promise_machine_contract.py`. Refresh `.horos/boundary.json` only
if its exact scan changes. Modify no Fiat state/ledger semantics, capture,
redaction, storage, dashboard, version, manifest, or CI file.

**Tests.** Observe missing command/schema guards red on the Step 1 parent.
Give each event and relation a minimal positive or negative fixture. Bind the
five issue acceptance faults to distinct codes; test all study bounds and
combined probes; compare text and JSON finding objects exactly. Run the
focused demonstration, root suite, Promise checks, three discipline lints,
prose gates, correct Horos command, and diff check. Record actual counts and
expected-refusal exits.

**Disciplines.** phylax: confined regular input, streaming limits, safe JSON,
duplicate keys, paths, raw payloads, and bounded diagnostics are security
boundaries. ephoros: results answer which contract/run/event refused, why, and
whether tokens were recorded or unknown. metron: safety ceilings are not
performance claims. elenchus: every accepted relationship, refusal, and
combined fault starts red and remains guarded. hypomnema: schema owns fields,
operator docs own use and overclaims, Promise law owns authority, tests own
examples, and downstream capture/redaction/binding/diagnosis remain in issues
#435, #436, and #449.
