# Runbook: inject known-failure guards before production changes

Five stacked steps deliver the selected `receipted-inoculation` design. Each
step starts and finishes green. A deliberately red guard-only commit may exist
between those boundaries, and the final green branch carries it as an
ancestor. It must never be pushed as the branch head or a finished step, handed
off as green, described as an expected failure, or used as a passing claim.

The installed controller cannot enforce the phase it is building. Before a
product path changes in steps 1 through 4, Mason runs that step's exact guard
command. Mason records the signed guard commit and bounded Elenchus JSON below
`.hexaemeron/bootstrap/step-<n>/` and stops unless the result is exactly
`guarded`. This bootstrap evidence is not a receipt and does not attest
retained report bytes. Step 5 proves the checked-in successor controller in a
disposable repository. Every Warden round reviews all 12 ids in the study risk
register, uses the step's exact audit runner, and fixes every finding before
the prose and push phases. Shipped prose goes through the bounded Sapheneia
operation, Imprimatur, a surface-only Vulgate rewrite, a second Imprimatur
check, and Brevitas.

```version-relations
elenchus | plugins/hexaemeron/skills/elenchus/EVOLUTION.md | next-generation-after-integration-base
fiat | plugins/hexaemeron/skills/fiat/EVOLUTION.md | next-generation-after-integration-base
protasis | plugins/hexaemeron/skills/protasis/EVOLUTION.md | next-generation-after-integration-base
```

```design-lock
schema | protasis-design-evidence/v1
sha256 | 0af3099f87a07e6a51c08e8fe0bffd9fa73780711561817aa35fc18727239473
candidate | receipted-inoculation
```

After all five step pull requests have merged and the run reaches `integrate`,
the candidate rows and package values are still provisional. If the base has
advanced, first complete the controller-directed signed product/base sync,
integration revalidation, and any resulting corrections to candidate rows,
skill metadata, package manifests, marketplaces, and pinned consumers. Then
run the explicit post-stack gate `hexctl done resolve-versions`. Only its zero
exit and receipt establish the exact three skill labels against one stable
base and candidate head; a collision, stale base, mismatched skill metadata,
or uncorrected package consumer blocks integration.

## Step 1: Define the source-bound known-failure inventory

**Goal.** Build the `inventory-contract` module: commit the study and runbook,
add the closed inventory parser and reporter, and refuse incomplete or stale
known-failure input before any controller state can depend on it.

**Entry.** Start from `main` at
`5bc2494c4f5802efcd8a92e58554809ac4b9f147` on the run branch. The root and
Hexaemeron suites pass; `.python-version`, the existing workflows, root and
plugin licences, and repository layout are present and require no change.

**Exit.** `protasis-known-failure-inventory/v1` is parsed from one bounded,
stable study. The parser requires every source/view path and SHA-256, every
finding field, one assignment to a real runbook step, one exact `{report}`
argument, an admitted report format, portable guard paths, and either a
non-empty finding set or a digest-bound no-known-findings claim. Duplicate
keys, omitted or extra ids, stale views, unsafe paths, bad caps, and unassigned
entries refuse with no state or ledger write. The accepted seven-entry
inventory assigns `kf-453-01` to this step. The committed study and runbook are
byte-identical to the receipted artefacts. Protasis receives one provisional
candidate generation row whose prior frontier fields remain unchanged; exact
label resolution belongs to the post-stack gate. The toolchain, CI, licences,
and dependencies remain unchanged.
Prove the green exit with:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_issue_453_known_failure_inventory -v
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study plugins/hexaemeron/docs/known-failure-inoculation/study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py plugins/hexaemeron/docs/known-failure-inoculation/runbook.md
python3 scripts/portable_promise_machine.py sync
python3 scripts/portable_promise_machine.py check
python3 scripts/promise_machine.py check
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/run_checks.py --base 5bc2494c4f5802efcd8a92e58554809ac4b9f147
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/docs/known-failure-inoculation/study.md plugins/hexaemeron/docs/known-failure-inoculation/runbook.md plugins/hexaemeron/skills/protasis/SKILL.md plugins/hexaemeron/skills/protasis/EVOLUTION.md audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md --max-defects 0
for draft in plugins/hexaemeron/docs/known-failure-inoculation/study.md plugins/hexaemeron/docs/known-failure-inoculation/runbook.md plugins/hexaemeron/skills/protasis/SKILL.md plugins/hexaemeron/skills/protasis/EVOLUTION.md audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md; do
  python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py "$draft" --mode report || exit 1
done
git diff --check
```

**Files.** Create
`plugins/hexaemeron/docs/known-failure-inoculation/study.md`,
`plugins/hexaemeron/docs/known-failure-inoculation/runbook.md`,
`plugins/hexaemeron/skills/protasis/scripts/known_failure_inventory.py`,
`plugins/hexaemeron/tests/test_issue_453_known_failure_inventory.py`,
`plugins/hexaemeron/tests/emit_issue_453_guard_report.py`, and
`plugins/hexaemeron/tests/fixtures/issue-453/inventory.json`. Change
`plugins/hexaemeron/skills/protasis/SKILL.md`,
`plugins/hexaemeron/skills/protasis/EVOLUTION.md`, and
`tests/promise_machine_coverage.json`. Generate the ignored local verification
payload at `.agents/skills/promise-machine/runtime/` and its `MANIFEST.json`
with the repository script, but do not stage or describe it as a release file;
regenerate
`.horos/boundary.json`, `.horos/candidates.json`, and `.horos/census.json` only
when the repository-owned scan changes them. Warden alone appends
`audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md` and its
sibling `.synopsis.md`.

**Tests.** Before changing the parser, make a signed guard-only commit whose
sole parent is the packet's `branch_from` and whose changed paths are exactly
the three `kf-453-01` guard paths in the study. Replace
`<signed-guard-commit>` with that object and run:

```bash
python3 plugins/hexaemeron/skills/elenchus/scripts/elenchus.py --ref <signed-guard-commit> --test-command "python3 plugins/hexaemeron/tests/emit_issue_453_guard_report.py --case kf-453-01 --report {report}" --report-format unittest-json-v1 --report-file .elenchus/issue-453-kf-453-01.json --require-guard --format json
```

Stop unless it reports `guarded`; retain the command, commit, exit, and bounded
JSON outside Git. On the fixed tree run
`python3 plugins/hexaemeron/tests/emit_issue_453_guard_report.py --case kf-453-01 --report .elenchus/issue-453-kf-453-01-green.json` and require a positive,
complete, non-skipped, error-free, assertion-free report. The focused module
covers accepted input and every omission, duplication, shape, source-drift,
assignment, path, command, report-format, and cap refusal; its final case count
is recorded rather than guessed here. Warden's exact audit runner is command
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`,
format `unittest-json-v1`, file `.elenchus/fiat-453-step-1-audit.json`. Rerun
the complete Exit commands after every audit fix.

**Disciplines.** phylax: the study, JSON object, source views, paths, commands,
and files cross parser and filesystem boundaries, so type, size, containment,
stability, and duplicate checks apply before use. ephoros: stable refusal
codes, ids, counts, paths, and digests answer which inventory item failed
without printing source content. metron: none, this step makes no performance
claim; caps are correctness controls. elenchus: `kf-453-01` must fail by
assertion on the exact parent and finish green after the parser lands.
hypomnema: the inventory authority, assignment rule, and empty-set rule live in
the Protasis contract, its provisional candidate row, and the committed study
and runbook; integration owns the exact label.

## Step 2: Open inoculation before implementation

**Goal.** Build the `inoculation-transition` module: add the explicit phase,
state, directive, Mason packet, receipt boundary, and source-bound no-findings
route before `implement`.

**Entry.** Start from Step 1's signed, merged, and verified green exit. The
closed seven-entry inventory is available, but `done runbook` still opens
`implement` and no inoculation receipt exists.

**Exit.** New runs open `inoculate` after runbook receipt. `next` gives Mason
the exact study/runbook bindings, consuming step, assigned inventory entries,
allowed guard paths, commands, formats, report files, and step parent. One
`done inoculate` transition accepts either the complete assigned evidence set
or a non-empty no-known-findings claim binding all source-view digests and the
step. An empty list never passes. Missing, duplicate, foreign, or partial ids,
an unassigned step, and `done implement` before the inoculation receipt refuse
before state, design transition, ledger, or checkpoint mutation. Accepted
inoculation alone opens `implement` on the same branch. Pre-contract states
remain on their existing path without fabricated inventory. The numberless
ADR draft records the phase order, atomic receipt, red-intermediate boundary,
and old-controller bootstrap limit. Because the phase contract changes inside
the reviewed Fiat instruction span, re-author the bound phase model, source
spans, closed questions, and hostile mutations; regenerate its compact form;
then refresh the manifest, measurement, parity, and coverage bindings. The
source-digest-only reconciliation shortcut must refuse this semantic edit.
Prove the green exit with:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_issue_453_inoculation_lifecycle -v
python3 scripts/agent_instruction.py format --root . --input tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/model.json --output tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/compact.wai
python3 scripts/agent_instruction.py measure --root . --manifest tests/fixtures/agent-instruction-v1/manifest.json --output tests/fixtures/agent-instruction-v1/evidence/measurement.json
python3 scripts/agent_instruction.py parity --root . --manifest tests/fixtures/agent-instruction-v1/manifest.json --output tests/fixtures/agent-instruction-v1/evidence/parity.json
python3 scripts/agent_instruction.py check --root . --manifest tests/fixtures/agent-instruction-v1/manifest.json
python3 -m unittest tests.test_agent_instruction tests.test_agent_instruction_corpus -v
python3 scripts/portable_promise_machine.py sync
python3 scripts/portable_promise_machine.py check
python3 scripts/promise_machine.py check
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/run_checks.py --base 5bc2494c4f5802efcd8a92e58554809ac4b9f147
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/fiat/SKILL.md plugins/hexaemeron/agents/mason.md docs/agent-instruction-language-v1.md docs/decisions/drafts/require-inoculation-before-implementation.md audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md --max-defects 0
for draft in plugins/hexaemeron/skills/fiat/SKILL.md plugins/hexaemeron/agents/mason.md docs/agent-instruction-language-v1.md docs/decisions/drafts/require-inoculation-before-implementation.md audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md; do
  python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py "$draft" --mode report || exit 1
done
git diff --check
```

**Files.** Change `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/skills/fiat/SKILL.md`,
`plugins/hexaemeron/agents/mason.md`,
`plugins/hexaemeron/tests/test_hexctl.py`,
`plugins/hexaemeron/tests/test_fiat_skill.py`,
`scripts/agent_instruction.py`,
`tests/test_agent_instruction.py`,
`tests/test_agent_instruction_corpus.py`,
`docs/agent-instruction-language-v1.md`,
`tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/model.json`,
`tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/compact.wai`,
`tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/questions.json`,
`tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/mutations.json`,
`tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/source-spans.json`,
`tests/fixtures/agent-instruction-v1/manifest.json`,
`tests/fixtures/agent-instruction-v1/evidence/measurement.json`,
`tests/fixtures/agent-instruction-v1/evidence/parity.json`, and
`tests/promise_machine_coverage.json`. Create
`plugins/hexaemeron/tests/test_issue_453_inoculation_lifecycle.py`,
`plugins/hexaemeron/tests/fixtures/issue-453/no-known-findings.json`, and
`docs/decisions/drafts/require-inoculation-before-implementation.md` with
stable identity `adr/require-inoculation-before-implementation`; its number is
assigned only at integration. Refresh the ignored local portable verification
payload without staging it and, only when their generators change them, the
three `.horos/` records named in Step 1.
Warden alone changes the configured audit record and synopsis.

**Tests.** Before the controller edit, make the signed guard-only commit from
Step 1's merged exit using only the two `kf-453-02` guard paths. Run:

```bash
python3 plugins/hexaemeron/skills/elenchus/scripts/elenchus.py --ref <signed-guard-commit> --test-command "python3 plugins/hexaemeron/tests/emit_issue_453_guard_report.py --case kf-453-02 --report {report}" --report-format unittest-json-v1 --report-file .elenchus/issue-453-kf-453-02.json --require-guard --format json
```

Retain the bounded bootstrap result outside Git and stop unless it is
`guarded`. After the fix run
`python3 plugins/hexaemeron/tests/emit_issue_453_guard_report.py --case kf-453-02 --report .elenchus/issue-453-kf-453-02-green.json` and require clean,
positive completion. Lifecycle cases cover phase order, packet reconstruction,
complete and partial sets, explicit no-findings, legacy state, and unchanged
state/ledger/checkpoint bytes on every refusal. The instruction fixture adds
the inoculation node and its ordering before implementation, binds every
changed source span, adds a closed question and mutation for bypass, regenerates
`compact.wai` only from `model.json`, and updates exact counts and digests in
the manifest and coverage record. Re-run measurement and parity with the
manifest-pinned adapters; an unavailable adapter or changed reviewed answer
blocks this step rather than preserving stale evidence. The two agent
instruction test modules must accept the new exact corpus and reject every
stale derivative. Warden uses command
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`,
format `unittest-json-v1`, file `.elenchus/fiat-453-step-2-audit.json`, then
reruns every Exit command after a fix.

**Disciplines.** phylax: worker packets and controller arguments are
untrusted data, so closed keys, caps, portable paths, exact Git objects, and
mutation ordering are checked. ephoros: `status --json`, `next`, receipt
stdout, and named refusals expose phase, assigned count, remaining ids, and
no-findings provenance. metron: none, one extra interactive transition is the
selected design, not a latency claim. elenchus: `kf-453-02` proves the old
direct-to-implement path before the phase is added. hypomnema: the ADR draft
owns the phase and atomicity decision; Fiat's contract cites it without
inventing a merge-time number.

## Step 3: Bind guard evidence and refuse product edits

**Goal.** Build the `guard-evidence` module: retain exact reports, emit closed
per-finding manifests, bind them to Git and inventory bytes, and admit only
`guarded` before a product path exists.

**Entry.** Start from Step 2's signed, merged, and verified green exit. The
controller can stop at `inoculate`, but it does not yet retain report bytes or
prove the parent, guard paths, test blobs, command, outcome, or consuming step.

**Exit.** Elenchus can atomically retain a fresh bounded report before detached
worktree cleanup and emit one closed manifest for it. Each manifest binds the
finding id, inventory/study digest, consuming step, exact native step parent,
single-parent guard commit, sorted changed paths, test blob digests, exact test
command, report format and logical file, retained bytes and SHA-256, counters,
and verdict. Fiat reads the fixed controller-owned inoculation directory with
no-follow regular-file and stability checks, replays every binding from native
Git objects, and accepts the set atomically. Import error, timeout, empty or
skipped run, missing, stale, malformed, oversized or unstable report,
infrastructure error, mixed error/assertion, command or blob drift, wrong
parent, undeclared path, and `unguarded`, `passed`, or `inconclusive` each
refuse by name before state or ledger mutation. Only exact `guarded` opens
`implement`. Elenchus receives one provisional candidate generation row; its
four verdict meanings remain unchanged, and exact label resolution belongs to
the post-stack gate. Prove the green exit with:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_issue_453_guard_evidence -v
python3 -m unittest plugins.hexaemeron.tests.test_elenchus_checker -v
python3 scripts/portable_promise_machine.py sync
python3 scripts/portable_promise_machine.py check
python3 scripts/promise_machine.py check
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/run_checks.py --base 5bc2494c4f5802efcd8a92e58554809ac4b9f147
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/elenchus/SKILL.md plugins/hexaemeron/skills/elenchus/EVOLUTION.md plugins/hexaemeron/skills/fiat/SKILL.md plugins/hexaemeron/agents/mason.md plugins/hexaemeron/agents/warden.md audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md --max-defects 0
for draft in plugins/hexaemeron/skills/elenchus/SKILL.md plugins/hexaemeron/skills/elenchus/EVOLUTION.md plugins/hexaemeron/skills/fiat/SKILL.md plugins/hexaemeron/agents/mason.md plugins/hexaemeron/agents/warden.md audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md; do
  python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py "$draft" --mode report || exit 1
done
git diff --check
```

**Files.** Change
`plugins/hexaemeron/skills/elenchus/scripts/elenchus.py`,
`plugins/hexaemeron/skills/elenchus/SKILL.md`,
`plugins/hexaemeron/skills/elenchus/EVOLUTION.md`,
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/skills/fiat/SKILL.md`,
`plugins/hexaemeron/agents/mason.md`,
`plugins/hexaemeron/agents/warden.md`,
`plugins/hexaemeron/tests/test_elenchus_checker.py`,
`plugins/hexaemeron/tests/test_hexctl.py`, and
`tests/promise_machine_coverage.json`. Create
`plugins/hexaemeron/tests/test_issue_453_guard_evidence.py` and the fixtures
`plugins/hexaemeron/tests/fixtures/issue-453/guard-evidence.json`,
`plugins/hexaemeron/tests/fixtures/issue-453/guard-outcomes.json`, and
`plugins/hexaemeron/tests/fixtures/issue-453/path-boundary.json`. Regenerate
the ignored local portable verification payload without staging it and the
conditionally generated `.horos/` records. Warden alone changes the configured
audit record and synopsis.

**Tests.** Before product edits, make one signed guard-only commit from Step
2's merged exit using the union of the declared guard paths for `kf-453-03`,
`kf-453-04`, and `kf-453-05`, and run all three commands:

