# Runbook: restore the Shoggoth public front door and demo frontier

This runbook is derived from the receipted study at SHA-256
`d96c4b1d669e4fcda9e5b339a6b1be210c079c63e597cd5021fcf24e1f7cace7`.
The repository starts at
`a2b634d8e039af988bf30c8316defccf70071d8d`. Use CPython `3.14.6` from
`.python-version`. The selected construction is the per-skill demonstration
ledger. Nothing in this run may add a field to `EVOLUTION.md`, change a held
behaviour job, or treat an unfiled demonstration job as a GitHub issue.

```design-lock
schema | protasis-design-evidence/v1
sha256 | 252bb05b83662a9b88c04f5f54c0e9f65dbd8b1a7cd902d8c33127c719c73d25
candidate | per-skill-demo-ledger
```

There is no `version-relations` block. The accepted design keeps every current
`EVOLUTION.md` byte and frontier digest unchanged. Demonstration versions and
jobs live only in the new adjacent ledgers.

Build order is `topology`, `demo-ledgers`, `demo-runner`, `front-door`,
`public-surface`, then `joined-proof`. Each item depends on every item before
it. Each step is one independently green pull request and may assume only its
controller-supplied entry head plus the receipted study, runbook, and immutable
design record.

Always use the pinned interpreter, run the source-bound tests before an
implementation receipt, run Imprimatur on changed prose, preserve the external
human contributor identity rule, and finish with `git diff --check`. Ask before
adding a dependency, changing CI workflow behaviour, enabling network access,
changing a public interface outside this runbook, filing or editing an issue,
or touching any `EVOLUTION.md`. Never edit historical audits, ADR histories,
specimens, content-addressed releases, or the ignored portable runtime. Never
run `gh issue create`, close an issue, change a label, or advance either a held
behaviour job or a demonstration job during this run. A later authorised queue
operation may consume the policy this run ships.

## Step 1: Commit the design boundary and scaffold checked topology

**Goal.** Put the receipted specification in stable repository paths and give
later steps one checked discovery function for the 17 plugins and 26 governed
skills.

**Entry.** The controller-created run branch at
`a2b634d8e039af988bf30c8316defccf70071d8d`; the study receipt above; the
design record at SHA-256
`252bb05b83662a9b88c04f5f54c0e9f65dbd8b1a7cd902d8c33127c719c73d25`;
an empty tracked diff; and the existing root and Hexaemeron suites green.

**Exit.** `docs/shoggoth-public-front-door-study.md` is byte-identical to the
receipted study and `docs/shoggoth-public-front-door-runbook.md` is
byte-identical to this runbook. `scripts/shoggoth_topology.py` reads the two
marketplace manifests and discovers governed directories from `EVOLUTION.md`
without following symlinks. It returns 17 plugin ids, 26 governed skill ids,
17 canonical or domain ids, and nine phase ids at the entry tree. It rejects a
duplicate id, a manifest disagreement, a skill without its canonical
`SKILL.md`, or a path outside `plugins/`. The root check graph owns the new
module and tests. `.python-version`, `pyproject.toml`, `LICENSE`, and
`.github/workflows/plugins.yml` remain unchanged. Prove the exit with:

```bash
cmp .hexaemeron/study.md docs/shoggoth-public-front-door-study.md
cmp .hexaemeron/runbook.md docs/shoggoth-public-front-door-runbook.md
python3 -m unittest tests.test_shoggoth_topology -v
python3 scripts/run_checks.py --plan
python3 scripts/run_checks.py
git diff --check
```

**Files.** Create `docs/shoggoth-public-front-door-study.md`,
`docs/shoggoth-public-front-door-runbook.md`, `scripts/shoggoth_topology.py`,
`tests/test_shoggoth_topology.py`, and
`tests/fixtures/shoggoth-topology/valid-17-26.json`,
`tests/fixtures/shoggoth-topology/duplicate-plugin.json`,
`tests/fixtures/shoggoth-topology/missing-skill.json`, and
`tests/fixtures/shoggoth-topology/unexpected-phase.json`. Change
`tests/check-map-v1.json`. Permit `.horos/boundary.json` and
`.horos/candidates.json` only if a deterministic Horos scan changes them.
Warden alone may append
`audit/rounds/fiat-restore-the-shoggoth-public-front-door-and-demo.md` and
regenerate its `.synopsis.md` companion.

**Boundaries.** The inputs are repository-relative manifest and file paths.
The reader uses bounded regular-file reads, rejects symlinks and duplicate
keys, sorts ids before comparison, and opens no socket or subprocess. The four
fixture JSON files are the only synthetic topology specimens. The live tree is
the integration specimen.

**Risks.** Review `count-drift`, `historical-record-rewrite`, and
`generated-copy-drift`. All other study risk ids are not applicable because
this step neither writes public claims nor executes demonstrations.

**Contracts.** Apply `plugins/hexaemeron/skills/protasis/SKILL.md` to the two
tracked specification copies, `plugins/hexaemeron/skills/phylax/SKILL.md` to
the path reader, `plugins/hexaemeron/skills/elenchus/SKILL.md` to any discovered
failure, and `plugins/hexaemeron/skills/hypomnema/SKILL.md` to the stable spec
homes.

