# Runbook: immutable Fiat run anchors and checkpoint identity

### Source receipts

```text
study sha256: 0fe8d030fc9d1b83cbf4793f60982af153553750aa8962565cfc56bf3d10b9ea
starting ref: 8c4073ed5db91986e74c4500867ba630cecce15b
run branch: fiat/560-bind-portable-runs-to-an-immutable-base-and
task issue: https://github.com/wildcat-finance/skills/issues/560
predecessor: skills#557, pull request #772, ADR-028
```

The study selects one capability in three dependency-ordered steps. Step 1
records and implements the immutable init anchor. Step 2 derives a canonical,
read-only checkpoint identity from verified controller evidence. Step 3 proves
the narrow hand-off that issue #561 needs and publishes the versioned
contract. Issues #508 and #547 remain boundaries, while #561 archive work and
#682 mutation dispatch remain out of scope. Existing license, CI and toolchain
files are reused. Audit rounds append only to
`audit/rounds/fiat-560-bind-portable-runs-to-an-immutable-base-and.md`.

## Step 1: Record and pin the immutable run anchor

**Goal.** Resolve a run's starting ref once before initialization mutates the
repository, retain its named integration branch separately, and record the
joined `fiat-run-anchor/v1` evidence.

**Entry.** Exact run branch
`fiat/560-bind-portable-runs-to-an-immutable-base-and` at
`8c4073ed5db91986e74c4500867ba630cecce15b`, with receipted study SHA-256
`0fe8d030fc9d1b83cbf4793f60982af153553750aa8962565cfc56bf3d10b9ea`.
The entry controller stores a named `--base main` in `state.base` and can
resolve it again after the branch moves. This run itself was initialized by
that legacy controller and must not be retroactively anchored.

**Exit.** All of the following hold:

1. Before its first filesystem mutation, `init` resolves the requested
   starting ref to exactly one full commit, creates the worktree from that
   commit, stores it in `state.base`, and retains the named delivery branch in
   `config.git.base`. A commit input retains the configured integration branch.
2. The initial state and ledger event bind one closed
   `fiat-run-anchor/v1` receipt to repository, task, run id, run branch,
   integration branch, controller identity and immutable starting commit.
   Verification checks every join when the receipt is present, accepts legacy
   absence for existing commands, and provides no post-init re-anchor mutation.
3. A named-base movement guard fails on the entry controller and passes on the
   implementation. It proves `state.base`, the worktree parent and the anchor
   remain the pre-mutation commit after `main` moves. Malformed refs, origin or
   task substitution, unsafe integration branches and mismatched anchors
   refuse without a partial worktree, state, ledger or breadcrumb.
4. ADR-028 carries a dated amendment recording the semantic-identity split,
   init-owned anchor, hard legacy identity refusal, and rejected manifest-
   reuse, archive-owned and retired-service alternatives. Tracked study and
   runbook copies are byte-identical to their receipted sources and point to
   ADR-028 as the standing record.
5. The focused module, affected checked runner, portable-runtime check,
   Protasis, Phylax, Ephoros, Hypomnema, Imprimatur, Horos and
   `git diff --check` exit 0. Canonical and generated controller bytes agree.

**Files.** Create
`docs/fiat-checkpoint-identity-study.md`,
`docs/fiat-checkpoint-identity-runbook.md`,
`plugins/hexaemeron/tests/test_hexctl_checkpoint_identity.py`, and any small
JSON fixture owned by that focused module. Amend
`docs/decisions/ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md`
and `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`. Deterministically sync
the generated controller and `.agents/skills/promise-machine/runtime/MANIFEST.json`.
Update only the exact digest bindings required by those changed source bytes:
`plugins/hexaemeron/tests/test_issue_429_recovery.py`,
`tests/promise_machine_coverage.json`,
`scripts/verify_issue_622_inoculation.py`, and
`tests/fixtures/issue-622-inoculation-v1.json`. Regenerate
`.horos/boundary.json` and `.horos/candidates.json` only when their generators
change them. Warden may append this run's named audit record and synopsis.
Do not add identity output, archive work, a dependency, CI change or version
bump in this step.

**Tests.** Preserve a parent-red focused guard named
`test_init_named_base_is_resolved_once_before_worktree_add`, then run:

