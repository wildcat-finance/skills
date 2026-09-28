# Wildcat boundary fixtures runbook

The accepted study is `.hexaemeron/study.md`, committed as a copy in Step 1.
Deliver issue 1384 from `2dbfe40e08ee41429c521e0089a31ed872a1890d` on the run
branch `fiat/1384-lazarus-34-fixed-block-fixture-at-a-sealed`, with Python
3.14.6 and the pinned Lazarus requirements. The selected design proves every
mapped storage word for both Wildcat estates at their capture boundaries, V1 at
block 22074622 and V2 at block 26022093, and keeps every fixture, release and
admission archive in Miskatonic custody.

```design-lock
schema | protasis-design-evidence/v1
sha256 | 6ff7cd6915dafcd5c9c4bca04219821a0b1df5180cc7eb135ed1503848b669ca
candidate | full-map-r2-handoff
```

```version-relations
lazarus | plugins/lazarus/skills/lazarus/EVOLUTION.md | next-generation-after-integration-base
```

```command-interfaces
schema | protasis-command-interfaces/v1
plugins/lazarus/tests/run_tests.py | report_target | 30ac03545680e6233d7be0e57628b4dadb6224254de487179c3e4639d5a9425d
```

The registered Lazarus runner is the existing reviewed source. Its parser takes
one optional fresh Elenchus report path inside the checkout and discovers the
Lazarus tests. No step edits it. Interface validation is never reported as
execution, and test counts come from executed reports.

Rules every step keeps:

1. Fixture, release and Alexandria archive bytes never enter the tree. They
   live in one private directory with mode 0700 outside every checkout. The
   two release trees are named by `WILDCAT_BOUNDARY_V1_RELEASE` and
   `WILDCAT_BOUNDARY_V2_RELEASE`. Committed files carry digests, counts and
   reports, never a local path.
2. The gateway credential is read from `~/.config/alexandria/rpc.env` in a
   subshell. No step prints it, passes it in argv or writes it, or any provider
   URL or raw provider error, into a file.
3. Each step raises the Lazarus package version above every version any local
   or remote ref claims, in the four version files, and the plugin release check
   in `scripts/plugin_release.py` passes against the step's pull request base
   before push.
4. Each commit is staged, then Horos rescans the boundary and the census, then
   both are staged, then the commit is made. The root suite runs on the
   committed tree.
5. Public prose writes as if the protocol data is to hand. It names no private
   repository, capture pipeline or corpus beyond what the value map at
   `docs/kickoff/1384/values.md` already names.
6. The Lazarus ledger gains exactly one generation row, in Step 4. Its frontier
   sentence, frontier revision and held job stay byte-identical.

## Step 1: Commit the specification and the plan generator

**Goal.** Ship the accepted study, runbook, design record and reports, the
custody decision draft, and the example's slot module, probe summaries and plan
generator, so both boundary plans regenerate byte for byte offline.

**Entry.** The run branch at the starting commit, with the receipted study,
runbook and design lock. Nothing has been captured.

**Exit.** The committed study and runbook copies are byte-identical to the
receipted artefacts, the committed design record and its 36 reports are
byte-identical to the receipted ones, and the decision draft exists at the path
the study's design bridge names. The example directory holds the slot module,
the probe script, both probe summaries, the plan generator and a digest record
of both plans. The generator, run from the repository root with no network,
writes the V1 plan with 434 requests, 21 proof targets and 244 slots and the V2
plan with 14,561 requests, 151 proof targets and 9,080 slots, each to a fresh
path and each at the digest the record commits, and Lazarus plan validation
accepts both. The generator refuses a request inventory that differs from the
value map's request spec and a market whose derived word count differs from its
probe. The README states that the example reads the value map under
`docs/kickoff/1384/` and needs a full source checkout. The portable package
stays under its line. These commands exit 0:

