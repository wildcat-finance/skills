# Runbook: route a zero decision and gate the line that unlocks a run

Derived from [the study](route-a-zero-decision-study.md) and
[skills#1345](https://github.com/wildcat-finance/skills/issues/1345). Five steps
in dependency order, each green at both ends. Step 1 scaffolds and step 5
demonstrates.

The selected design is bound below and is not reopened inside a step.

```design-lock
schema | protasis-design-evidence/v1
sha256 | 88c6d36590c92b497113e3958697b7dc0b464a39bdabda2bcf930cb08cc3992a
candidate | decision-age-window
```

## Three readings this runbook records

**The decision record is a draft, not a numbered final.** Study item 12 puts the
record under `docs/decisions/` and says the number is allocated against the
default branch immediately before pushing. That numbering sentence is superseded
by the state of the base. A delta adding `docs/decisions/ADR-NNN-*.md` without
allocator trailers is refused by `.github/workflows/adr-assignments.yml`, and
only the merge-time allocator produces those trailers. `docs/decisions/drafts/`
is empty on the base and the allocator is healthy against it, so the draft path
is available and the numbered path is not. The record is authored as a draft and
numbered at merge.

**The committed study re-bases five links.** The study's five links to sibling
skills are written for a file inside `plugins/hexaemeron/skills/`, and resolve
nowhere else. Each gains the `plugins/hexaemeron/skills/` prefix in the
committed copy. Nothing else differs, and the exit states the rule rather than a
line count.

**One fixture re-pin, in one step.** Editing `plugins/hexaemeron/skills/fiat/SKILL.md`
moves the whole-file digest that
`tests/fixtures/agent-instruction-v1/manifest.json` binds, and the filing
paragraph sits before the reviewed span so it also shifts the recorded offsets.
All prose edits to that file therefore land in step 5, once, so the derived
chain is re-pinned once.

## Step 1: Land the specification and the decision draft

**Goal.** Put the study, this runbook and the decision behind them in the
repository, so a reader holding only the branch can build the remaining steps.

**Entry.** Branch `fiat/1345-route-a-zero-decision-and-gate-the-line-tha` at
`f22de68086ad7265869636903554d09cf751e765`, clean worktree.

**Exit.** `docs/route-a-zero-decision-study.md` is the receipted study with each
of its five sibling-skill links given the `plugins/hexaemeron/skills/` prefix and
nothing else changed. `docs/route-a-zero-decision-runbook.md` is this runbook.
`docs/decisions/drafts/route-a-filed-zero-as-an-answer.md` opens `# Decision: `,
carries its stable identity, holds no number, and records the three decisions of
study item 12: that a filed `0` is an answer rather than an error and supersedes
that clause of ADR-067, that no override exists, and that the gate reads no
editor identity. The Horos boundary and census are regenerated after staging.
Proved by `python3 scripts/run_checks.py` exiting 0.

**Files.** `docs/route-a-zero-decision-study.md`,
`docs/route-a-zero-decision-runbook.md`,
`docs/decisions/drafts/route-a-filed-zero-as-an-answer.md`,
`.horos/boundary.json`, `.horos/census.json`.

**Tests.** No new case. The step is proved by the checked runner and by
`python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md
AGENTS.md .agents/skills/promise-machine/SKILL.md
.agents/skills/promise-machine/PORTABLE.md plugins docs` exiting 0. Elenchus
runner contract for any fix this step's audit claims: command `python3
"$PLUGIN_ROOT/skills/elenchus/scripts/elenchus.py" --ref HEAD --test-command
"python3 plugins/hexaemeron/tests/run_tests.py {report}" --report-format
unittest-json-v1 --report-file .elenchus/step-1.json`, format
`unittest-json-v1`, report file `.elenchus/step-1.json`.

**Disciplines.** phylax: none, the step adds no boundary and reads nothing from
outside the repository. ephoros: none, nothing here runs unattended. metron:
none, no performance claim. elenchus: none, no failure in hand. hypomnema: this
is the step the discipline governs, and study item 12's three decisions land in
one record because reversing any of them reopens the same choice.

## Step 2: Route a filed zero to a directive

**Goal.** Make a filed `0` an answer the loop can act on rather than an error an
agent reads as an obstacle.

**Entry.** Step 1's branch and tree.

**Exit.** `hexctl init --task-issue <a Fiat-Required: 0 issue>` prints one closed
JSON directive on stdout and exits 0, naming the pull-request route, the issue
it closes and what closing it requires. No run state, worktree or branch is
created, and `git status --short` is clean afterwards. The refusal bytes name no
mechanism that grants this same run: the sentence beginning "If that decision was
wrong" is gone from `hexctl.py`, and no replacement text names an edit, a flag or
an override. Any issue-derived field inside the directive passes the
control-character stripping `hexctl` already applies to displayed text. Proved by
`python3 scripts/run_checks.py` exiting 0.

**Files.** `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/tests/test_hexctl.py`.

**Tests.** `plugins/hexaemeron/tests/test_hexctl.py` gains cases for the routed
directive's shape and exit code, for the absence of run state after it, for the
refusal bytes naming no grant, and for control-character stripping on an
issue-derived field. Expected new cases: 5. Elenchus runner contract: command
`python3 "$PLUGIN_ROOT/skills/elenchus/scripts/elenchus.py" --ref HEAD
--test-command "python3 plugins/hexaemeron/tests/run_tests.py {report}"
--report-format unittest-json-v1 --report-file .elenchus/step-2.json`, format
`unittest-json-v1`, report file `.elenchus/step-2.json`.

**Disciplines.** phylax: the routed directive is a new surface an agent consumes,
so the closed shape and the control-character stripping are its controls.
ephoros: the routed directive is the only record that a `0` was routed, and study
item 8 names the gap that nothing counts them. metron: none, no request is added
here. elenchus: each new case is observed red against this step's entry tree
before its behaviour lands. hypomnema: none, step 1 recorded the decision this
step implements.

## Step 3: Record the filing decision's provenance

**Goal.** Make a run say what it read, so a later reader can tell a decision that
stood from one that moved.

**Entry.** Step 2's branch and tree.

**Exit.** The init receipt carries a provenance block for the filing decision:
the value read, the body digest, `created_at`, `updated_at`, and, where GraphQL
is reachable, the edit count, the last edit time and the prior `Fiat-Required`
value. Where it is not reachable, each of those is recorded as `unknown` with its
reason, never omitted. Prior body text reaches neither the receipt, the ledger
nor stderr: it is reduced to the value and a digest inside the reader. `hexctl
verify` compares the recorded provenance against the issue as it stands and
reports a divergence rather than treating the receipt as the whole truth.
`cmd_record` still refuses `task_issue_contract`. `init` makes at most two
network requests for the filing decision and no other command gains one, counted
by a test against a stubbed API. Proved by `python3 scripts/run_checks.py`
exiting 0.

**Files.** `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/tests/test_hexctl.py`.

**Tests.** `plugins/hexaemeron/tests/test_hexctl.py` gains cases for the
provenance block against a readable and an unreachable GraphQL, for `unknown`
carrying a reason rather than a field being absent, for no body text reaching any
recorded surface, for `verify` reporting a divergence, and for the request count
against a stubbed API. Expected new cases: 7. Elenchus runner contract: command
`python3 "$PLUGIN_ROOT/skills/elenchus/scripts/elenchus.py" --ref HEAD
--test-command "python3 plugins/hexaemeron/tests/run_tests.py {report}"
--report-format unittest-json-v1 --report-file .elenchus/step-3.json`, format
`unittest-json-v1`, report file `.elenchus/step-3.json`.

**Disciplines.** phylax: this step opens the one new external boundary, a GraphQL
request for `userContentEdits`, with pinned argv, no shell, a bounded read, a
hard timeout and a failure recorded as `unknown` rather than degraded to a pass;
prior body text is the new untrusted input and is reduced before it is recorded.
ephoros: this step emits study item 8's signals one and three. metron: the
request-count budget is checked here, as a count rather than a duration, because
the 1057 rounds record three times that no baseline was ever taken. elenchus:
every new case is observed red first. hypomnema: none.

## Step 4: Refuse a decision younger than the window

**Goal.** Stop a run whose filing decision changed just before it started, and
name nothing that would grant it.

**Entry.** Step 3's branch and tree.

**Exit.** `init` refuses when the task issue's body changed inside a bounded
window before it ran, stating what it observed and naming no mechanism that
grants this same run. Over REST alone the read is `updated_at` differing from
`created_at` and falling inside the window; where GraphQL is reachable it refines
to the body edits themselves and the prior value of the line. Where neither can
say whether the body itself changed, `init` proceeds and the receipt names the
read as undiscriminated, and no output reports the window as having been
enforced. No override exists, and no flag, environment variable or argument
clears the refusal. Proved by `python3 scripts/run_checks.py` exiting 0.

**Files.** `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/tests/test_hexctl.py`.

**Tests.** `plugins/hexaemeron/tests/test_hexctl.py` gains cases for a refusal
inside the window, for acceptance outside it, for the undiscriminated REST read
proceeding and being recorded as such, for the GraphQL refinement naming the
prior value, and for the refusal text naming no grant. Expected new cases: 6.
Elenchus runner contract: command `python3
"$PLUGIN_ROOT/skills/elenchus/scripts/elenchus.py" --ref HEAD --test-command
"python3 plugins/hexaemeron/tests/run_tests.py {report}" --report-format
unittest-json-v1 --report-file .elenchus/step-4.json`, format
`unittest-json-v1`, report file `.elenchus/step-4.json`.

**Disciplines.** phylax: the window read consumes the same two boundaries step 3
opened and adds none. ephoros: the refusal is the signal, and it states its
observation rather than a conclusion. metron: none, the window adds no request
beyond step 3's budget. elenchus: each refusal case is observed red before its
rule lands, and the guard convention is the runner contract above. hypomnema:
none, the no-override decision is already recorded.

## Step 5: Update the prose, advance the ledger, and demonstrate

**Goal.** Make the documents describe what the controller now does, record the
generation Fiat owes, and run the study's demo path end to end.

**Entry.** Step 4's branch and tree.

**Exit.** `AGENTS.md` no longer says `init` refuses a `0`, and says what it does
instead. The `## Start or resume` filing paragraph and the `## Hard rules` bullet
in `plugins/hexaemeron/skills/fiat/SKILL.md` say the same, and neither names an
edit that would grant a run. Because that file's whole-file digest is bound and
the filing paragraph sits before the reviewed span, the derived chain is
re-pinned in this step: `python3 ~/.claude/tools/repin_fixture.py . fiat-study-runbook-phase <the
pre-edit ref>` regenerates the manifest source and artefact digests, the model,
source-spans and compact fixtures and the span offsets, and the recorded span
bytes are unchanged, which the pending `reviewed-span-unchanged` cell checks.
`plugins/hexaemeron/skills/fiat/EVOLUTION.md` gains one generation row whose
`Frontier status`, `Frontier revision`, `Current frontier`, `Next Fiat job`
naming skills#363 and `Frontier SHA-256` are retained byte for byte, with the
evolution and epoch counters unmoved. `SKILL.md` frontmatter and the Hexaemeron
package version agree at every site `tests/test_version_propagation.py`
discovers. The demo path from study item 1 runs against the live API and its
observed output is recorded at `docs/route-a-zero-decision-demo.md`. Proved by
`python3 scripts/run_checks.py` exiting 0 and by the recorded demo commands
reproducing byte for byte from the committed bytes.

**Files.** `AGENTS.md`, `plugins/hexaemeron/skills/fiat/SKILL.md`,
`plugins/hexaemeron/skills/fiat/EVOLUTION.md`,
`tests/fixtures/agent-instruction-v1/manifest.json`,
`tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/`,
`tests/fixtures/agent-instruction-v1/evidence/`,
`tests/promise_machine_coverage.json`, `tests/test_version_propagation.py`,
`plugins/hexaemeron/tests/test_phylax_model_proxy.py`,
`plugins/hexaemeron/.claude-plugin/plugin.json`,
`plugins/hexaemeron/.codex-plugin/plugin.json`, `.claude-plugin/marketplace.json`,
`.agents/plugins/marketplace.json`, `docs/route-a-zero-decision-demo.md`,
`.horos/boundary.json`, `.horos/census.json`.

**Tests.** No new case beyond the demo record. The step's claims are what
`tests/test_version_propagation.py`, `tests/test_evolution_contract.py`,
`tests/test_agent_instruction_corpus.py` and `python3
scripts/promise_machine.py coverage --check` already assert. Elenchus runner
contract: command `python3 "$PLUGIN_ROOT/skills/elenchus/scripts/elenchus.py"
--ref HEAD --test-command "python3 plugins/hexaemeron/tests/run_tests.py
{report}" --report-format unittest-json-v1 --report-file .elenchus/step-5.json`,
format `unittest-json-v1`, report file `.elenchus/step-5.json`.

**Disciplines.** phylax: none, the step writes prose, manifests, fixtures and one
ledger row. ephoros: none beyond the signals steps 2 to 4 emit. metron: none, no
performance claim is made here. elenchus: none, no failure in hand; the demo is a
demonstration rather than a guard. hypomnema: the prose surfaces are updated in
place rather than recorded, because they describe behaviour the step 1 record
already decided.

### Amendment -- 2026-09-07

**What changed.** Complete replacement Exit: `docs/route-a-zero-decision-study.md` is the receipted study with each of its five sibling-skill links given the `plugins/hexaemeron/skills/` prefix and nothing else changed. `docs/route-a-zero-decision-runbook.md` is this runbook. `docs/decisions/drafts/route-a-filed-zero-as-an-answer.md` opens `# Decision: `, carries its stable identity, holds no number, and records the three decisions of study item 12: that a filed `0` is an answer rather than an error and supersedes that clause of ADR-067, that no override exists, and that the gate reads no editor identity. The Horos boundary and census are regenerated after staging. Proved by `python3 scripts/run_checks.py --base fiat/1345-route-a-zero-decision-and-gate-the-line-tha` reporting `outcome green`.

**Why.** The clause named a command that proves nothing. On a clean tree
`python3 scripts/run_checks.py` reports `outcome green` for no scope, selects
zero checks, omits the root suite and exits 0, so the exit code alone could not
tell a passing suite from one that was never chosen. That is the state a step
is in the moment it commits, which is the moment the clause is read. The
repaired clause names the base the delta is computed from and the outcome word,
neither of which a vacuous run produces. Raised as S1-R2-01 in step 1 round 2
and filed against the runner as skills#1429.

**Steps touched.** Step 1, whose Exit named the bare command.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-09-07

**What changed.** Complete replacement Exit: `hexctl init --task-issue <a Fiat-Required: 0 issue>` prints one closed JSON directive on stdout and exits 0, naming the pull-request route, the issue it closes and what closing it requires. No run state, worktree or branch is created, and `git status --short` is clean afterwards. The refusal bytes name no mechanism that grants this same run: the sentence beginning "If that decision was wrong" is gone from `hexctl.py`, and no replacement text names an edit, a flag or an override. Any issue-derived field inside the directive passes the control-character stripping `hexctl` already applies to displayed text. Proved by `python3 scripts/run_checks.py --base fiat/1345-route-a-zero-decision-and-gate-the-line-tha` reporting `outcome green`.

**Why.** The clause named a command that proves nothing. On a clean tree
`python3 scripts/run_checks.py` reports `outcome green` for no scope, selects
zero checks, omits the root suite and exits 0, so the exit code alone could not
tell a passing suite from one that was never chosen. That is the state a step
is in the moment it commits, which is the moment the clause is read. The
repaired clause names the base the delta is computed from and the outcome word,
neither of which a vacuous run produces. Raised as S1-R2-01 in step 1 round 2
and filed against the runner as skills#1429.

**Steps touched.** Step 2, whose Exit named the bare command.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-09-07

**What changed.** Complete replacement Exit: The init receipt carries a provenance block for the filing decision: the value read, the body digest, `created_at`, `updated_at`, and, where GraphQL is reachable, the edit count, the last edit time and the prior `Fiat-Required` value. Where it is not reachable, each of those is recorded as `unknown` with its reason, never omitted. Prior body text reaches neither the receipt, the ledger nor stderr: it is reduced to the value and a digest inside the reader. `hexctl verify` compares the recorded provenance against the issue as it stands and reports a divergence rather than treating the receipt as the whole truth. `cmd_record` still refuses `task_issue_contract`. `init` makes at most two network requests for the filing decision and no other command gains one, counted by a test against a stubbed API. Proved by `python3 scripts/run_checks.py --base fiat/1345-route-a-zero-decision-and-gate-the-line-tha` reporting `outcome green`.

**Why.** The clause named a command that proves nothing. On a clean tree
`python3 scripts/run_checks.py` reports `outcome green` for no scope, selects
zero checks, omits the root suite and exits 0, so the exit code alone could not
tell a passing suite from one that was never chosen. That is the state a step
is in the moment it commits, which is the moment the clause is read. The
repaired clause names the base the delta is computed from and the outcome word,
neither of which a vacuous run produces. Raised as S1-R2-01 in step 1 round 2
and filed against the runner as skills#1429.

**Steps touched.** Step 3, whose Exit named the bare command.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-09-07

**What changed.** Complete replacement Exit: `init` refuses when the task issue's body changed inside a bounded window before it ran, stating what it observed and naming no mechanism that grants this same run. Over REST alone the read is `updated_at` differing from `created_at` and falling inside the window; where GraphQL is reachable it refines to the body edits themselves and the prior value of the line. Where neither can say whether the body itself changed, `init` proceeds and the receipt names the read as undiscriminated, and no output reports the window as having been enforced. No override exists, and no flag, environment variable or argument clears the refusal. Proved by `python3 scripts/run_checks.py --base fiat/1345-route-a-zero-decision-and-gate-the-line-tha` reporting `outcome green`.

**Why.** The clause named a command that proves nothing. On a clean tree
`python3 scripts/run_checks.py` reports `outcome green` for no scope, selects
zero checks, omits the root suite and exits 0, so the exit code alone could not
tell a passing suite from one that was never chosen. That is the state a step
is in the moment it commits, which is the moment the clause is read. The
repaired clause names the base the delta is computed from and the outcome word,
neither of which a vacuous run produces. Raised as S1-R2-01 in step 1 round 2
and filed against the runner as skills#1429.

**Steps touched.** Step 4, whose Exit named the bare command.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-09-07

**What changed.** Complete replacement Exit: `AGENTS.md` no longer says `init` refuses a `0`, and says what it does instead. The `## Start or resume` filing paragraph and the `## Hard rules` bullet in `plugins/hexaemeron/skills/fiat/SKILL.md` say the same, and neither names an edit that would grant a run. Because that file's whole-file digest is bound and the filing paragraph sits before the reviewed span, the derived chain is re-pinned in this step: `python3 ~/.claude/tools/repin_fixture.py . fiat-study-runbook-phase <the pre-edit ref>` regenerates the manifest source and artefact digests, the model, source-spans and compact fixtures and the span offsets, and the recorded span bytes are unchanged, which the pending `reviewed-span-unchanged` cell checks. `plugins/hexaemeron/skills/fiat/EVOLUTION.md` gains one generation row whose `Frontier status`, `Frontier revision`, `Current frontier`, `Next Fiat job` naming skills#363 and `Frontier SHA-256` are retained byte for byte, with the evolution and epoch counters unmoved. `SKILL.md` frontmatter and the Hexaemeron package version agree at every site `tests/test_version_propagation.py` discovers. The demo path from study item 1 runs against the live API and its observed output is recorded at `docs/route-a-zero-decision-demo.md`. Proved by `python3 scripts/run_checks.py --base fiat/1345-route-a-zero-decision-and-gate-the-line-tha` reporting `outcome green` and by the recorded demo commands reproducing byte for byte from the committed bytes.

**Why.** The clause named a command that proves nothing. On a clean tree
`python3 scripts/run_checks.py` reports `outcome green` for no scope, selects
zero checks, omits the root suite and exits 0, so the exit code alone could not
tell a passing suite from one that was never chosen. That is the state a step
is in the moment it commits, which is the moment the clause is read. The
repaired clause names the base the delta is computed from and the outcome word,
neither of which a vacuous run produces. Raised as S1-R2-01 in step 1 round 2
and filed against the runner as skills#1429.

**Steps touched.** Step 5, whose Exit named the bare command.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-09-07

**What changed.** Complete replacement Exit: `docs/route-a-zero-decision-study.md` is the receipted study with each of its five sibling-skill links given the `plugins/hexaemeron/skills/` prefix and nothing else changed. `docs/route-a-zero-decision-runbook.md` is this runbook. `docs/decisions/drafts/route-a-filed-zero-as-an-answer.md` opens `# Decision: `, carries its stable identity, holds no number, and records the three decisions of study item 12: that a filed `0` is an answer rather than an error and supersedes that clause of ADR-067, that no override exists, and that the gate reads no editor identity. The Horos boundary and census are regenerated after staging. Proved by `python3 scripts/run_checks.py --base fiat/1345-route-a-zero-decision-and-gate-the-line-tha` reporting `outcome green`. The bare command reports `outcome nothing-selected` on a clean tree and exits 0 without selecting a check, so it establishes nothing.

**Why.** This corrects the five amendment blocks above, which each state that
the bare command "reports `outcome green` for no scope". It does not. The
observed token is `outcome nothing-selected`, recorded at 2026-09-06 against
commit 7c6f5ca8 and again on a clean tree here. The conclusion those blocks
draw is unchanged and the Exit clauses they installed are unaffected: only the
output token they name was wrong. Earlier amendment bytes cannot be edited, so
the correction is appended and the true token now sits in step 1's Exit where a
reader meets it.

**Steps touched.** Step 1, whose Exit now carries the correction on behalf of
all five blocks.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-09-07

**What changed.** Complete replacement Exit: `hexctl init --task-issue <a Fiat-Required: 0 issue>` prints one closed JSON directive on stdout and exits 0, naming the pull-request route, the issue it closes and what closing it requires. No run state, worktree or branch is created, and `git status --short` is clean afterwards. The refusal bytes name no mechanism that grants this same run: the sentence beginning "If that decision was wrong" is gone from `hexctl.py`, and no replacement text names an edit, a flag or an override. Any issue-derived field inside the directive passes the control-character stripping `hexctl` already applies to displayed text. Proved by `python3 scripts/run_checks.py --base fiat/1345-route-a-zero-decision-and-gate-the-line-tha` reporting `outcome green`. The bare command reports `outcome nothing-selected` on a clean tree and exits 0 without selecting a check, so it establishes nothing.

**Why.** The five amendment blocks above each state that the bare command
"reports `outcome green` for no scope". It does not: it reports `outcome
nothing-selected`, and `run_checks.py` reaches `outcome green` only after checks
have run. The error is worse than a misnamed token, because `outcome green` is
the exact token this step's repaired Exit requires. Read as written, those
blocks assert that a run selecting nothing yields what the new clause demands,
which argues the repair is as empty as the clause it replaced. It is not.

An earlier correction named step 1 alone. A step's packet composes its baseline
with the amendments whose `Steps touched` names that step, so a worker
delegated this step received the false claim and no correction. This block puts
the true token in step 2's own packet. Raised as S1-R3-01 in step 1 round 3.

**Steps touched.** Step 2, whose packet carried the false claim uncorrected.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-09-07

**What changed.** Complete replacement Exit: The init receipt carries a provenance block for the filing decision: the value read, the body digest, `created_at`, `updated_at`, and, where GraphQL is reachable, the edit count, the last edit time and the prior `Fiat-Required` value. Where it is not reachable, each of those is recorded as `unknown` with its reason, never omitted. Prior body text reaches neither the receipt, the ledger nor stderr: it is reduced to the value and a digest inside the reader. `hexctl verify` compares the recorded provenance against the issue as it stands and reports a divergence rather than treating the receipt as the whole truth. `cmd_record` still refuses `task_issue_contract`. `init` makes at most two network requests for the filing decision and no other command gains one, counted by a test against a stubbed API. Proved by `python3 scripts/run_checks.py --base fiat/1345-route-a-zero-decision-and-gate-the-line-tha` reporting `outcome green`. The bare command reports `outcome nothing-selected` on a clean tree and exits 0 without selecting a check, so it establishes nothing.

**Why.** The five amendment blocks above each state that the bare command
"reports `outcome green` for no scope". It does not: it reports `outcome
nothing-selected`, and `run_checks.py` reaches `outcome green` only after checks
have run. The error is worse than a misnamed token, because `outcome green` is
the exact token this step's repaired Exit requires. Read as written, those
blocks assert that a run selecting nothing yields what the new clause demands,
which argues the repair is as empty as the clause it replaced. It is not.

An earlier correction named step 1 alone. A step's packet composes its baseline
with the amendments whose `Steps touched` names that step, so a worker
delegated this step received the false claim and no correction. This block puts
the true token in step 3's own packet. Raised as S1-R3-01 in step 1 round 3.

**Steps touched.** Step 3, whose packet carried the false claim uncorrected.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-09-07

**What changed.** Complete replacement Exit: `init` refuses when the task issue's body changed inside a bounded window before it ran, stating what it observed and naming no mechanism that grants this same run. Over REST alone the read is `updated_at` differing from `created_at` and falling inside the window; where GraphQL is reachable it refines to the body edits themselves and the prior value of the line. Where neither can say whether the body itself changed, `init` proceeds and the receipt names the read as undiscriminated, and no output reports the window as having been enforced. No override exists, and no flag, environment variable or argument clears the refusal. Proved by `python3 scripts/run_checks.py --base fiat/1345-route-a-zero-decision-and-gate-the-line-tha` reporting `outcome green`. The bare command reports `outcome nothing-selected` on a clean tree and exits 0 without selecting a check, so it establishes nothing.

**Why.** The five amendment blocks above each state that the bare command
"reports `outcome green` for no scope". It does not: it reports `outcome
nothing-selected`, and `run_checks.py` reaches `outcome green` only after checks
have run. The error is worse than a misnamed token, because `outcome green` is
the exact token this step's repaired Exit requires. Read as written, those
blocks assert that a run selecting nothing yields what the new clause demands,
which argues the repair is as empty as the clause it replaced. It is not.

An earlier correction named step 1 alone. A step's packet composes its baseline
with the amendments whose `Steps touched` names that step, so a worker
delegated this step received the false claim and no correction. This block puts
the true token in step 4's own packet. Raised as S1-R3-01 in step 1 round 3.

**Steps touched.** Step 4, whose packet carried the false claim uncorrected.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-09-07

**What changed.** Complete replacement Exit: `AGENTS.md` no longer says `init` refuses a `0`, and says what it does instead. The `## Start or resume` filing paragraph and the `## Hard rules` bullet in `plugins/hexaemeron/skills/fiat/SKILL.md` say the same, and neither names an edit that would grant a run. Because that file's whole-file digest is bound and the filing paragraph sits before the reviewed span, the derived chain is re-pinned in this step: `python3 ~/.claude/tools/repin_fixture.py . fiat-study-runbook-phase <the pre-edit ref>` regenerates the manifest source and artefact digests, the model, source-spans and compact fixtures and the span offsets, and the recorded span bytes are unchanged, which the pending `reviewed-span-unchanged` cell checks. `plugins/hexaemeron/skills/fiat/EVOLUTION.md` gains one generation row whose `Frontier status`, `Frontier revision`, `Current frontier`, `Next Fiat job` naming skills#363 and `Frontier SHA-256` are retained byte for byte, with the evolution and epoch counters unmoved. `SKILL.md` frontmatter and the Hexaemeron package version agree at every site `tests/test_version_propagation.py` discovers. The demo path from study item 1 runs against the live API and its observed output is recorded at `docs/route-a-zero-decision-demo.md`. Proved by `python3 scripts/run_checks.py --base fiat/1345-route-a-zero-decision-and-gate-the-line-tha` reporting `outcome green` and by the recorded demo commands reproducing byte for byte from the committed bytes. The bare command reports `outcome nothing-selected` on a clean tree and exits 0 without selecting a check, so it establishes nothing.

**Why.** The five amendment blocks above each state that the bare command
"reports `outcome green` for no scope". It does not: it reports `outcome
nothing-selected`, and `run_checks.py` reaches `outcome green` only after checks
have run. The error is worse than a misnamed token, because `outcome green` is
the exact token this step's repaired Exit requires. Read as written, those
blocks assert that a run selecting nothing yields what the new clause demands,
which argues the repair is as empty as the clause it replaced. It is not.

An earlier correction named step 1 alone. A step's packet composes its baseline
with the amendments whose `Steps touched` names that step, so a worker
delegated this step received the false claim and no correction. This block puts
the true token in step 5's own packet. Raised as S1-R3-01 in step 1 round 3.

**Steps touched.** Step 5, whose packet carried the false claim uncorrected.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-09-07

**What changed.** Complete replacement Files: `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, `plugins/hexaemeron/tests/test_hexctl.py`, `plugins/hexaemeron/tests/test_issue_filing_contract.py`, `tests/promise_machine_coverage.json`. Complete replacement Tests: `plugins/hexaemeron/tests/test_hexctl.py` gains cases for the routed directive's shape and exit code, for the absence of run state after it, for the refusal bytes naming no grant, and for control-character stripping on an issue-derived field. Expected new cases: 6, because the stripping case splits: the contract parser refuses a control character in a carryover row before any body reaches the router, so one case holds that refusal and one exercises the directive builder directly. `plugins/hexaemeron/tests/test_issue_filing_contract.py` has its existing zero-refusal case rewritten to the routed outcome rather than deleted, because the question it asks, whether a `0` reaches a run, is the question this step answers differently. `tests/promise_machine_coverage.json` re-pins the eleven bindings that carry the controller digest. Elenchus runner contract: command `python3 "$PLUGIN_ROOT/skills/elenchus/scripts/elenchus.py" --ref HEAD --test-command "python3 plugins/hexaemeron/tests/run_tests.py {report}" --report-format unittest-json-v1 --report-file .elenchus/step-2.json`, format `unittest-json-v1`, report file `.elenchus/step-2.json`.

**Why.** Two files the step must edit were absent from Files, and both are
forced by the Exit rather than chosen. `test_issue_filing_contract.py` carries
`test_a_zero_refuses_before_any_state_worktree_or_branch_exists`, which asserts
the exit code and the refusal text this step removes; it fails the moment the
Exit is met, so the step cannot be green at both ends without it.
`tests/promise_machine_coverage.json` pins the controller's whole-file digest
in eleven bindings, and `test_audit_synopsis_recovery` refuses any edit to
`hexctl.py` until all eleven are re-pinned. Both were found by running the
Hexaemeron suite against the built step: 2437 tests, these two failures, no
others. The case count moves from 5 to 6 for the reason Tests now states.

**Steps touched.** Step 2, whose Files named two of the four files it edits.

**Still holding.** Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-09-07

**What changed.** Complete replacement Files: `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, `plugins/hexaemeron/tests/test_hexctl.py`, `plugins/hexaemeron/tests/test_issue_filing_contract.py`, `tests/promise_machine_coverage.json`, `.horos/census.json`. Complete replacement Tests: `plugins/hexaemeron/tests/test_hexctl.py` gains cases for the routed directive's shape and exit code, for the absence of run state after it, for the refusal bytes naming no grant, and for control-character stripping on an issue-derived field. Expected new cases: 7. The stripping case splits three ways: the contract parser refuses a control character in a carryover row before any body reaches the router, so one case holds that refusal, one exercises the directive builder on string values, and one holds the builder to its own docstring by passing keys, nesting and non-string values the parser does not currently produce. `plugins/hexaemeron/tests/test_issue_filing_contract.py` has its existing zero-refusal case rewritten to the routed outcome rather than deleted, because the question it asks, whether a `0` reaches a run, is the question this step answers differently. `tests/promise_machine_coverage.json` re-pins the eleven bindings that carry the controller digest. Elenchus runner contract: command `python3 "$PLUGIN_ROOT/skills/elenchus/scripts/elenchus.py" --ref HEAD --test-command "python3 plugins/hexaemeron/tests/run_tests.py {report}" --report-format unittest-json-v1 --report-file .elenchus/step-2.json`, format `unittest-json-v1`, report file `.elenchus/step-2.json`. Complete replacement Disciplines: phylax: the routed directive is a new surface an agent consumes, so the closed shape and the control-character stripping are its controls. ephoros: the routed directive is the only record that a `0` was routed, and study item 8 names the gap that nothing counts them. metron: none, no request is added here. elenchus: the runner reports `inconclusive` for this step and cannot report otherwise. A step that adds a function has no parent tree its new cases can run against: overlaying them on the entry commit makes `test_the_directive_strips_a_control_character_from_every_field` error rather than fail, because `routed_filing_directive` does not exist there, and `test_an_issue_body_carrying_a_control_character_never_reaches_a_run` pass, because it asserts parser behaviour this step leaves alone. Redness against the entry tree is therefore recorded per case rather than claimed for the set: four of the seven fail on the parent, one errors, one passes and is marked as asserting unchanged behaviour. hypomnema: none, step 1 recorded the decision this step implements.

**Why.** Three repairs from step 2 round 1. Files named four paths where the
commit edits five: `.horos/census.json` is forced by the same rule that admitted
the coverage JSON, because any tracked-file edit reddens the census currency
test (S2-R1-06). Tests moves from six cases to seven, the seventh holding the
directive builder to its own docstring rather than to the parser coupling that
currently makes the docstring true (S2-R1-04). Disciplines claimed each new case
is observed red against the entry tree, which this step cannot deliver and no
step that adds a function can: the measured outcome is four failures, one error
and one pass, and the clause now states that instead of asserting what the
runner cannot produce (S2-R1-08).

**Steps touched.** Step 2, whose Files, Tests and Disciplines each overstated
what the step delivers.

**Still holding.** Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-09-07

**What changed.** Complete replacement Disciplines: phylax: the routed directive is a new surface an agent consumes, so the closed shape and the control-character stripping are its controls. ephoros: the routed directive is the only record that a `0` was routed, and study item 8 names the gap that nothing counts them. metron: none, no request is added here. elenchus: the runner reports `inconclusive` for this step and cannot report otherwise. A step that adds a function has no parent tree its new cases can run against: overlaying them on the entry commit makes `test_the_directive_strips_a_control_character_from_every_field` error rather than fail, because `routed_filing_directive` does not exist there, and `test_an_issue_body_carrying_a_control_character_never_reaches_a_run` pass, because it asserts parser behaviour this step leaves alone. Redness against the entry tree is therefore recorded per case rather than claimed for the set. Measured by overlaying the three changed files on the entry commit and running each case alone: four of the seven fail, two error because `routed_filing_directive` does not exist there, and one passes and is marked as asserting unchanged behaviour. hypomnema: none, step 1 recorded the decision this step implements.

**Why.** The Disciplines replacement above accounted for six cases across a set
of seven and named one erroring case where there are two. The seventh case is
the one that same amendment added for S2-R1-04, and it errors for the same
reason. Measured by overlaying the three changed files on the entry commit and
running each case alone: `test_the_directive_strips_a_control_character_from_every_field`
and `test_the_directive_strips_control_characters_from_keys_and_nesting` both
raise `AttributeError: module 'hexctl_under_test' has no attribute
'routed_filing_directive'`. The true count is four failures, two errors and one
pass. Raised as S2-R2-02 in step 2 round 2.

**Steps touched.** Step 2, whose Disciplines clause counted six of seven cases.

**Still holding.** Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-09-07

**What changed.** Complete replacement Files: `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, `plugins/hexaemeron/tests/test_hexctl.py`, `plugins/hexaemeron/tests/test_issue_filing_contract.py`, `tests/promise_machine_coverage.json`, `.horos/census.json`, `docs/route-a-zero-decision-runbook.md`.

**Why.** `.hexaemeron/` carries `*` in its own `.gitignore`, so
`.hexaemeron/runbook.md` is working state and
`docs/route-a-zero-decision-runbook.md` is the runbook this repository ships.
Step 1 committed that copy at runbook receipt `34adeafc`; four amendments have
landed since, so the shipped copy is three amendment blocks and 57 lines behind
the artefact it claims to be. Step 1's Exit reads that the committed file is
this runbook, in the present tense, and it stopped being true the moment step 2
amended anything. This step refreshes it, and names it in Files so the refresh
is declared rather than incidental. The same obligation falls on every later
step that amends: refresh after the last amendment of the step, before the
commit that closes it.

**Steps touched.** Step 2, which amended the runbook four times and shipped none
of it.

**Still holding.** Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-09-07

**What changed.** Complete replacement Exit: The init receipt carries a provenance block for the filing decision: the value read, the body digest, `created_at`, `updated_at`, and, where GraphQL is reachable, the edit count, the last edit time and the prior `Fiat-Required` value. Where it is not reachable, each of those is recorded as `unknown` with its reason, never omitted. Prior body text reaches neither the receipt, the ledger nor stderr: it is reduced to the value and a digest inside the reader. `hexctl verify --check-filing-decision` compares the recorded provenance against the issue as it stands and reports a divergence rather than treating the receipt as the whole truth. Plain `verify` makes no request, so the internal calls `amend` and `done` make are unchanged. `cmd_record` still refuses `task_issue_contract`. `init` makes at most two network requests for the filing decision and no other command gains one, counted by a test against a stubbed API. Proved by `python3 scripts/run_checks.py --base fiat/1345-route-a-zero-decision-and-gate-the-line-tha` reporting `outcome green`. The bare command reports `outcome nothing-selected` on a clean tree and exits 0 without selecting a check, so it establishes nothing. Complete replacement Files: `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, `plugins/hexaemeron/tests/test_hexctl.py`, `plugins/hexaemeron/tests/hexctl_harness.py`, `tests/promise_machine_coverage.json`, `.horos/census.json`, `docs/route-a-zero-decision-runbook.md`.

**Why.** The Exit could not be satisfied as written, and Files named two of the
six paths the step edits.

The study asks for both halves of a contradiction. Item 8 says `verify` compares
the recorded provenance against the issue as it stands now, which requires
reading the issue. Item 10 says `verify` makes no additional request. `verify_run`
is not only a user command: `amend` and `done` call it after writing state, so an
unconditional read would put a GitHub round trip inside every receipt and make
every offline receipt fail. The flag answers item 8 on demand and leaves item 10
true for every automatic invocation. It reports a divergence and changes no gate,
so it is a diagnostic rather than a way into a refused run, which is the
distinction this whole delivery turns on. The study keeps the contradiction: a
study amendment would move `study_sha256` and silently drop all fourteen runbook
amendments.

Files gains four paths. The fake `gh` in `hexctl_harness.py` returns `number`,
`body`, `title` and `labels` only, and this step needs `created_at`,
`updated_at` and a GraphQL branch from it. `tests/promise_machine_coverage.json`
carries the controller digest in eleven bindings and any edit to `hexctl.py`
reddens them. `.horos/census.json` moves on any tracked-file edit. And
`docs/route-a-zero-decision-runbook.md` is the copy this repository ships, which
goes stale on every amendment including this one, so each step refreshes it
before the commit that closes it.

**Steps touched.** Step 3, whose Exit asked for a request its own budget forbids.

**Still holding.** Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-09-07

**What changed.** Complete replacement Files: `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, `plugins/hexaemeron/tests/test_hexctl.py`, `plugins/hexaemeron/tests/hexctl_harness.py`, `tests/promise_machine_coverage.json`, `.horos/census.json`, `docs/route-a-zero-decision-runbook.md`, `plugins/hexaemeron/tests/test_filing_decision_provenance.py`, `plugins/hexaemeron/tests/test_issue_filing_contract.py`.

**Why.** Two more paths, both forced by the root suite rather than chosen.

`test_hexctl.py` is bounded at 262144 bytes and this step's seven cases pushed
it to 265382. `test_promise_machine_contract` and `test_run_observation_capture`
both refuse a contract over that limit with PM003, and the Hexaemeron suite does
not see it, so the failure appears only in the root suite the commit gate runs.
The cases move to `test_filing_decision_provenance.py`, which returns
`test_hexctl.py` to 259222 bytes. That file's own docstring records the same
reason for the harness having moved out before them.

`test_issue_filing_contract.py`'s module docstring still said `init` refuses to
create any state on a `0` so the run does not get a chance to start. Step 2
changed that behaviour and rewrote the case below it without correcting the
prose above it, which is the `stale-claim-elsewhere` risk inside a file the run
had already edited.

**Steps touched.** Step 3, whose test law outgrew the file it was written into.

**Still holding.** Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-09-07

**What changed.** Complete replacement Files: `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, `plugins/hexaemeron/tests/hexctl_harness.py`, `plugins/hexaemeron/tests/test_filing_decision_provenance.py`, `plugins/hexaemeron/tests/test_issue_filing_contract.py`, `tests/promise_machine_coverage.json`, `.horos/census.json`, `.horos/boundary.json`, `docs/route-a-zero-decision-runbook.md`. Complete replacement Tests: `plugins/hexaemeron/tests/test_filing_decision_provenance.py` gains cases for the provenance block against a readable and an unreachable GraphQL, for `unknown` carrying a reason rather than a field being absent, for no body text reaching any recorded surface, for `verify --check-filing-decision` reporting a divergence, and for the request count against a stubbed API. Expected new cases: 7. Elenchus runner contract: command `python3 "$PLUGIN_ROOT/skills/elenchus/scripts/elenchus.py" --ref HEAD --test-command "python3 plugins/hexaemeron/tests/run_tests.py {report}" --report-format unittest-json-v1 --report-file .elenchus/step-3.json --timeout 2400`, format `unittest-json-v1`, report file `.elenchus/step-3.json`, timeout 2400 seconds.

**Why.** Files named eight paths and the step commit `f4f0d4b8` edits eight, but
not the same eight. `.horos/boundary.json` is edited and unnamed.
`plugins/hexaemeron/tests/test_hexctl.py` is named and its net change is zero,
because the previous amendment moved this step's seven cases out of it before
the commit was made and returned it to 259222 bytes. `boundary.json` moves in
the step commit rather than in the audit loop's own output, which is the
distinction that held `.horos/candidates.json` unowed, so it is owed here.

Tests still named `test_hexctl.py` as the file the cases land in, which the same
move made false, and its runner contract named no `--timeout`. `elenchus.py`
defaults that to 900 seconds and returns `inconclusive` reading `the run did not
finish inside 900s`. The suite the contract names does not finish inside it on
this repository: `run_checks` timed `hexaemeron-suite` at 1297.9s, and the round
1 contract run took 904 seconds of wall clock, 2026-09-07T15:36:36Z to 15:51:40Z,
exiting 0 with that detail and an empty report. The contract as written could
therefore return no verdict about a guard for any commit that changes a test
file. 2400 seconds is chosen against the 1297.9s measurement. A second reason
for `inconclusive` stands behind the clock and this replacement does not touch
it: `classify` returns `inconclusive` whenever `errors` exceeds zero, tested
before assertion failures are read.

**Steps touched.** Step 3, whose Files and Tests both named a file the step does
not edit.

**Still holding.** Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.
