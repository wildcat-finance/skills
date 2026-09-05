# Runbook: declare a held job's required inputs in the ledger

Derived from [the study](ledger-declared-inputs-study.md) and
[skills#1276](https://github.com/wildcat-finance/skills/issues/1276). Four
steps in dependency order, each green at both ends. Step 1 scaffolds and
step 4 demonstrates.

The selected design is bound below. It is not reopened inside a step.

```design-lock
schema | protasis-design-evidence/v1
sha256 | c9b7d2d3343f0b9fb2f58c804abcfbd6f1f952fb2dfc4bae0a385d4c992bd8f6
candidate | versioning-fenced-block
```

## Two readings this runbook records

**The decision record is numbered, not drafted.** The study names
`docs/decisions/drafts/<slug>.md` as the primary home, per ADR-077, and admits
the numbered alternative with a re-pick before pushing. This runbook takes the
numbered path. ADR-077 is `Proposed`, `docs/decisions/drafts/` holds no record,
and every landed record from ADR-001 to ADR-079 is numbered, so the numbered
path is the one this repository actually runs. Merge-time allocation fires only
on `done sync-run`, which a run whose base never advances never reaches, and a
draft would then land with no number at all. Step 1 re-picks the number against
`origin/main` immediately before pushing.

**No `version-relations` block.** This run advances one counter on one ledger
and the controller already holds it: the run is pinned to
`plugins/hexaemeron/skills/kronos/EVOLUTION.md` and `done integrate` refuses
without exactly one new valid row. A declared target may carry no concrete
`kronos-v0.9.0` token outside the block, which steps 3 and 4 must both write.
The run stays on the literal path.

## Step 1: Land the specification and the decision record

**Goal.** Put the study, this runbook and the decision behind them in the
repository, so a reader holding only the branch can build the remaining steps.

**Entry.** Branch `fiat/1276-declare-a-held-job-s-required-inputs-in-the` at
`5bc2494c4f5802efcd8a92e58554809ac4b9f147`, clean worktree.

**Exit.** `docs/ledger-declared-inputs/study.md` and
`docs/ledger-declared-inputs/runbook.md` are byte-identical to the receipted
artefacts. The decision record exists, carries the three decisions of study
item 12 in one record, and its number is the greatest present on `origin/main`
plus one, re-picked immediately before the push. Proved by
`python3 scripts/run_checks.py` exiting 0, which selects `docs` and `root` from
the changed paths and runs the Hypomnema record-shape check over `docs`.

**Files.** `docs/ledger-declared-inputs/study.md`,
`docs/ledger-declared-inputs/runbook.md`,
`docs/decisions/ADR-NNN-declare-a-held-jobs-inputs-in-the-ledger.md`.

**Tests.** No new test. The step is proved by the existing checked runner and
by `python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md
AGENTS.md .agents/skills/promise-machine/SKILL.md
.agents/skills/promise-machine/PORTABLE.md plugins docs` exiting 0. Elenchus
runner contract for any fix claimed in this step's audit: command `python3
plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`, format
`elenchus.unittest.v1`, report file `.hexaemeron/elenchus/step-1.json`.

**Disciplines.** phylax: none, the step adds no boundary and reads no input
from outside the repository. ephoros: none, nothing here runs unattended.
metron: none, no performance claim. elenchus: none, no failure in hand.
hypomnema: this is the step the discipline governs, and the three decisions of
study item 12 land in one record because they are one choice seen from three
sides.

## Step 2: Define the block in `VERSIONING.md` and check its shape repo-wide

**Goal.** State the optional `declared-inputs` block as ledger policy and
refuse a malformed one on any governed ledger, without moving a single
recorded frontier digest.

**Entry.** Step 1's branch and tree.

**Exit.** `VERSIONING.md` defines the block: info string `declared-inputs`,
placed after the last frontier header bullet and before `## History`, rows of
four pipe-separated fields `id | kind | availability | note`, `kind` from
`credential`, `endpoint`, `person`, `corpus`, `tool`, `availability` from
`available`, `absent`, `unknown`, at most 16 rows, at most 4096 bytes, id at
most 64 bytes and note at most 200, ids kebab-case and unique within the block.
It states that the block sits outside the four-field frontier digest, that the
closed vocabularies and the 16-row cap are extendable by an ordinary change to
this file, and that a declaration is a claim its ledger's owner makes and is
never checked for truth. `tests/test_evolution_contract.py` enforces that shape
over every governed ledger and refuses one specimen per risk-register entry:
`header-shadowing`, `block-placement`, `unclosed-fence`, `row-shape` and
`unbounded-block`. All 27 governed ledgers are accepted unchanged and each
recomputed frontier digest equals the value recorded on `main` at `5bc2494c`,
Kronos's staying
`ac28d95d80724aa001a92740f76416164e65d7b7b9cb5da43674d1ea73a214d1`. Proved by
`python3 scripts/run_checks.py` exiting 0.

The step also writes
`.hexaemeron/reports/versioning-fenced-block-absent-declaration-neutrality.json`
as a closed `protasis-design-report/v1` object, because that cell blocks
`step:3` and Fiat runs the design checker before step 3 opens. Its value is the
count of governed ledgers whose accepted-unchanged and digest-identical result
differs from the pre-change tree, which must be 0.

**Files.** `plugins/hexaemeron/skills/VERSIONING.md`,
`tests/test_evolution_contract.py`, specimen fixtures under
`tests/fixtures/evolution-contract/`,
`.hexaemeron/reports/versioning-fenced-block-absent-declaration-neutrality.json`.

**Tests.** `tests/test_evolution_contract.py` is extended with one accepting
case per governed ledger as it stands today, one accepting case for a
well-formed block, and one refusing case per named specimen, each asserting the
specimen's own refusal message. Expected new cases: 6 refusing, 2 accepting.
Elenchus runner contract: command `python3 -m unittest
tests.test_evolution_contract -v` for the suite itself, and for any fix claimed
in this step's audit `python3 plugins/hexaemeron/tests/run_tests.py
--elenchus-report {report}`, format `elenchus.unittest.v1`, report file
`.hexaemeron/elenchus/step-2.json`.

**Disciplines.** phylax: the shape check reads every governed ledger, so the
row, field and whole-block caps land here rather than in the consumer.
ephoros: none, the check runs inside a suite a person watches. metron: none,
the measured read cost belongs to step 3's reader. elenchus: each refusing
specimen is observed red against this step's entry tree before its rule lands.
hypomnema: none, step 1 already recorded the decision this step implements.

## Step 3: Teach `kronos.py` to read a declaration

**Goal.** Derive `declared_inputs` from the ledger on disk, refuse a malformed
block, record what was found on each pass, and mark a declaration that moved
under an unchanged held job.

**Entry.** Step 2's branch and tree, with the design checker clean at `step:3`.

**Exit.** `kronos.py` derives `declared_inputs` from the ledger on disk exactly
as `held_job_hash` is derived, never from the caller: a pass document that
states `declared_inputs` itself is refused as an unknown field. A malformed
block refuses the whole pass with `K022` and appends nothing. A ledger with no
block records `declared_inputs` as `null` and leaves every other recorded field
byte-identical to a pass taken before the change. `show` marks a moved
declaration digest for a candidate whose held-job hash did not move, beside the
existing axis drift. No axis, cap, tie-break, parked-lane or dispatch behaviour
changes. Proved by `python3 scripts/run_checks.py` exiting 0.

**Files.** `plugins/hexaemeron/skills/kronos/scripts/kronos.py`,
`plugins/hexaemeron/tests/test_kronos_scoreboard.py`, fixture ledgers under
`plugins/hexaemeron/tests/fixtures/kronos/`.

**Tests.** `plugins/hexaemeron/tests/test_kronos_scoreboard.py` gains cases for
a present block, an absent block recording `null`, a caller-supplied
`declared_inputs` refused, each `K022` refusal reason, and `show` marking a
moved declaration digest under an unchanged held-job hash. Expected new cases:
9. Elenchus runner contract: command `python3
plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`, format
`elenchus.unittest.v1`, report file `.hexaemeron/elenchus/step-3.json`.

**Disciplines.** phylax: this step opens the one new boundary, a ledger's block
read by `kronos.py`, and carries the row count, field and whole-block caps and
the closed vocabularies as its controls. ephoros: the recorded pass is the only
thing read afterwards, so `declared_inputs`, the declaration digest and the
`K022` refusal message are the three signals study item 8 names. metron: the
declaration read is measured against the recorded baseline of 88 ms over 200
passes before any cost claim is made. elenchus: every refusal case is observed
red before its guard lands. hypomnema: none, the decision is already recorded.

## Step 4: Instruct the ranking, advance the ledger, and demonstrate

**Goal.** Tell the ranking to read the block, record the generation row Kronos
owes, and run the study's demo path end to end.

**Entry.** Step 3's branch and tree.

**Exit.** `kronos/SKILL.md` tells step 3 of the loop to read the declaration
where present and to say in the basis that it inferred where absent. Its
`kronos-frontier-ranking` promise gains the declaration to Evidence and the
shape-not-truth statement to Boundary, with `tests/promise_machine_coverage.json`
and `plugins/hexaemeron/tests/fixtures/promise-machine/evaluation-cases.json`
updated to match. `kronos/SKILL.md` frontmatter `version` becomes `0.9.0`, the
Hexaemeron package advances from `1.6.24` to `1.6.25` in both plugin manifests
and both marketplace manifests, and `kronos/EVOLUTION.md` gains one generation
row `kronos-v0.9.0` whose `Frontier revision`, `Current frontier`, `Next Fiat
job` and `Frontier SHA-256` are retained byte for byte from `kronos-v0.8.0`.
The frontier status stays `mature` and the evolution counter stays at 0.

The demo path from the study's problem statement runs and prints one
declaration and one `declared: none` over a fixture root holding one declaring
ledger and one that does not, and prints `declared: none` for all 21 rankable
skills over the real checkout. Proved by `python3 scripts/run_checks.py`
exiting 0 and by the two recorded demo commands.

**Files.** `plugins/hexaemeron/skills/kronos/SKILL.md`,
`plugins/hexaemeron/skills/kronos/EVOLUTION.md`,
`plugins/hexaemeron/.claude-plugin/plugin.json`,
`plugins/hexaemeron/.codex-plugin/plugin.json`, `.claude-plugin/marketplace.json`,
`.codex-plugin/marketplace.json`, `tests/promise_machine_coverage.json`,
`plugins/hexaemeron/tests/fixtures/promise-machine/evaluation-cases.json`,
`docs/ledger-declared-inputs/demo.md`.

**Tests.** `tests/test_version_propagation.py` and
`tests/test_evolution_contract.py` already check the version agreement and the
generation row, and `python3 scripts/promise_machine.py coverage --check`
checks the promise. No new case is written beyond the demo record, because the
step's own claims are what those three existing gates already assert. Elenchus
runner contract: command `python3 plugins/hexaemeron/tests/run_tests.py
--elenchus-report {report}`, format `elenchus.unittest.v1`, report file
`.hexaemeron/elenchus/step-4.json`.

**Disciplines.** phylax: none, the step adds no boundary; it writes prose,
manifests and one ledger row. ephoros: none beyond step 3's three signals.
metron: none, no performance claim is made here. elenchus: none, no failure in
hand; the demo path is a demonstration rather than a guard. hypomnema: the
promise change is a contract change whose homes are the coverage file and the
evaluation cases, both named above, and it earns no second decision record.

### Amendment -- 2026-09-05

**What changed.** Complete replacement Exit: `docs/ledger-declared-inputs-study.md` is byte-identical to the receipted study. `docs/ledger-declared-inputs-runbook.md` is the receipted runbook with one relative link changed, `study.md` to `ledger-declared-inputs-study.md`, which the flat path requires. The decision record exists, carries the three decisions of study item 12 in one record, and its number is the greatest present on `origin/main` plus one, re-picked immediately before the push. Proved by `python3 scripts/run_checks.py` exiting 0, which selects `docs` and `root` from the changed paths and runs the Hypomnema record-shape check over `docs`, and by `diff` over the two committed copies showing no difference in the study and one changed link line in the runbook.
Complete replacement Files: `docs/ledger-declared-inputs-study.md`, `docs/ledger-declared-inputs-runbook.md`, `docs/decisions/ADR-NNN-declare-a-held-jobs-inputs-in-the-ledger.md`.
**Why.** The receipted study's five links to sibling skills are written for its home one level below the repository root. At `docs/ledger-declared-inputs/study.md` all five resolve to nothing and `hypomnema.py` refuses them as H001. An amendment appends and cannot rewrite the receipted study's link depth, so the copy either stops being byte-identical or moves to a path where the links resolve. The flat path resolves all five and costs one changed link in the runbook copy instead of five in the study.
**Steps touched.** Step 1's exit and files.
**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds.

### Amendment -- 2026-09-05

**What changed.** Complete replacement Files: `docs/ledger-declared-inputs-study.md`, `docs/ledger-declared-inputs-runbook.md`, `docs/decisions/ADR-NNN-declare-a-held-jobs-inputs-in-the-ledger.md`, `.horos/boundary.json`.
**Why.** Adding three tracked documents moves `files_walked` in `.horos/boundary.json` from 2569 to 2572, and `tests/test_boundary_currency.py` refuses the stale counts with `['.horos/boundary.json#counts']` until `python3 plugins/horos/skills/horos/scripts/horos.py scan . --write` regenerates them. The regenerated file adds no entry, so the three documents are counted and not classified. It is a changed path and belongs in this field.
**Steps touched.** Step 1's files.
**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds.