**Tests.** The valid specimen contains exactly 17 plugins and 26 skills. The
three invalid specimens each fail for their named cause, and a temporary-tree
case proves a symlinked skill is refused. Run the commands in Exit and record
observed counts. The audit-fix runner is
`python3 tests/run_tests.py --elenchus-report {report}`; its format is
`unittest-json-v1`, its expected schema is `elenchus.unittest.v1`, and its
fresh report path is `.elenchus/shoggoth-front-door-step-1.json`. The
`{report}` placeholder occurs exactly once.

**Disciplines.** phylax: repository paths and JSON are bounded untrusted
inputs. ephoros: none, because this step adds no unattended operation.
metron: none, because discovery counts are correctness facts rather than a
speed claim. elenchus: malformed and symlinked topology cases guard each
refusal. hypomnema: the tracked study and runbook preserve the accepted design
boundary.

## Step 2: Govern one demonstration ledger per skill

**Goal.** Add the independent demonstration contract, all 26 local ledgers,
and a read-only demo-frontier selection mode without changing the behaviour
frontier.

**Entry.** The signed, audited Step 1 head supplied by the controller; the two
tracked specification files still match their receipts; discovery returns
17 plugins and 26 governed skills; and no `EVOLUTION.md` differs from
`a2b634d8e039af988bf30c8316defccf70071d8d`.

**Exit.** `plugins/hexaemeron/skills/DEMONSTRATIONS.md` defines the closed
`shoggoth-demonstration/v1` record, independent demonstration version and
history digest, the five accepted status values, one current record, and one
next demonstration job. `scripts/demonstrations.py check --root .` discovers
the same 26 directories as `scripts/shoggoth_topology.py` and accepts exactly
one `DEMONSTRATION.md` beside every `EVOLUTION.md`. Each record binds its skill,
status, material source classes, byte digests or chain anchor, network policy,
argv arrays, expected observations, public claim id, non-claim, timeout, and
frontier state. Berean is `mixed`, Synkrisis is `constructed`, and Anamnesis,
Lazarus, and Alexandria are `real-data`; every other status follows only from
evidence in that skill's current tree.

The Kronos contract gains an explicit demo-lane mode that reads only
`DEMONSTRATION.md`. Default and phase-only modes continue to read only
`EVOLUTION.md`. The demo mode may rank and print an eligible job, but it does
not file an issue, dispatch Fiat, advance either ledger, reuse a behaviour
issue without matching acceptance, or write `.kronos/` unless the user later
authorises the corresponding existing Kronos operation. `{skill}-demo` and
`demo-frontier` become governed title and label conventions, not evidence that
an issue exists. ADR-068 records the separate lane, co-delivery rule, and issue
reuse rule. The behaviour ledgers remain byte-identical to the entry base.
Prove the exit with:

```bash
python3 scripts/demonstrations.py check --root .
python3 scripts/demonstrations.py frontier --root . --lane demo --dry-run
python3 -m unittest tests.test_demonstrations -v
python3 -m unittest plugins.hexaemeron.tests.test_kronos_scoreboard -v
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
git diff --exit-code a2b634d8e039af988bf30c8316defccf70071d8d -- ':(glob)plugins/**/EVOLUTION.md'
python3 scripts/run_checks.py
git diff --check
```

**Files.** Create `plugins/hexaemeron/skills/DEMONSTRATIONS.md`,
`scripts/demonstrations.py`, `tests/test_demonstrations.py`,
`tests/fixtures/demonstrations/valid-ledger.md`,
`tests/fixtures/demonstrations/duplicate-key.md`,
`tests/fixtures/demonstrations/unsafe-argv.md`,
`tests/fixtures/demonstrations/missing-source.md`,
`tests/fixtures/demonstrations/mixed-as-real.md`, and
`tests/fixtures/demonstrations/duplicate-job.md`. Create these exact ledgers:

- `plugins/alexandria/skills/alexandria/DEMONSTRATION.md`
- `plugins/anamnesis/skills/anamnesis/DEMONSTRATION.md`
- `plugins/ariadne/skills/ariadne/DEMONSTRATION.md`
- `plugins/berean/skills/berean/DEMONSTRATION.md`
- `plugins/brevitas/skills/brevitas/DEMONSTRATION.md`
- `plugins/hermes/skills/hermes/DEMONSTRATION.md`
- `plugins/hexaemeron/skills/elenchus/DEMONSTRATION.md`
- `plugins/hexaemeron/skills/ephoros/DEMONSTRATION.md`
- `plugins/hexaemeron/skills/fiat/DEMONSTRATION.md`
- `plugins/hexaemeron/skills/hypomnema/DEMONSTRATION.md`
- `plugins/hexaemeron/skills/imprimatur/DEMONSTRATION.md`
- `plugins/hexaemeron/skills/kronos/DEMONSTRATION.md`
- `plugins/hexaemeron/skills/metron/DEMONSTRATION.md`
- `plugins/hexaemeron/skills/phylax/DEMONSTRATION.md`
- `plugins/hexaemeron/skills/protasis/DEMONSTRATION.md`
- `plugins/hexaemeron/skills/vulgate/DEMONSTRATION.md`
- `plugins/homologia/skills/homologia/DEMONSTRATION.md`
- `plugins/horos/skills/horos/DEMONSTRATION.md`
- `plugins/janus/skills/janus/DEMONSTRATION.md`
- `plugins/lazarus/skills/lazarus/DEMONSTRATION.md`
- `plugins/lemma/skills/lemma/DEMONSTRATION.md`
- `plugins/pandects/skills/pandects/DEMONSTRATION.md`
- `plugins/probitas/skills/probitas/DEMONSTRATION.md`
- `plugins/sapheneia/skills/sapheneia/DEMONSTRATION.md`
- `plugins/synkrisis/skills/synkrisis/DEMONSTRATION.md`
- `plugins/tabularium/skills/tabularium/DEMONSTRATION.md`

Change `AGENTS.md`, `plugins/hexaemeron/AGENTS.md`,
`plugins/hexaemeron/skills/kronos/SKILL.md`,
`plugins/hexaemeron/skills/kronos/scripts/kronos.py`,
`plugins/hexaemeron/tests/test_kronos_scoreboard.py`,
`docs/decisions/ADR-068-govern-real-data-demonstrations-separately.md`,
`tests/promise_machine_coverage.json`, and `tests/check-map-v1.json`. Permit the
same generated Horos and Warden files named in Step 1. Do not change any
`EVOLUTION.md`, marketplace package version, or
`.agents/skills/promise-machine/runtime/` path.

**Boundaries.** Ledger Markdown and its fenced JSON are untrusted input. Check
mode performs bounded, no-follow, duplicate-key-rejecting reads and starts no
command. Frontier mode is read-only, sorts the complete eligible set, refuses
an unfiled job presented as a URL, and emits no GitHub request. The behaviour
ledger is a neighbouring source, never a write destination.

**Risks.** Review `claim-without-demo`, `demo-class-inflation`, `source-drift`,
`frontier-lane-collision`, `count-drift`, `pending-member-overclaim`,
`queue-duplication`, `demo-skip-as-pass`, and `historical-record-rewrite`.

**Contracts.** Apply `PROMISE_MACHINE.md`,
`plugins/hexaemeron/skills/kronos/SKILL.md`,
`plugins/hexaemeron/skills/phylax/SKILL.md`,
`plugins/hexaemeron/skills/elenchus/SKILL.md`, and
`plugins/hexaemeron/skills/hypomnema/SKILL.md`. ADR-068 is the durable policy
home; each `DEMONSTRATION.md` owns only its skill's evidence and next demo job.

**Tests.** Assert exact discovery parity at 26, all five status values, closed
field sets, canonical ordering, digest recomputation, independent frontier
digests, one owner hop, and refusal of missing, duplicate, symlinked,
oversized, malformed, unsafe-argv, inflated-status, or duplicate-issue input.
Assert default Kronos reads only `EVOLUTION.md`, demo-lane mode reads only
`DEMONSTRATION.md`, and `--dry-run` cannot mutate Git, `.kronos/`, or GitHub.
Run the commands in Exit. The audit-fix runner is
`python3 tests/run_tests.py --elenchus-report {report}`; its format is
`unittest-json-v1`, its expected schema is `elenchus.unittest.v1`, and its
fresh report path is `.elenchus/shoggoth-front-door-step-2.json`.

**Disciplines.** phylax: ledgers, paths, JSON, and issue-shaped strings are
untrusted and bounded. ephoros: rank output states the lane, complete candidate
count, selected skill, record digest, and read-only result; no persistent
telemetry is added. metron: none, because no performance claim is made.
elenchus: every malformed-ledger and cross-lane specimen must fail on the
entry implementation and pass after its cause is guarded. hypomnema: ADR-068
and the suite contract own the separate-lane decision while local ledgers own
skill facts.

## Step 3: Run the three real-data demonstrations offline

**Goal.** Execute Anamnesis, Lazarus, and Alexandria through one bounded
offline runner and emit checkable reports for the three public claims.

**Entry.** The signed, audited Step 2 head supplied by the controller;
`scripts/demonstrations.py check --root .` is green; all 26 ledgers are present;
the three selected records are `real-data`; and the report paths named below do
not exist.

**Exit.** `scripts/demonstrations.py run` accepts only a checked record or the
closed root demo set. It verifies every declared source digest or chain anchor
before execution, expands only its reserved private-work token inside argv
elements, never invokes a shell, strips credential and Git environment keys,
denies sockets by default, bounds each command by its record timeout, caps
stdout and stderr, tears down the process group, and atomically writes one
`shoggoth-demonstration-report/v1` object to a new caller-selected path.