```bash
python3 plugins/hexaemeron/skills/elenchus/scripts/elenchus.py --ref <signed-guard-commit> --test-command "python3 plugins/hexaemeron/tests/emit_issue_453_guard_report.py --case kf-453-03 --report {report}" --report-format unittest-json-v1 --report-file .elenchus/issue-453-kf-453-03.json --require-guard --format json
python3 plugins/hexaemeron/skills/elenchus/scripts/elenchus.py --ref <signed-guard-commit> --test-command "python3 plugins/hexaemeron/tests/emit_issue_453_guard_report.py --case kf-453-04 --report {report}" --report-format unittest-json-v1 --report-file .elenchus/issue-453-kf-453-04.json --require-guard --format json
python3 plugins/hexaemeron/skills/elenchus/scripts/elenchus.py --ref <signed-guard-commit> --test-command "python3 plugins/hexaemeron/tests/emit_issue_453_guard_report.py --case kf-453-05 --report {report}" --report-format unittest-json-v1 --report-file .elenchus/issue-453-kf-453-05.json --require-guard --format json
```

Stop unless all three report `guarded`. On the fixed tree run each inventory
`green_command` for `kf-453-03` through `kf-453-05` and require positive,
complete, assertion-free reports. Table-driven cases cover every failure class
named in Exit, exact report retention, post-read replacement, native Git
replacement refusal, complete-set atomicity, and no mutation on refusal.
Warden's runner is command
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`,
format `unittest-json-v1`, file `.elenchus/fiat-453-step-3-audit.json`; rerun
the complete Exit after every fix.

**Disciplines.** phylax: subprocess argv, Git objects, declared paths, report
files, and retained evidence cross trust boundaries and need no-shell,
no-follow, cap, containment, freshness, stability, and atomic-write controls.
ephoros: manifests and refusals expose finding, parent, commit, command,
counters, digest, result, and phase without treating stderr as authority.
metron: none, existing size and timeout limits are retained without a speed
claim. elenchus: the three assigned guards cover missing binding, verdict
confusion, and path escape while preserving all four verdict meanings.
hypomnema: Elenchus's provisional candidate row owns exact report-byte
retention; the ADR owns controller permission, so neither contract restates
the other, and integration owns the exact label.

## Step 4: Recover inventory and require final green

**Goal.** Build the `recovery-and-final-green` module: replay inoculation
through every recovery surface and forbid implementation, audit, prose, push,
or step completion until the same cases and both suites are green.

**Entry.** Start from Step 3's signed, merged, and verified green exit. Fresh
guard evidence can open `implement`, but resume parity and fixed-tree closure
are not yet complete.

**Exit.** State, ledger, checkpoints, `status`, `next`, `verify`, restore, and
post-compaction delegation preserve the inventory/study digest, step parent,
assigned, completed, and remaining ids, report/manifest digests, and explicit
no-findings claim. Reconstruction rejects missing, reordered, stale, or
foreign evidence. `done implement` requires one final-green manifest for every
assigned id, produced by the same command identity on the final commit, with a
positive complete run, no skip, infrastructure error, or assertion failure;
it also binds successful root and Hexaemeron suite evidence. A red guard commit
cannot reach audit, prose, push, checkpoint completion, or handoff. Legacy
states remain readable without invented evidence. The audit-loop reference
states that the first Warden audit begins only after a complete inoculation
receipt and final-green implementation evidence. Fiat receives one provisional
candidate generation row, retaining its prior frontier fields; exact label
resolution belongs to the post-stack gate. Prove the green exit with:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_issue_453_recovery plugins.hexaemeron.tests.test_fiat_skill -v
python3 -m unittest plugins.hexaemeron.tests.test_hexctl_checkpoint plugins.hexaemeron.tests.test_hexctl_checkpoint_identity -v
python3 scripts/portable_promise_machine.py sync
python3 scripts/portable_promise_machine.py check
python3 scripts/promise_machine.py check
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/run_checks.py --base 5bc2494c4f5802efcd8a92e58554809ac4b9f147
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/fiat/SKILL.md plugins/hexaemeron/skills/fiat/references/controller-checkpoint.md plugins/hexaemeron/skills/fiat/references/audit-loop.md plugins/hexaemeron/skills/fiat/EVOLUTION.md audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md --max-defects 0
for draft in plugins/hexaemeron/skills/fiat/SKILL.md plugins/hexaemeron/skills/fiat/references/controller-checkpoint.md plugins/hexaemeron/skills/fiat/references/audit-loop.md plugins/hexaemeron/skills/fiat/EVOLUTION.md audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md; do
  python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py "$draft" --mode report || exit 1
done
git diff --check
```

**Files.** Change `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/skills/fiat/SKILL.md`,
`plugins/hexaemeron/skills/fiat/references/controller-checkpoint.md`,
`plugins/hexaemeron/skills/fiat/references/audit-loop.md`,
`plugins/hexaemeron/skills/fiat/EVOLUTION.md`,
`plugins/hexaemeron/tests/test_hexctl.py`,
`plugins/hexaemeron/tests/test_hexctl_checkpoint.py`,
`plugins/hexaemeron/tests/test_hexctl_checkpoint_identity.py`, and
`tests/promise_machine_coverage.json`. Create
`plugins/hexaemeron/tests/test_issue_453_recovery.py`,
`plugins/hexaemeron/tests/fixtures/issue-453/recovery.json`, and
`plugins/hexaemeron/tests/fixtures/issue-453/final-green.json`. Refresh the
ignored local portable verification payload without staging it and regenerate
the `.horos/` records only when their checker requires it. Warden alone changes
the configured audit record and synopsis.

**Tests.** Before product edits, make one signed guard-only commit from Step
3's merged exit using the union of the declared paths for `kf-453-06` and
`kf-453-07`, then run:

```bash
python3 plugins/hexaemeron/skills/elenchus/scripts/elenchus.py --ref <signed-guard-commit> --test-command "python3 plugins/hexaemeron/tests/emit_issue_453_guard_report.py --case kf-453-06 --report {report}" --report-format unittest-json-v1 --report-file .elenchus/issue-453-kf-453-06.json --require-guard --format json
python3 plugins/hexaemeron/skills/elenchus/scripts/elenchus.py --ref <signed-guard-commit> --test-command "python3 plugins/hexaemeron/tests/emit_issue_453_guard_report.py --case kf-453-07 --report {report}" --report-format unittest-json-v1 --report-file .elenchus/issue-453-kf-453-07.json --require-guard --format json
```

Stop unless both report `guarded`. Run both inventory `green_command` values
on the fixed tree. Recovery tests cover status, next, verify, checkpoint save
and restore, compaction, no-findings, final-green completeness, legacy states,
and unchanged bytes on every refusal. Fiat skill tests also pin that no audit
directive or Warden packet is available until both inoculation and final-green
evidence are receipted, and that the audit-loop reference states the same
ordering. Warden uses command
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`,
format `unittest-json-v1`, file `.elenchus/fiat-453-step-4-audit.json`, then
reruns every Exit command after each fix.

**Disciplines.** phylax: checkpoint and state bytes, Git ids, report paths,
and restored packets require the same bounded, stable, source-bound validation
as their writers. ephoros: status and next show remaining ids, phase, parent,
and evidence digests; verification names the first broken join. metron: none,
no recovery-speed claim is made. elenchus: `kf-453-06` and `kf-453-07` guard
resume parity, explicit emptiness, red-step containment, and fixed-tree green.
hypomnema: Fiat's provisional candidate row, checkpoint reference, and
audit-loop reference record recovery and completion semantics; historical
receipts are not rewritten, and integration owns the exact label.

## Step 5: Demonstrate and release the inoculation contract

**Goal.** Build the `release-demonstration` module: drive the checked-in
controller end to end in a disposable repository, reconcile prose and release
surfaces, and prove the complete five-step contract without claiming this run's
older controller enforced it.

**Entry.** Start from Step 4's signed, merged, and verified green exit. All
inventory, phase, evidence, recovery, and final-green behavior exists; the
disposable proof, package propagation, and final cold read remain.

**Exit.** `python3 plugins/hexaemeron/docs/known-failure-inoculation/proof.py`
creates a temporary signed repository, uses the tracked controller from the
final tree, atomically writes the bounded sibling `proof.md` transcript, and
checks that transcript against the run it just completed. It proves
runbook-to-inoculate order, one early-product refusal,
every non-guard verdict and runner-fault refusal, exact report-byte and Git
binding, one explicit no-known-findings step, resume, fixed-tree guard success,
audit entry, and final verification with unchanged state/ledger digests around
refusals. It records controller and source digests, commands, exits, counts,
and evidence digests without credentials or raw signatures. The proof states
that this run used only the manual bootstrap procedure.

The three declared skill ledgers carry one provisional candidate generation
each. The two plugin manifests and two marketplace records carry one matching
candidate Hexaemeron package increment. The three hard-pinned version
consumers agree with those candidate bytes. These values become exact only
after any base-sync correction and the post-stack `done resolve-versions`
receipt. The ADR allocator assigns the numberless draft only during final
composition. The portable runtime is an ignored local verification payload,
not a committed release surface; Horos records remain generator-produced. The
study, runbook, proof, skill contracts, worker roles, ADR, audit, ledgers,
manifests, marketplaces, and version consumers make the same bounded claim.
Issue #363 and all unrelated audit sources remain unchanged. Prove the final
green candidate tree with:

```bash
python3 plugins/hexaemeron/docs/known-failure-inoculation/proof.py
python3 -m unittest plugins.hexaemeron.tests.test_issue_453_known_failure_inventory plugins.hexaemeron.tests.test_issue_453_inoculation_lifecycle plugins.hexaemeron.tests.test_issue_453_guard_evidence plugins.hexaemeron.tests.test_issue_453_recovery -v
python3 scripts/portable_promise_machine.py sync
python3 scripts/portable_promise_machine.py check
python3 scripts/promise_machine.py check
python3 plugins/horos/skills/horos/scripts/horos.py scan . --write
python3 plugins/horos/skills/horos/scripts/horos.py check .
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 -m unittest tests.test_version_propagation tests.test_evolution_contract plugins.hexaemeron.tests.test_phylax_model_proxy -v
python3 scripts/run_checks.py --base 5bc2494c4f5802efcd8a92e58554809ac4b9f147
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study plugins/hexaemeron/docs/known-failure-inoculation/study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py plugins/hexaemeron/docs/known-failure-inoculation/runbook.md
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/docs/known-failure-inoculation/study.md plugins/hexaemeron/docs/known-failure-inoculation/runbook.md plugins/hexaemeron/docs/known-failure-inoculation/proof.md plugins/hexaemeron/skills/protasis/SKILL.md plugins/hexaemeron/skills/protasis/EVOLUTION.md plugins/hexaemeron/skills/fiat/SKILL.md plugins/hexaemeron/skills/fiat/EVOLUTION.md plugins/hexaemeron/skills/fiat/references/controller-checkpoint.md plugins/hexaemeron/skills/fiat/references/audit-loop.md plugins/hexaemeron/skills/elenchus/SKILL.md plugins/hexaemeron/skills/elenchus/EVOLUTION.md plugins/hexaemeron/agents/mason.md plugins/hexaemeron/agents/warden.md docs/agent-instruction-language-v1.md docs/decisions/drafts/require-inoculation-before-implementation.md audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md --max-defects 0
for draft in plugins/hexaemeron/docs/known-failure-inoculation/study.md plugins/hexaemeron/docs/known-failure-inoculation/runbook.md plugins/hexaemeron/docs/known-failure-inoculation/proof.md plugins/hexaemeron/skills/protasis/SKILL.md plugins/hexaemeron/skills/fiat/SKILL.md plugins/hexaemeron/skills/fiat/references/controller-checkpoint.md plugins/hexaemeron/skills/fiat/references/audit-loop.md plugins/hexaemeron/skills/elenchus/SKILL.md plugins/hexaemeron/agents/mason.md plugins/hexaemeron/agents/warden.md docs/agent-instruction-language-v1.md docs/decisions/drafts/require-inoculation-before-implementation.md audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md; do
  python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py "$draft" --mode report || exit 1
done
git diff --check
```

**Files.** Create
`plugins/hexaemeron/docs/known-failure-inoculation/proof.py` as the disposable
generator/checker and
`plugins/hexaemeron/docs/known-failure-inoculation/proof.md` as its bounded,
deterministic transcript. Change
`plugins/hexaemeron/README.md`,
`plugins/hexaemeron/.claude-plugin/plugin.json`,
`plugins/hexaemeron/.codex-plugin/plugin.json`,
`.claude-plugin/marketplace.json`, and
`.agents/plugins/marketplace.json`,
`tests/test_version_propagation.py`,
`plugins/hexaemeron/tests/test_phylax_model_proxy.py`, and
`tests/test_evolution_contract.py`. Reconcile the three declared
`EVOLUTION.md` files without adding a second candidate row, and update
`tests/promise_machine_coverage.json` only for final source digests. Regenerate
the ignored local `.agents/skills/promise-machine/runtime/` verification
payload and its manifest without staging them, then regenerate
`.horos/boundary.json`, `.horos/candidates.json`, and `.horos/census.json` from
their repository scripts. The integration allocator renames and numbers
`docs/decisions/drafts/require-inoculation-before-implementation.md`. Warden
alone completes the configured audit record and synopsis.

**Tests.** No finding is assigned to this step. Before any release edit,
record a non-empty no-known-findings claim below
`.hexaemeron/bootstrap/step-5/` that binds the receipted study digest, all three
inventory source-view digest pairs, step 5, and the assertion that none of the
seven entries applies; an empty array is not evidence. The disposable proof
must then pass the same form through the checked-in controller, write
`proof.md`, and refuse when replay changes any bound command, exit, count,
commit, path, or digest. Warden's exact audit runner is command
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`,
format `unittest-json-v1`, file `.elenchus/fiat-453-step-5-audit.json`. The
proof and four focused modules run before and after every audit fix, followed
by every Exit command. No test count is predicted; every structured report
records a positive completed count, zero skip/error/failure on the fixed tree,
and its exact command and digest. Version tests cover both manifests, both
marketplaces, every declared skill row and metadata value, and the three
hard-pinned consumers. After this step merges, obey any sync directive, correct
all provisional values and pins against the new base, rerun these commands,
and require `hexctl done resolve-versions` to exit zero before integration.

**Disciplines.** phylax: the proof creates local Git state, invokes
subprocesses, reads evidence, and writes only bounded temporary and generated
paths; it uses argv, no network, no secret output, and cleans up. ephoros: the
proof maps each operator question to phase, id set, parent, command, result,
count, or digest and checks refusal messages without promoting diagnostics to
evidence. metron: none, the proof measures correctness and makes no latency or
throughput claim. elenchus: the demo replays every named failure and shows each
guard clean only after the product fix. hypomnema: the final ADR, three
provisional candidate rows, proof, and committed study/runbook are the durable
homes; integration resolves exact labels, and package metadata only identifies
the released bytes after that gate.

### Amendment -- 2026-09-05

**What changed.** Complete replacement Files: Create
`plugins/hexaemeron/docs/known-failure-inoculation/study.md`,
`plugins/hexaemeron/docs/known-failure-inoculation/runbook.md`,
`plugins/hexaemeron/skills/protasis/scripts/known_failure_inventory.py`,
`plugins/hexaemeron/tests/test_issue_453_known_failure_inventory.py`,
`plugins/hexaemeron/tests/emit_issue_453_guard_report.py`, and
`plugins/hexaemeron/tests/fixtures/issue-453/inventory.json`. Change
`plugins/hexaemeron/skills/protasis/SKILL.md`,
`plugins/hexaemeron/skills/protasis/EVOLUTION.md`,
`tests/test_evolution_contract.py`, and
`tests/promise_machine_coverage.json`. Generate the ignored local verification
payload at `.agents/skills/promise-machine/runtime/` and its `MANIFEST.json`
with the repository script, but do not stage or describe it as a release file;
regenerate `.horos/boundary.json`, `.horos/candidates.json`, and
`.horos/census.json` only when the repository-owned scan changes them. Warden
alone appends
`audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md` and its
sibling `.synopsis.md`.

**Why.** Step 1's provisional Protasis generation row changes the ledger's
current and latest version. The repository-wide suite pins both values in
`tests/test_evolution_contract.py`; with the candidate ledger present and that
test untouched, the exact focused case fails before checking any Step 1
behaviour. Moving the two matching assertions with the row keeps the declared
full-suite exit green and makes the test change part of the same version
contract, while Step 5 retains authority to reconcile it if integration-base
resolution changes the candidate label.

**Steps touched.** Step 1's Files field only.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5:
entry holds; exit holds.

### Amendment -- 2026-09-05

**What changed.** Complete replacement Files: Create
`plugins/hexaemeron/docs/known-failure-inoculation/study.md`,
`plugins/hexaemeron/docs/known-failure-inoculation/runbook.md`,
`plugins/hexaemeron/skills/protasis/scripts/known_failure_inventory.py`,
`plugins/hexaemeron/tests/test_issue_453_known_failure_inventory.py`,
`plugins/hexaemeron/tests/emit_issue_453_guard_report.py`, and
`plugins/hexaemeron/tests/fixtures/issue-453/inventory.json`. Change
`plugins/hexaemeron/skills/protasis/SKILL.md`,
`plugins/hexaemeron/skills/protasis/EVOLUTION.md`,
`tests/test_evolution_contract.py`, and
`tests/promise_machine_coverage.json`. Generate the ignored local verification
payload at `.agents/skills/promise-machine/runtime/` and its `MANIFEST.json`
with the repository script, but do not stage or describe it as a release file;
regenerate `.horos/boundary.json`, `.horos/candidates.json`, and
`.horos/census.json` only when the repository-owned scan changes them. Warden
alone appends
`audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md` and its
sibling `.synopsis.md`.

**Why.** The preceding amendment correctly added the evolution-contract test
but described only its two version-value assertions. The same test method also
pins the newest row's evidence and change text to the prior generation. Those
three assertions must move to the new study, runbook, and inventory-contract
evidence with the candidate row; copying the prior row's evidence into the new
row would misstate what changed. Assertions over the prior row remain in place
as historical checks.

