# ADR-020: Licence first-party skills under Apache-2.0

## Status

Accepted, 2026-08-22. Renumbered from 012 on 2026-08-24. Two records were
accepted the same day and both took 012, because git merges files with
different names and no conflict and nothing compared the numbers inside them.
This record moved rather than
[ADR-012](ADR-012-run-fiat-in-a-dedicated-worktree.md), which landed second,
because an append-only audit record cites 012 meaning that one and correcting
a past record is not permitted here. This record had no inbound references.

## Context

Several Wildcat Labs plugins already carried Apache-2.0 licence files, some
carried no plugin-root licence, and Lazarus still named MIT. Host manifests did
not state one consistent licence. A reader therefore could not determine the
first-party licensing boundary from the repository structure, and publication
could drift without a machine check.

Hexaemeron also vendors the Pashov security suite. Those five canonical skills
are upstream-owned, carry their own MIT licence and notices, and are required to
remain unmodified. A repository-wide licence rule that descended into their
directories would falsely claim Wildcat ownership and break the vendoring
contract.

## Decision

Wildcat Labs first-party work is licensed under Apache-2.0 with `Wildcat Labs`
as the named copyright holder. The root `LICENSE` is canonical. Every plugin
that contains a governed first-party skill carries a byte-identical copy, and
both host manifests name `Apache-2.0` and `Wildcat Labs`.

The Promise Machine owns a repository-level
`promise-machine-first-party-licence` check. It discovers plugins through the
existing governed-skill inventory and checks only each first-party plugin root
and its host manifests. It does not descend into canonical skill directories
for licensing. The vendored Pashov directories remain outside the check and
keep their upstream MIT licence and notices.

## Alternatives

- **Add a root licence only.** This is simple, but installed plugins may be
  packaged without the repository root, leaving the licence behind.
- **Add SPDX headers to every file.** This is explicit but would create a large,
  noisy rewrite and is unnecessary while each packaged first-party plugin has
  a licence at its root.
- **Apply Apache-2.0 to the whole tree.** This was rejected because the Pashov
  suite is vendored upstream work and Wildcat Labs has no authority to
  relicense it.
- **Keep each plugin's existing choice.** This preserves history but leaves the
  marketplace inconsistent and makes host metadata an unreliable guide.

## Consequences

Every first-party plugin package carries the same licence text even when it is
installed without the repository root. A missing copy, changed copy, or
inconsistent host declaration now fails before publication.

The check proves consistency of the recorded boundary, not copyright ownership
or legal suitability. Upstream and third-party material remains governed by its
own licence. In particular, nothing in this decision edits, governs, or
relicenses the Pashov suite.
