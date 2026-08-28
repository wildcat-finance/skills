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