```sh
python3 scripts/run_checks.py --base fiat/1384-lazarus-34-fixed-block-fixture-at-a-sealed --scope root --scope lazarus --scope docs --scope repo-lints --format json
python3 plugins/lazarus/tests/run_tests.py
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/lazarus-wildcat-boundary-fixtures/study.md docs/lazarus-wildcat-boundary-fixtures/runbook.md plugins/lazarus/examples/wildcat-boundary-v0/README.md docs/decisions/drafts/keep-wildcat-boundary-fixtures-in-miskatonic-custody.md --max-defects 0
```

**Files.** Create `docs/lazarus-wildcat-boundary-fixtures/study.md`,
`runbook.md` and `design-evidence.json` as byte copies of the receipted
artefacts, and `docs/lazarus-wildcat-boundary-fixtures/design/` holding the 36
reports under `reports/`, the four plan summaries under `plans/`,
`candidates.json` and `resolve.py`, copied byte for byte from
`.hexaemeron/design/` so the record's relative report paths resolve. Create
`docs/decisions/drafts/keep-wildcat-boundary-fixtures-in-miskatonic-custody.md`.
Create `plugins/lazarus/examples/wildcat-boundary-v0/` holding `README.md`,
`wildcat_slots.py`, `probe.py`, `probe-v1.json`, `probe-v2.json`, `plan_v3.py`
and `plans.json`. Add `plugins/lazarus/tests/test_wildcat_boundary.py`. Raise the
version in `plugins/lazarus/.claude-plugin/plugin.json`,
`plugins/lazarus/.codex-plugin/plugin.json`, `.claude-plugin/marketplace.json`
and `tests/test_version_propagation.py`. Change `tests/check-map-v1.json` only
if a new path needs an owner, and `scripts/portable_promise_machine.py` with
`tests/test_portable_skills.py` only if the portable package must omit the new
test. Regenerate `.horos/boundary.json` and `.horos/census.json` through Horos.

**Tests.** The new test regenerates both plans into a scratch directory and
checks each digest, byte count and count of requests, proof targets and slots
against `plans.json`, and runs Lazarus plan validation on each. It checks the
generator's two refusals with altered copies of the request spec and a probe,
checks that the generator refuses an output path that exists or is a symlink,
checks the copies under `docs/lazarus-wildcat-boundary-fixtures/` against the
digests the design record and study receipt pin, and checks that no committed
file in the example carries a URL or credential pattern. Expect about ten new
tests. Elenchus command: `python3 plugins/lazarus/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.elenchus/wildcat-boundary-step-1.json`.

**Disciplines.** phylax: the generator reads only the value map and its own
directory and writes only to a fresh caller-named path, and the probe script's
network reads stay study-time evidence that no test repeats. ephoros: none,
nothing here runs unattended. metron: the portable package measurement is
recorded against its line, with no speed claim. elenchus: no known failure is
carried, and a generator mismatch stops the step. hypomnema: the custody
decision gets its draft record, and the word-naming method its README section.

## Step 2: Capture and verify both boundary fixtures

**Goal.** Capture each estate's plan-v3 fixture over the gateway into private
custody, verify both offline, and commit their capture records and per-value
relation reports.

**Entry.** Step 1's tree, the gateway environment file, and an empty private
directory with mode 0700 outside every checkout.

**Exit.** Both captures completed through Lazarus's own capture command from
plans regenerated at the committed digests, with the gateway as primary route
and the two archive routes as opaque anchor sources. Lazarus verify exits 0 on
each fixture offline and reports proof-backed relations equal to the plan's
proof targets plus slots, one header-bound relation, recorded-RPC entries equal
to the plan's requests and two receipt-trie-proved relations; the study expects
265, 1, 434 and 2 for V1 and 9,231, 1, 14,561 and 2 for V2. For each estate the
example commits a capture record carrying the fixture manifest digest, each
component's path, byte count and SHA-256, the verify report, and the capture's
terminal result with stage, elapsed seconds and request and byte counts but no
provider identity. It also commits a relation report giving each of the 61 map
rows exactly one class, proved, header-bound, recorded or unsupported, with
the proof target or request that backs it. The one V1 batch pair whose getter
simulates an expired pending batch is marked as a proved word with a differing
recorded view. No fixture byte, provider URL or credential enters the tree.
These commands exit 0:

