# ADR-100: Refuse location-dependent pointers before a receipt pins a digest

## Status

Accepted, 2026-09-14. The record takes its number at the integration
composition, where the merge composer assigns one from the base branch.

## Context

`done study` and `done runbook` pinned an artefact's SHA-256 without checking
its links, and `amend study` and `amend runbook` keep the receipted bytes as an
exact prefix, so a pinned pointer cannot be corrected in place. The receipt
reads `.hexaemeron/study.md`, one directory below the worktree root, while step
1 of a runbook commits a copy one to four directories deep. Of the 160 committed
study copies at the starting ref, 55 sit one directory deep, 55 two, 19 three
and 31 four, and a link written relative to its own file resolves at some of
those depths and not at others.

Three runs met this after the digest was pinned. The fiat-377 and skills#1070
runs each recorded five H001 findings on a committed study, and the fiat-857
run shipped a study that differs from its receipt. The work is
[skills#1086](https://github.com/wildcat-finance/skills/issues/1086); the study
behind this record is `docs/fiat-link-gate/study.md`, and its checked design
record is `docs/fiat-link-gate/design-evidence.json`.

## Decision

`done study`, `done runbook`, `amend study` and `amend runbook` refuse a
recognised Markdown link or `runbook:` pointer that is neither an absolute URL
with a scheme the bundled Hypomnema checker skips nor an in-page anchor, a
`/`-rooted path included. The checker then runs over the captured bytes with
`docs/decisions` in scope, and a finding on the artefact, a timeout, an output
overflow or malformed output refuses as well. The verdict reads the pointer, not
the artefact's path, so identical bytes get one verdict at every depth.

Four construction choices belong to the decision:

- The controller loads the bundled `hypomnema.py` in-process and calls its
  `LINK`, `RUNBOOK`, `suppressed`, `_external`, `_code_spans` and `_within`,
  rather than copying that parser or adding a Hypomnema mode. A missing module
  or name refuses the receipt. The module exposes no fence reader, so the rule
  copies the backtick fence toggle in its `check()`.
- An amendment is checked over the bytes it appends, read in the fence state
  the receipted prefix leaves, so a pointer an older controller receipted
  cannot block a later amendment.
- The in-process scan runs under a real-time alarm of the checker's 30-second
  `GIT_TIMEOUT` and refuses when the alarm fires, because Hypomnema's `LINK`
  pattern backtracks quadratically on a line dense in `[` and `_within` scans
  every code span for each match. A process that cannot hold that alarm
  refuses rather than scanning without a bound.
- No contract key, receipt field, ledger event field or packet field is added.
  A refusal exits 2 before any state, ledger or artefact write.

## Alternatives

**`declare-only`.** Require `hexaemeron:hypomnema` in `--skills`, as
`done prose` requires its two skill ids. It is the smallest change, but it never
opens the artefact, so it accepts the frozen specimen whenever the id is
declared. It failed the `catches-observed-defect`,
`verdict-location-independent` and `enforces-result-not-declaration` gates.

**`lint-in-place`.** Run the bundled check on the artefact where it sits. It
refuses the specimen, but identical bytes pass at one depth and fail at another,
so a verdict at `.hexaemeron/study.md` says nothing about the committed copy. It
failed `verdict-location-independent`.

**Copy the parser into the controller.** The copy would add 2,568 bytes that can
drift from the pointers the checker actually resolves.

**Add a Hypomnema mode.** It would change Hypomnema's behaviour, which this run
left to that skill.

`require-location-independent` passed all four gates and was the only
survivor, so the rule was `unique-frontier` and neither metric decided the
selection.

## Consequences

Identical bytes get one pointer verdict at the receipt location and at every
depth a committed copy occupies. Commit-pinned absolute URLs, in-page anchors,
code-span paths, pointers under Hypomnema's allow pragma, and stable decision
references and superseding pointers to records under `docs/decisions` are
accepted.

A study or runbook an older controller accepted can be refused by this one. Its
author cites repository files by commit-pinned URL or code-span path, and a
`/`-rooted link is refused even where it resolves. A stable reference to a
decision record outside `docs/decisions` is refused, because only that
directory is in the checker's scope.

The receipts now depend on six names in the bundled `hypomnema.py`, so a
Hypomnema change that renames one refuses every study and runbook receipt until
the controller follows it. Each receipt also runs one checker subprocess.

A line dense enough to hold the scan past 30 seconds refuses the receipt
rather than stalling it. The bound needs `SIGALRM` on the main thread: called
from another thread, on a platform without `setitimer`, or while another alarm
or `SIGALRM` handler is set, every study and runbook receipt refuses.

Bytes an older controller receipted are never checked again, and the rule
makes no network call, so a commit-pinned URL to a missing path is accepted.