**Steps touched.** Step 1's Files field only.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5:
entry holds; exit holds.

### Amendment -- 2026-09-05

**What changed.** Complete replacement Exit: The
`protasis-known-failure-inventory/v1` object is parsed from one bounded, stable
study. The parser requires every source/view path and SHA-256, every finding
field, one assignment to a real unfenced runbook step, one closed reporter argv
with one exact `{report}` argument, an admitted report format, portable guard
and report paths, and either a non-empty finding set or a digest-bound
no-known-findings claim. Duplicate keys, omitted or extra ids, stale views or
sources, unsafe paths, bad caps, command substitution, and unassigned entries
refuse with no state or ledger write. The accepted seven-entry inventory
assigns `kf-453-01` to this step. `docs/known-failure-inoculation-study.md` and
`plugins/hexaemeron/docs/known-failure-inoculation/runbook.md` are byte-identical
to the current receipted artefacts. The numberless ADR draft records the chosen
cross-cutting phase and evidence boundary before the study ships. Protasis
receives one provisional candidate generation row whose prior frontier fields
remain unchanged; exact label resolution belongs to the post-stack gate. The
toolchain, CI, licences, and dependencies remain unchanged.

Run `python3 -m unittest discover -s tests` from a clean detached worktree at
the exact Step 1 commit: two inherited corpus tests inspect a root
`.hexaemeron/design-evidence.json`, so the live controller worktree is not a
clean root-suite input. Prove the complete exit with:

```bash
cmp .hexaemeron/study.md docs/known-failure-inoculation-study.md
cmp .hexaemeron/runbook.md plugins/hexaemeron/docs/known-failure-inoculation/runbook.md
python3 -m unittest plugins.hexaemeron.tests.test_issue_453_known_failure_inventory -v
python3 plugins/hexaemeron/skills/protasis/scripts/known_failure_inventory.py docs/known-failure-inoculation-study.md plugins/hexaemeron/docs/known-failure-inoculation/runbook.md --repository . --expected-id kf-453-01 --expected-id kf-453-02 --expected-id kf-453-03 --expected-id kf-453-04 --expected-id kf-453-05 --expected-id kf-453-06 --expected-id kf-453-07
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/known-failure-inoculation-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py plugins/hexaemeron/docs/known-failure-inoculation/runbook.md
python3 scripts/portable_promise_machine.py sync
python3 scripts/portable_promise_machine.py check
python3 scripts/promise_machine.py check
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/run_checks.py --base 5bc2494c4f5802efcd8a92e58554809ac4b9f147
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/known-failure-inoculation-study.md plugins/hexaemeron/docs/known-failure-inoculation/runbook.md plugins/hexaemeron/skills/protasis/SKILL.md plugins/hexaemeron/skills/protasis/EVOLUTION.md docs/decisions/drafts/require-inoculation-before-implementation.md audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md --max-defects 0
for draft in plugins/hexaemeron/skills/protasis/SKILL.md plugins/hexaemeron/skills/protasis/EVOLUTION.md docs/decisions/drafts/require-inoculation-before-implementation.md audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md; do
  python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py "$draft" --mode report || exit 1
done
git diff --check
```

The study and runbook are completeness-oriented specification artefacts, so
the recorded Brevitas applicability boundary excludes them; their complete
inventory block and glossary remain intact. Imprimatur and Hypomnema still
check their exact shipped bytes.

Complete replacement Files: Create
`docs/known-failure-inoculation-study.md`,
`plugins/hexaemeron/docs/known-failure-inoculation/runbook.md`,
`plugins/hexaemeron/skills/protasis/scripts/known_failure_inventory.py`,
`plugins/hexaemeron/tests/test_issue_453_known_failure_inventory.py`,
`plugins/hexaemeron/tests/emit_issue_453_guard_report.py`,
`plugins/hexaemeron/tests/fixtures/issue-453/inventory.json`, and
`docs/decisions/drafts/require-inoculation-before-implementation.md`. Change
`plugins/hexaemeron/skills/protasis/SKILL.md`,
`plugins/hexaemeron/skills/protasis/EVOLUTION.md`,
`tests/test_evolution_contract.py`, and
`tests/promise_machine_coverage.json`. Generate the ignored local verification
payload at `.agents/skills/promise-machine/runtime/` and its `MANIFEST.json`
with the repository script, but do not stage or describe it as a release file;
regenerate `.horos/boundary.json`, `.horos/candidates.json`, and
`.horos/census.json` only when the repository-owned scan changes them. Warden
alone appends
`audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md` and its
sibling `.synopsis.md`.

**Why.** The byte-identical study's five discipline links resolve from root
`docs/` but not from the plugin-local directory originally named. The committed
runbook also cites the stable cross-cutting ADR identity, and Hypomnema refuses
that dangling reference until the already-selected decision has its draft.
Moving the exact study bytes and the ADR creation into this step makes the
required whole-tree pointer gate true without rewriting receipted evidence or
deferring a record past the step that ships its source. Brevitas reports the
study's required 95-line inventory and ten glossary labels as structural
defects even though its applicability receipt excludes completeness-oriented
specifications, so those two exact documents are removed from that loop rather
than edited to satisfy an inapplicable budget.

**Steps touched.** Step 1's Exit and Files fields only.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5:
entry holds; exit holds.

### Amendment -- 2026-09-05

**What changed.** Complete replacement Files: Change
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/skills/fiat/SKILL.md`,
`plugins/hexaemeron/agents/mason.md`,
`plugins/hexaemeron/tests/test_hexctl.py`,
`plugins/hexaemeron/tests/test_fiat_skill.py`,
`scripts/agent_instruction.py`,
`tests/test_agent_instruction.py`,
`tests/test_agent_instruction_corpus.py`,
`docs/agent-instruction-language-v1.md`,
`tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/model.json`,
`tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/compact.wai`,
`tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/questions.json`,
`tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/mutations.json`,
`tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/source-spans.json`,
`tests/fixtures/agent-instruction-v1/manifest.json`,
`tests/fixtures/agent-instruction-v1/evidence/measurement.json`,
`tests/fixtures/agent-instruction-v1/evidence/parity.json`, and
`tests/promise_machine_coverage.json`. Create
`plugins/hexaemeron/tests/test_issue_453_inoculation_lifecycle.py` and
`plugins/hexaemeron/tests/fixtures/issue-453/no-known-findings.json`. The
existing
`docs/decisions/drafts/require-inoculation-before-implementation.md` remains
the stable numberless record and is read but not changed. Refresh the ignored
local portable verification payload without staging it and, only when their
generators change them, the three `.horos/` records named in Step 1. Warden
alone changes the configured audit record and synopsis.

**Why.** Step 1 now creates the stable ADR draft before it ships the study that
selected that cross-cutting decision. Step 2 implements the recorded phase and
evidence boundary; creating the same stable identity again would be false and
would fail the unique-record gate. The decision and rejected alternatives are
already settled, so Step 2 reads the record and leaves its bytes unchanged.

**Steps touched.** Step 2's Files field only.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5:
entry holds; exit holds.

### Amendment -- 2026-09-05

**What changed.** Complete replacement Exit: The
`protasis-known-failure-inventory/v1` object is parsed from one bounded, stable
study. The parser requires every source/view path and SHA-256, every finding
field, one assignment to a real unfenced runbook step, one closed reporter argv
with one exact `{report}` argument, an admitted report format, portable guard
and report paths, and either a non-empty finding set or a digest-bound
no-known-findings claim. Duplicate keys, omitted or extra ids, stale views or
sources, unsafe paths, bad caps, command substitution, and unassigned entries
refuse with no state or ledger write. The accepted seven-entry inventory
assigns `kf-453-01` to this step. `docs/known-failure-inoculation-study.md` and
`plugins/hexaemeron/docs/known-failure-inoculation/runbook.md` are byte-identical
to the current receipted artefacts. The numberless ADR draft records the chosen
cross-cutting phase and evidence boundary before the study ships. Protasis
receives one provisional candidate generation row whose prior frontier fields
remain unchanged; exact label resolution belongs to the post-stack gate. The
toolchain, CI, licences, and dependencies remain unchanged.

Run `python3 -m unittest discover -s tests` from a clean detached worktree at
the exact Step 1 commit: two inherited corpus tests inspect a root
`.hexaemeron/design-evidence.json`, so the live controller worktree is not a
clean root-suite input. Prove the complete exit with:

```bash
cmp .hexaemeron/study.md docs/known-failure-inoculation-study.md
cmp .hexaemeron/runbook.md plugins/hexaemeron/docs/known-failure-inoculation/runbook.md
python3 -m unittest plugins.hexaemeron.tests.test_issue_453_known_failure_inventory -v
python3 plugins/hexaemeron/skills/protasis/scripts/known_failure_inventory.py docs/known-failure-inoculation-study.md plugins/hexaemeron/docs/known-failure-inoculation/runbook.md --repository . --expected-id kf-453-01 --expected-id kf-453-02 --expected-id kf-453-03 --expected-id kf-453-04 --expected-id kf-453-05 --expected-id kf-453-06 --expected-id kf-453-07
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/known-failure-inoculation-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py plugins/hexaemeron/docs/known-failure-inoculation/runbook.md
python3 scripts/portable_promise_machine.py sync
python3 scripts/portable_promise_machine.py check
python3 scripts/promise_machine.py check
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/run_checks.py --base 5bc2494c4f5802efcd8a92e58554809ac4b9f147
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/plugins/marketplace.json .agents/skills/promise-machine/PORTABLE.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/scripts/verify_runtime.py plugins docs
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/known-failure-inoculation-study.md plugins/hexaemeron/docs/known-failure-inoculation/runbook.md plugins/hexaemeron/skills/protasis/SKILL.md plugins/hexaemeron/skills/protasis/EVOLUTION.md docs/decisions/drafts/require-inoculation-before-implementation.md audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md --max-defects 0
for draft in plugins/hexaemeron/skills/protasis/SKILL.md docs/decisions/drafts/require-inoculation-before-implementation.md audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md; do
  python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py "$draft" --mode report || exit 1
done
git diff --check
```

The study and runbook are completeness-oriented specification artefacts, so
the recorded Brevitas applicability boundary excludes them; their complete
inventory block and glossary remain intact. The evolution ledger is a fixed
single-table version register whose required Hypomnema pragma interrupts its
table, so it is not engineering prose and is excluded from that prose budget.
Imprimatur and Hypomnema still check all five exact shipped documents. The
Hypomnema command names the four tracked `.agents` inputs explicitly so it
checks their authored links without traversing the ignored generated portable
runtime.

**Why.** The preceding replacement sent the structured evolution ledger
through a prose-only shape budget and sent Hypomnema through an ignored runtime
tree produced by `portable_promise_machine.py sync`. The base ledger already
fails Brevitas because its one required History section and pragma-separated
table cannot satisfy the prose heading and real-data-table heuristics. The
ignored runtime contains deliberately partial portable copies whose links
resolve only in the source tree, while all four tracked `.agents` inputs and
the complete authored tree pass the pointer check. Narrowing both commands to
their applicable authored inputs removes those inherited false gates without
changing a study fact, parser promise, product path, or verification outcome.

**Steps touched.** Step 1's Exit field only.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5:
entry holds; exit holds.

### Amendment -- 2026-09-05

**What changed.** Complete replacement Exit: The
`protasis-known-failure-inventory/v1` object is parsed from one bounded, stable
study. The parser requires every source/view path and SHA-256, every finding
field, one assignment to a real unfenced runbook step, one closed reporter argv
with one exact `{report}` argument, an admitted report format, portable guard
and report paths, and either a non-empty finding set or a digest-bound
no-known-findings claim. Duplicate keys, omitted or extra ids, stale views or
sources, unsafe paths, bad caps, command substitution, and unassigned entries
refuse with no state or ledger write. The accepted seven-entry inventory is bound by these exact visible records:

Known-failure assignment: `kf-453-01` -> Step 1
Known-failure assignment: `kf-453-02` -> Step 2
Known-failure assignment: `kf-453-03` -> Step 3
Known-failure assignment: `kf-453-04` -> Step 3
Known-failure assignment: `kf-453-05` -> Step 3
Known-failure assignment: `kf-453-06` -> Step 4
Known-failure assignment: `kf-453-07` -> Step 4

`docs/known-failure-inoculation-study.md` and
`plugins/hexaemeron/docs/known-failure-inoculation/runbook.md` are byte-identical
to the current receipted artefacts. The numberless ADR draft records the chosen
cross-cutting phase and evidence boundary before the study ships. Protasis
receives one provisional candidate generation row whose prior frontier fields
remain unchanged; exact label resolution belongs to the post-stack gate. The
toolchain, CI, licences, and dependencies remain unchanged.

Run `python3 -m unittest discover -s tests` from a clean detached worktree at
the exact Step 1 commit: two inherited corpus tests inspect a root
`.hexaemeron/design-evidence.json`, so the live controller worktree is not a
clean root-suite input. Prove the complete exit with:

```bash
cmp .hexaemeron/study.md docs/known-failure-inoculation-study.md
cmp .hexaemeron/runbook.md plugins/hexaemeron/docs/known-failure-inoculation/runbook.md
python3 -m unittest plugins.hexaemeron.tests.test_issue_453_known_failure_inventory -v
python3 plugins/hexaemeron/skills/protasis/scripts/known_failure_inventory.py docs/known-failure-inoculation-study.md plugins/hexaemeron/docs/known-failure-inoculation/runbook.md --repository . --expected-id kf-453-01 --expected-id kf-453-02 --expected-id kf-453-03 --expected-id kf-453-04 --expected-id kf-453-05 --expected-id kf-453-06 --expected-id kf-453-07
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/known-failure-inoculation-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py plugins/hexaemeron/docs/known-failure-inoculation/runbook.md
python3 scripts/portable_promise_machine.py sync
python3 scripts/portable_promise_machine.py check
python3 scripts/promise_machine.py check
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/run_checks.py --base 5bc2494c4f5802efcd8a92e58554809ac4b9f147
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/plugins/marketplace.json .agents/skills/promise-machine/PORTABLE.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/scripts/verify_runtime.py plugins docs
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/known-failure-inoculation-study.md plugins/hexaemeron/docs/known-failure-inoculation/runbook.md plugins/hexaemeron/skills/protasis/SKILL.md plugins/hexaemeron/skills/protasis/EVOLUTION.md docs/decisions/drafts/require-inoculation-before-implementation.md audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md --max-defects 0
for draft in plugins/hexaemeron/skills/protasis/SKILL.md docs/decisions/drafts/require-inoculation-before-implementation.md audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md; do
  python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py "$draft" --mode report || exit 1
done
git diff --check
```

The study and runbook are completeness-oriented specification artefacts, so
the recorded Brevitas applicability boundary excludes them; their complete
inventory block and glossary remain intact. The evolution ledger is a fixed
single-table version register whose required Hypomnema pragma interrupts its
table, so it is not engineering prose and is excluded from that prose budget.
Imprimatur and Hypomnema still check all five exact shipped documents. The
Hypomnema command names the four tracked `.agents` inputs explicitly so it
checks their authored links without traversing the ignored generated portable
runtime.

**Why.** The preceding replacement validated an id whenever it appeared in an
unfenced Step section. That admits an inert comment, link target, or negated
sentence as if it were the study's operative assignment. The seven closed
records above give the parser one visible full-line grammar, name the consuming
step directly, and leave every other mention non-authoritative. Requiring each
inventory id exactly once and checking its named positive step against
`consumes_step` closes the correlation boundary without changing any finding,
guard path, command, or step allocation.

**Steps touched.** Step 1's Exit field only.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5:
entry holds; exit holds.

### Amendment -- 2026-09-05

**What changed.** Complete replacement Exit: The
`protasis-known-failure-inventory/v1` object is parsed from one bounded, stable
study. The parser requires every source/view path and SHA-256, every finding
field, one assignment to a real unfenced runbook step, one closed reporter argv
with one exact `{report}` argument, an admitted report format, portable guard
and report paths, and either a non-empty finding set or a digest-bound
no-known-findings claim. Duplicate keys, omitted or extra ids, stale views or
sources, unsafe paths, bad caps, command substitution, and unassigned entries
refuse with no state or ledger write. The accepted seven-entry inventory is
bound by these exact visible records:

Known-failure assignment: `kf-453-01` -> Step 1
Known-failure assignment: `kf-453-02` -> Step 2
Known-failure assignment: `kf-453-03` -> Step 3
Known-failure assignment: `kf-453-04` -> Step 3
Known-failure assignment: `kf-453-05` -> Step 3
Known-failure assignment: `kf-453-06` -> Step 4
Known-failure assignment: `kf-453-07` -> Step 4

`docs/known-failure-inoculation-study.md` and
`plugins/hexaemeron/docs/known-failure-inoculation/runbook.md` are byte-identical
to the current receipted artefacts. The numberless ADR draft records the chosen
cross-cutting phase and evidence boundary before the study ships. Protasis
receives one provisional candidate generation row whose prior frontier fields
remain unchanged; exact label resolution belongs to the post-stack gate. The
toolchain, CI, licences, and dependencies remain unchanged.

Run `python3 -m unittest discover -s tests` from a clean detached worktree at
the exact Step 1 commit. The live controller worktree carries a root
`.hexaemeron/design-evidence.json` inspected by two corpus tests and is not a
clean root-suite input. Prove the complete exit with:

```bash
cmp .hexaemeron/study.md docs/known-failure-inoculation-study.md
cmp .hexaemeron/runbook.md plugins/hexaemeron/docs/known-failure-inoculation/runbook.md
python3 -m unittest plugins.hexaemeron.tests.test_known_failure_inventory -v
python3 plugins/hexaemeron/skills/protasis/scripts/known_failure_inventory.py docs/known-failure-inoculation-study.md plugins/hexaemeron/docs/known-failure-inoculation/runbook.md --repository . --expected-id kf-453-01 --expected-id kf-453-02 --expected-id kf-453-03 --expected-id kf-453-04 --expected-id kf-453-05 --expected-id kf-453-06 --expected-id kf-453-07
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/known-failure-inoculation-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py plugins/hexaemeron/docs/known-failure-inoculation/runbook.md
python3 scripts/portable_promise_machine.py sync
python3 scripts/portable_promise_machine.py check
python3 scripts/promise_machine.py check
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/run_checks.py --base 5bc2494c4f5802efcd8a92e58554809ac4b9f147
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/plugins/marketplace.json .agents/skills/promise-machine/PORTABLE.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/scripts/verify_runtime.py plugins docs
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/known-failure-inoculation-study.md plugins/hexaemeron/docs/known-failure-inoculation/runbook.md plugins/hexaemeron/skills/protasis/SKILL.md plugins/hexaemeron/skills/protasis/EVOLUTION.md docs/decisions/drafts/require-inoculation-before-implementation.md audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md --max-defects 0
for draft in plugins/hexaemeron/skills/protasis/SKILL.md docs/decisions/drafts/require-inoculation-before-implementation.md audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md; do
  python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py "$draft" --mode report || exit 1