```sh
python3 scripts/run_checks.py --base fiat/1384-lazarus-34-fixed-block-fixture-at-a-sealed --scope root --scope lazarus --scope docs --scope repo-lints --format json
python3 plugins/lazarus/tests/run_tests.py
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/lazarus/examples/wildcat-boundary-v0/README.md --max-defects 0
```

**Files.** Add `capture-v1.json`, `capture-v2.json`, `relations.py`,
`relations-v1.json` and `relations-v2.json` under
`plugins/lazarus/examples/wildcat-boundary-v0/`, and extend its `README.md`
with the capture procedure, the environment variable names and the custody
class without a path. Extend `plugins/lazarus/tests/test_wildcat_boundary.py`.
Raise the version in the four version files named in Step 1 and regenerate the
Horos boundary and census.

**Tests.** Check that each relation report covers all 61 rows with one class
and a backing entry present in the committed plan record or capture record,
that no row the map marks unsupported has a proof target, that the simulated
batch pair carries its differing view, that each capture record's counts equal
the plan counts in `plans.json`, that the relation generator refuses an output
path that exists, and that no committed file carries a URL or credential
pattern. These tests read committed records only; fixture verification against
the external bytes is the coordinator's recorded evidence, not a unit test.
Elenchus command: `python3 plugins/lazarus/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.elenchus/wildcat-boundary-step-2.json`.

**Disciplines.** phylax: this step opens the RPC transport and holds the
bearer, which stays in a subshell environment and out of argv and artefacts,
and its output lands only in private custody. ephoros: the capture record keeps
the terminal stage, counts and elapsed time with provider identities redacted,
which answers which stage stopped and which limit tripped. metron: each capture
stays under its plan's elapsed limit and records the measured time, with no
speed claim. elenchus: a capture or verify failure stops the step and is worked
to its cause, and no plan is narrowed and no digest edited to pass. hypomnema:
the README records the capture procedure beside the Step 1 custody draft.

## Step 3: Release, bind and demonstrate the refusals

**Goal.** Write each estate's Ariadne state-fixture/v2 statement, Lazarus
release and Alexandria proof-backed-state admission, and ship the demonstration
that verifies the releases and refuses altered bytes.

**Entry.** Step 2's tree, with both verified fixtures in private custody
byte-identical to their capture records.

**Exit.** For each estate Ariadne writes an unsigned state-fixture/v2
statement whose four evidence counts equal the verify report, Lazarus release
writes a release tree at the path its environment variable names, and
verify-release and Ariadne verify exit 0 on it. Alexandria admits each fixture
as a proof-backed-state capture in a release outside the tree, and its release
verification reruns Lazarus and exits 0. The example's demo script has three
subcommands. The mutations subcommand changes one storage value, one code byte
and one receipt byte per estate in fresh copies and exits 0 only when Lazarus
verify refuses all six and the unchanged fixtures still verify. The
verify-releases subcommand runs verify-release and Ariadne verify on both
release trees. The verify-preserved subcommand checks the committed digests and
reports offline, needs no external tree, and refuses an edited digest. The demo
script refuses a missing environment variable, an existing output path and a
symlinked input, and runs pinned argv without a shell. The example commits each
statement, each release document, both Alexandria capture plans and each
archive's digest inventory. These commands exit 0:

```sh
python3 scripts/run_checks.py --base fiat/1384-lazarus-34-fixed-block-fixture-at-a-sealed --scope root --scope lazarus --scope docs --scope repo-lints --format json
python3 plugins/lazarus/tests/run_tests.py
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/lazarus/examples/wildcat-boundary-v0/README.md --max-defects 0
```

