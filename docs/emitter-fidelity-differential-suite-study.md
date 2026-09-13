# Emitter-fidelity differential suite

Assuming, unless corrected:

1. The deliverable lands in `wildcat-finance/skills`, on the run branch
   `fiat/1354-fizz-4-emitter-fidelity-differential-suite` cut from `main`. The
   code under study lives in `wildcat-finance/v2-protocol` and is read only.
2. The protocol source is pinned to `v2-protocol` `main` at
   `f5a26146987926f4811b72a795d662813dedfe85`. `git diff --stat v2.1.0 main` in
   that repository returns five files -- `.gitattributes`, three `.horos/`
   JSON files and `AGENTS.md` -- and no Solidity, so the pinned tree is
   Solidity-identical to the production tag.
3. `forge` 1.7.1 (commit `4072e48705af9d93e3c0f6e29e93b5e9a40caed8`) is the
   build and test command. No standalone `solc` binary is on this machine;
   `forge` resolves the pinned compiler itself.
4. The Python interpreter is the one in `.python-version`, 3.14.6.
5. The fuzz engine is Foundry's own stateless fuzzer with a recorded
   `--fuzz-seed`. The emitters are pure free functions holding no storage, so a
   stateful campaign under Echidna or Medusa would explore no state a stateless
   campaign does not.
6. The suite is developer- and CI-run, not a deployed service.
7. This is ordinary target delivery, not a frontier advance. Fizz keeps no
   ledger and no version may be incremented for it; see item 2.

I will proceed on these unless corrected.

## 1. Problem statement

Twenty-seven event emitters in `wildcat-finance/v2-protocol` build their logs by
hand in assembly rather than through the compiler's `emit`. Twenty-two are free
functions in `src/libraries/MarketEvents.sol`; five are free functions in
`src/spherex/SphereXProtectedEvents.sol`. Each one `mstore`s a data region and
calls `log1`, `log2` or `log3` with a hard-coded 32-byte topic0 constant --
fourteen `log1`, nine `log2`, four `log3`, no `log4`. There is no assembly
`log` opcode anywhere else in that repository's `src/`.

Anything that decodes a Wildcat market's history decodes against the Solidity
`event` declarations in `src/interfaces/IMarketEventsAndErrors.sol` and
`src/spherex/SphereXConfig.sol`. Nothing holds the assembly to those
declarations. The arity and indexed count of each event has so far been
established by reading the assembly, and a read is not a check. A divergence
that still decodes would corrupt every capture built on the declaration without
producing an error anywhere.

**Who this is for.** The engineer changing an emitter, the auditor asked whether
an event is topic-filterable on a given argument, the indexer author who decodes
against the declared ABI, and Hermes, which needs a standing executable
reference under its `CMP-10` rule.

**Where it lands, and why that is the study's central question.** The kickoff
issue says "a suite under `test/fizz/`". That path is a convention of the
protocol repository. This run's deliverable lands in `wildcat-finance/skills`,
because `hexctl init --task-issue` refuses a task issue that lives in a
different repository from the run's origin and filing a mirror issue in the
target is forbidden. Item 4 settles the home from measurement, not from the
issue's wording.

**What a working prototype means here.** A first-party Foundry root at
`plugins/hexaemeron/harness/` in this repository, carrying the pinned
v2-protocol emitter and declaration closure, a reference contract that emits
each declared event through high-level `emit`, and a differential suite in which
every one of the 27 emitters is fuzzed across its argument domain. For each case
five fields are compared and reported separately: topic0, the topic count,
indexed topic 1, indexed topic 2, and the data region. Five is derived from the
tree rather than chosen: the maximum indexed count across the 28 declarations is
2, so `3 + 2 = 5` comparable fields. A difference in any field fails the case
and is preserved as a specimen.

**The demo path.** From the repository root:

```
cd plugins/hexaemeron/harness && forge test --fuzz-seed <seed> -vv
```

exits zero, and `plugins/hexaemeron/harness/campaign/emitter-fidelity-campaign.json`
records the engine and its version, the seed, the runs per case, both source
commits and the emitter count.

**Success criteria, each checked by a command.**

1. `forge build` and `forge test` from `plugins/hexaemeron/harness/` both exit
   zero. Measured today on the vendored closure alone: `forge build` exits 0 in
   522 ms cold, with 32 warning-level `unsafe-typecast` lints and zero
   error-level lints.
2. `python3 scripts/run_checks.py --full` exits zero, having selected and run
   the two new declared checks. A changed path with no declared owner refuses
   the plan, so the check-map entry is not optional.
3. The suite asserts that the number of emitter cases it pairs equals the number
   of `emit_` free functions in the two vendored emitter files. A new emitter
   with no case makes the suite fail rather than pass quietly.
4. A tracked provenance check asserts the SHA-256 of each vendored file against
   the pinned protocol ref. Drift fails rather than silently re-baselining.
5. A committed specimen with a deliberately wrong topic0 and a second with
   deliberately wrong data bytes are both rejected by the comparison, proving
   the comparison can fail.
6. The campaign record exists and names engine, seed, run length and both
   commits.
7. Zero counterexamples, or each counterexample is a committed specimen test
   that fails without the fix.

## 2. Prior art

### In this repository

The measurement in `.hexaemeron/measure_design.py --facts` reads the tracked
tree and reports exactly four Foundry roots and exactly two of them compiled:

| Foundry root | built with forge | declared where |
| --- | --- | --- |
| `plugins/janus/harness` | yes | `.github/workflows/janus-forge.yml` |
| `plugins/pandects` | yes | `pandects-forge.yml` and `tests/check-map-v1.json` |
| `plugins/ariadne/tests/fixtures/forge-project/v1` | no | nowhere; `out/` is checked in |
| `plugins/ariadne/tests/fixtures/forge-project/v2` | no | nowhere; `out/` is checked in |

