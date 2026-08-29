# Runbook: one checked `sync-run` transition across a generator-owned payload

## Source receipts

```text
study sha256: 24e723155b1dd232a2adb2ef2442cd7bf5e9808a3636e8533c5e523e0d6dee56
starting ref: bec742ac17a5fdd95f0242d2b7ba894828cebf22
run branch: fiat/710-give-sync-run-one-checked-transition-across
task issue: https://github.com/wildcat-finance/skills/issues/710
```

Repository commands written as `python3` mean the exact interpreter pinned by
`.python-version`, CPython 3.13.15. The three steps are dependency ordered and
must each be green at entry and exit. Step 1 freezes the accepted design. Step
2 implements the complete canonical, test, version, package, and generated-copy
change in one commit. Step 3 runs the issue topology as the proving demo and
publishes only evidence produced by that final tree. The audit record belongs
at `audit/rounds/fiat-710-give-sync-run-one-checked-transition-across.md`.

## Step 1: Publish the accepted generator-aggregate specification

**Goal.** Commit byte-identical tracked copies of the receipted study and
runbook so the authority, evidence, resource, compatibility, and refusal
decisions used by the implementation remain reviewable from the repository.

**Entry.** The clean run branch
`fiat/710-give-sync-run-one-checked-transition-across` at starting ref
`bec742ac17a5fdd95f0242d2b7ba894828cebf22`; the study receipt names SHA-256
`24e723155b1dd232a2adb2ef2442cd7bf5e9808a3636e8533c5e523e0d6dee56`,
and no tracked issue-710 artefact exists.

**Exit.** All of the following hold:

1. `docs/fiat-sync-run-generator-aggregates-study.md` is byte-identical to
   `.hexaemeron/study.md`.
2. `docs/fiat-sync-run-generator-aggregates-runbook.md` is byte-identical to
   `.hexaemeron/runbook.md`.
3. Protasis accepts the tracked study and runbook; Imprimatur and Brevitas
   accept the shipped prose under their applicable modes; every relative link
   resolves from both tracked publication paths; and Hypomnema reports no
   missing durable home.
4. A deterministic Horos scan describes the tracked tree.
5. The root and Hexaemeron suites pass and `git diff --check` exits 0.

**Files.** Create only
`docs/fiat-sync-run-generator-aggregates-study.md` and
`docs/fiat-sync-run-generator-aggregates-runbook.md`. Permit
`.horos/boundary.json`, `.horos/candidates.json`, and `.horos/census.json` only
when the deterministic Horos write changes them. Permit the configured audit
record and its generated `.synopsis.md` companion only for append-only Warden
rounds. Do not change controller, test, manifest, version, dependency, or CI
files in this step's implementation.

**Tests.** No product test is added. Copy the two receipted artefacts without
rewriting them, then run:

```bash
cmp -s .hexaemeron/study.md docs/fiat-sync-run-generator-aggregates-study.md
cmp -s .hexaemeron/runbook.md docs/fiat-sync-run-generator-aggregates-runbook.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/fiat-sync-run-generator-aggregates-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/fiat-sync-run-generator-aggregates-runbook.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-sync-run-generator-aggregates-study.md docs/fiat-sync-run-generator-aggregates-runbook.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py --mode report docs/fiat-sync-run-generator-aggregates-study.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py --mode report docs/fiat-sync-run-generator-aggregates-runbook.md
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs plugins
python3 plugins/horos/skills/horos/scripts/horos.py check .
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
git diff --check
```

The source-bound Elenchus runner contract for any audit repair is:

```text
test command: python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}
report format: unittest-json-v1
expected report schema: elenchus.unittest.v1
report file: .elenchus/fiat-710-step-1.json
```

The report path must be fresh. A missing, stale, empty, malformed, or
infrastructure-failed report is `inconclusive`, not evidence that a repair is
guarded.

**Disciplines.** phylax: none, because static Markdown opens no input or
execution boundary. ephoros: none, because nothing new runs unattended.
metron: none, because no performance claim is made. elenchus: byte identity,
links, structure, reading-boundary currency, and both suites stop the step;
audit repairs use the exact runner above. hypomnema: the tracked study and
runbook are the durable specification homes selected by the receipted study.

## Step 2: Implement and propagate aggregate-aware v2 revalidation

**Goal.** `done sync-run` accepts the exact v2 generator aggregate selected by
the study, retains the v1 transition byte-for-byte, refuses every malformed or
uncovered surface before mutation, and ships one current canonical controller
through every package and generated-copy surface.

**Entry.** Step 1's signed, audited, prose-checked branch tip. Re-read the live
Fiat ledger, package manifests, ADR directory, and generated runtime before the
first edit. Expected collision-free identities are Fiat `5.31.1`, Hexaemeron
`1.6.6`, and
`docs/decisions/ADR-042-bind-sync-run-generator-aggregates.md`; if any is no
longer free, stop and amend this runbook rather than selecting another value
silently. The entry controller must still reproduce
`integration path delta exceeds 500 paths` for the 1,095-path v1 incident
surface.

**Exit.** All of the following hold:

1. `fiat-integration-revalidation/v1` follows its unchanged parser and
   500-path route. `fiat-integration-revalidation/v2` accepts only the exact
   top-level, aggregate, and check fields fixed by the study.
2. The source registry contains only
   `promise-machine-portable-runtime-v1`, with its exact prefix, generator,
   manifest contract, verification command, 1,024-file ceiling, and 32 MiB
   ceiling. No artefact can create or widen an owner.
3. V2 classifies the complete bounded Git deltas before the individual cap;
   every path remains safe and unique; at most 500 outside paths are exact and
   individually covered; and selected prefixes are exact and non-overlapping.
4. One argv-only, deadline-bound Git object reader proves the final sync tree,
   manifest rows, modes, blob sizes and SHA-256 values without reading the
   worktree. The manifest self row, file count, domain-separated tree digest,
   and Git tree id are recomputed and retained in the normalized receipt.
5. Wrong registry data, count, manifest digest, tree digest, membership, mode,
   object type, batch framing, resource bound, generator command, aggregate
   coverage, or outside-path coverage exits 2 before the exact state or ledger
   bytes change.
6. A focused controller module carries the issue-710 fixture and guards all
   five acceptance groups: the v1 1,095-path refusal; the v2 887-file aggregate
   plus 208 outside paths through `done integrate`; aggregate tampering;
   undeclared or missing outside paths; and unchanged small v1 receipts. It
   also guards 1,024/1,025 files, 32 MiB/one byte over, timeout, oversized
   metadata, partial batch output, symlink, submodule, non-blob, and unsafe-path
   failures.
7. ADR-042 records the schema, static authority, whole-tree scope, self row,
   digest domain, and reviewed envelope. Fiat's current row is exactly
   `fiat-v5.31.1`, retains frontier revision `state-shape-validation` and its
   digest, cites issue #710, and leaves issue #363 as the held frontier.
8. Fiat `SKILL.md` exposes version `5.31.1` and the v2 promise without rewriting
   its v1 history. Hexaemeron version `1.6.6` agrees across both plugin
   manifests, both marketplaces, and the propagation test. The current-version
   assertions in the beginner-primer builder, test, and study agree with those
   two new values.
9. Promise Machine digest pins match the canonical controller; the portable
   runtime is regenerated from `scripts/portable_promise_machine.py`; its
   manifest and all generated copies pass `check`; Horos describes the final
   tracked tree; every applicable lint and both suites pass; and
   `git diff --check` exits 0.

**Files.** Create
`docs/decisions/ADR-042-bind-sync-run-generator-aggregates.md`,
`plugins/hexaemeron/tests/test_hexctl_generator_aggregates.py`, and
`plugins/hexaemeron/tests/fixtures/fiat-710-generator-aggregate.json`. Change
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/skills/fiat/SKILL.md`,
`plugins/hexaemeron/skills/fiat/EVOLUTION.md`,
`tests/promise_machine_coverage.json`, `tests/test_evolution_contract.py`,
`tests/test_version_propagation.py`, `.claude-plugin/marketplace.json`,
`.agents/plugins/marketplace.json`,
`plugins/hexaemeron/.claude-plugin/plugin.json`,
`plugins/hexaemeron/.codex-plugin/plugin.json`,
`scripts/build_child_or_golden_retriever_primer.py`,
`tests/test_child_or_golden_retriever_primer.py`, and only the current-version
sentence in `docs/a-child-or-a-golden-retriever-study.md`. Regenerate, never
hand-edit, `.agents/skills/promise-machine/runtime/` including its
`MANIFEST.json`. Permit the three `.horos` JSON files only when the deterministic
scan changes them and the configured audit record plus its generated
`.synopsis.md` companion only for Warden rounds. Any other file requires a
receipted runbook amendment before it is changed.

**Tests.** Add focused cases whose names identify the five issue acceptance
groups and the resource, framing, object, path, compatibility, and
mutation-order boundaries. Preserve a red result against the entry controller
for every behaviour that the new mechanism fixes. Then run:

```bash
python3 -m unittest discover -s plugins/hexaemeron/tests -p 'test_hexctl_generator_aggregates.py' -t plugins/hexaemeron
python3 scripts/portable_promise_machine.py sync
python3 scripts/portable_promise_machine.py check
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/fiat/SKILL.md plugins/hexaemeron/skills/fiat/EVOLUTION.md docs/decisions/ADR-042-bind-sync-run-generator-aggregates.md docs/a-child-or-a-golden-retriever-study.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py --mode report docs/decisions/ADR-042-bind-sync-run-generator-aggregates.md
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

The source-bound Elenchus runner contract for any audit repair is:

```text
test command: python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}
report format: unittest-json-v1
expected report schema: elenchus.unittest.v1
report file: .elenchus/fiat-710-step-2.json
```

The report path must be fresh. A missing, stale, empty, malformed, or
infrastructure-failed report is `inconclusive`, not evidence that a repair is
guarded.

