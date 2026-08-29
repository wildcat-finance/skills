# Issue 576: give each Fiat run its own audit log path

Rounds for the run on branch
`fiat/576-give-each-fiat-run-its-own-audit-log-path`, off `main` at
`103fa90c444f35eb09e87b9d2ec29c43a6d34c1f`. The run set
`config audit.log_path` to this file before its first round, so its own
evidence exercises the change it delivers rather than landing in
`audit/AUDIT.md`. Headings carry step and round alone, because the file names
the run.

## Step 1, round 1 -- 2026-08-24

Non-Solidity round over the two Markdown documents step 1 commits, at
`fe7f59ff03d699178a2a2a656a8b7381d7680be0`. Zero findings.

The three bundled lints exit 0: Phylax and Ephoros over `plugins` and `tests`,
Hypomnema over `README.md AGENTS.md .agents plugins docs`. Protasis accepts the
shipped study in `--study` mode and the shipped runbook in runbook mode.
Imprimatur reports no defect on either, both scoring 100.0. Brevitas exits 0 on
each. Horos reports that the boundary matches the tree. The root suite reports
349 tests OK with no skips and the Hexaemeron suite 986/986, both from inside
this run's worktree. The commit's local signature is good and it carries exactly
one co-author trailer and one origin trailer.

One deviation from the step's stated exit, and it is why this round is clean
rather than red. The exit says both shipped documents are byte-identical to the
run's `.hexaemeron` copies. The shipped study is not. It differs in five link
targets and nothing else:

```text
266c266
< [ephoros](../ephoros/SKILL.md) owns what a signal must carry.
---
> [ephoros](../../skills/ephoros/SKILL.md) owns what a signal must carry.
282c282
< model output reaching a command. [phylax](../phylax/SKILL.md) owns the boundary
---
> model output reaching a command. [phylax](../../skills/phylax/SKILL.md) owns the boundary
289c289
< no step is taken in the name of speed, so [metron](../metron/SKILL.md) has
---
> no step is taken in the name of speed, so [metron](../../skills/metron/SKILL.md) has
304c304
< [elenchus](../elenchus/SKILL.md) owns the triage order and the guard rule.
---
> [elenchus](../../skills/elenchus/SKILL.md) owns the triage order and the guard rule.
322c322
< [hypomnema](../hypomnema/SKILL.md) owns which decisions earn a record and where
---
> [hypomnema](../../skills/hypomnema/SKILL.md) owns which decisions earn a record and where
```

The receipted study cites the five discipline skills as `../<name>/SKILL.md`,
which resolves from a skill directory and from nowhere else. A study ships under
`plugins/hexaemeron/docs/<topic>/`, where all five resolve to nothing. Hypomnema
H001 named every one, and `test_hypomnema_checker.OverTheMarketplace` and
`test_hypomnema_checker.SourceComments` failed the Hexaemeron suite at 984/986
with them. The shipped copy cites `../../skills/<name>/SKILL.md`, which is the
same five documents from where this file lives, and is what the two studies
already committed under `plugins/hexaemeron/docs/` do.

A receipted study cannot be edited and `amend study` only appends, so the choice
was a red tree or a shipped document differing from the receipt in five link
targets. Protasis forbids handing the next step a broken tree. The tree is green
and the difference is recorded here, in full. No claim, criterion, assumption or
design in the document changed.

Two register concerns are reachable at this step and both were checked.
`history-mutation`: `git diff fiat/576-give-each-fiat-run-its-own-audit-log-path
-- audit/AUDIT.md` is empty, because this run's rounds go to this file instead.
`boundary-currency`: `horos check .` reports that the boundary matches the tree,
and `tests/test_boundary_currency.py` passes 7 tests. The other five concerns,
`derived-path-injection`, `override-escape`, `legacy-state-drift`,
`recorded-log-divergence` and `overclaimed-record`, sit in the step 2 and step 3
diffs and are not reachable yet.