done
git diff --check
```

The study and runbook are completeness-oriented specification artefacts, so
the recorded Brevitas applicability boundary excludes them; their complete
inventory block and glossary remain intact. The evolution ledger is a fixed
single-table version register whose required Hypomnema pragma interrupts its
table, so it is not engineering prose and is excluded from that prose budget.
Imprimatur and Hypomnema still check all five exact shipped documents. The
Hypomnema command names the four tracked `.agents` inputs explicitly so it
checks their authored links without traversing the ignored generated portable
runtime.

Complete replacement Files: Rename
`plugins/hexaemeron/tests/test_issue_453_known_failure_inventory.py` to
`plugins/hexaemeron/tests/test_known_failure_inventory.py` after preserving the
signed guard proof at its historical path. Create
`docs/known-failure-inoculation-study.md`,
`plugins/hexaemeron/docs/known-failure-inoculation/runbook.md`,
`plugins/hexaemeron/skills/protasis/scripts/known_failure_inventory.py`,
`plugins/hexaemeron/tests/emit_issue_453_guard_report.py`,
`plugins/hexaemeron/tests/fixtures/issue-453/inventory.json`, and
`docs/decisions/drafts/require-inoculation-before-implementation.md`. Change
`plugins/hexaemeron/skills/protasis/SKILL.md`,
`plugins/hexaemeron/skills/protasis/EVOLUTION.md`,
`tests/test_evolution_contract.py`,
`tests/test_promise_machine_contract.py`, and
`tests/promise_machine_coverage.json`. Generate the ignored local verification
payload at `.agents/skills/promise-machine/runtime/` and its `MANIFEST.json`
with the repository script, but do not stage or describe it as a release file.
Regenerate `.horos/boundary.json`, `.horos/candidates.json`, and
`.horos/census.json` when the repository-owned scan changes them; the clean
exact-commit suite at `dfd380b83bd459a862184272ba91fb241fba5568` proves the
count drift, so this step must refresh the records. Warden alone appends
`audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md` and its
sibling `.synopsis.md`.

**Why.** The first signed product commit reached the required clean detached
root-suite boundary and exposed four integration failures that the dirty
controller worktree could not classify. Two are the conditionally declared
Horos count drift. The new promise heading also requires the root contract
population test to name it, and the repository naming gate refuses a maintained
test module named for issue 453. Renaming that module after the historical
guard proof preserves the signed failing object while making the maintained
surface behavioural. Updating the focused command and hard-coded promise
population closes the two contract failures without changing the inventory,
guard verdict, parser behaviour, or selected design.

**Steps touched.** Step 1's Exit and Files fields.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5:
entry holds; exit holds.

### Amendment -- 2026-09-05

**What changed.** Complete replacement Exit: The
`protasis-known-failure-inventory/v1` object is parsed from one bounded, stable
study. The parser requires every source/view path and SHA-256, every finding
field, one assignment to a real unfenced runbook step, one closed reporter argv
with one exact `{report}` argument, an admitted report format, portable guard
and report paths, and either a non-empty finding set or a digest-bound
no-known-findings claim. Duplicate keys, omitted or extra ids, stale views or
sources, unsafe paths, bad caps, command substitution, and unassigned entries
refuse with no state or ledger write.

Assignment authority is derived from the checked runbook bytes alone. Its
generation zero is the visible baseline before the first real amendment.
Every structurally valid full Exit field supplied by a real amendment replaces
the whole generation; the final such value alone is authoritative even when
empty, while amendments replacing only other fields preserve it. Superseded
Exit records remain readable history but are not counted. Step headings come
only from the baseline. Assignment-like lines in non-Exit amendment scopes,
ambiguous or malformed amendment and replacement boundaries, repeated Exit
clauses, and post-amendment Step headings refuse. The existing exact-line,
assignment-only-block, uniqueness, and step-correlation rules apply only to
the effective generation, so every later full Exit replacement must restate
the whole set. The accepted seven-entry inventory is bound by these exact
visible records:

Known-failure assignment: `kf-453-01` -> Step 1
Known-failure assignment: `kf-453-02` -> Step 2
Known-failure assignment: `kf-453-03` -> Step 3
Known-failure assignment: `kf-453-04` -> Step 3
Known-failure assignment: `kf-453-05` -> Step 3
Known-failure assignment: `kf-453-06` -> Step 4
Known-failure assignment: `kf-453-07` -> Step 4

`docs/known-failure-inoculation-study.md` and
`plugins/hexaemeron/docs/known-failure-inoculation/runbook.md` are byte-identical
to the current receipted artefacts. The numberless ADR draft records the chosen
cross-cutting phase and evidence boundary before the study ships. Protasis
receives one provisional candidate generation row whose prior frontier fields
remain unchanged; exact label resolution belongs to the post-stack gate. The
toolchain, CI, licences, and dependencies remain unchanged.

Run `python3 -m unittest discover -s tests` from a clean detached worktree at
the exact Step 1 commit. The live controller worktree carries a root
`.hexaemeron/design-evidence.json` inspected by two corpus tests and is not a
clean root-suite input. Prove the complete exit with:

```bash
cmp .hexaemeron/study.md docs/known-failure-inoculation-study.md
cmp .hexaemeron/runbook.md plugins/hexaemeron/docs/known-failure-inoculation/runbook.md
python3 -m unittest plugins.hexaemeron.tests.test_known_failure_inventory -v
python3 plugins/hexaemeron/skills/protasis/scripts/known_failure_inventory.py docs/known-failure-inoculation-study.md plugins/hexaemeron/docs/known-failure-inoculation/runbook.md --repository . --expected-id kf-453-01 --expected-id kf-453-02 --expected-id kf-453-03 --expected-id kf-453-04 --expected-id kf-453-05 --expected-id kf-453-06 --expected-id kf-453-07
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/known-failure-inoculation-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py plugins/hexaemeron/docs/known-failure-inoculation/runbook.md
python3 scripts/portable_promise_machine.py sync
python3 scripts/portable_promise_machine.py check
python3 scripts/promise_machine.py check
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/run_checks.py --base 5bc2494c4f5802efcd8a92e58554809ac4b9f147
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/plugins/marketplace.json .agents/skills/promise-machine/PORTABLE.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/scripts/verify_runtime.py plugins docs
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/known-failure-inoculation-study.md plugins/hexaemeron/docs/known-failure-inoculation/runbook.md plugins/hexaemeron/skills/protasis/SKILL.md plugins/hexaemeron/skills/protasis/EVOLUTION.md docs/decisions/drafts/require-inoculation-before-implementation.md audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md --max-defects 0
for draft in plugins/hexaemeron/skills/protasis/SKILL.md docs/decisions/drafts/require-inoculation-before-implementation.md audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md; do
  python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py "$draft" --mode report || exit 1
done
git diff --check
```

The study and runbook are completeness-oriented specification artefacts, so
the recorded Brevitas applicability boundary excludes them; their complete
inventory block and glossary remain intact. The evolution ledger is a fixed
single-table version register whose required Hypomnema pragma interrupts its
table, so it is not engineering prose and is excluded from that prose budget.
Imprimatur and Hypomnema still check all five exact shipped documents. The
Hypomnema command names the four tracked `.agents` inputs explicitly so it
checks their authored links without traversing the ignored generated portable
runtime.

Complete replacement Files: Rename
`plugins/hexaemeron/tests/test_issue_453_known_failure_inventory.py` to
`plugins/hexaemeron/tests/test_known_failure_inventory.py` after preserving the
signed guard proof at its historical path. Create
`docs/known-failure-inoculation-study.md`,
`plugins/hexaemeron/docs/known-failure-inoculation/runbook.md`,
`plugins/hexaemeron/skills/protasis/scripts/known_failure_inventory.py`,
`plugins/hexaemeron/tests/emit_issue_453_guard_report.py`,
`plugins/hexaemeron/tests/fixtures/issue-453/inventory.json`, and
`docs/decisions/drafts/require-inoculation-before-implementation.md`. Change
`plugins/hexaemeron/skills/protasis/SKILL.md`,
`plugins/hexaemeron/skills/protasis/EVOLUTION.md`,
`tests/test_evolution_contract.py`,
`tests/test_promise_machine_contract.py`, and
`tests/promise_machine_coverage.json`. Generate the ignored local verification
payload at `.agents/skills/promise-machine/runtime/` and its `MANIFEST.json`
with the repository script, but do not stage or describe it as a release file.
Regenerate `.horos/boundary.json`, `.horos/candidates.json`, and
`.horos/census.json` when the repository-owned scan changes them; the clean
exact-commit suite at `dfd380b83bd459a862184272ba91fb241fba5568` proves the
count drift, so this step must refresh the records. Warden alone appends
`audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md` and its
sibling `.synopsis.md`.

**Why.** The receipted study amendment
`f73bf693a00fd08c643c34cf9cd81f9d9215bd19f2e644cffe0ca0fefd30d25b`
marks Step 1's exit broken after the exact committed parity check proved that
document-global counting treats two valid sequential full Exit replacements
as duplicate live authority. Selecting the final effective Exit generation
keeps every append-only historical byte while preventing an older, partial,
or conflicting record set from authorising implementation. It also preserves
the root-suite repairs already proved necessary: the behavioural test-module
name, the complete root promise population, and regenerated Horos counts.

**Steps touched.** Step 1's Exit and Files fields.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5:
entry holds; exit holds.

### Amendment -- 2026-09-05

**What changed.** Complete replacement Exit: The
`protasis-known-failure-inventory/v1` object is parsed from one bounded, stable
study. The parser requires every source/view path and SHA-256, every finding
field, one assignment to a real unfenced runbook step, one closed reporter argv
with one exact `{report}` argument, an admitted report format, portable guard
and report paths, and either a non-empty finding set or a digest-bound
no-known-findings claim. Duplicate keys, omitted or extra ids, stale views or
sources, unsafe paths, bad caps, command substitution, and unassigned entries
refuse with no state or ledger write.

Assignment authority is derived from the checked runbook bytes alone.
Ordinary exact or assignment-like records outside every structurally valid
full Exit replacement clause remain active under the document-global
fail-closed rules. Only records inside those clauses are versioned. Their
source-ordered values form generations, and only the final valid clause's
records are added to the ordinary set; an empty or incomplete final clause
never falls back to an earlier one. Amendments replacing only other fields
preserve that generation, while superseded Exit records remain readable
history but are not counted. Step headings come only from the baseline.
Ambiguous or malformed amendment and replacement boundaries, repeated Exit
clauses, and post-amendment Step headings refuse. The existing exact-line,
assignment-only-block, uniqueness, and step-correlation rules apply to the
projected effective set, so every later full Exit replacement must restate
the whole set. The accepted seven-entry inventory is bound by these exact
visible records:

Known-failure assignment: `kf-453-01` -> Step 1
Known-failure assignment: `kf-453-02` -> Step 2
Known-failure assignment: `kf-453-03` -> Step 3
Known-failure assignment: `kf-453-04` -> Step 3
Known-failure assignment: `kf-453-05` -> Step 3
Known-failure assignment: `kf-453-06` -> Step 4
Known-failure assignment: `kf-453-07` -> Step 4

`docs/known-failure-inoculation-study.md` and
`plugins/hexaemeron/docs/known-failure-inoculation/runbook.md` are byte-identical
to the current receipted artefacts. The numberless ADR draft records the chosen
cross-cutting phase and evidence boundary before the study ships. Protasis
receives one provisional candidate generation row whose prior frontier fields
remain unchanged; exact label resolution belongs to the post-stack gate. The
toolchain, CI, licences, and dependencies remain unchanged.

Run `python3 -m unittest discover -s tests` from a clean detached worktree at
the exact Step 1 commit. The live controller worktree carries a root
`.hexaemeron/design-evidence.json` inspected by two corpus tests and is not a
clean root-suite input. Prove the complete exit with:

```bash
cmp .hexaemeron/study.md docs/known-failure-inoculation-study.md
cmp .hexaemeron/runbook.md plugins/hexaemeron/docs/known-failure-inoculation/runbook.md
python3 -m unittest plugins.hexaemeron.tests.test_known_failure_inventory -v
python3 plugins/hexaemeron/skills/protasis/scripts/known_failure_inventory.py docs/known-failure-inoculation-study.md plugins/hexaemeron/docs/known-failure-inoculation/runbook.md --repository . --expected-id kf-453-01 --expected-id kf-453-02 --expected-id kf-453-03 --expected-id kf-453-04 --expected-id kf-453-05 --expected-id kf-453-06 --expected-id kf-453-07
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/known-failure-inoculation-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py plugins/hexaemeron/docs/known-failure-inoculation/runbook.md
python3 scripts/portable_promise_machine.py sync
python3 scripts/portable_promise_machine.py check
python3 scripts/promise_machine.py check
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/run_checks.py --base 5bc2494c4f5802efcd8a92e58554809ac4b9f147
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/plugins/marketplace.json .agents/skills/promise-machine/PORTABLE.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/scripts/verify_runtime.py plugins docs
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/known-failure-inoculation-study.md plugins/hexaemeron/docs/known-failure-inoculation/runbook.md plugins/hexaemeron/skills/protasis/SKILL.md plugins/hexaemeron/skills/protasis/EVOLUTION.md docs/decisions/drafts/require-inoculation-before-implementation.md audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md --max-defects 0
for draft in plugins/hexaemeron/skills/protasis/SKILL.md docs/decisions/drafts/require-inoculation-before-implementation.md audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md; do
  python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py "$draft" --mode report || exit 1
