# Runbook: bind the integrate gate to the sync receipt's recorded base head

### Source receipts

```text
study sha256: 4229f580b240d7bded8aa1f9b48c4d39afa3fffe6444156a06fc8c831d503095
starting ref: c4650f02a979e859ce36374779eac9cd70744288
run branch: fiat/608-bind-the-integrate-gate-to-the-sync-receipt
task issue: https://github.com/wildcat-finance/skills/issues/608
```

The topic is one capability with three dependency-ordered steps, per the
study's decomposition decision. Step 1 freezes the accepted proposition in the
tracked tree. Step 2 lands the shared-constant fix with its regression module
and the fiat ledger row. Step 3 moves the package version across its five
compared surfaces and runs the demonstration. The ledger version, the
contract-test literals and the package version are global identifiers that
concurrent runs take first, so each is picked at the step that writes it,
after re-reading the tree, and this preamble names only the expected values.
This run's audit records land in the run-derived file
`audit/rounds/fiat-608-bind-the-integrate-gate-to-the-sync-receipt.md`.

## Step 1: Publish the accepted base-head specification

**Goal.** Commit byte-identical tracked copies of the receipted study and
runbook, with their structure, lexicon, links and reading boundary checked
before any controller code changes.

**Entry.** The exact run branch
`fiat/608-bind-the-integrate-gate-to-the-sync-receipt` at starting ref
`c4650f02a979e859ce36374779eac9cd70744288`; the study receipt names SHA-256
`4229f580b240d7bded8aa1f9b48c4d39afa3fffe6444156a06fc8c831d503095`. No
tracked file from this run exists at entry.

**Exit.** The following all hold:

1. `docs/fiat-integrate-base-head-study.md` is byte-identical to the
   receipted `.hexaemeron/study.md`.
2. `docs/fiat-integrate-base-head-runbook.md` is byte-identical to the
   receipted `.hexaemeron/runbook.md`.
3. Protasis accepts both tracked artefacts, Imprimatur reports no defect on
   either, and every relative link resolves from the publication location.
4. The deterministic Horos scan describes the resulting tracked tree.
5. The root and Hexaemeron suites remain green and `git diff --check`
   exits 0.

**Files.** Create only:

- `docs/fiat-integrate-base-head-study.md`;
- `docs/fiat-integrate-base-head-runbook.md`;
- `.horos/boundary.json` only when the deterministic Horos scan changes it;
- `audit/rounds/fiat-608-bind-the-integrate-gate-to-the-sync-receipt.md` only
  for append-only Warden round records.

No canonical skill, script, test, manifest, ledger, CI file, or dependency
changes in this step's implementation.

**Tests.** None written; copy the two receipted artefacts without rewriting
them, then run:

```bash
cmp -s .hexaemeron/study.md docs/fiat-integrate-base-head-study.md
cmp -s .hexaemeron/runbook.md docs/fiat-integrate-base-head-runbook.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/fiat-integrate-base-head-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/fiat-integrate-base-head-runbook.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-integrate-base-head-study.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-integrate-base-head-runbook.md
python3 plugins/horos/skills/horos/scripts/horos.py check .
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
git diff --check
```

The source-bound Elenchus runner contract for any audit repair is:

```text
test command: python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}
report format: unittest-json-v1
expected report schema: elenchus.unittest.v1
report file: .elenchus/fiat-608-step-1.json
```

The report path must be fresh. A missing, stale, empty, malformed, or
infrastructure-failed report is `inconclusive`, not evidence that a repair is
guarded.

**Disciplines.** phylax: none, because this step adds static Markdown and no
new input or execution boundary. ephoros: none, because it adds no unattended
operation. metron: none, because it makes no performance claim. elenchus:
byte-identity, link, structural, boundary, and suite regressions stop the
step and any repair uses the exact runner above. hypomnema: the tracked study
and runbook are the durable homes the accepted proposition selected.

## Step 2: Read the sync receipt through one shared key and prove the subtraction

**Goal.** The integrate gate reads the merged base tip through the same
module-level constant the sync receipt writer stores it under, a regression
module drives the demonstrated controller-currency topology from red to
green, and the fiat ledger gains this run's one generation row.

**Entry.** Step 1's signed, audited, prose-checked branch tip. The entry
controller's `cmd_done_integrate` asks the sync receipt for `base_commit`, a
key no shipped writer ever stored, so `base_ledger_versions` receives None
and returns the empty set: a state whose sync absorbed published ledger rows
is refused for rows it did not write. Preserve that red reproduction before
changing the mechanism (study risk `receipt-key-drift`).

**Exit.** The following all hold:

1. One module-level constant names the sync receipt's base-tip key, written
   by the `done sync-run` receipt writer and read by `done integrate`'s
   published-set call, so the two sites cannot name different keys again.
2. A new regression module `plugins/hexaemeron/tests/test_hexctl_frontier_receipt.py`
   drives the demonstrated topology end to end: a frontier-pinned run whose
   receipted sync absorbed two published ledger rows and whose ledger carries
   exactly one own row passes the integrate arithmetic, with the subtracted
   versions visible in the integrate receipt. The module also pins the sync
   receipt's key set, and guards that a missing or malformed base tip still
   reads as the empty set (study risks `ledger-arithmetic`, `state-compat`).