**Disciplines.** phylax: the supplied v2 JSON, Git subprocess, batch protocol,
manifest, registry, and state write use the exact closures and ceilings in the
study; no shell, network, worktree-byte, dynamic import, or runtime-owner
boundary opens. ephoros: normalized status and receipt data answer which tree
was accepted and whether every path was accounted for; bounded diagnostics and
byte-identical refusal evidence answer why a transition stopped. metron: no
speed claim is made; file, byte, metadata, and time bounds are termination
guards and their boundary fixtures must pass. elenchus: the incident red,
one-field corruptions, resource edges, and state/ledger byte comparisons guard
the cause; audit repairs use the exact runner above. hypomnema: ADR-042 owns the
expensive schema and authority decisions, the controller owns executable
values once, the fixture owns incident facts, and generated copies own no
independent decision.

## Step 3: Demonstrate the checked incident transition

**Goal.** Publish a reproducible proof from the completed tree that the exact
issue-710 topology stays red under v1, becomes green only under the registered
v2 aggregate, reaches `done integrate`, and refuses every named corruption
without a partial receipt.

**Entry.** Step 2's signed, audited, prose-checked branch tip with canonical and
generated sources byte-current, all expected version identities present, and
the focused acceptance module green. Do not change controller behaviour,
schema, registry, ceilings, versions, fixtures, or tests in this step.

**Exit.** `docs/fiat-sync-run-generator-aggregates-proof.md` records commands
and checked outputs produced afresh from the step-2 tree: starting, product,
base, sync, and merge-base commit ids; fixture SHA-256; 53 product paths; 1,087
upstream paths; 887 runtime files; 1,095 required paths; 208 individual paths;
the exact v1 exit-2 diagnostic; the normalized v2 aggregate count, manifest
SHA-256, tree SHA-256, Git tree id, coverage ids, and successful integrate
receipt; one-field tamper and missing/undeclared outside-path refusals with
unchanged state and ledger digests; and unchanged normalized receipts for every
existing small v1 fixture. The document distinguishes reconstructed fixture
evidence from unavailable #622 operator bytes. The focused module, complete
Hexaemeron suite, root suite, portable-runtime check, Promise coverage,
version-propagation checks, audit-synopsis currency, all applicable lints,
Horos check, and `git diff --check` exit 0.

**Files.** Create only
`docs/fiat-sync-run-generator-aggregates-proof.md`. Permit the configured audit
record and its generated `.synopsis.md` companion only for append-only Warden
rounds, and the three `.horos` JSON files only if the deterministic scan
changes them. Test reports remain ignored and uncommitted. A proof mismatch is
repaired in the proof; a product mismatch stops the step and requires a
receipted runbook amendment before any step-2 file changes.

**Tests.** Generate the proof from fresh commands, never by copying the issue
claim, and run:

```bash
python3 -m unittest discover -s plugins/hexaemeron/tests -p 'test_hexctl_generator_aggregates.py' -t plugins/hexaemeron
python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report .elenchus/fiat-710-step-3.json
python3 -m unittest discover -s tests
python3 scripts/portable_promise_machine.py check
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-sync-run-generator-aggregates-proof.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py --mode report docs/fiat-sync-run-generator-aggregates-proof.md
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

The source-bound Elenchus runner contract for any audit repair is:

```text
test command: python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}
report format: unittest-json-v1
expected report schema: elenchus.unittest.v1
report file: .elenchus/fiat-710-step-3.json
```

The report path must be fresh. A missing, stale, empty, malformed, or
infrastructure-failed report is `inconclusive`, not evidence that a repair is
guarded.

**Disciplines.** phylax: no new capability opens; the proof invokes the
already-reviewed local commands against fixed Git objects and contains no
secret. ephoros: the proof makes the receipt, counts, aggregate identity,
coverage, and bounded refusals available to an operator without inventing a
telemetry backend. metron: no performance claim is made and only the step-2
termination bounds are reported. elenchus: the exact v1 red, v2 green,
corruption matrix, and byte-identical refusal checks are the demonstration;
repairs use the fresh report above. hypomnema: the proof is the durable home for
the final reproduction, while ADR-042 and the fixture remain the homes for the
decision and incident preimage.

### Amendment -- 2026-08-28

**What changed.** Complete replacement Exit: All of the following hold: (1) `docs/fiat-sync-run-generator-aggregates-study.md` is byte-identical to `.hexaemeron/study.md`; (2) `docs/fiat-sync-run-generator-aggregates-runbook.md` is byte-identical to `.hexaemeron/runbook.md`; (3) Protasis accepts the tracked study and runbook, Imprimatur accepts both, Brevitas accepts the tracked runbook, and the study is recorded as excluded under Brevitas's completeness-oriented specification boundary; (4) every relative link resolves from both tracked publication paths and Hypomnema reports no missing durable home; (5) a deterministic Horos scan describes the tracked tree; and (6) the root and Hexaemeron suites pass and `git diff --check` exits 0. Prove those claims with the complete replacement Tests commands below. Complete replacement Tests: No product test is added. Copy the two receipted artefacts without rewriting them, then run `cmp -s .hexaemeron/study.md docs/fiat-sync-run-generator-aggregates-study.md`, `cmp -s .hexaemeron/runbook.md docs/fiat-sync-run-generator-aggregates-runbook.md`, `python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/fiat-sync-run-generator-aggregates-study.md`, `python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/fiat-sync-run-generator-aggregates-runbook.md`, `python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-sync-run-generator-aggregates-study.md docs/fiat-sync-run-generator-aggregates-runbook.md`, `python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py --mode report docs/fiat-sync-run-generator-aggregates-runbook.md`, `python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs plugins`, `python3 plugins/horos/skills/horos/scripts/horos.py check .`, `python3 -m unittest discover -s tests`, `python3 plugins/hexaemeron/tests/run_tests.py`, and `git diff --check`. The source-bound Elenchus runner contract for any audit repair remains exact: test command `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`; report format `unittest-json-v1`; expected report schema `elenchus.unittest.v1`; report file `.elenchus/fiat-710-step-1.json`. The report path must be fresh. A missing, stale, empty, malformed, or infrastructure-failed report is `inconclusive`, not evidence that a repair is guarded.
**Why.** The byte-identical study is a completeness-oriented specification, which Brevitas expressly excludes, and its protected field structure produces eighteen B023 diagnostics. Rewriting either copy would break the receipted SHA-256 and the step's byte-identity exit. The runbook remains inside the explicit step contract and passes Brevitas report mode.
**Steps touched.** Step 1.
**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds.
### Amendment -- 2026-08-28

**What changed.** Complete replacement Goal: Commit byte-identical tracked copies of the receipted study and runbook, and publish ADR-042 as the standing record for the authority, evidence, resource, compatibility, and refusal decisions selected by that study. Complete replacement Exit: All of the following hold: (1) `docs/fiat-sync-run-generator-aggregates-study.md` is byte-identical to `.hexaemeron/study.md`; (2) `docs/fiat-sync-run-generator-aggregates-runbook.md` is byte-identical to `.hexaemeron/runbook.md`; (3) `docs/decisions/ADR-042-bind-sync-run-generator-aggregates.md` records the v2 schema, static-owner rule, whole-final-tree scope, manifest self row, digest domain, reviewed resource envelope, rejected general-cap and runtime-owner alternatives, and issue-710 consequence without claiming the step-2 implementation exists; (4) Protasis accepts the tracked study and runbook, Imprimatur accepts all three documents, Brevitas accepts the tracked runbook and ADR, and the study is recorded as excluded under Brevitas's completeness-oriented specification boundary; (5) every relative link resolves from both tracked publication paths and Hypomnema reports no missing durable home; (6) a deterministic Horos scan describes the tracked tree; and (7) the root and Hexaemeron suites pass and `git diff --check` exits 0. Prove those claims with the complete replacement Tests commands below. Complete replacement Files: Create or update only `docs/fiat-sync-run-generator-aggregates-study.md`, `docs/fiat-sync-run-generator-aggregates-runbook.md`, and `docs/decisions/ADR-042-bind-sync-run-generator-aggregates.md`. Permit `.horos/boundary.json`, `.horos/candidates.json`, and `.horos/census.json` only when the deterministic Horos write changes them. Permit the configured audit record and its generated `.synopsis.md` companion only for append-only Warden rounds. Do not change controller, test, manifest, version, dependency, or CI files in this step's implementation or audit fix. Complete replacement Tests: No product test is added. Copy the two receipted artefacts without rewriting them, add ADR-042 from the study's accepted decision, then run `cmp -s .hexaemeron/study.md docs/fiat-sync-run-generator-aggregates-study.md`, `cmp -s .hexaemeron/runbook.md docs/fiat-sync-run-generator-aggregates-runbook.md`, `python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/fiat-sync-run-generator-aggregates-study.md`, `python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/fiat-sync-run-generator-aggregates-runbook.md`, `python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-sync-run-generator-aggregates-study.md docs/fiat-sync-run-generator-aggregates-runbook.md docs/decisions/ADR-042-bind-sync-run-generator-aggregates.md`, `python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py --mode report docs/fiat-sync-run-generator-aggregates-runbook.md`, `python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py --mode report docs/decisions/ADR-042-bind-sync-run-generator-aggregates.md`, `python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs plugins`, `python3 plugins/horos/skills/horos/scripts/horos.py check .`, `python3 -m unittest discover -s tests`, `python3 plugins/hexaemeron/tests/run_tests.py`, and `git diff --check`. The source-bound Elenchus runner contract for any audit repair remains exact: test command `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`; report format `unittest-json-v1`; expected report schema `elenchus.unittest.v1`; report file `.elenchus/fiat-710-step-1.json`. The report path must be fresh. A missing, stale, empty, malformed, or infrastructure-failed report is `inconclusive`, not evidence that a repair is guarded. Complete replacement Disciplines: phylax: none, because static Markdown opens no input or execution boundary. ephoros: none, because nothing new runs unattended. metron: none, because no performance claim is made. elenchus: byte identity, links, structure, standing-record placement, reading-boundary currency, and both suites stop the step; audit repairs use the exact runner above. hypomnema: ADR-042 is the standing decision record, while the tracked study and runbook preserve the accepted specification and build sequence.
**Why.** Warden finding S1-R1-01 established that publishing the study before its selected standing decision record conflicts with Hypomnema's placement contract. Moving ADR-042 into Step 1 closes that record gap.
**Steps touched.** Step 1.
**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds.

### Amendment -- 2026-08-28

**What changed.** Complete replacement Entry: Step 1's signed, audited, prose-checked branch tip with ADR-042 committed as the standing decision record. Re-read the live Fiat ledger, package manifests, ADR-042, and generated runtime before the first step-2 edit. Expected collision-free implementation identities are Fiat `5.31.1` and Hexaemeron `1.6.6`; ADR-042 must remain byte-identical to the step-1 record. If either version is no longer free or the ADR bytes have drifted, stop and amend this runbook rather than selecting another value or rewriting the decision silently. The entry controller must still reproduce `integration path delta exceeds 500 paths` for the 1,095-path v1 incident surface. Complete replacement Files: Create `plugins/hexaemeron/tests/test_hexctl_generator_aggregates.py` and `plugins/hexaemeron/tests/fixtures/fiat-710-generator-aggregate.json`. Change `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, `plugins/hexaemeron/skills/fiat/SKILL.md`, `plugins/hexaemeron/skills/fiat/EVOLUTION.md`, `tests/promise_machine_coverage.json`, `tests/test_evolution_contract.py`, `tests/test_version_propagation.py`, `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`, `plugins/hexaemeron/.claude-plugin/plugin.json`, `plugins/hexaemeron/.codex-plugin/plugin.json`, `scripts/build_child_or_golden_retriever_primer.py`, `tests/test_child_or_golden_retriever_primer.py`, and only the current-version sentence in `docs/a-child-or-a-golden-retriever-study.md`. Regenerate, never hand-edit, `.agents/skills/promise-machine/runtime/` including its `MANIFEST.json`. Read but do not change `docs/decisions/ADR-042-bind-sync-run-generator-aggregates.md`. Permit the three `.horos` JSON files only when the deterministic scan changes them and the configured audit record plus its generated `.synopsis.md` companion only for Warden rounds. Any other file requires a receipted runbook amendment before it is changed.
**Why.** ADR-042 now belongs to Step 1. Removing it from Step 2's creation scope prevents the implementation step from treating an owned path as free or rewriting the accepted decision.
**Steps touched.** Step 2.
**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds.