done
git diff --check
```

The study and runbook are completeness-oriented specification artefacts, so
the recorded Brevitas applicability boundary excludes them; their complete
inventory block and glossary remain intact. The evolution ledger is a fixed
single-table version register whose required Hypomnema pragma interrupts its
table, so it is not engineering prose and is excluded from that prose budget.
Imprimatur and Hypomnema still check all five exact shipped documents. The
Hypomnema command names the four tracked `.agents` inputs explicitly so it
checks their authored links without traversing the ignored generated portable
runtime.

Complete replacement Files: Rename
`plugins/hexaemeron/tests/test_issue_453_known_failure_inventory.py` to
`plugins/hexaemeron/tests/test_known_failure_inventory.py` after preserving the
signed guard proof at its historical path. Create
`docs/known-failure-inoculation-study.md`,
`plugins/hexaemeron/docs/known-failure-inoculation/runbook.md`,
`plugins/hexaemeron/skills/protasis/scripts/known_failure_inventory.py`,
`plugins/hexaemeron/tests/emit_issue_453_guard_report.py`,
`plugins/hexaemeron/tests/fixtures/issue-453/inventory.json`, and
`docs/decisions/drafts/require-inoculation-before-implementation.md`. Change
`plugins/hexaemeron/skills/protasis/SKILL.md`,
`plugins/hexaemeron/skills/protasis/EVOLUTION.md`,
`tests/test_evolution_contract.py`,
`tests/test_promise_machine_contract.py`, and
`tests/promise_machine_coverage.json`. Generate the ignored local verification
payload at `.agents/skills/promise-machine/runtime/` and its `MANIFEST.json`
with the repository script, but do not stage or describe it as a release file.
Regenerate `.horos/boundary.json`, `.horos/candidates.json`, and
`.horos/census.json` when the repository-owned scan changes them; the clean
exact-commit suite at `dfd380b83bd459a862184272ba91fb241fba5568` proves the
count drift, so this step must refresh the records. Warden alone appends
`audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md` and its
sibling `.synopsis.md`.

**Why.** The receipted study refinement
`3f4312cfbfa88cd639d5b445928b9d1d4c82945b8b32672a634291f2bc6230f8`
keeps ordinary baseline and stray amendment records active instead of letting
a replacement hide them. Versioning only records inside full Exit clauses
still resolves the exact append-only collision proved by the sequential
receipted runbooks, but preserves every earlier refusal case outside that
narrow repeated-field scope. The behavioural module rename, complete root
promise population, regenerated Horos counts, and all other Step 1 claims
remain unchanged.

**Steps touched.** Step 1's Exit and Files fields.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5:
entry holds; exit holds.

### Amendment -- 2026-09-05

**What changed.** Complete replacement Exit: The
`protasis-known-failure-inventory/v1` object is parsed from one bounded, stable
study. The parser requires every source/view path and SHA-256, every finding
field, one assignment to a real unfenced runbook step, one closed reporter argv
with one exact `{report}` argument, an admitted report format, portable guard
and report paths, and either a non-empty finding set or a digest-bound
no-known-findings claim. Duplicate keys, omitted or extra ids, stale views or
sources, unsafe paths, bad caps, command substitution, and unassigned entries
refuse with no state or ledger write.

Assignment authority is derived from the checked runbook bytes alone.
Ordinary exact or assignment-like records outside every structurally valid
full Exit replacement clause remain active under the document-global
fail-closed rules. Only records inside those clauses are versioned. Their
source-ordered values form generations, and only the final valid clause's
records are added to the ordinary set; an empty or incomplete final clause
never falls back to an earlier one. Amendments replacing only other fields
preserve that generation, while superseded Exit records remain readable
history but are not counted. Step headings come only from the baseline.
Ambiguous or malformed amendment and replacement boundaries, repeated Exit
clauses, and post-amendment Step headings refuse. The existing exact-line,
assignment-only-block, uniqueness, and step-correlation rules apply to the
projected effective set, so every later full Exit replacement must restate
the whole set.

Study inventory discovery alone tolerates unmatched inline-backtick runs in
ordinary prose, including a delimiter whose match appears on a later physical
line; it never masks those bytes. It first processes or refuses every
column-zero fence candidate and retains the raw-HTML, image, indented-fence,
fence-kind, closure, blank-isolation, and exact-one-block checks. An adjacent
apparent inventory fence after an open tick therefore fails isolation, while
a blank-separated fence is counted as a real block. The runbook assignment
surface keeps the strict single-physical-line inline-code rule.

The accepted seven-entry inventory is bound by these exact visible records:

Known-failure assignment: `kf-453-01` -> Step 1
Known-failure assignment: `kf-453-02` -> Step 2
Known-failure assignment: `kf-453-03` -> Step 3
Known-failure assignment: `kf-453-04` -> Step 3
Known-failure assignment: `kf-453-05` -> Step 3
Known-failure assignment: `kf-453-06` -> Step 4
Known-failure assignment: `kf-453-07` -> Step 4

`docs/known-failure-inoculation-study.md` and
`plugins/hexaemeron/docs/known-failure-inoculation/runbook.md` are byte-identical
to the current receipted artefacts. The numberless ADR draft records the chosen
cross-cutting phase and evidence boundary before the study ships. Protasis
receives one provisional candidate generation row whose prior frontier fields
remain unchanged; exact label resolution belongs to the post-stack gate. The
toolchain, CI, licences, and dependencies remain unchanged.

Run `python3 -m unittest discover -s tests` from a clean detached worktree at
the exact Step 1 commit. The live controller worktree carries a root
`.hexaemeron/design-evidence.json` inspected by two corpus tests and is not a
clean root-suite input. Prove the complete exit with:

```bash
cmp .hexaemeron/study.md docs/known-failure-inoculation-study.md
cmp .hexaemeron/runbook.md plugins/hexaemeron/docs/known-failure-inoculation/runbook.md
python3 -m unittest plugins.hexaemeron.tests.test_known_failure_inventory -v
python3 plugins/hexaemeron/skills/protasis/scripts/known_failure_inventory.py docs/known-failure-inoculation-study.md plugins/hexaemeron/docs/known-failure-inoculation/runbook.md --repository . --expected-id kf-453-01 --expected-id kf-453-02 --expected-id kf-453-03 --expected-id kf-453-04 --expected-id kf-453-05 --expected-id kf-453-06 --expected-id kf-453-07
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/known-failure-inoculation-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py plugins/hexaemeron/docs/known-failure-inoculation/runbook.md
python3 scripts/portable_promise_machine.py sync
python3 scripts/portable_promise_machine.py check
python3 scripts/promise_machine.py check
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/run_checks.py --base 5bc2494c4f5802efcd8a92e58554809ac4b9f147
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/plugins/marketplace.json .agents/skills/promise-machine/PORTABLE.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/scripts/verify_runtime.py plugins docs
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/known-failure-inoculation-study.md plugins/hexaemeron/docs/known-failure-inoculation/runbook.md plugins/hexaemeron/skills/protasis/SKILL.md plugins/hexaemeron/skills/protasis/EVOLUTION.md docs/decisions/drafts/require-inoculation-before-implementation.md audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md --max-defects 0
for draft in plugins/hexaemeron/skills/protasis/SKILL.md docs/decisions/drafts/require-inoculation-before-implementation.md audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md; do
  python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py "$draft" --mode report || exit 1
