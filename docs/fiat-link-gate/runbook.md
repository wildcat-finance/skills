# Runbook: gate study and runbook links before their digests are pinned

Three steps build `require-location-independent` from the study receipted at
`.hexaemeron/study.md`. Step 1 commits the design records and changes no
behaviour. Step 2 adds the pointer rule to the four receipts that pin a study or
runbook digest, and pays every re-pin those edits force, the generation row and
version bump included: `CHECKPOINT_COMPATIBLE_CONTROLLER_VERSIONS` is itself a
`hexctl.py` edit, and a second controller edit would repeat the digest cascade.
Step 3 runs the demonstration and gives the Surveyor the rule.

Every step is green at both ends. Each Exit names the root suite and the
Hexaemeron suite, run on a detached snapshot of the step head, because the three
audit lints run neither. A later step is cut from the previous step's `--audit`
head when that branch carries commits, since the audit fixes live there.

```design-lock
schema | protasis-design-evidence/v1
sha256 | 91bf0bca556227725c060e4bb7ded86cdc4d93b642ddbed61b75178dda83c0e1
candidate | require-location-independent
```

## Step 1: Commit the design records

**Goal.** Land the receipted study, runbook, design record, resolver and 18
reports under `docs/fiat-link-gate/` byte for byte, with no behaviour changed.

**Entry.** The run branch at `485c90d3ad545b696584197f83d942c705988216` with the
receipted `.hexaemeron/` artefacts in place, and
`design_evidence.py .hexaemeron/design-evidence.json --transition step:1`
exiting 0.

**Exit.** The four committed files and the 18 reports match their `.hexaemeron/`
sources byte for byte, and the committed record passes the design checker from
its own directory. The check map's Hypomnema, Phylax and Ephoros argv are clean,
and Imprimatur finds no defect in either committed document. The Horos artefacts
are regenerated after staging, and both suites exit 0 on a detached snapshot of
the step head. Prove it with:

```bash
for f in study.md runbook.md design-evidence.json resolve.py; do cmp ".hexaemeron/$f" "docs/fiat-link-gate/$f"; done
diff -r .hexaemeron/reports docs/fiat-link-gate/reports
python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py docs/fiat-link-gate/design-evidence.json --transition design-lock
python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition step:2
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests scripts docs
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests scripts docs
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-link-gate/study.md docs/fiat-link-gate/runbook.md --max-defects 0
python3 plugins/horos/skills/horos/scripts/horos.py scan . --write
python3 plugins/horos/skills/horos/scripts/horos.py scan . --census --write
git diff --check
git worktree add --detach tmp/fiat-1086-step-1-snapshot HEAD
(cd tmp/fiat-1086-step-1-snapshot && python3 -m unittest discover -t . -s tests)
(cd tmp/fiat-1086-step-1-snapshot && python3 plugins/hexaemeron/tests/run_tests.py --jobs 8)
```

**Files.** Create `docs/fiat-link-gate/study.md`,
`docs/fiat-link-gate/runbook.md`, `docs/fiat-link-gate/design-evidence.json`,
`docs/fiat-link-gate/resolve.py` and the 18 `.json` reports under
`docs/fiat-link-gate/reports/`, each copied from `.hexaemeron/`. Change
`.horos/boundary.json`, `.horos/candidates.json` and `.horos/census.json` where
the scans move them.

