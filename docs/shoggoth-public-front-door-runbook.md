# Runbook: restore the Shoggoth public front door and demo frontier

This runbook is derived from the receipted study at SHA-256
`38b40ebb7e2a98c1cfa49ec6382a3179b01a9a869a13caf5032bf7e4fc4cddce`. The
repository starts at `66b6cfd6b20610484321abcb85079a0dce1b6070` on `main`. Use
CPython `3.14.6` from `.python-version`. The selected construction is the
per-skill demonstration ledger. Nothing in this run may add a field to
`EVOLUTION.md`, change a held behaviour job, or treat an unfiled demonstration
job as a GitHub issue.

```design-lock
schema | protasis-design-evidence/v1
sha256 | e66cd1c56570e629cac254dd4ae74817c0d01496a77f75bb35cb1efd7e5d8407
candidate | per-skill-demo-ledger
```

There is no `version-relations` block. The accepted design keeps every current
`EVOLUTION.md` byte and frontier digest unchanged. Demonstration versions and
jobs live only in the new adjacent ledgers.

Build order is `topology`, `demo-ledgers`, `demo-runner`, `front-door`,
`public-surface`, then `joined-proof`. Each step depends on every step before
it. Each step is one independently green pull request and may assume only its
controller-supplied entry head plus the receipted study, runbook, and immutable
design record.

## Standing rules for every step

Always use the pinned interpreter. Run the source-bound tests before an
implementation receipt. Run Imprimatur on changed prose. Preserve the external
human contributor identity rule. Finish with `git diff --check`.

**Counts are derived.** No step exit may assert a literal count against the
live tree. Every exit that touches a count asserts agreement between
independent sources: both marketplace manifests, discovery over the plugin
tree, and the counts written into public prose. Synthetic specimens keep their
literal expectations and carry their own arbitrary plugin and skill ids; no
assertion may compare a specimen identity set with a live identity set.

**The security suite is waived.** This run changes Python, Markdown and JSON
only and ships no Solidity, so `x-ray`, `solidity-auditor` and `fizz` have no
target. Every audit round instead owes three lint exits, and each step's
Disciplines field names what they are run against:

```bash
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py <changed Python>
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py <changed Python>
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py <changed Markdown>
```

**No task issue exists.** The controller recorded the nulls. No step, exit, or
carryover row may assume an issue, and no step may run `gh issue create`, close
an issue, or change a label.

**Report paths are fresh and never reused.** Each step's audit-fix report path
appears once, stays inside the worktree under the gitignored `.elenchus/`, and
must not already exist when the round starts. A stale report reads as a clean
pass, so a report path that already exists is a refusal, not an overwrite.

**Ask before** adding a dependency, changing CI workflow behaviour, enabling
network access, changing a public interface outside this runbook, filing or
editing an issue, or touching any `EVOLUTION.md`. Never edit historical audits,
ADR histories, specimens, content-addressed releases, or the ignored portable
runtime.