3. Each new test is an Elenchus guard: the pre-fix red is captured against
   the entry controller, and every guard fails with the fix reverted.
4. `plugins/hexaemeron/skills/fiat/EVOLUTION.md` carries exactly one new
   generation row for this change, picked after re-reading the ledger and
   the base (expected `fiat-v5.25.1`), retaining frontier revision
   `state-shape-validation` and its digest byte for byte; the fiat
   `SKILL.md` frontmatter version matches the ledger; the pinned fiat
   frontier literals in `tests/test_evolution_contract.py` move to the new
   head, literals only.
5. The six hexctl.py digest pins in `tests/promise_machine_coverage.json`
   are refreshed to the changed controller's digest, values only (study risk
   `version-propagation`).
6. Both suites are green, the deterministic Horos scan describes the tree,
   and `git diff --check` exits 0.

**Files.** Change or create only:

- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`;
- `plugins/hexaemeron/tests/test_hexctl_frontier_receipt.py`, plus fixtures
  under `plugins/hexaemeron/tests/fixtures/` as the new cases need them;
- `tests/promise_machine_coverage.json`, refreshed runtime digests only;
- `plugins/hexaemeron/skills/fiat/EVOLUTION.md`;
- `plugins/hexaemeron/skills/fiat/SKILL.md`, frontmatter version only;
- `tests/test_evolution_contract.py`, the pinned fiat frontier literals only;
- `.horos/boundary.json` only when the deterministic Horos scan changes it;
- `audit/rounds/fiat-608-bind-the-integrate-gate-to-the-sync-receipt.md`
  only for append-only Warden round records.

The package version does not move in this step; it is picked at step 3.

**Tests.** Adds `plugins/hexaemeron/tests/test_hexctl_frontier_receipt.py`:
the end-to-end absorbed-rows topology; the sync receipt key-set pin; the
shared-constant identity between writer and reader; the empty-set guard for a
missing or malformed base tip; and the subtracted-versions receipt field. At
least five new tests. Then run:

```bash
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

The source-bound Elenchus runner contract for any audit repair is:

```text
test command: python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}
report format: unittest-json-v1
expected report schema: elenchus.unittest.v1
report file: .elenchus/fiat-608-step-2.json
```

The report path must be fresh. A missing, stale, empty, malformed, or
infrastructure-failed report is `inconclusive`, not evidence that a repair is
guarded.

**Disciplines.** phylax: no new boundary opens; the fix changes which recorded
key an existing bounded read consumes. ephoros: the integrate receipt's
subtracted-versions field is the signal that answers whether the subtraction
engaged. metron: none, because no performance claim is made. elenchus: the
halted run's refusal is the captured red, and every behaviour lands as a
guard proven to fail with the fix reverted. hypomnema: the ledger row is the
record; no new decision earns an ADR, because the fix implements what
fiat-v5.16.1 already decided.

## Step 3: Move the package version and demonstrate

**Goal.** The hexaemeron package version moves across all five compared
surfaces so `claude plugin update` copies this fix, and the study's demo path
runs green.

**Entry.** Step 2's signed, audited, prose-checked branch tip. The fix and
its regression module are tested; the five version surfaces still name the
entry package version. Re-read the five surfaces and the base before picking
the new value (expected `1.6.1`).

**Exit.** The following all hold:

1. The hexaemeron package version moves on all five compared surfaces and
   `tests/test_version_propagation.py` passes:
   `plugins/hexaemeron/.claude-plugin/plugin.json`,
   `plugins/hexaemeron/.codex-plugin/plugin.json`,
   `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`,
   and the pinned `DELIVERY_PACKAGE_VERSIONS` map (study risk
   `version-propagation`).
2. The demonstration runs green: the regression module's absorbed-rows
   topology through the Hexaemeron suite, then the repository proof commands
   below.
3. Every changed prose surface lints clean.

**Files.** Change only:

- `plugins/hexaemeron/.claude-plugin/plugin.json`;
- `plugins/hexaemeron/.codex-plugin/plugin.json`;
- `.claude-plugin/marketplace.json`;
- `.agents/plugins/marketplace.json`;
- `tests/test_version_propagation.py`, the pinned map only;
- `.horos/boundary.json` only when the deterministic Horos scan changes it;
- `audit/rounds/fiat-608-bind-the-integrate-gate-to-the-sync-receipt.md`
  only for append-only Warden round records.

**Tests.** None written beyond step 2's; the propagation and evolution suites
already compare every touched surface. Then run:

```bash
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/promise_machine.py check
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

The source-bound Elenchus runner contract for any audit repair is:

```text
test command: python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}
report format: unittest-json-v1
expected report schema: elenchus.unittest.v1
report file: .elenchus/fiat-608-step-3.json
```

The report path must be fresh. A missing, stale, empty, malformed, or
infrastructure-failed report is `inconclusive`, not evidence that a repair is
guarded.

**Disciplines.** phylax: none, because no boundary opens. ephoros: none
beyond what step 2's receipt field already carries. metron: none, because no
performance claim is made. elenchus: a demonstration regression stops the
step and uses the runner above. hypomnema: the five version surfaces are the
durable record that the fix ships to installed hosts.