One observation for step 5, which owns the boundary.
`python3 plugins/horos/skills/horos/scripts/horos.py scan . --write` inside a run
worktree rewrites `counts.files_walked` from 1496 to 1532 while all 100 entries
stay identical, because the CLI's walk counts paths that the committed
boundary's `tracked` universe excludes. Step 5's exit pairs that command with
`git diff --exit-code .horos/boundary.json`, which would fail on a count nobody
meant to change. `horos check .` answers the same question without writing, so
step 5 uses it and regenerates only if an entry drifts.

Leads not pursued: none.

## Step 2, round 1 -- 2026-08-24

Non-Solidity round over the derivation and the override constraint, at
`ff74c6ad45031599563310ce4db8531d31b9a19b`. Two findings, both fixed in this
round.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | high | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | `cmd_config` checked the override only on the exact path `audit.log_path`, and `config set audit '{...}'` writes the whole section through the same command. `config set audit '{"max_rounds": 8, "stacked_suffix": "--audit", "fold": false, "log_path": "audit/AUDIT.md"}'` was accepted against a fresh run and `config get audit.log_path` then answered `"audit/AUDIT.md"`, so the constraint was one section write away from not existing. | fixed in this round: a section write carrying `log_path` meets the same check, with `test_replacing_the_whole_audit_section_meets_the_same_check` and `test_replacing_the_section_with_an_allowed_path_still_works` as the guards |
| S2-R1-02 | low | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | `check_audit_log_path` passed the stored `run_branch` to `flattened_run_branch`, which runs a regex over it. A state holding `17` there raised `TypeError: expected string or bytes-like object, got 'int'` and exited 1 with a traceback, where every other refusal in this file exits 2 with a diagnosis. `validate_state_shape` checks the container spine and not this leaf, so nothing upstream ruled it out. | fixed in this round: a stored branch of the wrong type is treated the same as an absent one, which is the case the function already had an answer for, guarded by `test_a_branch_stored_as_the_wrong_type_answers_rather_than_raising` |

Both guards were run against `ff74c6ad`, the unfixed commit, and both fail there.
The third new test is the companion that keeps the section write working for an
allowed path, and it passed before and after.

The three bundled lints exit 0: Phylax and Ephoros over `plugins` and `tests`,
Hypomnema over `README.md AGENTS.md .agents plugins docs`.
`scripts/promise_machine.py check` and `coverage --check` are both clean after
the recorded `hexctl.py` digest moved to
`592251a28f328ee049a298d6058ff0987d1720eeee6376ea2f24f943ad682f60`; the four
Fiat runtime field maps are unchanged, because the change adds no result field
to any of them. Horos reports that the boundary matches the tree. The root suite
reports 349 tests OK with no skips and the Hexaemeron suite 1,001/1,001, both
from inside this run's worktree. The commits carry good local signatures with
exactly one co-author trailer and one origin trailer each.

Five register concerns are reachable at this step and each was checked.
`derived-path-injection`: `run_audit_log_path` reaches the filesystem only
through `flattened_run_branch`, which calls `check_branch_name` first, so a name
git would not accept never becomes a path. `override-escape`: the four textual
checks run before `scoped_path`, and the symlink test proves the last one still
catches something, since every textual check passes on
`elsewhere/<derived name>` where `elsewhere` points outside the tree.
`legacy-state-drift`: a run with no usable branch keeps the older unconstrained
value, and S2-R1-02 widened that from absent to unusable. `history-mutation`:
`git diff fiat/576-give-each-fiat-run-its-own-audit-log-path -- audit/AUDIT.md`
is empty. `boundary-currency`: `horos check .` is clean. The remaining two,
`recorded-log-divergence` and `overclaimed-record`, sit in step 3's diff.

