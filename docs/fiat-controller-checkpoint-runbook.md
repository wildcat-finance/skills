# Runbook: portable Fiat controller-state recovery

### Source receipts

```text
study sha256: ef73798be8ed333cce2626c9a5ccd4a59bb7877217ae8516be1665daa619b000
starting ref: 66da3817761415f31bd467140ac1510f77b91b62
run branch: fiat/557-portable-run-state-recovery-r2
task issue: https://github.com/wildcat-finance/skills/issues/557
halted predecessor state sha256: 92a9dcce5a9aec8c210e4da87cd64a1d35975ddc3b081df32714639b267d2810
```

The study selects Fiat as the owner and one capability with four
dependency-ordered steps. Step 1 records the accepted design in ADR-028 and
publishes the receipted proposition under a fresh Mason and Warden cycle.
Step 2 adds deterministic export. Step 3 adds checked relocation and the
clone-loss guard. Step 4 reconciles the public contract, version and generated
surfaces and runs the complete demonstration. The halted predecessor remains
prior evidence only; no successor receipt reuses its commit, audit or prose
draft. This is generation work, so Fiat's held issue 363 frontier remains
byte-identical. Global version identifiers are chosen only in Step 4 after
re-reading the then-current base. Audit records append to
`audit/rounds/fiat-557-portable-run-state-recovery-r2.md`.

## Step 1: Record and publish the accepted recovery design

**Goal.** Amend ADR-028 with the accepted controller-capsule decision and
publish byte-identical tracked copies of the receipted study and runbook before
controller code changes.

**Entry.** The exact run branch `fiat/557-portable-run-state-recovery-r2` at
starting ref `66da3817761415f31bd467140ac1510f77b91b62`; the study receipt names
SHA-256 `ef73798be8ed333cce2626c9a5ccd4a59bb7877217ae8516be1665daa619b000`.
The halted predecessor's Step 1 commit and audit are not successor receipts.
ADR-028 accepts checkpoint-only continuation but does not yet record the
`fiat-controller-checkpoint/v1` capsule, relocation receipt, retained outer
transport, or rejected complete-automation, Git-ref and predecessor-reuse
designs.

**Exit.** All of the following hold:

1. ADR-028 carries a dated amendment that records the controller-state capsule
   and same-ledger relocation receipt, keeps semantic checkpoint identity and
   the outer archive separate, names the retained manual-transport trade, and
   rejects complete standing-checkpoint automation, Git-only controller state,
   and reuse of the predecessor Step 1 before the record exists.
2. `docs/fiat-controller-checkpoint-study.md` and
   `docs/fiat-controller-checkpoint-runbook.md` are byte-identical to their
   receipted `.hexaemeron` sources and point to ADR-028 as the standing record;
   neither calls itself a durable decision home.
3. `tests.test_fiat_checkpoint_decision_record` fails on the entry tree and
   passes on the complete Step 1 tree. Protasis accepts the study and runbook;
   Hypomnema and Imprimatur accept all three documents; their relative links
   resolve; Horos describes the tracked tree; the root and Hexaemeron suites
   and `git diff --check` exit 0.
4. A fresh Warden round reviews the ADR, both tracked run artefacts and the
   recovery-predecessor boundary. No predecessor audit result substitutes for
   that round.

**Files.** Create `docs/fiat-controller-checkpoint-study.md`,
`docs/fiat-controller-checkpoint-runbook.md`, and
`tests/test_fiat_checkpoint_decision_record.py`; amend
`docs/decisions/ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md`;
update `.horos/boundary.json` only if the deterministic scan changes it; append
only this run's named audit record during Warden rounds. Do not change a
canonical skill, controller script, manifest, ledger, dependency or CI file.

**Tests.** First prove the focused decision-record guard fails against the
entry ref, then pass it on the implementation. Run:

```bash
cmp -s .hexaemeron/study.md docs/fiat-controller-checkpoint-study.md
cmp -s .hexaemeron/runbook.md docs/fiat-controller-checkpoint-runbook.md
mise exec python@3.14.6 -- python3 -m unittest tests.test_fiat_checkpoint_decision_record -v
mise exec python@3.14.6 -- python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/fiat-controller-checkpoint-study.md
mise exec python@3.14.6 -- python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/fiat-controller-checkpoint-runbook.md
mise exec python@3.14.6 -- python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs/fiat-controller-checkpoint-study.md docs/fiat-controller-checkpoint-runbook.md docs/decisions/ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md
mise exec python@3.14.6 -- python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-controller-checkpoint-study.md docs/fiat-controller-checkpoint-runbook.md docs/decisions/ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md
mise exec python@3.14.6 -- python3 plugins/horos/skills/horos/scripts/horos.py check .
mise exec python@3.14.6 -- python3 -m unittest discover -s tests
mise exec python@3.14.6 -- python3 plugins/hexaemeron/tests/run_tests.py
git diff --check
```

