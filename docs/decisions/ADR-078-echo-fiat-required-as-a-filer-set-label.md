# ADR-078: Echo `Fiat-Required` as a filer-set label

## Status

Accepted, 2026-09-05.

## Context

[ADR-067](ADR-067-gate-a-run-on-what-its-issue-filed.md)
already makes one `Fiat-Required:` line the checked answer to whether an
issue needs a Fiat run: `1` for a run, `0` for one independent pull request.
`hexctl issue-check` and `init` read that line. Nothing surfaces it on the
issue list itself, so telling the two kinds of work apart still means opening
each issue. [ADR-009](ADR-009-four-issue-queues-and-their-titles.md)
solved the same list-level problem for the four issue queues: `held-job`,
`wish` and `observation` sit beside their title prefixes, set by the filer,
checked nowhere, useful precisely because a reader does not have to open the
issue to see them.

ADR-067's Alternatives already rejected a `fiat-required`/`pr-suffices` label
pair, for three reasons: a label cannot be set by a filer without write
access, it does not travel with a body quoted into a study or a checkpoint,
and an absent label there would be indistinguishable from a never-decided
issue. All three describe a label used in place of the checked line. None
describes a label sitting beside it, the way `held-job`, `wish` and
`observation` already sit beside a title prefix that carries the same
information unchecked. That is the shape asked for here.

## Decision

An issue carries a label matching its own `Fiat-Required:` line:
`fiat-run-needed` for `1`, `only-pr-needed` for `0`. The filer sets it at
filing time, the same convention ADR-009 already uses for the four queue
labels. Neither `hexctl issue-check` nor `init` reads it; the
`Fiat-Required:` line stays the sole checked answer, so a missing or stale
label changes nothing about what a run is gated on.

The two labels are created directly in the repository, the way the four
queue labels already are.

## Alternatives

- **Read the label instead of, or ahead of, the `Fiat-Required:` line.** The
  pair ADR-067 already rejected, for the reasons given there. Rejected again
  here for the same reasons.
- **A workflow that sets the label from the line on `issues: opened` and
  `issues: edited`.** Keeps the two in sync automatically, at the cost of a
  workflow holding write access to issue labels and a second parser of the
  `Fiat-Required:` grammar. ADR-067 put that grammar in `hexctl` once, for the
  drift reason Protasis gives for extending a study walk instead of adding a
  scanner. A second parser reopens that question without a new reason to.
- **No label; point queue-browsing tools at the body line instead.** Cheapest,
  and truest to ADR-067's one-checked-answer claim, but leaves the plain
  GitHub issue list with no visible answer, which is the gap this record
  exists to close.

## Consequences

The issue list shows the Fiat-run decision without opening an issue, the way
`held-job`, `wish` and `observation` already read from a title. The label can
drift from the `Fiat-Required:` line the same way a queue label can drift
from a title prefix: nothing here enforces the match, and `hexctl` never
reads the label, so it cannot notice a mismatch. A filer who edits
`Fiat-Required:` after filing has to update the label by hand; nothing
records whether they did, the same gap ADR-067 already names for the line's
own edit history.
