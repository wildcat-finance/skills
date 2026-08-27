# The five gates

<!-- marketplace-context:start -->
> **Marketplace context: Probitas.** Probitas builds a sourced record of what a counterparty did across lending venues from addresses they declared, without identifying a person or issuing a Wildcat verdict. Use Alexandria for archived lending inputs and Tabularium when the job is publishing a reusable credit-event release rather than assessing one counterparty. **Current frontier:** Euler v1/v2 now ship; Morpho Midnight fixed-maturity coverage and curation remain unimplemented.
<!-- marketplace-context:end -->

What each one checks, and how. Run by `probitas.py verify`, implemented in
`scripts/probitas_lib/gates.py`, one line of output each.

## 1. Address provenance

Every address carries a tier: `declared` by the counterparty, `linked` where
the tie is provable on chain, or `inferred` where it is suspected and nothing
more.

The gate finds every occurrence of every inferred address in the document and
fails if one falls outside the "Addresses not declared" section. It then checks
the reverse: a declared address appearing inside that section fails too. With
no inferred addresses in the run it passes and says so, rather than passing
silently, because a gate that goes quiet is indistinguishable from one that did
not run.

The evidence model refuses the same blurring one layer down. An address given
as both declared and inferred raises at construction rather than quietly
keeping whichever came last.

## 2. Coverage is stated

Every venue in the registry has to have a coverage row. A missing row fails,
and the venue is named.

A row needs a status. A row whose status is `checked` or `empty` also needs a
block range, because a venue that was actually queried can say over what span.
A venue with status `unimplemented` or `unconfigured` cannot, and inventing one
would be worse than the gap it is already declaring.

The five statuses mean different things and the difference matters:

| Status | Meaning |
| --- | --- |
| `checked` | The adapter ran and returned what it found |
| `empty` | The adapter ran and this counterparty has no history at this venue |
| `error` | The adapter ran and failed. This is not a clean record |
| `unimplemented` | No adapter exists yet |
| `unconfigured` | An adapter exists but the operator supplied no credential |

`empty` is a finding. The other three are gaps and become entries in the
negative space section.

## 3. Sourcing is total

Three checks, in order.

Every record carries a non-empty source. The schema already guarantees this at
construction, so a failure here means the evidence file was edited after it was
written.

Every URL cited in the document resolves to a record's source. A link to
something no record mentions fails.

Then the sieve. Gate 3 rebuilds, from the evidence alone, every number and hash
a truthful dossier could carry: raw values, the same values formatted as
amounts, basis points, durations and dates, block numbers, addresses, sources
and their shortened forms. It uses the same formatting helpers the renderer
uses, so both halves agree without the checker having to trust the renderer's
output. It then scans the document for every hex string and every run of four
or more digits, and fails on any that is not in that set.

This catches an invented transaction hash, an amount rounded in the retelling,
and a market that was never there. It deliberately does not read sentences: a
paragraph of prose carrying no figures passes untouched, because the gate
checks assertions of fact rather than tone.

Three passes, because one is not enough. The first splits on word boundaries.
The second catches a number grouped with spaces, since `9 000 000` walks past a
sieve that treats a space as a boundary and a wrong amount is just as wrong
written that way. The third catches a hash or address written without its `0x`,
because sixteen hex characters in a row is not something prose does by
accident.

The threshold is four digits. Below that the false positive rate is not worth
it, and an underwriting document rarely turns on a number that small.

The sieve fails closed on formatting it did not produce. A correct figure
regrouped by hand fails too, and that is deliberate: teaching it every way to
group a thousand is how the spaced evasion gets back in, and it is cheaper to
use the rendered form than to argue with the checker.

## 4. Negative space is explicit

The "What could not be established" section has to exist, has to be non-empty,
and has to come before any summary. Where a heading appears twice, the first
occurrence counts, so a summary planted near the top cannot hide behind a real
one at the bottom.

## 5. No score without a rubric

The gate looks for a verdict, meaning a rating word followed by an actual
value: `rating: B+`, `score = 72`, `rated 4 out of 5`. The word on its own is
not a verdict, and a sentence saying the tool emits no rating is doing the
opposite of taking a view, so a denial within thirty characters before the
match is skipped. A gate that fires on its own boilerplate is a gate people
learn to ignore.

Where a verdict is found, the document must also print a rubric. This version
emits no rating at all, following the specification's lean toward evidence
without one, so in practice the gate passes by having nothing to catch. It
exists so that whoever adds a rubric later finds the discipline already
written down rather than having to invent it.

## One citation that points at the market rather than the event

A Wildcat withdrawal batch that expired with no expiry event indexed is cited
to the transaction that created the market. That transaction did not cause the
expiry. The citation identifies the market so a reader can go and look, which
is the best available and less bad than the alternatives: dropping the finding
would hide a lender who asked for money and did not get it, and reporting it
uncited would break gate 3. Recorded here so nobody has to work out why a date
and a citation disagree.