### Amendment -- 2026-08-28

**What changed.** Complete replacement Tests: Add focused cases whose names identify the five issue acceptance groups and the resource, framing, object, path, compatibility, and mutation-order boundaries. Preserve a red result against the entry controller for every behaviour that the new mechanism fixes. Then run `python3 -m unittest discover -s plugins/hexaemeron/tests -p 'test_hexctl_generator_aggregates.py'`, `python3 scripts/portable_promise_machine.py sync`, `python3 scripts/portable_promise_machine.py check`, `python3 plugins/hexaemeron/tests/run_tests.py`, `python3 -m unittest discover -s tests`, `python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/fiat/SKILL.md plugins/hexaemeron/skills/fiat/EVOLUTION.md docs/decisions/ADR-042-bind-sync-run-generator-aggregates.md docs/a-child-or-a-golden-retriever-study.md`, `python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py --mode report docs/decisions/ADR-042-bind-sync-run-generator-aggregates.md`, `python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests`, `python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests`, `python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs`, `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`, `python3 plugins/horos/skills/horos/scripts/horos.py check .`, and `git diff --check`. The source-bound Elenchus runner contract for any audit repair remains exact: test command `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`; report format `unittest-json-v1`; expected report schema `elenchus.unittest.v1`; report file `.elenchus/fiat-710-step-2.json`. The report path must be fresh. A missing, stale, empty, malformed, or infrastructure-failed report is `inconclusive`, not evidence that a repair is guarded.
**Why.** The prescribed focused discovery command used `-t plugins/hexaemeron`, but `plugins/hexaemeron/tests` is not an importable package and the pinned Python therefore exits with `ImportError: Start directory is not importable` before collecting a test. Removing only `-t plugins/hexaemeron` preserves the same start directory and filename pattern and runs all thirteen focused tests. Adding an otherwise unnecessary `__init__.py` would expand the step's file surface without improving the proof.
**Steps touched.** Step 2.
**Still holding.** Step 2: entry holds; exit holds. Step 3: entry holds; exit holds.

### Amendment -- 2026-08-28

