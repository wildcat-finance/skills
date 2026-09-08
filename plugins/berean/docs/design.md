# Design decisions

<!-- marketplace-context:start -->
> **Marketplace context: Berean.** Berean pins the corpus, chain readings and evaluation record a protocol agent's answers rest on, so a release can be checked without the model that produced it. Use Lemma to produce source-linked chunks, Lazarus to preserve the chain evidence itself, and Ariadne to bind a released artefact digest to its evidence. **Current frontier:** The Wildcat reference release pins three captured official documents and five recorded market calls at Ethereum block 25907928, with an unsigned Ariadne statement binding all 18 release components. The release frontier is mature; authored answers keep its demonstration status mixed.
<!-- marketplace-context:end -->

Decisions expensive to reverse, each with the reason it went the way it did.
The study behind them is [study.md](study.md); the specification is
[spec.md](spec.md).

## Original binding decision

The following records the original deferral and its rejected alternative.
These were the implementation-time reasons, not the current Ariadne boundary.

The specification's first open question asks whether the release manifest
should extend Ariadne directly or stay a separate document referenced by an
Ariadne release statement. It stays separate, for two reasons that will not
age away:

1. Ariadne's core gate 4 refuses conclusion vocabulary anywhere in a
   predicate, including `score`, `verdict` and `grade`. A berean release
   carries evaluation thresholds and results as structured fields, so those
   fields cannot live inside an Ariadne predicate at all.
2. Ariadne's own ledger holds `grounded-agent-predicate` as its next job. An
   ordinary berean delivery must not consume a sibling's held frontier.

The precedent is Lazarus: the kit owns its artefact format and its own
release document; Ariadne owns one predicate type describing that artefact;
each side names the other by constant and is held to it by a drift test;
neither imports the other. When the grounded-agent predicate exists, a berean
release binds to a statement the same way. Until then, `release-v1` keeps
every artefact digest such a statement would cover: the corpus digest, each
component digest and the release digest, all lowercase sha256 hex over
canonical JSON, so the binding needs no new fields when it arrives.

## The Ariadne binding keeps the release separate

The original implementation deferred the binding while Ariadne's
`grounded-agent-predicate` frontier was open. Ariadne now supplies the
`grounded-agent/v1` predicate and capture adapter. The Wildcat reference uses
that existing adapter without changing either owner's format or frontier.

The Berean release stays a separate document. Ariadne recomputes its component
identities and projects its policy and recorded results into the registered
predicate; Berean still grades the answers. The Wildcat statement is unsigned,
so it establishes no publisher identity. Its adapter records producer version
`0.2.0`, the version that built the fixed release; later skill metadata does
not rewrite that evidence. The statement sits outside the exact release file
set to avoid making the release include its own binding.

## Aave v4 reads are copied bytes, not a cross-plugin reference

The historical Aave reference needed real, block-bound mainnet reads that verify
offline. The Lazarus example fixture at
`plugins/lazarus/examples/aave-v4-spoke-v0-release/fixture/` preserves exactly
that: recorded RPC outcomes for a Aave v4 contract at block 25870892,
keyed by `request_key = sha256(canonical({method, params}))`.

Berean's example carries its own `reads.jsonl` holding the records it uses,
copied byte for byte, rather than reading the Lazarus fixture path at run
time. Reasons:

1. Each marketplace plugin must be usable alone. A release that only
   verifies when a sibling plugin happens to be checked out beside it is not
   self-contained, and an installed plugin does not see its siblings.
2. The Lazarus fixture is a digested component of a published release;
   nothing may depend on being able to write near it or reshape it.

The copy is held honest the same way Ariadne holds its copied Lazarus
constants: a drift test asserts each copied record is byte-identical to the
record with the same request key in the Lazarus fixture whenever that plugin
is present in the tree. The copied records keep their evidence class,
`recorded-rpc`, and berean never restates them as anything stronger.

## The demonstration corpus is frozen and fabricated

The historical Aave release's documents describe the demonstration subject in a
form that lets every gate fire: a claim the chain confirms, a claim a later
block contradicts, a poisoned document carrying instructions, and a question
the corpus cannot answer. They are written for the release and frozen by
digest in its corpus manifest.

They are not Wildcat documentation. The current Wildcat release keeps three
captured official documents separate from two constructed adversarial specimens. Reusing
Lemma's baseline corpus was considered and rejected: those files carry
mutable marketplace-context blocks that frontier passes rewrite, so pinning
their bytes would break at the next prose refresh. A corpus that exists to
demonstrate byte-exact pinning cannot be built on bytes that move under it.

## The original specification header

The specification is preserved at [spec.md](spec.md) with one change: its
marketplace block, which read "Berean remains unbuilt. Lemma can prepare
source-linked chunks and Ariadne can bind a future agent release to its
evidence; neither supplies the grounded answering and evaluation discipline
specified here.", now carries the standard rolling context so the repository
prose checks hold it to the same frontier as every other berean document.
