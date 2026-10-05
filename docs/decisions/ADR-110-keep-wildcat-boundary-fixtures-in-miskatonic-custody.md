# ADR-110: Keep the Wildcat boundary fixtures in Miskatonic custody

## Status

Accepted, 2026-09-27, for issue #1384.

## Context

Issue #1384 delivers one Lazarus plan-v3 fixture per Wildcat estate on Ethereum
mainnet, V1 at block 22074622 and V2 at block 26022093, each with a Lazarus
release and an Alexandria admission. The study at
`docs/lazarus-wildcat-boundary-fixtures/study.md` measured the fixture and
release copies for the full map at 117,913,418 bytes. The portable package
measured 18,715,497 bytes at the starting commit against its 20,971,520-byte
line, a margin of 2,256,023 bytes. Where the bytes live is expensive to reverse
once a consumer names a custody path.

On 2026-09-26 the maintainer ruled for the #1924 run that Wildcat fixture
custody is Miskatonic and its R2 buckets, reached through a handoff pull
request under `storage/r2/handoffs/` and Miskatonic's own custody tooling. On
2026-09-27 the maintainer confirmed that custody for these fixtures and
declined a public copy.

## Decision

Keep every fixture, release and admission archive in Miskatonic R2 custody,
proposed through one handoff pull request under `storage/r2/handoffs/` that
lists each archive's byte count and SHA-256 with a proposed source-register
row, and uploaded only through Miskatonic's custody tooling after the operator
accepts that row by digest.

## Alternatives

The private archive repository beside the interval captures measured the same
as the selected route on every criterion and lost on the 2026-09-26 ruling,
which moved fixture custody to R2.

Committing the fixtures under `plugins/lazarus/examples/`, as the Aave v4
example is committed, measured 117,913,418 bytes against the 2,256,023-byte
margin. It fails the space gate and the ruling against vendoring fixture bytes.

Proving only the state words, queue heads and code, with accounts, batches,
statuses and balances left as recorded calls, still measured 78,480,052 bytes
in the tree, because the recorded calls and code dominate. It also fails the
mapped-words-proved gate, because the map's per-account and per-batch numbers
would no longer be proved.

A public copy of the bytes, such as an asset on a skills release, was put to
the maintainer and declined on 2026-09-27.

## Consequences

No fixture byte enters this repository. The tree keeps the plan generator,
slot module, probe summaries, plan digests, relation reports and demonstration
under `plugins/lazarus/examples/wildcat-boundary-v0/`, and committed records
carry digests, counts and reports, never a local path. Full verification names
the release trees through `WILDCAT_BOUNDARY_V1_RELEASE` and
`WILDCAT_BOUNDARY_V2_RELEASE`; the committed digests are checked offline
without them. A stranger needs Miskatonic access to fetch the bytes. The upload
waits on the operator accepting the register row, so the run carries R2
admission forward by name if that has not happened by integration.
