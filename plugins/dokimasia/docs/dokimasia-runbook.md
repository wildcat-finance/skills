# Dokimasia: implementation runbook

This runbook implements the selected design from [the study](dokimasia-study.md). Each
step is one pull request and begins only after the design checker admits that
transition.

```design-lock
schema | protasis-design-evidence/v1
sha256 | bc4ff4ae50a72d9b17ef11a3f2470dcd042228b2b956c789176aae4d370f7dd3
candidate | inventory-first
```

## Step 1: Land the Dokimasia scaffold and its router row

**Goal.** Add the plugin so both hosts discover it and every repository gate
accepts it, with every substantive verb refusing by name.

**Entry.** Clean `wildcat-finance/skills` at
`51fb586e41f67bff1cd53bed8414e3fc63ff48cb`; Python `==3.14.*` and no
third-party dependency; `.hexaemeron/design-evidence.json` has SHA-256
`bc4ff4ae50a72d9b17ef11a3f2470dcd042228b2b956c789176aae4d370f7dd3` with its 18
selection reports present; the repository's Apache-2.0 posture is inherited.

**Exit.** Both host manifests agree on one version, the canonical contract
declares its promises, every substantive verb refuses, the router corpus check
is green against a regrade recorded in the same change, and the Step 2 report
is emitted by
`python3 scripts/run_checks.py && python3 -m unittest discover -s plugins/dokimasia/tests -t plugins/dokimasia && python3 plugins/dokimasia/scripts/dokimasia.py selftest --report .hexaemeron/reports/conformance/inventory-first-scaffold-contract-check.json`.

**Files.** `plugins/dokimasia/.claude-plugin/plugin.json`;
`plugins/dokimasia/.codex-plugin/plugin.json`; `plugins/dokimasia/AGENTS.md`;
`plugins/dokimasia/README.md`; `plugins/dokimasia/LICENSE`;
`plugins/dokimasia/PROMISE_MACHINE.md`;
`plugins/dokimasia/skills/dokimasia/SKILL.md`;
`plugins/dokimasia/skills/dokimasia/EVOLUTION.md`;
`plugins/dokimasia/scripts/dokimasia.py`; `plugins/dokimasia/tests/`;
`plugins/dokimasia/docs/dokimasia-study.md`;
`plugins/dokimasia/docs/dokimasia-runbook.md`;
`plugins/dokimasia/docs/design-evidence.json`;
`plugins/dokimasia/docs/reports/selection/`;
`plugins/dokimasia/docs/decisions/ADR-001-one-disposition-per-scoped-item.md`;
`tests/check-map-v1.json`; `tests/promise_machine_coverage.json`;
`tests/fixtures/router-selection/cases.json`; `.claude-plugin/marketplace.json`;
`.agents/plugins/marketplace.json`; `.agents/skills/promise-machine/SKILL.md`;
the regenerated `.agents/skills/promise-machine/runtime/` tree; `AGENTS.md`;
`README.md`; `INSTALL.md`.

**Tests.** Add scaffold tests covering both manifests, one declared version
across every file that states one, the promises the contract declares, the
marketplace boundary sentence, and a refusal for every substantive verb; add
router-selection case `RS-40` for the new row, add it to the
`guard-missing-row` fixture as well, rebind the two pinned fixture digests,
and record a 40-case regrade over the whole corpus. `RS-33` is expected to
fail; framework-73 owns it.
Retain every existing repository test. Elenchus runner:
`python3 plugins/dokimasia/scripts/dokimasia.py selftest --report {report}`;
report format `protasis-design-report/v1`; report file
`.hexaemeron/reports/conformance/inventory-first-scaffold-contract-check.json`.

**Disciplines.** phylax: the filesystem, packaging and ownership boundaries
open here, and a plugin that reads outside its declared root is the first thing
to get wrong; ephoros: the report identity and version fields every later step
joins to are fixed here; metron: none, this step makes no runtime claim;
elenchus: every refusal gets a test that fails without it; hypomnema: the name,
the marketplace boundary and the disposition vocabulary are expensive to
reverse and are recorded with the committed study and runbook.

## Step 2: Compile the route, action and guard inventory

**Goal.** Turn one pinned application checkout into a closed, digest-bound
inventory of routes, API handlers, actions and access guards.

**Entry.** Step 1 is merged; the design checker admits `step:2` by consuming
the passing `scaffold-contract-check` report; a read-only checkout of
`wildcat-finance/wildcat-app-v2` at
`bb9685fb7dbe9cd2f5b7683a9b3f164509dc2de9` is available locally.

