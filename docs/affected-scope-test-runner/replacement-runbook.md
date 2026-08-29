# Runbook: reconstruct and complete the affected-scope parallel test runner

Source: `.hexaemeron/study.md`, receipted at SHA-256
`536140f92ee144a298329c757985302691e50ba76bd7fb4924f081e4b30ff563`.

The replacement run starts at
`5489863196006d8e8b45799d74b56208cac65e4d` on
`fiat/622-carryover-inoculate-affected-scope-runner`. The published #622
comment, packet and patch are the only cumulative reconstruction source. The
archived attempt is evidence, not a base to merge, rebase, cherry-pick or
resume. Every step starts from the signed and audited step below it and leaves
a green, separately reviewable tree.

## Step 1: Reconstruct and verify the complete carryover union

**Goal.** Reconstruct all #621 and Step 2 mechanisms on current `main`, make
their completeness independently machine-checkable, resolve the one ADR
number collision, and present the complete fixed tree for a new independent
audit.

**Entry.** Starting commit
`5489863196006d8e8b45799d74b56208cac65e4d`, with the replacement study and
this runbook receipted, the tracked worktree clean, and these published inputs
available:

- issue comment
  `https://github.com/wildcat-finance/skills/issues/622#issuecomment-5423433742`;
- `622-CARRYOVER.md`, SHA-256
  `08048f48dfea9dc4bbdc08d08c40b182853c66a74d327e46bb776034c2f6e486`;
- `622-INOCULATION.patch`, SHA-256
  `108eb3a907c49e8ad99508526fd328e101f331ae343a2a9e63c5595e85541c6e`;
  and
- archive ref
  `archive/622-affected-scope-parallel-runner-attempt-1@f78f6b4c990c41629f4b77ceafe4977f016aeba1`,
  tree `7507f0e13b3c6f846adf9fe7d075a8ce0e7baa82`.

Before any product test, lint, reporter, acceptance command or audit round:

1. obtain independent run-local copies of both attachments and verify their
   published hashes;
2. verify the archive ref, tree, signed chain and packet inventory as
   provenance without checking out the archive as the worktree;
3. materialise all eighteen patch paths on the current-base tree;
4. move only logical
   `docs/decisions/ADR-035-select-and-schedule-repository-checks-from-one-graph.md`
   to physical
   `docs/decisions/ADR-045-select-and-schedule-repository-checks-from-one-graph.md`
   and rewrite every imported reference to that decision; and
5. create the artifact-anchored record and verifier below, then run that
   verifier as the first product command. Any other current-base conflict
   stops the step for a source-bound runbook amendment.

**Exit.** The exact packet and patch hashes, eighteen logical paths, eighteen
unique current targets, one ADR transform, twenty-three finding IDs, exact
owners, current guard sets and thirteen families agree across the published
sources, `tests/fixtures/issue-622-inoculation-v1.json`, the current AST and
the reconstructed files. The verifier rejects a substituted artifact,
missing or additional path, duplicate target, undeclared transform, missing
guard, unknown family, self-authorising record or partial tree. Its report
names the current base and every count without treating a count as future
configuration.

All reconstructed #621 fixtures disable signing only in each newly created
non-signature repository. The hostile inherited-signer guard leaves its
sentinel, outer checkout and global configuration unchanged; existing signed,
unsigned and invalid-signature cases retain their expectations. Contributors'
delivery identities and keys remain outside product behavior.

