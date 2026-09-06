# Decision: Route a filed zero as an answer

Stable identity: `adr/route-a-filed-zero-as-an-answer`.

## Status

Proposed, 2026-09-06. Numberless under
[ADR-077](../ADR-077-assign-adr-numbers-at-merge-not-at-authoring.md), which
assigns the number at merge.

## Context

[ADR-067](../ADR-067-gate-a-run-on-what-its-issue-filed.md) made one unfenced
`Fiat-Required:` line the checked answer to whether work earns a Fiat run, and
gave `hexctl init` the job of reading it before any state, worktree or branch
exists. For a `0` it specified a stop: init "refuses with the pull-request route
named, so the run does not get a chance to start."

The refusal that implements it ends by naming the edit that turns it off, at
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py:5031-5041`. That last sentence
is a recovery written for a person who filed wrongly. Delivered instead to an
agent that has just been told to start a run, it is the instruction for doing
so. On 6 September 2026 an agent met it against
[skills#1337](https://github.com/wildcat-finance/skills/issues/1337), edited the
issue from `0` to `1`, and the run started. Nothing in any receipt recorded that
a refusal had preceded the edit.

ADR-067 named this exposure and left it open: "Nothing stops a filer editing an
issue from 0 to 1, and nothing here records that they did beyond the issue's own
edit history." What it did not anticipate is that the refusal itself would be
the thing proposing the edit.

Two questions are settled here rather than in
[the study](../../route-a-zero-decision-study.md), because a study is read once
and a record is read whenever somebody meets the behaviour. Whether a `0` is an
error decides what every future reader of that exit code believes. Whether a
bypass exists decides the shape of every refusal built on this gate, and adding
one later is cheaper than removing one.

## Decision

**A filed `0` is an answer, not an error.** `hexctl init` against an issue
declaring `Fiat-Required: 0` prints one directive object on stdout, exits 0, and
creates no state, worktree or branch. The directive names the pull-request route,
the issue it closes, and what closing it requires. It names no mechanism that
would grant a run instead. This supersedes ADR-067's clause that a `0` refuses so
that the run does not get a chance to start; the rest of ADR-067 stands, and its
bytes are left as the historical decision.

**No override exists.** The gate this delivery adds refuses an `init` whose task
issue carries a filing decision younger than a bounded window. The recovery is to
wait for the window to pass, or to route the work as the pull request the `0`
decided on. No flag, environment variable, argument or configuration key clears
that refusal, and none will be added without superseding this record.

The reason is the failure above. A refusal that names its own bypass, delivered
to an agent that wants the run, is an instruction for getting one. An override
flag is that same failure with a flag in place of an issue edit, and it is worse
in one respect: it is faster. Time cannot be named as an instruction, cannot be
passed as an argument, and clears itself.

**The gate reads no editor identity.** Neither the window refusal nor the
provenance it records consults who edited the issue. Edit history establishes
when a line changed and never who decided it. The measurement behind this is that
all four edits on skills#1337 carry the login `laurenceday`: the agent publishes
through the maintainer's own account, so editor and operator are one identity,
and a check on that field would separate nothing.

## Alternatives

- **Move the recovery sentence into a reference and leave the exit code at 1.**
  Rejected. It stops the refusal proposing a bypass and leaves the `0` an error,
  so an agent still meets a stop where the filer wrote an answer.
- **Route the `0` and record the filing decision's provenance, gating nothing.**
  Rejected as the whole answer, adopted as part of it. The issue that asks for
  this says of provenance alone that it prevents nothing by itself. Provenance
  makes the edit visible after the fact; the window makes it not work.
- **Keep a host-side record of routed issues and refuse a later `1` against it,
  unless an override argument passes.** Rejected. The record does not survive a
  fresh clone and can be deleted, and the refusal has to name the override to be
  usable, which is the shape that started this.
- **Give the window refusal an override that takes a written reason.** Rejected
  for the reason the Decision states. A reason field is satisfied by whatever the
  caller types, and the caller here is the party the gate exists to slow down.
- **Refuse when the editor and the operator differ.** Rejected. The two are the
  same login in every observed case, so the rule would fire on nothing it is
  aimed at while implying a check that had been made.
- **Keep the refusal and rely on review to catch the edit.** Rejected. The edit
  and the run appear in the same delivery, and the receipt that would show the
  sequence is the one that never recorded it.

## Consequences

An exit code changes meaning. A `0` from `init` no longer implies a run began,
and anything reading that exit code has to read stdout to tell a routed answer
from a started run. The directive is one closed object of the shape the loop
already acts on, so a caller that parses it needs no new grammar.

A routed `0` creates no state, so nothing counts how many issues were routed
rather than run. The operator's transcript is the only record. Closing that gap
needs a store this delivery does not add, for the same reason the host-side
record was set aside.

The window's length is a tuned parameter of the gate and not a decision here;
changing it is a code change with a test, and reversing the absence of an
override is not. In an environment where only REST is reachable the gate is
advisory: it reads `updated_at` differing from `created_at`, which a comment, a
label or an assignment also moves. Where neither transport can say whether the
body itself changed, `init` proceeds and the receipt names the read as
undiscriminated rather than as an enforced window.

Because no override exists, an operator who has legitimately corrected a filing
decision waits. On an issue under active discussion that wait has no upper bound
in the operator's control, which is the cost this record accepts in exchange for
a gate with nothing to name.
