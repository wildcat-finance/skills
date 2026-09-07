# Runbook: emitter-fidelity differential suite

Derived from `.hexaemeron/study.md`. The selected design is the one the record
below locks; no step reopens that choice.

```design-lock
schema | protasis-design-evidence/v1
sha256 | 4ec55f9ff970320a4009ecebfbc057d8985ba863c39d869b365aca1e41ec05ce
candidate | skills-harness
```

### Source receipts

```text
starting ref: e7d0fdea1a636e06725fc55a55d02c24f74a64ee
run branch: fiat/1354-fizz-4-emitter-fidelity-differential-suite
task issue: https://github.com/wildcat-finance/skills/issues/1354
protocol ref: f5a26146987926f4811b72a795d662813dedfe85
```

The topic is one capability in four dependency-ordered steps, so there is no
module table. Step 1 puts the accepted proposition and its decision draft in the
tree. Step 2 vendors the pinned protocol closure and stands the Foundry root up
so that it builds. Step 3 builds the mirror-emit reference, the comparison and
all 27 emitter cases. Step 4 runs the campaign and records it. No step appends a
version row and no `version-relations` block is declared, because Fizz keeps no
frontier ledger and no Hexaemeron plugin-level ledger exists in the tracked
tree; the issue's held-job label does not authorise an increment.

Three commands matter at every step. The harness commands are:

```bash
forge build
forge test
```

each run with `plugins/hexaemeron/harness` as the working directory. They are
meaningful from step 2 onward and both must exit 0 at every exit that names
them. The repository-wide command is:

```bash
python3 scripts/run_checks.py
```

run from the repository root, and it must exit 0 at every step's exit. It is the
root suite the repository actually gates on, and a green lint is not a
substitute for it.

`forge build` is usable here and that is a change from the protocol tree. On the
whole protocol tree it exits 1 with `Error: Lint failed` and this Foundry
release offers no flag to skip the lint. On the vendored closure alone it exits
0 with 32 warning-level `unsafe-typecast` lints, all in
`src/libraries/SafeCastLib.sol`, and zero error-level lints. The denial comes
from a file outside the closure.

The committed Horos boundary and census describe a tracked universe and byte
counts, so every step that adds or edits a tracked file regenerates both with

```bash
python3 plugins/horos/skills/horos/scripts/horos.py scan . --write
python3 plugins/horos/skills/horos/scripts/horos.py scan . --census --write
```

as its last action before committing, and requires

```bash
python3 plugins/horos/skills/horos/scripts/horos.py check .
```

to report that the boundary matches the tree.

The source-bound Elenchus runner contract for steps 2, 3 and 4 uses the harness
suite, because that is where each of those steps' evidence is. The test command
is `sh -c "cd plugins/hexaemeron/harness && forge test --junit > {report}"`, the
report format is `forge-junit-v1`, and the report file is
`.hexaemeron/test-reports/step-<n>.json`. Step 1 has no Solidity, so its runner
uses the repository's own suite instead: the test command is
`sh -c "python3 -m unittest discover -s plugins/hexaemeron/tests -t plugins/hexaemeron > {report} 2>&1"`,
the report format is `unittest-text-v1`, and the report file is
`.hexaemeron/test-reports/step-1.json`. A missing, stale, empty or malformed
report is `inconclusive` at every step, never evidence that a repair is guarded.

## Step 1: Publish the accepted specification

**Goal.** Commit the receipted study and runbook as tracked documents, and the
decision draft the design record's four expensive choices earn, so the
proposition is readable before any Solidity exists.

**Entry.** The run branch at starting ref `e7d0fdea`, working tree clean, no
tracked file from this run present. `docs/` holds twelve paired
`<slug>-study.md` and `<slug>-runbook.md` files and no index. `docs/decisions/`
holds numbered records named `ADR-NNN-<slug>.md` and unnumbered drafts named
`draft-<slug>.md`.

**Exit.** All of the following hold on the committed head:

1. `docs/emitter-fidelity-differential-suite-study.md` is byte-identical to the
   receipted `.hexaemeron/study.md` and
   `docs/emitter-fidelity-differential-suite-runbook.md` is byte-identical to
   the receipted `.hexaemeron/runbook.md`, each proved by `cmp -s` exiting 0.
2. `docs/decisions/draft-deliver-the-emitter-fidelity-suite-as-a-first-party-harness.md`
   exists, carries status, context, decision, the three rejected candidates with
   the gate each failed, and consequences, and states the mirror-emit oracle,
   the vendored-closure re-pinning duty and the absence of a version increment
   as sections of that one record. It is unnumbered at this step and cited
   elsewhere by its stable slug.
3. `python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/emitter-fidelity-differential-suite-study.md`
   and
   `python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/emitter-fidelity-differential-suite-runbook.md`
   exit 0.
4. `python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py`,
   `python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py` and
   `python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py` each
   report no defect over the three new documents at their committed paths.