**Files.** Add `demo.py`, `statement-v1.json`, `statement-v2.json`,
`release-v1.json`, `release-v2.json`, `alexandria-plan-v1.json`,
`alexandria-plan-v2.json` and `archives.json` under
`plugins/lazarus/examples/wildcat-boundary-v0/`, and extend its `README.md`
with the release, admission and demonstration commands. Extend
`plugins/lazarus/tests/test_wildcat_boundary.py`. Raise the version in the four
version files and regenerate the Horos boundary and census. Lazarus, Ariadne
and Alexandria runtime code stays unchanged; a needed change there is a study
amendment first.

**Tests.** Run verify-preserved in the suite and check that it refuses an
edited digest. Exercise the mutation routine against the committed Aave v4
release fixture, so its three refusal classes are checked offline in the suite.
Check the demo script's refusals of a missing variable, an existing output and
a symlinked input. Check that each committed statement's counts equal the
capture record's verify report and that each release document names the
statement and fixture digests the archive inventory records. The mutations and
verify-releases subcommands over the real release trees are the coordinator's
recorded delivery evidence; when their variables are unset the suite skips them
with that reason named. Elenchus command: `python3 plugins/lazarus/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.elenchus/wildcat-boundary-step-3.json`.

**Disciplines.** phylax: the demo script validates every supplied path and
variable, copies before it mutates, and never writes inside a release tree.
ephoros: each subcommand prints which check refused and on which estate, and
the committed records separate offline digest checks from full verification.
metron: none, no performance claim. elenchus: a verification or refusal that
does not behave as specified stops the step, and a fix lands with a guard test.
hypomnema: the README records the release and demonstration commands and what
each does not establish.

## Step 4: Hand off custody, record the generation and run the demo path

**Goal.** Propose Miskatonic custody for the archives, record the handoff and
the Lazarus generation, and run the study's demo path end to end.

**Entry.** Step 3's tree, with both release trees and both Alexandria releases
in private custody and verifying.

**Exit.** One pull request to wildcat-finance/miskatonic adds a handoff
directory under storage/r2/handoffs/ in the shape of the Wildcat handoffs
already there, listing each archive's byte count and SHA-256 and a proposed
source-register row, and is left open for the operator. Archives reach R2 only
through Miskatonic's custody tooling after the operator accepts that row by
digest; if that has not happened by integration, R2 admission is carried
forward by name. The example commits a handoff record naming that pull request,
the proposed source id and each archive's byte count and SHA-256, plus the
replication receipt's digest when an upload completed. The Lazarus ledger gains
one generation row whose evidence names this delivery's proof record, and the
skill metadata version matches it. The proof record in the docs directory
records each demo-path command from the study's problem statement with its exit
code and output digest, the six mutation refusals and the edited-digest
refusal, and states what the demonstration does not establish. These commands
exit 0:

```sh
python3 scripts/run_checks.py --base fiat/1384-lazarus-34-fixed-block-fixture-at-a-sealed --scope root --scope lazarus --scope docs --scope repo-lints --format json
python3 plugins/lazarus/tests/run_tests.py
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/lazarus-wildcat-boundary-fixtures/proof.md plugins/lazarus/examples/wildcat-boundary-v0/README.md --max-defects 0
```

**Files.** Add `plugins/lazarus/examples/wildcat-boundary-v0/handoff.json` and
`docs/lazarus-wildcat-boundary-fixtures/proof.md`, and extend the example's
`README.md`. Add the generation row to
`plugins/lazarus/skills/lazarus/EVOLUTION.md` and move `metadata.version` in
`plugins/lazarus/skills/lazarus/SKILL.md` to match. Refresh any Promise Machine
runtime-authority, coverage or agent-instruction fixture that pins the Lazarus
ledger or skill digest, through its owning tool, replaying no model. Extend
`plugins/lazarus/tests/test_wildcat_boundary.py`. Raise the version in the four
version files and regenerate the Horos boundary and census. The Miskatonic pull
request's files live in that repository.

**Tests.** Check that the handoff record names a pull request URL in
wildcat-finance/miskatonic and that its archive rows equal `archives.json`,
that the proof record lists every demo-path command with an exit code of 0 and
an output digest, and that the ledger's new row is the only one added and
leaves the frontier fields unchanged. Grep every suite for a pin of the Lazarus
ledger or skill digest before committing. Elenchus command: `python3 plugins/lazarus/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.elenchus/wildcat-boundary-step-4.json`.