**What changed.** Complete replacement Files: Create `plugins/hexaemeron/tests/test_hexctl_generator_aggregates.py` and `plugins/hexaemeron/tests/fixtures/fiat-710-generator-aggregate.json`. Change `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, `plugins/hexaemeron/skills/fiat/SKILL.md`, `plugins/hexaemeron/skills/fiat/EVOLUTION.md`, `plugins/hexaemeron/tests/test_issue_429_recovery.py`, `tests/promise_machine_coverage.json`, `tests/test_evolution_contract.py`, `tests/test_version_propagation.py`, `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`, `plugins/hexaemeron/.claude-plugin/plugin.json`, `plugins/hexaemeron/.codex-plugin/plugin.json`, `scripts/build_child_or_golden_retriever_primer.py`, `tests/test_child_or_golden_retriever_primer.py`, and only the current-version sentence in `docs/a-child-or-a-golden-retriever-study.md`. Regenerate, never hand-edit, `.agents/skills/promise-machine/runtime/` including its `MANIFEST.json`. Read but do not change `docs/decisions/ADR-042-bind-sync-run-generator-aggregates.md`. Permit the three `.horos` JSON files only when the deterministic scan changes them and the configured audit record plus its generated `.synopsis.md` companion only for Warden rounds. Any other file requires a receipted runbook amendment before it is changed.
**Why.** The complete Hexaemeron suite proved that `plugins/hexaemeron/tests/test_issue_429_recovery.py` independently pins the integrated canonical controller digest. Canonical source, the generated copy, and the six already-permitted Promise Machine coverage pins agree on the new digest, while this historical recovery constant still names the prior controller and is the suite's sole failure. Updating that one existing digest assertion is required to keep the recovery fixture bound to the current controller; no recovery behavior or fixture topology changes.
**Steps touched.** Step 2.
**Still holding.** Step 2: entry holds; exit holds. Step 3: entry holds; exit holds.

### Amendment -- 2026-08-28

**What changed.** Complete replacement Entry: Step 1's signed, audited, prose-checked branch tip, followed by the signed Step-2 implementation commit and the current study amendment. Re-read the live Fiat ledger, package manifests, `docs/decisions/ADR-043-bind-sync-run-generator-aggregates.md`, and generated runtime before the repair edit. `origin/main` at `4296f9f0b3eb03926d9b5b03258246dcab8c13ec` owns `docs/decisions/ADR-042-advance-the-python-suite-to-3-14.md`; ADR-043 is the next free default-branch identity. Expected implementation identities remain Fiat `5.31.1` and Hexaemeron `1.6.6`. The renamed ADR must preserve the accepted generator-aggregate decision while changing its number, path, title, and current references. The entry controller's exact `integration path delta exceeds 500 paths` refusal for the 1,095-path v1 incident remains the red baseline. Complete replacement Exit: All of the following hold: (1) `fiat-integration-revalidation/v1` follows its unchanged parser and 500-path route, while `fiat-integration-revalidation/v2` accepts only the exact top-level, aggregate, and check fields fixed by the study; (2) the source registry contains only `promise-machine-portable-runtime-v1`, with its exact prefix, generator, manifest contract, verification command, 1,024-file ceiling, and 32 MiB ceiling, and no artefact can create or widen an owner; (3) v2 classifies the complete bounded Git deltas before the individual cap, every path remains safe and unique, at most 500 outside paths are exact and individually covered, and selected prefixes are exact and non-overlapping; (4) one argv-only, deadline-bound Git object reader proves the final sync tree, manifest rows, modes, blob sizes, and SHA-256 values without reading the worktree, and the manifest self row, file count, domain-separated tree digest, and Git tree id are recomputed and retained in the normalized receipt; (5) wrong registry data, count, manifest digest, tree digest, membership, mode, object type, batch framing, resource bound, generator command, aggregate coverage, or outside-path coverage exits 2 before the exact state or ledger bytes change; (6) the focused controller module carries the issue-710 fixture and guards the v1 1,095-path refusal, the v2 887-file aggregate plus 208 outside paths through `done integrate`, aggregate tampering, undeclared or missing outside paths, unchanged small v1 receipts, 1,024/1,025 files, 32 MiB/one byte over, timeout, oversized metadata, partial batch output, symlink, submodule, non-blob, and unsafe-path failures; (7) `docs/decisions/ADR-043-bind-sync-run-generator-aggregates.md` records the schema, static authority, whole-tree scope, self row, digest domain, reviewed envelope, and renumbering cause, while no current product path claims the conflicting ADR-042 identity and the append-only Step-1 audit remains historical; (8) Fiat's current row is exactly `fiat-v5.31.1`, retains frontier revision `state-shape-validation` and its digest, cites issue #710, leaves issue #363 as the held frontier, and Fiat `SKILL.md`, Hexaemeron `1.6.6`, both plugin manifests, both marketplaces, the propagation test, primer builder, primer test, and current-version study sentence agree; and (9) Promise Machine digest pins match the canonical controller, the portable runtime is regenerated from `scripts/portable_promise_machine.py`, canonical and generated copies match, the tracked study and runbook match their amended controller artefacts, ADR numbering is unique against current `origin/main`, Horos describes the final tracked tree, every applicable lint and both suites pass, and `git diff --check` exits 0. Complete replacement Files: Rename `docs/decisions/ADR-042-bind-sync-run-generator-aggregates.md` to `docs/decisions/ADR-043-bind-sync-run-generator-aggregates.md`. Change `docs/fiat-sync-run-generator-aggregates-study.md`, `docs/fiat-sync-run-generator-aggregates-runbook.md`, `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, `plugins/hexaemeron/skills/fiat/SKILL.md`, `plugins/hexaemeron/skills/fiat/EVOLUTION.md`, `plugins/hexaemeron/tests/test_issue_429_recovery.py`, `plugins/hexaemeron/tests/test_hexctl_generator_aggregates.py`, `tests/promise_machine_coverage.json`, `tests/test_evolution_contract.py`, `tests/test_version_propagation.py`, `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`, `plugins/hexaemeron/.claude-plugin/plugin.json`, `plugins/hexaemeron/.codex-plugin/plugin.json`, `scripts/build_child_or_golden_retriever_primer.py`, `tests/test_child_or_golden_retriever_primer.py`, and only the current-version sentence in `docs/a-child-or-a-golden-retriever-study.md`. Retain the created `plugins/hexaemeron/tests/fixtures/fiat-710-generator-aggregate.json`. Regenerate, never hand-edit, `.agents/skills/promise-machine/runtime/` including its `MANIFEST.json`. Permit `.horos/boundary.json`, `.horos/candidates.json`, and `.horos/census.json` only when the deterministic scan changes them. Leave the configured append-only audit record and generated synopsis unchanged during implementation; they may change only in later Warden rounds. Any other file requires a receipted runbook amendment before it is changed. Complete replacement Tests: Preserve the entry-controller red result for every behavior the new mechanism fixes. Run `cmp -s .hexaemeron/study.md docs/fiat-sync-run-generator-aggregates-study.md`, `cmp -s .hexaemeron/runbook.md docs/fiat-sync-run-generator-aggregates-runbook.md`, `python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/fiat-sync-run-generator-aggregates-study.md`, `python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/fiat-sync-run-generator-aggregates-runbook.md`, `python3 -m unittest discover -s plugins/hexaemeron/tests -p 'test_hexctl_generator_aggregates.py'`, `python3 scripts/portable_promise_machine.py sync`, `python3 scripts/portable_promise_machine.py check`, `python3 plugins/hexaemeron/tests/run_tests.py`, `python3 -m unittest discover -s tests`, `python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/fiat/SKILL.md plugins/hexaemeron/skills/fiat/EVOLUTION.md docs/decisions/ADR-043-bind-sync-run-generator-aggregates.md docs/fiat-sync-run-generator-aggregates-study.md docs/fiat-sync-run-generator-aggregates-runbook.md docs/a-child-or-a-golden-retriever-study.md`, `python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py --mode report docs/decisions/ADR-043-bind-sync-run-generator-aggregates.md`, `python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py --mode report docs/fiat-sync-run-generator-aggregates-runbook.md`, `python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests`, `python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests`, `python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs`, `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`, `python3 plugins/horos/skills/horos/scripts/horos.py check .`, and `git diff --check`. The source-bound Elenchus runner contract for any audit repair remains exact: test command `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`; report format `unittest-json-v1`; expected report schema `elenchus.unittest.v1`; report file `.elenchus/fiat-710-step-2.json`. The report path must be fresh. A missing, stale, empty, malformed, or infrastructure-failed report is `inconclusive`, not evidence that a repair is guarded. Complete replacement Disciplines: phylax: the supplied v2 JSON, Git subprocess, batch protocol, manifest, registry, and state write use the exact closures and ceilings in the study; no shell, network, worktree-byte, dynamic import, or runtime-owner boundary opens. ephoros: normalized status and receipt data answer which tree was accepted and whether every path was accounted for; bounded diagnostics and byte-identical refusal evidence answer why a transition stopped. metron: no speed claim is made; file, byte, metadata, and time bounds are termination guards and their boundary fixtures must pass. elenchus: the incident red, one-field corruptions, resource edges, state/ledger byte comparisons, and live ADR-number collision guard the cause; audit repairs use the exact runner above. hypomnema: ADR-043 owns the expensive schema and authority decisions plus the renumbering cause, the controller owns executable values once, the fixture owns incident facts, generated copies own no independent decision, and the append-only audit preserves the earlier ADR-042 finding as historical evidence.
**Why.** Pull request #718 assigned ADR-042 on `main` after Step 1 passed and while Step 2 was under final verification. The live root suite correctly refused the resulting number collision. The current study amendment selects ADR-043 as the next free identity without changing the accepted design; this complete Step-2 repair moves the standing record and every current product reference while preserving the signed Step-1 and append-only audit history.
**Steps touched.** Step 2.
**Still holding.** Step 2: entry holds; exit holds. Step 3: entry holds; exit holds.

