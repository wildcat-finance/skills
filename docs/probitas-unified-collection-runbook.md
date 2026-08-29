# Runbook: unified live and archive collection

Derived from `.hexaemeron/study.md`, receipted for run
`fiat/391-unified-live-and-archive-collection` off `main` at
`2b1c5cccca6d688c5d0223d311dd8df177ca5614`. Task issue
[skills#391](https://github.com/wildcat-finance/skills/issues/391).

Four steps, in dependency order. Step 1 scaffolds and commits the
specification. Step 2 makes a coverage row say where it came from while only
one route can still run. Step 3 lets both routes run together. Step 4
demonstrates the union offline and records the generation.

Every step runs both plugin suites and the root suite locally, because neither
`plugins/probitas/tests` nor `plugins/alexandria/tests` appears in any workflow
under `.github/workflows/`. Every audit round in this run owes the three
bundled lint exits, because the `security_suite` receipt is a waiver.

The run's audit record is
`audit/rounds/fiat-391-unified-live-and-archive-collection.md` with its
generated sibling `audit/rounds/fiat-391-unified-live-and-archive-collection.synopsis.md`.
`audit.fold` is true, so each step's fix branch merges into its step branch
before that step's prose phase.

Regenerate, never hand-edit, `.agents/skills/promise-machine/runtime/` and its
`MANIFEST.json`, with `python3 scripts/portable_promise_machine.py sync`
followed by `check`. That mirror covers `scripts`, `skills`, `docs`,
`examples`, `assets` and the three root documents of each plugin; it does not
cover `tests`. Permit `.horos/boundary.json`, `.horos/candidates.json` and
`.horos/census.json` only where the deterministic scan changes them. Any file
outside a step's `Files` list requires a receipted runbook amendment before it
is changed.

## Step 1: Commit the specification and give Probitas an Elenchus runner

**Goal.** Land the study and this runbook as repository documents, amend the
study where deriving the runbook proved one sentence unbuildable, and add the
per-plugin test runner every later step's audit contract names.

**Entry.** The run branch `fiat/391-unified-live-and-archive-collection` at
`2b1c5ccc`, which is `main` at `2b1c5cccca6d688c5d0223d311dd8df177ca5614`, with
the study and runbook receipted and no product file changed.

**Exit.** All of the following hold. Study item 1 named
`plugins/alexandria/examples/credit-history-v0/demo.py` as the home of the
union demonstration; that file is mirrored into
`.agents/skills/promise-machine/runtime/`, which excludes `tests`, so a union
run there would have to read `plugins/probitas/tests/fixtures/` and would break
in the portable copy. One receipted Protasis amendment moves the union
demonstration into Probitas's own suite, keeps the Alexandria demonstration as
the archive-only rebuild check, and records a verdict for every unbuilt step.
`docs/probitas-unified-collection-study.md` and
`docs/probitas-unified-collection-runbook.md` then match the receipted
controller artefacts byte for byte, and
`plugins/probitas/tests/run_tests.py` runs the Probitas suite and writes an
`elenchus.unittest.v1` report to a fresh path below the worktree. Proved by:
`python3 plugins/hexaemeron/skills/fiat/scripts/hexctl.py --dir . amend study --artifact <candidate>` exiting 0,
`cmp -s .hexaemeron/study.md docs/probitas-unified-collection-study.md`,
`cmp -s .hexaemeron/runbook.md docs/probitas-unified-collection-runbook.md`,
`python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/probitas-unified-collection-study.md`,
`python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/probitas-unified-collection-runbook.md`,
`python3 plugins/probitas/tests/run_tests.py --elenchus-report .elenchus/probitas-391-step-1.json` reporting 276 of 276 passed,
`python3 -m unittest discover -s plugins/alexandria/tests -t .`,
`python3 -m unittest discover -s tests`,
`python3 scripts/portable_promise_machine.py sync` then `check`,
`python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/probitas-unified-collection-study.md docs/probitas-unified-collection-runbook.md`,
and `git diff --check`.

**Files.** Create `docs/probitas-unified-collection-study.md`,
`docs/probitas-unified-collection-runbook.md` and
`plugins/probitas/tests/run_tests.py`. Change nothing under
`plugins/probitas/scripts` or `plugins/alexandria`. Regenerate
`.agents/skills/promise-machine/runtime/` and its `MANIFEST.json`. Permit the
three `.horos` JSON files only where the deterministic scan changes them.

**Tests.** No new assertions; the runner is exercised by running it against
the unchanged 276-test suite, and the two `cmp` checks are the step's own
proof. The Elenchus runner contract for any audit repair in this step is
exact: test command
`python3 plugins/probitas/tests/run_tests.py --elenchus-report {report}`;
report format `unittest-json-v1`; expected report schema
`elenchus.unittest.v1`; report file `.elenchus/probitas-391-step-1.json`. The
report path must be fresh. A missing, stale, empty, malformed or
infrastructure-failed report is `inconclusive`, not evidence that a repair is
guarded.

**Disciplines.** phylax: the runner accepts an operator-named report path and
writes a file, which is the one boundary this step opens; it is the audited
Alexandria runner's confinement logic and must keep refusing a path outside
the worktree, an existing target and a non-directory parent. ephoros: none,
the step adds no unattended behaviour beyond the runner's own report, and the
report is the signal. metron: none, no performance claim. elenchus: none, no
failure in hand at entry. hypomnema: the committed study becomes the standing
pointer for the design decision recorded in study item 12, and the amendment
keeps the run's earlier belief readable rather than editing it away.

## Step 2: Every coverage row names its source class

**Goal.** A coverage row states which route produced it and, for an archive
row, which Alexandria releases stand behind it; gate 2 counts rows instead of
collapsing the ones that share a venue; gate 3 admits the new fields; the
renderer prints them; the evidence schema becomes 2.

**Entry.** Step 1's signed, audited, prose-checked branch tip, with the
amended study and this runbook committed and both plugin suites and the root
suite green.

**Exit.** All of the following hold. `Coverage` requires a `source` from the
closed vocabulary `live`, `fixtures`, `archive`, `none` and refuses any other
value at construction, and carries `releases`, which is a sorted
comma-separated list of Alexandria release identities on an archive row and
`None` elsewhere. `Evidence.to_dict` emits `"schema": 2` and both new fields
on every coverage row. `render.load` accepts schema 2 and refuses schema 1 by
name with an instruction to collect again, rather than letting it reach a
gate. `gate_2_coverage` keys rows on the venue-and-source pair, fails a
repeated pair by name, fails a row whose source is absent or outside the
vocabulary, fails an observing archive row that names no release, still
requires every registry venue to hold at least one row, and still requires an
observing row to name a block range. `known_tokens` includes `source` and
`releases`, so a release identity in the rendered table is a permitted figure.
`_coverage` prints a `Source` column after `Status`, keeping the venue in the
first cell so gate 2's table check is unaffected. The adapter route stamps
`live` or `fixtures` from whether a fixture directory was supplied, the
archive route stamps `archive`, and `unchecked_coverage` stamps `none`. Only
one route can still run per invocation, so no venue yet holds two rows.
`docs/example-dossier.md` is regenerated and
`plugins/alexandria/examples/credit-history-v0/expected-probitas.json` carries
the two new digests, with its coverage status counts unchanged at
`checked` 1, `error` 1, `unconfigured` 4, `unimplemented` 9. Proved by:
`python3 plugins/probitas/tests/run_tests.py --elenchus-report .elenchus/probitas-391-step-2.json` passing with at least 290 tests,
`python3 -m unittest discover -s plugins/alexandria/tests -t .`,
`python3 -m unittest discover -s tests`,
`output="$(mktemp -d)/credit-history-v0"; python3 plugins/alexandria/examples/credit-history-v0/demo.py build --output "$output"` then `python3 plugins/alexandria/examples/credit-history-v0/demo.py verify "$output"` both exiting 0,
`python3 scripts/portable_promise_machine.py sync` then `check`,
`python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/probitas/skills/probitas/references/gates.md`,
and `git diff --check`.

**Files.** Change `plugins/probitas/scripts/probitas_lib/evidence.py`,
`plugins/probitas/scripts/probitas_lib/gates.py`,
`plugins/probitas/scripts/probitas_lib/render.py`,
`plugins/probitas/scripts/probitas_lib/adapters/__init__.py`,
`plugins/probitas/scripts/probitas.py`,
`plugins/probitas/tests/test_evidence.py`,
`plugins/probitas/tests/test_gates.py`,
`plugins/probitas/tests/test_render.py`,
`plugins/probitas/tests/test_cli.py`,
`plugins/probitas/tests/test_registry.py`,
`plugins/probitas/docs/example-dossier.md`,
`plugins/probitas/skills/probitas/references/gates.md`,
`plugins/alexandria/examples/credit-history-v0/expected-probitas.json`.
Regenerate `.agents/skills/promise-machine/runtime/` and its `MANIFEST.json`.
Permit the three `.horos` JSON files only where the deterministic scan changes
them.

**Tests.** Extend `test_evidence.py` with the closed source vocabulary, the
refusal of an unknown source, the `releases` field on the wire and the schema
number. Extend `test_gates.py` with a repeated venue-and-source pair failing
gate 2 by name, a missing source failing it, an observing archive row with no
release failing it, two rows for one venue both being counted, and a release
identity in the table passing gate 3. Extend `test_render.py` with the
`Source` column and the venue staying in the first cell. Extend `test_cli.py`
with the emitted schema number and the refusal of a schema-1 file by
`render.load`. Expected count at least 290, from 276. The Elenchus runner
contract for any audit repair in this step is exact: test command
`python3 plugins/probitas/tests/run_tests.py --elenchus-report {report}`;
report format `unittest-json-v1`; expected report schema
`elenchus.unittest.v1`; report file `.elenchus/probitas-391-step-2.json`. The
report path must be fresh. A missing, stale, empty, malformed or
infrastructure-failed report is `inconclusive`, not evidence that a repair is
guarded.

**Disciplines.** phylax: release identities become a rendered field, so
operator-adjacent strings reach a Markdown table cell for the first time since
audit finding S2-R1-01, and the closed vocabulary plus the existing value
sanitiser are the controls. ephoros: the `releases` field is signal three from
study item 8, and this step is where it becomes readable. metron: none, no
performance claim. elenchus: the four refusals in study item 11 each get a
test that fails without its guard, and `coverage-row-collapse` is the concern
the round should reproduce first. hypomnema: the gate contract change belongs
in `references/gates.md`, which is where the gate contract already lives, and
nowhere else.

## Step 3: One collect run gathers both routes

**Goal.** `collect` accepts an Alexandria index together with an adapter route
and writes one evidence file carrying both sets of records, without any
existing invocation starting to reach the network.

**Entry.** Step 2's signed, audited, prose-checked branch tip, with schema 2
emitted, gate 2 keyed on the venue-and-source pair, and all three suites
green.

**Exit.** All of the following hold. The mutually exclusive source group is
gone. `--fixtures` and `--alexandria-index` combine. A new `--live` flag names
the network adapter route; `--live` with `--fixtures` exits 2 and names the
contradiction; `--live` alone names the existing default and changes nothing.
`--alexandria-index` alone still runs no adapter and reaches no network. The
seven rows of the study's route table each hold, exercised by a test. Both
routes' records enter one `Evidence`. Each route contributes coverage rows only
for the venues it observed; a final pass adds one `none` row per venue no
requested route observed, whose note names why each requested route did not
cover it and whose status keeps the existing `unconfigured` and `unimplemented`
distinction. A venue any route observed is not also listed as an unchecked
gap; an `error` row still produces one. The `collect` summary on stderr names
each requested route and its backing. The README, `SKILL.md`, `AGENTS.md` and
`references/venues.md` carry the route table and `--live`. Proved by:
`python3 plugins/probitas/tests/run_tests.py --elenchus-report .elenchus/probitas-391-step-3.json` passing with at least 310 tests,
`python3 -m unittest discover -s plugins/alexandria/tests -t .`,
`python3 -m unittest discover -s tests`,
`output="$(mktemp -d)/credit-history-v0"; python3 plugins/alexandria/examples/credit-history-v0/demo.py build --output "$output"` then `verify` on that output, both exiting 0 and matching the step-2 receipts unchanged,
`python3 scripts/portable_promise_machine.py sync` then `check`,
`python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/probitas/README.md plugins/probitas/AGENTS.md plugins/probitas/skills/probitas/SKILL.md plugins/probitas/skills/probitas/references/venues.md`,
and `git diff --check`.

**Files.** Change `plugins/probitas/scripts/probitas.py`,
`plugins/probitas/scripts/probitas_lib/adapters/__init__.py`,
`plugins/probitas/tests/test_cli.py`,
`plugins/probitas/tests/test_registry.py`,
`plugins/probitas/README.md`, `plugins/probitas/AGENTS.md`,
`plugins/probitas/skills/probitas/SKILL.md`,
`plugins/probitas/skills/probitas/references/venues.md`. Regenerate
`.agents/skills/promise-machine/runtime/` and its `MANIFEST.json`. Permit the
three `.horos` JSON files only where the deterministic scan changes them.

**Tests.** Extend `test_cli.py` with one case per row of the route table,
including the refusal of `--live --fixtures` at exit 2, the union writing
records from both routes into one file, `--alexandria-index` alone making no
adapter call, the route-aware `none` note, and a venue observed by one route
not appearing as a gap. Extend `test_registry.py` with the merge holding when
a venue is observed by both routes, using synthetic coverage rather than a real
index. Expected count at least 310, from at least 290. The Elenchus runner
contract for any audit repair in this step is exact: test command
`python3 plugins/probitas/tests/run_tests.py --elenchus-report {report}`;
report format `unittest-json-v1`; expected report schema
`elenchus.unittest.v1`; report file `.elenchus/probitas-391-step-3.json`. The
report path must be fresh. A missing, stale, empty, malformed or
infrastructure-failed report is `inconclusive`, not evidence that a repair is
guarded.

**Disciplines.** phylax: this step makes the network adapter route reachable in
the same run as the archive route, and `--live` is the control that keeps every
existing invocation reaching exactly what it reached before. ephoros: signals
one and two from study item 8 land here, in the stderr summary and the
route-aware `none` note. metron: none, no performance claim; a union run does
the work of two routes that already run separately. elenchus: the
`unrequested-network` and `gap-double-count` concerns are what a round should
try to reproduce, and the `--live --fixtures` refusal gets a guard test.
hypomnema: the route table is an interface others call, so it goes in the
README, `SKILL.md` and `AGENTS.md` beside the flags rather than in a separate
document.

## Step 4: Demonstrate the union offline and record the generation

**Goal.** Prove the union end to end without a network, then record the
generation on the Probitas ledger and reconcile the counts the documents state.

**Entry.** Step 3's signed, audited, prose-checked branch tip, with the union
available and all three suites green. Re-read `origin/main` immediately before
writing the ledger row and the package versions, because both are repository
global identifiers.

**Exit.** All of the following hold. `plugins/probitas/tests/test_union.py`
builds a disposable Alexandria index offline through `alexandria_lib`, runs
`collect --fixtures tests/fixtures/demo --alexandria-index <index>`, then
`render` and `verify`, and asserts that the evidence carries adapter records
and archive records together, that both source classes appear in the coverage
table, that an archive row names its releases, and that all five gates pass.
The README documents that command. `plugins/probitas/skills/probitas/EVOLUTION.md`
carries exactly one new `generation` row at `probitas-v0.2.0`, retaining
frontier revision `morpho-midnight-coverage` and digest
`5f66077a0c39a9ee647bd34233504b3891493f864fe4a16a9eb0c0337b3ee688` byte for
byte, citing issue #391 and the committed study, and leaving `Next Fiat job`
unchanged. `plugins/probitas/skills/probitas/SKILL.md` metadata reads
`version: "0.2.0"`. The Probitas package version moves from `0.1.1` to `0.1.2`
in `plugins/probitas/.claude-plugin/plugin.json`,
`plugins/probitas/.codex-plugin/plugin.json` and `.claude-plugin/marketplace.json`,
and `DELIVERY_PACKAGE_VERSIONS` in `tests/test_version_propagation.py` agrees.
The `probitas-evidence-collection` promise in `SKILL.md` states the two source
classes and the merge's refusals, keeping its promise identity so
`tests/promise_machine_coverage.json` needs no new row. The README's stated
test count matches the suite, replacing the stale `234`. Alexandria's ledger
and package version are untouched, because its only changed bytes are the two
pinned digests its dependency's format forced and no Alexandria behaviour
changed. Proved by:
`python3 plugins/probitas/tests/run_tests.py --elenchus-report .elenchus/probitas-391-step-4.json` passing with at least 316 tests,
`python3 -m unittest discover -s plugins/alexandria/tests -t .`,
`python3 -m unittest discover -s tests`,
`output="$(mktemp -d)/credit-history-v0"; python3 plugins/alexandria/examples/credit-history-v0/demo.py build --output "$output"` then `verify` on that output, both exiting 0,
`python3 scripts/portable_promise_machine.py sync` then `check`,
`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`,
`python3 plugins/horos/skills/horos/scripts/horos.py check .`,
`python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/probitas/README.md plugins/probitas/skills/probitas/SKILL.md plugins/probitas/skills/probitas/EVOLUTION.md`,
and `git diff --check`.

**Files.** Create `plugins/probitas/tests/test_union.py`. Change
`plugins/probitas/skills/probitas/EVOLUTION.md`,
`plugins/probitas/skills/probitas/SKILL.md`,
`plugins/probitas/.claude-plugin/plugin.json`,
`plugins/probitas/.codex-plugin/plugin.json`,
`.claude-plugin/marketplace.json`,
`tests/test_version_propagation.py`, `plugins/probitas/README.md`.
Regenerate `.agents/skills/promise-machine/runtime/` and its `MANIFEST.json`,
and the three `.horos` JSON files where the deterministic scan changes them.

**Tests.** Create `test_union.py` with the offline end-to-end demonstration
above and the assertions named in the exit. Expected count at least 316, from
at least 310. The Elenchus runner contract for any audit repair in this step is
exact: test command
`python3 plugins/probitas/tests/run_tests.py --elenchus-report {report}`;
report format `unittest-json-v1`; expected report schema
`elenchus.unittest.v1`; report file `.elenchus/probitas-391-step-4.json`. The
report path must be fresh. A missing, stale, empty, malformed or
infrastructure-failed report is `inconclusive`, not evidence that a repair is
guarded.

**Disciplines.** phylax: the demonstration builds a disposable index in a
temporary directory and reads it back, so the boundary is the temporary tree
and the control is that the test creates and removes its own and reaches no
network. ephoros: none, the demonstration is a test whose output is its own
report. metron: none, no performance claim. elenchus: the
`demo-receipt-drift` concern is the one a round should reproduce, by rebuilding
the Alexandria demonstration and comparing. hypomnema: the generation row is
the standing record for the whole design, pointing at the committed study for
the options that lost, which is where study item 12 put it.

### Amendment -- 2026-08-29

**What changed.** Complete replacement Files: Change
`plugins/probitas/scripts/probitas_lib/evidence.py`,
`plugins/probitas/scripts/probitas_lib/gates.py`,
`plugins/probitas/scripts/probitas_lib/render.py`,
`plugins/probitas/scripts/probitas_lib/adapters/__init__.py`,
`plugins/probitas/scripts/probitas.py`,
`plugins/alexandria/scripts/alexandria_lib/probitas.py`,
`plugins/probitas/tests/test_evidence.py`,
`plugins/probitas/tests/test_gates.py`,
`plugins/probitas/tests/test_render.py`,
`plugins/probitas/tests/test_cli.py`,
`plugins/probitas/tests/test_registry.py`,
`plugins/probitas/docs/example-dossier.md`,
`plugins/probitas/skills/probitas/references/gates.md`,
`plugins/alexandria/examples/credit-history-v0/expected-probitas.json`. Refresh
`docs/probitas-unified-collection-study.md` and
`docs/probitas-unified-collection-runbook.md` so the committed copies match the
receipted controller artefacts byte for byte after any amendment this step
records. Regenerate `.agents/skills/promise-machine/runtime/` and its
`MANIFEST.json`. Permit the three `.horos` JSON files only where the
deterministic scan changes them.

**Why.** Two reasons, both found while starting step 2. Step 2 puts the
Alexandria release identities on the coverage row as a field a gate can read,
and today they exist only inside the prose of the note that
`alexandria_lib.probitas.translate` writes. The alternatives are worse: a row
with zero records has no record to derive them from, so deriving them
Probitas-side fails for exactly the empty archive row that most needs them, and
parsing another plugin's prose would turn an undocumented format into a
contract. `translate` gains one `releases` key per coverage row instead, which
makes it an Alexandria behaviour change, so step 4 will owe Alexandria its own
generation row and that is a separate amendment when step 4 becomes current.
Separately, step 1 committed copies of the study and runbook and proved them
equal to the receipted artefacts; an amendment recorded during a later step
makes those copies stale, and no step could refresh them without this
allowance.

**Steps touched.** Step 2's files only. No other field of step 2 changes, and
steps 3 and 4 are untouched by this amendment.

**Still holding.** Step 2: entry holds; exit holds. Step 3: entry holds; exit
holds. Step 4: entry holds; exit holds.

### Amendment -- 2026-08-29

**What changed.** Complete replacement Files: Change
`plugins/probitas/scripts/probitas_lib/evidence.py`,
`plugins/probitas/scripts/probitas_lib/gates.py`,
`plugins/probitas/scripts/probitas_lib/render.py`,
`plugins/probitas/scripts/probitas_lib/adapters/__init__.py`,
`plugins/probitas/scripts/probitas.py`,
`plugins/alexandria/scripts/alexandria_lib/probitas.py`,
`plugins/probitas/tests/test_evidence.py`,
`plugins/probitas/tests/test_gates.py`,
`plugins/probitas/tests/test_render.py`,
`plugins/probitas/tests/test_cli.py`,
`plugins/probitas/tests/test_registry.py`,
`plugins/probitas/docs/example-dossier.md`,
`plugins/probitas/skills/probitas/references/gates.md`,
`plugins/alexandria/examples/credit-history-v0/expected-probitas.json`,
`tests/promise_machine_coverage.json`. Refresh
`docs/probitas-unified-collection-study.md` and
`docs/probitas-unified-collection-runbook.md` so the committed copies match the
receipted controller artefacts byte for byte after any amendment this step
records. Regenerate `.agents/skills/promise-machine/runtime/` and its
`MANIFEST.json`. Permit the three `.horos` JSON files only where the
deterministic scan changes them.

**Why.** `tests/promise_machine_coverage.json` pins a digest of
`plugins/probitas/scripts/probitas.py` under
`runtime.probitas-dossier-verification`, together with the field map describing
what a verification result exposes. Step 2 changes that file, so the repository
suite reports PM071 drift and names the remedy: review the changed result
surface and update the field map and the digest together. Neither can be left
alone without leaving the root suite red, and no other step touches that file.

**Steps touched.** Step 2's files only. No other field of step 2 changes, and
steps 3 and 4 are untouched by this amendment.

**Still holding.** Step 2: entry holds; exit holds. Step 3: entry holds; exit
holds. Step 4: entry holds; exit holds.