**Exit.** Two compiles of the same checkout produce the same inventory digest,
every declared cap refuses before it is exceeded, no path escapes the declared
root, and the Step 3 report is emitted by
`python3 -m unittest discover -s plugins/dokimasia/tests -t plugins/dokimasia && python3 plugins/dokimasia/scripts/dokimasia.py inventory --check --report .hexaemeron/reports/conformance/inventory-first-inventory-determinism.json`.

**Files.** `plugins/dokimasia/scripts/dokimasia_lib/inventory.py`;
`plugins/dokimasia/scripts/dokimasia_lib/lexer.py`;
`plugins/dokimasia/scripts/dokimasia_lib/paths.py`;
`plugins/dokimasia/schemas/inventory-v1.json`;
`plugins/dokimasia/tests/fixtures/app/`;
`plugins/dokimasia/tests/test_inventory.py`;
`plugins/dokimasia/tests/test_lexer.py`; `plugins/dokimasia/tests/test_paths.py`;
`plugins/dokimasia/docs/inventory-rules.md`.

**Tests.** Cover page routes, dynamic segments, route groups, API handlers,
server actions, middleware guards and client-side gates over a committed
synthetic application fixture; prove two compiles agree byte for byte; prove a
symlink, an absolute path, a parent-directory path, an oversized file, an
over-deep tree and an over-large file count each refuse by name; prove no
subprocess is spawned and no socket is opened. Elenchus runner:
`python3 plugins/dokimasia/scripts/dokimasia.py inventory --check --report {report}`;
report format `protasis-design-report/v1`; report file
`.hexaemeron/reports/conformance/inventory-first-inventory-determinism.json`.

**Disciplines.** phylax: the application checkout is untrusted input read
through a lexer, and the caps are the control; ephoros: the inventory digest
and the commit it came from become the run's first two signals; metron: record
the compile duration as a baseline, set no target; elenchus: every cap and path
refusal gets a reducing fixture; hypomnema: the inventory rules for one
framework are a contract other people will argue with, so they get their own
document.

## Step 3: Import the workbook into a closed record

**Goal.** Read a UAT spreadsheet into a closed record that preserves every
source id, status, comment, evidence and source label.

**Entry.** Step 2 is merged; the design checker admits `step:3` by consuming
the passing `inventory-determinism` report; a synthetic workbook fixture is
committed and the reviewed workbook is supplied out of band against its
recorded digest.

**Exit.** Every source id survives a round trip, a compound row splits without
losing its source identity, every archive cap refuses before extraction, and
the Step 4 report is emitted by
`python3 -m unittest discover -s plugins/dokimasia/tests -t plugins/dokimasia && python3 plugins/dokimasia/scripts/dokimasia.py workbook --check --report .hexaemeron/reports/conformance/inventory-first-workbook-roundtrip.json`.

**Files.** `plugins/dokimasia/scripts/dokimasia_lib/workbook.py`;
`plugins/dokimasia/scripts/dokimasia_lib/xlsx.py`;
`plugins/dokimasia/schemas/workbook-v1.json`;
`plugins/dokimasia/tests/fixtures/workbooks/`;
`plugins/dokimasia/tests/test_workbook.py`;
`plugins/dokimasia/tests/test_xlsx.py`;
`plugins/dokimasia/docs/workbook-lineage.md`.

**Tests.** Cover shared strings, inline strings, empty cells, merged headers,
multiple sheets, a compound row split into atomic cases, and a row whose status
is unknown; prove the round trip preserves ids, statuses, comments, evidence
and source labels; prove a zip bomb, a traversal member name, an over-count
archive, an over-size member and a non-spreadsheet file each refuse by name;
prove no formula is evaluated. Elenchus runner:
`python3 plugins/dokimasia/scripts/dokimasia.py workbook --check --report {report}`;
report format `protasis-design-report/v1`; report file
`.hexaemeron/reports/conformance/inventory-first-workbook-roundtrip.json`.

**Disciplines.** phylax: a spreadsheet is an untrusted zip archive and the caps
are the whole control; ephoros: the workbook digest and its row counts become
run signals; metron: record the import duration, set no target; elenchus: every
archive refusal gets a hostile fixture; hypomnema: what lineage means, and what
a split row owes its source, is a contract worth writing down once.

## Step 4: Reconcile both sides into dispositions