Two observations about the base, which advanced while this step was being built.
`main` is now `08512d4`, carrying issue 554's runbook amendment receipts. First,
`fiat-v5.21.1` is taken, so this run's row is `fiat-v5.22.1`, to be re-read
against `main` at step 5 rather than trusted from here. Second, the paths 554
changed include `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/tests/test_hexctl.py`,
`tests/promise_machine_coverage.json`,
`plugins/hexaemeron/skills/protasis/SKILL.md` and `audit/AUDIT.md`. The first
four are this run's overlap at sync and were always going to be. The fifth is
the file this issue exists to remove from that set, and this run only enters it
because step 4 appends a one-time pointer there. That pointer is written once
and never again, so it does not reintroduce the churn; this run pays the overlap
one last time to leave the note.

Leads not pursued: none.

## Step 2, round 2 -- 2026-08-24

Non-Solidity round over the fixed tree at
`02f53def2f325c7e9dd7d4784481830a234ba6ad`. Zero findings.

The three bundled lints exit 0 over the same trees as round 1.
`scripts/promise_machine.py check` and `coverage --check` are clean, Horos
reports that the boundary matches the tree, the root suite reports 349 tests OK
with no skips, and the Hexaemeron suite reports 1,001 tests run with 0 failures,
0 errors and 0 skipped through the Elenchus reporter.

Round 1's two fixes were re-read for what a fix can break. The section write
takes the value `parse_value` just produced, so the in-place assignment touches
no stored object, and the ledger still records the section it wrote.
`args.path` cannot be both `audit` and `audit.log_path`, so the branch order
decides nothing. A section write that drops `log_path` altogether is still
accepted and still fails later in the Warden packet with the message that
absence already had, which is the behaviour every other missing config key has
and not something round 1 introduced. `run_audit_log_path` has two callers,
`cmd_init` after `check_branch_name` and `check_audit_log_path` after the type
guard, so neither reaches the regex with something it cannot match.

All five reachable register concerns were re-checked against the fixed tree and
each holds as recorded in round 1.

Leads not pursued: none.

## Step 3, round 1 -- 2026-08-24

Non-Solidity round over the declared-log binding, at
`ca72a2d4542d1c882b0deb42fcce76c9e41294be`. Two findings, both fixed in this
round.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R1-01 | medium | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | `done_audit` called `check_declared_audit_log` unconditionally and then discarded its answer whenever `--log` was omitted, so closing an audit read `config audit.log_path` even when the recorded round already had the value. A run whose config had lost that key, with a round that recorded one, closed before this change and was refused after it. The refusal was correct for a run with nothing recorded and wrong for a run with something. | fixed in this round: config is consulted only when there is nothing recorded to keep, guarded by `test_a_closure_keeping_a_recorded_log_does_not_need_the_config` and its companion `test_a_closure_with_nothing_recorded_and_no_config_still_refuses` |
| S3-R1-02 | info | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | `check_declared_audit_log` took `declared` untyped, coerced it with `str()` and tested it against `None`, none of which can happen: argparse hands this function a string or the caller does not call it. The coercion told a reader the contract was looser than it is. | fixed in this round: the parameter is typed `str`, the `None` test moved to the two call sites that already knew the answer, and the coercion is gone |

The first guard fails against `ca72a2d4`, the unfixed commit. The second is a
clarity fix with no behaviour to guard, and the eleven cases in
`AuditRoundLogBindingTests` cover the behaviour it did not change.

The three bundled lints exit 0 over the same trees as every round in this run.
`scripts/promise_machine.py check` and `coverage --check` are clean after the
recorded `hexctl.py` digest moved to
`96b73e96543820d5bc9bb9fac66fbb0cf180a1a8bdbe60657db317356786bba0`. Horos
reports that the boundary matches the tree. The root suite reports 349 tests OK
with no skips and the Hexaemeron suite 1,012/1,012.

Both remaining register concerns are reachable at this step and each was
checked. `recorded-log-divergence`: a declared `--log` that names another file
is refused on both receipts, and `test_a_round_naming_another_file_is_refused`
asserts the round list is still empty afterwards, so a refusal appends nothing.
`overclaimed-record`: the field records the path the round was told to write,
which is the obligation the loop already placed on it, and the controller still
does not open the file or attest its bytes. Nothing in this diff claims it does.