### Amendment -- 2026-08-28

**What changed.** Complete replacement Exit: `docs/fiat-sync-run-generator-aggregates-proof.md` records commands and checked outputs produced afresh from the Step-2 tree: starting, product, base, sync, and merge-base commit ids; fixture SHA-256; 53 product paths; 1,087 upstream paths; 887 runtime files; 1,095 required paths; 208 individual paths; the exact v1 exit-2 diagnostic; the normalized v2 aggregate count, manifest SHA-256, tree SHA-256, Git tree id, coverage ids, and successful integrate receipt; one-field tamper and missing or undeclared outside-path refusals with unchanged state and ledger digests; and unchanged normalized receipts for every existing small v1 fixture. The document distinguishes reconstructed fixture evidence from unavailable #622 operator bytes. `docs/fiat-sync-run-generator-aggregates-runbook.md` is byte-identical to the amended `.hexaemeron/runbook.md`. The focused module, complete Hexaemeron suite, root suite, portable-runtime check, Promise coverage, version-propagation checks, audit-synopsis currency, Protasis check, every applicable lint, Horos check, and `git diff --check` exit 0. Complete replacement Files: Create `docs/fiat-sync-run-generator-aggregates-proof.md`. Change only `docs/fiat-sync-run-generator-aggregates-runbook.md`, and only by copying the amended `.hexaemeron/runbook.md` byte for byte. Permit the configured audit record and its generated `.synopsis.md` companion only for append-only Warden rounds, and `.horos/boundary.json`, `.horos/candidates.json`, and `.horos/census.json` only if the deterministic scan changes them. Test reports remain ignored and uncommitted. Do not change controller behavior, schema, registry, ceilings, versions, fixtures, or tests. A proof mismatch is repaired in the proof; a product mismatch stops the step and requires another receipted runbook amendment before any Step-2 file changes. Complete replacement Tests: Generate the proof from fresh commands, never by copying the issue claim, copy the amended runbook without rewriting it, and run `cmp -s .hexaemeron/runbook.md docs/fiat-sync-run-generator-aggregates-runbook.md`, `python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/fiat-sync-run-generator-aggregates-runbook.md`, `python3 -m unittest discover -s plugins/hexaemeron/tests -p 'test_hexctl_generator_aggregates.py'`, `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report .elenchus/fiat-710-step-3.json`, `python3 -m unittest discover -s tests`, `python3 scripts/portable_promise_machine.py check`, `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`, `python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-sync-run-generator-aggregates-proof.md docs/fiat-sync-run-generator-aggregates-runbook.md`, `python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py --mode report docs/fiat-sync-run-generator-aggregates-proof.md`, `python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py --mode report docs/fiat-sync-run-generator-aggregates-runbook.md`, `python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests`, `python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests`, `python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs`, `python3 plugins/horos/skills/horos/scripts/horos.py check .`, and `git diff --check`. The source-bound Elenchus runner contract for any audit repair remains exact: test command `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`; report format `unittest-json-v1`; expected report schema `elenchus.unittest.v1`; report file `.elenchus/fiat-710-step-3.json`. The report path must be fresh. A missing, stale, empty, malformed, or infrastructure-failed report is `inconclusive`, not evidence that a repair is guarded. Complete replacement Disciplines: phylax: no new capability opens; the proof invokes the already-reviewed local commands against fixed Git objects and contains no secret. ephoros: the proof makes the receipt, counts, aggregate identity, coverage, and bounded refusals available to an operator without inventing a telemetry backend. metron: no performance claim is made and only the Step-2 termination bounds are reported. elenchus: the exact v1 red, v2 green, corruption matrix, and byte-identical refusal checks are the demonstration; repairs use the fresh report above. hypomnema: the proof is the durable home for the final reproduction, ADR-043 and the fixture remain the homes for the decision and incident preimage, and the tracked runbook preserves this amendment byte for byte.
**Why.** The Step-3 baseline retained the import-root flag already proved invalid during Step 2, still named the superseded ADR-042, and did not permit the tracked runbook to follow a controller amendment. Correcting those three instructions before implementation keeps the proof command executable, preserves the live ADR identity, and prevents the canonical and tracked runbooks from drifting.
**Steps touched.** Step 3.
**Still holding.** Step 3: entry holds; exit holds.