**Tests.** None added. The `cmp` and `diff -r` commands hold the copies, and the
check map's `lint-hypomnema`, `lint-phylax` and `lint-ephoros` cover `docs/`
from here on. The audit-fix runner for a guard under the root `tests/` is
`python3 tests/run_tests.py --elenchus-report {report}`, report format
`unittest-json-v1`, report file `.elenchus/fiat-1086-step-1.json`; a guard under
`plugins/hexaemeron/tests/` uses
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}` with
the same format and report file.

**Disciplines.** phylax: the committed resolver runs the bundled checker with
fixed argv and writes only to a new `--out` path, and the step opens no product
boundary. ephoros: none, nothing here runs unattended. metron: none, the step
makes no performance claim. elenchus: none, no failure is in hand at entry.
hypomnema: the records' committed home is fixed here, so Step 2's decision draft
and ledger row can cite it.

## Step 2: Refuse location-dependent pointers before a receipt pins a digest

**Goal.** Make `done study`, `done runbook`, `amend study` and `amend runbook`
refuse a location-dependent pointer, or one the bundled Hypomnema check cannot
resolve, before any write; record the decision, the phase note and the
generation row; and re-pin every artefact those edits move.

**Entry.** Step 1's exit state, cut from Step 1's `--audit` head when that
branch carries commits, with
`design_evidence.py .hexaemeron/design-evidence.json --transition step:2`
exiting 0.

**Exit.** The behaviour:

- `hexctl.py` loads the bundled `hypomnema.py` in-process from the plugin root,
  resolved with `realpath` and required to be a regular file, and uses its
  `LINK`, `RUNBOOK`, `suppressed`, `_external`, `_code_spans` and `_within`. A
  missing module or name refuses.
- A recognised pointer that is neither an absolute URL with a skipped scheme nor
  an in-page anchor refuses at every depth, a `/`-rooted path included.
- The bundled checker then runs as a bounded subprocess with fixed argv, no shell
  and `--format json`, over the captured bytes in a controlled temporary file
  under the run-state directory whose name no Hypomnema path rule selects, with
  `docs/decisions` in scope when it exists. Any finding on the artefact refuses,
  and so do a timeout, an output overflow and JSON outside the closed shape.
- `done study` and `done runbook` check the whole artefact. `amend study` and
  `amend runbook` check only the bytes the amendment appends.
- Each refusal exits 2 before any state, ledger or artefact write, names the
  artefact, line, pointer target and refusing stage in bounded printable text,
  and carries no raw child output.
- A conforming artefact receipts exactly as before. No contract key, receipt
  field, ledger event field or packet field is added.

The records and pins:

- The `**Study and runbook.**` phase note in
  `plugins/hexaemeron/skills/fiat/SKILL.md` states the rule after byte 23631, and
  `metadata.version` reads `6.57.1`. No byte from 18784 to 23112 changes, and the
  version line keeps its length.
- A decision draft at
  `docs/decisions/drafts/refuse-location-dependent-pointers-before-a-receipt-pins-a-digest.md`
  opens with `# Decision:` and records study decisions 12.1 and 12.2, with
  `declare-only` and `lint-in-place` as the rejected alternatives. It cites
  sources by commit-pinned URL or code-span path, so it passes the rule and
  survives numbering.
- `plugins/hexaemeron/skills/fiat/EVOLUTION.md` reads `fiat-v6.57.1` and gains
  exactly one generation row. The row keeps revision `delegated-task-identity`
  and digest `a54452aef0e415d7d17a548751178de0804d22af4829255b3c5d8bfe289581f1`,
  and the status, frontier text and held job stay byte-identical.
  `tests/test_evolution_contract.py` checks the `fiat-v6.56.1` row by version and
  the new row as the head.
- `CHECKPOINT_COMPATIBLE_CONTROLLER_VERSIONS` gains `fiat-v6.57.1`, and
  Hexaemeron reads `1.6.38` at all six version sites.
- Every pin study section 3 lists is current: the coverage record; the
  agent-instruction manifest and its three `fiat-study-runbook-phase` fixtures,
  re-pinned through the prover's `prepare` and `apply`;
  `fiat-final-integration.json`; `evaluation-run.json`, re-tallied from its
  committed answers with the recorded model and date; the demonstration pair; and
  the three Horos artefacts. No evaluation answer, measurement or parity record
  is re-obtained.