**Superseded prior work.** The first run's step branches remain open as
[PR #1077](https://github.com/wildcat-finance/skills/pull/1077) at `34f6b8ab`
and [PR #1078](https://github.com/wildcat-finance/skills/pull/1078) at
`d06e63c9`. This run rebuilds their content against the corrected specification.
No step merges, rebases, cherry-picks, or depends on either branch. They are
closed as superseded at integrate, with a comment naming the replacement pull
request, and their branches stay until then.

**Out of scope, by name**, so the integrate carryover block disposes of these
by reference rather than rediscovering them: issue
[#971](https://github.com/wildcat-finance/skills/issues/971)'s stale Fiat
generator-aggregate entry; the Lazarus provider-independence and
canonical-chain limits; the Alexandria coverage-field, loader shape-check and
dropped-venue leads; the held behaviour frontiers of Berean, Synkrisis,
Tabularium and Dokimasia; and the absent generator for
`docs/pdf/the-promise-machine-explained-properly.pdf`, which this run inspects
but cannot regenerate. Each is named in the study's non-goals and none is taken
here.

**Audit-record carryovers taken as step work.** All six carryovers the study
named from the Dokimasia and Anamnesis audit records are in scope and are
placed: `absence-passes-a-gate` in steps 2 and 4, `schema-declared-not-checked`
in step 2, `contract-refusal-drift` in step 2, `report-path-escape` in step 3,
`empty-suite-as-pass` in step 3, and `stale-Horos-boundary` in every step's
Files field and again in step 6. None is deferred.

## Step 1: Commit the design boundary and derive the checked topology

**Goal.** Put the receipted specification and its regenerable design record in
stable repository paths, and give later steps one checked discovery function
whose answer is derived rather than written down.

**Entry.** The controller-created run branch at
`66b6cfd6b20610484321abcb85079a0dce1b6070`; the receipted study at SHA-256
`38b40ebb7e2a98c1cfa49ec6382a3179b01a9a869a13caf5032bf7e4fc4cddce`; the
immutable design record at SHA-256
`e66cd1c56570e629cac254dd4ae74817c0d01496a77f75bb35cb1efd7e5d8407` with its 24
reports under `.hexaemeron/reports/`; an empty tracked diff; and
`python3 scripts/run_checks.py --full` green.

**Exit.** `docs/shoggoth-public-front-door-study.md` and
`docs/shoggoth-public-front-door-runbook.md` are byte-identical to the
receipted study and this runbook.
`docs/design/build_shoggoth_front_door_design_evidence.py` exists at exactly
that path, takes `--out <directory>`, and writes `design-evidence.json` plus a
`reports/` directory of 24 `protasis-design-report/v1` objects, serialised as
UTF-8 ASCII with `indent=2`, `sort_keys=True` and one trailing newline. Running
it reproduces the receipted record and all 24 receipted reports byte for byte,
and the committed copy at
`docs/shoggoth-public-front-door-design-evidence.json` with its 24 reports
under `docs/reports/` is byte-identical to the receipted pair and passes the
design-lock check in its committed location. This is the whole point of the
step: the `command` field every report carries must resolve for somebody who
clones this repository, which is the Dokimasia `S1-R1-01` defect this run
exists not to repeat. `scripts/shoggoth_topology.py` reads both marketplace
manifests and discovers governed directories from `EVOLUTION.md` without
following symlinks, anchored at `plugins/<id>/skills`. It refuses a duplicate
id, a manifest disagreement, a governed directory without a regular `SKILL.md`,
a symlinked skill-tree entry, a path outside `plugins/`, and a phase outside
Hexaemeron. `tests/test_shoggoth_topology.py` asserts that the two manifests
and tree discovery return the same plugin set, that every plugin has exactly
one canonical entry skill with Fiat as Hexaemeron's, that canonical plus phase
equals governed, and that
`plugins/hexaemeron/tests/fixtures/hypomnema/design-bridge/` is not counted;
it asserts no literal count against the live tree. Its four synthetic specimens
keep exact literal counts and use their own arbitrary ids, and no assertion
compares a specimen identity set with a live one. The root check graph owns the
new module and tests. `.python-version`, `pyproject.toml`, `LICENSE`, and
`.github/workflows/plugins.yml` are unchanged. Prove the exit with:

```bash
cmp .hexaemeron/study.md docs/shoggoth-public-front-door-study.md
cmp .hexaemeron/runbook.md docs/shoggoth-public-front-door-runbook.md
work="$(mktemp -d)"
python3 docs/design/build_shoggoth_front_door_design_evidence.py --out "$work"
cmp .hexaemeron/design-evidence.json "$work/design-evidence.json"
for f in .hexaemeron/reports/*.json; do cmp "$f" "$work/reports/$(basename "$f")"; done
cmp .hexaemeron/design-evidence.json docs/shoggoth-public-front-door-design-evidence.json
for f in .hexaemeron/reports/*.json; do cmp "$f" "docs/reports/$(basename "$f")"; done
python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py \
  docs/shoggoth-public-front-door-design-evidence.json --transition design-lock
python3 -m unittest tests.test_shoggoth_topology -v
python3 scripts/run_checks.py --plan
python3 scripts/run_checks.py --full --jobs 6 --report .hexaemeron/run-checks-step-1.json
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

Each command exits 0, and the Horos output is read rather than discarded.

**Files.** Create `docs/shoggoth-public-front-door-study.md`,
`docs/shoggoth-public-front-door-runbook.md`,
`docs/shoggoth-public-front-door-design-evidence.json`,
`docs/design/build_shoggoth_front_door_design_evidence.py`, the 24 reports
under `docs/reports/`, `scripts/shoggoth_topology.py`,
`tests/test_shoggoth_topology.py`, and four specimens under
`tests/fixtures/shoggoth-topology/`. Change `tests/check-map-v1.json`. Permit
`.horos/boundary.json` and `.horos/candidates.json` only when a deterministic
Horos scan whose output was read changes them. Warden alone may append
`audit/rounds/fiat-shoggoth-front-door-derived-counts.md` and regenerate its
`.synopsis.md` companion.

**Boundaries.** The inputs are repository-relative manifest and file paths and
one caller-supplied `--out` directory. The reader uses bounded no-follow
regular-file reads, refuses duplicate JSON keys, caps entries and depth, sorts
ids before comparison, and opens no socket or subprocess. The generator writes
only below its `--out` directory, refuses an existing target, and reads
nothing outside the repository. The four specimen JSON files are the only
synthetic topology inputs; the live tree is the integration specimen.

**Risks.** Review `count-literal-reintroduction`, `specimen-live-coupling`,
`fixture-tree-miscount`, `design-command-unreachable`,
`historical-record-rewrite` and `horos-boundary-staleness`. Every other study
risk id is not applicable because this step writes no public claim, governs no
ledger, and executes no demonstration.

**Contracts.** Apply `plugins/hexaemeron/skills/protasis/SKILL.md` to the
tracked specification and design copies,
`plugins/hexaemeron/skills/phylax/SKILL.md` to the path reader and generator,
`plugins/hexaemeron/skills/elenchus/SKILL.md` to any discovered failure, and
`plugins/hexaemeron/skills/hypomnema/SKILL.md` to the stable specification
homes.

**Tests.** Each of the four specimens carries its own arbitrary ids: the valid
one contains its exact declared plugin and skill counts, and the three invalid
ones fail for duplicate plugin id, missing canonical `SKILL.md`, and a phase
outside Hexaemeron. A temporary-tree case proves a symlinked skill directory is
refused. A temporary-tree case adds a nineteenth plugin and proves that exactly
the derived numbers move and nothing else breaks. A case proves the hypomnema
design-bridge fixture is excluded from discovery. No case asserts a literal
against the live tree. Run every command in Exit and record the observed
derived numbers as observations, not expectations. The audit-fix runner is
`python3 tests/run_tests.py --elenchus-report {report}`; its format is
`unittest-json-v1`, its expected schema is `elenchus.unittest.v1`, and its
fresh report path is `.elenchus/front-door-derived-counts-step-1.json`. The
`{report}` placeholder occurs exactly once.

**Disciplines.** phylax: run against `scripts/shoggoth_topology.py` and
`docs/design/build_shoggoth_front_door_design_evidence.py`, because both take
repository paths and JSON as bounded untrusted input. ephoros: run against the
same two files; this step adds no unattended operation, so the expected result
is a clean exit rather than new instrumentation. hypomnema: run against
`docs/shoggoth-public-front-door-study.md` and
`docs/shoggoth-public-front-door-runbook.md`, whose relative links must resolve
from `docs/`. metron: none, because discovery agreement is a correctness fact
rather than a speed claim. elenchus: the malformed, symlinked and
new-plugin specimens guard each refusal and the derivation itself.

## Step 2: Govern one demonstration ledger per skill

**Goal.** Add the independent demonstration contract, one ledger for every
discovered governed skill including Dokimasia, and a read-only demo-frontier
selection mode, without changing any behaviour frontier.

**Entry.** Step 1 merged; `scripts/shoggoth_topology.py` and its tests green;
`python3 scripts/run_checks.py --full` green; an empty tracked diff.

**Exit.** `plugins/hexaemeron/skills/DEMONSTRATIONS.md` states the normative
policy: the five closed status meanings, the `shoggoth-demonstration/v1` record
grammar, the independence of the demonstration lane from the behaviour lane,
the co-delivery rule, the `{skill}-demo` queue convention, and the exact list
of conditions the checker refuses. `schemas/shoggoth-demonstration-v1.json`
states that record shape, and the checker validates records against it with an
unknown key refused, so the schema is checked rather than merely declared. Every
governed skill directory discovery returns carries exactly one
`DEMONSTRATION.md` beside its `EVOLUTION.md`, each with a human ledger and one
fenced strict `shoggoth-demonstration/v1` object naming skill, status, source
class and identity, source digests or chain anchor, network policy, argv
arrays, expected observations, public claim id, non-claim, and per-command
timeout. `scripts/demonstrations.py check --root .` discovers exactly the
directories `scripts/shoggoth_topology.py` discovers, requires one record per
directory, and refuses a record whose `status` key is absent rather than
treating absence as a value. The count of refusal conditions stated in
`DEMONSTRATIONS.md` equals the count the checker enforces, proved by a test
that counts both. Dokimasia's ledger is authored on the same terms as every
other skill and records `real-data` with its stated caveat. Every existing
`EVOLUTION.md` is byte-identical to its entry state. Prove the exit with:

```bash
python3 scripts/demonstrations.py check --root .
python3 -m unittest tests.test_demonstrations -v
python3 -m unittest tests.test_shoggoth_topology -v
git diff --exit-code -- 'plugins/*/skills/**/EVOLUTION.md'
python3 scripts/run_checks.py --full --jobs 6 --report .hexaemeron/run-checks-step-2.json
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

Each command exits 0.

**Files.** Create `plugins/hexaemeron/skills/DEMONSTRATIONS.md`,
`schemas/shoggoth-demonstration-v1.json`, `scripts/demonstrations.py`,
`tests/test_demonstrations.py`, one `DEMONSTRATION.md` in every governed skill
directory discovery returns, and refusal specimens under
`tests/fixtures/demonstrations/`. Change `tests/check-map-v1.json`. Permit the
generated Horos files named in Step 1. Change no `EVOLUTION.md`. Warden alone
may append the audit round and its synopsis.

**Boundaries.** The inputs are local demonstration records and the discovered
skill tree. The checker performs bounded no-follow regular-file reads, refuses
duplicate keys, caps depth and bytes, requires exact field sets validated
against the committed schema, refuses unknown keys, refuses symlink traversal,
and starts no subprocess and opens no socket in this step. The demo-frontier
selection mode is read-only: it reads ledgers and prints, and never writes a
ledger, opens an issue, changes a label, or advances a frontier.

**Risks.** Review `frontier-lane-collision`, `schema-declared-not-checked`,
`contract-refusal-drift`, `demo-class-inflation`, `dokimasia-source-class`,
`queue-duplication`, `count-literal-reintroduction` and
`horos-boundary-staleness`. `subprocess-execution`, `external-data-egress`,
`report-path-escape`, `empty-selection-as-pass`, `partial-demo-output` and
`demo-skip-as-pass` are not applicable here because this step executes nothing;
step 3 takes them. The front-door risks are not applicable because this step
writes no public claim.

**Contracts.** Apply `plugins/hexaemeron/skills/protasis/SKILL.md` to the
record grammar, `plugins/hexaemeron/skills/phylax/SKILL.md` to the record
reader, `plugins/hexaemeron/skills/hypomnema/SKILL.md` to `DEMONSTRATIONS.md`
as the normative policy home, and `plugins/hexaemeron/skills/kronos/SKILL.md`
as the contract the demo lane must not disturb.

**Tests.** Discovery over the skill tree and the demonstration checker return
the same directory set, asserted as set equality rather than against a number.
A record missing `status` is refused. A record carrying an unknown key is
refused against the committed schema. A record whose status is outside the
closed five is refused. A ledger present twice in one directory is refused. A
governed directory with no ledger is refused. A test counts the refusal
conditions stated in `DEMONSTRATIONS.md` and the conditions the checker
enforces and asserts they are equal. A test asserts every `EVOLUTION.md`
digest is unchanged from the entry tree. The audit-fix runner is `python3
tests/run_tests.py --elenchus-report {report}`; its format is
`unittest-json-v1`, its expected schema is `elenchus.unittest.v1`, and its
fresh report path is `.elenchus/front-door-derived-counts-step-2.json`. The
`{report}` placeholder occurs exactly once.

**Disciplines.** phylax: run against `scripts/demonstrations.py`, which parses
untrusted local records and resolves paths. ephoros: run against
`scripts/demonstrations.py`, which gains the bounded
`demonstration.public_claim.checked` event and the demo-frontier selection
event; a no-eligible-job result must be a bounded event, not silence.
hypomnema: run against `plugins/hexaemeron/skills/DEMONSTRATIONS.md` and every
new `DEMONSTRATION.md`, whose relative links must resolve from their own
directories. metron: none, because this step makes no speed claim. elenchus:
each refusal specimen fails on the entry parent and passes on the fix.

## Step 3: Run the four real-data demonstrations offline

**Goal.** Give the four registered demonstrations one bounded, offline,
fail-closed runner, and record what each actually produced.

**Entry.** Step 2 merged; every governed skill carries one checked
demonstration ledger; `python3 scripts/demonstrations.py check --root .` green;
`python3 scripts/run_checks.py --full` green; an empty tracked diff.

**Exit.** `scripts/demonstrations.py run` accepts only a checked record or the
closed public set named by `--public-set`. It verifies every declared source
digest before execution and records a declared chain anchor as recorded
evidence rather than a proved one. It expands only its reserved `{work}`
private-work token inside argv elements, never invokes a shell, strips
credential and Git environment keys, denies sockets in Python children,
bounds each command by its record timeout, caps stdout and stderr, tears down
the process group, and atomically writes one `shoggoth-demonstration-report/v1`
object to a new caller-selected path whose containment below the declared
output root is checked after path resolution, so a traversing `--report` value
is refused rather than followed. A run that selects zero records exits nonzero;
an empty selection is never a clean pass. A registered demonstration missing
its command, source or dependency fails rather than skips. The four
demonstrations reproduce the results the study recorded: Anamnesis rebuilds the
committed pilot twice to one digest across 7 components and verifies the
Elenchus and Synkrisis projections; Lazarus runs
`plugins/lazarus/examples/goldfinch-v1/demo.py` as the registered producer
command, offline and under the ambient temporary root, proving the receipt-trie
relation at block `0xc7da16` with 224 contiguous receipts, target index `0xbf`,
110 target logs and the exact five-log projection; Alexandria rebuilds and
verifies `credit-history-v0` under the private work root to its recorded
release id; and Dokimasia reproduces the `wildcat-app-v2` scrutiny from its
committed evidence. Each report repeats its ledger's non-claim and cannot
promote source completeness, canonical-chain finality, finding truth, remedy
correctness, protocol safety, coverage adequacy or underwriting merit. The four
finish within the aggregate 600,000 millisecond ceiling. Prove the exit with:

```bash
python3 scripts/demonstrations.py check --root .
python3 -m unittest tests.test_demonstrations -v
python3 -m unittest discover -s plugins/anamnesis/tests -t plugins/anamnesis
python3 -m unittest discover -s plugins/lazarus/tests -t plugins/lazarus
python3 -m unittest discover -s plugins/alexandria/tests -t plugins/alexandria
python3 -m unittest discover -s plugins/dokimasia/tests -t plugins/dokimasia
python3 scripts/demonstrations.py run --public-set \
  --report .hexaemeron/reports/public-set-step-3.json
python3 scripts/run_checks.py --full --jobs 6 --report .hexaemeron/run-checks-step-3.json
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

Each command exits 0. The execution report stays under `.hexaemeron/` and is
never committed.

**Files.** Change `scripts/demonstrations.py`, `tests/test_demonstrations.py`,
`plugins/hexaemeron/skills/DEMONSTRATIONS.md`, and the four public-set ledgers
`plugins/anamnesis/skills/anamnesis/DEMONSTRATION.md`,
`plugins/lazarus/skills/lazarus/DEMONSTRATION.md`,
`plugins/alexandria/skills/alexandria/DEMONSTRATION.md` and
`plugins/dokimasia/skills/dokimasia/DEMONSTRATION.md`. Create refusal specimens
under `tests/fixtures/demonstrations/` for a network attempt, oversized output,
a timeout, a partial report, a stale source, a traversing report path, and an
empty selection. Permit the generated Horos files named in Step 1. Change no
`EVOLUTION.md`.

**Boundaries.** This is the step with the widest surface. Demonstration
manifests, sources, subprocess arguments and output paths are untrusted. Argv
arrays are executed without a shell under the pinned interpreter in a private
temporary root with a minimal environment. Sockets are denied by default and no
capture exception is declared in this run, so any socket attempt is a refusal.
Filesystem writes are confined to the private work root and one caller-selected
report path, checked for containment after resolution, refusing an existing
target, and published atomically or left visibly incomplete. Nothing is
committed from an execution run.

**Risks.** Review `source-drift`, `subprocess-execution`,
`external-data-egress`, `report-path-escape`, `empty-selection-as-pass`,
`partial-demo-output`, `demo-skip-as-pass`, `demo-class-inflation`,
`dokimasia-source-class` and `horos-boundary-staleness`. The front-door risks
are not applicable because this step writes no public claim;
`frontier-lane-collision` is not applicable because no ledger frontier
advances.

**Contracts.** Apply `plugins/hexaemeron/skills/phylax/SKILL.md` to the
runner's subprocess, network, path and environment boundaries,
`plugins/hexaemeron/skills/elenchus/SKILL.md` to every refusal specimen,
`plugins/hexaemeron/skills/ephoros/SKILL.md` to the emitted run events, and
`plugins/hexaemeron/skills/metron/SKILL.md` to the recorded durations, which
are observations and not a speed claim.

**Tests.** A record whose declared source digest does not match is refused
before execution. An argv element containing shell metacharacters is executed
literally, not interpreted. A child that opens a socket is refused. A child
that exceeds its output cap is truncated and refused. A child that exceeds its
timeout is killed with its process group. A `--report` path containing `..` is
refused. A `--report` path that already exists is refused. A public-set run
whose selection resolves to zero records exits nonzero. A registered
demonstration whose dependency is absent fails rather than skips. A partial
report is never published. Each of the four demonstrations is asserted against
the observations its ledger declares, not against a number written in prose.
The audit-fix runner is `python3 tests/run_tests.py --elenchus-report
{report}`; its format is `unittest-json-v1`, its expected schema is
`elenchus.unittest.v1`, and its fresh report path is
`.elenchus/front-door-derived-counts-step-3.json`. The `{report}` placeholder
occurs exactly once.

**Disciplines.** phylax: run against `scripts/demonstrations.py`, which is the
subprocess, network, credential and filesystem boundary of this run. ephoros:
run against `scripts/demonstrations.py`, which must emit
`demonstration.selected`, `started`, `verified` and `refused` under one
correlation id, with `selected` carrying the record count so a zero-selection
run is visible. hypomnema: run against `DEMONSTRATIONS.md` and the four changed
ledgers. metron: the aggregate ceiling and the three-repetition baseline are
recorded here; no per-skill threshold is declared. elenchus: every refusal
specimen fails on the entry parent and passes on the fix, and an inconclusive
comparison is not written up as guarded.

## Step 4: Restore the root front door and its derived counts

**Goal.** Make `README.md` a front door: short, self-aware, contribution
early, four checked demonstration cards, and every count derived.

**Entry.** Step 3 merged; the four demonstrations run green offline;
`python3 scripts/run_checks.py --full` green; an empty tracked diff.

**Exit.** `scripts/check_public_front_door.py --root .` exists and proves the
root contract: the Shoggoth portrait precedes the title; the introduction is at
most 150 words; `## SO, YOU WANT TO BUILD GOD?` and the external-contributor
route begin within the first 220 words; the file is at most 1,400 words; no
link target appears twice; the complete governed roster is not inlined; the
first Promise Machine contract link and the first catalogue link both follow
contribution and demonstrations; every ATX heading is all caps; and no root
image other than the collective portrait is present. `## WHAT CAN IT DO?`
carries exactly the four cards whose demonstration records are `real-data`,
each binding a hidden marker to its skill id, claim id and record digest, and
each displaying one command, one named preserved source, one concrete observed
result and the record's non-claim. A card whose bound record is absent,
downgraded, or digest-mismatched fails the check; a marker with no bound record
fails rather than passing by absence. Every count claim in `README.md` is
checked against agreement between both manifests, tree discovery, and the prose
itself, and no literal is compared against the live tree. The old chirp "Ask
the Atlas for a number. Pick your harness. Finish what you start." is retained,
and at least one further short self-aware line appears before the first
technical section. `tests/test_marketplace_prose.py` no longer pins a literal
member count or a stale sentence-case heading, and its roster-completeness
assertions move to `FUTUREPROOFING.md`. Prove the exit with:

```bash
python3 scripts/check_public_front_door.py --root .
python3 -m unittest tests.test_marketplace_prose -v
python3 -m unittest tests.test_shoggoth_topology -v
python3 scripts/demonstrations.py check --root .
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py README.md
python3 scripts/run_checks.py --full --jobs 6 --report .hexaemeron/run-checks-step-4.json
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

Each command exits 0, and the rendered README is visually inspected for
hierarchy, overflow, anomalous images and broken links.

**Files.** Create `scripts/check_public_front_door.py` and
`tests/test_public_front_door.py`, with front-door refusal specimens under
`tests/fixtures/public-front-door/`. Change `README.md`,
`tests/test_marketplace_prose.py`, `FUTUREPROOFING.md` to receive the complete
roster, and `tests/check-map-v1.json`. Permit the generated Horos files named
in Step 1. Change no `EVOLUTION.md` and no `DEMONSTRATION.md`.

**Boundaries.** The checker reads the repository's own Markdown and the
discovered demonstration records as bounded regular files, starts no
subprocess, opens no socket, and writes nothing. It grades structure, order,
budgets, markers and derived agreement; it never grades free-form voice, which
belongs to Imprimatur, Vulgate, Brevitas and human review.

**Risks.** Review `front-door-regression`, `claim-without-demo`,
`real-data-nonclaim-loss`, `portrait-inconsistency`,
`count-literal-reintroduction`, `demo-class-inflation` and
`horos-boundary-staleness`. `subprocess-execution`, `external-data-egress` and
`report-path-escape` are not applicable because this checker executes nothing
and writes nothing.

**Contracts.** Apply `plugins/hexaemeron/skills/imprimatur/SKILL.md` and
`plugins/hexaemeron/skills/vulgate/SKILL.md` to the rewritten prose,
`plugins/hexaemeron/skills/brevitas/SKILL.md` to its length,
`plugins/hexaemeron/skills/phylax/SKILL.md` to the checker's file reads, and
`plugins/hexaemeron/skills/hypomnema/SKILL.md` to the front-door role and its
budgets.

**Tests.** Specimens fail for each named condition and pass on the fix: a
sentence-case maintained heading; a contribution heading after the 220-word
boundary; an introduction over 150 words; a file over 1,400 words; a duplicate
link target; a root portrait other than the collective one; an inlined complete
roster; a card whose record is `mixed` but labelled `real-data`; a card whose
bound digest no longer matches; a marker with no bound record; a card missing
its non-claim; and a count claim disagreeing with either manifest or with
discovery. A test proves the checker fails when a named maintained document is
absent, rather than skipping it. The audit-fix runner is `python3
tests/run_tests.py --elenchus-report {report}`; its format is
`unittest-json-v1`, its expected schema is `elenchus.unittest.v1`, and its
fresh report path is `.elenchus/front-door-derived-counts-step-4.json`. The
`{report}` placeholder occurs exactly once.

**Disciplines.** phylax: run against `scripts/check_public_front_door.py`,
which reads untrusted repository Markdown and JSON. ephoros: run against the
same file; the checker emits one bounded
`demonstration.public_claim.checked` event per card. hypomnema: run against
`README.md` and `FUTUREPROOFING.md`, whose relative links must resolve from the
repository root. metron: the word and link budgets are contract limits measured
by the checker, not performance claims. elenchus: each front-door specimen
guards one refusal.

## Step 5: Reconcile the rest of the maintained public surface

**Goal.** Bring the remaining maintained documents into agreement with the
tree: derived counts everywhere, all-caps headings, two live factual repairs,
and the portrait boundary.

**Entry.** Step 4 merged; `scripts/check_public_front_door.py --root .` green;
`python3 scripts/run_checks.py --full` green; an empty tracked diff.

**Exit.** The checker's sweep covers a fixed, named set of maintained
documents and fails when one is absent rather than skipping it: `README.md`,
`INSTALL.md`, `FUTUREPROOFING.md`, `SHOGGOTH.md`, `PROMISE_MACHINE.md`,
`docs/how-to-help-shoggoth.md`, `docs/fiat-in-plain-english.md`,
`docs/the-promise-machine-explained-properly.md`, all 18 plugin `README.md`
files, and `.agents/skills/promise-machine/SKILL.md`. Every current
topology claim across that set is derived and agrees with both manifests and
discovery; no literal is compared against the live tree; and
`INSTALL.md`'s thirteen and fourteen plugin figures are untouched because they
are historical statements about a dated capture rather than claims about now.
Every ATX heading on that set is all caps. Two factual repairs land:
`plugins/anamnesis/README.md` no longer says the version implements source
admission only, because `anamnesis-v3.1.0` builds, verifies and projects a
release; and `README.md` no longer says Dokimasia's compile path has not
shipped, because `dokimasia-v2.1.0` compiles, imports, reconciles and
demonstrates. A test asserts that no maintained document describes a member as
unshipped in a way its own `EVOLUTION.md` contradicts. The 960-pixel Anamnesis
portrait is removed from `README.md`; its contextual portrait and character
section on `plugins/anamnesis/README.md` remain.
`docs/pdf/how-to-help-shoggoth.pdf` is regenerated by
`scripts/build_contributor_guide.py` and every page is visually inspected.
`docs/pdf/the-promise-machine-explained-properly.pdf` has no generator in this
repository; it is inspected, and if any heading or count in
`docs/the-promise-machine-explained-properly.md` changed in this run, the gap
between source and binary is recorded as a finding for the integrate carryover
rather than left as a stale binary nobody named. The portable package builds and its tests pass in a
disposable directory; the ignored runtime is not committed. Prove the exit
with:

```bash
python3 scripts/check_public_front_door.py --root .
python3 -m unittest tests.test_marketplace_prose -v
python3 -m unittest tests.test_public_front_door -v
python3 scripts/promise_machine.py check
python3 scripts/build_contributor_guide.py
git diff --exit-code -- docs/pdf/how-to-help-shoggoth.pdf || true
out="$(mktemp -d)/skills-runtime"
python3 scripts/portable_promise_machine.py package --out "$out"
python3 -m unittest tests.test_skills_sh_package -v
python3 scripts/run_checks.py --full --jobs 6 --report .hexaemeron/run-checks-step-5.json
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

Every command except the deliberately tolerant PDF comparison exits 0, and the
regenerated PDF is inspected page by page.

**Files.** Change `SHOGGOTH.md`, `docs/how-to-help-shoggoth.md`,
`docs/fiat-in-plain-english.md`,
`docs/the-promise-machine-explained-properly.md`, `PROMISE_MACHINE.md`,
`.agents/skills/promise-machine/SKILL.md`, `plugins/anamnesis/README.md`,
`README.md`, the remaining plugin `README.md` files that carry a maintained
heading or a current count, `scripts/check_public_front_door.py`,
`tests/test_public_front_door.py`, and `docs/pdf/how-to-help-shoggoth.pdf`.
Permit the generated Horos files named in Step 1. Change no `EVOLUTION.md`, no
`DEMONSTRATION.md`, no audit record, no ADR history, no specimen, and no
content-addressed release. Do not commit
`.agents/skills/promise-machine/runtime/`.

**Boundaries.** The inputs are the repository's own maintained Markdown, two
committed PDFs, and one disposable package directory. The package build writes
only below a temporary directory. The PDF generator is deterministic and writes
one named output. No network is used. Historical records are read-only: audits,
ADR bodies, studies, runbooks, specimens, releases, and `INSTALL.md`'s dated
capture figures are outside the writable set.

**Risks.** Review `absent-document-as-clean`, `stale-member-status`,
`historical-record-rewrite`, `generated-copy-drift`, `visual-surface-drift`,
`count-literal-reintroduction`, `portrait-inconsistency` and
`horos-boundary-staleness`. The demonstration-execution risks are not
applicable because this step runs no demonstration.

**Contracts.** Apply `plugins/hexaemeron/skills/imprimatur/SKILL.md` and
`plugins/hexaemeron/skills/vulgate/SKILL.md` to every changed document,
`plugins/hexaemeron/skills/brevitas/SKILL.md` to the reconciled lengths,
`plugins/hexaemeron/skills/hypomnema/SKILL.md` to the document homes and the
portrait boundary, and `plugins/horos/skills/horos/SKILL.md` to the binary
assets.

**Tests.** A specimen with a maintained document absent fails the sweep. A
specimen whose prose count disagrees with either manifest fails. A specimen
describing a member as unshipped against its own ledger fails. A specimen with
a sentence-case heading on the maintained set fails. A specimen rewriting an
`INSTALL.md` historical figure fails, because history is not a current claim. A
specimen restoring the root Anamnesis portrait fails. The package tests run
against a disposable build. The audit-fix runner is `python3
tests/run_tests.py --elenchus-report {report}`; its format is
`unittest-json-v1`, its expected schema is `elenchus.unittest.v1`, and its
fresh report path is `.elenchus/front-door-derived-counts-step-5.json`. The
`{report}` placeholder occurs exactly once.

**Disciplines.** phylax: run against `scripts/check_public_front_door.py` as
changed here; the PDF generator and package builder are existing audited code
and are not modified. ephoros: run against the same changed checker; this step
adds no unattended operation. hypomnema: run against every changed Markdown
document, which is the largest hypomnema surface in the run, and its relative
links must resolve from each document's own directory. metron: none, because
no speed claim is made. elenchus: each maintained-surface specimen guards one
refusal.

## Step 6: Prove the joined public front door and demo path

**Goal.** Prove the two capabilities work as one, and record the decisions
that were expensive to reverse.

**Entry.** Step 5 merged; the whole maintained surface reconciled;
`python3 scripts/run_checks.py --full` green; an empty tracked diff.

**Exit.** The joined proving path runs clean from a fresh clone of the run
branch, in this order, with network denied:

```bash
python3 scripts/check_public_front_door.py --root .
python3 scripts/demonstrations.py check --root .
python3 scripts/demonstrations.py run --public-set \
  --report .hexaemeron/reports/public-set-step-6.json
python3 scripts/run_checks.py --full --jobs 6 --report .hexaemeron/run-checks-step-6.json
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

Each command exits 0. Three decision records land:
`docs/decisions/ADR-068-govern-real-data-demonstrations-separately.md`,
`docs/decisions/ADR-069-keep-the-root-readme-as-a-front-door.md`, and
`docs/decisions/ADR-070-derive-topology-counts-from-the-tree.md`, the last
naming commit `67a01a6c` as the worked example of the failure it prevents and
recording the pinned-specimen exception. An end-to-end test proves the joined
relation rather than the parts: changing one demonstration record's status from
`real-data` to `mixed` makes the front-door check fail on the card that binds
it, and restoring it makes the check pass. A second end-to-end test adds a
nineteenth plugin to a scratch tree and proves that exactly the derived numbers
move, that the front-door check still passes once prose is regenerated from
discovery, and that no literal needed editing. The committed
`.horos/boundary.json` matches the delivered tree, with the scan output read
rather than discarded. Prove the exit with the commands above plus:

```bash
python3 -m unittest tests.test_joined_front_door -v
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs/decisions/ADR-068-govern-real-data-demonstrations-separately.md docs/decisions/ADR-069-keep-the-root-readme-as-a-front-door.md docs/decisions/ADR-070-derive-topology-counts-from-the-tree.md
```

**Files.** Create the three ADRs and `tests/test_joined_front_door.py`. Change
`tests/check-map-v1.json` and, only if the joined proof exposes a defect,
`scripts/check_public_front_door.py`, `scripts/demonstrations.py` or
`scripts/shoggoth_topology.py`. Permit the generated Horos files named in Step
1. Change no `EVOLUTION.md`.

**Boundaries.** The joined proof executes the demonstration runner, so it
inherits step 3's whole boundary: no shell, denied sockets, bounded output,
private work root, contained report path. The scratch-tree case builds a
nineteenth plugin below a temporary directory and never writes into the
repository. No issue is filed, no label changed, and no frontier advanced.

**Risks.** Review every id in the study's register. This is the step where a
concern disposed of as not applicable in an earlier step must be re-examined
against the joined path, because a boundary that held for one component can
fail where two meet.

**Contracts.** Apply `plugins/hexaemeron/skills/hypomnema/SKILL.md` to the
three decision records, `plugins/hexaemeron/skills/elenchus/SKILL.md` to the
joined guards, `plugins/hexaemeron/skills/phylax/SKILL.md` to the executed
path, and `plugins/hexaemeron/skills/protasis/SKILL.md` to the claim that the
prototype is complete.

**Tests.** The status-downgrade round trip fails and recovers as described. The
nineteenth-plugin scratch tree moves exactly the derived numbers. A test
asserts the committed Horos boundary matches the delivered tree. A test asserts
that `scripts/demonstrations.py` exposes no superseded public-set option
spelling and that no document on the maintained public surface names one, so
the rename is consistent everywhere a reader can reach. That sweep excludes
the two committed specification copies, because this runbook names the
superseded spelling in order to forbid it. A test
asserts no shipped first-party document carries a topology literal compared
against the live tree. The audit-fix runner is `python3 tests/run_tests.py
--elenchus-report {report}`; its format is `unittest-json-v1`, its expected
schema is `elenchus.unittest.v1`, and its fresh report path is
`.elenchus/front-door-derived-counts-step-6.json`. The `{report}` placeholder
occurs exactly once.

**Disciplines.** phylax: run against every Python file this step changes, and
re-run against `scripts/demonstrations.py` because the joined path executes it.
ephoros: run against the same set; the joined run must emit the same bounded
events under one correlation id. hypomnema: run against the three ADRs and any
changed Markdown. metron: the aggregate demonstration ceiling is re-measured
and recorded as an observation. elenchus: the two joined guards each fail on a
deliberately broken parent and pass on the delivered tree.

### Amendment -- 2026-09-02

**What changed.** Complete replacement Files: Create
`docs/shoggoth-public-front-door-study.md`,
`docs/shoggoth-public-front-door-runbook.md`,
`docs/shoggoth-public-front-door-design-evidence.json`,
`docs/design/build_shoggoth_front_door_design_evidence.py`, the 24 reports
under `docs/reports/`, `scripts/shoggoth_topology.py`,
`tests/test_shoggoth_topology.py`, and four specimens under
`tests/fixtures/shoggoth-topology/`. Change `tests/check-map-v1.json`. Permit
`.horos/boundary.json` and `.horos/candidates.json` only when a deterministic
Horos scan whose output was read changes them. Warden alone may append
`audit/rounds/fiat-shoggoth-front-door-derived.md` and regenerate its
`.synopsis.md` companion.

**Why.** Step 1's Files field named
`audit/rounds/fiat-shoggoth-front-door-derived-counts.md`, which this run does
not have. That path is derived from the run branch, and this run's branch is
`fiat/shoggoth-front-door-derived`; the earlier halted run used
`fiat/shoggoth-front-door-derived-counts`, and the runbook was carried forward
from it. The controller reports `audit.log_path` as
`audit/rounds/fiat-shoggoth-front-door-derived.md`, and `hexctl next` names
that same path on every audit-round directive, so Warden would have written a
file the permitted-paths list did not cover and step 1's tracked-diff exit
would have refused it. The audit record is a durable repository artefact, so
naming it after a branch that never existed is the stale-record-provenance
concern this study's own risk register carries from the Dokimasia S4-R1-01
finding, where provenance that is merely stale reads the same as provenance
that is wrong. Only the file name changes; the permitted set, its ownership by
Warden, and every other path are unchanged.

**Steps touched.** Step 1.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step
5: entry holds; exit holds. Step 6: entry holds; exit holds.

### Amendment -- 2026-09-04

**What changed.** Complete replacement Exit:
`docs/shoggoth-public-front-door-study.md` and
`docs/shoggoth-public-front-door-runbook.md` are byte-identical to the current
receipted study and runbook.
`docs/decisions/drafts/govern-real-data-demonstrations-separately.md` records
the selected `per-skill-demo-ledger` construction, and the study's one
`hypomnema-design-bridge/v1` block binds that candidate to that record.
`docs/design/build_shoggoth_front_door_design_evidence.py` exists at exactly
that path, takes `--out <directory>`, and writes `design-evidence.json` plus a
`reports/` directory of 24 `protasis-design-report/v1` objects, serialised as
UTF-8 ASCII with `indent=2`, `sort_keys=True` and one trailing newline. Running
it reproduces the receipted record and all 24 receipted reports byte for byte,
and the committed copy at
`docs/shoggoth-public-front-door-design-evidence.json` with its 24 reports
under `docs/reports/` is byte-identical to the receipted pair and passes the
design-lock check in its committed location. This is the whole point of the
step: the `command` field every report carries must resolve for somebody who
clones this repository, which is the Dokimasia `S1-R1-01` defect this run
exists not to repeat. `scripts/shoggoth_topology.py` reads both marketplace
manifests and discovers governed directories from `EVOLUTION.md` without
following symlinks, anchored at `plugins/<id>/skills`. It refuses a duplicate
id, a manifest disagreement, a governed directory without a regular `SKILL.md`,
a symlinked skill-tree entry, a path outside `plugins/`, and a phase outside
Hexaemeron. `tests/test_shoggoth_topology.py` asserts that the two manifests
and tree discovery return the same plugin set, that every plugin has exactly
one canonical entry skill with Fiat as Hexaemeron's, that canonical plus phase
equals governed, and that
`plugins/hexaemeron/tests/fixtures/hypomnema/design-bridge/` is not counted;
it asserts no literal count against the live tree. Its four synthetic specimens
keep exact literal counts and use their own arbitrary ids, and no assertion
compares a specimen identity set with a live one. The root check graph owns the
new module and tests. `.python-version`, `pyproject.toml`, `LICENSE`, and
`.github/workflows/plugins.yml` are unchanged. Prove the exit with:

```bash
cmp .hexaemeron/study.md docs/shoggoth-public-front-door-study.md
cmp .hexaemeron/runbook.md docs/shoggoth-public-front-door-runbook.md
work="$(mktemp -d)"
python3 docs/design/build_shoggoth_front_door_design_evidence.py --out "$work"
cmp .hexaemeron/design-evidence.json "$work/design-evidence.json"
for f in .hexaemeron/reports/*.json; do cmp "$f" "$work/reports/$(basename "$f")"; done
cmp .hexaemeron/design-evidence.json docs/shoggoth-public-front-door-design-evidence.json
for f in .hexaemeron/reports/*.json; do cmp "$f" "docs/reports/$(basename "$f")"; done
python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py \
  docs/shoggoth-public-front-door-design-evidence.json --transition design-lock
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py \
  --study docs/shoggoth-public-front-door-study.md \
  --design-evidence docs/shoggoth-public-front-door-design-evidence.json \
  --repo-root .
python3 -m unittest tests.test_shoggoth_topology -v
python3 scripts/run_checks.py --plan
python3 scripts/run_checks.py --full --jobs 6 --report .hexaemeron/run-checks-step-1.json
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

Each command exits 0, and the Horos output is read rather than discarded.

Complete replacement Files: Create
`docs/shoggoth-public-front-door-study.md`,
`docs/shoggoth-public-front-door-runbook.md`,
`docs/shoggoth-public-front-door-design-evidence.json`,
`docs/design/build_shoggoth_front_door_design_evidence.py`, the 24 reports
under `docs/reports/`,
`docs/decisions/drafts/govern-real-data-demonstrations-separately.md`,
`scripts/shoggoth_topology.py`, `tests/test_shoggoth_topology.py`, and four
specimens under `tests/fixtures/shoggoth-topology/`. Change
`tests/check-map-v1.json`. Permit `.horos/boundary.json` and
`.horos/candidates.json` only when a deterministic Horos scan whose output was
read changes them. Warden alone may append
`audit/rounds/fiat-shoggoth-front-door-derived.md` and regenerate its
`.synopsis.md` companion.

Complete replacement Disciplines: phylax: run against
`scripts/shoggoth_topology.py` and
`docs/design/build_shoggoth_front_door_design_evidence.py`, because both take
repository paths and JSON as bounded untrusted input. ephoros: run against the
same two files; this step adds no unattended operation, so the expected result
is a clean exit rather than new instrumentation. hypomnema: run the ordinary
walk against `docs/shoggoth-public-front-door-study.md`,
`docs/shoggoth-public-front-door-runbook.md`, and
`docs/decisions/drafts/govern-real-data-demonstrations-separately.md`, whose
relative links must resolve from their own directories, and run study mode
against the study and committed design evidence to prove the selected
candidate's one standing record. metron: none, because discovery agreement is
a correctness fact rather than a speed claim. elenchus: the malformed,
symlinked and new-plugin specimens guard each refusal and the derivation
itself.

**Why.** Step 1 ships the study, so Hypomnema requires the selected design to
point at a standing record before the step is receipted. The earlier exit ran
only the ordinary documentation walk and left that join unchecked. Current
`main` also assigned the study's former ADR number to another decision. This
replacement admits the correctly numbered record, checks the bridge explicitly
and leaves the topology boundary unchanged.

**Steps touched.** Step 1.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5:
entry holds; exit holds. Step 6: entry holds; exit broken.

### Amendment -- 2026-09-04

**What changed.** Complete replacement Exit: The joined proving path runs
clean from a fresh clone of the run branch, in this order, with network denied:

```bash
python3 scripts/check_public_front_door.py --root .
python3 scripts/demonstrations.py check --root .
python3 scripts/demonstrations.py run --public-set \
  --report .hexaemeron/reports/public-set-step-6.json
python3 scripts/run_checks.py --full --jobs 6 --report .hexaemeron/run-checks-step-6.json
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

Each command exits 0. The accepted per-skill-ledger decision already exists at
`docs/decisions/drafts/govern-real-data-demonstrations-separately.md` from
step 1. Two further decision records land:
`docs/decisions/drafts/keep-the-root-readme-as-a-front-door.md` and
`docs/decisions/drafts/derive-topology-counts-from-the-tree.md`, the last
naming commit `67a01a6c` as the worked example of the failure it prevents and
recording the pinned-specimen exception. An end-to-end test proves the joined
relation rather than the parts: changing one demonstration record's status from
`real-data` to `mixed` makes the front-door check fail on the card that binds
it, and restoring it makes the check pass. A second end-to-end test adds a
nineteenth plugin to a scratch tree and proves that exactly the derived numbers
move, that the front-door check still passes once prose is regenerated from
discovery, and that no literal needed editing. The committed
`.horos/boundary.json` matches the delivered tree, with the scan output read
rather than discarded. Prove the exit with the commands above plus:

```bash
python3 -m unittest tests.test_joined_front_door -v
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs/decisions/drafts/govern-real-data-demonstrations-separately.md docs/decisions/drafts/keep-the-root-readme-as-a-front-door.md docs/decisions/drafts/derive-topology-counts-from-the-tree.md
```

Complete replacement Files: Create
`docs/decisions/drafts/keep-the-root-readme-as-a-front-door.md`,
`docs/decisions/drafts/derive-topology-counts-from-the-tree.md`, and
`tests/test_joined_front_door.py`. Change `tests/check-map-v1.json` and, only
if the joined proof exposes a defect, `scripts/check_public_front_door.py`,
`scripts/demonstrations.py` or `scripts/shoggoth_topology.py`. Permit the
generated Horos files named in Step 1. Change no `EVOLUTION.md`.

**Why.** The study's former ADR-068 through ADR-070 paths now name unrelated
records on current `main`. The selected design's record moved to step 1 so the
study bridge can resolve when the study ships; the other two decisions keep
their original Step 6 ownership under the next collision-free numbers.

**Steps touched.** Step 6.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5:
entry holds; exit holds. Step 6: entry holds; exit holds.