done
git diff --check
```

The study and runbook are completeness-oriented specification artefacts, so
the recorded Brevitas applicability boundary excludes them; their complete
inventory block and glossary remain intact. The evolution ledger is a fixed
single-table version register whose required Hypomnema pragma interrupts its
table, so it is not engineering prose and is excluded from that prose budget.
Imprimatur and Hypomnema still check all five exact shipped documents. The
Hypomnema command names the four tracked `.agents` inputs explicitly so it
checks their authored links without traversing the ignored generated portable
runtime.

**Why.** The receipted study amendment
`4cfd15fdb155fb30151a18f50e17cadab525d9bb52fb2a38ac2c231ff07ec77c`
marks Step 1's exit broken because the strict runbook surface was also applied
to ordinary study prose. The exact study contains one valid CommonMark code
span across two physical lines and no hidden machine syntax. The study-only
tolerance consumes those receipted bytes while fence precedence and inventory
cardinality keep a second or concealed block from authorising the parser. The
effective-Exit projection and every other Step 1 claim remain unchanged.

**Steps touched.** Step 1's Exit field only.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5:
entry holds; exit holds.

### Amendment -- 2026-09-05

**What changed.** Complete replacement Exit: The
`protasis-known-failure-inventory/v1` object is parsed from one bounded, stable
study. The parser requires every source/view path and SHA-256, every finding
field, one assignment to a real unfenced runbook step, one closed reporter argv
with one exact `{report}` argument, an admitted report format, portable guard
and report paths, and either a non-empty finding set or a digest-bound
no-known-findings claim. Duplicate keys, omitted or extra ids, stale views or
sources, unsafe paths, bad caps, command substitution, and unassigned entries
refuse with no state or ledger write.

Assignment authority is derived from the checked runbook bytes alone. Its
machine surface refuses every `[` byte outside a complete one-physical-line
inline code span or a complete fenced block, while the study surface retains
its separate rules. `What changed` is the first nonblank, unfenced record after
each amendment heading. Link, image, reference-label, and multiline-title
syntax therefore cannot donate a hidden heading, field, clause, or assignment.
Step headings come only from the baseline. Ambiguous or malformed amendment
and replacement boundaries, repeated Exit clauses, and post-amendment Step
headings refuse.

Ordinary exact or assignment-like records outside every valid full Exit clause
remain active under the document-global fail-closed rules and stay outside the
generation comparison. Only records inside Exit clauses are versioned. Each
generation first passes the exact-line, assignment-only-block, unique-id, and
real-Step checks and yields a set of finding-id-to-Step pairs. Leading empty
generations are permitted. The first nonempty map locks assignment authority;
every later Exit generation, including an empty one, must carry the same map.
Source order governs, pair order does not, and the lock cannot reset or fall
back. Empty, partial, extra, and reassigned post-lock generations refuse.
Amendments replacing only other fields preserve the current Exit generation.
Superseded matching Exit records remain readable history but are not counted
in the effective set. The final generation's records are joined to the ordinary
set, so every later full Exit replacement must restate the same whole map.

Study inventory discovery alone tolerates unmatched inline-backtick runs in
ordinary prose, including a delimiter whose match appears on a later physical
line; it never masks those bytes. It first processes or refuses every
column-zero fence candidate and retains the raw-HTML, image, indented-fence,
fence-kind, closure, blank-isolation, and exact-one-block checks. An adjacent
apparent inventory fence after an open tick therefore fails isolation, while a
blank-separated fence is counted as a real block. The remaining runbook inline
code policy stays single-physical-line and fail closed.

The accepted seven-entry inventory is bound by these exact visible records:

Known-failure assignment: `kf-453-01` -> Step 1
Known-failure assignment: `kf-453-02` -> Step 2
Known-failure assignment: `kf-453-03` -> Step 3
Known-failure assignment: `kf-453-04` -> Step 3
Known-failure assignment: `kf-453-05` -> Step 3
Known-failure assignment: `kf-453-06` -> Step 4
Known-failure assignment: `kf-453-07` -> Step 4

`docs/known-failure-inoculation-study.md` and
`plugins/hexaemeron/docs/known-failure-inoculation/runbook.md` are byte-identical
to the current receipted artefacts. The numberless ADR draft records the chosen
cross-cutting phase and evidence boundary before the study ships. Protasis
receives one provisional candidate generation row whose prior frontier fields
remain unchanged; exact label resolution belongs to the post-stack gate. The
toolchain, CI, licences, and dependencies remain unchanged.

Run `python3 -m unittest discover -s tests` from a clean detached worktree at
the exact Step 1 commit. The live controller worktree carries a root
`.hexaemeron/design-evidence.json` inspected by two corpus tests and is not a
clean root-suite input. Prove the complete exit with:

```bash
cmp .hexaemeron/study.md docs/known-failure-inoculation-study.md
cmp .hexaemeron/runbook.md plugins/hexaemeron/docs/known-failure-inoculation/runbook.md
python3 -m unittest plugins.hexaemeron.tests.test_known_failure_inventory -v
python3 plugins/hexaemeron/skills/protasis/scripts/known_failure_inventory.py docs/known-failure-inoculation-study.md plugins/hexaemeron/docs/known-failure-inoculation/runbook.md --repository . --expected-id kf-453-01 --expected-id kf-453-02 --expected-id kf-453-03 --expected-id kf-453-04 --expected-id kf-453-05 --expected-id kf-453-06 --expected-id kf-453-07
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/known-failure-inoculation-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py plugins/hexaemeron/docs/known-failure-inoculation/runbook.md
python3 scripts/portable_promise_machine.py sync
python3 scripts/portable_promise_machine.py check
python3 scripts/promise_machine.py check
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/run_checks.py --base 5bc2494c4f5802efcd8a92e58554809ac4b9f147
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/plugins/marketplace.json .agents/skills/promise-machine/PORTABLE.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/scripts/verify_runtime.py plugins docs
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/known-failure-inoculation-study.md plugins/hexaemeron/docs/known-failure-inoculation/runbook.md plugins/hexaemeron/skills/protasis/SKILL.md plugins/hexaemeron/skills/protasis/EVOLUTION.md docs/decisions/drafts/require-inoculation-before-implementation.md audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md --max-defects 0
for draft in plugins/hexaemeron/skills/protasis/SKILL.md docs/decisions/drafts/require-inoculation-before-implementation.md audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md; do
  python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py "$draft" --mode report || exit 1
done
git diff --check
```

The study and runbook are completeness-oriented specification artefacts, so
the recorded Brevitas applicability boundary excludes them; their complete
inventory block and glossary remain intact. The evolution ledger is a fixed
single-table version register whose required Hypomnema pragma interrupts its
table, so it is not engineering prose and is excluded from that prose budget.
Imprimatur and Hypomnema still check all five exact shipped documents. The
Hypomnema command names the four tracked `.agents` inputs explicitly so it
checks their authored links without traversing the ignored generated portable
runtime.

**Why.** The receipted study amendment
`bce7995f4f4e8c4fb81b4276f1469fdb296552fc8b1c1d05eee97fef5fbc3f57`
marks Step 1's exit broken after hostile-input review showed that a multiline
link title could supply three raw field markers and suppress an extra
assignment when a later Exit existed. The runbook has no square-bracket bytes,
so the source-surface rule preserves its current content. Its first two Exit
generations contain no assignments and its next five carry the same seven
pairs, so the map lock preserves every receipted assignment while refusing the
demonstrated suppression case and any empty, partial, extra, or reassigned
successor.

**Steps touched.** Step 1's Exit field only.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5:
entry holds; exit holds.

### Amendment -- 2026-09-05

**What changed.** Complete replacement Files: Rename
`plugins/hexaemeron/tests/test_issue_453_known_failure_inventory.py` to
`plugins/hexaemeron/tests/test_known_failure_inventory.py` after preserving the
signed guard proof at its historical path. Create
`docs/known-failure-inoculation-study.md`,
`plugins/hexaemeron/docs/known-failure-inoculation/runbook.md`,
`plugins/hexaemeron/skills/protasis/scripts/known_failure_inventory.py`,
`plugins/hexaemeron/tests/emit_issue_453_guard_report.py`,
`plugins/hexaemeron/tests/fixtures/issue-453/inventory.json`, and
`docs/decisions/drafts/require-inoculation-before-implementation.md`. Change
`plugins/hexaemeron/skills/protasis/SKILL.md`,
`plugins/hexaemeron/skills/protasis/EVOLUTION.md`,
`tests/test_evolution_contract.py`,
`tests/test_promise_machine_contract.py`, and
`tests/promise_machine_coverage.json`. Generate the ignored local verification
payload at `.agents/skills/promise-machine/runtime/` and its `MANIFEST.json`
with the repository script, but do not stage or describe it as a release file.
Regenerate `.horos/boundary.json`, `.horos/candidates.json`, and
`.horos/census.json` when the repository-owned scan changes them; the clean
exact-commit suite at `dfd380b83bd459a862184272ba91fb241fba5568` proves the
count drift, so this step must refresh the records. Warden alone appends
`audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md` and its
sibling `.synopsis.md`.

**Why.** The preceding Exit amendment correctly added one matching generation
to the append-only runbook, but its explanation described only the prior
prefix. The resulting receipted runbook has eight Exit generations: the first
two are empty and the remaining six carry the same seven finding-id-to-Step
pairs. This non-Exit amendment corrects that count without creating another
Exit generation. The source-surface rule, immutable map, Step 1 file set, and
every other exit claim remain unchanged.

**Steps touched.** Step 1's Files field only.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5:
entry holds; exit holds.

### Amendment -- 2026-09-05

**What changed.** Complete replacement Files: Rename
`plugins/hexaemeron/tests/test_issue_453_known_failure_inventory.py` to
`plugins/hexaemeron/tests/test_known_failure_inventory.py` after preserving the
signed guard proof at its historical path. Create
`docs/known-failure-inoculation-study.md`,
`plugins/hexaemeron/docs/known-failure-inoculation/runbook.md`,
`plugins/hexaemeron/skills/protasis/scripts/known_failure_inventory.py`,
`plugins/hexaemeron/tests/emit_issue_453_guard_report.py`,
`plugins/hexaemeron/tests/fixtures/issue-453/inventory.json`, and
`docs/decisions/drafts/require-inoculation-before-implementation.md`. Change
`plugins/hexaemeron/skills/protasis/SKILL.md`,
`plugins/hexaemeron/skills/protasis/EVOLUTION.md`,
`tests/test_evolution_contract.py`,
`tests/test_promise_machine_contract.py`, and
`tests/promise_machine_coverage.json`. Generate the ignored local verification
payload at `.agents/skills/promise-machine/runtime/` and its `MANIFEST.json`
with the repository script, but do not stage or describe it as a release file.
Regenerate `.horos/boundary.json`, `.horos/candidates.json`, and
`.horos/census.json` when the repository-owned scan changes them; the clean
exact-commit suite at `dfd380b83bd459a862184272ba91fb241fba5568` proves the
count drift, so this step must refresh the records. Warden alone appends
`audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md` and its
sibling `.synopsis.md`.

**Why.** The Exit amendment before the count clarification says the runbook has
no square-bracket bytes. Its own admitted inline-code example contains one such
byte. The supported statement is that the exact runbook has no uncovered
square-bracket bytes: its only one is inside a complete one-line code span, and
the exact checker accepts it under the receipted rule. This clarification does
not add an Exit generation or change the eight-generation distribution,
locked assignment map, source-surface behavior, file set, or any other Step 1
claim.

**Steps touched.** Step 1's Files field only.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5:
entry holds; exit holds.

### Amendment -- 2026-09-05

**What changed.** Complete replacement Exit: The
`protasis-known-failure-inventory/v1` object is parsed from one bounded, stable
study. The parser requires every source/view path and SHA-256, every finding
field, one assignment to a real unfenced runbook step, one closed reporter argv
with one exact `{report}` argument, an admitted report format, portable guard
and report paths, and either a non-empty finding set or a digest-bound
no-known-findings claim. Duplicate keys, omitted or extra ids, stale views or
sources, unsafe paths, bad caps, command substitution, and unassigned entries
refuse with no state or ledger write.

Assignment authority is derived from the checked runbook bytes alone. Its
machine surface refuses every `[` byte outside a complete one-physical-line
inline code span or a complete fenced block, while the study surface retains
its separate rules. `What changed` is the first nonblank, unfenced record after
each amendment heading. Link, image, reference-label, and multiline-title
syntax therefore cannot donate a hidden heading, field, clause, or assignment.
Step headings come only from the baseline. Ambiguous or malformed amendment
and replacement boundaries, repeated Exit clauses, and post-amendment Step
headings refuse.

Ordinary exact or assignment-like records outside every valid full Exit clause
remain active under the document-global fail-closed rules and stay outside the
generation comparison. Only records inside Exit clauses are versioned. Each
generation first passes the exact-line, assignment-only-block, unique-id, and
real-Step checks and yields a set of finding-id-to-Step pairs. Leading empty
generations are permitted. The first nonempty map locks assignment authority;
every later Exit generation, including an empty one, must carry the same map.
Source order governs, pair order does not, and the lock cannot reset or fall
back. Empty, partial, extra, and reassigned post-lock generations refuse.
Amendments replacing only other fields preserve the current Exit generation.
Superseded matching Exit records remain readable history but are not counted
in the effective set. The final generation's records are joined to the ordinary
set, so every later full Exit replacement must restate the same whole map.

Study inventory discovery alone tolerates unmatched inline-backtick runs in
ordinary prose, including a delimiter whose match appears on a later physical
line; it never masks those bytes. It first processes or refuses every
column-zero fence candidate and retains the raw-HTML, image, indented-fence,
fence-kind, closure, blank-isolation, and exact-one-block checks. An adjacent
apparent inventory fence after an open tick therefore fails isolation, while a
blank-separated fence is counted as a real block. The remaining runbook inline
code policy stays single-physical-line and fail closed.

The study carries exactly one `hypomnema-design-bridge/v1` block. Its decision
is `receipted-inoculation` and its record is the stable identity
`adr/require-inoculation-before-implementation`. Hypomnema study mode continues
to accept an existing portable path to a numbered ADR or governed skill
ledger. It additionally accepts exactly `adr/<slug>`, with a lowercase ASCII
kebab-case slug no longer than 96 bytes, and resolves it only against
`docs/decisions/drafts/<slug>.md` and the fixed three-digit
`docs/decisions/ADR-NNN-<slug>.md` namespace.

The stable selector admits exactly one bounded, ordinary, no-follow, stably
read record. A missing identity, a draft and final together, multiple numbered
finals, malformed or oversized slug, non-canonical placement, symlink, special
file, oversized record, unsafe component, or changed read refuses as H008.
The ordinary walk's H009 result remains unchanged. A direct draft path is not
an admitted bridge record. The same stable selector therefore survives
integration's existing draft-to-numbered transformation without an append-only
study rewrite. The allocator and its plan, apply, and replay contracts remain
unchanged.

The accepted seven-entry inventory is bound by these exact visible records:

Known-failure assignment: `kf-453-01` -> Step 1
Known-failure assignment: `kf-453-02` -> Step 2
Known-failure assignment: `kf-453-03` -> Step 3
Known-failure assignment: `kf-453-04` -> Step 3
Known-failure assignment: `kf-453-05` -> Step 3
Known-failure assignment: `kf-453-06` -> Step 4
Known-failure assignment: `kf-453-07` -> Step 4

`docs/known-failure-inoculation-study.md` and
`plugins/hexaemeron/docs/known-failure-inoculation/runbook.md` are byte-identical
to the current receipted artefacts. The numberless ADR draft records the chosen
cross-cutting phase and evidence boundary before integration assigns its
number. Protasis receives one provisional candidate generation row whose prior
frontier fields remain unchanged; exact label resolution belongs to the
post-stack gate.

Hypomnema's skill metadata is `5.8.0`. Its ledger current version and one new
history row are the literal `hypomnema-v5.8.0`, the row's axis is `generation`,
its frontier status is `open`, its frontier revision is
`duplicate-home-discovery`, and its frontier SHA-256 is
`74714f68f73e5a2f4394b7f40d55b77055336c76a1665884e279a8325bb9eed3`.
The held frontier text and Next Fiat job remain byte-identical. This closes
only the stable design-bridge resolution gap and does not claim semantic
duplicate-home discovery.

Brevitas adds the explicit `fiat-audit-record` value to its existing `--mode`
interface. It applies report-mode behaviour while suppressing only B010 and
B011. Every other Brevitas rule remains active. Auto, answer, and ordinary
report modes are unchanged, and no subcommand or B012 rule is added.

A Fiat-audit-record invocation is admissible only after
`audit_synopsis.py --check .` has accepted the exact audit tree. Brevitas does
not parse or establish a Fiat audit schema, finding count, risk inventory,
controller transition, synopsis, or receipt. The synopsis checker and
`hexctl audit-round` retain those authorities. The explicit mode establishes
only that the remaining applicable prose budgets pass without padding the
schema-owned H2 heading or findings table.

Brevitas's skill metadata is `0.4.0`. Its ledger current version and one new
history row are the literal `brevitas-v0.4.0`, the row's axis is `generation`,
its frontier status is `open`, its frontier revision is
`held-engineering-corpus`, and its frontier SHA-256 is
`dcff4f6b1397570468dedb18a1ebaa5f45377272bcd2f71cd69ad6818eeb0b62`.
The held frontier text and Next Fiat job remain byte-identical. Its evidence
names issue 453 and the committed study and runbook, not the separately owned
audit file. The Brevitas plugin package stays `0.2.2`; its manifests,
marketplaces, held corpus, version-propagation test, and check map remain
unchanged.

The existing three-row `version-relations` block stays byte-identical and gains
neither Hypomnema nor Brevitas. No concrete token for a relation-declared
target appears. The two intentional literal targets use the omission Protasis
permits for a partial relation list. Fiat's post-stack version-resolution
receipt continues to establish only the three declared relations. A base
movement that consumes or changes either literal next generation requires
separate integration revalidation and correction of its ledger row and
matching metadata before composition. The toolchain, CI, licences, and
dependencies remain unchanged.

Run `python3 -m unittest discover -s tests` from a clean detached worktree at
the exact signed Step 1 product fix. The live controller worktree carries the
root `.hexaemeron/design-evidence.json` inspected by two corpus tests and is not
a clean root-suite input. The two `cmp` commands and the explicit Hypomnema
study-mode command run in the managed controller worktree because they consume
the receipted artefacts and untracked design evidence. The audit synopsis,
Imprimatur audit input, and Fiat-audit-record Brevitas command run on the audit
branch after Warden has appended and regenerated the round-2 record and
synopsis. Prove the complete exit with:

```bash
cmp .hexaemeron/study.md docs/known-failure-inoculation-study.md
cmp .hexaemeron/runbook.md plugins/hexaemeron/docs/known-failure-inoculation/runbook.md
python3 -m unittest plugins.hexaemeron.tests.test_known_failure_inventory -v
python3 -m unittest plugins.hexaemeron.tests.test_hypomnema_checker.DesignBridge -v
python3 -m unittest plugins.hexaemeron.tests.test_hypomnema_decision_assignments -v
python3 -m unittest discover -s plugins/brevitas/tests -t plugins/brevitas
python3 plugins/brevitas/skills/brevitas/scripts/run_evals.py
python3 plugins/brevitas/tests/run_tests.py .elenchus/fiat-453-step-1-brevitas-green.json
python3 -m unittest tests.test_evolution_contract tests.test_promise_machine_contract -v
python3 plugins/hexaemeron/skills/protasis/scripts/known_failure_inventory.py docs/known-failure-inoculation-study.md plugins/hexaemeron/docs/known-failure-inoculation/runbook.md --repository . --expected-id kf-453-01 --expected-id kf-453-02 --expected-id kf-453-03 --expected-id kf-453-04 --expected-id kf-453-05 --expected-id kf-453-06 --expected-id kf-453-07
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/known-failure-inoculation-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py plugins/hexaemeron/docs/known-failure-inoculation/runbook.md
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py --study .hexaemeron/study.md --design-evidence .hexaemeron/design-evidence.json --repo-root .
python3 scripts/portable_promise_machine.py sync
python3 plugins/horos/skills/horos/scripts/horos.py scan . --write
python3 scripts/portable_promise_machine.py sync
python3 scripts/portable_promise_machine.py check
python3 plugins/horos/skills/horos/scripts/horos.py check .
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/run_checks.py --base 5bc2494c4f5802efcd8a92e58554809ac4b9f147
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/plugins/marketplace.json .agents/skills/promise-machine/PORTABLE.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/scripts/verify_runtime.py plugins docs
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/known-failure-inoculation-study.md plugins/hexaemeron/docs/known-failure-inoculation/runbook.md plugins/hexaemeron/skills/protasis/SKILL.md plugins/hexaemeron/skills/protasis/EVOLUTION.md plugins/hexaemeron/skills/hypomnema/SKILL.md plugins/hexaemeron/skills/hypomnema/EVOLUTION.md plugins/brevitas/skills/brevitas/SKILL.md plugins/brevitas/skills/brevitas/EVOLUTION.md plugins/brevitas/README.md plugins/brevitas/AGENTS.md docs/decisions/drafts/require-inoculation-before-implementation.md audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md --max-defects 0
for draft in plugins/hexaemeron/skills/protasis/SKILL.md plugins/hexaemeron/skills/hypomnema/SKILL.md plugins/brevitas/skills/brevitas/SKILL.md plugins/brevitas/README.md plugins/brevitas/AGENTS.md docs/decisions/drafts/require-inoculation-before-implementation.md; do
  python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py "$draft" --mode report || exit 1
done
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md --mode fiat-audit-record
git diff --check
```

The study and runbook are completeness-oriented specification artefacts, so
the recorded Brevitas applicability boundary excludes them; their complete
inventory block, design bridge, and glossary remain intact. The three changed
evolution ledgers are governed version registers and remain outside the
engineering-prose budget. Imprimatur and Hypomnema still inspect every exact
shipped document named by the commands. The ordinary Hypomnema command names
the four tracked `.agents` inputs explicitly so it checks their authored links
without traversing the ignored generated portable runtime. The audit source is
not removed from Brevitas; it uses the explicit mode only after the authoritative
synopsis check succeeds.

Complete replacement Files: Rename
`plugins/hexaemeron/tests/test_issue_453_known_failure_inventory.py` to
`plugins/hexaemeron/tests/test_known_failure_inventory.py` after preserving the
signed guard proof at its historical path. Create
`docs/known-failure-inoculation-study.md`,
`plugins/hexaemeron/docs/known-failure-inoculation/runbook.md`,
`plugins/hexaemeron/skills/protasis/scripts/known_failure_inventory.py`,
`plugins/hexaemeron/tests/emit_issue_453_guard_report.py`,
`plugins/hexaemeron/tests/fixtures/issue-453/inventory.json`, and
`docs/decisions/drafts/require-inoculation-before-implementation.md`. Change
`plugins/hexaemeron/skills/protasis/SKILL.md`,
`plugins/hexaemeron/skills/protasis/EVOLUTION.md`,
`plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py`,
`plugins/hexaemeron/tests/test_hypomnema_checker.py`,
`plugins/hexaemeron/skills/hypomnema/SKILL.md`,
`plugins/hexaemeron/skills/hypomnema/EVOLUTION.md`,
`plugins/brevitas/skills/brevitas/scripts/brevitas.py`,
`plugins/brevitas/tests/test_brevitas.py`,
`plugins/brevitas/skills/brevitas/SKILL.md`,
`plugins/brevitas/skills/brevitas/EVOLUTION.md`,
`plugins/brevitas/README.md`,
`plugins/brevitas/AGENTS.md`,
`tests/test_evolution_contract.py`,
`tests/test_promise_machine_contract.py`, and
`tests/promise_machine_coverage.json`.

Do not change
`plugins/hexaemeron/skills/hypomnema/scripts/decision_assignments.py`,
`plugins/hexaemeron/tests/test_hypomnema_decision_assignments.py`,
`plugins/brevitas/skills/brevitas/scripts/held_corpus.py`,
`tests/test_version_propagation.py`,
`tests/check-map-v1.json`, any plugin manifest, or any marketplace record.
Generate the ignored local verification payload at
`.agents/skills/promise-machine/runtime/` and its `MANIFEST.json` with the
repository script, but do not stage or describe it as a release file.
Regenerate `.horos/boundary.json`, `.horos/candidates.json`, and
`.horos/census.json` only when the repository-owned scan changes them.

The signed product, specification, and test fix is one commit on the Step 1
branch whose sole parent is
`3253af2a873028d87111237bd3638905626956d4`. It contains no audit source or
synopsis. Warden alone owns
`audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md` and
`audit/rounds/fiat-453-inject-known-failure-guards-before-productio.synopsis.md`
on the audit branch. The audit branch first receives the signed product fix by
a signed no-fast-forward merge whose first parent is
`0d58501d` and whose second parent is the product fix. Warden then appends the
round-2 source and regenerated synopsis in a later signed audit-branch commit.

Complete replacement Tests: Before changing the parser, make a signed
guard-only commit whose sole parent is the packet's `branch_from` and whose
changed paths are exactly the three `kf-453-01` guard paths in the study.
Replace `<signed-guard-commit>` with that object and run:

```bash
python3 plugins/hexaemeron/skills/elenchus/scripts/elenchus.py --ref <signed-guard-commit> --test-command "python3 plugins/hexaemeron/tests/emit_issue_453_guard_report.py --case kf-453-01 --report {report}" --report-format unittest-json-v1 --report-file .elenchus/issue-453-kf-453-01.json --require-guard --format json
```

Stop unless it reports `guarded`; retain the command, commit, exit, and bounded
JSON outside Git. On the fixed tree run
`python3 plugins/hexaemeron/tests/emit_issue_453_guard_report.py --case kf-453-01 --report .elenchus/issue-453-kf-453-01-green.json`
and require a positive, complete, non-skipped, error-free, assertion-free
report. The focused inventory module covers accepted input and every omission,
duplication, shape, source-drift, assignment, path, command, report-format, and
cap refusal; its final case count is recorded rather than guessed here.

The H008 repair adds regression methods to
`plugins/hexaemeron/tests/test_hypomnema_checker.py`. They use only the
pre-existing public and test-helper surface, so overlaying that changed test
file on parent `3253af2a873028d87111237bd3638905626956d4` produces assertion
failures rather than import or infrastructure errors. The cases prove a unique
draft selector, the same selector after assignment to a unique numbered final,
a dangling selector, malformed and oversized slugs, a direct draft path,
draft-plus-final duplication, multiple numbered finals, non-canonical
near-matches, and symlinked, special, oversized, and unstable matched records.
The existing concrete numbered ADR, governed ledger, selection-envelope,
bounded-input, allocator, and ordinary-walk cases remain unchanged.

The Brevitas repair adds focused cases to
`plugins/brevitas/tests/test_brevitas.py` through the pre-existing `lint_text`
entrypoint. The parent overlay fails by assertion, not import or runner error.
The cases show that explicit `fiat-audit-record` suppresses only B010 and B011
for zero-, one-, and two-finding audit shapes, while B024, B027, B030, and every
other applicable rule remain active. Auto, answer, and report modes do not
select the exemption; the existing small-table and two-section cases remain
red. A parser-level case proves the CLI accepts the explicit value while
turning any parent `SystemExit` into an assertion failure. No test asks
Brevitas to validate the Fiat schema. Add
`test_brevitas_fiat_audit_record_mode_keeps_held_frontier` to
`tests/test_evolution_contract.py`, and update the existing
`brevitas-structure-check` coverage selectors without adding another promise.

Let `<signed-product-fix>` be the single signed Step 1 product,
specification, and test commit whose sole parent is
`3253af2a873028d87111237bd3638905626956d4`. It contains both regression test
files and no audit file. Run both source-bound guards:

```bash
python3 plugins/hexaemeron/skills/elenchus/scripts/elenchus.py --ref <signed-product-fix> --test-command "python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}" --report-format unittest-json-v1 --report-file .elenchus/fiat-453-step-1-h008.json --require-guard --format json
python3 plugins/hexaemeron/skills/elenchus/scripts/elenchus.py --ref <signed-product-fix> --test-command "python3 plugins/brevitas/tests/run_tests.py {report}" --report-format unittest-json-v1 --report-file .elenchus/fiat-453-step-1-brevitas.json --require-guard --format json
```

Stop unless both results are exactly `guarded`. Elenchus overlays changed test
bytes on the exact parent and does not need the audit source in the product
commit. Retain both commands, the signed commit, exits, and bounded reports
outside Git. On the fixed product tree, the focused Hypomnema class, unchanged
allocator module, complete Brevitas suite and evaluations, explicit
current-study command, evolution contract, Promise Machine coverage check, and
both repository suites must pass.

Merge `<signed-product-fix>` into the audit branch with a signed
no-fast-forward merge whose parents are, in order, `0d58501d` and
`<signed-product-fix>`. Warden then appends the round-2 audit record and
regenerates its synopsis in a separate signed audit-branch commit. Run
`audit_synopsis.py --check .` before the exact `--mode fiat-audit-record`
Brevitas invocation. The controller audit-round receipt names
`<signed-product-fix>` as `--fixes-commit`; it does not substitute the merge
commit or the later audit-record commit.

H008 and the Brevitas defect are not added to the seven-entry inventory and do
not alter the existing `kf-453-01` proof. Warden's exact audit runner remains
command `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`,
format `unittest-json-v1`, and file
`.elenchus/fiat-453-step-1-audit.json`. Rerun every complete Exit command after
each audit fix.

Complete replacement Disciplines: phylax: the study, JSON object, source views,
paths, commands, and files cross parser and filesystem boundaries, so type,
size, containment, stability, and duplicate checks apply before use. The
stable bridge examines only its canonical bounded draft and three-digit final
slots, follows no path symlink, admits one ordinary stable record, and refuses
zero or multiple matches before treating the design as recorded. The
Fiat-audit-record mode consumes no schema authority: the exact audit tree must
first pass the existing bounded synopsis checker. ephoros: stable refusal
codes, ids, counts, paths, and digests answer which inventory item failed
without printing source content; H008 additionally distinguishes malformed
identity, absent identity, duplicate identity, unsafe placement, and failed
stable read without promoting record contents. metron: none, this step makes no
performance claim; inventory caps and the fixed stable-identity candidate set
are correctness controls. elenchus: `kf-453-01` must fail by assertion on its
exact parent and finish green after the inventory parser lands; the H008 and
Brevitas regressions must each fail by assertion on the exact Step 1 product
parent and pass on the same signed product fix. hypomnema: the inventory
authority, assignment rule, and empty-set rule live in the Protasis contract,
its provisional candidate row, and the committed study and runbook; the
selected cross-cutting decision has the single durable identity
`adr/require-inoculation-before-implementation`, integration owns its number,
and the literal `hypomnema-v5.8.0` generation records only stable bridge
resolution while preserving the held frontier. brevitas: explicit
`fiat-audit-record` mode suppresses only B010 and B011 after the authoritative
synopsis check; all other budgets and evidence precedence remain active,
ordinary modes receive no exemption, Brevitas makes no Fiat-schema claim, and
the literal `brevitas-v0.4.0` generation preserves the held corpus frontier.

**Why.** The current study has no design bridge, which is a study defect, while
the current H008 implementation cannot consume the stable ADR identity its own
version 5.7 authoring and integration contract requires, which is a product
defect. The paired amendments and guarded product repair close both without
rewriting an earlier receipt, assigning an ADR number early, accepting a path
that will dangle, or duplicating the decision in a governed ledger.

The exact Fiat audit record is valid host-owned prose but fails Brevitas B010
and B011 solely because its schema permits one H2 record and one findings row.
Padding it would falsify the record, while deleting it from the lint would
weaken the repository gate. The explicit mode and mandatory prior synopsis
check preserve both authorities: Fiat validates the record, and Brevitas
applies every compatible prose budget without reimplementing Fiat's parser.

The existing runbook prefix has eight replacement-Exit generations: its first
two are empty and its remaining six carry the same seven pairs. This full Exit
replacement creates the ninth generation, with the first two still empty and
the remaining seven carrying the identical locked map. It changes no finding,
assignment, source digest, reporter, step topology, relation-declared target,
toolchain, CI file, licence, dependency, package manifest, marketplace,
allocator, or held corpus.

The product repair and audit evidence remain separate signed objects. The
Step 1 fix is based directly on
`3253af2a873028d87111237bd3638905626956d4` and contains no audit bytes. The
audit branch preserves `0d58501d` as the first parent of its signed merge,
Warden alone appends round 2 afterwards, and the controller receipts the
product fix rather than either audit-branch commit.

**Steps touched.** Step 1's Exit, Files, Tests, and Disciplines.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5:
entry holds; exit holds.

### Amendment -- 2026-09-06

**What changed.** Complete replacement Entry: Start from the directive's exact
`branch_from`, which is the signed, audited, prose-checked and pushed Step 1
head. Its stacked pull request remains open; no Step has merged because stack
merging belongs to integration. The closed seven-entry inventory, public
checker and byte-identical committed study and runbook are present. The
checked-in controller still lacks the inoculation transition, and this run's
installed controller still follows its recorded bootstrap boundary.

Complete replacement Exit: The public Protasis
`load_checked_inventory` operation is the only controller ingestion path. It
returns absent only when neither an inventory nor an assignment surface exists,
returns the stable K000 through K012 findings on every attempted malformed or
partial surface, or returns one closed
`protasis-known-failure-inventory-capture/v1` object after bounded stable reads
and final revalidation. Its fields are `schema`, `study_sha256`,
`runbook_sha256`, `inventory_sha256`, `source_views`, `findings`,
`no_known_findings`, and `assignments`; its inventory digest uses Fiat's
canonical JSON bytes. The command-line checker projects the same result.

The current runbook machine surface and immutable assignment-generation rules
remain unchanged. Ordinary records stay active, replacement Exit generations
stay source ordered, the first nonempty map remains locked, and the final
generation repeats the complete seven-pair map:

Known-failure assignment: `kf-453-01` -> Step 1
Known-failure assignment: `kf-453-02` -> Step 2
Known-failure assignment: `kf-453-03` -> Step 3
Known-failure assignment: `kf-453-04` -> Step 3
Known-failure assignment: `kf-453-05` -> Step 3
Known-failure assignment: `kf-453-06` -> Step 4
Known-failure assignment: `kf-453-07` -> Step 4

A clean capture is stored under the runbook receipt and activates `inoculate`.
`done runbook` opens the first Step there, and `done push` opens every later
Step there. `next` delegates to Mason with the exact source digests, capture,
assigned entries, allowed paths, reporter contracts, branch and branch parent,
and fixed evidence directory. `status --json` exposes phase, inventory digest,
assigned count, completed ids and remaining ids without printing report
content. A receipt predating the capture retains its existing phase path and
receives no fabricated inventory.

The only phase receipt command is `hexctl done inoculate`, with no
phase-specific option. Its exact `fiat-known-failure-inoculation/v1` fields are
`schema`, `step`, `study_sha256`, `runbook_sha256`, `inventory_sha256`,
`step_parent`, `assigned_ids`, `source_views`, `no_known_findings`, and
`guard_manifests`. Assigned ids and manifest references are uniquely sorted.
Each manifest reference has exactly `finding_id`, `path`, and `sha256`.
Foreign `done` options, stale source, a changed parent, duplicate state, or an
unsupported field refuses before state, design-transition, ledger, or
checkpoint mutation.

For zero assigned ids, the command reads the fixed
`.hexaemeron/steps/<n>/inoculation/no-known-findings.json` file. Its
`fiat-no-known-findings/v1` object has exactly `schema`, `study_sha256`,
`inventory_sha256`, `source_views`, `consuming_step`, and `assertion`; the
assertion is `no-known-findings-for-step`. Exact agreement receipts the checked
record with an empty `guard_manifests` list and opens `implement`. This route is
available only from a clean capture assigning zero ids. An attempted malformed
or partial inventory or assignment surface is never absent and never becomes a
no-known-findings receipt.

For one or more assigned ids, Step 2 records the complete declaration in the
capture, packet and status but does not treat the declaration as evidence.
`hexctl done inoculate` refuses while `guard_manifests` is empty, and
`done implement` refuses while no valid inoculation receipt exists. Step 3
alone retains and validates reports and supplies the nonempty complete
manifest-reference list. No Step 2 result claims that a guard ran, a report was
retained, or product editing is authorised for an assigned finding.

The historical `kf-453-02` guard uses
`plugins/hexaemeron/tests/test_issue_453_inoculation_lifecycle.py` and the
reporter named by the immutable inventory. The fixed tree renames the module to
`plugins/hexaemeron/tests/test_inoculation_lifecycle.py` and updates the
reporter to select it, while the signed guard object, command and retained
report keep the historical path. The Fiat phase instruction model is
re-authored from every affected source span; its compact form, questions,
mutations, manifest, measurement, parity and coverage bindings are regenerated.
A digest-only reconciliation refuses this semantic edit. The committed study
and runbook equal the current receipted bytes. The existing numberless ADR
draft remains unchanged. The toolchain, CI, licences and dependencies remain
unchanged.

Prove the complete exit with:

```bash
cmp .hexaemeron/study.md docs/known-failure-inoculation-study.md
cmp .hexaemeron/runbook.md plugins/hexaemeron/docs/known-failure-inoculation/runbook.md
python3 -m unittest plugins.hexaemeron.tests.test_known_failure_inventory plugins.hexaemeron.tests.test_inoculation_lifecycle -v
python3 plugins/hexaemeron/tests/emit_issue_453_guard_report.py --case kf-453-02 --report .elenchus/issue-453-kf-453-02-green.json
python3 plugins/hexaemeron/skills/protasis/scripts/known_failure_inventory.py docs/known-failure-inoculation-study.md plugins/hexaemeron/docs/known-failure-inoculation/runbook.md --repository . --expected-id kf-453-01 --expected-id kf-453-02 --expected-id kf-453-03 --expected-id kf-453-04 --expected-id kf-453-05 --expected-id kf-453-06 --expected-id kf-453-07
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/known-failure-inoculation-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py plugins/hexaemeron/docs/known-failure-inoculation/runbook.md
python3 scripts/agent_instruction.py format --root . --input tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/model.json --output tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/compact.wai
python3 scripts/agent_instruction.py measure --root . --manifest tests/fixtures/agent-instruction-v1/manifest.json --output tests/fixtures/agent-instruction-v1/evidence/measurement.json
python3 scripts/agent_instruction.py parity --root . --manifest tests/fixtures/agent-instruction-v1/manifest.json --output tests/fixtures/agent-instruction-v1/evidence/parity.json
python3 scripts/agent_instruction.py check --root . --manifest tests/fixtures/agent-instruction-v1/manifest.json
python3 -m unittest tests.test_agent_instruction tests.test_agent_instruction_corpus tests.test_repository_naming -v
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py --study .hexaemeron/study.md --design-evidence .hexaemeron/design-evidence.json --repo-root .
python3 scripts/portable_promise_machine.py sync
python3 plugins/horos/skills/horos/scripts/horos.py scan . --write
python3 scripts/portable_promise_machine.py sync
python3 scripts/portable_promise_machine.py check
python3 plugins/horos/skills/horos/scripts/horos.py check .
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/run_checks.py --base 5bc2494c4f5802efcd8a92e58554809ac4b9f147
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/plugins/marketplace.json .agents/skills/promise-machine/PORTABLE.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/scripts/verify_runtime.py plugins docs
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/known-failure-inoculation-study.md plugins/hexaemeron/docs/known-failure-inoculation/runbook.md plugins/hexaemeron/skills/protasis/SKILL.md plugins/hexaemeron/skills/fiat/SKILL.md plugins/hexaemeron/agents/mason.md docs/agent-instruction-language-v1.md docs/decisions/drafts/require-inoculation-before-implementation.md audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md --max-defects 0
for draft in plugins/hexaemeron/skills/protasis/SKILL.md plugins/hexaemeron/skills/fiat/SKILL.md plugins/hexaemeron/agents/mason.md docs/agent-instruction-language-v1.md docs/decisions/drafts/require-inoculation-before-implementation.md; do
  python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py "$draft" --mode report || exit 1
done
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md --mode fiat-audit-record
git diff --check
```

Run the root suites from a clean detached worktree at the exact signed Step 2
candidate. The managed controller worktree contains ignored controller evidence
and is not a clean root-suite input. The two `cmp` commands and the explicit
Hypomnema study-mode command run in the managed controller worktree because
they consume the receipted artefacts and untracked design evidence. The study
and runbook are completeness-oriented specifications, so Brevitas does not
budget them; Imprimatur and Hypomnema still inspect them. The audit synopsis,
Imprimatur audit input, and Fiat-audit-record Brevitas command run on the audit
branch after Warden owns the audit update.

Complete replacement Files: In the guard-only commit, create
`plugins/hexaemeron/tests/test_issue_453_inoculation_lifecycle.py` and change
`plugins/hexaemeron/tests/emit_issue_453_guard_report.py`. In the fixed tree,
rename the lifecycle module to
`plugins/hexaemeron/tests/test_inoculation_lifecycle.py` and update the reporter
again. Change
`plugins/hexaemeron/skills/protasis/scripts/known_failure_inventory.py`,
`plugins/hexaemeron/tests/test_known_failure_inventory.py`,
`plugins/hexaemeron/skills/protasis/SKILL.md`,
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/skills/fiat/SKILL.md`,
`plugins/hexaemeron/agents/mason.md`,
`plugins/hexaemeron/tests/test_hexctl.py`,
`plugins/hexaemeron/tests/test_fiat_skill.py`,
`scripts/agent_instruction.py`,
`tests/test_agent_instruction.py`,
`tests/test_agent_instruction_corpus.py`,
`docs/agent-instruction-language-v1.md`,
`tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/model.json`,
`tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/compact.wai`,
`tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/questions.json`,
`tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/mutations.json`,
`tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/source-spans.json`,
`tests/fixtures/agent-instruction-v1/manifest.json`,
`tests/fixtures/agent-instruction-v1/evidence/measurement.json`,
`tests/fixtures/agent-instruction-v1/evidence/parity.json`,
`tests/promise_machine_coverage.json`,
`docs/known-failure-inoculation-study.md`, and
`plugins/hexaemeron/docs/known-failure-inoculation/runbook.md`. Create
`plugins/hexaemeron/tests/fixtures/issue-453/no-known-findings.json`. Read but do
not change `docs/decisions/drafts/require-inoculation-before-implementation.md`.
Refresh the ignored local portable verification payload without staging it.
Regenerate `.horos/boundary.json`, `.horos/candidates.json`, and
`.horos/census.json` only when the repository-owned scan changes them. Warden
alone changes the configured audit record and synopsis.

Complete replacement Tests: Before changing the loader or controller, make a
signed guard-only commit on the directive's exact Step 2 branch. Its sole parent
is the exact `branch_from` head
`1019fd36326b7e1c51765f3f0d5a0ef57805304a`, and its changed paths are exactly
`plugins/hexaemeron/tests/test_issue_453_inoculation_lifecycle.py` and
`plugins/hexaemeron/tests/emit_issue_453_guard_report.py`. Replace
`<signed-guard-commit>` with that object and run:

```bash
python3 plugins/hexaemeron/skills/elenchus/scripts/elenchus.py --ref <signed-guard-commit> --test-command "python3 plugins/hexaemeron/tests/emit_issue_453_guard_report.py --case kf-453-02 --report {report}" --report-format unittest-json-v1 --report-file .elenchus/issue-453-kf-453-02.json --require-guard --format json
```

Stop unless it reports exactly `guarded`; retain the command, commit, exit and
bounded JSON outside Git. On the fixed tree run
`python3 plugins/hexaemeron/tests/emit_issue_453_guard_report.py --case kf-453-02 --report .elenchus/issue-453-kf-453-02-green.json` and require a positive,
complete, non-skipped, error-free and assertion-free report.

The inventory tests cover explicit absence only when both the inventory and
assignment surfaces are absent, every attempted malformed or partial surface
as a K000 through K012 finding rather than absence, one stable clean capture,
canonical digesting, assignment order and source drift. Lifecycle cases cover
phase order, exact packet reconstruction, closed receipt shapes, zero-assigned
no-known evidence, nonempty-assigned empty-manifest refusal, foreign options,
legacy states, changed parents and unchanged state, design-transition, ledger
and checkpoint bytes on every refusal. Test the checked-in controller's full
new-run path in disposable repositories only; this live run remains on the
installed controller's bootstrap `implement` path. The instruction corpus must
bind every changed span, add the inoculation node before implementation, and
reject stale compact, question, mutation, measurement, parity, manifest and
coverage derivatives. Warden uses command
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`,
format `unittest-json-v1`, and file
`.elenchus/fiat-453-step-2-audit.json`, then reruns every Exit command after a
fix.

Complete replacement Disciplines: phylax: the study, inventory object, source
views, worker packets, controller arguments, paths, commands and evidence files
cross parser, process and filesystem boundaries, so closed keys, caps,
containment, stable no-follow reads, exact Git objects and mutation ordering are
checked before use. An attempted inventory surface fails closed and can never
be reclassified as absence. ephoros: `status --json`, `next`, receipt stdout and
stable named refusals expose phase, inventory digest, assigned count, completed
ids, remaining ids and no-known provenance without source or report content.
metron: none, the extra interactive transition is the selected correctness
design, not a latency claim. elenchus: `kf-453-02` must fail by assertion on the
exact Step 2 parent through the signed two-path guard commit and finish green
after the fixed tree lands. hypomnema: the existing ADR draft owns the phase,
atomic receipt, red-intermediate and bootstrap decisions; Fiat cites its stable
identity without changing it or inventing an integration number.

**Why.** The current checker returns only a finding list and discards the
accepted object. Rereading or reparsing after a clean result would lose the
stable-read boundary and could diverge from the locked replacement-Exit
projection. The original Step 2 Exit also calls an assigned id set evidence
even though Step 3 owns report retention, Git binding and verdict admission.
That would recreate the pre-edit bypass this design closes. Explicit absence
therefore means that neither machine surface was attempted; malformed or
partial attempted content stays visible as a checker finding and can never
open the no-known path. The original Entry incorrectly calls the open Step 1
stack merged, its Files omit the loader and reporter and retain an
issue-numbered maintained test, and its broad Hypomnema command traverses
ignored generated state.

**Steps touched.** Step 2's Entry, Exit, Files, Tests, and Disciplines.

**Still holding.** Step 2: entry holds; exit holds. Step 3: entry holds; exit
holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-09-06

**What changed.** Complete replacement Files: In the guard-only commit, create
`plugins/hexaemeron/tests/test_issue_453_inoculation_lifecycle.py` and change
`plugins/hexaemeron/tests/emit_issue_453_guard_report.py`. In the fixed tree,
rename the lifecycle module to
`plugins/hexaemeron/tests/test_inoculation_lifecycle.py` and update the reporter
again. Change
`plugins/hexaemeron/skills/protasis/scripts/known_failure_inventory.py`,
`plugins/hexaemeron/tests/test_known_failure_inventory.py`,
`plugins/hexaemeron/skills/protasis/SKILL.md`,
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/skills/fiat/SKILL.md`,
`plugins/hexaemeron/agents/mason.md`,
`plugins/hexaemeron/tests/test_hexctl.py`,
`plugins/hexaemeron/tests/test_fiat_skill.py`,
`scripts/agent_instruction.py`,
`tests/test_agent_instruction.py`,
`tests/test_agent_instruction_corpus.py`,
`docs/agent-instruction-language-v1.md`,
`tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/model.json`,
`tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/compact.wai`,
`tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/questions.json`,
`tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/mutations.json`,
`tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/source-spans.json`,
`tests/fixtures/agent-instruction-v1/manifest.schema.json`,
`tests/fixtures/agent-instruction-v1/manifest.json`,
`tests/fixtures/agent-instruction-v1/evidence/measurement.json`,
`tests/fixtures/agent-instruction-v1/evidence/parity.json`,
`tests/promise_machine_coverage.json`,
`docs/known-failure-inoculation-study.md`, and
`plugins/hexaemeron/docs/known-failure-inoculation/runbook.md`. Create
`plugins/hexaemeron/tests/fixtures/issue-453/no-known-findings.json`. Read but do
not change `docs/decisions/drafts/require-inoculation-before-implementation.md`.
Refresh the ignored local portable verification payload without staging it.
Regenerate `.horos/boundary.json`, `.horos/candidates.json`, and
`.horos/census.json` only when the repository-owned scan changes them. Warden
alone changes the configured audit record and synopsis.

**Why.** The Fiat instruction fixture is validated twice: the manifest carries
its counts, and `manifest.schema.json` freezes those same counts as constants.
Adding the required inoculation directive raises the fixture binding count,
and its new closed question and hostile mutation raise their corresponding
counts. Leaving the schema outside the allowed files makes the semantic
re-authoring impossible to validate. This replacement adds only that already
governed derivative; it changes no phase design, inventory assignment, source
authority, test command, toolchain, dependency, licence, or audit ownership.

**Steps touched.** Step 2's Files field only.

**Still holding.** Step 2: entry holds; exit holds. Step 3: entry holds; exit
holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-09-06

**What changed.** Complete replacement Exit: The public Protasis
`load_checked_inventory` operation is the sole ingestion boundary. It returns
an explicit absent result only when neither the inventory nor assignment
surface exists, the existing K000 through K012 refusal set for every attempted
malformed or partial surface, or one closed
`protasis-known-failure-inventory-capture/v1` object after the same bounded
reads and final stability checks as the command-line checker. A clean capture
has exactly `schema`, `study_sha256`, `runbook_sha256`, `inventory_sha256`,
`source_views`, `findings`, `no_known_findings`, and `assignments`. The
inventory digest is SHA-256 over the parsed inventory in Fiat's canonical JSON
form. Assignments are ordered by Step and finding id. The checker and Fiat
consume this one operation; neither reparses a clean result or reimplements
assignment discovery. An attempted, malformed, partial, changed or stale
surface never becomes absent.

The operation retains the runbook machine surface and immutable generation map
unchanged. Ordinary records remain active, replacement Exit generations remain
source ordered, the first nonempty map stays locked, and the final generation
repeats this same complete seven-pair map exactly:

Known-failure assignment: `kf-453-01` -> Step 1
Known-failure assignment: `kf-453-02` -> Step 2
Known-failure assignment: `kf-453-03` -> Step 3
Known-failure assignment: `kf-453-04` -> Step 3
Known-failure assignment: `kf-453-05` -> Step 3
Known-failure assignment: `kf-453-06` -> Step 4
Known-failure assignment: `kf-453-07` -> Step 4

The strict bracket, amendment-field, replacement-clause, baseline-Step, fence,
and single-line inline-code rules remain in force.

For a runbook that yields a clean capture, `done runbook` stores that exact
capture in its receipt and opens the first Step at `inoculate`; `done push`
opens every later Step at the same phase. `next` gives Mason the current study
and runbook digests, capture digest, consuming Step, exact assigned entries,
allowed guard paths, reporter commands, report formats and logical report
files, exact branch and branch parent, and the fixed controller evidence
directory. `status --json` exposes the phase, inventory digest, assigned count,
completed ids, remaining ids and no-known provenance without source or report
content. A pre-contract state whose runbook receipt has no capture retains its
recorded implementation-first route without an invented inventory or receipt.

The sole new receipt command is `hexctl done inoculate`; it takes no
phase-specific argument. Phase-foreign `done` options refuse before mutation.
Its closed receipt schema is `fiat-known-failure-inoculation/v1`, with exactly
`schema`, `step`, `study_sha256`, `runbook_sha256`, `inventory_sha256`,
`step_parent`, `assigned_ids`, `source_views`, `no_known_findings`, and
`guard_manifests`. Assigned ids and manifest references are uniquely sorted.
Each future manifest reference has exactly `finding_id`, `path`, and `sha256`.

For a Step with no assigned finding, Mason writes the fixed
`.hexaemeron/steps/<n>/inoculation/no-known-findings.json` record under schema
`fiat-no-known-findings/v1`. It has exactly `schema`, `study_sha256`,
`inventory_sha256`, `source_views`, `consuming_step`, and `assertion`, with
assertion `no-known-findings-for-step`. Fiat accepts that route only when the
checked capture assigns zero ids, the study and source-view digests agree, and
the file is a bounded stable regular file. Its receipt carries the checked
record and an empty `guard_manifests` list.

For a Step with assigned findings, Step 2 captures and reports the complete
declaration but does not call it evidence. `hexctl done inoculate` remains
refused while `guard_manifests` is empty, and `done implement` remains refused
while the Step has no valid inoculation receipt. Step 3 alone retains reports,
checks manifests and fills the nonempty list. This freezes the command and
receipt shape without allowing an id declaration to authorise product work.

The signed `kf-453-02` guard commit continues to use exactly the historical
`plugins/hexaemeron/tests/test_issue_453_inoculation_lifecycle.py` path and the
reporter named by the immutable inventory. After retaining that red result,
rename the maintained module to
`plugins/hexaemeron/tests/test_inoculation_lifecycle.py` and update the reporter
to select the numberless module on the fixed tree. The historical commit,
command and report remain unchanged.

The existing `fiat-study-runbook-phase` reviewed span and semantic fixture
remain byte-for-byte unchanged. Remove the proposed `inoculate` row from the
measured `## The loop` table. The table still describes the legacy
implementation-first route for a runbook receipt without a capture. Retain the
public loader/capture paragraph, standalone Inoculation phase note, hard rule,
and Promise entry after the existing reviewed envelope; together they document
the capture-aware exception without extending the old semantic model.

Do not run `agent_instruction.py measure`, `agent_instruction.py parity`, a
tokenizer, a recorded-family adapter, Ollama, or any other model process. Do
not change the semantic model's nodes, bindings, questions or mutations, the
manifest schema or count constants, the instruction implementation or tests,
the language document, or either evidence record. Use only
`python3 scripts/prove_agent_instruction_reconciliation.py reconcile --root .`
after the Fiat source bytes are final. That existing offline operation verifies
the old reviewed span at its recorded offsets, substitutes only the whole-file
source digest in the model and source-span record, derives the compact form
with `format`, refreshes the manifest artefact digests, and rebinds the coverage
row. It opens no socket and runs no model. The committed `measurement.json` and
`parity.json` remain byte-for-byte identical to the signed guard parent and
make no claim about the new prose.

Refresh the committed study and runbook copies to the current receipted bytes.
The existing ADR draft remains unchanged. All lifecycle tests use the
checked-in controller only in disposable repositories; the live managed run
continues through the installed controller's bootstrap `implement` path and
must not invoke the checked-in controller for a live transition.

Complete replacement Files: The guard-only commit has already created
`plugins/hexaemeron/tests/test_issue_453_inoculation_lifecycle.py` and changed
`plugins/hexaemeron/tests/emit_issue_453_guard_report.py`. In the fixed tree,
rename the former to
`plugins/hexaemeron/tests/test_inoculation_lifecycle.py` and update the reporter
again. Change
`plugins/hexaemeron/skills/protasis/scripts/known_failure_inventory.py`,
`plugins/hexaemeron/tests/test_known_failure_inventory.py`,
`plugins/hexaemeron/skills/protasis/SKILL.md`,
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/skills/fiat/SKILL.md`,
`plugins/hexaemeron/agents/mason.md`,
`plugins/hexaemeron/tests/test_hexctl.py`,
`plugins/hexaemeron/tests/test_fiat_skill.py`,
`tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/model.json`,
`tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/compact.wai`,
`tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/source-spans.json`,
`tests/fixtures/agent-instruction-v1/manifest.json`,
`tests/promise_machine_coverage.json`,
`docs/known-failure-inoculation-study.md`, and
`plugins/hexaemeron/docs/known-failure-inoculation/runbook.md`. Create
`plugins/hexaemeron/tests/fixtures/issue-453/no-known-findings.json`.

Read but do not change
`scripts/prove_agent_instruction_reconciliation.py` and
`docs/decisions/drafts/require-inoculation-before-implementation.md`. Do not
change `scripts/agent_instruction.py`, `tests/test_agent_instruction.py`,
`tests/test_agent_instruction_corpus.py`,
`docs/agent-instruction-language-v1.md`,
`tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/questions.json`,
`tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/mutations.json`,
`tests/fixtures/agent-instruction-v1/manifest.schema.json`,
`tests/fixtures/agent-instruction-v1/evidence/measurement.json`, or
`tests/fixtures/agent-instruction-v1/evidence/parity.json`. Refresh the ignored
local portable verification payload without staging it. Regenerate
`.horos/boundary.json`, `.horos/candidates.json`, and `.horos/census.json` only
when the repository-owned scan changes them. Warden alone changes the
configured audit record and synopsis.

Complete replacement Tests: The signed guard-only commit is
`13a2c9f22065c89e85d031bd5bb084b36a487670`, its sole parent is the exact
`branch_from` head `1019fd36326b7e1c51765f3f0d5a0ef57805304a`, and its changed
paths are exactly the historical lifecycle module and reporter. Its retained
Elenchus report is already `guarded`. On the fixed tree run:

```bash
python3 plugins/hexaemeron/tests/emit_issue_453_guard_report.py --case kf-453-02 --report .elenchus/issue-453-kf-453-02-green.json
python3 plugins/hexaemeron/skills/protasis/scripts/known_failure_inventory.py docs/known-failure-inoculation-study.md plugins/hexaemeron/docs/known-failure-inoculation/runbook.md --repository . --expected-id kf-453-01 --expected-id kf-453-02 --expected-id kf-453-03 --expected-id kf-453-04 --expected-id kf-453-05 --expected-id kf-453-06 --expected-id kf-453-07
python3 -m unittest plugins.hexaemeron.tests.test_known_failure_inventory -v
python3 -m unittest plugins.hexaemeron.tests.test_inoculation_lifecycle -v
python3 -m unittest plugins.hexaemeron.tests.test_hexctl -v
python3 -m unittest plugins.hexaemeron.tests.test_fiat_skill -v
git diff --exit-code HEAD -- scripts/agent_instruction.py tests/test_agent_instruction.py tests/test_agent_instruction_corpus.py docs/agent-instruction-language-v1.md tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/questions.json tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/mutations.json tests/fixtures/agent-instruction-v1/manifest.schema.json tests/fixtures/agent-instruction-v1/evidence/measurement.json tests/fixtures/agent-instruction-v1/evidence/parity.json
python3 scripts/prove_agent_instruction_reconciliation.py reconcile --root .
git diff --exit-code HEAD -- scripts/agent_instruction.py tests/test_agent_instruction.py tests/test_agent_instruction_corpus.py docs/agent-instruction-language-v1.md tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/questions.json tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/mutations.json tests/fixtures/agent-instruction-v1/manifest.schema.json tests/fixtures/agent-instruction-v1/evidence/measurement.json tests/fixtures/agent-instruction-v1/evidence/parity.json
python3 scripts/agent_instruction.py check --root . --manifest tests/fixtures/agent-instruction-v1/manifest.json
python3 -m unittest tests.test_agent_instruction tests.test_agent_instruction_corpus tests.test_repository_naming -v
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/run_checks.py --base 5bc2494c4f5802efcd8a92e58554809ac4b9f147
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/PORTABLE.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/scripts/verify_runtime.py plugins docs
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/known-failure-inoculation-study.md plugins/hexaemeron/docs/known-failure-inoculation/runbook.md plugins/hexaemeron/skills/protasis/SKILL.md plugins/hexaemeron/skills/fiat/SKILL.md plugins/hexaemeron/agents/mason.md docs/decisions/drafts/require-inoculation-before-implementation.md audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md --max-defects 0
for draft in plugins/hexaemeron/skills/protasis/SKILL.md plugins/hexaemeron/skills/fiat/SKILL.md plugins/hexaemeron/agents/mason.md docs/decisions/drafts/require-inoculation-before-implementation.md; do
  python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py "$draft" --mode report || exit 1
done
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md --mode fiat-audit-record
git diff --check
```

The inventory cases cover explicit absence only when both surfaces are absent,
every attempted malformed or partial surface as a K000 through K012 finding,
one stable clean capture, canonical digesting, assignment order and source
drift. Lifecycle cases cover phase order, exact packet reconstruction, closed
receipt shapes, zero-assigned no-known evidence, nonempty-assigned
empty-manifest refusal, foreign options, legacy states, changed parents and
unchanged state, design-transition, ledger and checkpoint bytes on every
refusal. The first and second `git diff --exit-code` commands prove the
forbidden semantic and model-evidence surfaces are unchanged both before and
after reconciliation. The instruction check and focused suites prove the
mechanical digest rebind without executing a model. Warden uses command
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`,
format `unittest-json-v1`, and file
`.elenchus/fiat-453-step-2-audit.json`, then reruns every Exit command after a
fix.

Run the root suites from a clean detached worktree at the exact signed Step 2
candidate. The managed controller worktree contains ignored controller
evidence and is not a clean root-suite input. The source-copy comparisons and
the explicit Hypomnema study-mode command run in the managed controller
worktree because they consume receipted artefacts and untracked design
evidence. The study and runbook are completeness-oriented specifications, so
Brevitas does not budget them; Imprimatur and Hypomnema still inspect them. The
audit synopsis, Imprimatur audit input, and Fiat-audit-record Brevitas command
run on the audit branch after Warden owns the audit update.

Complete replacement Disciplines: phylax: the study, inventory object, source
views, worker packets, controller arguments, paths, commands and evidence files
cross parser, process and filesystem boundaries, so closed keys, caps,
containment, stable no-follow reads, exact Git objects and mutation ordering are
checked before use. An attempted inventory surface fails closed and can never
be reclassified as absence. ephoros: `status --json`, `next`, receipt stdout and
stable named refusals expose phase, inventory digest, assigned count, completed
ids, remaining ids and no-known provenance without source or report content.
metron: none; no performance or model-measurement claim is in scope. elenchus:
the retained `kf-453-02` guard must fail by assertion at the exact Step 2 parent
through the signed two-path guard commit and finish green on the fixed tree.
hypomnema: the existing ADR draft owns the phase, atomic receipt,
red-intermediate and bootstrap decisions; Fiat cites its stable identity
without changing it or inventing an integration number. The offline
reconciliation is a deterministic digest repair, not measurement or model
evidence.

**Why.** The prior Step 2 replacement accidentally treated semantic
re-authoring, tokenizer measurement and two-family parity as consequences of
documenting the new lifecycle. That contradicts the controller owner's frozen
boundary. The new text can remain outside the already reviewed source envelope,
so the old semantic fixture and evidence remain truthful and untouched. Only
the whole-file source digest and its deterministic derivatives need repair.
This preserves the complete capture, lifecycle, guard, legacy-state and audit
requirements while explicitly forbidding the model and measurement paths.

**Steps touched.** Step 2's Exit, Files, Tests, and Disciplines.

**Still holding.** Step 2: entry holds; exit holds. Step 3: entry holds; exit
holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.


### Amendment -- 2026-09-06

**What changed.** Complete replacement Files: The guard-only commit has already created
`plugins/hexaemeron/tests/test_issue_453_inoculation_lifecycle.py` and changed
`plugins/hexaemeron/tests/emit_issue_453_guard_report.py`. In the fixed tree,
rename the former to
`plugins/hexaemeron/tests/test_inoculation_lifecycle.py` and update the reporter
again. Change
`plugins/hexaemeron/skills/protasis/scripts/known_failure_inventory.py`,
`plugins/hexaemeron/tests/test_known_failure_inventory.py`,
`plugins/hexaemeron/skills/protasis/SKILL.md`,
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/skills/fiat/SKILL.md`,
`plugins/hexaemeron/agents/mason.md`,
`plugins/hexaemeron/tests/test_hexctl.py`,
`plugins/hexaemeron/tests/test_fiat_skill.py`,
`tests/test_promise_machine_contract.py`,
`tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/model.json`,
`tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/compact.wai`,
`tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/source-spans.json`,
`tests/fixtures/agent-instruction-v1/manifest.json`,
`tests/promise_machine_coverage.json`,
`docs/known-failure-inoculation-study.md`, and
`plugins/hexaemeron/docs/known-failure-inoculation/runbook.md`. Create
`plugins/hexaemeron/tests/fixtures/issue-453/no-known-findings.json`.

Read but do not change
`scripts/prove_agent_instruction_reconciliation.py` and
`docs/decisions/drafts/require-inoculation-before-implementation.md`. Do not
change `scripts/agent_instruction.py`, `tests/test_agent_instruction.py`,
`tests/test_agent_instruction_corpus.py`,
`docs/agent-instruction-language-v1.md`,
`tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/questions.json`,
`tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/mutations.json`,
`tests/fixtures/agent-instruction-v1/manifest.schema.json`,
`tests/fixtures/agent-instruction-v1/evidence/measurement.json`, or
`tests/fixtures/agent-instruction-v1/evidence/parity.json`. Refresh the ignored
local portable verification payload without staging it. Regenerate
`.horos/boundary.json`, `.horos/candidates.json`, and `.horos/census.json` only
when the repository-owned scan changes them. Warden alone changes the
configured audit record and synopsis.

**Why.** The signed Step 2 product range changes
`tests/test_promise_machine_contract.py` to admit
`fiat-known-failure-inoculation` into the required Promise set and increase the
runtime binding cardinality from 47 to 48. That contract test is mechanically
required by the already-declared promise/runtime binding, but the latest
complete replacement Files field omitted it. This replacement corrects only
the file inventory. Every other changed, created, read-only, forbidden,
ignored-generated, Horos-conditional, and Warden-owned classification remains
unchanged. The frozen semantic fixture and model evidence remain outside
scope: measurement, parity, tokenizer, recorded-family adapter, Ollama, and
every other model process remain explicitly disabled.

**Steps touched.** Step 2's Files field only.

**Still holding.** Step 2: entry holds; exit holds. Step 3: entry holds; exit
holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.
