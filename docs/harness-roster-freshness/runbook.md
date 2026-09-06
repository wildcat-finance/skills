# Runbook: separate harness roster content from observation age

Derived from `.hexaemeron/study.md` for issue
[#1247](https://github.com/wildcat-finance/skills/issues/1247). Base ref
`5bc2494c4f5802efcd8a92e58554809ac4b9f147` on `main`, run branch
`fiat/1247-decouple-harness-roster-metadata-and-enforc`.

The repository already supplies the Python pin, root test adapter, check graph,
licence, generated-region markers, and PDF builder. Step 1 scaffolds this
change by committing the study, runbook, and numberless decision draft into
their existing homes. No step changes the manifest schema or probe contract.

## The runner contract every step shares

Test command `python3 tests/run_tests.py --elenchus-report {report}`, report
format `elenchus.unittest.v1`, report file
`.elenchus/fiat-1247-step-<N>.json`. Warden receives those three inputs and may
not infer another command from the changed files.

Each exit runs `python3 scripts/run_checks.py --base origin/main` at exit zero
on the committed step tree. If parallel load reports an adapter timeout, rerun
the same plan with `--jobs 1`; that is a scheduling recovery, not authority to
omit a check. No step edits an existing file under `audit/`.

```design-lock
schema | protasis-design-evidence/v1
sha256 | f0aef4b6db072ee7fd4ab4cbb30abeec391371e004f138a29351f60ee6a41681
candidate | separate-hard-freshness
```

## Step 1: Lock the content-and-freshness decision

**Goal.** Commit the run documents and the durable decision that replaces
ADR-079's metadata-coupled surface consequence.

**Entry.** Clean run branch at
`5bc2494c4f5802efcd8a92e58554809ac4b9f147` with the issue-856 harness roster
machinery present.

**Exit.** `docs/harness-roster-freshness/study.md` and
`docs/harness-roster-freshness/runbook.md` are byte-identical to the controller
artefacts. The numberless draft at
`docs/decisions/drafts/separate-harness-roster-content-from-observation-age.md`
records content-only surfaces, a separate hard 30-day budget, no-op PDF writes,
and the exact part of ADR-079 it supersedes. The inherited toolchain, root test
adapter, check graph, licence, schema, and probe remain present. Proved by
`python3 scripts/run_checks.py --base origin/main` at exit zero on the committed
tree.

**Files.** `docs/harness-roster-freshness/study.md`,
`docs/harness-roster-freshness/runbook.md`,
`docs/decisions/drafts/separate-harness-roster-content-from-observation-age.md`,
and `.horos/boundary.json` only if the tracked-file count requires it.

**Tests.** Existing decision-record, documentation, Horos-boundary, and root
checks must remain green; this step adds no executable behavior. Step audit
runner contract is test command
`python3 tests/run_tests.py --elenchus-report {report}`, report format
`elenchus.unittest.v1`, report file `.elenchus/fiat-1247-step-1.json`.

**Disciplines.** phylax: none, this step adds no executable input or process.
ephoros: none, no unattended behavior starts here. metron: none, no performance
claim is made. elenchus: none, the reproduced defect is specified but not fixed
in this step. hypomnema: the dropped surface date, hard age budget, check split,
and no-op PDF path are expensive to reverse, so the numberless draft is their
home.

## Step 2: Separate content drift and enforce manifest age

**Goal.** Make public surfaces depend only on roster content, skip metadata-only
surface writes, and add the hard freshness check to the repository graph.

**Entry.** Step 1's green committed state and its accepted decision draft.

**Exit.** `scripts/render_harness_roster.py` renders no observation metadata,
keeps all existing manifest validation, and does not run the PDF builder when
the existing harness page already matches roster content. `--check` detects
content drift only. `--check-freshness` accepts ages zero through 30 inclusive
and refuses age 31 and future dates. `tests/check-map-v1.json` declares both
reachable checks for the docs scope. The README, guide, PDF, and Horos boundary
are regenerated once for the deliberate content change. Proved by
`python3 -m unittest tests.test_harness_manifest` and
`python3 scripts/run_checks.py --base origin/main`, both at exit zero on the
committed tree.

**Files.** `scripts/render_harness_roster.py`,
`tests/test_harness_manifest.py`, `tests/check-map-v1.json`, `README.md`,
`docs/how-to-help-shoggoth.md`, `docs/pdf/how-to-help-shoggoth.pdf`, and
`.horos/boundary.json`.

**Tests.** Replace the old assertion that each `recorded` field reddens content
drift with a case mutating all three fields and observing no Markdown, PDF
expectation, write, or declared content-check difference. Add exact freshness
boundary cases for ages 0, 30, 31, and -1, malformed metadata refusal, content
drift preservation, PDF-build skipping, and check-map reachability. Step audit
runner contract is test command
`python3 tests/run_tests.py --elenchus-report {report}`, report format
`elenchus.unittest.v1`, report file `.elenchus/fiat-1247-step-2.json`.

**Disciplines.** phylax: the manifest and operator paths remain untrusted, so
existing bounded reads, closed types, credential sweeps, and fixed subprocess
argv must survive. ephoros: the two commands must state whether content drifted
or the manifest exceeded its named age budget. metron: no speed claim; the
zero-write requirement is asserted behavior, not a timing measurement.
elenchus: the metadata-only and stale-age reproductions become cause-level
guards. hypomnema: implementation must match the step-1 decision without
silently changing its budget or comparison boundary.

## Step 3: Demonstrate a no-churn re-probe and a real stale failure

**Goal.** Leave a reproducible public demonstration of both halves of the new
contract and verify the final repository delta.

**Entry.** Step 2's green committed content-only renderer and separate
freshness check.

**Exit.** `docs/harness-roster-freshness/demonstration.md` records commands and
outputs showing: the committed checks green; a staged manifest with only host,
date, and base-ref changes leaves all three surfaces byte-identical and writes
none; a staged 31-day-old manifest fails only the freshness check; and one
harness-content edit still fails the content check. The document names the
30-day budget and the provenance limit. Proved by its listed commands and by
`python3 scripts/run_checks.py --base origin/main` at exit zero on the committed
tree.

**Files.** `docs/harness-roster-freshness/demonstration.md` and
`.horos/boundary.json` only if the tracked-file count requires it.

**Tests.** Re-run `python3 -m unittest tests.test_harness_manifest`, both direct
harness commands, and the complete delta plan. No new executable case is owed
unless the demonstration finds a failure not already guarded. Step audit
runner contract is test command
`python3 tests/run_tests.py --elenchus-report {report}`, report format
`elenchus.unittest.v1`, report file `.elenchus/fiat-1247-step-3.json`.

**Disciplines.** phylax: use only temporary copies and fixed local commands;
publish no host path or credential. ephoros: preserve the exact success and
refusal lines that answer the two operator questions. metron: none, no runtime
comparison is claimed. elenchus: if the demo contradicts a guard, reproduce
and fix that cause before recording success. hypomnema: the demonstration is
evidence for the existing decision, not a second decision record.

### Amendment -- 2026-09-05

**What changed.** Complete replacement Goal: Commit the run documents and the durable decision that replaces ADR-079's metadata-coupled surface consequence, and repair Hypomnema so its explicit study bridge recognizes that repository-valid numberless draft without weakening H008. Complete replacement Exit: `docs/harness-roster-freshness/study.md` and `docs/harness-roster-freshness/runbook.md` are byte-identical to the controller artefacts. The numberless draft at `docs/decisions/drafts/separate-harness-roster-content-from-observation-age.md` records content-only surfaces, a separate hard 30-day budget, no-op PDF writes, and the exact part of ADR-079 it supersedes. Hypomnema `5.8.0` accepts a directly nested, shape-valid `docs/decisions/drafts/<slug>.md` target whose filename and stable identity agree, while its unsafe-path, malformed-record, wrong-home, duplicate, numbered-ADR, and governed-ledger results remain unchanged. The held `duplicate-home-discovery` frontier revision and digest are byte-identical to `5.7.0`. A regression is observed failing on the unfixed checker and passing on the repaired checker. The inherited toolchain, root test adapter, check graph, licence, schema, and probe remain present. Proved by the focused Hypomnema test, `python3 plugins/hexaemeron/tests/run_tests.py`, and `python3 scripts/run_checks.py --base origin/main`, all at exit zero on the committed tree. Complete replacement Files: `docs/harness-roster-freshness/study.md`, `docs/harness-roster-freshness/runbook.md`, `docs/decisions/drafts/separate-harness-roster-content-from-observation-age.md`, `plugins/hexaemeron/skills/hypomnema/SKILL.md`, `plugins/hexaemeron/skills/hypomnema/EVOLUTION.md`, `plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py`, `plugins/hexaemeron/tests/test_hypomnema_checker.py`, and `.horos/boundary.json` only if the tracked-file count requires it. Complete replacement Tests: Add a focused case that invokes study mode with a selected candidate bridged to a directly nested numberless draft, prove that case fails as H008 on the unfixed checker, then prove it passes after repair. Add negative cases for a malformed draft shape and filename/identity mismatch, and retain existing numbered-ADR, governed-ledger, wrong-home, unsafe-path, and duplicate results. Run `python3 -m unittest plugins.hexaemeron.tests.test_hypomnema_checker`, `python3 plugins/hexaemeron/tests/run_tests.py`, and `python3 scripts/run_checks.py --base origin/main`. Step audit runner contract is test command `python3 tests/run_tests.py --elenchus-report {report}`, report format `elenchus.unittest.v1`, report file `.elenchus/fiat-1247-step-1.json`. Complete replacement Disciplines: phylax: retain stable bounded reads, portable repository-relative paths, symlink and special-file refusals, and fixed input ceilings; no new external input or subprocess boundary is introduced. ephoros: preserve H008's exact path-bound diagnostic and zero-exit success contract; no unattended behavior starts here. metron: none, no performance claim is made. elenchus: preserve the exact draft-target H008 reproduction, run the new guard against the unfixed checker before repair, state the cause as the home classifier omitting its own draft lifecycle, and require focused plus full suites green. hypomnema: update the mechanical and Promise Machine descriptions to name valid draft homes, record the generation in `EVOLUTION.md`, and preserve the current frontier revision, digest, status, and next job exactly.

**Why.** Step 1 cannot satisfy its receipted design bridge because Hypomnema's
study-mode home classifier rejects the numberless draft path that Hypomnema's
own authoring and merge-assignment contract requires. The replacement fields
make the repair, regression evidence, version ledger, and unchanged refusal
boundary part of the source-bound step rather than an out-of-band edit.

**Steps touched.** Step 1 only.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds.

### Amendment -- 2026-09-05

**What changed.** Complete replacement Exit: `docs/harness-roster-freshness/study.md` and `docs/harness-roster-freshness/runbook.md` are byte-identical to the controller artefacts. The numberless draft at `docs/decisions/drafts/separate-harness-roster-content-from-observation-age.md` records content-only surfaces, a separate hard 30-day budget, no-op PDF writes, and the exact part of ADR-079 it supersedes. Hypomnema `5.8.0` accepts a directly nested, shape-valid `docs/decisions/drafts/<slug>.md` target whose filename carries a valid stable identity, while its unsafe-path, malformed-record, wrong-home, duplicate, numbered-ADR, and governed-ledger results remain unchanged. The held `duplicate-home-discovery` frontier revision and digest are byte-identical to `5.7.0`, and the reviewed Hypomnema bytes are rebound in the Promise Machine coverage inventory. The agent-instruction prover ignores this run's unrelated design candidate set and retains its own exact closed fallback. Both reproduced failures have cause-level regressions observed red before their fixes and green afterwards. The inherited toolchain, root test adapter, check graph, licence, schema, and probe remain present. Proved by the focused regressions, `python3 plugins/hexaemeron/tests/run_tests.py`, and `python3 scripts/run_checks.py --base origin/main`, all at exit zero on the committed tree. Complete replacement Files: `docs/harness-roster-freshness/study.md`, `docs/harness-roster-freshness/runbook.md`, `docs/decisions/drafts/separate-harness-roster-content-from-observation-age.md`, `plugins/hexaemeron/skills/hypomnema/SKILL.md`, `plugins/hexaemeron/skills/hypomnema/EVOLUTION.md`, `plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py`, `plugins/hexaemeron/tests/test_hypomnema_checker.py`, `scripts/prove_agent_instruction_reconciliation.py`, `tests/test_agent_instruction_corpus.py`, `tests/promise_machine_coverage.json`, and `.horos/boundary.json` only if the tracked-file count requires it. Complete replacement Tests: Retain the focused Hypomnema cases from the prior amendment. Add a root prover case showing that an unrelated valid Fiat candidate set cannot replace the prover's four closed candidates, while the exact matching set remains accepted. Rebind and check the Promise Machine runtime digest after the Hypomnema bytes are final. Run the focused Hypomnema and agent-instruction modules, `python3 plugins/hexaemeron/tests/run_tests.py`, and `python3 scripts/run_checks.py --base origin/main`. Because dead-code currency requires a committed tree, the final delta plan runs after the signed Step 1 commit; any failure is repaired and amended before audit. Step audit runner contract is test command `python3 tests/run_tests.py --elenchus-report {report}`, report format `elenchus.unittest.v1`, report file `.elenchus/fiat-1247-step-1.json`. Complete replacement Disciplines: phylax: retain stable bounded reads, portable repository-relative paths, symlink and special-file refusals, fixed input ceilings, strict closed candidate ids, and no new external or subprocess boundary. ephoros: preserve H008's exact path-bound diagnostic and zero-exit success contract; no unattended behavior starts here. metron: none, no performance claim is made. elenchus: preserve both exact reproductions, require each new guard red before repair and green after, state each cause as a mechanism, and require focused plus full suites green. hypomnema: update the mechanical and Promise Machine descriptions to name valid draft homes, record the generation in `EVOLUTION.md`, preserve the current frontier revision, digest, status, and next job exactly, and bind the final skill digest in the coverage inventory.

**Why.** The repository delta plan requires an exact Promise Machine digest
for changed skill bytes and runs the root self-test inside this live Fiat
worktree. Without the prover boundary, that self-test consumes issue #1247's
unrelated design candidates and refuses its own declared candidate before any
proof runs.

**Steps touched.** Step 1 only.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds.