For an audit repair, use exactly:

```text
test command: mise exec python@3.14.6 -- python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}
report format: unittest-json-v1
expected report schema: elenchus.unittest.v1
report file: .elenchus/fiat-557-r2-step-1.json
```

The report path must be fresh. A missing, stale, empty, malformed or
infrastructure-failed report is `inconclusive`.

**Disciplines.** phylax: no runtime boundary opens, but the predecessor-to-
successor evidence boundary must keep old receipts out of new claims. ephoros:
none, because static records run nothing unattended. metron: none, because no
performance claim is made. elenchus: the focused record guard, byte identity,
structure, links, boundary and suites stop the step, and repairs use the exact
runner above. hypomnema: ADR-028 is the standing home for the accepted
decision; the tracked study and runbook remain reviewed run artefacts that
point to it.

## Step 2: Export a deterministic controller capsule

**Goal.** `hexctl checkpoint export` captures a verified live controller tree
at one accepted boundary into a deterministic, bounded and privately staged
capsule without changing the run.

**Entry.** Step 1's signed, audited and prose-checked tip. ADR-028 records the
accepted design, while the entry controller has no `checkpoint` parser or
native export path. Preserve that red interface and the clone-local failure
before adding export.

**Exit.** All of the following hold:

1. `checkpoint export --out <directory>` is a locked mutating command that
   accepts only a post-`done push` boundary before another action or an active
   `audit-verdict`; every other phase or pending transaction refuses before an
   output appears.
2. The output uses `fiat-controller-checkpoint/v1`, contains a closed
   `MANIFEST.json` plus the complete `.hexaemeron` regular-file tree except the
   transient lock, and records the sorted inventory, resource totals, source
   state and ledger identities, ledger tail, controller identity, semantic
   directive and exact ref boundary without a timestamp or source path.
3. No-follow stable reads, regular-file and hard-link checks, the study's
   count, size and path caps, fixed-argument bounded Git, private modes and a
   sibling stage followed by atomic rename close the live-tree boundary.
   Symlinks, special files, moving inputs, unsafe paths, duplicate JSON keys,
   cap breaches and occupied destinations refuse without state or ledger
   change and without captured bytes in diagnostics.
4. Two exports of unchanged state at both accepted boundaries are byte-
   identical, the manifest's out-of-band SHA-256 is reported, interruption
   before publication leaves no valid-looking final capsule, and all focused
   export guards are green.
5. The focused module, both repository suites, the three non-Solidity
   discipline lints, Imprimatur on changed prose, Horos and `git diff --check`
   exit 0.

**Files.** Change or create only
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/tests/test_hexctl_checkpoint.py`,
`plugins/hexaemeron/skills/fiat/references/controller-checkpoint.md`,
`tests/promise_machine_coverage.json` for changed source digests,
`.horos/boundary.json` when its scan changes it, and this run's append-only
audit record. Do not expose restore yet, move version fields, alter existing
receipts or change the standing outer-checkpoint procedure.

**Tests.** Preserve the red entry behaviour, implement the export-focused
tests including `test_export_is_deterministic_at_both_boundaries`,
`test_export_refuses_every_unaccepted_boundary`, and
`test_resource_limits_refuse_before_publish`, then run:

```bash
mise exec python@3.14.6 -- python3 -m unittest plugins.hexaemeron.tests.test_hexctl_checkpoint -v
mise exec python@3.14.6 -- python3 plugins/hexaemeron/tests/run_tests.py
mise exec python@3.14.6 -- python3 scripts/run_checks.py
mise exec python@3.14.6 -- python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
mise exec python@3.14.6 -- python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
mise exec python@3.14.6 -- python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs
mise exec python@3.14.6 -- python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/fiat/scripts/hexctl.py plugins/hexaemeron/tests/test_hexctl_checkpoint.py plugins/hexaemeron/skills/fiat/references/controller-checkpoint.md
mise exec python@3.14.6 -- python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

For an audit repair, use exactly:

```text
test command: mise exec python@3.14.6 -- python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}
report format: unittest-json-v1
expected report schema: elenchus.unittest.v1
report file: .elenchus/fiat-557-r2-step-2.json
```

The report path must be fresh. A missing, stale, empty, malformed or
infrastructure-failed report is `inconclusive`.

**Disciplines.** phylax: operator paths, the live controller tree, Git refs,
manifest fields and recursive filesystem entries are hostile boundaries and
receive the study's containment, no-follow, cap, fixed-argument and private-
output controls. ephoros: the command emits the accepted boundary, ledger and
manifest identities, bounded counts, semantic directive and destination; no
service metrics or alert is added. metron: none, because the resource ceilings
are safety caps rather than speed targets. elenchus: the missing entry command
and each hostile or interrupted export specimen receive focused guards before
the full suites. hypomnema: the standalone checkpoint reference records the
public format and refusal reasons while ADR-028 keeps the decision.

