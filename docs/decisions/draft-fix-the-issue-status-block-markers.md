# Fix the issue status block markers

## Status

Proposed, 2026-08-31. Unnumbered on purpose. A number is assigned when this
record merges, per issue #888, which records ADR-050 colliding at authoring time
and the ADR-024 duplicate that turned `main` red until #582 renumbered the Wave
Delta chain. The filename carries no `ADR-` prefix because
`tests/test_decision_records.py` globs `ADR-*.md` and then requires digits, so a
prefixed draft fails `test_every_filename_follows_the_convention`. Issue #888
lists the draft form as an open question and stays free to settle it.

## Context

ADR-014's amendment of 2026-08-31 authorises one bounded write to an open
issue's body: a single block recording current status, supersession, or a
changed requirement. It fixes the delimiters as `<!-- status:start -->` and
`<!-- status:end -->` and requires the Atlas dependency extractor to skip the
block.

Those bytes are matched by more than one reader. `hexctl issue-check` reads them
in this repository. The Atlas reads issue bodies in a repository this run cannot
change, and issue #497 records its dependency extractor reading a `depends on`
line as a declaration about the issue that contained it. A block naming other
issues would change eligibility if the extractor did not skip it.

A marker contract that lives only in an amendment's prose is hard to match
against. This record states it once, in the form a second implementation can
follow.

## Decision

**The delimiters are exactly `<!-- status:start -->` and `<!-- status:end -->`,**
each alone on its line, leading and trailing whitespace ignored. They are HTML
comments, so a reader who does not know about them sees nothing.

**One block per body.** Two opened blocks refuse: a body carrying two has made
no statement. An opened block that is never closed refuses rather than consuming
the rest of the body. A closer with no opener refuses.

**A marker inside a fenced code span is not a marker.** A body quoting the
delimiters as an example carries no block, the same rule the `Fiat-Required`
line already follows. This is what lets this record show its own markers.

**The block sits at the top of the body,** before the filing prose, so a reader
meets the current statement before the original one.

**Absence is not a refusal.** Most bodies carry no block, and that is ordinary.

**Filing prose outside the block is never rewritten.** Where a filing is wrong
rather than stale, the block says so and the original text stays. This keeps the
append-only discipline that governs documents.

**A consumer that parses issue bodies for anything else must skip the block.**
The Atlas dependency extractor inherits this obligation and it is delivered in
the Atlas repository, not here.

## Alternatives

- **A fenced block with an info string,** matching the `carryover` and
  `risk-register` shape. Rejected because a fence renders as a visible code
  block in the issue, and this content is prose a reader should read normally.
- **A heading convention such as `## Status`.** Rejected because ten open issues
  already use that heading for unrelated purposes, so a parser could not tell a
  contract block from ordinary prose.
- **A separate tracking file in the repository.** Rejected because the census
  reads issue bodies, and a file in this repository is exactly the surface it
  does not read.

## Consequences

An open issue can state its current requirement where the census reads it, and
the statement is machine-checkable rather than conventional.

The obligation on the Atlas extractor is stated here and satisfied elsewhere. A
reader of this record should not assume it has been delivered; until it is, a
block naming other issues can still reach the dependency logic.

Nothing in this record retrofits the block onto issues that already exist, and
nothing judges whether a status claim is true. The check reads shape, exactly as
the carryover reader does.
