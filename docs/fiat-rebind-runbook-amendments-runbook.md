# Runbook: rebind runbook amendments across a study amendment

Derived from `.hexaemeron/study.md` for issue
[#1264](https://github.com/wildcat-finance/skills/issues/1264). Starting ref
`b9f8e36b8b6210bcd023a68059ecb46da3e35769` on `main`. Three steps in
dependency order: step 1 scaffolds, step 2 builds the selected design with
its guards, step 3 demonstrates and advances the ledger.

```design-lock
schema | protasis-design-evidence/v1
sha256 | cac7ad35cbda99ed8508c5e2110ef8b5adee4ebcbef12c96781097996f3d9505
candidate | verdict-rebind
```

Every step's exit runs both suites on a clean detached snapshot of the
committed head, because the run worktree itself reddens two root tests
through `.hexaemeron/design-evidence.json`, recorded in skills#1228. The
snapshot is made with `rm -rf .hexaemeron/snapshot && mkdir -p
.hexaemeron/snapshot && git archive HEAD | tar -x -C .hexaemeron/snapshot`
and every suite command below runs from that directory. Baseline on the
starting commit: root suite 1882 tests OK, hexaemeron suite 2615 of 2615.
No exit pins an unfiltered count.

## Step 1: Commit the study, runbook and draft decision record

**Goal.** Put the receipted study, this runbook and the draft decision record into the repository as the change-control boundary for the run.

**Entry.** `b9f8e36b8b6210bcd023a68059ecb46da3e35769`, the receipted `.hexaemeron/study.md` and `.hexaemeron/runbook.md`, and the uncommitted draft at `docs/decisions/drafts/rebind-runbook-amendments-on-a-holding-verdict.md`.

**Exit.** `cmp .hexaemeron/study.md docs/fiat-rebind-runbook-amendments-study.md` exit 0 and `cmp .hexaemeron/runbook.md docs/fiat-rebind-runbook-amendments-runbook.md` exit 0. `python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/fiat-rebind-runbook-amendments-study.md` exit 0 and `python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/fiat-rebind-runbook-amendments-runbook.md` exit 0. `python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-rebind-runbook-amendments-study.md docs/fiat-rebind-runbook-amendments-runbook.md docs/decisions/drafts/rebind-runbook-amendments-on-a-holding-verdict.md` exit 0. `python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs/fiat-rebind-runbook-amendments-runbook.md docs/fiat-rebind-runbook-amendments-study.md docs/decisions/drafts` exit 0. `python3 plugins/horos/skills/horos/scripts/horos.py scan . --write` and `python3 plugins/horos/skills/horos/scripts/horos.py scan . --census --write` leave `git status --short .horos` empty. On the snapshot: `python3 -m unittest discover -s tests` exit 0 and `python3 plugins/hexaemeron/tests/run_tests.py` exit 0.

**Files.** `docs/fiat-rebind-runbook-amendments-study.md`, `docs/fiat-rebind-runbook-amendments-runbook.md`, `docs/decisions/drafts/rebind-runbook-amendments-on-a-holding-verdict.md`; `.horos/census.json`, `.horos/boundary.json` and `.horos/candidates.json` if the three added files move them.

**Tests.** No test is written. The existing root suite guards Horos currency and the decision-record shape. Elenchus runner contract for any fix claimed in this step's audit:

```text
test command: python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}
report format: unittest-json-v1
expected report schema: elenchus.unittest.v1
report file: .hexaemeron/elenchus-step-1.json
```

**Disciplines.** phylax: none, the step adds three Markdown files and opens no input path, subprocess or credential. ephoros: none, nothing here runs unattended. metron: none, no performance claim. elenchus: none, no failure in hand; the runner contract above serves the audit loop. hypomnema: the draft record committed here is the decision's home, and the study and runbook copies are the change-control record.

## Step 2: Record rebind decisions at amend study and follow them in the packet

**Goal.** Make `hexctl amend study` record one retained or displaced decision per effective runbook amendment, print each one, and make the packet builders and `verify` follow the recorded chain.

**Entry.** Step 1's exit commit, with the three documents in place and both suites green on the snapshot.

**Exit.** `python3 -m unittest plugins.hexaemeron.tests.test_hexctl -k StudyAmendmentRebind` runs 3 tests, all pass; the same command on step 1's exit commit fails at least 2 of them. `python3 scripts/agent_instruction.py check --manifest tests/fixtures/agent-instruction-v1/manifest.json` exit 0 after the `SKILL.md` edit. `python3 scripts/promise_machine.py check` exit 0 after the re-pin is committed. `python3 plugins/horos/skills/horos/scripts/horos.py scan . --write` and `python3 plugins/horos/skills/horos/scripts/horos.py scan . --census --write` leave `git status --short .horos` empty. `python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/fiat/SKILL.md` exit 0. On the snapshot: `python3 -m unittest discover -s tests` exit 0 and `python3 plugins/hexaemeron/tests/run_tests.py` exit 0.

**Files.** `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`: `_study_amendment_record` and `cmd_amend_study` compute `runbook_rebinds`, one record `{amendment_sha256, from_study_sha256, to_study_sha256, decision}` per runbook amendment effective under the prior digest, `retained` when every touched step reads `entry holds; exit holds` in the new verdicts and `displaced` otherwise, printed as one line each with the step numbers and replaced field names, and carried in the study receipt's amendment entry and the `amend:study` event data; `_recover_study_amendment` compares the recomputed list with the pending one; `source_runbook_step` and `amendment_block` admit an amendment whose recorded `study_sha256`, followed through retained rebinds in study-history order, reaches the current digest; `verify_run` recomputes every list from the study and runbook histories and dies with exit 1 on a mismatch, an unknown decision value or a chain gap; a study amendment entry without the key means no rebinds. `plugins/hexaemeron/tests/test_hexctl.py`: class `StudyAmendmentRebindTests`. `plugins/hexaemeron/skills/fiat/SKILL.md`: the paragraph beginning "A broken runbook verdict blocks the current step" at byte 31724, after the last bound span ending at byte 23038, rewritten to state the rebind rule; then `python3 scripts/prove_agent_instruction_reconciliation.py reconcile --root .` applies the six mechanical passes to `tests/fixtures/agent-instruction-v1/manifest.json` and its fixture files, and the `agent_instruction` row of `tests/promise_machine_coverage.json` is re-pinned by hand as `tests/test_agent_instruction.py` requires. The `hexctl.py` re-pin chain: `tests/promise_machine_coverage.json` whole-file digest, `docs/promise-machine/obligation-gates/evaluation-run.json` re-tallied by `tests/promise_evaluation_driver.py`, `docs/promise-machine/obligation-gates/demonstration-run.json` and `demonstration-evidence.md`, then `.horos/census.json`, `.horos/boundary.json` and `.horos/candidates.json`. The `fiat-runbook-amendment` stanza is not edited; if Warden requires it, the edit and the `tests/promise_machine_id_history.json` re-pin are a runbook amendment to this step.

**Tests.** `StudyAmendmentRebindTests` in `plugins/hexaemeron/tests/test_hexctl.py`, 3 tests: one receipts a runbook amendment, applies two unrelated study amendments and asserts the `next` packet carries the same amendment bytes, two `retained` records with the chained digests sit in the ledger and `verify` exits 0; one applies a related study amendment marking the touched step broken and asserts the `displaced` record, the printed line naming the step and fields, the dropped packet bytes and the step still blocked; one builds a receipt without `runbook_rebinds` and asserts `verify` exits 0 and the packet drops the amendment as before. Each fails on step 1's exit commit. Elenchus runner contract for any fix claimed in this step's audit:

```text
test command: python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}
report format: unittest-json-v1
expected report schema: elenchus.unittest.v1
report file: .hexaemeron/elenchus-step-2.json
```

**Disciplines.** phylax: the study amendment candidate and the two receipt histories are the inputs; the printed lines carry only digests, step numbers and the closed field-name set, and `verify` recomputes the chain so an edited `state.json` is refused. ephoros: the retained and displaced lines and the `runbook_rebinds` list answer "which amendments did the last study amendment displace" and "does step N's packet still carry repair X". metron: the study's one budget, `amend study` over 500 effective amendments under 1000 milliseconds, is re-measured on the real command with a 500-item fixture inside `StudyAmendmentRebindTests` and recorded in the audit round. elenchus: three guard tests fail on the entry commit and pass on the exit, on the fix-with-a-failing-test rule. hypomnema: the decision is recorded in the draft under `docs/decisions/drafts/` committed at step 1; the rewritten `SKILL.md` paragraph is the contract home for the packet rule.

## Step 3: Demonstrate the rebind on a scratch run and advance the ledger

**Goal.** Run the demo path from study item 1 on a scratch run and record the generation row and plugin version that integration owes.

**Entry.** Step 2's exit commit, both suites green on the snapshot.

**Exit.** `python3 plugins/hexaemeron/tests/demo_rebind.py --root .hexaemeron/demo` exit 0, where the script drives `hexctl` on a scratch run through one runbook amendment and two unrelated study amendments and prints the `next` packet's amendment digest and the two `retained` records from `.hexaemeron/demo/.hexaemeron/ledger.jsonl`. `python3 -m unittest tests.test_evolution_contract tests.test_version_propagation` exit 0 with the fiat ledger at `fiat-v5.55.1` and hexaemeron at `1.6.34`. `python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/fiat/EVOLUTION.md` exit 0. `python3 plugins/horos/skills/horos/scripts/horos.py scan . --write` and `python3 plugins/horos/skills/horos/scripts/horos.py scan . --census --write` leave `git status --short .horos` empty. On the snapshot: `python3 -m unittest discover -s tests` exit 0 and `python3 plugins/hexaemeron/tests/run_tests.py` exit 0.

**Files.** `plugins/hexaemeron/tests/demo_rebind.py`, new. `plugins/hexaemeron/skills/fiat/EVOLUTION.md`: `Current version` set to `fiat-v5.55.1` and one appended `generation` row for `fiat-v5.55.1` with revision `state-shape-validation` and digest `e413d6041edb34b3807a54019489605814a591f60547755f8f66f01830f643aa`, citing skills#1264; the held issue #363 job untouched. `plugins/hexaemeron/.claude-plugin/plugin.json`, `plugins/hexaemeron/.codex-plugin/plugin.json`, `.claude-plugin/marketplace.json` and `.agents/plugins/marketplace.json`: `1.6.33` to `1.6.34`. `tests/test_version_propagation.py` line 47 and `tests/test_evolution_contract.py` lines 354 to 369: the pinned version, row and change text. `plugins/hexaemeron/README.md` and the root `README.md` name no plugin version on the starting ref, so neither is edited; `PROMISE_MACHINE.md` and `SOURCES.md` are edited only if `tests/test_evolution_contract.py` or `tests/test_version_propagation.py` fails without it. `.horos/census.json`, `.horos/boundary.json` and `.horos/candidates.json`. The version bump stays in this step because no test ties a `hexctl.py` edit to the plugin version; `tests/test_version_propagation.py` pins the number alone.

**Tests.** `tests/test_evolution_contract.py` and `tests/test_version_propagation.py` are edited to pin `fiat-v5.55.1` and `1.6.34`; no other test is written, and `demo_rebind.py` is a demonstration script, not a test. Elenchus runner contract for any fix claimed in this step's audit:

```text
test command: python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}
report format: unittest-json-v1
expected report schema: elenchus.unittest.v1
report file: .hexaemeron/elenchus-step-3.json
```

**Disciplines.** phylax: the demo script runs `hexctl` as a subprocess with an argument list and no shell, inside `.hexaemeron/demo` only. ephoros: the demo prints the two retained records and the packet digest, the same signals the on-call questions read. metron: none, the budget was measured at step 2 and this step adds no code path to `hexctl`. elenchus: none, no failure in hand. hypomnema: the `fiat-v5.55.1` row in `plugins/hexaemeron/skills/fiat/EVOLUTION.md` is the ledger home for the generation, and it cites the draft record by its path.