Anamnesis rebuilds the committed pilot twice from real public audit records
and verifies the Elenchus and Synkrisis projections. Lazarus reconstructs 224
contiguous Ethereum mainnet receipts at block `0xc7da16`, verifies target
index `0xbf`, 110 target logs, and the exact five-log projection. Its private
temporary root removes the macOS `/var` versus `/private/var` alias without
weakening path confinement. Alexandria rebuilds `credit-history-v0`, verifies
522 events and 31 observations, and checks the 11-event Clearpool query and 11
Probitas records. Each report repeats the ledger's non-claim and cannot promote
source completeness, canonical-chain finality, finding truth, remedy
correctness, protocol safety, or underwriting merit. The three commands finish
within the aggregate 600,000 millisecond ceiling. Prove the exit with:

```bash
python3 scripts/demonstrations.py check --root .
python3 -m unittest tests.test_demonstrations -v
python3 -m unittest discover -s plugins/anamnesis/tests -t plugins/anamnesis
python3 -m unittest discover -s plugins/lazarus/tests -t plugins/lazarus
python3 -m unittest discover -s plugins/alexandria/tests -t plugins/alexandria
python3 scripts/demonstrations.py run --showcase --report .hexaemeron/reports/showcase-step-3.json
python3 scripts/run_checks.py
git diff --check
```

**Files.** Change `scripts/demonstrations.py`,
`tests/test_demonstrations.py`,
`plugins/anamnesis/skills/anamnesis/DEMONSTRATION.md`,
`plugins/lazarus/skills/lazarus/DEMONSTRATION.md`, and
`plugins/alexandria/skills/alexandria/DEMONSTRATION.md`. Create
`tests/fixtures/demonstrations/network-attempt.py`,
`tests/fixtures/demonstrations/oversized-output.py`,
`tests/fixtures/demonstrations/timeout.py`,
`tests/fixtures/demonstrations/partial-report.json`, and
`tests/fixtures/demonstrations/stale-source.md`. Permit the generated Horos and
Warden files named in Step 1. The execution report stays under
`.hexaemeron/reports/` and is never committed.

**Boundaries.** The runner crosses record, source-file, subprocess, temporary
filesystem, optional-network, and report-publication boundaries. The three
committed examples are read-only sources. The runner creates one private
worktree below a resolved caller-owned root and refuses an existing report,
symlink, non-regular source, unknown token, shell string, network request,
timeout, output overflow, unexpected observation, or partial child result.

**Risks.** Review `claim-without-demo`, `demo-class-inflation`, `source-drift`,
`external-data-egress`, `subprocess-execution`, `partial-demo-output`,
`demo-skip-as-pass`, and `real-data-nonclaim-loss`.

**Contracts.** Apply `plugins/hexaemeron/skills/phylax/SKILL.md` to input,
subprocess, network, and output controls;
`plugins/hexaemeron/skills/ephoros/SKILL.md` to the closed event and report
fields; `plugins/hexaemeron/skills/metron/SKILL.md` to the 600,000 millisecond
ceiling; and `plugins/hexaemeron/skills/elenchus/SKILL.md` to every reproduced
runner failure. The three canonical skill contracts continue to own what their
results mean.

**Tests.** Test exact successful observations for all three demos and parent-red
cases for the `/var` alias, stale digest, symlink, duplicate key, unknown work
token, shell-shaped argv, environment leak, socket attempt, timeout, output
cap, nonzero child, incomplete expected observation, existing report, and
interrupted atomic write. Run each plugin suite and the commands in Exit. The
audit-fix runner is `python3 tests/run_tests.py --elenchus-report {report}`;
its format is `unittest-json-v1`, its expected schema is
`elenchus.unittest.v1`, and its fresh report path is
`.elenchus/shoggoth-front-door-step-3.json`.

**Disciplines.** phylax: this step opens the declared source, subprocess,
network-refusal, temporary-path, and report boundaries. ephoros: selected,
started, verified, refused, duration, and peak-RSS records answer the study's
on-call questions without retaining source bytes or secrets. metron: the same
three-demo command is measured against the 600,000 millisecond aggregate
ceiling. elenchus: each runner refusal has a minimal parent-red specimen and a
fixed-tree guard. hypomnema: none, because Step 2 already records the durable
format and lane decisions and this step supplies evidence under them.

## Step 4: Restore the root front door and authoritative counts

**Goal.** Replace the root catalogue-first README with the short, self-aware
front door whose claims bind the three checked demonstration records.

**Entry.** The signed, audited Step 3 head supplied by the controller; the
three real-data reports pass; their ledger digests are final for this run; and
the Step 1 discovery still returns 17 plugins and 26 governed skills.

**Exit.** `README.md` is no more than 1,400 words. Its opening explanation is
no more than 150 words, `## SO, YOU WANT TO BUILD GOD?` is present, and the
external contribution heading begins within the first 220 words. It retains
the line `Ask the Atlas for a number. Pick your harness. Finish what you
start.` and at least one other short self-aware line before technical detail.
Contribution and `## WHAT CAN IT DO?` precede the Promise Machine mechanism and
the first catalogue link. The README has no complete roster, no repeated link
target, no Anamnesis portrait, no stale 16/25 count, and no lower-case ATX
heading. It states 17 canonical or domain agents plus nine phase agents, 26
governed first-party agents in total, while keeping workers and vendored skills
outside that count. Dokimasia appears once as pending, with no capability,
route, or member count.