**Goal.** Give every inventory item and every workbook row exactly one
disposition, with a reason for each manual and excluded item.

**Entry.** Step 3 is merged; the design checker admits `step:4` by consuming
the passing `workbook-roundtrip` report; the inventory and workbook records for
the committed fixtures both validate.

**Exit.** The closure ratio is one over the scoped set, an unreviewed item, a
stale item and a double disposition each refuse, the gap list names every
manual and excluded item with its reason, and the Step 5 report is emitted by
`python3 -m unittest discover -s plugins/dokimasia/tests -t plugins/dokimasia && python3 plugins/dokimasia/scripts/dokimasia.py reconcile --check --report .hexaemeron/reports/conformance/inventory-first-disposition-closure.json`.

**Files.** `plugins/dokimasia/scripts/dokimasia_lib/reconcile.py`;
`plugins/dokimasia/schemas/coverage-v1.json`;
`plugins/dokimasia/tests/fixtures/dispositions/`;
`plugins/dokimasia/tests/test_reconcile.py`;
`plugins/dokimasia/docs/coverage-contract.md`.

**Tests.** Cover a covered item, a manual item with a reason, an excluded item
with a reason, an item with no disposition, an item with two, a disposition
naming an oracle that is absent, a workbook row with no matching inventory
item, an inventory item with no matching row, and a disposition recorded
against an inventory digest that has since moved; prove the numerator and
denominator of the closure ratio separately; prove the agent cannot mark an
item covered without a reviewed oracle. Elenchus runner:
`python3 plugins/dokimasia/scripts/dokimasia.py reconcile --check --report {report}`;
report format `protasis-design-report/v1`; report file
`.hexaemeron/reports/conformance/inventory-first-disposition-closure.json`.

**Disciplines.** phylax: this is where an agent could quietly widen coverage,
so the control is that a person owns every disposition; ephoros: the closure
ratio and the gap list are the signals the whole prototype exists to emit;
metron: record the reconcile duration, set no target; elenchus: every ambiguous
or stale disposition gets a reducing case; hypomnema: the disposition
vocabulary and the closure ratio are the decision this run is most likely to be
argued with about, so they get an ADR.

## Step 5: Demonstrate against the pinned application and release

**Goal.** Run one complete scrutiny of the pinned application and the reviewed
workbook, record what it found, and open the skill's ledger.

**Entry.** Step 4 is merged; no later conformance report is pre-populated; the
pinned application checkout and the reviewed workbook are both available and
match their recorded digests.

**Exit.** One scrutiny of the pinned commit emits a digest-bound coverage
record with a stated closure ratio and gap list, the recorded evidence
regenerates byte for byte, the run finishes within 120,000 milliseconds, and
the integration report is emitted by
`python3 -m unittest discover -s plugins/dokimasia/tests -t plugins/dokimasia && python3 scripts/run_checks.py && python3 plugins/dokimasia/scripts/dokimasia.py demonstrate --check --report-timing --report .hexaemeron/reports/conformance/inventory-first-pinned-demonstration.json`.

**Files.** `plugins/dokimasia/scripts/dokimasia_lib/demonstrate.py`;
`plugins/dokimasia/docs/evidence/wildcat-app-v2.coverage.json`;
`plugins/dokimasia/docs/evidence/wildcat-app-v2-scrutiny.md`;
`plugins/dokimasia/tests/test_demonstration.py`;
`plugins/dokimasia/skills/dokimasia/EVOLUTION.md`;
`plugins/dokimasia/README.md`; `plugins/dokimasia/skills/dokimasia/SKILL.md`.

**Tests.** Prove the committed evidence regenerates from the pinned inputs;
prove a moved application commit, a moved workbook digest and a moved skill
version each change the record and are each reported as a distinct cause; prove
the timing report records a measured duration rather than a target; assert the
recorded closure ratio, scoped count and gap count as separate fields. Elenchus
runner:
`python3 plugins/dokimasia/scripts/dokimasia.py demonstrate --check --report {report}`;
report format `protasis-design-report/v1`; report file
`.hexaemeron/reports/conformance/inventory-first-pinned-demonstration.json`.

**Disciplines.** phylax: the reviewed workbook is read locally and its bytes are
never committed; ephoros: this step must answer all four study questions from
one record; metron: the 120,000 millisecond budget is measured here and the
observed timing is what a later budget will be set from; elenchus: a moved
number must have exactly one named cause; hypomnema: the ledger row, the
frontier and any later budget change are recorded decisions.