### Amendment -- 2026-08-28

**What changed.** Complete replacement Exit: The final integration commit is a signed two-parent merge of exact product head `e05ab974dddd558480d76422c5c21f9b843fc0fe` and exact `origin/main` `44ad3740158b6c46646e8c7a8c93f17110bd7259`, in that first-parent order; `docs/decisions/ADR-043-bind-sync-run-generator-aggregates.md` has moved to `docs/decisions/ADR-044-bind-sync-run-generator-aggregates.md`; the decision title, Fiat evolution evidence, evolution test, and proof link name ADR-044; the append-only audit retains its historical ADR-043 wording; the portable runtime and Horos boundary describe the combined tree; and `fiat-integration-revalidation/v2` admits the signed merge only with the registered portable-runtime aggregate, exact outside paths, and green covering checks.
**Why.** The advanced base owns `docs/decisions/ADR-043-record-corpus-provenance-beside-the-chunks.md`. The root suite refuses that collision, while the local Fiat drafts' CPython 3.13.15 references are ignored controller evidence rather than committed-tree defects. A clean worktree at the signed sync commit must pass the root suite under the base's pinned CPython 3.14.6.
**Steps touched.** Final integration composition only.
**Still holding.** Steps 1 through 3 retain their exact signed implementation, audit, prose, and push evidence. The sync adds composition evidence; it does not reopen or rewrite the product run.
