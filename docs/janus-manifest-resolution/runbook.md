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