```bash
mise exec node@26.6.0 python@3.14.6 -- python3 -m unittest plugins.hexaemeron.tests.test_hexctl_checkpoint_identity.HexctlCheckpointIdentityTests.test_init_named_base_is_resolved_once_before_worktree_add -v
mise exec node@26.6.0 python@3.14.6 -- python3 -m unittest plugins.hexaemeron.tests.test_hexctl_checkpoint_identity -v
cmp -s .hexaemeron/study.md docs/fiat-checkpoint-identity-study.md
cmp -s .hexaemeron/runbook.md docs/fiat-checkpoint-identity-runbook.md
mise exec python@3.14.6 -- python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/fiat-checkpoint-identity-study.md
mise exec python@3.14.6 -- python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/fiat-checkpoint-identity-runbook.md
mise exec python@3.14.6 -- python3 scripts/portable_promise_machine.py check
mise exec node@26.6.0 python@3.14.6 -- python3 scripts/run_checks.py
mise exec python@3.14.6 -- python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
mise exec python@3.14.6 -- python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
mise exec python@3.14.6 -- python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs
mise exec python@3.14.6 -- python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-checkpoint-identity-study.md docs/fiat-checkpoint-identity-runbook.md docs/decisions/ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md plugins/hexaemeron/skills/fiat/scripts/hexctl.py plugins/hexaemeron/tests/test_hexctl_checkpoint_identity.py
mise exec python@3.14.6 -- python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

For every audit repair, use exactly:

```text
test command: mise exec node@26.6.0 python@3.14.6 -- python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}
report format: unittest-json-v1
expected report schema: elenchus.unittest.v1
report file: .elenchus/fiat-560-step-1.json
```

The report path must be fresh. A missing, stale, empty, malformed, zero-test or
infrastructure-failed report is `inconclusive`.

**Disciplines.** phylax: operator ref, Git output, target origin and task
identity cross into persistent anchor evidence and need fixed argv, bounded
reads and exact joins. ephoros: init's existing bounded output names the pinned
base and stable refusal class; no unattended signal is added. metron: none,
because one bounded local Git resolution carries no performance claim.
elenchus: the moved-base defect starts parent-red and every repair uses the
exact structured runner above. hypomnema: ADR-028 is the standing home for the
anchor and identity split; tracked study and runbook copies remain run
artefacts.

## Step 2: Build the canonical checkpoint identity provider

**Goal.** Add a read-only `checkpoint identity` command and a pure captured-
bytes helper that derive one domain-separated `snapshot_id` from verified,
path-free controller evidence.

**Entry.** Step 1's signed, audited and prose-checked tip. Future runs have a
verified immutable anchor; legacy export and restore still work without one.
The entry parser accepts only `checkpoint export` and `checkpoint restore`, so
the identity interface is parent-red.

**Exit.** All of the following hold:

1. `checkpoint identity` accepts only an anchored run at ADR-028's existing
   post-push or active audit-verdict boundary. It verifies state, exact
   appendable ledger prefix, tail and fingerprint, current study and runbook
   receipts, behavior-policy projection, optional observation bindings,
   anchor, final receipted working commit and ancestry from the immutable base.
2. The command prints canonical `fiat-checkpoint-identity-result/v1` JSON with
   a closed `fiat-checkpoint-identity/v1` object and a lowercase SHA-256
   `snapshot_id` over the exact domain prefix and canonical identity bytes.
   It takes no mutation lock, changes no state, ledger, Git ref or filesystem
   byte, and refuses before stdout on any mismatch or unstable reread.
3. A pure bounded helper consumes already captured state and ledger bytes plus
   validated Git/ref evidence, returns the same identity object or a fixed
   refusal, and never reopens a path. This is the only hand-off promised to
   #561.
4. Golden bytes and hostile fixtures prove exact keys and types, canonical
   encoding, duplicate-key/type refusal, resource caps, path/secret exclusion,
   domain separation, base and working-commit substitution, boundary and
   ledger drift, policy projection, observation absent/bound distinction, and
   source/ref mutation during the read.
5. Carrier filename, compression, timestamps, permissions, proposed archive
   digest, current branch tip and #557 capsule digest cannot change
   `snapshot_id`; changing any accepted semantic input does. Legacy symbolic-
   base state, missing or mismatched anchor, unreceipted or non-descendant
   working commit and non-checkpoint phase refuse without writes.
6. The focused module, complete Hexaemeron and root coverage selected by the
   affected checked runner, portable runtime, three discipline lints,
   Imprimatur, Horos and `git diff --check` exit 0.

**Files.** Amend
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py` and
`plugins/hexaemeron/tests/test_hexctl_checkpoint_identity.py`; create the
module's exact golden/hostile fixture and
`plugins/hexaemeron/skills/fiat/references/checkpoint-identity.md`.
Deterministically sync the generated controller, generated reference and
runtime manifest. Update only their exact issue-429, Promise coverage and
issue-622 digest closures in
`plugins/hexaemeron/tests/test_issue_429_recovery.py`,
`tests/promise_machine_coverage.json`,
`scripts/verify_issue_622_inoculation.py`, and
`tests/fixtures/issue-622-inoculation-v1.json`; update
`tests/test_promise_machine_contract.py` only if the new executable reference
changes its fixed contract inventory. Regenerate Horos boundary/candidates
only when prescribed, and append only this run's audit record/synopsis. Do not
change native export/restore meaning, checkpoint boundaries, versions, public
SKILL prose, CI, dependencies, archive bytes, publication or mutation policy.

