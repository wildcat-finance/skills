# Release policy

<!-- marketplace-context:start -->
> **Marketplace context: Berean.** Berean pins the corpus, chain readings and evaluation record a protocol agent's answers rest on, so a release can be checked without the model that produced it. Use Lemma to produce source-linked chunks, Lazarus to preserve the chain evidence itself, and Ariadne to bind a released artefact digest to its evidence. **Current frontier:** The reference release answers against a frozen demonstration corpus and preserved Aave v4 mainnet reads; no release yet cites live Wildcat documentation or a captured Wildcat market read, and no Ariadne statement binds a berean release.
<!-- marketplace-context:end -->

How a berean release becomes active, stands down and gets corrected. The
format is [release-v1.json](../schemas/release-v1.json) and
[promotion-record-v1.json](../schemas/promotion-record-v1.json); the checks
live in `scripts/berean_lib/release.py` and `promote.py`. The doctrine is
Tabularium's, applied to agent releases: published bytes are immutable, and
every change of standing is a record.

## Immutability

A release directory's contents are pinned by `release.json`, and
`release.json` is pinned by its own `release_digest` over the named
identity fields. Corrections are new releases; nothing edits a published
one. The one file that grows is `promotions.jsonl`, which sits beside the
release and is deliberately outside the release digest: the chain records
what happened to the release, so it cannot also be inside it.

## Promotion

`promote` records that a release became active, on evidence:

1. The release's own evaluation report is re-read and its digest checked
   against the release's pin.
2. The report must grade this release's corpus, cases and answers, by
   digest agreement on all three. The report never names the release
   digest itself, because the release pins the report's bytes and a cycle
   would close nothing.
3. The threshold is fixed in v1: zero failures allowed. A report carrying
   a failure does not promote, whatever its note says.

The record repeats the counts and pins the report and cases digests, so
the chain stands alone: a reader with only `promotions.jsonl` and the
release directory can re-derive whether the promotion was earned.

## Rollback

A rollback is a record naming the restored release's digest and the
reason. Only an active release rolls back, the chain replays in sequence
order from the start on every read, and a gap, reorder or forged count is
a refusal of the whole chain rather than a different history. The
superseded release's bytes stay where they are; standing down is not
deletion.

## What this does not claim

The chain is unsigned. It proves internal consistency and evidence
agreement, not publisher identity. Binding a release and its chain to a
signed statement is the deferred Ariadne work recorded in
[design.md](design.md).