The three cards bind the Anamnesis, Lazarus, and Alexandria skill id, public
claim id, and exact demonstration-record digest through hidden markers. Each
card names one preserved source, one observed result, one command or governed
runner invocation, and the record's non-claim. The Protasis imbalance is gone
because the root no longer carries individual engineering-agent essays.
`scripts/check_public_front_door.py --root . --front-door-only` checks all of
these relations, and `scripts/demonstrations.py check-public --root .` refuses
a missing, stale, downgraded, mixed, constructed, or failed record. ADR-069
records the root information architecture. Prove the exit with:

```bash
python3 scripts/check_public_front_door.py --root . --front-door-only
python3 scripts/demonstrations.py check-public --root .
python3 -m unittest tests.test_public_front_door tests.test_marketplace_prose -v
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py README.md
python3 scripts/run_checks.py
git diff --check
```

**Files.** Change `README.md`, `tests/test_marketplace_prose.py`, and
`tests/check-map-v1.json`. Create `scripts/check_public_front_door.py`,
`tests/test_public_front_door.py`,
`docs/decisions/ADR-069-keep-the-root-readme-as-a-front-door.md`, and these
exact specimens:
`tests/fixtures/public-front-door/valid/README.md`,
`tests/fixtures/public-front-door/late-contribution/README.md`,
`tests/fixtures/public-front-door/duplicate-links/README.md`,
`tests/fixtures/public-front-door/oversized/README.md`,
`tests/fixtures/public-front-door/unexpected-member-image/README.md`,
`tests/fixtures/public-front-door/lowercase-heading/README.md`,
`tests/fixtures/public-front-door/stale-count/README.md`, and
`tests/fixtures/public-front-door/dokimasia-overclaim/README.md`. Permit the
generated Horos and Warden files named in Step 1.

**Boundaries.** The checker reads bounded Markdown, links, image targets, and
hidden claim markers without fetching them. It resolves only repository-local
ledger paths through the Step 1 discovery map, recomputes digests, and treats
voice as human-authored prose outside its verdict. Historical documents and
plugin portraits are outside this step's write set.

**Risks.** Review `claim-without-demo`, `count-drift`,
`front-door-regression`, `pending-member-overclaim`,
`portrait-inconsistency`, `real-data-nonclaim-loss`, and
`historical-record-rewrite`.

**Contracts.** Apply `SHOGGOTH.md` for collective identity and portrait
placement, `PROMISE_MACHINE.md` for authority boundaries,
`plugins/hexaemeron/skills/imprimatur/SKILL.md` and
`plugins/hexaemeron/skills/vulgate/SKILL.md` for the public wording,
`plugins/brevitas/skills/brevitas/SKILL.md` for structure, and
`plugins/hexaemeron/skills/hypomnema/SKILL.md` for ADR-069.

**Tests.** The valid fixture passes. Each invalid fixture fails only its named
relation. Add direct tests for the 150, 220, and 1,400 word boundaries, repeated
fragment-normalised targets, all-caps ATX headings, catalogue ordering, hidden
marker digest drift, 17/26 discovery, the absent root Anamnesis image, and the
bounded Dokimasia note. Run the commands in Exit. The audit-fix runner is
`python3 tests/run_tests.py --elenchus-report {report}`; its format is
`unittest-json-v1`, its expected schema is `elenchus.unittest.v1`, and its
fresh report path is `.elenchus/shoggoth-front-door-step-4.json`.

**Disciplines.** phylax: bounded local Markdown and claim-marker paths are the
only untrusted inputs; no network or command execution occurs. ephoros: none,
because this step adds no unattended operation. metron: none, because word and
ordering limits are content contracts, not performance claims. elenchus: every
current root regression has a focused specimen that fails without the repair.
hypomnema: ADR-069 owns the durable front-door role and budgets.

## Step 5: Reconcile the maintained public surface and derived guide

**Goal.** Apply the agreed house style and current facts across every maintained
human entry surface, regenerate the contributor PDF, and preserve the one deep
technical catalogue.

**Entry.** The signed, audited Step 4 head supplied by the controller; the root
front-door checks pass; ADR-068 and ADR-069 exist; all 26 demonstration records
check; and no historical evidence or generated portable runtime has changed.

**Exit.** Every ATX heading in the maintained public surface is all caps. The
complete 26-agent technical catalogue appears once in `FUTUREPROOFING.md` and
not in the root README. Current count statements derive from the 17/26
discovery result. `SHOGGOTH.md` keeps the collective portrait rule.
`plugins/anamnesis/README.md` keeps its contextual portrait and character
section, removes the obsolete source-admission-only claim, and describes the
shipped whole seed path without strengthening its audit boundaries. The root
contains no Anamnesis portrait. The single Dokimasia note remains pending and
unrouted. The Promise Machine router, contributor guide, installation guide,
Fiat explanation, technical explanation, and all 17 plugin landing pages agree
on current topology and do not repeat the root's catalogue.