Prove it with:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_link_gate -v
python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition step:3
python3 scripts/agent_instruction.py check --manifest tests/fixtures/agent-instruction-v1/manifest.json
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py sync --check
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests scripts docs
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests scripts docs
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/fiat/SKILL.md docs/decisions/drafts/refuse-location-dependent-pointers-before-a-receipt-pins-a-digest.md --max-defects 0
python3 plugins/hexaemeron/skills/hypomnema/scripts/decision_assignments.py plan --repo . --base "$(git rev-parse origin/main)" --base-ref refs/remotes/origin/main --product "$(git rev-parse HEAD)" --report tmp/fiat-1086-step-2-decision-plan.json
for f in study.md runbook.md; do cmp ".hexaemeron/$f" "docs/fiat-link-gate/$f"; done
python3 plugins/horos/skills/horos/scripts/horos.py scan . --write
python3 plugins/horos/skills/horos/scripts/horos.py scan . --census --write
git diff --check
git worktree add --detach tmp/fiat-1086-step-2-snapshot HEAD
(cd tmp/fiat-1086-step-2-snapshot && python3 -m unittest discover -t . -s tests)
(cd tmp/fiat-1086-step-2-snapshot && python3 plugins/hexaemeron/tests/run_tests.py --jobs 8)
```

**Files.** Change `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/skills/fiat/SKILL.md`,
`plugins/hexaemeron/skills/fiat/EVOLUTION.md`, `tests/test_evolution_contract.py`,
`tests/test_version_propagation.py`,
`plugins/hexaemeron/tests/test_phylax_model_proxy.py`,
`.agents/plugins/marketplace.json`, `.claude-plugin/marketplace.json`,
`plugins/hexaemeron/.claude-plugin/plugin.json`,
`plugins/hexaemeron/.codex-plugin/plugin.json`,
`tests/promise_machine_coverage.json`,
`tests/fixtures/agent-instruction-v1/manifest.json`,
`tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/model.json`,
`tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/source-spans.json`,
`tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/compact.wai`,
`tests/fixtures/promise-machine/runtime/fiat-final-integration.json`,
`docs/promise-machine/obligation-gates/evaluation-run.json`,
`docs/promise-machine/obligation-gates/demonstration-run.json`,
`docs/promise-machine/obligation-gates/demonstration-evidence.md`,
`.horos/boundary.json`, `.horos/candidates.json` and `.horos/census.json`. Create
`plugins/hexaemeron/tests/test_link_gate.py` and
`docs/decisions/drafts/refuse-location-dependent-pointers-before-a-receipt-pins-a-digest.md`.
Change an existing test only where its copied plugin root must now carry
`skills/hypomnema/scripts/hypomnema.py`, such as
`plugins/hexaemeron/tests/test_hexctl_checkpoint_identity.py`, together with
every fixture that pins that test file's SHA-256. Change
`tests/fixtures/agent-instruction-v1/evidence/measurement.json` and
`tests/fixtures/agent-instruction-v1/evidence/parity.json` only if the prover
names them. Refresh `docs/fiat-link-gate/study.md` and
`docs/fiat-link-gate/runbook.md` from `.hexaemeron/` when an amendment has moved
either.

**Tests.** Add `plugins/hexaemeron/tests/test_link_gate.py` rather than extending
`test_hexctl.py` or `test_fiat_skill.py`, whose digests five fixtures pin. It
covers:

1. `done study` over the five `../<skill>/SKILL.md` citations the skills#1070
   run froze exits 2, names the first line and target, and leaves `state.json`
   and `ledger.jsonl` byte-identical.
2. A file-relative link that resolves from `.hexaemeron/` is still refused.
3. A `/`-rooted link, a link inside a `~~~` block and a `runbook:` keyword
   pointer are each refused.
4. A commit-pinned absolute URL, an in-page anchor, a code-span path and a
   pointer under Hypomnema's allow pragma are accepted.
5. Identical bytes get one verdict at `.hexaemeron/study.md`, two directories
   deep and four deep.
6. `done runbook` refuses the specimen with state and ledger unchanged, and
   accepts a conforming runbook.
7. `amend study` and `amend runbook` refuse an appended location-dependent
   pointer, and accept a conforming amendment to a run whose receipted prefix
   already carries one.
8. A missing `hypomnema.py`, a missing name, a checker timeout and malformed
   checker output each refuse.
9. The committed `docs/fiat-link-gate/study.md` and
   `docs/fiat-link-gate/runbook.md` pass the rule.
10. A line holding tens of thousands of backticks is scanned in linear time.
11. The SKILL.md phase note names the four receipts and the appended-bytes check.

Every refusal case fails against the step's parent and passes on the fix. The
`evaluation-run.json` re-tally is accepted only after packets emitted from the
parent and from this tree differ in `tree_sha256` alone. The audit-fix runner is
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`,
report format `unittest-json-v1`, report file `.elenchus/fiat-1086-step-2.json`;
a guard under the root `tests/` uses
`python3 tests/run_tests.py --elenchus-report {report}` with the same format and
report file.

