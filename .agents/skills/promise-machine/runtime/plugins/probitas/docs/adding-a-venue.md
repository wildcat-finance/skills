# Adding a venue

<!-- marketplace-context:start -->
> **Marketplace context: Probitas.** Probitas builds a sourced record of what a counterparty did across lending venues from addresses they declared, without identifying a person or issuing a Wildcat verdict. Use Alexandria for archived lending inputs and Tabularium when the job is publishing a reusable credit-event release rather than assessing one counterparty. **Current frontier:** Euler v1/v2 now ship; Morpho Midnight fixed-maturity coverage and curation remain unimplemented.
<!-- marketplace-context:end -->

Probitas builds a dossier on what a counterparty has done across on-chain
lending venues: what they borrowed, whether they gave it back, and what could
not be established. It reads lending venues through small adapters, one
per venue, and it currently reads four of the fifteen it knows about.

The other eleven are the interesting part of this document. Each one is a named
gap in every dossier the tool produces, and closing one is a self-contained
piece of work that makes every future dossier better. This is what each gap
actually is, and what it takes to close it.

You don't need to know anything about Wildcat to write an adapter. You need to
know one lending protocol well enough to say what its events mean.

## Why the gaps are stated rather than hidden

A dossier that quietly skips a venue reads exactly like a dossier that checked
it and found nothing. For a lender deciding whether to hand over money with no
collateral behind it, those two are opposites, and telling them apart is most
of the value of the document.

So every venue in the registry gets a row in every dossier, whether an adapter
exists or not, and the row says which of five things happened:

| Status | Meaning |
| --- | --- |
| `checked` | The adapter ran and returned what it found |
| `empty` | The adapter ran and this counterparty has no history here |
| `error` | The adapter ran and failed. This is not a clean record |
| `unimplemented` | No adapter exists yet |
| `unconfigured` | An adapter exists but no credential was supplied |

`empty` is a finding. The last three are gaps, and they appear in the dossier's
negative space section ahead of anything that reads like a conclusion. A run
that checks a venue whose registry flag claims an adapter it does not have
fails its own test suite, so the table cannot drift into claiming coverage the
tool does not have.

## What is reachable today

Probed directly rather than taken from documentation. Everything below was a
live request.

### Built

| Venue | Source | Key |
| --- | --- | --- |
| Wildcat | Goldsky subgraph | none |
| Morpho Blue | `blue-api.morpho.org/graphql` | none |
| Euler v1 | Canonical proxy log through `mainnet.gateway.tenderly.co` | none |
| Euler v2 | `v3.euler.finance` activity, liquidation and EVK vault endpoints | none |

### Reachable, keyless, and unbuilt

These need an adapter and nothing else. No permission, no key, no negotiation.

**Centrifuge** is the most build-ready of the lot. `api.centrifuge.io` serves a
Ponder GraphQL API that introspects cleanly and answers without a key. Twenty
four pools on mainnet, with pools, holdings, investor transactions and debt
changes all queryable. Someone who knows Centrifuge's pool model could write
this adapter in an afternoon.

**Aave** turned out to be reachable after all, which was a correction to an
earlier assumption here rather than a discovery. The subgraph route needs a
paid gateway key, so the venue was written off. But `api.aave.com/graphql`
answers without one, and `api.v4.aave.com/graphql` does the same for v4, which
went live on Ethereum mainnet in March 2026 with a hub and spoke architecture
in place of one pool. A counterparty who borrowed on v3 and borrows on v4 is
one counterparty, and a dossier covering one version is quietly wrong about
them.