Two deliberate limits, neither pursued. An absolute `--log` naming the same file
is refused, because the comparison is textual and reaching the filesystem to
decide would pull symlink resolution into a receipt check. And
`os.path.normpath` accepts a trailing slash as the same path, which names the
same record either way. The five step 2 concerns were re-checked and hold.

Leads not pursued: none.

## Step 3, round 2 -- 2026-08-24

Non-Solidity round over the fixed tree at
`da1713851403871b82ccb58461926b98cd7264d7`. Zero findings.

The three bundled lints exit 0, `scripts/promise_machine.py check` and
`coverage --check` are clean, Horos reports that the boundary matches the tree,
the root suite reports 349 tests OK with no skips, and the Hexaemeron suite
reports 1,012 tests run with 0 failures, 0 errors and 0 skipped through the
Elenchus reporter.

Round 1's fixes were re-read for what a narrowed read can miss. `done audit`
now has three paths and each was exercised: a declared log that matches is
checked and recorded, an omitted log with a recorded round keeps that round's
value without touching config, and an omitted log with nothing recorded falls
back to config and is refused when config has nothing either. `cmd_audit_round`
has the two it always had. Removing the `str()` coercion changed no call, since
argparse hands both call sites a string or `None` and each now tests for `None`
before calling.

The two step 3 register concerns and the five from step 2 were re-checked
against the fixed tree and each holds as recorded.

Leads not pursued: none.

## Step 4, round 1 -- 2026-08-24

Non-Solidity round over the five changed documents and the new decision record,
at `4af4388c9a31d2f5677cc3905070c012dee0f8a7`. One finding, fixed in this round.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S4-R1-01 | low | `plugins/hexaemeron/skills/protasis/SKILL.md` | The item 2 replacement was written into the paragraph without re-flowing what followed, leaving line 108 at 94 characters where the rest of that paragraph wraps between 71 and 79. No lint reads column width, so nothing was going to catch it. | fixed in this round: the paragraph is re-flowed at the width it already used, and the same replacement is now nine lines rather than one long one |

The three bundled lints exit 0. Imprimatur scores every changed document 100.0
with no defects: `references/audit-loop.md`, `plugins/hexaemeron/README.md`,
Fiat's `SKILL.md`, Protasis's `SKILL.md`, `ADR-025` and the appended section of
`audit/AUDIT.md`. Brevitas is clean on all of them except the two historical
tables at `audit/AUDIT.md:12349` and `:12363`, which carry B011 and predate this
run; nothing above the appended section was touched. The Protasis checker passes
69 tests, `tests/test_decision_records.py` passes 5, the root suite reports 349
OK with no skips and the Hexaemeron suite 1,012/1,012. Horos reports that the
boundary matches the tree.

`git diff fiat/576-give-each-fiat-run-its-own-audit-log-path -- audit/AUDIT.md`
removes no line, which is the check the step's exit names, so the appended
section is the whole of this run's change to that file.

Two register concerns are reachable and both were checked. `history-mutation`:
the diff above is append-only, and `tests/test_run_observation.py` still passes,
which is the reader that made the file an evidence dependency in the first
place. `boundary-currency`: `horos check .` is clean, so the new documents earned
no entry. The five code concerns sit in steps 2 and 3 and were closed there.

One check this round could not make, and step 5 owns it. `ADR-025` states
`fiat-v5.22.1` as the generation carrying the decision, and the record is
numbered 025 against a `main` read at
`08512d4`. Both are global identifiers picked locally, and `fiat-v5.21.1` was
already taken by issue 554 between this run's base and now. Step 5 re-reads
`main` for both before it writes the ledger row, and corrects this record if
either has moved.

A second look at `plugins/hexaemeron/README.md:54`, which still names
`plugins/hexaemeron/audit/AUDIT.md`. That file exists and is the plugin's own
fuzz-audit log, a different artefact from the root record this change moves, so
the sentence is accurate and was left alone.

Leads not pursued: none.

## Step 4, round 2 -- 2026-08-24