**Disciplines.** phylax: the handoff pull request publishes to another
repository, so it carries sizes, digests and a proposed row only, with no
private path, URL or credential. ephoros: the handoff record and proof record
answer whether the committed digests still match an archive somebody restored.
metron: none, beyond recording the capture times Step 2 measured. elenchus: a
demo-path command that exits non-zero stops the step. hypomnema: the ledger row
records the generation, the proof record the demonstration, and the Step 1 draft
the custody decision.

### Amendment -- 2026-09-27

**What changed.**
Complete replacement Exit: Both captures completed through Lazarus's capture routine, called by the example's capture driver, from plans regenerated at the committed digests, with the gateway as primary route and the two archive routes as opaque anchor sources. The driver reads the gateway URL and bearer from named environment variables, sends the bearer as a request header, and puts neither value in argv, output or a file. Lazarus verify exits 0 on each fixture offline and reports proof-backed relations equal to the plan's proof targets plus slots, one header-bound relation, recorded-RPC entries equal to the plan's requests and two receipt-trie-proved relations; the study expects 265, 1, 434 and 2 for V1 and 9,231, 1, 14,561 and 2 for V2. For each estate the example commits a capture record carrying the fixture manifest digest, each component's path, byte count and SHA-256, the verify report, and the capture's terminal result with stage, elapsed seconds and request and byte counts but no provider identity. It also commits a relation report giving each of the 61 map rows exactly one class, proved, header-bound, recorded or unsupported, with the proof target or request that backs it. The one V1 batch pair whose getter simulates an expired pending batch is marked as a proved word with a differing recorded view. The committed runbook copy is byte-identical to the receipted runbook, this amendment included. No fixture byte, provider URL or credential enters the tree. These commands exit 0:

```sh
python3 scripts/run_checks.py --base fiat/1384-lazarus-34-fixed-block-fixture-at-a-sealed --scope root --scope lazarus --scope docs --scope repo-lints --format json
python3 plugins/lazarus/tests/run_tests.py
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/lazarus/examples/wildcat-boundary-v0/README.md --max-defects 0
```

Complete replacement Files: Add `capture.py`, `capture-v1.json`, `capture-v2.json`, `relations.py`, `relations-v1.json` and `relations-v2.json` under `plugins/lazarus/examples/wildcat-boundary-v0/`, and extend its `README.md` with the capture procedure, the environment variable names and the custody class without a path. Re-copy `docs/lazarus-wildcat-boundary-fixtures/runbook.md` from the receipted runbook and move its digest pin in `plugins/lazarus/tests/test_wildcat_boundary.py`, which the step also extends. Raise the version in the four version files named in Step 1 and regenerate the Horos boundary and census. Lazarus runtime code stays unchanged.

Complete replacement Tests: Check that each relation report covers all 61 rows with one class and a backing entry present in the committed plan record or capture record, that no row the map marks unsupported has a proof target, that the simulated batch pair carries its differing view, that each capture record's counts equal the plan counts in `plans.json`, that the relation generator refuses an output path that exists, and that no committed file carries a URL or credential pattern. Check that the capture driver refuses when either named environment variable is unset and when its output path exists, and, with Lazarus's capture routine replaced by a recording stand-in, that it passes the bearer only as a request header and never in argv or printed output. These tests read committed records only and reach no network; fixture verification against the external bytes is the coordinator's recorded evidence, not a unit test. Elenchus command: `python3 plugins/lazarus/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.elenchus/wildcat-boundary-step-2.json`.

**Why.** The Lazarus capture command takes its RPC URL in argv and passes no request header, while the gateway authenticates with a bearer header, which only Lazarus's capture routine accepts as an argument. A driver in the example keeps the credential out of argv without changing Lazarus, and this amendment changes the runbook bytes Step 1 committed, so Step 2 re-copies them.

**Steps touched.** Step 2.

**Still holding.** Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds.
