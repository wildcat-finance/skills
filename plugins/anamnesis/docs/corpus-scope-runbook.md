# Runbook: declare the corpus scope in the release policy and build the estate corpus

Derived from the study committed beside this file as `corpus-scope-study.md`.
The selected design is `release-policy-scope`: `scope` becomes a required
closed object in the curation policy, the policy the release manifest records
and the release id already hashes; the resolver-side constant goes; the pilot
is re-released under its declared scope; and a second specimen, the estate
corpus, is built under its own.

Four steps. Step 1 commits the design records and admits this run's step
numbers to the runner. Step 2 declares the scope, removes the constant,
re-releases the pilot and records the decision. Step 3 builds the estate
specimen. Step 4 advances the ledger, reconciles the prose and runs both demo
paths.

The plugin's Elenchus runner numbers its steps by the plugin's own history, and
runbook steps 1 to 4 of this run are its steps 7 to 10. Each step's `Tests`
line names the exact command, so Warden takes the runner argument from there
and does not infer it from the heading.

Every step's exit runs the root suite from a clean detached snapshot of the
committed head, because the run worktree's own `.hexaemeron/design-evidence.json`
reddens two root tests that read that path (skills#1228). Every commit is
preceded by `python3 plugins/horos/skills/horos/scripts/horos.py scan . --write`
and `python3 plugins/horos/skills/horos/scripts/horos.py scan . --census --write`
over the staged tree, because the boundary counts tracked paths and the census
counts bytes.

```design-lock
schema | protasis-design-evidence/v1
sha256 | b9e9d4d14113b460b6ffbd78aa463d86620bf1b46fe948becf1e49874702f32b
candidate | release-policy-scope
```

## Step 1: Commit the design records and admit this run's step runner

**Goal.** Land the study, runbook, design record, its 32 reports and their
resolver in the plugin's docs, and admit this run's step numbers to the
Elenchus runner, with no product behaviour changed.

**Entry.** Exact commit `0bc39f278e24d8cdd79abed5da16bd5ce81e4c5a` on the run
branch, with `.hexaemeron/study.md`, `.hexaemeron/runbook.md`,
`.hexaemeron/design-evidence.json` and `.hexaemeron/reports/` receipted;
`python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition step:1`
exits zero.

**Exit.** `plugins/anamnesis/docs/corpus-scope-study.md` and
`plugins/anamnesis/docs/corpus-scope-runbook.md` are byte-identical to the
receipted `.hexaemeron/study.md` and `.hexaemeron/runbook.md`;
`plugins/anamnesis/docs/corpus-scope/design-evidence.json`, its 32 reports and
`reports/resolve.py` are committed with the receipted bytes;
`plugins/anamnesis/tests/elenchus.py` admits steps 7 to 10;
`python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py plugins/anamnesis/docs/corpus-scope-study.md plugins/anamnesis/docs/corpus-scope-runbook.md`
exits zero;
`python3 -m unittest discover -s plugins/anamnesis/tests -t plugins/anamnesis`
is green; `python3 -m unittest discover -t . -s tests` is green from a clean
detached snapshot of the committed head; `git diff --check` is clean;
`python3 plugins/horos/skills/horos/scripts/horos.py check .` exits zero; and
`python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition step:2`
exits zero before the pull request is ready.

**Files.** Create `plugins/anamnesis/docs/corpus-scope-study.md`,
`plugins/anamnesis/docs/corpus-scope-runbook.md`,
`plugins/anamnesis/docs/corpus-scope/design-evidence.json`,
`plugins/anamnesis/docs/corpus-scope/reports/` (32 report objects and
`resolve.py`) and `plugins/anamnesis/tests/test_s7_records.py`. Change
`plugins/anamnesis/tests/elenchus.py` (`STEPS`), `.horos/boundary.json` and
`.horos/census.json`.

**Tests.** Add `plugins/anamnesis/tests/test_s7_records.py`: the committed
design record parses, declares schema `protasis-design-evidence/v1`, names four
candidates and eight criteria covering all five concerns, selects
`release-policy-scope` under `unique-frontier` with `admission-policy-scope`
failing exactly `scope-recorded-in-release` and the other two candidates failing
`release-id-declared-function`, `estate-findings-admissible-without-widening`
and `scope-recovery-by-policy-edit`; every one of the 32 result cells names a
report whose recorded SHA-256 matches the committed bytes and whose `command`
names the committed `resolve.py`; and the two committed copies equal the
receipted artefacts byte for byte. The audit runner contract is
`python3 plugins/anamnesis/tests/elenchus.py --step 7 {report}`, its format is
`elenchus.unittest.v1`, and Warden writes
`.hexaemeron/elenchus/anamnesis-step-7.json`. Also run the anamnesis suite from
the repository root, the root suite from a clean snapshot, and
`git diff --check`. Expected new focused tests: 6.

**Disciplines.** phylax: none, the step adds documents and a test and opens no
boundary. ephoros: none, nothing here runs unattended. metron: none, no
performance claim and no speed-motivated change. elenchus: none, no failure in
hand at entry. hypomnema: the design record's committed location and the
study's bridge to the ledger are the one choice here that is awkward to move
later, and both are settled by this step.

## Step 2: Declare the scope in the release policy and re-release the pilot

**Goal.** Make `scope` a required closed object of the curation policy, checked
both ways against the admitted sources and against the declared record bounds,
remove `seed_scope`, re-release the pilot under its declared scope, re-pin the
demonstration ledger and the root card, and record the decision.

**Entry.** Step 1's exit state;
`python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition step:2`
exits zero.

**Exit.** `CURATION_POLICY_KEYS` and `schemas/policy-v1.json` require `scope`
with `id`, `preserves`, `sources` and `records` (`minimum`, `maximum`) and
nothing else; `check_scope` refuses `A074` for an admitted source outside
`scope.sources`, `A075` for a scope source not admitted, `A073` for a record
count outside the declared bounds naming those bounds, and `A076` for a
malformed scope, and runs from `admit-seed` (which takes `--curation-policy`),
`curate`, `release` and `_rebuild_once`; `verify_release` refuses `A077` when
`manifest.sources` and `manifest.policy.scope.sources` differ; no literal record
bound remains in `anamnesis.py`; the pilot's `curation-policy.json` declares
scope `warden-seed-pilot` with bounds 25 to 50 under version
`curation-2026-09-06`; the pilot release, both projections, `DEMONSTRATION.md`
(program digest, observation lines, one generation row `anamnesis-demo-v0.2.0`
with the demo frontier revision and digest unchanged) and the root `README.md`
card digest are regenerated, and `policy.json`, the three sources, both event
streams, `engagements.json`, `assertions.json`, `quarantine.json` and
`unknowns.json` are byte-identical;
`plugins/anamnesis/docs/decisions/ADR-006-declared-corpus-scope.md` exists with
the five sections and a dated status; `python3 scripts/demonstrations.py check --root .`
and `python3 scripts/check_public_front_door.py` exit zero;
`python3 plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py demo --specimen plugins/anamnesis/specimens/pilot`
exits zero; the anamnesis suite is green; the root suite is green from a clean
snapshot; `git diff --check` is clean; the Horos check exits zero; and
`python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition step:3`
exits zero before the pull request is ready.

**Files.** Change `plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py`,
`plugins/anamnesis/skills/anamnesis/schemas/policy-v1.json`,
`plugins/anamnesis/specimens/pilot/curation-policy.json`,
`plugins/anamnesis/specimens/pilot/release/` (`manifest.json`, `policy.json`,
`relations.json`), `plugins/anamnesis/specimens/pilot/projections/` (both
files), `plugins/anamnesis/skills/anamnesis/DEMONSTRATION.md`,
`plugins/anamnesis/skills/anamnesis/SKILL.md` (the `admit-seed` command, the
scope paragraph and the curation and release `Refuses` lines),
`plugins/anamnesis/AGENTS.md` (the `admit-seed` sentence), root `README.md`
(the card digest), `plugins/anamnesis/tests/test_s1_admission.py`
(`PilotScope` becomes a declared-scope suite), `.horos/boundary.json` and
`.horos/census.json`. Create
`plugins/anamnesis/docs/decisions/ADR-006-declared-corpus-scope.md` and
`plugins/anamnesis/tests/test_s8_scope.py`.

**Tests.** Add `plugins/anamnesis/tests/test_s8_scope.py`: one specimen per
refusal code `A073`, `A074`, `A075`, `A076` and `A077`; a curation policy
without `scope` refuses `A012`; a one-byte change to any scope field changes the
release id; `seed_scope` is absent from the module and the literal
`25 <= record_count <= 50` is absent from its source; the pilot rebuilds to the
committed release id under the new policy; the committed projections equal fresh
ones; `DEMONSTRATION.md` names the current program and admission policy
digests and its observation lines carry the committed release id; and the
committed root card digest equals `demonstrations.record_digest` of the
ledger record. Rewrite `PilotScope` in `test_s1_admission.py` to read the bound
from the pilot's curation policy. The audit runner contract is
`python3 plugins/anamnesis/tests/elenchus.py --step 8 {report}`, its format is
`elenchus.unittest.v1`, and Warden writes
`.hexaemeron/elenchus/anamnesis-step-8.json`. Also run the anamnesis suite from
the repository root, the root suite from a clean snapshot, the pilot demo, and
`git diff --check`. Expected new focused tests: 12.

**Disciplines.** phylax: the scope check reads two policy files and compares
bounded strings and small integers through the closed-object and bounded-text
validation every policy field already passes; no new input class is opened.
ephoros: the five refusal codes are raised inside `refusals_recorded`, so each
emits the existing `anamnesis.source.refused` event with rule, record, policy
version and correlation id; no new event kind. metron: none, no budget and no
speed-motivated change; the demo prints its baselines. elenchus: each refusal
specimen is the guard's own bad case, and every new guard runs against the
parent commit to show it fails there. hypomnema: the scope's home in the
release policy is the decision that is expensive to reverse; ADR-006 holds the
four alternatives and the matrix, and the ledger row in step 4 cites it.

## Step 3: Build the estate specimen under its own declared scope

**Goal.** Add `plugins/anamnesis/specimens/estate/`, a second corpus under
scope `capture-estate-findings`, holding the capture estate's own findings and
open actions as public derived text authored by Wildcat Labs, and prove it
rebuilds to its own release id.

**Entry.** Step 2's exit state; the maintainer's grant of public derived text
for the seventeen estate findings is recorded in the `rights.statement` of both
estate sources (study assumption 4), without which this step is blocked and not
guessed;
`python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition step:3`
exits zero.

**Exit.** `plugins/anamnesis/specimens/estate/` holds `policy.json`
(`anamnesis-pilot-policy/v1`, version `estate-2026-09-06`, two sources,
17 records), `curation-policy.json` (version `estate-2026-09-06`, mapper
`warden-audit-round-markdown` 1, taxonomy `estate-severity` 1 with `high`,
`medium` and `unrated`, scope `capture-estate-findings` with both source ids
and bounds 10 to 40), `sources/archive-verification-2026-08-31.md` (rounds
"Priority findings, round 1" with V1-R1-01 to V1-R1-12 and "Family verdicts,
round 2" with V1-R2-01), `sources/counterparty-history-2026-09-05.md` (rounds
"Capture inventory, round 1" with P1-R1-01 and "Open actions carried from prior
handovers, round 2" with P1-R2-01 to P1-R2-03), `release/` with 7 components,
`projections/` with the severity-`high` analogues and the cohort of 17, and
`events/admit.jsonl`; every source cites its original by date, section and
SHA-256 and names no repository, branch, file path or local disk path;
`python3 plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py demo --specimen plugins/anamnesis/specimens/estate`
exits zero with two fresh builds agreeing on the estate release id, 17 findings
across 4 rounds, `verdict None` and 17 included against 17; the estate
admission policy under the pilot's curation policy refuses `A074` and `A075`;
`anamnesis.py` is unchanged from step 2's exit; the anamnesis suite is green;
the root suite is green from a clean snapshot; `git diff --check` is clean; the
Horos check exits zero; and
`python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition step:4`
exits zero before the pull request is ready.

**Files.** Create `plugins/anamnesis/specimens/estate/policy.json`,
`curation-policy.json`, `sources/archive-verification-2026-08-31.md`,
`sources/counterparty-history-2026-09-05.md`, `release/` (7 files),
`projections/elenchus-severity-high.json`, `projections/synkrisis-cohort.json`,
`events/admit.jsonl` and `plugins/anamnesis/tests/test_s9_estate.py`. Change
`.horos/boundary.json` and `.horos/census.json`.

**Tests.** Add `plugins/anamnesis/tests/test_s9_estate.py`: two fresh builds of
the estate specimen agree byte for byte and equal the committed release; the
committed release verifies with 17 findings, 4 rounds, 0 remediations and 4
verifications all `unknown`; the estate release id differs from the pilot's;
the committed projections equal fresh ones; the estate admission policy under
the pilot curation policy refuses `A074` and, with a pilot source added,
`A075`; every estate source's `provenance` names a date and a 64-hex digest and
its `rights` are `permission`, `public`, holder Wildcat Labs with a non-empty
statement; and no estate source or policy byte carries a local path prefix, a
URL scheme or a repository slug. The audit runner contract is
`python3 plugins/anamnesis/tests/elenchus.py --step 9 {report}`, its format is
`elenchus.unittest.v1`, and Warden writes
`.hexaemeron/elenchus/anamnesis-step-9.json`. Also run the estate demo, the
anamnesis suite from the repository root, the root suite from a clean snapshot,
and `git diff --check`. Expected new focused tests: 9.

**Disciplines.** phylax: the estate source bytes enter through the existing
admission path (regular file below the policy root, no symlink, byte cap, exact
digest), and the one thing worth taking at this boundary is a repository name,
a path or a credential value, so a guard refuses local path prefixes, URL
schemes and repository slugs in the specimen and the sources are reviewed byte
by byte. ephoros: none, the specimen runs from a terminal and the existing
refusal stream covers it. metron: none, `measure-release` checks the estate
release against the existing 50,000,000-byte cap and no budget is declared.
elenchus: the two refusal specimens are the scope's own bad cases and run
against the parent commit. hypomnema: the rights basis and disclosure of each
estate source are recorded where ADR-003 puts them, in the `rights` object of
the estate `policy.json`, with the maintainer's grant as the statement.

## Step 4: Advance the ledger, reconcile the prose, and run both demo paths

**Goal.** Record the completed frontier job in Anamnesis's ledger, reconcile
every mutable first-party document that still describes the constant or the
old state, and demonstrate the whole path over both specimens.

**Entry.** Step 3's exit state;
`python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition step:4`
exits zero.

**Exit.** `plugins/anamnesis/skills/anamnesis/EVOLUTION.md` carries exactly one
new row valid under the versioning contract: evolution incremented once to
`anamnesis-v4.1.0`, generation and epoch retained, the prior revision
`corpus-scope` and digest
`1da8d2f843cb3b0ff1fd6dac5d41d4cafb5746388635c3f1ba5e41adde1d1f77` preserved
in the `v3.1.0` row, the header and row naming the same version, the row's
Evidence citing ADR-006 and the step 8 and step 9 suites, and either one
evidenced next job or `mature` with `None -- mature`; `SKILL.md` frontmatter
reads `4.1.0`; the marketplace-context blocks in `plugins/anamnesis/README.md`,
`AGENTS.md` and `skills/anamnesis/SKILL.md`, the front-door status block in
`plugins/anamnesis/README.md` and the `Next Fiat job` paragraph in
`plugins/anamnesis/README.md` describe the declared scope and the new held
job, and no first-party document under `plugins/anamnesis/` still says the
scope is a resolver-side constant; both demo paths from the study's problem
statement exit zero; `python3 scripts/check_public_front_door.py`,
`python3 scripts/demonstrations.py check --root .` and
`python3 scripts/portable_promise_machine.py check` exit zero; the anamnesis
suite is green; the root suite is green from a clean snapshot;
`git diff --check` is clean; the Horos check exits zero; and
`python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition integration`
exits zero before the pull request is ready.

**Files.** Change `plugins/anamnesis/skills/anamnesis/EVOLUTION.md`,
`plugins/anamnesis/skills/anamnesis/SKILL.md`, `plugins/anamnesis/README.md`,
`plugins/anamnesis/AGENTS.md`, `plugins/anamnesis/tests/test_s6_ledger.py`
(the `v3.1.0` header assertion moves into a by-version block), any other
first-party document the cold read finds carrying the stale claim,
`.horos/boundary.json` and `.horos/census.json`. Create
`plugins/anamnesis/tests/test_s10_ledger.py`.

**Tests.** Add `plugins/anamnesis/tests/test_s10_ledger.py`: the ledger's
header version is `anamnesis-v4.1.0` and matches its newest row, which is an
`evolution` row; the new row's frontier digest recomputes over the exact
`{status}|{frontier revision}|{current frontier}|{next Fiat job}` line
including its final newline; the `v3.1.0` row keeps revision `corpus-scope`
and digest `1da8d2f8…`; the `SKILL.md` frontmatter matches the header; the
front-door status block names `anamnesis-v4.1.0`; and no live document under
`plugins/anamnesis/` outside `docs/` and the ledger history says
"resolver-side constant". The audit runner contract is
`python3 plugins/anamnesis/tests/elenchus.py --step 10 {report}`, its format is
`elenchus.unittest.v1`, and Warden writes
`.hexaemeron/elenchus/anamnesis-step-10.json`. Also run both demo paths, the
anamnesis suite from the repository root, the root suite from a clean snapshot,
`python3 scripts/portable_promise_machine.py check`, and `git diff --check`.
Expected new focused tests: 6.

**Disciplines.** phylax: none, the step edits documents and reads two
specimens. ephoros: none. metron: none, both demos print their existing
baselines and no budget is declared. elenchus: the prose reconciliation is
driven by a cold read rather than by memory of what was written, so a missed
document is a test failure rather than an oversight. hypomnema: the ledger row
is the durable record of the decision, its home is fixed by the versioning
contract, and it cites ADR-006 rather than restating it.