## Step 3: Restore the same ledger in a fresh clone

**Goal.** `hexctl checkpoint restore` verifies a capsule and separately
restored Git boundary, relocates only controller-owned paths, appends one
receipt to the same ledger and recreates the run in a fresh origin without
acting on its next directive.

**Entry.** Step 2's signed, audited and prose-checked tip. Deterministic export
and its hostile-input guards are green; the entry controller has no restore
parser or relocation transaction and the clone-loss demonstration is red.

**Exit.** All of the following hold:

1. `checkpoint restore --from <capsule> --manifest-sha256 <digest>` accepts
   only an empty fresh origin and an unoccupied marker-owned derived worktree,
   reads the capsule as hostile input under the export caps, verifies canonical
   manifest bytes, inventory, source state, exact ledger prefix and tail,
   controller identity, expected semantic directive and every exact local Git
   ref before active state exists.
2. Only imported `config.git.origin` and `config.git.worktree` change before
   one `checkpoint:restore` event is appended. The event binds the manifest,
   source state and ledger digests, old tail, ref boundary and relocated state
   fingerprint. Opaque evidence files and the old ledger prefix remain byte-
   identical.
3. A marker-first transaction owns the derived worktree and sibling stage.
   Every interruption point is rerunnable to a clean refusal or one completed
   restore; occupied, second-restore, symlinked, moved, digest-mismatched or
   ref-substituted inputs never overwrite or delete an unowned path.
4. Success recreates the breadcrumb, runs the internal `verify`, `status` and
   semantic `next` checks, reports their bounded identities, and executes no
   directive. `test_restore_after_source_clone_loss`, the prefix, relocation,
   replay and interruption guards all pass offline.
5. The focused module, both repository suites, the three non-Solidity
   discipline lints, Imprimatur on changed prose, Horos and `git diff --check`
   exit 0.

**Files.** Change only
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/tests/test_hexctl_checkpoint.py`,
`plugins/hexaemeron/skills/fiat/references/controller-checkpoint.md`,
`tests/promise_machine_coverage.json` for changed source digests,
`.horos/boundary.json` when its scan changes it, and this run's append-only
audit record. Do not add network publication, archive extraction, key handling,
canonical checkpoint identity, a general mutation dispatcher or a new audit
loop.

**Tests.** Preserve the red clone-loss demo on the entry commit, then implement
`test_restore_after_source_clone_loss`,
`test_restore_preserves_prefix_and_appends_one_receipt`,
`test_restore_relocates_only_controller_paths`, replay, ref-substitution,
hostile-file and every interruption-window specimen. Run:

```bash
mise exec python@3.14.6 -- python3 -m unittest plugins.hexaemeron.tests.test_hexctl_checkpoint -v
mise exec python@3.14.6 -- python3 -m unittest plugins.hexaemeron.tests.test_hexctl_checkpoint.HexctlCheckpointTests.test_restore_after_source_clone_loss -v
mise exec python@3.14.6 -- python3 plugins/hexaemeron/tests/run_tests.py
mise exec python@3.14.6 -- python3 scripts/run_checks.py
mise exec python@3.14.6 -- python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
mise exec python@3.14.6 -- python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
mise exec python@3.14.6 -- python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs
mise exec python@3.14.6 -- python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/fiat/scripts/hexctl.py plugins/hexaemeron/tests/test_hexctl_checkpoint.py plugins/hexaemeron/skills/fiat/references/controller-checkpoint.md
mise exec python@3.14.6 -- python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

For an audit repair, use exactly:

```text
test command: mise exec python@3.14.6 -- python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}
report format: unittest-json-v1
expected report schema: elenchus.unittest.v1
report file: .elenchus/fiat-557-r2-step-3.json
```

The report path must be fresh. A missing, stale, empty, malformed or
infrastructure-failed report is `inconclusive`.

**Disciplines.** phylax: capsule bytes, manifest paths, imported state and
ledger, Git refs, the fresh origin, marker-owned worktree and every filesystem
write are hostile boundaries and receive exact-digest, no-follow, containment,
cap, fixed-argument and no-overwrite controls. ephoros: bounded restore output
names manifest and ledger identities, ref counts, transaction recovery, target
worktree, verify result and semantic next directive without captured content;
no alert is added. metron: none, because no performance claim is made.
elenchus: the clone-loss failure and each transaction window receive a parent-
red guard before full-suite evidence. hypomnema: the checkpoint reference owns
the restore schema and recovery states; ADR-028 remains the decision record.

## Step 4: Publish the contract and demonstrate portable recovery

**Goal.** Reconcile every public Fiat and contributor surface, move the Fiat
generation and Hexaemeron package versions once, regenerate installed copies
and the contributor PDF, and demonstrate the complete scoped recovery path.