The reconstructed runner preserves fresh coordinator/worker discovery,
dynamic IDs, exact disjoint assignment and completion, stable bounded replay,
single-worker parity, drain-all behavior, secure report/cache paths,
balance-only timing data and every carried refusal. A focused parent-red guard
makes unexpected successes non-green. The descendant-output-descriptor lead
has an explicit bounded lifetime/drain rule and cause-level guard, or remains
a named blocker to a completed-runner claim. The valid one-test/two-subtest
consumer mismatch is linked to
[`elenchus-wish` #643](https://github.com/wildcat-finance/skills/issues/643);
#622 does not claim that external reader is repaired here.

The replacement study and runbook are committed under distinct replacement
filenames; the imported first-attempt copies remain immutable historical
evidence. These commands exit zero in this order after the bootstrap verifier:

```bash
python3 scripts/verify_issue_622_inoculation.py \
  --packet .hexaemeron/carryover/622-CARRYOVER.md \
  --patch .hexaemeron/carryover/622-INOCULATION.patch \
  --record tests/fixtures/issue-622-inoculation-v1.json \
  --root .
python3 plugins/hexaemeron/tests/test_issue_622_inoculation.py -v
python3 plugins/hexaemeron/tests/test_disposable_git_signing.py -v
python3 plugins/hexaemeron/tests/run_tests.py --jobs 1
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 plugins/hermes/skills/hermes/scripts/test_hermes.py
python3 -m unittest discover -s plugins/horos/tests -t plugins/horos
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins scripts tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins scripts tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs scripts
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py \
  docs/affected-scope-test-runner/replacement-study.md \
  docs/affected-scope-test-runner/replacement-runbook.md \
  docs/decisions/ADR-045-select-and-schedule-repository-checks-from-one-graph.md
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

Passing these commands establishes current reconstruction and product
evidence, not audit closure. The controller must receive a later Warden round
over the complete fixed tree with zero findings before this step can proceed
to prose or push.

**Files.** Preserve verified run-local inputs at
`.hexaemeron/carryover/622-CARRYOVER.md` and
`.hexaemeron/carryover/622-INOCULATION.patch`. Reconstruct the packet's full
eighteen-path manifest, with only its ADR source mapped to ADR-041. Add
`tests/fixtures/issue-622-inoculation-v1.json`,
`scripts/verify_issue_622_inoculation.py`, and
`plugins/hexaemeron/tests/test_issue_622_inoculation.py`. Add committed copies
`docs/affected-scope-test-runner/replacement-study.md` and
`docs/affected-scope-test-runner/replacement-runbook.md`. Update
`tests/promise_machine_coverage.json` only where the reconstructed runner's
exact digest changes while its reviewed public field map remains the same.
Refresh `.horos/boundary.json` only through the current Horos write command if
its deterministic classified tree changes. Touch no workflow, production
signature policy, plugin version, frontier or unrelated current-main path.

**Tests.** Before reconstruction, record only artifact, Git and path evidence;
do not run a product command. After all eighteen targets and the independent
record/verifier exist, run the verifier first and preserve its exact output.
Guard the verifier with bounded substituted-artifact, missing/extra path,
duplicate-target, bad-transform, missing-guard and self-authorisation cases.
Run every current carried guard on the reconstructed tree and retain the
packet's parent-red provenance without upgrading its historical Elenchus
wording. Add current parent-red evidence for the unexpected-success and
descendant-lifetime decisions. Fresh discovery supplies all counts. Elenchus
runner contract: `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`;
report format `unittest-json-v1`; report file `.elenchus/step-1.json`.

**Disciplines.** phylax: published artifacts, Git objects, JSON, AST names,
paths, subprocesses, reports and cleanup cross trust boundaries. ephoros: the
bootstrap and runner reports must bind source, map, assignment, failures and
capacity without forged or unbounded output. metron: historical timing is
context only; current serial and automatic runs establish the new baseline.
elenchus: every new acceptance defect needs current parent-red evidence and a
cause-level guard, while the 23 carried mechanisms retain their recorded
provenance. hypomnema: ADR-041, the machine record and distinct replacement
study/runbook copies preserve the decision, reconstruction and operating
contract.

## Step 2: Add the checked impact map and one global executor

**Goal.** Make declared scope plus every actual changed path select the full
applicable repository check graph, then execute independent work under one
shared quota-aware process budget.

**Entry.** Step 1's signed, reconstructed commit and zero-finding Warden
receipt, with the bootstrap verifier and all carried suites green.

**Exit.** `tests/check-map-v1.json` validates as
`wildcat.check-map.v1`. It declares total, non-overlapping ownership for
tracked and relevant untracked paths, fixed argv, working directories, named
consumers, dependency edges and ordered groups. `scripts/run_checks.py`
accepts repeated `--scope`, an optional base, `--full`, `--plan`, human or
versioned JSON output, a positive jobs override and a confined
repository-relative report path. Requested scope is always widened by the
actual committed, staged, unstaged and relevant untracked diff before
dependency closure. Every inclusion and widening has a reason.

Unknown or ambiguous ownership, stale commands, duplicate keys, unsafe paths,
cycles and invalid bases refuse before execution. One immutable attempt
snapshot contains the complete relevant working tree; one source movement
supersedes and retries the attempt, while repeated movement returns
`unstable-source` without reporting a test failure. One root scheduler owns
the process slots for commands, ordered groups and suite shards. A nested
runner receives only its allocation and cannot derive another independent
budget. All started work drains, output remains bounded, and the final
`wildcat.check-run.v1` report proves selection, assignment, execution and
failure class.

These commands exit zero and their JSON plans account for their exact selected
checks:

```bash
python3 scripts/run_checks.py --full --plan --format json
python3 scripts/run_checks.py --scope hexaemeron --plan --format json
python3 -m unittest discover -s plugins/hexaemeron/tests -p 'test_check_runner.py'
python3 plugins/hexaemeron/tests/run_tests.py
```

Bounded fixtures cover plugin-local, shared-contract, test-infrastructure,
Hexctl, Pandects, Janus, prose and unknown-path changes. The actual step diff
selects its complete self-audit before exit.

**Files.** Add `tests/check-map-v1.json`, `scripts/run_checks.py`,
`plugins/hexaemeron/tests/test_check_runner.py` and bounded fixtures below
`plugins/hexaemeron/tests/fixtures/check-runner/`. Modify `.gitignore` only if
the existing ignored runner-owned parent is insufficient. Clarify ADR-041
only with factual implementation evidence that does not change the accepted
decision. Update `tests/promise_machine_coverage.json` only when its governed
release-surface binding requires the exact implementation digest.

**Tests.** Cover the study's selection cases and refusals, requested-plus-diff
widening, rename/deletion and relevant untracked capture, deterministic graph
closure, fixed argv without a shell, ordered groups, one global live-child
high-water mark, nested allocation, bounded output, atomic report/cache
writes, single-change supersession, repeated-change `unstable-source`, owned
sentinel cleanup, exact-once aggregation and timing-only authority. Re-derive
the plan from the actual step diff. Elenchus runner contract:
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`;
report format `unittest-json-v1`; report file `.elenchus/step-2.json`.

**Disciplines.** phylax: the map parser, Git capture, snapshot, untracked-file
copy, subprocess queue, report/cache writers and cleanup each need bounded
hostile cases. ephoros: the plan and run reports bind source, reasons,
capacity, queue, shards, cache, supersession and distinct failure classes.
metron: planner/snapshot overhead and composed execution time are measured on
the same frozen workload; neutral complexity is removed. elenchus: unknown
ownership, graph, accounting, output and movement failures each retain a
parent-red regression. hypomnema: the versioned map and report schemas remain
consistent with ADR-041 and are documented beside their implementation.

## Step 3: Demonstrate, measure and document the complete runner

**Goal.** Prove the complete #621/#622 behavior on one frozen current tree,
publish the measured limits and make the checked runner the contributor
entrypoint without changing hosted CI.

**Entry.** Step 2's signed commit and zero-finding Warden receipt, with signing
isolation, cumulative inoculation, the checked graph and the global executor
green.

**Exit.** On one clean frozen revision, three alternating serial-control and
three automatic-policy Hexaemeron samples execute identical fresh manifests
and assertions. Each retains wall time, child CPU time, queue and live-child
high-water marks, available peak child memory, shard distribution and cache
state. The automatic policy is kept only when its median gain exceeds the sum
of the two median absolute deviations, no concurrency-only failure class
appears and observed resource growth stays within measured capacity; otherwise
the unproved scheduling policy is reverted without removing the correctness,
inoculation or selector work.

The hostile signer matrix and existing signature cases pass. A plan from the
replacement starting commit selects every actual changed surface. A full run
executes and accounts for every selected assertion under one global budget.
`AGENTS.md`, ADR-041, the replacement records and the benchmark agree with the
executable interfaces. Hosted workflows remain unchanged. The demonstration
commands are:

```bash
python3 plugins/hexaemeron/tests/run_tests.py --jobs 1
python3 plugins/hexaemeron/tests/run_tests.py
python3 scripts/run_checks.py \
  --base 5489863196006d8e8b45799d74b56208cac65e4d \
  --plan --format json
python3 scripts/run_checks.py --full
python3 scripts/verify_issue_622_inoculation.py \
  --packet .hexaemeron/carryover/622-CARRYOVER.md \
  --patch .hexaemeron/carryover/622-INOCULATION.patch \
  --record tests/fixtures/issue-622-inoculation-v1.json \
  --root .
python3 plugins/hexaemeron/tests/test_disposable_git_signing.py -v
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins scripts tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins scripts tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs scripts
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py \
  AGENTS.md \
  docs/affected-scope-test-runner/replacement-study.md \
  docs/affected-scope-test-runner/replacement-runbook.md \
  docs/affected-scope-test-runner/benchmark.md \
  docs/decisions/ADR-045-select-and-schedule-repository-checks-from-one-graph.md
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

The first two commands are alternated three times each rather than run once.
Passing the demonstration establishes the measured local result on that
revision; it does not claim unmeasured operating-system, quota or hosted-CI
portability. The controller still requires an independent zero-finding Warden
round over the final tree before prose, push or integration.

**Files.** Modify `AGENTS.md`; add
`docs/affected-scope-test-runner/benchmark.md`; clarify
`docs/decisions/ADR-045-select-and-schedule-repository-checks-from-one-graph.md`
and the committed replacement study/runbook copies only where the final
interfaces or measured evidence require factual updates. Modify an
implementation or test path only to repair a failure reproduced by the final
demonstration. Refresh `.horos/boundary.json` only through the governed Horos
write command if its deterministic classification changes. Do not change
hosted workflows.

**Tests.** Retain all six raw run summaries and the full-run report under
run-local evidence. Compare manifests by digest and membership, never to a
repository constant. Record the sample order, medians, deviations, keep-or-
revert verdict, source digest and resource gaps in the benchmark. Run every
Exit command on the final bytes. Elenchus runner contract:
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`;
report format `unittest-json-v1`; report file `.elenchus/step-3.json`.

**Disciplines.** phylax: inspect final artifact, plan, run, benchmark and
signature output for unsafe paths, unbounded data or signing material.
ephoros: verify every promised plan/run field from real output and retain no
secret or unbounded metric label. metron: the six same-source samples and
recorded spread decide whether automatic scheduling is kept. elenchus: stop
and work every final red result to cause before changing code or recording
green. hypomnema: `AGENTS.md`, ADR-041 and the benchmark are the established
homes for operation, decision and measured consequence.

### Amendment -- 2026-08-26

**What changed.** Complete replacement Exit: The exact packet and patch
hashes, eighteen logical paths, eighteen unique current targets, one ADR
transform, twenty-three finding IDs, exact owners, current guard sets and
thirteen families agree across the published sources,
`tests/fixtures/issue-622-inoculation-v1.json`, the current AST and the
reconstructed files. The verifier rejects a substituted artifact, missing or
additional path, duplicate target, undeclared transform, missing guard,
unknown family, self-authorising record or partial tree. Its report names the
current base and every count without treating a count as future
configuration.

All reconstructed #621 fixtures disable signing only in each newly created
non-signature repository. The hostile inherited-signer guard leaves its
sentinel, outer checkout and global configuration unchanged; existing signed,
unsigned and invalid-signature cases retain their expectations. Contributors'
delivery identities and keys remain outside product behavior.

The reconstructed runner preserves fresh coordinator/worker discovery,
dynamic IDs, stable bounded replay, single-worker parity, drain-all behavior,
secure report/cache paths, balance-only timing data and every carried refusal.
Every assigned ID receives exactly one disjoint terminal disposition: it is
started and completed exactly once, or it is `fixture-blocked` by a validated
class- or module-fixture `SkipTest` bound to that discovered test object and
the actual standard skip event. Assigned, started, completed and blocked IDs
remain separate in structured evidence, and a fixture-blocked ID is never
called started, completed or executed. A missing, duplicate, foreign,
overlapping or unproved disposition is a scheduler error. Public
`elenchus.unittest.v1` counters retain standard `unittest` meaning and schema.
A focused parent-red guard makes unexpected successes non-green. The
descendant-output-descriptor lead has an explicit bounded lifetime/drain rule
and cause-level guard, or remains a named blocker to a completed-runner claim.
The valid one-test/two-subtest consumer mismatch is linked to a separate
`elenchus-wish`; #622 does not claim that external reader is repaired here.

The replacement study and runbook are committed under distinct replacement
filenames; the imported first-attempt copies remain immutable historical
evidence. These commands exit zero in this order after the bootstrap verifier:

```bash
python3 scripts/verify_issue_622_inoculation.py \
  --packet .hexaemeron/carryover/622-CARRYOVER.md \
  --patch .hexaemeron/carryover/622-INOCULATION.patch \
  --record tests/fixtures/issue-622-inoculation-v1.json \
  --root .
python3 plugins/hexaemeron/tests/test_issue_622_inoculation.py -v
python3 plugins/hexaemeron/tests/test_disposable_git_signing.py -v
python3 plugins/hexaemeron/tests/run_tests.py --jobs 1
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 plugins/hermes/skills/hermes/scripts/test_hermes.py
python3 -m unittest discover -s plugins/horos/tests -t plugins/horos
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins scripts tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins scripts tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs scripts
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py \
  docs/affected-scope-test-runner/replacement-study.md \
  docs/affected-scope-test-runner/replacement-runbook.md \
  docs/decisions/ADR-045-select-and-schedule-repository-checks-from-one-graph.md
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

Passing these commands establishes current reconstruction and product
evidence, not audit closure. The controller must receive a later Warden round
over the complete fixed tree with zero findings before this step can proceed
to prose or push.

**Why.** The first reconstructed serial control discovered 1,348 assigned IDs
and recorded 1,343 starts and completions before returning scheduler-error.
The five-ID difference was the current-main `ReplayGuardExampleTests` class,
whose `setUpClass` raises `SkipTest` when all five optional Lazarus imports are
unavailable. Standard `unittest` records one class-fixture skip and does not
start those methods. The original Exit did not distinguish that valid
non-execution disposition from lost work.

**Steps touched.** Step 1.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds.