**Tests.** Preserve a parent-red command guard, then implement the complete
focused module including
`test_identity_is_read_only_and_byte_stable`,
`test_identity_refuses_legacy_symbolic_base`,
`test_carrier_fields_do_not_change_snapshot_id`, and
`test_semantic_inputs_each_change_snapshot_id`. Run:

```bash
mise exec node@26.6.0 python@3.14.6 -- python3 -m unittest plugins.hexaemeron.tests.test_hexctl_checkpoint_identity -v
mise exec node@26.6.0 python@3.14.6 -- python3 plugins/hexaemeron/tests/run_tests.py
mise exec python@3.14.6 -- python3 scripts/portable_promise_machine.py check
mise exec node@26.6.0 python@3.14.6 -- python3 scripts/run_checks.py
mise exec python@3.14.6 -- python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
mise exec python@3.14.6 -- python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
mise exec python@3.14.6 -- python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs
mise exec python@3.14.6 -- python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/fiat/scripts/hexctl.py plugins/hexaemeron/tests/test_hexctl_checkpoint_identity.py plugins/hexaemeron/skills/fiat/references/checkpoint-identity.md
mise exec python@3.14.6 -- python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

For every audit repair, use exactly:

```text
test command: mise exec node@26.6.0 python@3.14.6 -- python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}
report format: unittest-json-v1
expected report schema: elenchus.unittest.v1
report file: .elenchus/fiat-560-step-2.json
```

The report path must be fresh. A missing, stale, empty, malformed, zero-test or
infrastructure-failed report is `inconclusive`.

**Disciplines.** phylax: state, ledger, receipts, config, Git objects and
captured bytes cross into digest authority and need closed schemas, caps,
stable reads, exact types and fixed-argument Git. ephoros: stable JSON answers
which anchor, boundary, commit and evidence prefix produced an identity, while
fixed refusal classes explain absence; no retained service signal is added.
metron: none, because existing caps are safety bounds and no speed target is
claimed. elenchus: missing-command, hostile-input, source-drift and
differential specimens are guards under the exact runner. hypomnema: the new
reference owns callable schema and refusals while ADR-028 retains the decision.

## Step 3: Publish and demonstrate the issue 561 hand-off

**Goal.** Publish the versioned Fiat contract and prove that one moved-base
run yields stable semantic identity while carrier-only changes stay outside it.

**Entry.** Step 2's signed, audited and prose-checked tip with the anchor and
identity provider green. No outer archive, inspection or restore work from
#561 exists in this run.

**Exit.** All of the following hold:

1. The exact problem-statement demo initializes a future run from named
   `main`, advances `main`, reaches an accepted boundary and proves the stored
   base, worktree parent and run anchor remain the pre-mutation commit. Repeated
   identity output is byte-identical after branch movement.
2. The demo proves carrier labels and proposed archive digest do not affect
   `snapshot_id`, while working commit, ledger prefix, receipted study or
   runbook, policy projection and observation binding each do. Every named
   legacy, anchor, ancestry, receipt and boundary refusal is write-free.
3. Fiat's canonical SKILL, evolution ledger and checkpoint-identity reference
   state the read-only interface, evidence boundary, hard legacy refusal and
   #561 hand-off without claiming archive, service, portable-green or
   dispatcher work. Generated runtime copies are byte-identical.
4. Against the isolated base, generation work uses the valid next label
   `fiat-v5.36.1` and Hexaemeron plugin version `1.6.11`; integration later
   re-reads remote `main` and selects the then-next free labels without
   rewriting the behavior claim. Every manifest and version guard agrees.
5. The focused demo, full focused module, complete affected checked runner,
   portable runtime, deterministic contributor-guide build if selected,
   version/evolution guards, Phylax, Ephoros, Hypomnema, Imprimatur, Horos and
   `git diff --check` exit 0. No unresolved finding remains in the final audit
   round.

**Files.** Amend canonical Fiat `SKILL.md`, `EVOLUTION.md`, the checkpoint-
identity reference and the tracked study/runbook only if final verified facts
require a source-preserving correction. Update the Hexaemeron plugin version
in `.claude-plugin/marketplace.json`,
`plugins/hexaemeron/.claude-plugin/plugin.json`, and
`plugins/hexaemeron/.codex-plugin/plugin.json`; update exact version bindings
in `tests/test_evolution_contract.py`, `tests/test_version_propagation.py`,
`scripts/build_child_or_golden_retriever_primer.py`, and
`tests/test_child_or_golden_retriever_primer.py`. Deterministically sync the
full portable Promise Machine runtime and manifest. Regenerate
`docs/how-to-help-shoggoth.md` and its PDF only when the checked builder selects
them. Admit exact generator-owned closures in
`tests/promise_machine_coverage.json`,
`tests/test_promise_machine_contract.py`,
`plugins/hexaemeron/tests/test_phylax_model_proxy.py`,
`tests/test_child_or_golden_retriever_primer.py`,
`plugins/hexaemeron/tests/test_issue_429_recovery.py`,
`scripts/verify_issue_622_inoculation.py`,
`tests/fixtures/issue-622-inoculation-v1.json`, and Horos boundary/candidates
only when their checked values change. Extend the focused identity module and
fixture only for the declared demo/refusals. Append only this run's audit
record/synopsis. Do not create #561 archive bytes, change CI/dependencies, or
touch #508, #547 or #682 behavior.

**Tests.** The mandatory demonstration is:

```bash
mise exec node@26.6.0 python@3.14.6 -- python3 -m unittest plugins.hexaemeron.tests.test_hexctl_checkpoint_identity.HexctlCheckpointIdentityTests.test_identity_survives_named_base_movement_and_separates_transport -v
```

Then run:

```bash
mise exec node@26.6.0 python@3.14.6 -- python3 -m unittest plugins.hexaemeron.tests.test_hexctl_checkpoint_identity -v
mise exec node@26.6.0 python@3.14.6 -- python3 plugins/hexaemeron/tests/run_tests.py
mise exec python@3.14.6 -- python3 scripts/portable_promise_machine.py check
mise exec node@26.6.0 python@3.14.6 -- python3 scripts/run_checks.py
mise exec python@3.14.6 -- python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
mise exec python@3.14.6 -- python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
mise exec python@3.14.6 -- python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs
mise exec python@3.14.6 -- python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/fiat/SKILL.md plugins/hexaemeron/skills/fiat/EVOLUTION.md plugins/hexaemeron/skills/fiat/references/checkpoint-identity.md docs/fiat-checkpoint-identity-study.md docs/fiat-checkpoint-identity-runbook.md
mise exec python@3.14.6 -- python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