**Entry.** Step 3's signed, audited and prose-checked tip. Export, restore and
their focused guards are green; public skill, checkpoint procedure, version,
portable runtime and contributor-guide surfaces still describe the entry
controller. Re-read the then-current base and choose the next free generation
and package values at implementation time (expected Fiat `5.34.1` and
Hexaemeron package `1.6.9`).

**Exit.** All of the following hold:

1. Fiat's `SKILL.md` documents export-before-packaging and checked restore-
   after-verification and declares the bounded controller-checkpoint Promise;
   its frontmatter matches exactly one new generation row that keeps status,
   frontier revision, frontier text, issue 363 target and frontier digest
   byte-identical.
2. `push-discipline.md` retains the Git bundle, key, proof, Drive, issue-note,
   outer-sidecar and explicit-waiver duties while replacing manual state copy
   and relocation with the two controller commands. The standalone reference
   remains the schema and recovery authority.
3. `docs/how-to-help-shoggoth.md` removes the stale no-checkpoint warning,
   states the accepted verified-transfer boundary without overstating it, and
   its regenerated PDF agrees. ADR-028 and the beginner primer do not conflict.
4. Hexaemeron's five package-version surfaces agree, generated portable
   Promise Machine copies are synced, coverage digests and evolution literals
   are current, and the Horos boundary describes every generated change.
5. The exact clone-loss demo, all focused tests, the Hexaemeron suite, the
   checked root runner, portable-runtime check, version and evolution checks,
   all changed-prose lints, PDF regeneration and `git diff --check` exit 0.

**Files.** Change only the Step 2-3 files as needed for final contract text,
`plugins/hexaemeron/skills/fiat/SKILL.md`,
`plugins/hexaemeron/skills/fiat/EVOLUTION.md`,
`plugins/hexaemeron/skills/fiat/references/push-discipline.md`,
`docs/how-to-help-shoggoth.md`, `docs/pdf/how-to-help-shoggoth.pdf`,
`plugins/hexaemeron/.claude-plugin/plugin.json`,
`plugins/hexaemeron/.codex-plugin/plugin.json`,
`.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`,
`tests/test_version_propagation.py`, `tests/test_evolution_contract.py`,
`tests/promise_machine_coverage.json`, generated paths written by
`scripts/portable_promise_machine.py sync`, `.horos/boundary.json`, and this
run's append-only audit record. Do not change Fiat's held frontier or any issue
owned by #560, #561 or #682.

**Tests.** Update version, promise, portable-copy, documentation, PDF and
generated-surface guards as needed. Use the checked-in optional document
runtime for the PDF builder, then run:

```bash
/home/kethcode/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/build_contributor_guide.py
mise exec python@3.14.6 -- python3 -m unittest plugins.hexaemeron.tests.test_hexctl_checkpoint -v
mise exec python@3.14.6 -- python3 -m unittest plugins.hexaemeron.tests.test_hexctl_checkpoint.HexctlCheckpointTests.test_restore_after_source_clone_loss -v
mise exec python@3.14.6 -- python3 plugins/hexaemeron/tests/run_tests.py
mise exec python@3.14.6 -- python3 scripts/portable_promise_machine.py check
mise exec python@3.14.6 -- python3 -m unittest tests.test_version_propagation tests.test_evolution_contract tests.test_child_or_golden_retriever_primer
mise exec python@3.14.6 -- python3 scripts/run_checks.py
mise exec python@3.14.6 -- python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/fiat/SKILL.md plugins/hexaemeron/skills/fiat/EVOLUTION.md plugins/hexaemeron/skills/fiat/references/controller-checkpoint.md plugins/hexaemeron/skills/fiat/references/push-discipline.md docs/fiat-controller-checkpoint-study.md docs/fiat-controller-checkpoint-runbook.md docs/how-to-help-shoggoth.md docs/decisions/ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md
mise exec python@3.14.6 -- python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

For an audit repair, use exactly:

```text
test command: mise exec python@3.14.6 -- python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}
report format: unittest-json-v1
expected report schema: elenchus.unittest.v1
report file: .elenchus/fiat-557-r2-step-4.json
```

The report path must be fresh. A missing, stale, empty, malformed or
infrastructure-failed report is `inconclusive`.

**Disciplines.** phylax: the step preserves the established capsule and outer
checkpoint boundaries and runs their lint after generated copies move.
ephoros: command results and receipts remain the bounded signals; no alert or
service is added. metron: none, because the demonstration makes no performance
claim. elenchus: the clone-loss guard and complete selected checks stop the
release on any regression. hypomnema: Fiat's generation row records the
behaviour change, ADR-028 records the decision, and the reference, skill,
checkpoint procedure and contributor guide are the homes their audiences
start from.
