# Fiat #435 CARRYOVER-12 runbook: reconstruct the capture profile

This runbook derives from the receipted CARRYOVER-12 study. It constructs the
full 25-ID union on one tree before every product gate. No C1 through C11
partial tree is evidence for this run.

## Source and boundary

The CARRYOVER-12 issue comment is the sole reconstruction input. It keeps #436,
#437, and #508 outside this step and preserves ADR-017 as unrelated material.

## Step 1: Assemble and demonstrate the complete capture profile

**Goal.** Deliver the #435 pre-persistence capture profile, its closed schema,
privacy boundaries, confined writer and reporter, ADR-018, Promise coverage,
and all 25 aggregate guards without storing raw candidate content.

**Entry.** This controller's study receipt, this runbook, and current base
`411d5131ecc8f4e50f3db57deee881a56605cd38`. #436 receipt binding, #437
handover, and #508 process work are excluded.

**Exit.** One signed implementation commit contains the full 25-ID capture
profile union and `python3 -m unittest tests.test_run_observation_capture tests.test_run_observation_capture_inoculation tests.test_promise_machine_contract -v` passes with every named preflight and product gate. An audit record states every reviewed risk, finding, causal repair, structured Elenchus verdict, and bounded exception. No source study or runbook byte changes after receipt.

    python3 -m unittest tests.test_run_observation_capture tests.test_run_observation_capture_inoculation tests.test_promise_machine_contract -v

**Files.**

- Root Promise law and its generated copies.
- `schemas/promise-machine-run-observation-capture-v1.schema.json` and
  `scripts/run_observation_capture.py`.
- ADR-018 plus capture operator guidance and byte-identical study/runbook
  copies.
- Capture fixtures, source reporter, focused/inoculation tests, Promise
  coverage record, and Promise contract test.
- `audit/AUDIT.md` on Warden's stacked audit branch only.

**Tests.** Before any product command, assert all 25 IDs have one
owner/path/guard mapping, every declared product path is present, ADR-017 is
unchanged, ADR-018 exists, current study/runbook copies equal their receipt
bytes, both tails equal `2e 0a`, and no authored study/runbook byte sequence is
`5c 6e`. Assert the run base, branch start, study, runbook Entry, and controller
base are the current recorded SHA. Assert current Promise coverage binds
`sapheneia-durable-record-shape` and the three Fiat runtime rows to the current
`hexctl.py` digest.

**Tests.** After preflight, run:

    python3 -m unittest tests.test_run_observation_capture tests.test_run_observation_capture_inoculation tests.test_promise_machine_contract -v
    REPORT_PATH="$(pwd -P)/.elenchus/run-observation-capture.json"
    python3 tests/emit_run_observation_capture_report.py "$REPORT_PATH"
    python3 scripts/run_observation_capture.py check tests/fixtures/run-observation-capture/valid/accepted.json
    python3 scripts/run_observation_capture.py check tests/fixtures/run-observation-capture/valid/gap.json
    python3 scripts/run_observation_capture.py check tests/fixtures/run-observation-capture/valid/fingerprinted.json
    python3 scripts/run_observation_capture.py check tests/fixtures/run-observation-capture/invalid/raw-payload.json
    python3 scripts/run_observation_capture.py check tests/fixtures/run-observation-capture/invalid/unsafe-path.json
    python3 scripts/promise_machine.py sync --check
    python3 scripts/promise_machine.py check
    python3 scripts/promise_machine.py coverage --check
    python3 -m unittest discover -s tests
    python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py scripts tests
    python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py scripts tests
    python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md docs PROMISE_MACHINE.md
    python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/decisions/ADR-018-define-the-run-observation-capture-profile.md
    python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py docs/decisions/ADR-018-define-the-run-observation-capture-profile.md
    python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/promise-machine/run-observation-capture-v1.md
    python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py docs/promise-machine/run-observation-capture-v1.md
    python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/promise-machine/run-observation-capture-study.md
    python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py docs/promise-machine/run-observation-capture-study.md
    python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/promise-machine/run-observation-capture-runbook.md
    python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py docs/promise-machine/run-observation-capture-runbook.md
    python3 plugins/horos/skills/horos/scripts/horos.py check .
    git diff --cached --check
    git diff --check

**Audit command.** For a causal repair whose parent already contains the capture
surface, Warden runs:

    python3 plugins/hexaemeron/skills/elenchus/scripts/elenchus.py \
      --ref HEAD \
      --test-command "python3 tests/emit_run_observation_capture_report.py {report}" \
      --report-file .elenchus/run-observation-capture.json \
      --report-format unittest-json-v1

Runtime, schema, writer, and path repairs require a `guarded` result. A
reporter or test-only receipt repair may record `passed` only when two red
reproductions, a complete zero-error report, and its reason are preserved in
the audit record. Never manufacture a parent assertion failure. The direct
reporter receives the absolute `REPORT_PATH`; Elenchus receives the relative
declaration.

**Disciplines.** Phylax governs hostile candidate and reporter paths. Ephoros
governs durable outcome visibility without secret retention. Hypomnema governs
ADR-018 and the audit record. Metron does not apply. Elenchus governs causal
red-first evidence. Sapheneia shapes the new audit record without changing its
protected facts.

## Audit and carry-forward

Every audit round reviews the study risk register. A configured final-round
finding creates `435-CARRYOVER-13.md` as a full aggregate, then higher complete
packets as needed. The next Mason builds that one union before every check; it
never verifies a chain of partial trees.