**Disciplines.** phylax: the controller now runs a bundled script over bytes a
worker wrote, so the module path, argv, timeout, output cap, closed JSON shape
and the nonprinting check on an echoed target are this step's to hold (study
section 9). ephoros: the refusal is the only signal owed, and it names the
artefact, line, target and stage (study section 8). metron: none, no budget is
declared and nothing changes for speed. elenchus: each refusal case names its
specimen and fails against the parent, and a red digest test is repaired by
re-pinning its record, never by loosening the assertion. hypomnema: the rule and
its construction choices are expensive to reverse, so the decision draft records
them and the ledger row points at it.

## Step 3: Demonstrate the gate and give the Surveyor the rule

**Goal.** Run the study's demo path end to end with the Step 2 controller, commit
the transcript, and state the pointer rule where the Surveyor reads its brief.

**Entry.** Step 2's exit state, cut from Step 2's `--audit` head when that
branch carries commits, with
`design_evidence.py .hexaemeron/design-evidence.json --transition step:3`
exiting 0.

**Exit.** In a throwaway repository under the ignored `tmp/`, a run initialised
by the worktree's own `hexctl.py` and holding this run's design record and
reports refuses a study carrying the five frozen citations with exit 2. The
refusal names the first line and target, and the SHA-256 digests of the
throwaway run's `state.json` and `ledger.jsonl` are identical before and after.
The same study with each citation pinned to `485c90d3` receipts with exit 0.
`docs/fiat-link-gate/demonstration.md` records the commands, outputs and both
digest pairs, with local absolute paths replaced by `<worktree>`, and holds the
specimen inside a backtick fence. `plugins/hexaemeron/agents/surveyor.md` tells
the Surveyor, outside its generated marketplace-context block, that a study's
links must be absolute URLs or in-page anchors. Prove it with:

```bash
hexctl="$PWD/plugins/hexaemeron/skills/fiat/scripts/hexctl.py"
demo="$PWD/tmp/fiat-1086-demo"
mkdir "$demo"
git -C "$demo" init -q -b main
git -C "$demo" -c commit.gpgsign=false -c user.name=demo -c user.email=demo@example.invalid commit -q --allow-empty -m demo
python3 "$hexctl" --dir "$demo" init --topic "link gate demonstration"
run="$demo/tmp/fiat/fiat-link-gate-demonstration"
cp .hexaemeron/design-evidence.json "$run/.hexaemeron/"
cp -R .hexaemeron/reports "$run/.hexaemeron/"
{ printf '# Specimen\n\n'; for s in ephoros phylax metron elenchus hypomnema; do printf 'See [%s](../%s/SKILL.md) for its contract.\n' "$s" "$s"; done; } > "$run/.hexaemeron/study.md"
shasum -a 256 "$run/.hexaemeron/state.json" "$run/.hexaemeron/ledger.jsonl"
(cd "$run" && python3 "$hexctl" --dir . done study --artifact .hexaemeron/study.md --skills hexaemeron:protasis); echo "exit=$?"
shasum -a 256 "$run/.hexaemeron/state.json" "$run/.hexaemeron/ledger.jsonl"
{ printf '# Specimen\n\n'; for s in ephoros phylax metron elenchus hypomnema; do printf 'See [%s](https://github.com/wildcat-finance/skills/blob/485c90d3ad545b696584197f83d942c705988216/plugins/hexaemeron/skills/%s/SKILL.md) for its contract.\n' "$s" "$s"; done; } > "$run/.hexaemeron/study.md"
(cd "$run" && python3 "$hexctl" --dir . done study --artifact .hexaemeron/study.md --skills hexaemeron:protasis); echo "exit=$?"
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-link-gate/demonstration.md plugins/hexaemeron/agents/surveyor.md --max-defects 0
python3 scripts/promise_machine.py check
python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition integration
for f in study.md runbook.md; do cmp ".hexaemeron/$f" "docs/fiat-link-gate/$f"; done
python3 plugins/horos/skills/horos/scripts/horos.py scan . --write
python3 plugins/horos/skills/horos/scripts/horos.py scan . --census --write
git diff --check
git worktree add --detach tmp/fiat-1086-step-3-snapshot HEAD
(cd tmp/fiat-1086-step-3-snapshot && python3 -m unittest discover -t . -s tests)
(cd tmp/fiat-1086-step-3-snapshot && python3 plugins/hexaemeron/tests/run_tests.py --jobs 8)
```

**Files.** Create `docs/fiat-link-gate/demonstration.md`. Change
`plugins/hexaemeron/agents/surveyor.md`, and `.horos/boundary.json`,
`.horos/candidates.json` and `.horos/census.json` where the scans move them.
Refresh `docs/fiat-link-gate/study.md` and `docs/fiat-link-gate/runbook.md` from
`.hexaemeron/` when an amendment has moved either.