Non-Solidity round over the re-flowed tree at
`19d26e93c93d9ae134057aaf832d0d5bf7d5be01`. Zero findings.

The three bundled lints exit 0, Imprimatur scores every changed document 100.0,
the Protasis checker passes 69 tests, `tests/test_decision_records.py` passes 5,
the root suite reports 349 OK with no skips, the Hexaemeron suite reports
1,012/1,012, and Horos reports that the boundary matches the tree.

The re-flow was read for what re-wrapping can do to a document: it changes no
word, the paragraph still reads as one item under heading 2, the widest line is
74 characters against a paragraph that already used 71 to 79, and the Protasis
checker still parses items 1 through 12, which is what would break if the item
had lost its shape. `git diff origin/main` over that file shows the paragraph
and the frontmatter version, the latter only because this run branched before
issue 554 published `4.7.0`; the merge takes main's version and this run's
paragraph, and issue 554 changed nothing inside it.

`history-mutation` and `boundary-currency` were re-checked and hold. The step 5
obligation recorded in round 1, to re-read `main` for the ADR number and the
ledger version before writing either, stands unchanged.

Leads not pursued: none.

## Step 5, round 1 -- 2026-08-24

Non-Solidity round over the demonstration and the run-level body, at
`2f51f6bd8bb002c312842beaf10fa561f51bc082`. Zero findings.

The three bundled lints exit 0. Imprimatur scores
`plugins/hexaemeron/docs/fiat-per-run-audit-log/proof.md` and
`.hexaemeron/run-pr.md` 100.0 with no defects, and Brevitas is clean on the
proof. Horos reports that the boundary matches the tree, so the new document
earned no entry and `.horos/boundary.json` is unchanged. The root suite reports
349 tests OK with no skips and the Hexaemeron suite 1,012/1,012.

The transcript was re-read against what it claims. Every line in it came from a
scratch run this step created, driven by this branch's `hexctl.py` rather than
the `fiat-v5.20.1` controller driving this delivery, and the document says so
first rather than in a footnote. Section 4 shows the refusal and then shows one
round on the ledger rather than two, which is the part that would be worth
nothing without it. The closing section states the two things the transcript
does not establish: that anything was written to the file, because the
controller never opens it, and that the sync gate stops asking for a check over
the record, because that needs a base that advanced and the scratch run has
none.

Two deviations from the step's stated exit, both deliberate and both recorded in
`.hexaemeron/run-pr.md` under carried forward.

The ledger row is not in this step. `main` published `fiat-v5.21.1` from issue
554 between this run's base and now, so the row this run owes is `fiat-v5.22.1`,
and its axis arithmetic is checked against the row before it by
`tests/test_evolution_contract.py`. On this branch the row before it is
`fiat-v5.20.1`, so writing `fiat-v5.22.1` here fails that check and writing
`fiat-v5.21.1` duplicates a label already on `main`. The row goes in the sync
commit, which is the first point where the arithmetic is against the real
predecessor, and `done integrate` refuses the run if it is absent, malformed or
already published. The sync is certain: `tests/promise_machine_coverage.json`
and `audit/AUDIT.md` both changed on both sides.

`.horos/boundary.json` is unchanged rather than regenerated. `scan . --write`
inside a run worktree rewrites `counts.files_walked` while every one of the 100
entries stays identical, which is the observation step 1 round 1 recorded.
`horos check .` answers the question the exit was asking and reports that the
boundary matches the tree, and `tests/test_boundary_currency.py` passes, which
compares entries rather than counts.

`ADR-025` and `fiat-v5.22.1` were both re-read against `main` at `08512d4`
immediately before this round. ADR numbers 025, 026 and 027 are free, the only
open pull request touching `docs/decisions/` is this run's own step 4, and no
open pull request touches the Fiat ledger.

Leads not pursued: none.

## Integration -- 2026-08-24

Not a step round. What happened bringing the stack down, and what the merge with
`main` at `08512d4ada7b1d7418e1af213be0d4b8c1494b6d` had to resolve.

### The stack was merged out of order