`scripts/build_contributor_guide.py` deterministically rebuilds
`docs/pdf/how-to-help-shoggoth.pdf` from the reconciled source. PDF text,
links, five-page count, and binary signature pass. A fixed-argv local renderer
in `scripts/render_public_surface.py` renders the root README and all five PDF
pages without network access. A human inspects the six PNGs for hierarchy,
overflow, missing images, anomalous member art, and broken composition, then
the script binds their digests and the source/PDF digests in one
`shoggoth-visual-review/v1` report. The report checker proves completeness and
current digests without claiming that a machine judged the pictures. The full
public checker passes. Prove the exit with:

```bash
python3 scripts/build_contributor_guide.py
python3 scripts/check_public_front_door.py --root .
python3 scripts/demonstrations.py check-public --root .
python3 -m unittest tests.test_public_front_door tests.test_public_surface_render tests.test_marketplace_prose tests.test_shoggoth_identity tests.test_promise_machine_contract -v
python3 scripts/render_public_surface.py render --root . --out .hexaemeron/render/public-surface --report .hexaemeron/reports/public-surface-visual.json
python3 scripts/render_public_surface.py check --root . --report .hexaemeron/reports/public-surface-visual.json
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py README.md INSTALL.md FUTUREPROOFING.md SHOGGOTH.md PROMISE_MACHINE.md docs/how-to-help-shoggoth.md docs/fiat-in-plain-english.md docs/the-promise-machine-explained-properly.md plugins/*/README.md
for prose in README.md INSTALL.md FUTUREPROOFING.md SHOGGOTH.md PROMISE_MACHINE.md docs/how-to-help-shoggoth.md docs/fiat-in-plain-english.md docs/the-promise-machine-explained-properly.md plugins/*/README.md; do
  python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py "$prose"
done
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs
python3 plugins/horos/skills/horos/scripts/horos.py scan . --write
python3 scripts/run_checks.py
git diff --check
```

**Files.** Change `INSTALL.md`, `FUTUREPROOFING.md`, `SHOGGOTH.md`,
`PROMISE_MACHINE.md`, `.agents/skills/promise-machine/SKILL.md`,
`docs/how-to-help-shoggoth.md`, `docs/fiat-in-plain-english.md`,
`docs/the-promise-machine-explained-properly.md`,
`scripts/build_contributor_guide.py`, `docs/pdf/how-to-help-shoggoth.pdf`,
`tests/test_marketplace_prose.py`, `tests/test_shoggoth_identity.py`,
`tests/test_promise_machine_contract.py`, and these 17 landing pages:

- `plugins/alexandria/README.md`
- `plugins/anamnesis/README.md`
- `plugins/ariadne/README.md`
- `plugins/berean/README.md`
- `plugins/brevitas/README.md`
- `plugins/hermes/README.md`
- `plugins/hexaemeron/README.md`
- `plugins/homologia/README.md`
- `plugins/horos/README.md`
- `plugins/janus/README.md`
- `plugins/lazarus/README.md`
- `plugins/lemma/README.md`
- `plugins/pandects/README.md`
- `plugins/probitas/README.md`
- `plugins/sapheneia/README.md`
- `plugins/synkrisis/README.md`
- `plugins/tabularium/README.md`

Create `scripts/render_public_surface.py`,
`tests/test_public_surface_render.py`,
`tests/fixtures/public-front-door/visual-stale-digest.json`, and
`tests/fixtures/public-front-door/visual-missing-page.json`. Regenerate
`.horos/boundary.json` and `.horos/candidates.json` only through Horos. Permit
the Warden files named in Step 1. The render and review report stays under
`.hexaemeron/`. Do not create or edit
`.agents/skills/promise-machine/runtime/`.

**Boundaries.** Maintained Markdown and one PDF are the mutable public inputs.
Agent contracts change only where they own the 17/26 fact or demo-lane route;
their headings are not restyled. ADRs, audits, old studies, runbooks,
specimens, and releases remain read-only. The renderer accepts fixed local
paths, invokes only the existing browser and Poppler executables by argv,
denies network, bounds outputs, and refuses an existing or symlinked target.
The human inspection report records exact digests and page identities.

**Risks.** Review `count-drift`, `generated-copy-drift`,
`front-door-regression`, `pending-member-overclaim`,
`portrait-inconsistency`, `historical-record-rewrite`, and
`visual-surface-drift`.

**Contracts.** Apply `SHOGGOTH.md`, `PROMISE_MACHINE.md`, every affected
plugin `AGENTS.md`, `plugins/hexaemeron/skills/imprimatur/SKILL.md`,
`plugins/hexaemeron/skills/vulgate/SKILL.md`,
`plugins/brevitas/skills/brevitas/SKILL.md`,
`plugins/hexaemeron/skills/hypomnema/SKILL.md`, and
`plugins/horos/skills/horos/SKILL.md`. The contributor builder remains the sole
source of its PDF bytes.