5. The Horos boundary and census are regenerated and
   `python3 plugins/horos/skills/horos/scripts/horos.py check .` reports that
   the boundary matches the tree.
6. `python3 scripts/run_checks.py` exits 0 and `git diff --check` exits 0.

**Files.** Create the two documents under `docs/` and the one draft under
`docs/decisions/`. Rewrite `.horos/boundary.json` and `.horos/census.json` only
through the Horos scanner. No Solidity, no workflow, no configuration, no
dependency.

**Tests.** None written. The two receipted artefacts are copied without
rewriting a byte. The step-1 runner contract above applies to any repair.

**Disciplines.** phylax: none, the step adds static Markdown and opens no input
or execution boundary. ephoros: none, nothing here runs unattended. metron:
none, no performance claim is made. elenchus: a byte-identity, lint or root
suite regression stops the step and any repair uses the runner above.
hypomnema: the paired documents under `docs/` and the draft under
`docs/decisions/` are the durable homes this repository already uses, and the
draft's number is picked against the default branch at integration rather than
now.

## Step 2: Vendor the pinned closure and stand up the harness

**Goal.** Put the eleven pinned protocol source files into a first-party Foundry
root that builds with no dependency to fetch, with their provenance recorded and
checked, and wire that root into the repository's own check map and workflows.

**Entry.** Step 1 committed and green. No path under
`plugins/hexaemeron/harness/` exists.

**Exit.** All of the following hold on the committed head:

1. `plugins/hexaemeron/harness/foundry.toml` exists, copies the Janus profile
   with `libs = []`, `bytecode_hash = "none"`, the optimizer on at 200 runs, and
   declares neither `ffi` nor any `fs_permissions` entry beyond `out`.
2. Eleven files exist under `plugins/hexaemeron/harness/src/vendor/`, each
   byte-identical to its counterpart at protocol ref `f5a26146`, together
   46,799 bytes, and `grep -rn 'import' ` over them resolves every import inside
   that directory with no remapping.
3. `plugins/hexaemeron/harness/src/vendor/PROVENANCE.json` records the protocol
   repository, the ref, and each file's path and SHA-256, and a test asserts
   every recorded digest against the file on disk so drift fails rather than
   re-baselining.
4. `tests/check-map-v1.json` gains exactly two checks,
   `hexaemeron-forge-build` and `hexaemeron-forge-test`, each with
   `"cwd": "plugins/hexaemeron/harness"` and
   `"requires_executable": "forge"`, ordered in one group, and both added to the
   `hexaemeron` scope. Nothing else in that file changes.
5. `.github/workflows/hexaemeron-forge.yml` exists, triggers on the harness path
   and on itself, and runs `forge build` then `forge test` in that working
   directory.
6. `forge build` exits 0 from `plugins/hexaemeron/harness`, and `forge test`
   exits 0 there with the provenance test passing and no other test present.
7. `python3 scripts/run_checks.py` exits 0, plans both new checks, and refuses
   no path in the diff for want of an owner. The Horos boundary and census are
   regenerated and `horos.py check .` reports a match.

**Files.** Create `plugins/hexaemeron/harness/foundry.toml`, the eleven files
under `src/vendor/`, `src/vendor/PROVENANCE.json`, the provenance test under
`test/`, and `.github/workflows/hexaemeron-forge.yml`. Change
`tests/check-map-v1.json` only to add the two checks, the group and the scope
entries. Nothing under `plugins/hexaemeron/skills/fizz/`, `x-ray/` or
`solidity-auditor/` is written, and nothing is written into the protocol
repository.

**Tests.** One Solidity test asserting every `PROVENANCE.json` digest against
the vendored file, so a silent re-pin fails.

**Disciplines.** phylax: the harness reads only its own tree, declares no `ffi`
and no filesystem permission beyond `out`, and the step asserts that from the
committed `foundry.toml`. ephoros: the new workflow runs unattended on every
pull request touching the harness, and its failure surface is the two forge
commands with no retry and no continue-on-error. metron: none, no performance
claim is made; the 522 ms cold build in the study is a design measurement, not a
budget. elenchus: a build failure, a provenance mismatch or a check-map planning
refusal stops the step and any repair uses the runner contract above. hypomnema:
the re-pinning duty and the protocol ref live in the step-1 draft, and
`PROVENANCE.json` is the executable half of that record.

## Step 3: Build the mirror-emit reference and all 27 differential cases

**Goal.** Produce two logs for every emitter, one from the assembly and one from
the compiler, compare them field by field, and prove the comparison can fail.

**Entry.** Step 2 committed and green; `forge build` exits 0 in the harness.

**Exit.** All of the following hold on the committed head:

1. A reference contract under `plugins/hexaemeron/harness/src/` declares no
   event of its own, imports `IMarketEventsAndErrors` and `SphereXConfig` from
   `src/vendor/`, and emits each of the 27 events through high-level `emit`.