`plugins/janus/harness/` is the closest prior art and the shape this delivery
copies. It holds `foundry.toml` with `libs = []`, `solc = "0.8.25"`,
`evm_version = "cancun"` and no `ffi`, fifteen tracked `.sol` files under `src/`
and `test/`, and `.github/workflows/janus-forge.yml` runs `forge build` then
`forge test -vv` with `working-directory: plugins/janus/harness`. Its
`plugins/janus/scripts/run_forge_tests.py` runs `forge test --junit` with a
pinned argv, no shell and a cwd resolved from the file, and writes the report
only when forge exits zero and the output parses as XML. That launcher is the
Elenchus bridge this delivery reuses in shape.

`plugins/pandects/` is the second precedent and the only one wired into the root
runner. `tests/check-map-v1.json` declares `pandects-forge-build` and
`pandects-forge-test`, both with `argv` starting `forge`, `cwd:
plugins/pandects`, `requires_executable: forge`, ordered in the group
`pandects-forge` and attached to the `pandects` scope. Janus has a workflow but
no check-map entry, so a Janus Solidity break is invisible to
`scripts/run_checks.py`. This delivery takes the Pandects wiring as well as the
Janus layout, which is the one place it improves on both.

`plugins/ariadne/tests/fixtures/forge-project/v1/` and `v2/` each hold a real
`foundry.toml` and `src/Escrow.sol`, and both also ship compiler output --
`out/Escrow.sol/Escrow.json` and `out/build-info/*.json` -- checked into git.
Six Ariadne Python tests read that directory. Nothing compiles it. The fixture
pattern ships artifacts to be read, not a tree to be built, which is why the
`fixture-project` candidate in item 4 scores zero on the correctness gate.

`plugins/hexaemeron/skills/fizz/` is vendored. Its `NOTICE.md` records "vendored
verbatim from **Pashov Audit Group Skills**", upstream `https://github.com/pashov/skills`,
release tag `v28062026`, vendored 15 August 2026. It has 20 tracked `.sol` files
under `templates/`, none of them compiled by anything in this repository, and no
`foundry.toml` anywhere under `plugins/hexaemeron/`. It has a `VERSION` file
containing `1` and **no `EVOLUTION.md`**. The measurement finds three vendored
roots by their notices: `fizz`, `solidity-auditor` and `x-ray`.

Two first-party records govern what may be done there.
`plugins/hexaemeron/skills/VERSIONING.md` lines 9 to 11: "Vendored or
third-party skills are not governed and keep no ledger; inside Hexaemeron that
exempts the bundled Pashov suite (`fizz`, `x-ray`, `solidity-auditor`), which
remains covered by Hexaemeron's own plugin frontier."
`docs/decisions/ADR-005-vendor-the-pashov-suite-whole-and-ungoverned.md`, cited
by its stable slug `vendor-the-pashov-suite-whole-and-ungoverned`, accepted
2026-08-20, decides that the suite is "upstream-owned, byte-for-byte unmodified,
and ungoverned", and that "What the Wildcat suite accepts from a vendored
operation is stated outside the vendored bytes, in digest-bound overlay
declarations". Its consequence section says the loop's own conventions "stop at
the vendored boundary". `docs/decisions/ADR-003-bind-vendored-promises-with-digests.md`
records that binding: the declarations live in the single first-party file
`plugins/hexaemeron/PROMISES.md`.

That settles the frontier question the issue raises. Fizz keeps no ledger, there
is no plugin-level Hexaemeron frontier file in the tracked tree, and the only
Hexaemeron ledger relevant to the loop is
`plugins/hexaemeron/skills/fiat/EVOLUTION.md`, whose current frontier revision is
`state-shape-validation` and whose next job is skills#363 on delegation task
identities. Nothing here touches it. This delivery increments no version. The
sentence in `plugins/hexaemeron/skills/fizz/NOTICE.md` reading "The bundled
Solidity audit suite has not yet been exercised in a published end-to-end Fiat
delivery" sits inside a generated `marketplace-context` block, not a ledger, and
is not an authority for a version bump.

### The commits that last changed the subject

There is no merged pull request to read for this subject.
`gh api repos/wildcat-finance/skills/commits/<sha>/pulls` returns an empty list
for both commits below, so they landed as direct pushes to `main` and there is
no pull-request body carrying unfinished work forward. That is recorded rather
than glossed: the Protasis instruction to read the last two merged pull requests
has no object here, and the two commits are read instead.

`23110792`, 2026-08-28, "ci: detach plugin suites from unrelated changes", and
`1f2298b2`, 2026-08-27, "ci: give repo-wide invariants their own workflow and
gate forge to Solidity". Both touched `janus-forge.yml` and
`pandects-forge.yml`, and together they are why each Foundry root has a
path-filtered workflow of its own rather than a shared job. A new Foundry root
therefore owes a new path-filtered workflow, not an edit to an existing one.

The Fizz tree itself was last touched by `21263d0d`, 2026-08-17, and `48830c13`,
2026-08-17, both of which changed only `NOTICE.md` and `README.md` -- files the
notice names as first-party additions. The last change to a vendored byte was
`cd1dd5b6`, 2026-08-16, before the vendoring decision was accepted on 2026-08-20.
No upstream byte has moved since.

### Audit records

`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .` run
from the repository root exits zero, and every row reports `committed=match`, so
the verified synopses are the normal reading view for every in-scope source.
Three carried findings bear on this work.

`plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md`, step 0 round 2, leads not pursued:
"the vendored Pashov skills themselves were not exercised against this plugin --
they audit Solidity and the plugin is Python; their first real outing is the
first run with Solidity in it." This run is that outing. Carried forward as
content: the Solidity audit rounds apply here for the first time in the plugin's
own tree, and the risk register is written for a Solidity reviewer.

`audit/AUDIT_SYNOPSIS.md`, `S2-R1-05`, high: "A vendored instruction could author
its own Promise Machine contract while the structure check skipped it | fixed by
refusing contracts in vendored instructions and requiring a first-party overlay;
guarded". This is an executed check, not an opinion, and it is why the
`fizz-inline` candidate in item 4 is not merely disfavoured. Carried forward as
content: the delivery is first-party and sits outside the vendored roots.

`audit/rounds/fiat-329-janus-resolve-the-manifest-s-permitted-effec.synopsis.md`,
`S2-R2-01`, high: "the suite 168ec6d1 committed proved nothing under either
engine: neither Echidna 2.3.3 nor Medusa 1.5.1 implements keyExistsJson,
parseJsonUint or parseJsonString, so every generated manifest reverted with empty
return data before the reader resolved anything, resolveSuccesses stayed 0,
_check was never entered". Its sibling `S2-R2-07`, high, records nine properties
that stayed green while a resolver wrote `address(0xDEAD)` everywhere. Both are
the same failure: a suite that cannot fail. Carried forward as content in
success criteria 3 and 5 and as `comparison-cannot-fail` in the risk register.

`plugins/pandects/audit/AUDIT_SYNOPSIS.md`, `S2-R1-02`, medium: "The campaign
harnesses were written under `test/`. crytic-compile skips `test/` when it builds
a Foundry project, so Echidna could not see them at all". Carried forward as a
stated non-goal: this delivery runs under Foundry only, so the constraint does
not bind, and a later move to Echidna or Medusa would have to place harnesses
outside `test/`.

`plugins/pandects/audit/AUDIT_SYNOPSIS.md`, `S2-R1-01`, high, records a sound
reference that was not sound. Carried forward as `reference-is-not-authority` in
the risk register: the mirror-emit reference is trusted only because the compiler
derives it from the declaration, and the reference must import the declaring
interface rather than redeclare the events.

### In the protocol repository

`test/LogTest.sol` is not prior art and the name invites the mistake: it logs
natural-logarithm values through `console2.log`. `test/spherex/SphereXConfig.t.sol`
holds nine `vm.expectEmit` assertions over the five SphereX events with fixed
argument values and no fuzzing. `test/libraries/wrappers/` holds seven external
wrappers, and `TESTS.md` there records why: `expectEmit` and `expectRevert` act
on the next message call, so a free function that emits must be invoked
externally to be tested. That reason survives the move, so the harness reaches
the emitters through an external wrapper.

Violet security-review findings reached the protocol tree through its pull
requests 35 and 36, not through an audit record. Pull request 35's finding was
that `emit_SanctionedAccountAssetsQueuedForWithdrawal` clobbered the free memory
pointer at `0x40` without restoring it. The mitigation is visible in three
emitters today and nothing re-proves it. Carried forward as
`free-pointer-clobber` in the risk register.

### Hermes CMP-10

Read from `plugins/hermes/skills/hermes/references/gas-rule-corpus.json`: id
`CMP-10`, title "require semantic equivalence testing", priority P0, evidence
grade A, `verified_on` compiler `0.8.25` and evm `cancun`, which matches the
pinned protocol settings. Two obligations, quoted:

- "optimization validation must cover outputs, storage, logs, reverts, calls, value movement, and protocol invariants."
- "assembly and decoder rewrites should retain an executable reference implementation wherever possible."

One suite serves both members only in part. It discharges the second obligation
in full for these 27 emitters: it is an executable reference implementation of
every one of them, and Hermes can cite it. It touches the first obligation on one
of seven named surfaces, `logs`, and leaves outputs, storage, reverts, calls,
value movement and protocol invariants untouched. `CMP-10` also scopes itself to
validating an optimization, and nothing here is being optimized, so what Hermes
gains is a standing reference it can cite when it later proposes or attests an
emitter change, not a discharge of `CMP-10` for any particular rewrite. Hermes
accepting the suite as its `CMP-10` reference is a statement about the second
obligation, and its acceptance names the suite digest and limits.

### Outside both repositories