**Tests.** None added. The transcript is the evidence, and Step 2's cases hold
the behaviour. The audit-fix runner for a guard under the root `tests/` is
`python3 tests/run_tests.py --elenchus-report {report}`, report format
`unittest-json-v1`, report file `.elenchus/fiat-1086-step-3.json`; a guard under
`plugins/hexaemeron/tests/` uses
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}` with
the same format and report file.

**Disciplines.** phylax: none, the demonstration drives the controller in a
throwaway repository under the ignored `tmp/`, and the step opens no product
boundary. ephoros: none, nothing runs unattended. metron: none, the step makes no
performance claim. elenchus: the demonstration reproduces the frozen defect
before it shows the refusal, and a transcript that disagrees with a rerun is
worked to its cause. hypomnema: the transcript sits beside the design records it
demonstrates, and the Surveyor's brief carries the rule rather than a copy of the
decision.

### Amendment -- 2026-09-14

**What changed.**

Complete replacement Exit: `hexctl.py` loads the bundled `hypomnema.py` in-process from the plugin root, resolved with `realpath` and required to be a regular file, and uses its `LINK`, `RUNBOOK`, `suppressed`, `_external`, `_code_spans` and `_within`; a missing module or name refuses. A recognised pointer that is neither an absolute URL with a skipped scheme nor an in-page anchor refuses at every depth, a `/`-rooted path included. The bundled checker then runs as a bounded subprocess with fixed argv, no shell and `--format json`, over the captured bytes in a controlled temporary file under the run-state directory whose name no Hypomnema path rule selects, with `docs/decisions` in scope when it exists; any finding on the artefact refuses, and so do a timeout, an output overflow and JSON outside the closed shape. `done study` and `done runbook` check the whole artefact, and `amend study` and `amend runbook` check only the bytes the amendment appends. Each refusal exits 2 before any state, ledger or artefact write, names the artefact, line, pointer target and refusing stage in bounded printable text, and carries no raw child output. A conforming artefact receipts exactly as before, and no contract key, receipt field, ledger event field or packet field is added. The `**Study and runbook.**` phase note in `plugins/hexaemeron/skills/fiat/SKILL.md` states the rule after byte 23631, and `metadata.version` reads `6.57.1`; no byte from 18784 to 23112 changes, and the version line keeps its length. A decision draft at `docs/decisions/drafts/refuse-location-dependent-pointers-before-a-receipt-pins-a-digest.md` opens with `# Decision:` and records study decisions 12.1 and 12.2, with `declare-only` and `lint-in-place` as the rejected alternatives; it cites sources by commit-pinned URL or code-span path, so it passes the rule and survives numbering. `plugins/hexaemeron/skills/fiat/EVOLUTION.md` reads `fiat-v6.57.1` and gains exactly one generation row, which keeps revision `delegated-task-identity` and digest `a54452aef0e415d7d17a548751178de0804d22af4829255b3c5d8bfe289581f1`, with the status, frontier text and held job byte-identical; `tests/test_evolution_contract.py` checks the `fiat-v6.56.1` row by version and the new row as the head. `CHECKPOINT_COMPATIBLE_CONTROLLER_VERSIONS` gains `fiat-v6.57.1`, and Hexaemeron reads `1.6.39` at all six version sites, one above the `1.6.38` that `origin/main` carries at `d17990cb7f65aabbde83cc34030ad61dadaaface`. Every pin study section 3 lists is current: the coverage record; the agent-instruction manifest and its three `fiat-study-runbook-phase` fixtures, re-pinned through the prover's `prepare` and `apply`; `fiat-final-integration.json`; `evaluation-run.json`, re-tallied from its committed answers with the recorded model and date; the demonstration pair; and the three Horos artefacts. No evaluation answer, measurement or parity record is re-obtained. Prove it with:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_link_gate -v
python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition step:3
python3 scripts/agent_instruction.py check --manifest tests/fixtures/agent-instruction-v1/manifest.json
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py sync --check
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests scripts docs
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests scripts docs
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/fiat/SKILL.md docs/decisions/drafts/refuse-location-dependent-pointers-before-a-receipt-pins-a-digest.md --max-defects 0
python3 plugins/hexaemeron/skills/hypomnema/scripts/decision_assignments.py plan --repo . --base "$(git rev-parse origin/main)" --base-ref refs/remotes/origin/main --product "$(git rev-parse HEAD)" --report tmp/fiat-1086-step-2-decision-plan.json
for f in study.md runbook.md; do cmp ".hexaemeron/$f" "docs/fiat-link-gate/$f"; done
python3 plugins/horos/skills/horos/scripts/horos.py scan . --write
python3 plugins/horos/skills/horos/scripts/horos.py scan . --census --write
git diff --check
git worktree add --detach tmp/fiat-1086-step-2-snapshot HEAD
(cd tmp/fiat-1086-step-2-snapshot && python3 -m unittest discover -t . -s tests)
(cd tmp/fiat-1086-step-2-snapshot && python3 plugins/hexaemeron/tests/run_tests.py --jobs 8)
```

Complete replacement Tests: Add `plugins/hexaemeron/tests/test_link_gate.py` rather than extending `test_hexctl.py` or `test_fiat_skill.py`, whose digests five fixtures pin. It covers: `done study` over the five `../<skill>/SKILL.md` citations the skills#1070 run froze exits 2, names the first line and target, and leaves `state.json` and `ledger.jsonl` byte-identical; a file-relative link that resolves from `.hexaemeron/` is still refused; a `/`-rooted link, a link inside a `~~~` block and a `runbook:` keyword pointer are each refused; a commit-pinned absolute URL, an in-page anchor, a code-span path, a pointer under Hypomnema's allow pragma and a relative link inside a backtick fence are accepted; with a valid decision record under `docs/decisions`, a stable decision reference to that record's slug in a code span and a superseding pointer to that record's number are each accepted, and each is refused when no record carries the slug or number; identical bytes get one verdict at `.hexaemeron/study.md`, two directories deep and four deep; `done runbook` refuses the specimen with state and ledger unchanged, and accepts a conforming runbook; `amend study` and `amend runbook` refuse an appended location-dependent pointer, and accept a conforming amendment to a run whose receipted prefix already carries one; a missing `hypomnema.py`, a missing name, a checker timeout and malformed checker output each refuse; the committed `docs/fiat-link-gate/study.md` and `docs/fiat-link-gate/runbook.md` pass the rule; a line holding tens of thousands of backticks is scanned in linear time; and the SKILL.md phase note names the four receipts and the appended-bytes check. Every refusal case fails against the step's parent and passes on the fix. The `evaluation-run.json` re-tally is accepted only after packets emitted from the parent and from this tree differ in `tree_sha256` alone. The audit-fix runner is `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`, report format `unittest-json-v1`, report file `.elenchus/fiat-1086-step-2.json`; a guard under the root `tests/` uses `python3 tests/run_tests.py --elenchus-report {report}` with the same format and report file.

**Why.** Two changes, both found after Step 1 closed. S1-R1-01 in `audit/rounds/fiat-1086-gate-study-and-runbook-links-before-their-d.md` found that no Tests case held the two forms the study's `false-refusal` risk accepts only with `docs/decisions` in scope: a stable decision reference and a superseding pointer. The committed prototype checks an artefact alone and refuses both, so a gate built the same way would pass every listed case, while `docs/ephoros-typescript-rule-parity-study.md:104` and `docs/ledger-declared-inputs-runbook.md:230` already carry the first form. The same round's unraised lead found that Hypomnema exposes no fence reader, so the rule copies its backtick toggle; the added fence case holds that copy to Hypomnema's reading, beside the `~~~` refusal already listed. Separately, `origin/main` moved from `485c90d3ad545b696584197f83d942c705988216` to `d17990cb7f65aabbde83cc34030ad61dadaaface` after Step 1 was built, and the merged run set Hexaemeron to `1.6.38` at the six version sites the old Exit named, so building `1.6.38` here would give two different releases one version. The replacement Exit names `1.6.39` and restates every other clause unchanged, in one paragraph.

**Steps touched.** Step 2

**Still holding.** Step 2: entry holds; exit holds. Step 3: entry holds; exit holds.

### Amendment -- 2026-09-14

**What changed.**

Complete replacement Exit: `hexctl.py` loads the bundled `hypomnema.py` in-process from the plugin root, resolved with `realpath` and required to be a regular file, and uses its `LINK`, `RUNBOOK`, `suppressed`, `_external`, `_code_spans` and `_within`; a missing module or name refuses. A recognised pointer that is neither an absolute URL with a skipped scheme nor an in-page anchor refuses at every depth, a `/`-rooted path included. The bundled checker then runs as a bounded subprocess with fixed argv, no shell and `--format json`, over the captured bytes in a controlled temporary file under the run-state directory whose name no Hypomnema path rule selects, with `docs/decisions` in scope when it exists; any finding on the artefact refuses, and so do a timeout, an output overflow and JSON outside the closed shape. `done study` and `done runbook` check the whole artefact, and `amend study` and `amend runbook` check only the bytes the amendment appends. Each refusal exits 2 before any state, ledger or artefact write, names the artefact, line, pointer target and refusing stage in bounded printable text, and carries no raw child output. A conforming artefact receipts exactly as before, and no contract key, receipt field, ledger event field or packet field is added. The `**Study and runbook.**` phase note in `plugins/hexaemeron/skills/fiat/SKILL.md` states the rule after byte 23631, and `metadata.version` reads `6.57.1`; no byte from 18784 to 23112 changes, and the version line keeps its length. A decision draft at `docs/decisions/drafts/refuse-location-dependent-pointers-before-a-receipt-pins-a-digest.md` opens with `# Decision:` and records study decisions 12.1 and 12.2, with `declare-only` and `lint-in-place` as the rejected alternatives; it cites sources by commit-pinned URL or code-span path, so it passes the rule and survives numbering. `plugins/hexaemeron/skills/fiat/EVOLUTION.md` reads `fiat-v6.57.1` and gains exactly one generation row, which keeps revision `delegated-task-identity` and digest `a54452aef0e415d7d17a548751178de0804d22af4829255b3c5d8bfe289581f1`, with the status, frontier text and held job byte-identical; `tests/test_evolution_contract.py` checks the `fiat-v6.56.1` row by version and the new row as the head. `CHECKPOINT_COMPATIBLE_CONTROLLER_VERSIONS` gains `fiat-v6.57.1`, and Hexaemeron reads `1.6.39` at all six version sites, one above the `1.6.38` that `origin/main` carries at `d17990cb7f65aabbde83cc34030ad61dadaaface`. Every pin study section 3 lists is current: the coverage record; the agent-instruction manifest and its three `fiat-study-runbook-phase` fixtures, re-pinned through the prover's `prepare` and `apply`; `fiat-final-integration.json`; `evaluation-run.json`, re-tallied from its committed answers with the recorded model and date; the demonstration pair; and the three Horos artefacts. No evaluation answer, measurement or parity record is re-obtained. Prove it with:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_link_gate -v
python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition step:3
python3 scripts/agent_instruction.py check --manifest tests/fixtures/agent-instruction-v1/manifest.json
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py sync --check
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests scripts docs
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests scripts docs
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/fiat/SKILL.md docs/decisions/drafts/refuse-location-dependent-pointers-before-a-receipt-pins-a-digest.md --max-defects 0
python3 plugins/hexaemeron/skills/hypomnema/scripts/decision_assignments.py plan --repo . --base 485c90d3ad545b696584197f83d942c705988216 --base-ref refs/heads/fiat/1086-gate-study-and-runbook-links-before-their-d --product "$(git rev-parse HEAD)" --report .hexaemeron/decision-plan-step-2.json
for f in study.md runbook.md; do cmp ".hexaemeron/$f" "docs/fiat-link-gate/$f"; done
python3 plugins/horos/skills/horos/scripts/horos.py scan . --write
python3 plugins/horos/skills/horos/scripts/horos.py scan . --census --write
git diff --check
git worktree add --detach tmp/fiat-1086-step-2-snapshot HEAD
(cd tmp/fiat-1086-step-2-snapshot && python3 -m unittest discover -t . -s tests)
(cd tmp/fiat-1086-step-2-snapshot && python3 plugins/hexaemeron/tests/run_tests.py --jobs 8)
```

**Why.** Command 10 of the Exit, the `decision_assignments.py plan` dry run, could not pass as written. It named `origin/main` as the base, and `origin/main` at `d17990cb7f65aabbde83cc34030ad61dadaaface` is not an ancestor of the step head, so the planner refused `object-ancestry`; its `tmp/` report path also breaks the planner's rule that a report sits at `.hexaemeron/<name>.json`, so it would refuse `report-path` even on a valid base. Measured on step head `a4456e0a6d7969312562484e3ac1c3617e9b3075`: the same plan against the run base `485c90d3ad545b696584197f83d942c705988216`, named by the run branch ref, with a `.hexaemeron/` report path, exits 0 `planned` and maps the draft to ADR-097. A step's dry run belongs against the base the step is built on; the numbering against the moving `main` stays the integration composer's job. Every other clause of the Exit is restated unchanged.

**Steps touched.** Step 2

**Still holding.** Step 2: entry holds; exit holds. Step 3: entry holds; exit holds.
