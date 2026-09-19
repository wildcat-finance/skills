# Decision: Register the kickoff queue beside the four of ADR-009

## Status

Accepted, 2026-09-18. Numberless until the merge that lands it, under the
draft path [ADR-077](../ADR-077-assign-adr-numbers-at-merge-not-at-authoring.md)
set out. It extends
[ADR-009](../ADR-009-four-issue-queues-and-their-titles.md), whose four queues
stay as recorded; it does not supersede it.

## Context

On 2026-09-06 the maintainer filed 59 issues, #1350 to #1409, titled
`kickoff/{skill}-{n}: <summary>`, one per entry of an ordered list held
privately. All 59 carry `held-job`, and since 2026-09-08 all 59 carry a
`kickoff` label as well. On the day of this record 53 are open and six are
closed as completed: #1350, #1351, #1352, #1354, #1356 and #1360.

The filing contract in `hexctl.py` knew four title forms: `{skill}-next`,
`{skill}-N`, `{skill}-wish` and `framework-N`. A `kickoff/` prefix matches none
of them, so `hexctl issue-check` refused every one of the 59 with "title is not
one of". `hexctl init` reads only the `Fiat-Required` line and the `carryover`
block, so it bound runs against the same issues the publication check refused.
Every filing postdates the contract (`0ad3e363`, 2026-09-05). This was a live
queue the contract had never been told about, not legacy drift.
[#1475](https://github.com/wildcat-finance/skills/issues/1475) records the
census that found it.

Neither existing form could absorb the queue by retitling. `{skill}-next` is one
job per skill, and its `held-job` label reads "A ledger's held Next Fiat job";
the kickoff list holds up to five entries per skill. `{skill}-N` requires the
`wish` label, which ADR-009 closed at #334 and reserved for the generated
wishlist; retitling would file frontier work as wishes and change what closing
one means.

## Decision

A fifth queue, identified by its title prefix and two labels.

| Source | Title prefix | Labels |
| --- | --- | --- |
| A maintainer's kickoff filing for one held frontier job | `kickoff/{skill}-N` | `kickoff` and `held-job` |

`{skill}` is the skill's own governed name, as in ADR-009. `N` is the entry's
position in the list the filing came from; it is provenance, kept for the same
reason ADR-009 kept the wishlist ordinals, and nothing checks it for
uniqueness.

`held-job` stays because a kickoff filing keeps the frontier semantics of the
job it kicks off: closing one means what closing a `{skill}-next` means.
`kickoff` sits beside it so the two queues are told apart on the issue list. The
contract checks the pair as one exact set: a kickoff title with only one of the
two labels, or a `{skill}-next` carrying `kickoff`, is refused by name.

`hexctl issue-check`, the carryover `filed` gate at integration and every other
reader of `issue_queue_contract` accept the form from this record onward.
`init` is unchanged; it already bound these issues.

## Alternatives

- **Retitle the filings into `{skill}-next`.** Rejected above: that queue is
  defined as one job per skill, and the label description says so.
- **Retitle the filings into `{skill}-N` with `wish`.** Rejected above: the
  `wish` label is closed by ADR-009, and the retitle would change the meaning
  of closing one.
- **Decide the queue should not exist.** The filings are the maintainer's
  frontier programme, runs have already started against them, and six have
  closed as completed. Removing the queue would need a
  disposition for 53 open filings before any title moved, and nobody has
  proposed one.
- **Register `kickoff` alone, dropping `held-job`.** It would break the
  frontier semantics the 59 filings already carry, and every one of them
  would need a label change to pass.

## Consequences

`hexctl issue-check` reads all 59 kickoff titles as the queue they are, and
reports `queue: kickoff/{skill}-N (queue labels: held-job, kickoff)`. The
`ISSUE_QUEUE_LABELS` set gains `kickoff`, so the label now counts as a queue
label for every queue: a filing that carries it without the kickoff title
prefix is refused.

The Phylax GitHub issue publisher keeps its four queues. Kickoff filings are a
maintainer action, not an App publication, and the publisher's queue set is
pinned by its own conformance fixture. Teaching it the fifth queue is separate
work if an App ever needs to file one.

AGENTS.md lists five queues and five frozen title forms.
