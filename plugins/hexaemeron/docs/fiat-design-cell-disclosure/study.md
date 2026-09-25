# Study: disclose a failed integration design cell

Run `fiat/1524-integration-blocked-design-cell` for
[skills#1524](https://github.com/wildcat-finance/skills/issues/1524)
(framework-159), written 2026-09-21 against main at
`32a70f9cc3c8b14ed2001dcf9e2e7821b8c112a9`. Repository files below are pinned
to that commit; `hexctl.py` means
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py` and `design_evidence.py`
means `plugins/hexaemeron/skills/protasis/scripts/design_evidence.py`.

Assuming, unless corrected:

1. The controller that gates this run is the installed plugin `1.6.70`
   (`fiat-v6.72.1`), so nothing this run builds can be used by this run's own
   design record. Its cells are therefore ones the run can pass or resolve
   before the last merge-step.
2. Python is `3.14.6` (`.python-version`), stdlib `unittest`, no new
   dependency. The Hexaemeron suite runs only through
   `plugins/hexaemeron/tests/run_tests.py`; the root suite through
   `python3 -m unittest discover -t . -s tests`.
3. Both changed skills take generation rows, not frontier rows. Fiat's ledger
   is open at `fiat-v6.72.1` with the held job skills#1212 untouched;
   Protasis is mature at `protasis-v6.16.1` and still takes a generation row
   (its `protasis-v6.16.1` row for skills#1762 is the precedent).
4. The disclosure covers a cell due at `integration` only. A cell due at
   `step:N` keeps today's fail-closed behaviour (section 3 says why).
5. `hexctl disclose design` is the command name. If Fiat prefers another
   spelling, only the prose and the argparse registration move.

## 1. Problem statement

A `protasis-design-evidence/v1` record may carry a conformance cell whose
evidence is due at `integration`. The record is digest-pinned in
`receipts.study.design_evidence` at `done study` (`hexctl.py` line 14037 to
14058) and re-checked at every later transition
(`_checked_design_transition`, line 8041 to 8091, dies with `design-evidence
artefact digest changed`). `hexctl amend` has exactly two subcommands, `study`
and `runbook` (line 31081 to 31091). The `integration` transition is consumed
by `done merge-step` for the last step (line 19026 to 19028), so when the
collected data fails the cell the checker returns D008 (`design_evidence.py`
line 19, 572 to 585), the final merge-step never receipts, `done integrate`
is unreachable, and the operator lands the step stack by hand. The skills#1298
run did exactly that on 2026-09-10 (section 2).

The second observation from the same run: a resolver whose `--report` argument
is the path the controller expects the closed `protasis-design-report/v1`
object at cannot be run as written, because the resolver's own report shape
overwrites the object.

What is built, for the operator driving a Fiat run and for the Surveyor,
Mason and Warden who read its records:

1. A closed disclosure contract owned by Protasis. A
   `protasis-design-disclosure/v1` object binds one failing due cell of the
   selected candidate to the receipted record digest, the failing report's
   path and digest, the observed value, and the locked comparator and
   threshold, with a bounded reason. `design_evidence.py` accepts one or more
   `--disclosure <record-relative path>` flags at `--transition integration`
   only; a D008 cell with a matching disclosure is reported in a new receipt
   field `disclosed` instead of as a finding, every other D008 stays, and a
   malformed, misplaced or mismatched disclosure refuses under a new code
   D009.
2. A receipted route in Fiat. `hexctl disclose design --cell
   <candidate>/<criterion> --report <path> --reason <text>` writes the
   disclosure below `.hexaemeron/`, appends it to
   `receipts.study.design_evidence.disclosures`, and commits a
   `design:disclose` ledger event. The final `done merge-step` passes the
   recorded disclosures to the checker and receipts the `disclosed` cells;
   `verify` replays them; `next` prints the rows the run pull request body
   must carry under a `## Design evidence` heading; `done integrate` refuses
   a body whose rows do not equal the recorded disclosures. The record bytes,
   the report bytes, the runbook's `design-lock` block and every earlier
   transition receipt are unchanged.
3. A Protasis wrapper, `design_report.py`, that runs a resolver with a list
   argv and writes the closed `protasis-design-report/v1` object to an
   `--out` path that must not exist and must not equal any argv element, so
   a resolver's own `--report` output and the controller's object cannot
   share a path.

A working prototype means the checked-in controller drives a disposable
Git-backed run whose integration cell fails, and the run reaches
`done integrate` only through the disclosure. The proving demo path is
`python3 -m unittest plugins.hexaemeron.tests.test_hexctl_design_disclosure`
and `python3 -m unittest plugins.hexaemeron.tests.test_protasis_design_report`,
both printing `OK`, with the observed positive path and the six refusals
(undisclosed D008, drifted report digest, disclosure of a passing cell,
disclosure of a `step:N` cell, disclosure on a legacy state, run pull request
body rows that do not match) recorded in
`plugins/hexaemeron/docs/fiat-design-cell-disclosure/proof.md`. This run's own
controller is `1.6.70`, so its own cells never rely on the new route; its one
conformance cell is the step-3 guard module, resolved through the wrapper
before step 3's push (section 4).

## 2. Prior art

**Standing decision.**
[ADR-061](https://github.com/wildcat-finance/skills/blob/32a70f9cc3c8b14ed2001dcf9e2e7821b8c112a9/docs/decisions/ADR-061-lock-designs-with-progressive-checked-evidence.md#L64-L67)
makes the record immutable after design lock and reserves "a separate future
design-amendment transition; until then the run halts and a new run begins".
Its Consequences
([lines 107 to 111](https://github.com/wildcat-finance/skills/blob/32a70f9cc3c8b14ed2001dcf9e2e7821b8c112a9/docs/decisions/ADR-061-lock-designs-with-progressive-checked-evidence.md#L107-L111))
require that any future amendment design "must preserve that history rather
than weakening this lock". This study extends ADR-061 and edits none of its
bytes: the record stays immutable, and the new route records what the data did
against the locked threshold.
[Fiat SKILL.md lines 415 to 418](https://github.com/wildcat-finance/skills/blob/32a70f9cc3c8b14ed2001dcf9e2e7821b8c112a9/plugins/hexaemeron/skills/fiat/SKILL.md#L415-L418)
repeat the reservation; those bytes (25289 to 25598) sit inside the
agent-instruction fixture's governed range 18784 to 29736 and stay as they
are (section 3).

**Controller and checker at the starting commit.**

- `hexctl.py`: `_design_checker_receipt` (line 7955) accepts exactly the
  five receipt keys `schema, transition, selected, consumed, findings`;
  `_checked_design_transition` (8041); `_prepare_design_transition` (8130)
  refuses a transition already receipted; `done_study` (14024) receipts the
  lock; `done_push` (16023, the `step:N` call at 16073) opens the next step;
  `done_merge_step` (18879, the `integration` call at 19026); `done_integrate`
  (19550) requires the `## Carried forward` block through
  `carried_forward_fault` (6568) and `carried_forward_record` (6619);
  `cmd_halt` (30022) records only `reason` and `ts`; `verify_design_evidence`
  (30041) replays the transition spine and every consumed report digest;
  the `amend` parser (31081 to 31091).
- `design_evidence.py`: codes D000 to D008 (lines 11 to 19); `_report_findings`
  (313) turns a missing, malformed or non-zero report into D005, relabelled
  D008 for a pending cell due at the transition (344, 350, 576 to 585);
  `evaluate` (417) consumes only the selected candidate's due cells; the
  `--format receipt` output (743 onward).
- Protasis SKILL.md, "Design evidence and progressive gates"
  ([lines 290 to 374](https://github.com/wildcat-finance/skills/blob/32a70f9cc3c8b14ed2001dcf9e2e7821b8c112a9/plugins/hexaemeron/skills/protasis/SKILL.md#L290-L374)):
  "Conformance evidence may remain pending until its named step or
  integration transition. An unknown is therefore a scheduled refusal, not a
  guessed score."
- The in-repository pattern for "accepted with disclosure" is the
  `## Carried forward` gate from
  [ADR-067](https://github.com/wildcat-finance/skills/blob/32a70f9cc3c8b14ed2001dcf9e2e7821b8c112a9/docs/decisions/ADR-067-gate-a-run-on-what-its-issue-filed.md):
  the controller refuses `done integrate` until the run pull request body
  says what was left, in a fixed row grammar the controller parses. The
  disclosure section follows it.

**The affected run.** Fiat run `fiat/1298-imprimatur-structural-prose-family-evidence`
(plugin `1.6.31`): its
[proof, "Design cell and the halt"](https://github.com/wildcat-finance/skills/blob/32a70f9cc3c8b14ed2001dcf9e2e7821b8c112a9/plugins/hexaemeron/docs/imprimatur-structural-family-evidence/proof.md#L115-L141),
its
[study line 95](https://github.com/wildcat-finance/skills/blob/32a70f9cc3c8b14ed2001dcf9e2e7821b8c112a9/plugins/hexaemeron/docs/imprimatur-structural-family-evidence/study.md#L95)
(one conformance gate `two-independent-specimens`, count at least 2, pending
for every candidate, blocking `integration`), its runbook's `design-lock`
block (record `f96f2fb27c16da48ef639eae8e9f41caf6d2f40c6fa7fe8948848c91628746dc`)
and the 2026-09-10 amendment of Step 4's Exit that expects exit 1
([runbook lines 103 to 104](https://github.com/wildcat-finance/skills/blob/32a70f9cc3c8b14ed2001dcf9e2e7821b8c112a9/plugins/hexaemeron/docs/imprimatur-structural-family-evidence/runbook.md#L103-L104)).
Step pull requests #1449, #1519, #1521 and the run pull request
[#1525](https://github.com/wildcat-finance/skills/pull/1525) (merged
2026-09-10T11:40:31Z) were landed by hand; #1525's "Integration halt" section
and its carryover rows `design-gate-pinned-past-amendment | filed | #1524`
and `integration-halt-two-independent-specimens | none` are the previous
run's record of the unfinished work. Both are answered here: the first is
this study, the second stays as it is because no controller change lands a
run whose ledger already ended at step 4.

**Last two merged pull requests per changed subject.**

- `design_evidence.py` and the design-transition code in `hexctl.py` were
  created by [#1002](https://github.com/wildcat-finance/skills/pull/1002)
  (2026-08-31, skills#1000). `git log --first-parent` at the starting commit
  lists no second pull request for `design_evidence.py`; for the hexctl
  design code the later touches are
  [#1638](https://github.com/wildcat-finance/skills/pull/1638) (2026-09-14,
  skills#453) and [#1670](https://github.com/wildcat-finance/skills/pull/1670)
  (2026-09-15, skills#508). #1002's "Known boundary" (77 missing-target links
  in the partial generated runtime) is unrelated and stays with its owner.
  #1638 carried #1539, #1540 and #1541 as filed issues; #1540, a Files field
  that cannot anticipate an amendment, is the trap section 3 plans around and
  stays open under its own issue. #1670 carried #872, #873 and #875 as
  duplicates; none touches design evidence.
- The amendment code (`cmd_amend_study`, `cmd_amend_runbook`) was last changed
  by #1670 and [#943](https://github.com/wildcat-finance/skills/pull/943)
  (2026-09-01, skills#497), after
  [#585](https://github.com/wildcat-finance/skills/pull/585) and
  [#474](https://github.com/wildcat-finance/skills/pull/474). #943 carried
  three bullets (local checkpoint archives, unknown legacy synopsis fields,
  an unchanged README line); none is design evidence. The `fiat-v5.56.1` row
  (skills#1264) taught `amend study` to retain or displace runbook amendments;
  this run adds no amendment kind and leaves that chain alone.

**Audit records.** `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`
ran from the run worktree at the starting commit and exited 0 for all 99
pairs, so each synopsis is the read mode; every source remains authoritative.

- `plugins/hexaemeron/audit/AUDIT.md`, read through
  `plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md` (source SHA-256
  `8acff29ed567c97902941a85d72e41171c10850de6aa898b5d50564248eac28f`): two
  Step 0 rounds of 15 August 2026, F-01 to F-07 all `fixed`; its legacy
  fields `audit-schema`, `covered`, `not-checked` and `elenchus-verdict`
  are `[missing legacy field: ...]` and remain unknown. Nothing on design
  evidence, which postdates it.
- `audit/AUDIT.md`, read through `audit/AUDIT_SYNOPSIS.md` (source
  `d0be89aa23e8db7979ac29ff1613e31d59a1ee78d07131147d50eb6268e01d9d`), grepped
  for `design-evidence`, `design-lock`, `D008`, `amend`, `pending cell` and
  `conformance`: no finding on the design record or its transitions.
- `audit/rounds/fiat-1298-imprimatur-structural-prose-family-evidence.md`,
  read through its `.synopsis.md` (source
  `079ddb33af35ccb922b30bf606a9d51f26a56185eb631a1068a90873c82e5a05`) and
  its source grepped for `design`, `D008`, `two-independent` and `--report`:
  14 rounds, 43 findings. Step 4 round 1, `Leads not pursued`, names the
  resolver whose `--report` path equals the closed object's path, written to
  scratch instead; that lead becomes deliverable 3 above. `S2-R1-04`
  (`--report` written with `write_text` before findings are collected,
  `accepted`) belongs to the Imprimatur checker and stays accepted there.
- `audit/rounds/fiat-1264-rebind-runbook-amendments-across-a-study-am.md`,
  `fiat-1273-settle-declared-study-criteria-with-recorde.md`,
  `fiat-1086-gate-study-and-runbook-links-before-their-d.md`,
  `fiat-461-ship-the-hypomnema-design-bridge-check.md` and
  `fiat-508-restudy-residual-carryover-confinement-and-g.md`, each read
  through its `.synopsis.md`: their findings concern amendment rebinding, the
  criteria join, the link gate, the design bridge and command receipts; each
  `Covered`, `Not checked`, `Elenchus verdict` and `Leads not pursued` field
  was retained as written and none names a design-record cell. The 1264
  round's warning that the committed runbook copy trails every amendment is
  carried into section 3.

**Related open issues, named and left open.**
[skills#1713](https://github.com/wildcat-finance/skills/issues/1713)
(framework-165): a run that halts before `done integrate` owes task-issue
closure and no command records it. It is the sibling consequence of the same
halt; this run does not change `halt`, and a run that discloses instead of
halting reaches the existing closure receipt, which is the only relief this
run gives it.
[skills#1534](https://github.com/wildcat-finance/skills/issues/1534)
(framework-109): a `minimise` cell reports a bare pass and a study without a
design bridge is not caught by any step. This study carries its bridge in
section 12 and its metrics report the measured values; the cell semantics
change stays with #1534.

**Organisation.** No other `wildcat-finance` repository carries a Fiat
controller or a Protasis record; there is nothing to read.

**Outside.** Two standing patterns record a shortfall instead of editing the
standard. pytest's `xfail(strict=True)` marks a known failure with a reason
and fails the suite on an unexpected pass
([docs](https://docs.pytest.org/en/stable/how-to/skipping.html)); the NIST
plan of action and milestones records a failed control with the tasks and
dates that address it while the assessment result stands
([CSRC glossary](https://csrc.nist.gov/glossary/term/plan_of_action_and_milestones)).
The disclosure here is the first pattern's shape with the second's binding:
the failing evidence is retained by digest and the standard is unchanged.

## 3. Constraints and non-goals

**Starting state.** Base `32a70f9cc3c8b14ed2001dcf9e2e7821b8c112a9` (main,
2026-09-21). Run branch `fiat/1524-integration-blocked-design-cell`, pushed.
Controller `fiat-v6.72.1` from plugin `1.6.70`; run state
`contracts.design_evidence`, `gate_commands` and `success_criteria` present.
Toolchain: Python `3.14.6`, stdlib only, Git, `gh`.

**This run cannot use what it builds.** The controller gating this run is the
installed `1.6.70`. Every cell in this run's record is selection evidence
resolved before design lock, except one conformance gate,
`refusal-guards-green`, phrased about a check step 3 produces and blocking
`step:4`. Its resolver is the wrapper step 1 ships running the step-3 guard
module; the operator runs it once after step 3's audit closes and before
`done push --step 3`, which consumes it. Mason and Warden never run it, and
no step's Exit says the step "produces" that report. Nothing in this record
is pending at `integration`.

**Suites and gates every step must satisfy.** Each step's Exit names the
root suite `python3 -m unittest discover -t . -s tests` (2,083 tests, 290 to
390 s on 2026-09-20) and the Hexaemeron suite
`cd plugins/hexaemeron && python3 tests/run_tests.py --jobs 8 <fresh report path>`
(about 2,800 tests), run with `NO_COLOR=1` and
`CHECKPOINT_COSIGN=$HOME/.claude/tools/bin/cosign-3.1.3-darwin-arm64`
exported, since `FORCE_COLOR=3` in this shell reddens argparse assertions and
three checkpoint-authority tests refuse without the pinned cosign. Runbook
commands go through `python3 scripts/run_checks.py --base <run branch>
--scope root --scope hexaemeron --format json`, whose grammar admits only
`python3` plus a registered script. Before every commit:
`python3 plugins/horos/skills/horos/scripts/horos.py scan . --write` and
`... scan . --census --write`, after `git add`.

**One package version rise per step.** `scripts/plugin_release.py` refuses
any pull request that changes `plugins/hexaemeron/` without a version above
its own base. The highest version any remote ref claims is `1.6.71`
(`origin/claude/handle-1704-088ea1`), so the five steps take `1.6.72` to
`1.6.76`, re-checked against every remote ref immediately before each push.
Each rise touches `plugins/hexaemeron/.claude-plugin/plugin.json`,
`plugins/hexaemeron/.codex-plugin/plugin.json`, the hexaemeron entry in
`.claude-plugin/marketplace.json`, `tests/test_version_propagation.py` line 47
and `plugins/hexaemeron/tests/test_phylax_model_proxy.py` line 5684.

**Ledger rows.** The runbook declares a `version-relations` block for `fiat`
and `protasis`; no concrete version token may then appear in the runbook
outside that block (P006). Projected labels if main does not move:
`fiat-v6.73.1` and `protasis-v6.17.1`, both generation rows with the frontier
line and digest byte-for-byte unchanged. A ledger row moves `metadata.version`
in the sibling `SKILL.md` (same-length edit) and re-pins
`CHECKPOINT_COMPATIBLE_CONTROLLER_VERSIONS` in `hexctl.py` (line 481).

**Digest cascade.** Any `hexctl.py` edit re-pins
`tests/promise_machine_coverage.json` (line 4529), then
`docs/promise-machine/obligation-gates/evaluation-run.json` (re-tallied from
the confined answers, never a model run), then `integration-projection.json`
and `.md`, then `.horos/census.json`. `tests/promise_machine_coverage.json`
also pins `plugins/hexaemeron/tests/test_protasis_design_evidence.py` (lines
1337 and 5299), so the Protasis step walks the same cascade.
`design_evidence.py` is not in `gate_commands.py`'s `MODULE_BINDINGS`
(only `protasis.py` is), so no binding re-pin is owed unless `protasis.py`
changes outside its `main` builder, which no step does.

**Governed prose.** `plugins/hexaemeron/skills/fiat/SKILL.md` bytes 18784 to
29736 are bound by `tests/fixtures/agent-instruction-v1/manifest.json`
(`model_evidence_status: disabled`), so the paragraph at lines 415 to 418
stays as it is and the new paragraph goes after byte 29736, before
`**Amending receipted specifications.**` (byte 30735), with
`scripts/prove_agent_instruction_reconciliation.py` run against the base
commit. Changing the `fiat-design-evidence` promise stanza (line 1208
onward) moves its `semantic_sha256` in `tests/promise_machine_id_history.json`
(PM104) and the two obligation-gate digests that name that file; the step
that edits the stanza re-pins both.

**Byte-pinned records.** Every file under `audit/` and
`plugins/*/audit/` is prefix-pinned by `tests/test_audit_prefix_integrity.py`;
the run appends its rounds and edits no existing byte.
`plugins/hexaemeron/skills/fiat/checkpoint-authority/native-profile.json` is
frozen and is never edited.

**Decision record.** The new decision is the unnumbered draft
`docs/decisions/drafts/disclose-a-failed-integration-design-cell.md` with a
`# Decision:` heading, five sections and a dated status; the allocator
numbers it at integration. No inherited decision record changes a byte.

**Committed copies.** Step 1 commits byte-identical copies of the study, the
runbook, the record, its 28 reports and the probe under
`plugins/hexaemeron/docs/fiat-design-cell-disclosure/`. Every later amendment
makes the runbook copy trail; the step that amends re-copies and `cmp`s it.
The probe writes only to a fresh `--out` and removes its temporary
directories, so a reviewer re-running the committed copy cannot overwrite a
receipted report.

**Receipt shapes across steps.** `_design_checker_receipt` requires the exact
five-key receipt, so the Protasis step emits `disclosed` only when a
`--disclosure` flag was given; the Fiat step then admits either key set. Each
step is green at both ends with the tree's own controller tests.

**Ruled out and deferred.**

- A cell due at `step:N` is not disclosable. It fails at the `done push` that
  opens step N, before most of the stack exists, so ADR-061's halt and
  restart remains proportionate; an `integration` cell fails after every step
  is built, audited and merged.
- No change to `hexctl amend`, to D008 without a disclosure, to `halt`, to
  `reset`, or to ADR-061's bytes.
- No relief for the 1298 run: its ledger ended at step 4 and its stack is
  landed.
- skills#1713 and skills#1534 stay with their own issues.
- No second-party approval of a disclosure: the reason is the operator's
  claim, bound by digest and repeated in the pull request body, and the
  audit loop reads both.
- No Solidity; the security-suite waiver recorded at init stands.

## 4. Design options

Four candidates, one per reading the issue names plus the floor-then-tighten
question it asks. Each is a mechanism for the moment the collected data fails
an `integration`-due cell.

1. **`halt-as-today`.** The checker returns D008, the operator runs
   `hexctl halt --reason ...` and lands the stack by hand. Trade: nothing new
   to build; the failure leaves the controller with a free-text reason only,
   `done integrate` and the closure receipt are unreachable, and skills#1713
   follows.
2. **`threshold-amendment`.** An append-only sidecar lowers the cell's
   threshold to what the data supports and the cell is re-resolved; the record
   bytes are untouched. Trade: the run reaches `done integrate`, but the
   verdict is computed against a threshold chosen after the data was seen,
   which is the weakening ADR-061 forbids.
3. **`floor-then-tighten`.** The study locks a floor threshold it knows is
   below the design's need, and a later step appends a tighten to the real
   one. Trade: the lock's selection evidence is false by construction, and
   the tighten fails on the same data the real threshold would have failed
   on.
4. **`disclosed-refusal`.** A closed disclosure binds the failing report and
   the locked threshold; the transition admits the cell as disclosed; `done
   integrate` requires a matching row in the run pull request body. Trade:
   one new command, one new checker flag and code, one new receipt field and
   ledger event, and a body section the operator must write.

**How the cells were measured.** `.hexaemeron/design/probe.py` builds, in a
fresh temporary directory, a synthetic run in the skills#1298 shape: a locked
record with one conformance cell `jsonl-fixture/two-independent-specimens`,
count at least 2, due at `integration`; a receipted lock; a ledger. It writes
the failing resolver report (value 0, then value 1), applies the candidate's
operation, and takes every transition verdict from the repository's own
`design_evidence.py` at the starting commit. It does not run `hexctl`, so it
measures the mechanisms, and the runbook's steps must build and test the
controller that carries the selected one. It writes one closed
`protasis-design-report/v1` object per cell to `--out`, which must not exist,
and removes its temporary directories. Phylax and Ephoros lint it clean.

**Criteria and results.** Seven selection criteria cover the five concerns;
every gate is `equals true`, every metric is `minimise`.

| criterion (concern, owner) | halt-as-today | threshold-amendment | floor-then-tighten | disclosed-refusal |
| --- | --- | --- | --- | --- |
| `record-and-reports-unchanged` (correctness, hypomnema): receipted record and report digests hold after the operation | true | true | true | true |
| `locked-threshold-governs` (correctness, protasis): every verdict, on both datasets, is computed against the threshold locked at design lock | true | false | false | true |
| `failed-cell-on-ledger` (recovery, fiat): a structured ledger entry names candidate, criterion, report digest, value and threshold | false | true | false | true |
| `integrate-reachable` (recovery, fiat): the modelled `done integrate` admission is reached on both datasets | false | true | false | true |
| `legacy-state-untouched` (compatibility, fiat): a state without the contract is byte-identical after the candidate's command | true | true | true | true |
| `ledger-bytes-added` (space, metron): bytes the operation adds to state, ledger and sidecars, dataset 0 | 365 | 1,747 | 902 | 1,768 |
| `operation-ms` (time, metron): median of five runs of the operation including checker calls, dataset 0 | 77 | 166 | 88 | 80 |

Gates remove `halt-as-today` (two false), `threshold-amendment` (one false)
and `floor-then-tighten` (three false). One candidate survives, so the rule is
`unique-frontier` and the selection is **`disclosed-refusal`**. Its cost
against the status quo is 1,403 more bytes on the ledger and state per
disclosed cell and 3 ms more wall time on this fixture; both are below any
budget in section 10. The record is `.hexaemeron/design-evidence.json`, 4
candidates, 8 criteria, 32 cells, 28 resolved; `design_evidence.py
--transition design-lock`, `step:1` and `step:3` exit 0 on it, and `step:4`
refuses D008 until the step-3 report exists, which is the intended stop
point.

**The floor-then-tighten question.** No. A floor declared at `done study`
below the design's need makes the lock's own evidence false, and the probe
shows the route gains nothing: with data 0 the floor of 1 fails, with data 1
the tighten to 2 fails, and in both the verdict is computed against a value
the study did not lock. The disclosure route makes it unnecessary: the study
declares the threshold the design needs, and if the data falls short the run
says so against that threshold.

**Which skills upgrade.** Both. Protasis owns the disclosure object, the
checker flag, D009 and the `disclosed` receipt field, and the wrapper;
Fiat owns the command, the receipt field, the ledger event, the transition
and `verify` replay, the `next` and `status` surfaces, and the `done
integrate` body gate. Each takes one generation row.

**Shape of the selected design.**

- `protasis-design-disclosure/v1`: exactly `schema`, `candidate`,
  `criterion`, `record_sha256`, `report` (`path`, `sha256`), `value`, `unit`,
  `comparator`, `threshold`, `reason`; one closed JSON object of at most 64
  KiB, a non-symlink regular file below the record's directory, `reason` at
  most 4,096 printable bytes with no newline. It is admissible only for the
  selected candidate's pending conformance cell that blocks `integration`,
  whose report exists, is closed, and fails by non-zero exit or by its
  comparator; and only when `record_sha256` equals the record file's digest,
  `report.sha256` equals the report file's digest, and `value`, `unit`,
  `comparator` and `threshold` equal the report and the criterion.
- `design_evidence.py --transition integration --disclosure <path>` (repeatable,
  at most 32): an admitted disclosure removes that cell's D008 and lists it
  in a receipt field `disclosed` (`candidate`, `criterion`, `path`, `sha256`
  of the report, `disclosure_sha256`); every other D008 stands; D009 refuses a
  disclosure that is malformed, out of place, digest-mismatched, names a
  passing or non-due cell, names a non-selected candidate, or is supplied at
  another transition. Without the flag the checker is byte-for-byte today's.
- `hexctl disclose design --cell <candidate>/<criterion> --report <path>
  --reason <text>`: accepted only with the contract marker, in phase
  `integrate` before the final merge-step is receipted, not halted, when a
  dry run of the checker at `integration` reports D008 for exactly that cell
  and no disclosure for it exists. It writes
  `.hexaemeron/design-disclosures/<candidate>--<criterion>.json` through a
  temporary file and rename, appends `{candidate, criterion, path, sha256}`
  to `receipts.study.design_evidence.disclosures`, and commits
  `design:disclose` with the closed object. `_prepare_design_transition` at
  `integration` verifies each recorded disclosure's digest and passes it to
  the checker; the transition receipt carries `disclosed`;
  `verify_design_evidence` replays with the same flags and refuses a
  disclosure in state without its event or the reverse. `status` prints one
  `DESIGN:` line per disclosed cell; the integrate directive from `next`
  carries `design_disclosures` rows.
- `done integrate`: when the integration transition receipt lists disclosed
  cells, the run pull request body must carry `## Design evidence` with
  exactly one row per cell in the shape `<candidate>/<criterion> | <value>
  <unit> against <comparator> <threshold> | <report sha256> | <reason>`, no
  other rows, and the heading is refused when no cell was disclosed. The
  receipt records the rows under `integrate.design_disclosures`. Legacy runs
  without the contract are unchanged.
- `plugins/hexaemeron/skills/protasis/scripts/design_report.py --candidate
  <id> --criterion <id> --unit <unit> --out <path> (--value-from-exit |
  --value-json <inner report> --value-key <key>) -- <argv...>`: runs the argv
  with no shell, a 900 s timeout and a 1 MiB output cap; writes the closed
  report with `exit` set to the child's exit and `command` set to the quoted
  argv; refuses an `--out` that exists, is a symlink, lies outside the
  record's directory, or equals any argv element. It does not judge the
  value; the checker does.

**Build order** (the runbook derives the steps): 1 scaffold, docs copies,
draft decision, wrapper and its tests; 2 Protasis disclosure contract, checker
flag, D009, tests, SKILL.md paragraph, ledger row; 3 `hexctl disclose
design`, the integration transition and `verify` replay, tests; 4 the `next`
and `status` surfaces, the `done integrate` body gate, Fiat SKILL.md
paragraph and promise stanza, ledger row, promise-history re-pin; 5 the
disposable-run demonstration and proof. Steps 3 and 4 each edit `hexctl.py`
and walk the cascade; step 4 carries the Fiat ledger row so the checkpoint
version set moves once.

## 5. Risk register seed

The audit loop cites these ids. Python concerns dominate: bounded files,
digest binding, partial writes, and the one place the controller reads text a
person wrote.

```risk-register
record-digest-drift | the receipted record and report bytes at every transition and in verify | a disclosure changes none of them and drift still dies with the existing message
disclosure-report-binding | the disclosure's record_sha256 and report.sha256 against the current files | any mismatch refuses D009 and verify replays the same comparison
disclosure-of-passing-cell | a cell whose report passes, is not due at integration, or belongs to a non-selected candidate | disclose refuses before writing and the checker refuses D009
step-cell-out-of-scope | a cell that blocks step:N | disclose refuses it and done push still fails closed on D008
pr-body-parity | the Design evidence section of the run pull request body | rows equal the recorded disclosures exactly, one per cell, none extra, heading absent when nothing was disclosed
ledger-state-parity | design:disclose events against receipts.study.design_evidence.disclosures | verify refuses a disclosure on either side alone
partial-write | the disclosure file, state and ledger during disclose | temporary file and rename before the state write; a refusal writes nothing
reason-bounds | the --reason bytes and the disclosure file size | at most 4096 printable bytes without newline, file at most 64 KiB, non-symlink below the record directory
legacy-state | a run without contracts.design_evidence | disclose refuses and no receipt field is inferred
halted-run | disclose on a halted run | refuses until resume, as amend does
wrapper-out-collision | design_report.py --out against every argv element and existing paths | refuses an equal path, an existing path, a symlink and a path outside the record directory
wrapper-subprocess | the child argv of design_report.py | list argv without a shell, 900 s timeout, 1 MiB output cap, exit recorded and never judged
receipt-shape-compatibility | the five-key checker receipt Fiat requires today | disclosed appears only when a disclosure flag was given and the Fiat step admits both shapes
governed-prose | fiat SKILL.md bytes 18784 to 29736 and every audit file | untouched; new prose after byte 29736; audit rows appended only
version-surfaces | the plugin version, ledger rows, checkpoint version set, promise history and digest cascade | each step's Files names them and both suites are green at both ends
```

## 6. Glossary seeds

- **Design cell.** One candidate-by-criterion result in the record.
- **Due cell.** A pending conformance cell whose `blocks` names the current
  transition; the checker consumes only the selected candidate's due cells.
- **Locked threshold.** The criterion's `threshold` as receipted at design
  lock; it never changes inside a run.
- **Disclosure.** One closed `protasis-design-disclosure/v1` object binding a
  failing due cell to the record and report digests and the locked threshold.
- **Disclosed cell.** A due cell whose D008 the checker withheld because an
  admitted disclosure names it; listed under `disclosed` in the receipt.
- **D008.** Evidence due at the transition is absent or fails. **D009.** A
  disclosure is malformed, misplaced or mismatched.
- **Resolver.** The command a pending cell names to produce its report.
- **Report object.** The closed `protasis-design-report/v1` file the checker
  reads; its `exit` must be 0 for a pass.
- **Wrapper.** `design_report.py`, which runs a resolver and writes the report
  object at a distinct path.
- **Design-lock block.** The runbook fence binding the record's schema,
  SHA-256 and selected candidate before Step 1.
- **Run pull request body.** `run_pr_path` (`hexctl.py` line 2027), the file
  `done integrate` reads for `## Carried forward` and, now, `## Design
  evidence`.

## 7. Sources

- Issue skills#1524: https://github.com/wildcat-finance/skills/issues/1524
  (body SHA-256 `b287ff7cd95390b623c1174a63f41eb0f47e29a0919393871cfe5168b66ccf8e`
  as receipted at init). Related: skills#1713, skills#1534, skills#1000,
  skills#1298.
- ADR-061, pinned:
  https://github.com/wildcat-finance/skills/blob/32a70f9cc3c8b14ed2001dcf9e2e7821b8c112a9/docs/decisions/ADR-061-lock-designs-with-progressive-checked-evidence.md
- `hexctl.py` and `design_evidence.py` at the starting commit, line numbers as
  cited in sections 1 and 2:
  https://github.com/wildcat-finance/skills/blob/32a70f9cc3c8b14ed2001dcf9e2e7821b8c112a9/plugins/hexaemeron/skills/fiat/scripts/hexctl.py
  and
  https://github.com/wildcat-finance/skills/blob/32a70f9cc3c8b14ed2001dcf9e2e7821b8c112a9/plugins/hexaemeron/skills/protasis/scripts/design_evidence.py
- Fiat SKILL.md phase note and promise:
  https://github.com/wildcat-finance/skills/blob/32a70f9cc3c8b14ed2001dcf9e2e7821b8c112a9/plugins/hexaemeron/skills/fiat/SKILL.md#L395-L418
  and
  https://github.com/wildcat-finance/skills/blob/32a70f9cc3c8b14ed2001dcf9e2e7821b8c112a9/plugins/hexaemeron/skills/fiat/SKILL.md#L1208-L1219
- Protasis SKILL.md design-evidence section, pinned in section 2; Protasis
  ledger `plugins/hexaemeron/skills/protasis/EVOLUTION.md` (`protasis-v6.16.1`,
  mature); Fiat ledger `plugins/hexaemeron/skills/fiat/EVOLUTION.md`
  (`fiat-v6.72.1`, open, held job skills#1212);
  `plugins/hexaemeron/skills/VERSIONING.md`.
- The 1298 run: `plugins/hexaemeron/docs/imprimatur-structural-family-evidence/`
  (`study.md`, `runbook.md`, `proof.md`), pull requests #1449, #1519, #1521,
  #1525, and `audit/rounds/fiat-1298-imprimatur-structural-prose-family-evidence.md`.
- Pull requests #1002, #1638, #1670, #943, #585, #474 on
  https://github.com/wildcat-finance/skills/pulls
- Audit synopses named in section 2, verified by `audit_synopsis.py --check .`
  at the starting commit (exit 0, 99 pairs).
- The probe and its 28 reports: `.hexaemeron/design/probe.py` and
  `.hexaemeron/design/reports/`, committed by Step 1 under
  `plugins/hexaemeron/docs/fiat-design-cell-disclosure/design/`.
- Version surfaces: `scripts/plugin_release.py`,
  `tests/test_version_propagation.py`,
  `plugins/hexaemeron/tests/test_phylax_model_proxy.py`,
  `tests/promise_machine_coverage.json`,
  `tests/promise_machine_id_history.json`,
  `docs/promise-machine/obligation-gates/`,
  `tests/fixtures/agent-instruction-v1/manifest.json`.
- Remote refs enumerated 2026-09-21 for the highest claimed plugin version
  (`1.6.71` on `origin/claude/handle-1704-088ea1`, 436 refs read).
- pytest skipping and xfail:
  https://docs.pytest.org/en/stable/how-to/skipping.html
- NIST CSRC glossary, plan of action and milestones:
  https://csrc.nist.gov/glossary/term/plan_of_action_and_milestones

## 8. Signals, and the questions behind them

No unattended signal, and here is why: every command here runs at a terminal
inside one `hexctl` invocation and finishes in well under a second, nothing
runs on a schedule or serves a request, and Ephoros's event, metric and alert
rules have nothing to attach to. The questions a later reader will ask are
answered by receipts the steps already write:

1. "Which cell was disclosed, against what, and why?" The `design:disclose`
   ledger event and the file under `.hexaemeron/design-disclosures/` carry
   candidate, criterion, value, threshold, report digest and reason (step 3);
   `hexctl status` prints one `DESIGN:` line per disclosed cell (step 4).
2. "Did the run pull request say so?" The `done integrate` receipt's
   `design_disclosures` rows equal the body section (step 4).
3. "Was the report or the record changed after the disclosure?" `hexctl
   verify` replays the transition with the recorded digests and refuses on
   drift (step 3).

[ephoros](https://github.com/wildcat-finance/skills/blob/32a70f9cc3c8b14ed2001dcf9e2e7821b8c112a9/plugins/hexaemeron/skills/ephoros/SKILL.md)
owns what a signal must carry; none is added.

## 9. Boundaries, per capability

Each boundary this opens, what is worth taking at it, and the control that
closes it; the ids match section 5.

- **The disclosure file** (`disclosure-report-binding`, `reason-bounds`,
  `partial-write`): a hand-written JSON file the checker and controller read.
  Worth taking: a disclosure that names a cell the data did not fail, or
  points at a report that later changes. Controls: closed key set, 64 KiB
  cap, non-symlink regular file below the record directory, record and report
  digests compared on every read, `reason` bounded and printable, written by
  temporary file and rename.
- **The `--reason` text** (`reason-bounds`): operator prose that lands on the
  ledger and in `status` output. Controls: 4,096 printable bytes, no newline
  or control character, never interpreted.
- **The run pull request body** (`pr-body-parity`): text read from
  `run_pr_path`, already a controller input for `## Carried forward`.
  Controls: the same bounded reader, a fixed row grammar, exact set equality
  with the recorded disclosures, refusal before any state write.
- **The checker subprocess** (`receipt-shape-compatibility`): Fiat already
  runs `design_evidence.py` through `bounded_run` and admits only a closed
  receipt; the `disclosed` field is validated with the same shape rules as
  `consumed` (`DESIGN_CONSUMED_MAX` 128 at `hexctl.py` line 564).
- **The wrapper's child process** (`wrapper-subprocess`,
  `wrapper-out-collision`): a resolver command run on the operator's behalf.
  Controls: list argv, no shell, 900 s timeout, 1 MiB captured output,
  `--out` opened with `O_EXCL`, refused when it equals any argv element or
  lies outside the record directory; the wrapper records the exit and never
  turns it into a verdict.
- **Legacy and halted state** (`legacy-state`, `halted-run`): the command
  refuses both and writes nothing.

[phylax](https://github.com/wildcat-finance/skills/blob/32a70f9cc3c8b14ed2001dcf9e2e7821b8c112a9/plugins/hexaemeron/skills/phylax/SKILL.md)
owns the boundary list and its controls; the Phylax lint runs on every
changed Python file in every step.

## 10. The budget, or its absence

One budget, because the integration transition already runs the checker as a
subprocess at `done merge-step` and the disclosure adds file reads to it: the
checker at `--transition integration` with one `--disclosure` completes in
at most 1,000 ms of `real` time on the harness fixture, measured by
`/usr/bin/time -p python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py <record> --transition integration --disclosure <path> --format receipt`
before and after step 2, against the probe's baseline of 80 ms for the whole
disclosed-refusal operation (`.hexaemeron/design/reports/disclosed-refusal-operation-ms.json`).
State growth is bounded by construction: at most 32 disclosures per run, each
at most 64 KiB. The wrapper adds no budget of its own; it waits on the
resolver it runs. `hexctl disclose design` runs once per disclosed cell at a
terminal and has no budget.
[metron](https://github.com/wildcat-finance/skills/blob/32a70f9cc3c8b14ed2001dcf9e2e7821b8c112a9/plugins/hexaemeron/skills/metron/SKILL.md)
owns how the measurement is taken and compared.

## 11. The fail-closed posture

What stops the run: an undisclosed D008 at any transition, exactly as today;
a D009 from a malformed, misplaced or mismatched disclosure; a `disclose
design` on a cell that passes, is not due at `integration`, belongs to a
non-selected candidate, or already carries a disclosure; a run pull request
body whose `## Design evidence` rows do not equal the recorded disclosures;
any record, report or disclosure digest that drifts under `verify`; a
disclosure recorded in state without its ledger event or the reverse. Each
refusal names the cell and the digest it compared, writes nothing, and leaves
`hexctl halt` and `reset` available as before. The wrapper refuses an `--out`
it would overwrite or that collides with the resolver's own argument, so the
1298 collision cannot recur through it.

Guard convention: every refusal above gets a test that fails without the
fix, in `plugins/hexaemeron/tests/test_protasis_design_report.py` (step 1),
`plugins/hexaemeron/tests/test_protasis_design_evidence.py` (step 2, extending
its 11 cases) and `plugins/hexaemeron/tests/test_hexctl_design_disclosure.py`
(steps 3 to 5). A fix claimed in an audit round runs
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`,
format `unittest-json-v1`, report `.hexaemeron/elenchus-step-N.json`.
[elenchus](https://github.com/wildcat-finance/skills/blob/32a70f9cc3c8b14ed2001dcf9e2e7821b8c112a9/plugins/hexaemeron/skills/elenchus/SKILL.md)
owns the triage order and the guard rule.

This run's own stop points: `design_evidence.py --transition step:4` refuses
D008 until the operator runs the `refusal-guards-green` resolver after step
3's audit; the base is green under the environment named in section 3, and a
red that reproduces on a detached `origin/main` snapshot is the base's, not
the step's.

## 12. Decisions and their homes

One decision is expensive to reverse: a failed `integration`-due design cell
is disclosed against its locked threshold and admitted into `done integrate`
with the disclosure repeated in the run pull request body, rather than
amended, relaxed or left to a hand landing. Its home is the draft
`docs/decisions/drafts/disclose-a-failed-integration-design-cell.md`,
authored by Step 1 with the `# Decision:` heading, five sections and a dated
status, numbered by the allocator at integration; it extends ADR-061 and
names the three rejected candidates with the measured cells above.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | disclosed-refusal
record | docs/decisions/drafts/disclose-a-failed-integration-design-cell.md
```

The other homes are existing ones. The resolver-and-report separation rule
lives in the Protasis SKILL.md design-evidence section beside the wrapper,
because it is a contract rule, not a choice a later reader could reverse. The
record digest `600ee2050a5abbfecb4a0a6188f14f3d091f36f01875e006850c61f6d6cc7536`
is bound by the runbook's `design-lock` block. The two generation rows carry
the change into `plugins/hexaemeron/skills/fiat/EVOLUTION.md` and
`plugins/hexaemeron/skills/protasis/EVOLUTION.md`. The Fiat SKILL.md sentence
at lines 415 to 418 that says no amendment transition exists yet stays
byte-for-byte, and the new paragraph after byte 29736 names the route that now
exists.
[hypomnema](https://github.com/wildcat-finance/skills/blob/32a70f9cc3c8b14ed2001dcf9e2e7821b8c112a9/plugins/hexaemeron/skills/hypomnema/SKILL.md)
owns which decisions earn a record and where each lives.