A malformed shell loop passed an empty argument to `gh pr merge`, which falls
through to the current branch's pull request. The branch was step 5's, so
[#591](https://github.com/wildcat-finance/skills/pull/591) merged into the run
branch ahead of [#589](https://github.com/wildcat-finance/skills/pull/589) and
[#590](https://github.com/wildcat-finance/skills/pull/590). Step 5's branch was
cut from step 4's, which was cut from step 3's, so that one merge carried every
commit in the stack.

The product survived exactly. The run branch's tree is byte-identical to the
step 5 branch tip, and all thirteen signed commits are reachable from it and
GitHub-verified. Nothing was rewritten and nothing was dropped.

The bookkeeping did not. `done merge-step` requires each step's pull request to
be `MERGED` with `baseRefName` equal to the run branch. #589 and #590 cannot be
retargeted onto it, because GitHub reports no commits between them and a branch
their heads are already ancestors of, and a pull request cannot merge into a
base it is an ancestor of. Steps 1 and 2 are receipted; steps 3, 4 and 5 are
not, and `done integrate` will not run without them.

The run is halted on its ledger with that reason, at the maintainer's direction,
and the delivery finishes by hand: #589 and #590 closed with the explanation
above, one integration pull request from the run branch into `main`, and the
checks `done integrate` would have made carried out explicitly and recorded
here. What is lost is the terminal receipt. What it would have checked is
checked: the ledger row's arithmetic by `tests/test_evolution_contract.py` and
`plugins/hexaemeron/tests/test_evolution.py`, the signatures by GitHub, and the
carried-forward section by reading it.

### What the merge with the advanced base resolved

`main` moved from `103fa90` to `08512d4` during the run, landing issue 554's
runbook amendment receipts. One textual conflict, in
`tests/promise_machine_coverage.json`: both sides record the `hexctl.py` digest
and neither value describes the merged file. Resolved by taking the incoming
structure, which carries issue 554's new `fiat-runbook-amendment` promise, and
recomputing the digest from the merged controller to
`9da873deacc6a1f8045ecf91a5a66c05f5ea10758ce7b0ce4a0fbc83eba0c259`. This run's
own change to that file was never anything but the digest, so nothing of its own
was at stake in the resolution.

One composition failure that neither side could see alone. Issue 554's tests and
this run's both went into `plugins/hexaemeron/tests/test_hexctl.py`, and together
they took it to 263,626 bytes against the Promise Machine's 262,144-byte
bounded-read ceiling. `scripts/promise_machine.py check` refused with fourteen
`PM003` findings. Fixed by moving this run's two classes to
`plugins/hexaemeron/tests/test_audit_log_path.py`, unchanged, which leaves
`test_hexctl.py` at 251,141 bytes. No assertion was weakened or dropped; the
Hexaemeron suite reports the same count either way.

`tests/test_evolution_contract.py` pinned the current version and newest row to
`fiat-v5.21.1` with issue 554's evidence, which is what that run wrote for its
own row. Re-pinned to `fiat-v5.22.1` and this run's evidence. The frontier
revision, digest, frontier text and held job assertions are untouched, which is
what makes it a generation rather than an advance.

### The merged tree

Root suite 349 tests OK with no skips. Hexaemeron suite 1,045/1,045.
`promise_machine.py check` clean over 14 plugins and 14 copies, `coverage
--check` clean at 71 promises and 71 rows. Phylax, Ephoros and Hypomnema each
exit 0. Horos reports that the boundary matches the tree.
`plugins/hexaemeron/skills/fiat/EVOLUTION.md` carries one new row,
`fiat-v5.22.1`, generation, retaining `state-shape-validation` and its digest
byte for byte, and `SKILL.md` frontmatter matches it. The held issue 363 job is
untouched.

Leads not pursued: one, and it is the maintainer's. A Fiat run should not be
able to merge the wrong pull request from a mistyped command. Nothing in the
loop binds the merge to the pull request the directive names; the directive
carries `pr_url` and the operator types the merge by hand. That is filed
separately.
