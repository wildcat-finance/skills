# ADR-039: Keep one source for the beginner primer

## Status

Accepted, 2026-08-27.

## Context

A first-time reader needs the same four definitions, Fiat lifecycle, first
action, and stop rule in Markdown, two infographics, a short primer PDF, and a
one-page quick-start. Maintaining prose independently in those five surfaces
would let the names and controller order drift. The mascot kit is useful for
identity, but copying its reference library into this repository would widen
the source and review boundary.

## Decision

`docs/a-child-or-a-golden-retriever.md` is the canonical reader-facing
source. One checked-in builder reads its marked definitions, lifecycle, first
action, and stop rule, then produces both 1672 by 941 infographics and both
horizontal-A4 PDFs. One Creator-supplied captioned cover and two text-free
generated mascot illustrations are repository inputs, not prose sources. The
cover digest and copy boundary, plus the kit's pinned archive digest, exact
prompts, accepted output hashes, tool disclosure, and visual review, live in
the adjacent source note. The supplied reference library stays outside Git.

The committed study and runbook preserve delivery scope. They do not become a
second reader-facing primer.

## Alternatives

- Extend the existing 12-page Promise Machine field guide. It already has a
  build path, but it gives this audience the longest entrance and still does
  not yield two standalone beginner infographics.
- Ship infographics alone. They scan quickly, but they lose searchable text,
  meaningful links, an accessible equivalent, and a clear rebuild source.
- Build a microsite. It could be interactive, but it adds hosting, browser,
  telemetry, and accessibility boundaries to a one-step documentation job.
- Maintain separate prose for every output. That makes each file easy to edit
  in isolation and makes disagreement between them almost certain.

## Consequences

A wording or lifecycle change starts in one Markdown file and regenerates all
four derived outputs. The builder and focused test refuse drift, wrong
dimensions, missing PDF text or links, weak declared contrast, JavaScript,
and unclassified tracked binaries. The Markdown remains the text equivalent
for readers who cannot use the images; no PDF/UA claim follows from that.

The repository keeps one supplied cover, two generated source illustrations,
and four generated views. Rebuilding the views requires the bundled ReportLab
and Pillow runtime. A new visual direction may replace the three source images,
but it must update the source note and pass the applicable fixed-digest,
identity, typography, render, and Horos checks.
