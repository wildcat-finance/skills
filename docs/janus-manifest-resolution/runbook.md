# Runbook: janus resolves the manifest's permitted effects into the gate inputs

Derived from [the study](study.md). Run branch
`fiat/329-janus-resolve-the-manifest-s-permitted-effec` off `main` at
`6813bdb36ae27d23606f3449c019e5ab85520212`; task issue
[wildcat-finance/skills#329](https://github.com/wildcat-finance/skills/issues/329).
Six steps, dependency order: scaffold, resolution-core, adapter-resolution,
gate-rewiring, disagreement-proof, ledger-prose with the demonstration. Each
step is one pull request stacked on the one before it. Both suites
(`forge test` from `plugins/janus/harness/`; `python3 -m unittest discover -s
tests` from `plugins/janus/`) and `python3 scripts/janus.py validate
manifests/*.json` run green before every commit. The imprimatur lint runs on
every shipped document. Ask first before widening `fs_permissions`, adding a
dependency, changing the manifest schema's required shape, or touching CI.
Never weaken a gate, never commit a hostile fixture its gate does not catch,
never edit the held `Next Fiat job` or the frontier digest.

## Step 1: Scaffold: committed spec and the report launcher

**Goal.** The study and runbook ship in the repository and a repo-owned
launcher exists that writes `forge test --junit` XML to a named report path.
**Entry.** The run branch at `6813bdb36ae27d23606f3449c019e5ab85520212`, both
suites green as verified in the study.
**Exit.** `docs/janus-manifest-resolution/study.md` and `runbook.md` are
committed copies of the receipted artefacts; `python3
plugins/janus/scripts/run_forge_tests.py tmp/elenchus/fiat-329-step-1.xml`
exits 0 and the file it writes is JUnit XML naming 24 passing tests; both
suites and `janus.py validate` remain green.
**Files.** `docs/janus-manifest-resolution/study.md`,
`docs/janus-manifest-resolution/runbook.md`,
`plugins/janus/scripts/run_forge_tests.py`.
**Tests.** No new gates: the launcher run above is the check, plus the two
existing suites unchanged (24 forge tests, 21 Python tests). Elenchus runner
contract for this step: test command `python3
plugins/janus/scripts/run_forge_tests.py {report}`, report format
`forge-junit-v1`, report file `tmp/elenchus/fiat-329-step-1.xml`.
**Disciplines.** phylax: the launcher spawns `forge` with a pinned argv, no
shell, cwd `plugins/janus/harness`, and writes only to its single report-path
argument. ephoros: none, a terminal-invoked launcher whose failure is its
exit code. metron: none, no performance claim. elenchus: none, no failure in
hand; this step establishes the runner contract later fixes are guarded by.
hypomnema: the committed study and runbook are the run's durable spec record.

## Step 2: Resolution core: the manifest reader

**Goal.** A shared `ManifestReader.sol` turns one manifest file plus one host
adapter into a `ResolvedThreshold` for a named action, failing closed.
**Entry.** Step 1's exit tree on its branch; suites green.
**Exit.** `forge test` green including the new `ManifestReader.t.sol`
covering: threshold selected by action name (never by position), a missing
action reverts, the account symbol is the text before the first `.`, scope
`hook` and `host` resolve through the adapter and `external` resolves its
slot prefix, a `staticcall` entry admits nothing into the state-changing
allowed set, an unresolvable symbol or zero address reverts, and the gas
budget returned is the named action's own.
**Files.** `plugins/janus/harness/src/ManifestReader.sol` (new),
`plugins/janus/harness/src/Vm.sol` (adds `keyExistsJson`, signature copied
exactly from Foundry's canonical `Vm`),
`plugins/janus/harness/test/ManifestReader.t.sol` (new, with a stub adapter
local to the test).
**Tests.** `ManifestReader.t.sol`, expected 8 to 12 new tests, exercising
every reader behaviour named in Exit against `wildcat-open-term.json` and
inline stub adapters. Elenchus runner contract for this step: test command
`python3 plugins/janus/scripts/run_forge_tests.py {report}`, report format
`forge-junit-v1`, report file `tmp/elenchus/fiat-329-step-2.xml`.
**Disciplines.** phylax: the reader consumes repo-local JSON through the
scoped filesystem cheatcode; `fs_permissions` do not widen and an
unresolvable name aborts rather than shrinking or widening a set. ephoros:
none, refusals are named test aborts. metron: none, milliseconds per test
accepted in the study. elenchus: none, no failure in hand; the fail-closed
tests are the guards the study promised. hypomnema: the symbol grammar and
the staticcall reading are recorded in the reader's header comment now and in
the schema text in step 6.

## Step 3: Adapter resolution: the name table

**Goal.** The host adapter owns name-to-address resolution: `resolveAccount`
joins the reader to the Wildcat model's concrete addresses.
**Entry.** Step 2's exit tree on its branch; suites green.
**Exit.** `forge test` green including new adapter tests proving `hook`,
`host`, `asset`, and `roleProvider` resolve to the adapter's stored
addresses, an unknown symbol refuses, a symbol whose stored address is zero
refuses, and `MockRoleProvider` answers the two credential calls the shipped
manifest declares.
**Files.** `plugins/janus/harness/src/HostAdapter.sol` (adds the
`resolveAccount(string) returns (bool, address)` virtual),
`plugins/janus/harness/src/wildcat/WildcatHostAdapter.sol` (implements the
table, mirroring `categoryOf`),
`plugins/janus/harness/src/wildcat/MockRoleProvider.sol` (new),
`plugins/janus/harness/test/WildcatAdapter.t.sol` (new).
**Tests.** `WildcatAdapter.t.sol`, expected 5 to 8 new tests covering the
four-name table, the two refusals, and the mock provider's answers. Elenchus
runner contract for this step: test command `python3
plugins/janus/scripts/run_forge_tests.py {report}`, report format
`forge-junit-v1`, report file `tmp/elenchus/fiat-329-step-3.xml`.
**Disciplines.** phylax: only the named symbol's address enters a set; the
table never sweeps a category into a permit. ephoros: none, terminal-run
tests. metron: none, no performance claim. elenchus: none, no failure in
hand. hypomnema: none beyond step 2's records; the table mirrors an existing
classification and is cheap to reverse.

## Step 4: Gate rewiring: conformance sets come from the manifest

**Goal.** Every conformance-verdict test builds its gate sets from
manifest-through-adapter resolution, gas budgets are per-action reads, and
the honest example exercises a non-empty resolved permit set.
**Entry.** Step 3's exit tree on its branch; suites green.
**Exit.** `forge test` green; grep shows no conformance-verdict test passing
a hand-written `address[]` literal into a gate (the laundering forwarder,
host-read, and JSON escaping engine-mechanics tests keep theirs, listed by
name in the diff); no `.thresholds[0]` positional read remains; the
provider-backed `HonestAccessHook` path makes the manifest's declared
`validateCredential` call on deposit and passes all seven gates; gate 3's
monotone known-lender behaviour is unchanged.
**Files.** `plugins/janus/harness/test/WildcatConformance.t.sol`,
`plugins/janus/harness/test/HostileHooks.t.sol`,
`plugins/janus/harness/src/wildcat/HonestAccessHook.sol` (optional provider
path), `plugins/janus/harness/src/JanusHarness.sol` (comments at 107 and 112
rewritten to describe the mechanism that now exists; gate signatures
unchanged).
**Tests.** Existing conformance tests rewired to resolution, expected count
held at 24 plus step 2 and 3 additions plus 1 to 3 new provider-path tests;
each hostile hook still caught with its resolved set. Elenchus runner
contract for this step: test command `python3
plugins/janus/scripts/run_forge_tests.py {report}`, report format
`forge-junit-v1`, report file `tmp/elenchus/fiat-329-step-4.xml`.
**Disciplines.** phylax: the manifest becomes the permit authority for
verdict tests; the hostile five must still each be caught, which is the
over-permit check. ephoros: none, terminal-run tests. metron: none, the
study accepts the parse cost. elenchus: none at entry; any hostile-set
regression surfaced here is worked to cause before the step closes.
hypomnema: the gate comments in `JanusHarness.sol` become the mechanism
record the study's section 12 names.

## Step 5: Disagreement proof: refusal, permit, fail-closed

**Goal.** The disagreement class issue 329 names is pinned by tests: an
omitted manifest entry is refused, a declared one is admitted, and an
unresolvable symbol aborts.
**Entry.** Step 4's exit tree on its branch; suites green.
**Exit.** `forge test` green including: a hook that calls the role provider,
driven against `manifests/fixtures/wildcat-open-term-omitted-call.json`
(deposit threshold omits that call entry), fails gate 1; the same hook
against the shipped manifest passes gate 1; a manifest naming a symbol the
adapter cannot resolve aborts with the reader's named error
(`expectRevert`); the five hostile hooks remain caught. `python3
scripts/janus.py validate` exits 0 over the shipped manifest and the new
fixture; `python3 -m unittest discover -s tests` stays green.
**Files.** `plugins/janus/harness/manifests/fixtures/
wildcat-open-term-omitted-call.json` (new, valid under the schema),
`plugins/janus/harness/manifests/fixtures/
wildcat-open-term-unknown-symbol.json` (new, valid under the schema),
`plugins/janus/harness/test/ManifestDisagreement.t.sol` (new).
**Tests.** `ManifestDisagreement.t.sol`, expected 3 to 5 new tests: the
refusal, the permit, the fail-closed abort, and hostile regression assertions
where `HostileHooks.t.sol` does not already carry them. Elenchus
runner contract for this step: test command `python3
plugins/janus/scripts/run_forge_tests.py {report}`, report format
`forge-junit-v1`, report file `tmp/elenchus/fiat-329-step-5.xml`.
**Disciplines.** phylax: the fixtures stay inside `./manifests`, so
`fs_permissions` do not widen; both fixtures must pass the validator so the
refusal comes from the gate, not a malformed file. ephoros: none,
terminal-run tests. metron: none, no performance claim. elenchus: the
refusal test is the guard for the shipped disagreement, and the fail-closed
test guards the unresolvable-symbol path; each fails without its fix.
hypomnema: none new; the fixtures document themselves by name.

## Step 6: Ledger and prose, then the demonstration

**Goal.** The generation row lands, the shipped prose describes the mechanism
that now exists, and the demo path from the study's problem statement runs
end to end.
**Entry.** Step 5's exit tree on its branch; suites green.
**Exit.** `plugins/janus/skills/janus/EVOLUTION.md` carries exactly one new
row: `janus-v0.2.0`, axis `generation`, frontier revision
`second-host-adapter` and digest
`c244247ec1071dda04c29206e52efe3eab264e8c323eaf15468f03e3a9688764` retained
byte for byte, the held `Next Fiat job` unchanged; `SKILL.md` frontmatter
reads `0.2.0` and its prose, the plugin `README.md`, and the schema
`description` fields record the symbol grammar, account granularity, and the
staticcall reading; the imprimatur lint exits 0 over every changed document;
the repository prose suite stays green; then the demo path runs: both suites
green, and `python3 scripts/janus.py report --findings <emitted file> --md
report.md --sarif report.sarif` renders a findings file the harness emitted.
**Files.** `plugins/janus/skills/janus/EVOLUTION.md`,
`plugins/janus/skills/janus/SKILL.md`, `plugins/janus/README.md`,
`plugins/janus/harness/schemas/hook-manifest.schema.json` (`description`
fields only; required shape unchanged), `plugins/janus/AGENTS.md` and
`.agents/skills/janus/SKILL.md` where they repeat the changed prose.
**Tests.** No new gates: the two suites, the validator over all manifests,
and the repository prose suite (`python3 -m unittest discover -s tests` from
the repository root) all green; the demonstration run recorded in the pull
request body. Elenchus runner contract for this step: test command `python3
plugins/janus/scripts/run_forge_tests.py {report}`, report format
`forge-junit-v1`, report file `tmp/elenchus/fiat-329-step-6.xml`.
**Disciplines.** phylax: none new, prose and one schema-description surface.
ephoros: none, nothing starts running unattended. metron: none, no
performance claim. elenchus: none, no failure in hand. hypomnema: the
generation row is the durable record that from `janus-v0.2.0` the gates
consult the manifest; the schema descriptions are the format contract the
second-adapter author reads.

### Amendment -- 2026-08-28

**What changed.** Complete replacement Tests: No new gates: the launcher run
above is the check, plus the two existing suites unchanged (24 forge tests,
14 Python tests). Elenchus runner contract for this step: test command
`python3 plugins/janus/scripts/run_forge_tests.py {report}`, report format
`forge-junit-v1`, report file `tmp/elenchus/fiat-329-step-1.xml`.
**Why.** Mason's entry verification ran the Python suite at
`6813bdb36ae27d23606f3449c019e5ab85520212` and it reports 14 tests; the 21 in
the receipted step text was an unsourced count. The study states no Python
count, so only the runbook moves.
**Steps touched.** Step 1.
**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds.
Step 5: entry holds; exit holds. Step 6: entry holds; exit holds.

### Amendment -- 2026-08-28

**What changed.** Complete replacement Exit:
`docs/janus-manifest-resolution/runbook.md` is a committed copy of the
receipted runbook current at this step's final push;
`docs/janus-manifest-resolution/study.md` is the receipted study with its five
`../plugins/hexaemeron/skills/` links rewritten as
`../../plugins/hexaemeron/skills/` so each resolves from the committed
location, and no other byte changed; the portable Promise Machine runtime and
the Horos boundary are regenerated with `python3
scripts/portable_promise_machine.py sync` and `python3
plugins/horos/skills/horos/scripts/horos.py scan . --write` so the repository
invariant suite (`python3 -m unittest discover -s tests`) passes; `python3
plugins/janus/scripts/run_forge_tests.py tmp/elenchus/fiat-329-step-1.xml`
exits 0 and the file it writes is JUnit XML naming 24 passing tests; both
suites and `janus.py validate` remain green. Complete replacement Files:
`docs/janus-manifest-resolution/study.md`,
`docs/janus-manifest-resolution/runbook.md`,
`plugins/janus/scripts/run_forge_tests.py`,
`.agents/skills/promise-machine/runtime/MANIFEST.json`,
`.agents/skills/promise-machine/runtime/.horos/boundary.json`,
`.agents/skills/promise-machine/runtime/plugins/janus/scripts/run_forge_tests.py`,
`.horos/boundary.json`.
**Why.** The repository invariant suite on the pushed step branch failed
twice: the hypomnema pointer lint, because the study's five plugin links were
written for `.hexaemeron/` and resolve to nothing from
`docs/janus-manifest-resolution/`, and the portable-runtime currency check,
because the new launcher was not synchronised into the portable runtime.
Byte-identical committed copies and a green invariant suite cannot both hold,
so the exit names the link rewrite and the two regenerated surfaces.
**Steps touched.** Step 1.
**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds.
Step 5: entry holds; exit holds. Step 6: entry holds; exit holds.

### Amendment -- 2026-08-29

**What changed.** Complete replacement Files: `plugins/janus/harness/src/ManifestReader.sol` (new), `plugins/janus/harness/src/Vm.sol` (adds `keyExistsJson`, signature copied exactly from Foundry's canonical `Vm`), `plugins/janus/harness/test/ManifestReader.t.sol` (new, with a stub adapter local to the test), `plugins/janus/harness/adapters/ManifestFuzz.sol` (new, the invariant fuzz suite carrying `FuzzResolver` and `ManifestFuzz` with properties GL01 to GL07), `plugins/janus/harness/adapters/echidna/echidna.yaml` (new), `plugins/janus/harness/adapters/medusa/medusa.json` (new), and `plugins/janus/scripts/run_fuzz_campaigns.py` (new, pinned argv, no shell, cwd resolved from its own file, computing Medusa's absolute compilation target at run time). Corpus directories under `adapters/echidna/corpus/` and `adapters/medusa/corpus/` are generated by a campaign, never committed, and already excluded by the repository `.gitignore` rule `**/corpus/`.
**Why.** Round 1 of this step ran real Echidna and Medusa campaigns under the audit loop's fizz obligation, and the suite they ran was deleted before the round's commit because the receipted Files list did not name it. The campaigns are round evidence either way; the suite is worth keeping because every later round would otherwise rebuild it from nothing, and because its round-1 form encoded the S2-R1-01 defect as a law rather than testing for it, which is exactly the regression a persisted and corrected suite prevents. The suite lives under the harness Foundry root because that is where the pandects convention actually points: `plugins/pandects/foundry.toml` sits at its plugin root, so pandects' `adapters/` is inside its Foundry project, whereas `plugins/janus/adapters/` would sit outside this project while resembling the convention. Two boundaries stay closed and are stated rather than assumed: `fs_permissions` do not widen, because the suite calls `resolveJson` only and never reaches the filesystem cheatcode; and `foundry.toml` is not touched, so `forge test` does not compile the suite. The consequence of that second choice is accepted openly: a compile break inside the suite escapes the forge run and surfaces only when a campaign is run through the runner script. Running a campaign additionally requires Echidna 2.3.3, Medusa 1.5.1 and crytic-compile 0.4.2 on the machine; that is a toolchain requirement on whoever runs it, not a repository dependency, and no CI wiring is added here.
**Steps touched.** Step 2.
**Still holding.** Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds. Step 6: entry holds; exit holds.

### Amendment -- 2026-08-29

**What changed.** Complete replacement Exit: `plugins/janus/skills/janus/EVOLUTION.md` carries exactly one new row: `janus-v0.2.0`, axis `generation`, frontier revision `second-host-adapter` and digest `c244247ec1071dda04c29206e52efe3eab264e8c323eaf15468f03e3a9688764` retained byte for byte, the held `Next Fiat job` unchanged; `SKILL.md` frontmatter reads `0.2.0` and its prose, the plugin `README.md`, and the schema `description` fields record the symbol grammar, account granularity, and the staticcall reading; `docs/janus-manifest-resolution/runbook.md` is refreshed to the receipted runbook current at this step's push, including every amendment appended after step 1, and `docs/janus-manifest-resolution/study.md` to the receipted study under the same link rewrite step 1's exit established, so the committed spec names every file the run actually built; the portable Promise Machine runtime and the Horos boundary are regenerated with `python3 scripts/portable_promise_machine.py sync` and `python3 plugins/horos/skills/horos/scripts/horos.py scan . --write`, alternated to a fixpoint, so the repository invariant suite passes; the imprimatur lint exits 0 over every changed document; the repository prose suite stays green; then the demo path runs: both suites green, and `python3 scripts/janus.py report --findings <emitted file> --md report.md --sarif report.sarif` renders a findings file the harness emitted. Complete replacement Files: `plugins/janus/skills/janus/EVOLUTION.md`, `plugins/janus/skills/janus/SKILL.md`, `plugins/janus/README.md`, `plugins/janus/harness/schemas/hook-manifest.schema.json` (`description` fields only; required shape unchanged), `plugins/janus/AGENTS.md` and `.agents/skills/janus/SKILL.md` where they repeat the changed prose, `docs/janus-manifest-resolution/runbook.md`, `docs/janus-manifest-resolution/study.md`, `.agents/skills/promise-machine/runtime/MANIFEST.json`, `.agents/skills/promise-machine/runtime/.horos/boundary.json`, and `.horos/boundary.json`.
**Why.** Step 2 round 2 recorded S2-R2-04: the committed runbook copy carries only the two amendments of 2026-08-28, so it does not name `adapters/ManifestFuzz.sol`, `adapters/echidna/echidna.yaml`, `adapters/medusa/medusa.json` or `scripts/run_fuzz_campaigns.py`, the four files the fuzz-suite amendment of 2026-08-29 admitted and commit 168ec6d1 added. Step 1's exit required the copy to be current at step 1's push, which it was; nothing required it to be current again afterwards, so every amendment appended during the build steps leaves the committed spec a little further behind the receipted one. Reconciling once here rather than at each step's push is deliberate: the runbook may be amended again before step 6, a per-step refresh would go stale the moment it landed, and the copy is a record for a later reader rather than an input any step consumes. The mirror and boundary paths join this step's Files for the same reason they joined step 1's, because adding or changing a mirrored file makes the repository invariant suite fail until both are regenerated.
**Steps touched.** Step 6.
**Still holding.** Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds. Step 6: entry holds; exit holds.

### Amendment -- 2026-08-29

**What changed.** Complete replacement Files: `plugins/janus/harness/test/WildcatConformance.t.sol`, `plugins/janus/harness/test/HostileHooks.t.sol`, `plugins/janus/harness/src/wildcat/HonestAccessHook.sol` (optional provider path), `plugins/janus/harness/src/JanusHarness.sol` (comments at 107 and 112 rewritten to describe the mechanism that now exists; gate signatures unchanged), `plugins/janus/harness/src/wildcat/IRoleProvider.sol` (new, holding the `IRoleProviderCalls` interface), and `plugins/janus/harness/src/wildcat/MockRoleProvider.sol` (declares that interface rather than merely matching it).
**Why.** The optional provider path needs an interface for the two credential calls the manifest names, and where that interface lives decides whether the compiler checks anything. Declaring it inside `HonestAccessHook.sol` and casting `MockRoleProvider` to it at the call site compiles, but the cast is unchecked, so a signature drift between the provider and the interface would be caught only at run time. That is exactly the defect S3-R3-01 recorded and fixed one step earlier, where the shipped adapter matched `AccountResolver` without declaring it while five test doubles declared it and were checked. Repeating the shape here, in the round after finding it, is not a trade worth making. The interface therefore gets its own file so the hook and the provider can both depend on it without depending on each other, and `MockRoleProvider` declares it. Two files join the step's list as a result. The alternative of leaving `AccountResolver` inside `ManifestReader.sol` was recorded in step 3 round 3 as the cleaner fix not taken because it fell outside that step's list; this amendment is that lesson applied at the point where the file is being created rather than moved, which costs nothing.
**Steps touched.** Step 4.
**Still holding.** Step 4: entry holds; exit holds. Step 5: entry holds; exit holds. Step 6: entry holds; exit holds.

### Amendment -- 2026-08-29

**What changed.** Complete replacement Exit: `forge test` green; grep shows no conformance-verdict test passing a hand-written `address[]` literal into a gate (the laundering forwarder, host-read, and JSON escaping engine-mechanics tests keep theirs, listed by name in the diff); no `.thresholds[0]` positional read remains; the provider-backed `HonestAccessHook` path makes the manifest's declared `validateCredential` call on deposit, and a test pins both halves of gate 1 over that deposit: the call half admits the call against the resolved set, and the storage half rejects the write that call causes, with the role provider shown to be the only account whose absence from `permittedStorageWrites` makes it reject; gate 3's monotone known-lender behaviour is unchanged.
**Why.** The original Exit required the provider-backed honest path to pass all seven gates, and against the shipped manifest it cannot. Wiring the declared provider for real is what showed why, which is the thing this step existed to do. The deposit threshold declares `roleProvider.validateCredential` a `call`, the kind reserved for state-changing calls, and then lists two `permittedStorageWrites` entries both scoped `hook` and nothing scoped to the provider. Gate 1 attributes a write to the hook when the written account is one the hook's subtree made a state-changing call into, which is the attribution that catches a call laundered through a permitted forwarder. So a provider that records anything when validated -- and recording is the only reason to declare the call state-changing rather than `staticcall` -- produces a storage write the manifest did not enumerate, and gate 1's storage half rejects the honest hook. Executed rather than argued: the honest deposit fails the storage half against the resolved write set, and passes it when the provider address alone is added, so the rejection is the manifest's missing clause and not a gate defect. The manifest is the artefact under test and is not edited to make a verdict green; the schema already carries the clause that would close the gap, a `permittedStorageWrites` entry of scope `external` whose slot names `roleProvider`, and adding it is a change to the Wildcat spec that belongs to whoever owns that file. The replacement Exit therefore requires the disagreement to be pinned in both directions rather than requiring a green verdict that would only be reachable by weakening the example, editing the spec, or leaving the storage half unexercised on the honest path as it was before this step.
**Steps touched.** Step 4.
**Still holding.** Step 4: entry holds; exit holds. Step 5: entry holds; exit holds. Step 6: entry holds; exit holds.
