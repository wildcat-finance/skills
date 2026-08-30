# ADR-060: Remove the beginner primer and its generator

## Status

Accepted, 2026-08-30. Supersedes
[ADR-039](ADR-039-keep-one-source-for-the-beginner-primer.md).

## Context

`ADR-039` kept one Markdown source for the beginner primer and derived two
infographics and two PDFs from it with a checked-in builder. A focused test
rebuilt the outputs and compared them byte for byte against the committed
copies.

That comparison cannot pass anywhere. The test finds its interpreter by
probing the filesystem, and the repository's workflow installs no image
libraries, so in CI `find_builder_python()` returns `None`, `setUpClass`
returns early, and every assertion inside it is skipped without running. On a
developer machine carrying Pillow the rebuild does run and differs: 24,581
pixels in `a-child-or-a-golden-retriever-whos-who.png` and 28,661 in
`-fiat-flow.png`, across bounding boxes covering nearly the whole 1672 by 941
canvas. The cause is glyph rasterisation under a different Pillow and FreeType
build, and nothing in the repository pins either.
`docs/fiat-integration-path-bound-study.md:134` recorded the CI half of this
and called the result structurally invisible to the gate meant to catch it.

The binaries also cost other work. Five PNGs and two PDFs total 10,802,141
bytes of the Horos boundary. Fiat's `done sync-run` requires every path an
integration touches to be covered by a check recording exit 0, at
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py:6820` and `:6855`, so a run
whose base advance touches `docs/assets/` or `docs/pdf/` cannot receipt its
integration while the only check over those paths is one that cannot pass. The
`#936` run halted on exactly those three paths.

## Decision

Delete the primer, its generated images and documents, its builder and its
focused test: fifteen tracked files, 10,946,434 bytes. Delete the primer's own
two audit records with it, because the round audited a document that no longer
exists. Drop the three `README.md` links and write nothing in their place.

Publish no replacement here, and say nothing about one. The beginner entry
point is left unspoken until the Creator decides what stands in it.

Leave every historical reference alone. Ten studies and runbooks and four
audit records from other runs cite the primer as evidence for decisions taken
at the time; they keep saying what they said. Nine of the ten sit under
`docs/`. The tenth is
`plugins/hexaemeron/docs/fiat-author-publisher-separation/runbook.md`, whose
`.agents/` mirror is byte-identical and so needs no edit of its own.

## Alternatives

- Pin Pillow and FreeType and keep the byte comparison. This buys a passing
  gate for a document the Creator has already decided to replace, and it adds
  two pinned native dependencies to a repository that needs neither for
  anything else.
- Keep the primer and delete only the test. The binaries stay in the boundary
  and keep blocking integrations, and the outputs then have no rebuild source
  anyone checks.
- Keep the primer and mark the test as an expected failure. The failure is a
  property of whichever machine runs it, so the marking would be wrong on the
  hosts where the rebuild happens to agree.
- Write replacement prose in `README.md` now. That commits this run to a
  beginner entry point it has not studied, in a paragraph nobody would revisit
  once the real replacement lands.
- Rewrite history to reclaim the 10.4 MiB. The objects are reachable from
  every branch and tag that predates the removal, and the cost of the rewrite
  falls on everyone with a clone.

## Consequences

`ADR-039`'s single-source design keeps its reasoning and loses its subject. No
tracked path names the primer, so no check has to run against an artefact that
cannot be rebuilt reproducibly. The root suite loses its one standing error
without any test being rewritten, and `docs/assets/` and `docs/pdf/` stop
holding integrations that touch them.

A first-time reader arriving at `README.md` is given no route in. That is the
intended state, not an oversight, and it lasts until a replacement is decided
somewhere else.

Nothing here decides how generated artefacts are checked in general. Whether
any other output should be compared byte for byte against an unpinned
toolchain is a separate question that this removal makes less urgent rather
than answering.

Git keeps the deleted objects. Recovering the primer means restoring the
fifteen paths from history, and the rebuild still will not reproduce the
committed images on an arbitrary host.