For every audit repair, use exactly:

```text
test command: mise exec node@26.6.0 python@3.14.6 -- python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}
report format: unittest-json-v1
expected report schema: elenchus.unittest.v1
report file: .elenchus/fiat-560-step-3.json
```

The report path must be fresh. A missing, stale, empty, malformed, zero-test or
infrastructure-failed report is `inconclusive`.

**Disciplines.** phylax: the final hostile and differential demonstration
rechecks every digest and Git boundary without widening it. ephoros: sample
stdout and fixed refusals are the operator-facing evidence; #561 owns retained
archive events. metron: none, because the demo makes no performance claim.
elenchus: every final correction retains a parent-red focused guard and uses
the exact structured runner. hypomnema: ADR-028, the callable reference,
EVOLUTION and public SKILL keep their separate decision, interface, history and
audience roles.

### Amendment -- 2026-08-29

**What changed.** Complete replacement Files: Create
`docs/fiat-checkpoint-identity-study.md`,
`docs/fiat-checkpoint-identity-runbook.md`,
`plugins/hexaemeron/tests/test_hexctl_checkpoint_identity.py`, and any small
JSON fixture owned by that focused module. Amend
`docs/decisions/ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md`
and `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`. Deterministically sync
the generated controller and `.agents/skills/promise-machine/runtime/MANIFEST.json`.
Update only the exact digest bindings required by those changed source bytes:
`plugins/hexaemeron/tests/test_issue_429_recovery.py`,
`tests/promise_machine_coverage.json`,
`scripts/verify_issue_622_inoculation.py`, and
`tests/fixtures/issue-622-inoculation-v1.json`. Update only the legacy-state
fixture construction in `plugins/hexaemeron/tests/test_hexctl.py` and
`plugins/hexaemeron/tests/test_hexctl_currency.py` so a fixture that mutates
anchored init state also removes or consistently rebuilds the joined run-anchor
receipt and initial ledger digest; do not relax the production join.
Regenerate `.horos/boundary.json` and `.horos/candidates.json` only when their
generators change them. Warden may append this run's named audit record and
synopsis. Do not add identity output, archive work, a dependency, CI change or
version bump in this step.

**Why.** The complete Hexaemeron suite reproduced two legacy fixtures that
mutate post-init state but leave the new anchor receipt and its initial ledger
binding behind. Accepting that mismatch in production would defeat the anchor;
the narrow fixture repair preserves the hard join and the old behavior each
test actually exercises.

**Steps touched.** Step 1.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds.