**Tests.** Add exact maintained-surface inventory, heading-case, topology,
catalogue-location, image-placement, Dokimasia, Anamnesis-current-state, PDF
text/link/page, deterministic rebuild, renderer containment, stale-report, and
missing-page cases. Inspect every rendered PNG before the report is accepted.
Run the commands in Exit and record the PDF, PNG, and visual-report digests.
The audit-fix runner is `python3 tests/run_tests.py --elenchus-report {report}`;
its format is `unittest-json-v1`, its expected schema is
`elenchus.unittest.v1`, and its fresh report path is
`.elenchus/shoggoth-front-door-step-5.json`.

**Disciplines.** phylax: local renderer argv, input paths, binary reads, and
output confinement are bounded. ephoros: renderer and PDF failures name the
source, page, command class, and recovery; no service or persistent telemetry
ships. metron: none, because page and word counts are content limits.
elenchus: current stale headings, counts, Anamnesis wording, portrait placement,
and visual-report drift each get a focused guard. hypomnema: ADR-068, ADR-069,
the canonical identity and Promise Machine contracts, and local member pages
remain the separate decision and fact homes.

## Step 6: Prove the joined public front door and demo path

**Goal.** Demonstrate the complete front-door-to-real-data path, verify the
disposable installation package and visual evidence, and leave one reproducible
proof without committing generated runtime bytes.

**Entry.** The signed, audited Step 5 head supplied by the controller; all
maintained public surfaces and PDF bytes are final; the visual report is
current; `.agents/skills/promise-machine/runtime/` is absent; the final demo and
package report paths below do not exist; and no GitHub issue or held frontier
changed during Steps 1 through 5.

**Exit.** The exact four-command proving path from the study passes on the
assembled tree. The three real-data demonstrations repeat three times within
600,000 milliseconds per complete run, with identical expected observations
and non-claims. A disposable Promise Machine package contains the source-built
runtime manifest and passes the package-focused tests, while the source
checkout still has no generated runtime directory or tracked runtime file.
The visual report still binds the final root and five-page PDF. The full checked
runner, audit-synopsis currency check, Promise Machine checks, boundary lints,
Horos check, prose checks, and diff check pass. The proof document records exact
commit, commands, exit statuses, counts, durations, and artefact digests without
claiming hosted CI, publication, chain finality, corpus completeness, or issue
mutation. Prove the exit with:

```bash
python3 scripts/check_public_front_door.py --root .
python3 scripts/demonstrations.py check --root .
python3 scripts/demonstrations.py run --showcase --report .hexaemeron/reports/showcase.json
python3 scripts/run_checks.py --full
python3 scripts/demonstrations.py run --showcase --repeat 3 --report .hexaemeron/reports/showcase-budget.json
python3 scripts/render_public_surface.py check --root . --report .hexaemeron/reports/public-surface-visual.json
python3 scripts/portable_promise_machine.py package --out .hexaemeron/runtime-package
test -f .hexaemeron/runtime-package/.agents/skills/promise-machine/runtime/MANIFEST.json
python3 -m unittest tests.test_portable_skills tests.test_skills_sh_package -v
test ! -e .agents/skills/promise-machine/runtime
test -z "$(git ls-files -- .agents/skills/promise-machine/runtime)"
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs
python3 plugins/horos/skills/horos/scripts/horos.py check .
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py README.md INSTALL.md FUTUREPROOFING.md SHOGGOTH.md PROMISE_MACHINE.md docs/how-to-help-shoggoth.md docs/fiat-in-plain-english.md docs/the-promise-machine-explained-properly.md docs/shoggoth-public-front-door-proof.md plugins/*/README.md
git diff --check
```

**Files.** Create `docs/shoggoth-public-front-door-proof.md`. Permit only the
generated Horos and Warden files named in Step 1 if their owned checks require
an update. Keep `.hexaemeron/reports/showcase.json`,
`.hexaemeron/reports/showcase-budget.json`,
`.hexaemeron/reports/public-surface-visual.json`, and
`.hexaemeron/runtime-package/` ignored and local. No other product file changes
in this step.

**Boundaries.** This step reads the assembled tracked tree, executes only the
registered offline demonstrations and repository checks, and writes only the
proof plus ignored reports and disposable package. It makes no network request,
uses no credential, and performs no GitHub mutation. Package bytes come only
from `scripts/portable_promise_machine.py`; the checkout runtime path remains
absent.

**Risks.** Recheck every study id: `claim-without-demo`,
`demo-class-inflation`, `source-drift`, `frontier-lane-collision`,
`count-drift`, `generated-copy-drift`, `external-data-egress`,
`subprocess-execution`, `partial-demo-output`, `front-door-regression`,
`pending-member-overclaim`, `portrait-inconsistency`,
`historical-record-rewrite`, `demo-skip-as-pass`,
`real-data-nonclaim-loss`, `queue-duplication`, and
`visual-surface-drift`.