2. An external wrapper under the same root calls each of the 27 assembly
   emitters, because a free function that emits must be invoked externally for a
   recorded log to be attributable.
3. A comparison helper reports topic0, the topic count, each indexed topic and
   the data region as separate assertions, compares the topic array on length
   before element, and compares the data region on length before content, with
   no hard-coded topic ceiling.
4. The harness suite holds 27 fuzz cases, one per emitter, each recording
   exactly two `Vm.Log` entries in one `vm.recordLogs` window and pairing them by
   position rather than by topic0. Each case bounds its domain by the emitter's
   own parameter types, and the one case where the emitter's `uint32 expiry`
   narrows the declared `uint256 expiry` states that widening explicitly.
5. Two deliberate wrong-answer specimens are committed, one with a wrong topic0
   and one with wrong data bytes, and the suite asserts that the comparison
   rejects both, so the comparison is proved able to fail.
6. A test asserts that the count of `emit_` free functions in the two vendored
   emitter files equals the count of cases, so a new emitter with no case fails
   the suite rather than being skipped.
7. Two memory tests hold: the free memory pointer at `0x40` is unchanged across
   every emitter call, and a dirtied scratch space at `0x00` to `0x5f` before a
   call does not change the recorded data.
8. `forge build` and `forge test` both exit 0 in the harness,
   `python3 scripts/run_checks.py` exits 0, `git diff --check` exits 0, and the
   Horos boundary and census match the tree.

**Files.** Create the reference, the wrapper, the comparison helper, the case
suite and the two specimens under `plugins/hexaemeron/harness/`. Change no file
under `src/vendor/`, no check-map entry and no workflow. Change nothing in the
protocol repository.

**Tests.** The 27 differential cases, the two rejection specimens, the pairing
count test, and the two memory tests. Every expectation is derived from a
declaration; no expected topic, arity or data offset is read from or transcribed
out of the two emitter files.

**Disciplines.** phylax: the suite issues no `vm.ffi`, `vm.readFile` or
`vm.writeFile` call, checkable by grep over the harness tree. ephoros: the
workflow added in step 2 now carries real cases, and its failure surface is
still the two forge commands. metron: none, and no gas claim is made, because
Hermes owns gas. elenchus: a failing case, a passing specimen or a pairing-count
mismatch stops the step and any repair uses the runner contract above.
hypomnema: the oracle construction is already recorded in the step-1 draft and
this step adds no new decision.

## Step 4: Run the campaign and record it

**Goal.** Run the fuzz campaign at a recorded seed and run length, record what
actually ran, and state what a green campaign does and does not establish.

**Entry.** Step 3 committed and green; the harness suite passes at its default
run count.

**Exit.** All of the following hold on the committed head:

1. `plugins/hexaemeron/harness/fizz_data/PROPERTIES.md` states each property
   with a stable spec identifier and a `SHOULD-HOLD` or `EXPLORATORY` guarantee
   tag, covering topic0, topic count, indexed topics, data bytes, the free
   pointer and scratch space.
2. `plugins/hexaemeron/harness/fizz_data/campaign.json` records the engine, the
   `--fuzz-seed` used, the run length, this repository's commit, the protocol
   ref `f5a26146`, the emitter count and the counterexample count. Every value
   is read back from the run that produced it.
3. A test re-reads `campaign.json` and asserts its emitter count against the
   suite's own pairing count, so a hand-written record disagrees with the tree.
4. `forge test --fuzz-seed <the recorded seed>` exits 0 from the harness at the
   recorded run length, and the command and its output are quoted in the step's
   record.
5. Zero counterexamples, or each counterexample committed as a deterministic
   replay test that fails without its fix and is named in `campaign.json`. An
   unresolved divergence prevents the fidelity claim and stops the step.
6. `python3 scripts/run_checks.py` exits 0, `git diff --check` exits 0, and the
   Horos boundary and census match the tree.
7. The pull request body states that no skill version is incremented, and names
   the design record digest, the protocol ref, the seed and the run length.

**Files.** Create `fizz_data/PROPERTIES.md`, `fizz_data/campaign.json` and the
readback test under `plugins/hexaemeron/harness/`. Add a replay test per
counterexample if any exists. Change no vendored file.

**Tests.** The campaign readback test, and one replay test per counterexample.

**Disciplines.** phylax: none beyond step 3's, and the campaign writes only
inside the harness tree. ephoros: the campaign record is the artefact an
operator reads to know what ran, and it names the seed so the run is
reproducible. metron: the run length and seed are recorded, and no timing claim
is made from them. elenchus: an unresolved divergence stops the step, and a
counterexample becomes a deterministic replay test rather than a log line.
hypomnema: the absence of a version increment is recorded here and in the pull
request body rather than in a decision record, because a record of an absence
would read as a policy nobody made.