Introspection is switched off on both, which is a nuisance rather than an
obstacle: the full schema is published in
[`aave/aave-v4-sdk`](https://github.com/aave/aave-v4-sdk) at
`packages/graphql/schema.graphql`. The query an adapter wants is `activities`,
and this one runs today:

```graphql
query($user: EvmAddress!, $chains: [ChainId!]!) {
  activities(request: {
    query: { chainIds: $chains }
    user: $user
    types: [BORROW, REPAY, LIQUIDATED]
    pageSize: TEN
  }) {
    items {
      __typename
      ... on BorrowActivity {
        timestamp
        txHash
        borrowed {
          amount { onChainValue decimals }
          token { info { symbol } }
        }
      }
    }
    pageInfo { next }
  }
}
```

Two details that cost an hour of guessing, so they are written down here. `user`
is a sibling of `query` rather than a field inside it, and `query` is a oneof
that takes exactly one of `chainIds`, `hub`, `spoke`, `txHash` or
`userPositionId`. And `DecimalNumber` carries `onChainValue`, the exact integer,
alongside the human-readable `value`. Take `onChainValue`, because probitas
refuses floats and for good reason.

Every activity carries `txHash`, so gate 3 is satisfied by construction on this
venue the way it is on Wildcat.

**Morpho's other three surfaces.** The shipped adapter covers borrowing on Blue
markets. MetaMorpho vaults and Vaults V2 are separate surfaces on the same
keyless API, where a counterparty may appear as a curator rather than a
borrower, and a curator who allocated into a market that took bad debt made a
call that cost depositors money. Morpho Midnight is a fourth surface again:
fixed-rate, fixed-maturity lending on its own keyless REST API at
`api.morpho.org/v0/midnight`, on Base. Midnight is the most valuable of the
three, because a maturity is a date by which the money was due, and that makes
it the only venue outside Wildcat where repayment timeliness has an answer
rather than a story about a price.

### Euler: two versions, two data routes

**Euler v2** ships against the keyless V3 Data API, not the Goldsky simple
subgraph. `/v3/activity/accounts/<owner>/events` supplies the paginated event
ledger and an explicit complete indexed range. `/v3/liquidations` supplies
both liquidation legs. `/v3/evk/vaults/batch` resolves the assets and decimals
once per vault. Records are filed under the EVC owner and retain the subaccount.
`interest_accrued` is checked and omitted; it cannot cause a neighbouring
borrow to disappear.

The Goldsky schema remains preserved because it explains why the adapter does
not use that endpoint: it overwrites active-position balances and cannot
distinguish never borrowed from fully repaid.

**Euler v1** ships from the mainnet event log of proxy
`0x27182842E098f60e3D576794A5bFFb0777E025d3`. The archived contract source
defines borrower-indexed `Borrow`, `Repay` and `Liquidation` events. The first
two carry exact debt amounts; liquidation carries both exact debt repaid and
collateral seized. The adapter queries those topics through the keyless
archival RPC at `mainnet.gateway.tenderly.co`, through its finalized block.

The Messari Euler Finance Ethereum subgraph remains useful as source history.
Its subgraph ID is
`95nyAWFFaiz6gykko3HtBCyhRuP5vZzuKYsZiLxHxLhr`. Graph Explorer currently
points to deployment `QmfTzwSoE3krDFMfYT9XTdwLcdMYBmMwyPqA1FHTMkmsVs`,
version `1.3.0_1.4.0`; the separately reported `QmVRgU…` deployment is not the
current version. Its preserved schema has immutable `Borrow`, `Repay` and
`Liquidate` entities, but it omits the exact debt repaid during liquidation.

Authenticated probes of `_meta`, accounts, markets and borrows all failed at
the gateway because none of the three assigned indexers could serve the
deployment. The archived EulerScan hostname also no longer resolves. Neither
failure affects the shipped adapter. The schema, API probes and successful raw
log capture are preserved in `euler-v1-thegraph-schema.graphql`,
`euler-v1-thegraph-capture.json` and `euler-goldsky-discovery.md`.

The exact probes and preserved v2 schema are in
[`euler-goldsky-discovery.md`](euler-goldsky-discovery.md).

### Reachable, but not without something from someone else

**Compound v3** has no first-party API that answered. The Graph's gateway
rejects unauthenticated requests and the hosted service it replaced is gone, so
this one needs a paid key.

**Clearpool** is running, and its API sits behind a bot challenge that returns
403 to a plain request. Solving that challenge isn't something a diligence
tool should be doing, and probitas won't do it. The way in is an agreement
with Clearpool, not a workaround.

**TrueFi** restructured through 2025 and into a token migration that completed
in May 2026. No public API endpoint answered. The historical
undercollateralised loans are the part worth having.

### Wound down, and still worth reading

**Goldfinch** closed in June 2026 after originating around a hundred million
dollars, with depositors reporting losses far heavier than the dashboard had
been showing.

The instinct is to skip a dead protocol. That instinct is wrong here, and
Goldfinch is close to the perfect argument for this whole tool. A protocol that
wound down after defaults is a list of counterparties who did not repay,
sitting on chain, permanent, and directly relevant to anyone those same
counterparties approach next. The record doesn't stop being true because the
front end went away.

Reaching it needs a gateway key, since Goldfinch's data lived on The Graph.
That is the only thing in the way.

## What an adapter is

A callable that takes addresses and a configuration and returns records plus
one coverage row:

```python
def adapter(addresses, config):
    """addresses maps a lowercase address to its provenance tier."""
    ...
    return records, coverage
```

Everything else is enforced around you.

**A record cannot exist without a citation.** `Record` takes a source at
construction and refuses one that is missing, empty, or not a transaction hash,
an http URL or a `doc:` reference. You can't represent an unsourced claim, so you can't
ship one.

**Amounts stay integers.** A float in a value mapping raises. The danger with
token amounts is not overflow, since Python integers are unbounded, it is
something quietly rounding a balance on the way into a document about money.

**Two assets means two scales.** If your venue reports one amount in the loan
asset and another in the collateral asset, they carry different decimals and
they need different fields. Filing both under one scale produces a figure wrong
by orders of magnitude, which is a mistake this codebase has already made once
and now has a test against.

**No field can name a person.** The evidence schema rejects a value key that
looks like an identity: `name`, `email`, `employer`, `telegram_handle` and so
on. Entity-scoped names like `market_name` are allowed by an explicit list.
Probitas covers entities and addresses. A dossier that starts profiling people
is a different product and a worse one, and the line sits in the code rather
than in whoever is operating it at two in the morning.

**An unrecognised response shape must raise.** This is the one that catches
people, including the people who wrote the existing adapters. If the venue
renames a field or a transaction type and your adapter skips it quietly, every
record vanishes, the coverage row reads `empty`, and a borrower with a history
presents as one with none. List the types you ignore on purpose and raise on
everything else.

**Failing loudly is safe.** An adapter that raises produces a coverage row with
status `error`, which the dossier reports as a gap. Nothing is lost by
refusing to guess.

## What to write

Four things, and one of them is prose.

1. **The adapter**, at `scripts/probitas_lib/adapters/<venue>.py`.
2. **Fixtures**, at `tests/fixtures/<case>/<venue>.json`, holding the venue's
   own response shape. At least a clean borrower and one who did not repay.
   Offline, so the suite never touches the network.
3. **Tests**, including the ones that mutate a fixture and assert the adapter
   raises. Drop a field, corrupt a flag, rename a type. If any of those changes
   the output without raising, the adapter will empty a dossier the day the
   venue ships a schema change.
4. **A note in the registry** saying what your venue's events actually mean,
   because the next person reading a dossier needs it.

Then flip the registry's `implemented` flag. A test asserts the flags match the
adapters actually registered, so it won't let you flip one early.

## The judgement, which is the hard part

The mechanics above are a day's work for someone who knows the protocol. What
takes real care is deciding what an event means, and getting it wrong produces
a confident, well-cited, wrong claim about a named company.

Four worked examples from the venues already built.

**On Wildcat, a cured delinquency is not a default.** A borrower who dipped
below their reserve ratio and came back inside the grace period paid no penalty
interest. Reporting that as a default is the mistake a hand-assembled writeup
usually makes. One of the three synthetic fixtures exists to hold that
distinction still.

**On Morpho, a liquidation is not a default either.** Morpho is
overcollateralised, so nobody was relying on the borrower's word. A liquidation
says a price moved and the protocol closed a position. The record says so in as
many words, because a reader's instinct will be to call it a default. Bad debt
is the exception: when a liquidation does not cover what was owed, lenders lost
money, and that gets its own record.

**On Euler v2, the EVC owner is the subject.** One owner controls 256
subaccounts. A record filed under the touched subaccount alone would split one
counterparty into many apparent borrowers, so each record uses the owner and
keeps the subaccount as event context. Interest accrual is not a new draw and
is omitted. A liquidation remains a collateral event, with its debt and
collateral assets kept on separate scales.

The general shape: ask what the event would have meant if the collateral were
not there. On an overcollateralised venue, most of what looks alarming is a
price moving. On an undercollateralised one, the same event is about the
borrower. Wildcat is the second kind, which is why probitas exists at all.

## The gate you will meet

Once an adapter is written, everything it produces goes through five gates
before a dossier ships. The one you will meet is the third.

Gate 3 rebuilds, from the evidence alone, every number and hash a truthful
dossier could contain, then fails the document on any figure it contains that
is not in that set. An invented transaction hash, an amount rounded in the
retelling, a market that was never there: each fails the run rather than
shipping in it.

This is deliberately unforgiving, and it is aimed at the model writing the
narrative rather than at you. A model asked to cite its sources produces
citation-shaped sentences at some rate above zero, and only something outside
the model catches them. If your adapter's numbers are real, the gate is silent.

## Running it

```bash
python3 scripts/probitas.py venues

python3 scripts/probitas.py collect --entity "Acme Trading Ltd" \
  --address 0xa1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1 \
  --fixtures tests/fixtures/demo --out evidence.json

python3 scripts/probitas.py render evidence.json --out dossier.md
python3 scripts/probitas.py verify dossier.md evidence.json
```

Five gate lines, exit 0. Drop `--fixtures` to run against the live venues.
[`example-dossier.md`](example-dossier.md) is that command's real output.

Tests, from the repository root:

```bash
python3 -m unittest discover -s plugins/probitas/tests -t plugins/probitas
```

Run this with the exact interpreter in the suite
[pin](https://github.com/wildcat-finance/skills/blob/main/.python-version). The
implementation uses only the standard library: no install step or dependency
tree, because someone deciding whether to trust a counterparty should not first
have to decide whether to trust forty transitive packages.

## What this will not do, however it is asked

No personal data, no social graph, and no working out which individual is
behind an address. No unsourced assertion: a claim without a citation is
dropped rather than softened into a hedge. And no score, in this version,
because a rating invites people to lean on it harder than the underlying data
can bear. The gate that would police a rating is implemented anyway, so
whoever adds a rubric later finds the check already standing.

Wildcat Labs does not vet borrowers and this tool does not vet them either. It
runs on a lender's own machine, against a counterparty they are considering,
and they reach their own conclusion. That is the whole design, and an adapter
that respects it is worth more than one that covers more ground.