**Contracts.** Apply the selected `plugins/hexaemeron/skills/DEMONSTRATIONS.md`
contract, `PROMISE_MACHINE.md`, `SHOGGOTH.md`, the three demonstrated canonical
skill contracts, and all five discipline contracts cited in the study. The
proof is a Hypomnema current-evidence record, not a release attestation or a
new source of product policy.

**Tests.** Run every command in Exit from fresh report and package paths. The
proof must name observed counts and digests rather than predicted values. The
root and three affected plugin suites must report no skip as execution. The
audit-fix runner is `python3 tests/run_tests.py --elenchus-report {report}`;
its format is `unittest-json-v1`, its expected schema is
`elenchus.unittest.v1`, and its fresh report path is
`.elenchus/shoggoth-front-door-step-6.json`.

**Disciplines.** phylax: the complete offline subprocess, package, report, and
filesystem boundaries are rechecked without network or credentials. ephoros:
the final reports answer selection, start, refusal, duration, result, and
source-binding questions. metron: the repeated three-demo command enforces the
600,000 millisecond ceiling on the pinned runner. elenchus: any final failure
stops delivery and receives a minimal parent-red guard before rerun.
hypomnema: the proof records current evidence while ADR-068, ADR-069, and the
canonical contracts remain the policy homes.

### Amendment -- 2026-08-31

**What changed.** Complete replacement Exit: `docs/shoggoth-public-front-door-study.md`
is byte-identical to the receipted study and
`docs/shoggoth-public-front-door-runbook.md` is byte-identical to this
runbook. `scripts/shoggoth_topology.py` reads the two marketplace manifests
and discovers governed directories from `EVOLUTION.md` without following
symlinks. It returns 17 plugin ids, 26 governed skill ids, 17 canonical or
domain ids, and nine phase ids at the entry tree. It rejects a duplicate id,
a manifest disagreement, a skill without its canonical `SKILL.md`, or a path
outside `plugins/`. The root check graph owns the new module and tests. The
root `AGENTS.md` keeps its exact instruction while the words `Do not publish`
remain contiguous for Sapheneia's publication-boundary guard.
`.python-version`, `pyproject.toml`, `LICENSE`, and
`.github/workflows/plugins.yml` remain unchanged. Prove the exit with
`cmp .hexaemeron/study.md docs/shoggoth-public-front-door-study.md`,
`cmp .hexaemeron/runbook.md docs/shoggoth-public-front-door-runbook.md`,
`python3 -m unittest tests.test_shoggoth_topology -v`,
`python3 scripts/run_checks.py --base a2b634d8e039af988bf30c8316defccf70071d8d --plan`,
`env TMPDIR=/private/tmp python3 scripts/run_checks.py --base a2b634d8e039af988bf30c8316defccf70071d8d`,
and `git diff --check a2b634d8e039af988bf30c8316defccf70071d8d HEAD`, each exiting 0.
Complete replacement Files: Create
`docs/shoggoth-public-front-door-study.md`,
`docs/shoggoth-public-front-door-runbook.md`,
`scripts/shoggoth_topology.py`, `tests/test_shoggoth_topology.py`, and
`tests/fixtures/shoggoth-topology/valid-17-26.json`,
`tests/fixtures/shoggoth-topology/duplicate-plugin.json`,
`tests/fixtures/shoggoth-topology/missing-skill.json`, and
`tests/fixtures/shoggoth-topology/unexpected-phase.json`. Change
`tests/check-map-v1.json`. Reflow only the line break between `Do not` and
`publish` in the root `AGENTS.md`; its words and instruction remain fixed.
Permit `.horos/boundary.json` and `.horos/candidates.json` only if a
deterministic Horos scan changes them. Warden alone may append
`audit/rounds/fiat-restore-the-shoggoth-public-front-door-and-demo.md` and
regenerate its `.synopsis.md` companion. Complete replacement Tests: The
valid specimen contains exactly 17 plugins and 26 skills. The three invalid
specimens each fail for their named cause, and a temporary-tree case proves a
symlinked skill is refused. The Sapheneia publication-boundary test keeps the
same words and passes after the permitted line reflow. Run every command in
the complete replacement Exit under the stated canonical macOS temporary
root and record observed counts. The audit-fix runner remains
`python3 tests/run_tests.py --elenchus-report {report}`; its format is
`unittest-json-v1`, its expected schema is `elenchus.unittest.v1`, and its
fresh report path is `.elenchus/shoggoth-front-door-step-1.json`. The
`{report}` placeholder occurs exactly once.

**Why.** Changing `tests/check-map-v1.json` correctly selected every suite
whose execution authority it controls. The exact entry parent and the signed
Step 1 tree reproduced two inherited failures: Sapheneia expected the fixed
phrase across a Markdown line break, and Lazarus rejected ambient macOS
`TMPDIR=/var/...` because `/var` is a symlink to `/private/var`. The smallest
recovery keeps the check graph intact, preserves the instruction's words, and
runs the same graph below canonical `/private/tmp`; it does not take the
separate Lazarus implementation repair.

**Steps touched.** Step 1.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step
5: entry holds; exit holds. Step 6: entry holds; exit holds.
