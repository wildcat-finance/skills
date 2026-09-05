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
