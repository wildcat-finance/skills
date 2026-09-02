# ADR-067: Gate a run on what its issue filed

## Status

Accepted, 2026-08-31.

## Context

Two decisions were being made at filing time and recorded nowhere a program
could read.

The first is whether the work needs a Fiat run at all. A run costs a study, a
runbook, a step chain, an audit loop per step, a prose pass and an integration
merge. A wonky regular expression does not need any of that, and several issues
in the queue are that size. Nothing stopped a run being started against one, and
once `init` had cut a worktree and a branch the cheapest exit was to finish the
run.

The second is what happens to the work an issue names and does not itself carry.
Fiat already required a `## Carried forward` section in the run-level pull
request body, and `carried_forward_fault` required the heading and one non-blank
line under it. Prose satisfied that. `docs/fiat-bound-step-merge/study.md`
records a run that "carried forward four issues"; the study for the per-run audit
log names three items it left open and points at #583 and #579 for two of them.
Both were written by hand, and neither the count nor the pointers were checked
against anything. An item named in prose and filed nowhere is indistinguishable
from an item named in prose and filed twice.

`AGENTS.md` already fixes four issue title prefixes and an ordered publication
sequence for issue bodies, and ADR-009 records the queue reasoning. Neither says
what an issue body must decide, so the ordered sequence checked the register and
the wording of a body that had answered neither question.

## Decision

An issue in this repository carries both decisions as machine-readable text, and
`hexctl` reads them.

**The decision line.** Exactly one unfenced `Fiat-Required:` line, valued `1`
when the work needs a Fiat run and `0` when one independent pull request will do.
Read outside fenced code, so a body quoting the line decides nothing. Two
declarations are a fault rather than a precedence rule: an issue carrying both
answers has made no decision.

**The triage block.** One fenced block with the info string `carryover`, holding
one row per outstanding, carried-forward or unaddressed item:

```text
<id> | <disposition> | <reference>
```

The disposition is `filed`, `duplicate` or `none`. `filed` and `duplicate` point
at one canonical GitHub issue URL: the item's own new issue, or the existing
issue that already carries it. `none` states why the item earns neither, which is
the case ADR-009's standing prohibition on filing an issue to satisfy a workflow
requires the shape to have. Ids are kebab-case and used once. A filing that
carries nothing writes the single row `none | none | <why nothing is carried>`,
because an absent answer cannot be told apart from a question nobody asked.

**Three gates.** `hexctl issue-check` runs the contract over a candidate body
before anything is filed, or over a filed issue over REST. `hexctl init` reads a
GitHub task issue's contract before it creates any state, worktree or branch: a
malformed contract refuses, and `Fiat-Required: 0` refuses with the pull-request
route named, so the run does not get a chance to start. `hexctl done integrate`
requires the triage block inside the run pull request's `## Carried forward`
section, so integration does not proceed on leftovers nothing was decided about.
Both `init` and `integrate` record the parsed rows in their receipts.

One grammar and one parser serve all three, in `hexctl` rather than a second
script, for the reason Protasis gives for extending its study walk instead of
adding a scanner: two scanners of the same shape drift, and the one that drifts
is the one nothing exercises.

## Alternatives

- **A pair of GitHub labels, `fiat-required` and `pr-suffices`.** Cheaper to
  read, and labels are already how the four queues are told apart. Rejected
  because a label is repository administration: it cannot be set by a filer
  without write access, it does not travel with a body quoted into a study or a
  checkpoint, and the absent-label state is silently the same as the
  never-decided state. The queue labels can afford that because the title prefix
  carries the same information; here there would be no second copy.
- **A separate `scripts/issue_contract.py` at the repository root.** The rule is
  repository-wide and `hexctl` is the Fiat controller, so the home looks wrong.
  Rejected on drift: the run-level gate has to use the same parser as the filing
  check, and a root script reached from inside the plugin tree would break the
  portable mirror's import closure. The precedent is `imprimatur.py`, which every
  agent runs for a repository-wide prose rule from inside this plugin.
- **Prose plus a reviewer.** What was already there. It produced the counts and
  pointers described above, and no run was refused for a leftover nobody had
  disposed of.
- **Refuse a task issue that is not a GitHub issue.** `--task-issue` deliberately
  accepts other HTTP issue trackers. Refusing them would close the last way to
  reach `init` without a read decision, at the price of deleting a capability
  this rule does not reach. Taken the other way, with the gap recorded and
  warned rather than passed over.

## Consequences

Every open issue in this repository predates the contract, so a run started
against one refuses at `init` until the issue is edited to declare both parts.
The refusal names the exact line and block to add and costs nothing: no state, no
worktree, no branch. That is the intended cost of the rule, and it is paid once
per issue.

Three ways to reach `init` without a read decision remain, and each records the
nulls in the init receipt and says so on stderr rather than passing quietly: a
run naming no task issue, a run naming a tracker that is not GitHub, and a run
whose issue read failed in transport, which refuses in `github_rest`'s own
transport shape and says nothing about whether the work earned a run.

The checks read shape and never judgement. A `duplicate` row pointing at a real
issue about something else passes, a referenced issue is never opened to confirm
it exists, and a `none` reason nobody should have accepted still counts as an
answer. Whether the disposition was right stays with the reviewer; whether the
filer answered at all no longer does.

`Fiat-Required: 0` is a filing decision, not a verdict about difficulty. Nothing
stops a filer editing an issue from 0 to 1, and nothing here records that they
did beyond the issue's own edit history. A run started after such an edit records
the 1 it read, which is true of what it read and silent about what the issue said
first.
