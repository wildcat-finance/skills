# Decision: Keep the Wildcat X-Ray reports bound to two source commits

## Status

Accepted, 2026-09-26, for issue #1363.

## Context

Issue #1363 supplies issue #1387 with two complete X-Ray report sets, a
function-to-event linkage and an action comparison. The accepted
`wildcat-finance/v2-protocol` commits are deployed comparison source
`f5a26146987926f4811b72a795d662813dedfe85` and candidate
`bea503c2736d47de7fd34130c64f10783dc35b39`. The deployment registry establishes
only the narrower relations stated in the study at `docs/kickoff/1363/study.md`.

## Decision

Keep fresh reports, source digests, independent action inventories, event
dispositions, comparison, execution gaps and review evidence together; recover
source bytes through the two immutable Git commits.

## Alternatives

The selected `source-bound-reports` probe retained 43,414 bytes. A
`reports-and-source-archive` probe retained 1,395,094 bytes by adding an
uncompressed source archive. Both passed source identity, format and recovery
checks. Their recorded packaging times were 1 ms and 3 ms, excluding Git reads
and future reports. These single local observations establish no production
performance result. The archive lost because it duplicates public source bytes.

## Consequences

Every logical source file receives a disposition. Inherited actions remain in
the denominator, constructor records stay separate, and eventless or unresolved
paths remain explicit. Failed coverage remains an execution gap. The literal
entry-point diff accompanies the reviewed semantic comparison.

The issue-specific checker verifies retained bytes against fixed source and
action inventories and recorded review. It does not prove source semantics,
reviewer identity, deployed behaviour or protocol safety. Warden separately
reviews the source judgements. Recovering source requires the named public Git
objects; a future loss of those objects requires a separate preservation choice.