`forge-std`'s `Vm.Log` struct (`bytes32[] topics`, `bytes data`, `address
emitter`) and the `vm.recordLogs` and `vm.getRecordedLogs` cheatcodes are the
recording surface. The encoding under test is the one in the Solidity ABI
specification: topic0 is the keccak-256 of the canonical signature, each
`indexed` value-typed argument becomes one topic in declaration order, and the
non-indexed arguments are ABI-encoded into the data region.

## 3. Constraints and non-goals

**Starting refs.** This repository: `main`, run branch
`fiat/1354-fizz-4-emitter-fidelity-differential-suite`, worktree head
`e7d0fdea1a636e06725fc55a55d02c24f74a64ee`. The protocol repository:
`main` at `f5a26146987926f4811b72a795d662813dedfe85`, read only. The local clone
at `/Users/c0rtexzer0/Documents/GitHub/v2-protocol` is checked out on
`feat/v2.5-events-data-model` and carries four leftover `fiat/fizz-4-*` branches
from a withdrawn attempt; none is touched and every read goes through
`git show <sha>:<path>`.

**Toolchain pins.** `forge` 1.7.1, `solc 0.8.25` resolved by forge,
`evm_version cancun`, Python 3.14.6 from `.python-version`. The harness
`foundry.toml` copies the Janus profile: `libs = []`, `bytecode_hash = "none"`,
optimizer on at 200 runs, no `ffi`, no `fs_permissions` beyond `out`.

**The vendored closure.** The transitive Solidity import closure of the two
emitter files and the two declaring files is eleven files and 46,799 bytes:
`src/interfaces/IMarketEventsAndErrors.sol`, `src/libraries/Errors.sol`,
`src/libraries/FeeMath.sol`, `src/libraries/MarketEvents.sol`,
`src/libraries/MarketState.sol`, `src/libraries/MathUtils.sol`,
`src/libraries/SafeCastLib.sol`, `src/spherex/ISphereXEngine.sol`,
`src/spherex/SphereXConfig.sol`, `src/spherex/SphereXProtectedErrors.sol`,
`src/spherex/SphereXProtectedEvents.sol`. The measurement finds **zero** remapped
or external imports in that closure, so it compiles with `libs = []` and pulls no
dependency into this repository. The two emitter files themselves import
nothing.

**`forge build` is usable here, and that is a change from the protocol tree.**
On the whole protocol tree, `forge build` exits 1 with `Error: Lint failed` and
forge 1.7.1 offers no `--no-lint` flag. On the vendored closure alone it exits 0
in 522 ms cold with 32 warning-level `unsafe-typecast` lints, all in
`src/libraries/SafeCastLib.sol`, and zero error-level lints. The denial therefore
comes from a file outside this closure. Both `forge build` and `forge test` are
available as step exits, which is what lets the workflow copy the Janus and
Pandects shape exactly.

**Boundaries.**

*Always.* Run `forge build` and `forge test` from `plugins/hexaemeron/harness/`
before any commit on this branch. Run `python3 scripts/run_checks.py` and require
exit zero before a push. Run the imprimatur, brevitas and hypomnema lints on every
shipped document at its published `docs/` path. Regenerate the Horos boundary and
census with `python3 plugins/horos/skills/horos/scripts/horos.py scan . --write`
after adding tracked files, because the root suite checks it. Record the seed and
run length of any campaign whose result is reported.

*Ask first.* Adding a dependency under any `lib/`. Changing an existing
workflow rather than adding one. Changing `tests/check-map-v1.json` beyond adding
this scope's own entries. Widening the harness `foundry.toml` beyond the Janus
profile, and in particular enabling `ffi`. Allocating a decision-record number,
which collides against the default branch and must be re-picked just before
pushing.

*Never.* Write anything under `plugins/hexaemeron/skills/fizz/`,
`plugins/hexaemeron/skills/x-ray/` or `plugins/hexaemeron/skills/solidity-auditor/`.
Write anything into `wildcat-finance/v2-protocol`. Commit a key or an RPC
credential. Delete or skip a failing case to make the suite green. Report a
campaign that did not run or a seed that was not used. Derive an expected topic,
arity or data offset from the assembly.

**Non-goals.**

- The protocol repository's `release/v2.5` branch. Its emitter set differs and
  porting is not in this delivery.
- Delivering the suite into `wildcat-finance/v2-protocol`. That is a separate
  decision for the protocol maintainer, and this study neither makes it nor
  blocks it.
- Stateful fuzzing, handler generation and ghost variables. The emitters hold no
  state. Echidna and Medusa are out of scope, so the Pandects finding about
  `crytic-compile` skipping `test/` does not bind here and would have to be
  answered before any engine change.
- Any change to protocol source. If a counterexample proves an emitter wrong,
  the specimen is filed here and the fix is a separate decision there.
- Gas measurement. Hermes owns that and no gas claim is made.
- Events emitted through high-level `emit` in the protocol. Only the 27 assembly
  emitters are in scope.
- Completeness of the event set, and anything about off-chain capture. A green
  campaign is the absence of a counterexample in the explored space under the
  declared harness.

## 4. Design options

The question is where an emitter-fidelity differential suite for another
repository's contracts lives inside this one, and what the deliverable is. The
trap is a home that looks like a delivery and executes nothing, which is exactly
the failure two carried audit findings record.

**skills-harness.** A first-party Foundry root at `plugins/hexaemeron/harness/`
carrying the pinned closure under `src/vendor/`, a mirror-emit reference and the
differential suite, with `.github/workflows/hexaemeron-forge.yml` and two
`tests/check-map-v1.json` entries. The trade: this repository takes on 46,799
bytes of another repository's Solidity and the duty to re-pin it when the
protocol moves.

**fizz-inline.** A generator, template and reference added inside the vendored
Fizz skill tree, producing the suite for any assembly-emitting target. The trade
is stated by a decision record rather than discovered: the suite is upstream-owned
and byte-for-byte unmodified, and the repository's own structure check already
refuses first-party contracts inside vendored instructions.

**spec-only.** The emitter inventory, the property specification, the oracle
design and the campaign record land here as evidence; the executable suite goes
to the protocol repository separately. The trade: nothing in this repository can
re-run, and a reader holding only this repository cannot reproduce a filed
counterexample.

**fixture-project.** A Foundry project carrying the closure under
`plugins/hexaemeron/tests/fixtures/`, in the shape Ariadne already uses, driven
by the Python root suite. The trade: the existing fixtures of that shape ship
compiler output rather than a compiled tree, so the pattern's own precedent is
data, not execution.

The prose explains the candidates. The selection is made by
`.hexaemeron/design-evidence.json` under `protasis-design-evidence/v1`, from five
criteria whose every value `.hexaemeron/measure_design.py` computes from the two
real trees. Nothing in the matrix is transcribed from this prose, and the reverse
is also true.

The five criteria:

- `repo-runnable-emitters` (correctness, gate, at least 27, owner elenchus). How
  many of the emitters a `forge` command *declared in this repository* would
  execute. The script counts the emitters at the pinned protocol ref, then reads
  `tests/check-map-v1.json` and `.github/workflows/*.yml` for Foundry roots this
  repository actually builds, and matches the candidate's home shape against
  them.
- `vendored-tree-writes` (compatibility, gate, at most 0, owner hypomnema). How
  many of the candidate's write paths land under a directory whose `NOTICE.md`
  declares it vendored verbatim. The vendored root list is read from the tree,
  not asserted.
- `offline-missing-sources` (recovery, gate, at most 0, owner elenchus). How
  many closure files a reader holding only this repository would still have to
  fetch from elsewhere to reproduce a filed counterexample.
- `carried-source-bytes` (space, metric, minimise, owner metron). Bytes of
  protocol Solidity the candidate copies into this repository.
- `source-resolution-ms` (time, metric, minimise, owner metron). Measured
  wall-clock, median of five, to resolve the whole closure once.

The measured matrix:

| candidate | runnable | vendored writes | missing sources | carried bytes | resolution ms |
| --- | --- | --- | --- | --- | --- |
| skills-harness | 27 | 0 | 0 | 46799 | 0 |
| fizz-inline | 0 | 3 | 11 | 0 | 1193 |
| spec-only | 0 | 0 | 11 | 0 | 577 |
| fixture-project | 0 | 0 | 0 | 46799 | 0 |

`fizz-inline` fails all three gates, `spec-only` fails two, and `fixture-project`
fails the correctness gate because no declared check in this repository compiles a
Foundry root of its shape. One candidate survives, so the record's rule is
`unique-frontier` and the selected candidate is `skills-harness`. The gates
decided; the two metrics recorded no difference among survivors because there is
one. `source-resolution-ms` reports 0 for both source-carrying candidates because
the median of five local reads of eleven files rounds below half a millisecond,
and the float sits in the `--detail` output. That measurement also understates
the two fetching candidates for anyone who does not already hold a protocol
clone, and the report says so. The two gate columns reproduce exactly on a
re-run; the timing column does not, because it is wall clock. A second run of
the resolver on this machine gave 1, 1188, 1010 and 3 against the pinned 0,
1193, 577 and 0. The pinned report bytes are the evidence, the selection does
not rest on them, and a reader re-running the resolver should expect the timing
column to move and the three gates not to.

No criterion is left pending, and no conformance cell exists. A conformance cell
would demand the campaign run under three rejected homes, which is not evidence
anybody would use. The campaign result is the last runbook step's exit command
instead.

**What is already established, and what is not.** Running
`python3 .hexaemeron/measure_design.py --facts` against the pinned protocol ref
gives 27 emitters, 28 declarations, 27 paired to a declaration by stripping the
`emit_` prefix, zero unpaired; all 27 hard-coded topic0 constants equal the
keccak-256 of the declared canonical signature; all 27 `logN` arities equal the
declared indexed count plus one; all 27 data-region sizes equal the declared
non-indexed argument count in words. Two facts fall out of the same pass.
`AccountSanctioned` is declared in `IMarketEventsAndErrors` with no assembly
emitter, a dead declaration at this ref. And
`emit_SanctionedAccountAssetsQueuedForWithdrawal` takes `uint32 expiry` while
`SanctionedAccountAssetsQueuedForWithdrawal` declares `uint256 expiry`; the
recorded bytes agree because `mstore` zero-extends, but the emitter's Solidity
signature narrows what a caller may pass.

That is a static derivation, which is a stronger read than the one the issue
objects to but is still a read. It settles topic0, arity and word count and says
nothing about whether the runtime bytes in the data region are the right values
in the right order. The suite settles that, and it is why the static agreement
does not make the suite redundant.

## 5. Risk register seed

The concerns below are what the audit loop should look hardest at. This is the
first run in this plugin's own tree with Solidity in it, which the plugin's own
round 2 recorded as an untested path, so the Solidity rounds get their first real
object here. Two concerns exist because the emitters write into memory the rest
of the program owns: three borrow the free-pointer slot at `0x40` and restore it,
one writes past the free pointer without advancing it, and the rest use scratch
space at `0x00` to `0x3f`. Two more exist because two carried audit findings
record suites that could not fail, and one records a reference that was not sound.

```risk-register
comparison-cannot-fail | the differential assertion itself | a committed wrong-topic specimen and a committed wrong-data specimen are both rejected, so the comparison is proved able to fail
reference-is-not-authority | the mirror-emit reference contract | the reference imports the declaring interface rather than redeclaring the events, so a declaration change cannot pass unnoticed
oracle-derived-from-assembly | how each expected log is produced | no expected topic0, topic count, indexed position or data offset is read from or transcribed out of the two emitter files
vendored-source-drift | the pinned protocol closure under src/vendor | each vendored file's SHA-256 is checked against the recorded protocol ref, and drift fails rather than re-baselining
vendored-boundary-write | any path under the three Pashov skill roots | the diff writes nothing under plugins/hexaemeron/skills/fizz, x-ray or solidity-auditor
pairing-by-name | the emit_<EventName> to declaration mapping | every emitter resolves to exactly one declaration and the paired count equals the count of emit_ free functions in the two vendored files
unpaired-emitter | an emitter that resolves to no declaration | the suite fails rather than skipping, and a new emitter with no case makes it fail
narrowed-fuzz-domain | the argument domain each case explores | the emitter's own parameter types bound the domain, and the widening to the declared type is explicit where the two differ
free-pointer-clobber | memory at 0x40 across an emitter call | the free memory pointer is read before and after and is unchanged
scratch-space-reuse | memory 0x00 to 0x5f before an emitter call | a dirtied scratch space before the call does not change the recorded data
recordlogs-pairing | the two Vm.Log entries the harness compares | the harness asserts exactly two entries and pairs them by position, not by topic0, so a wrong topic0 cannot pair with itself
log4-arity-ceiling | the comparison's topic array handling | topic arrays compare on length first and then element by element, with no hard-coded ceiling
data-region-length | the data byte string of each recorded log | length is compared before content, so a short or long region fails on length rather than on a truncated comparison
campaign-record-provenance | the engine, seed, run length and commits in the campaign record | each value is read back from the run that produced it, not written by hand
ffi-disabled | the harness foundry.toml and every file under it | ffi is absent from the profile and no test calls vm.ffi, vm.readFile or vm.writeFile
check-map-ownership | tests/check-map-v1.json after the new scope is added | run_checks.py plans and runs the two new forge checks and refuses no path in the diff for want of an owner
```

## 6. Glossary seeds

- **Emitter.** One of the 27 `emit_<EventName>` free functions that builds a log in assembly.
- **Declaration.** The Solidity `event` statement the emitter corresponds to, in `IMarketEventsAndErrors` or `SphereXConfig`.
- **topic0.** The keccak-256 of the event's canonical signature; the first topic of a non-anonymous log.
- **Indexed topic.** A topic after topic0, carrying one `indexed` argument in declaration order.
- **Data region.** The ABI-encoded non-indexed arguments, the bytes `logN` reads from memory.
- **Arity.** The `N` in `logN`; equal to one plus the number of indexed arguments.
- **Mirror-emit reference.** A contract that declares nothing of its own, imports the declaring interface, and emits each event through high-level `emit` so the compiler derives the encoding.
- **Differential case.** One fuzz case that calls an emitter and its reference and compares the two recorded logs.
- **Closure.** The eleven pinned protocol source files the emitters and declarations transitively import.
- **Specimen.** A committed replay test built from a counterexample, which fails without the fix.
- **Campaign record.** The JSON naming engine, seed, run length, both commits and emitter count for a run.
- **Vendored root.** A skill directory whose `NOTICE.md` declares it vendored verbatim from upstream; its bytes are not ours to change.
- **Scratch space.** Memory `0x00` to `0x3f`, which Solidity leaves free for transient use.
- **Free memory pointer.** The word at `0x40` holding the next unallocated memory offset.

## 7. Sources

- `plugins/hexaemeron/skills/VERSIONING.md`, lines 9 to 11: the vendored-skill exemption naming `fizz`, `x-ray` and `solidity-auditor`.
- `docs/decisions/ADR-005-vendor-the-pashov-suite-whole-and-ungoverned.md`, cited by the slug `vendor-the-pashov-suite-whole-and-ungoverned`: upstream-owned, byte-for-byte unmodified, ungoverned.
- `docs/decisions/ADR-003-bind-vendored-promises-with-digests.md`: overlay declarations live in `plugins/hexaemeron/PROMISES.md`.
- `plugins/janus/harness/foundry.toml`, `.github/workflows/janus-forge.yml`, `plugins/janus/scripts/run_forge_tests.py`: the layout, workflow and Elenchus bridge this delivery copies.
- `plugins/pandects/foundry.toml`, `.github/workflows/pandects-forge.yml`, and the `pandects-forge-build` and `pandects-forge-test` entries in `tests/check-map-v1.json`: the root-runner wiring.
- `plugins/ariadne/tests/fixtures/forge-project/v1/` and `v2/`: the fixture pattern that ships `out/` artifacts rather than a compiled tree.
- `plugins/hexaemeron/skills/fizz/NOTICE.md` and `VERSION`: the vendoring record and the absent ledger.
- `plugins/hexaemeron/skills/fiat/EVOLUTION.md`: the only Hexaemeron ledger in scope, frontier revision `state-shape-validation`.
- `AGENTS.md`, "Checks for changes to this repository", "Solidity", "Lints", "Commit gate" and "Reading boundary".
- `plugins/hermes/skills/hermes/references/gas-rule-corpus.json`, rule `CMP-10`.
- `audit/AUDIT_SYNOPSIS.md` `S2-R1-05`; `plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md` step 0 round 2; `audit/rounds/fiat-329-janus-resolve-the-manifest-s-permitted-effec.synopsis.md` `S2-R2-01` and `S2-R2-07`; `plugins/pandects/audit/AUDIT_SYNOPSIS.md` `S2-R1-01` and `S2-R1-02`. Whole-set currency proved by `audit_synopsis.py --check .` exiting zero with every row `committed=match`.
- `wildcat-finance/v2-protocol` at `f5a26146987926f4811b72a795d662813dedfe85`: `src/libraries/MarketEvents.sol`, `src/spherex/SphereXProtectedEvents.sol`, `src/interfaces/IMarketEventsAndErrors.sol`, `src/spherex/SphereXConfig.sol`, `TESTS.md`, `test/LogTest.sol`, `test/spherex/SphereXConfig.t.sol`, `test/libraries/wrappers/`, and pull requests 35 and 36 for the Violet findings.
- Commits `23110792` and `1f2298b2` in this repository: the per-root path-filtered workflow convention.
- `wildcat-finance/skills` issue 1354, the task issue bound to this run.
- `.hexaemeron/measure_design.py`, `.hexaemeron/design-evidence.json` and `.hexaemeron/reports/`, this study's own measurements.

## 8. Signals, and the questions behind them

Three questions, and none is a three-in-the-morning question in the usual sense,
because this suite runs in CI and in a terminal rather than unattended in
production. They are still questions someone will ask of a red or green result
they did not watch. `plugins/hexaemeron/skills/ephoros/SKILL.md` owns what a
signal must carry.

**Did the campaign actually run, and with what?** A green suite says nothing
about how hard it was tried, and two carried audit findings are about suites that
tried nothing. The signal is
`plugins/hexaemeron/harness/campaign/emitter-fidelity-campaign.json`, written by
the final step, carrying the engine and its version, the `--fuzz-seed`, the runs
per case, this repository's commit, the pinned protocol commit, the emitter count
and the case count, every value read back from the run that produced it. The
final step emits this.

**Did an emitter go unchecked?** The case that costs the most is a new emitter
with no test, because the suite then passes. The signal is an assertion inside the
suite that the number of paired cases equals the number of `emit_` free functions
in the two vendored emitter files, with the count printed on every run. The step
that builds the harness emits this.

**Is the vendored copy still the protocol's?** A silent re-pin would make the
suite prove fidelity against a tree nobody deployed. The signal is a provenance
record naming the protocol ref and the SHA-256 of each vendored file, checked on
every run, printed with the ref on failure. Step 1 emits this.

## 9. Boundaries, per capability

`plugins/hexaemeron/skills/phylax/SKILL.md` owns the boundary list and the
controls. This delivery opens one new boundary and closes two that the
alternatives would have opened.

**Vendored protocol source entering this repository.** Eleven files and 46,799
bytes of another repository's Solidity become tracked here. What is worth taking
at that boundary is a stale or substituted copy that makes the suite prove
fidelity against something nobody deployed. The control is a provenance record
naming the protocol ref and each file's SHA-256, checked by the suite on every
run, and the `Never` rule that no vendored protocol file is edited in place. The
closure imports nothing outside itself, measured, so no dependency crosses with
it.

**Foundry FFI.** The harness profile omits `ffi` entirely, following
`plugins/janus/harness/foundry.toml`, which also states in a comment that it uses
no ffi and no network. The control is that `ffi` is absent from the profile and
that no file under the harness calls `vm.ffi`, `vm.readFile` or `vm.writeFile`,
checkable by grep; it is `ffi-disabled` in the risk register.

**The vendored skill boundary.** Nothing is written under
`plugins/hexaemeron/skills/fizz/`, `x-ray/` or `solidity-auditor/`. This is the
boundary the repository's own structure check enforces after finding `S2-R1-05`,
and it is why the delivery is first-party and outside those roots.

**Untrusted input.** The suite's only inputs are fuzzer-chosen argument values,
which are the point of it, and they reach only pure functions with no storage and
no external call. The study-time script `.hexaemeron/measure_design.py` reads a
local protocol clone through `git show` with a pinned full SHA and no shell,
makes no network call, and is not shipped. There is no subprocess in the suite, no
filesystem write from Solidity, no credential and no dependency addition.

## 10. The budget, or its absence

There is a budget, because the harness is meant to sit in CI and 27 fuzzed cases
at Foundry's default of 256 runs is 6,912 EVM executions, with a plausible target
of 1,000 runs per case. `plugins/hexaemeron/skills/metron/SKILL.md` owns what a
budget carries and how it is checked.

**The budget.** `forge build` then `forge test` from
`plugins/hexaemeron/harness/` finishes inside 120 seconds of wall clock at 1,000
runs per case on the machine that records the baseline, measured cold with no
`out/`.

**The recorded starting point.** A cold `forge build` over the vendored closure
alone, with no suite and no reference, exits 0 in 522 ms on this machine. That is
the floor the suite is added to, not the budget.

**The command that measures it.**

```
cd plugins/hexaemeron/harness && rm -rf out cache && time sh -c 'forge build && forge test --fuzz-runs 1000 --fuzz-seed <seed>'
```

The baseline is recorded before the budget is claimed to hold, and the same
command with the same seed and run count re-measures it. If it does not hold, the
lever is the run count per case, recorded in the campaign record, not a narrower
argument domain.

## 11. The fail-closed posture

`plugins/hexaemeron/skills/elenchus/SKILL.md` owns the triage order and the guard
rule.

**What stops the run.** Any difference in any of the five compared fields fails
the case. A recorded-log count other than two fails the case, because a harness
that recorded one log has not compared anything. An emitter that resolves to no
declaration fails the suite rather than being skipped. A paired-case count that
does not equal the emitter count fails the suite. A vendored file whose SHA-256
does not match the recorded protocol ref fails the suite. The two deliberate
wrong-topic and wrong-data specimens must be rejected, so a comparison that has
stopped comparing fails rather than passing. Nothing is warned about and allowed
through.

**The guard convention.** A counterexample becomes a specimen: a deterministic
replay test under `plugins/hexaemeron/harness/test/specimens/`, named
`test_emit_<EventName>_Specimen<N>`, hard-coding the failing arguments, with the
shrunk values and the seed that found them in a comment above it. The specimen
fails without the fix and passes with it. Specimens are committed even when the
underlying emitter is not changed in this delivery, so a deferred fix stays
visible; an unresolved divergence prevents a fidelity claim.

**The runner contract.** The exact command a step's audit uses when it claims a
fix, following the Janus launcher's shape:

```
python3 plugins/hexaemeron/scripts/run_forge_tests.py {report}
```

The report format is `forge-junit-v1` and the report file is
`.hexaemeron/test-reports/step-<n>.xml`. Elenchus admits `unittest-json-v1`,
`forge-junit-v1` and `node-test-json-v1` and would refuse Foundry's own JSON test
output, which is why the launcher runs `forge test --junit`.

## 12. Decisions and their homes

`plugins/hexaemeron/skills/hypomnema/SKILL.md` owns which decisions earn a record
and where each one lives. This repository already has the home: numbered records
under `docs/decisions/`, named `ADR-NNN-<slug>.md`, cited elsewhere by their
stable slug. The number is checked against the default branch, so it is picked
just before the push rather than at the start.

Four decisions are expensive to reverse.

**The suite is delivered into this repository as a first-party Foundry root, not
into the Fizz skill tree.** Reversing it moves every file, every specimen path and
the workflow, and the alternative it rejects is refused by an existing decision
record and by an executed structure check. Home: a new record under
`docs/decisions/`, carrying the status, the context, the decision, the three
rejected candidates with the gate each failed, and the consequence that a new
emitter must be paired by name or the suite fails. It supersedes nothing and
cites `vendor-the-pashov-suite-whole-and-ungoverned` as its constraint.

**The oracle is declaration-derived, through a mirror-emit reference.**
Reversing this means rewriting every case, and worse, a suite that has been green
for a year under a transcribed oracle has been proving nothing. Recorded as a
section of the same record, because it is the construction the home decision
makes possible rather than an independent choice, and because a reader who finds
one needs the other in the same place.

**This repository carries a pinned copy of another repository's Solidity.**
Reversing it removes the harness's ability to build at all, and the re-pinning
duty it creates outlives this delivery. Recorded as a section of the same record,
with the protocol ref and the provenance-check rule stated so a later re-pin is a
deliberate, evidenced change rather than a merge.

**This delivery increments no skill version.** Fizz keeps no ledger and no
Hexaemeron plugin-level ledger exists in the tracked tree, so there is nothing to
increment and the issue's `held-job` label does not authorise one. Recorded as a
line in the runbook's final step and in the pull request body rather than in a
decision record, because it is the absence of a change and a record of an absence
in `docs/decisions/` would read as a policy nobody made.

**Where the study and runbook live.** `docs/` already holds paired
`<slug>-study.md` and `<slug>-runbook.md` files, twelve pairs of them. These
follow: `docs/emitter-fidelity-differential-suite-study.md` and
`docs/emitter-fidelity-differential-suite-runbook.md`, committed by step 1 and
linted at those paths.

### Amendment -- 2026-09-13

**What changed.** Five corrections. First, the `source-resolution-ms` column
in section 4: the twenty reports the design record binds by digest hold 0,
1063, 956 and 1 for skills-harness, fizz-inline, spec-only and
fixture-project; the matrix rows and the sentence "the pinned 0, 1193, 577
and 0" quoted an unpinned run of the resolver, and the sentence "Nothing in
the matrix is transcribed from this prose" was false for that column alone.
The three gate columns and `carried-source-bytes` match the reports exactly
and the selection is unchanged. Second, section 2: `plugins/janus/harness/`
holds 20 tracked `.sol` files under `src/` (13) and `test/` (7) at
`e7d0fdea`, plus `adapters/ManifestFuzz.sol`, not fifteen. Third, section
12: the top level of `docs/` holds 51 `-study.md` and 50 `-runbook.md` files
at `e7d0fdea`, not twelve pairs. Fourth, section 12: the decision draft's
home is
`docs/decisions/drafts/deliver-the-emitter-fidelity-suite-as-a-first-party-harness.md`,
the one directory
`plugins/hexaemeron/skills/hypomnema/scripts/decision_assignments.py` reads
drafts from (`DRAFTS`, line 49), with the first heading `# Decision: Deliver
the emitter-fidelity suite as a first-party harness`; a non-`ADR-` file
directly under `docs/decisions/` is classified `misplaced` (lines 476 to 478)
and refused as `draft-placement` at composition (lines 602 to 604). The block
below binds the selected candidate to that record. Fifth, the Boundaries in
section 3: the repository-wide command is
`python3 scripts/run_checks.py --base main --format json` with `outcome`
`green`; the bare form plans nothing on a clean committed head and exits 0
with `nothing-selected`.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | skills-harness
record | docs/decisions/drafts/deliver-the-emitter-fidelity-suite-as-a-first-party-harness.md
```

**Why.** Audit round 1 of step 1 recorded S1-R1-01 (draft placement and the
missing design bridge), S1-R1-02 (the timing column), S1-R1-03 (the bare
check command) and S1-R1-04 (the two counts).

**Steps touched.** Steps 1, 2, 3 and 4.

**Still holding.** Step 1: entry holds; exit broken. Step 2: entry holds;
exit broken. Step 3: entry holds; exit broken. Step 4: entry holds; exit
broken.

### Amendment -- 2026-09-13

**What changed.** One correction to the amendment above: the `misplaced`
classification in
`plugins/hexaemeron/skills/hypomnema/scripts/decision_assignments.py` is at
lines 485 to 487, with `misplaced[path] = entry` at line 487, not at lines 476
to 478, which hold the `identity-duplicate` refusal. Line 49 and lines 602 to
604 stand as cited.

**Why.** Audit round 2 of step 1 recorded S1-R2-01. This amendment moves the
study digest, which un-binds the four runbook amendments until each is
re-issued against the new digest; the exits below are broken for that reason
and for no other.

**Steps touched.** Steps 1, 2, 3 and 4.

**Still holding.** Step 1: entry holds; exit broken. Step 2: entry holds;
exit broken. Step 3: entry holds; exit broken. Step 4: entry holds; exit
broken.
