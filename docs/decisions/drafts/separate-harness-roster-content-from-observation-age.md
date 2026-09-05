# Decision: Separate harness roster content from observation age

Stable identity: `adr/separate-harness-roster-content-from-observation-age`.

## Status

Accepted, 2026-09-05. This record supersedes ADR-079 only where ADR-079 makes
observation metadata part of generated public surfaces and requires every
probe to regenerate them. ADR-079 remains accepted for the manifest schema,
probe, classification vocabulary, evidence rules, and single-source roster.

## Context

ADR-079 introduced one probed manifest and three generated surfaces. The
manifest's `recorded` object holds `host`, `date`, and `base_ref`, and the
renderer included those values in both Markdown regions and the PDF roster
label. `--check` therefore treated observation metadata as roster content.

Issue #1247 reproduced the consequence against the issue-856 run: a re-probe
changed zero of 59 per-harness fields but moved the three metadata fields,
which made all three public surfaces stale and rebuilt a 2,702,681-byte PDF.
The inverse also passed: an old manifest remained green whenever its surfaces
matched it, because no command measured elapsed age.

The public Markdown surfaces already link
`docs/harness-classification.json`. That manifest is the durable provenance
record and remains one click away. Repeating its volatile metadata in generated
text adds churn without adding a separately checked fact.

## Decision

Generated README, guide, and PDF roster text depends only on harness content.
It contains none of `recorded.host`, `recorded.date`, or
`recorded.base_ref`. The renderer still validates all three fields before it
checks or writes anything, so removing them from display does not weaken the
manifest contract.

`harness-roster-check` compares roster content. A separate declared check,
`harness-roster-freshness`, reads `recorded.date` and fails when the manifest
is future-dated or more than 30 completed calendar days old. Ages zero through
30 pass. The split gives each failure one meaning and makes the budget visible
in the check graph.

Write mode first compares the existing PDF's harness page with current roster
content. When it matches, the ReportLab subprocess is skipped and the PDF
bytes remain untouched. A content change that reaches the PDF still builds the
PDF before either Markdown file is replaced, preserving the existing
all-or-nothing ordering for content-reachable failures.

The manifest schema and probe output do not change. A metadata-only re-probe
therefore updates the provenance record and nothing else.

## Alternatives

- Keep the date visible and exclude selected generated substrings from
  comparison. Rejected because write mode still changes public bytes and the
  PDF, while the checker must know which part of its own output it does not
  protect.
- Remove metadata from surfaces but report stale age without failing. Rejected
  because stale evidence stays green and the maintenance incentive remains
  backwards.
- Treat `base_ref` movement as staleness. Rejected because a probe cannot name
  the commit that later records its output, making the manifest stale at every
  commit rather than at a useful maintenance boundary.
- Drop the `recorded` object from the manifest. Rejected because provenance is
  useful in the canonical record and the issue asks to decouple it, not erase
  it.

## Consequences

A contributor may re-probe unchanged harnesses without editing the README,
guide, PDF, or Horos boundary. Readers who need the observation host, date, or
base commit follow the existing manifest link.

The repository gains one calendar-sensitive hard check. A manifest that is 31
days old stops the docs scope until somebody records a fresh observation. A
future date also fails rather than buying extra budget. This deliberate
maintenance obligation is the cost of making staleness real.

Content drift remains strict. Names, classes, versions, client presence,
authentication state, and blockers still reach the surfaces they did before,
and a mismatch remains a normal test failure. The PDF build is no longer an
unconditional side effect, so tests must hold both its skip and rebuild paths.
