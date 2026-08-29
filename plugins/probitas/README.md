![Probitas](./assets/characters/probitas.png)

# Probitas

<!-- marketplace-context:start -->
## In one line

Probitas builds a sourced dossier of borrowing and repayment across lending venues from addresses the counterparty declared, without identifying a person or issuing a Wildcat verdict.

**Current frontier.** Euler v1/v2 now ship; Morpho Midnight fixed-maturity coverage and curation remain unimplemented.

**Next Fiat job.** Use /hexaemeron:fiat to add fail-closed Morpho Midnight fixed-maturity coverage so a dossier can establish whether repayment was timely. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose. Change a skill's Next Fiat job only when that exact frontier job completed; otherwise leave it unchanged.
<!-- marketplace-context:end -->

## Place in the collective

Alexandria preserves venue captures and Tabularium turns supported records into
rebuildable credit events. Probitas consumes that evidence, keeps venue gaps and
source classes visible, and writes the counterparty-level dossier. It never
infers undeclared identity, blesses a borrower, sets credit terms, or replaces a
lender's judgement.

Synkrisis does not compare counterparties or dossiers. Its subject is
validated agent-run observations, its delivered operations build a checked
cohort and infer bounded findings over one, and neither skill can make an
underwriting decision.

A sourced dossier on a counterparty's record across on-chain lending venues,
built from the addresses they declared.

Give it an entity name and the addresses a counterparty has declared, and it
produces the writeup: what they borrowed, whether they gave it back, and what
could not be established.

The reason to want this is undercollateralised lending, where nothing stands
between a lender and a total loss except a judgement about the borrower, and
that judgement usually gets assembled by hand from whatever the person asking
happens to remember. The tool is not limited to that case. Most
on-chain borrowing is overcollateralised and it still tells you plenty: a
liquidation says a price moved, a bad debt says somebody was not made whole,
and a missed maturity says what it says anywhere.

The protocol stays out of it. Wildcat Labs doesn't vet borrowers, and becoming
the party that blesses counterparties would make us the underwriter we chose
not to be. So this runs on the lender's own machine, against a borrower they're
considering, and they reach their own conclusion. We hand over the instrument
and not the verdict.

## How it works

Undercollateralised lending is the reason to want one: nothing stands between a lender and a total loss except a judgement about the borrower, and that judgement usually gets assembled by hand from whatever the person asking happens to remember. The tool is not limited to that case. Most on-chain borrowing is collateralised and it still tells you plenty, because a liquidation says a price moved, a bad debt says somebody was not made whole, and a missed maturity says what it says anywhere.

Two halves, doing different jobs. A deterministic collector queries venue adapters and writes an evidence file in which a record cannot exist without a transaction hash, a URL or a document reference. The model writes the narrative from that file, and a gate checker reads the document and the evidence together before either ships.

Five gates decide whether a dossier is honest enough to hand to a lender:

1. Declared, provably linked and inferred addresses stay in separate sections.
2. Every venue in the registry gets a coverage row, and a venue that was queried says over what block range. Silence about a venue would read as a clean record.
3. Every assertion carries a citation, and every figure in the document traces back to a record.
4. What could not be established gets its own section, ahead of anything that reads like a conclusion.
5. No score without a rubric printed beside it. This version emits none.

Gate 3 is the one that does the work. It rebuilds, from the evidence alone, every number and hash a truthful dossier could carry, then fails the document on any figure that is not in that set. An invented transaction hash, an amount rounded in the retelling, a market that was never there: each fails the run rather than shipping in it.

## What it ships

- the executable [`probitas.py`](./scripts/probitas.py) collector, renderer and gate checker, standard library only;
- adapters for [Wildcat](https://wildcat.finance), Morpho Blue, Euler v1 and Euler v2, an archive route over verified Alexandria releases for Goldfinch and Clearpool, and eleven further venues carried as named gaps rather than silence;
- nine synthetic borrower fixtures, including the cured delinquency that a hand-assembled writeup usually reads as a default;
- a [committed example dossier](./docs/example-dossier.md) that the tests regenerate and compare, so it cannot drift;
- [a guide to closing a coverage gap](./docs/adding-a-venue.md) that assumes no knowledge of Wildcat; and
- 321 tests and an audit log ([`audit/AUDIT.md`](./audit/AUDIT.md)) recording every round, including the fixes that were wrong the first time.

## Day to day

**Business development.** A counterparty asks for a market and someone has to decide whether their word is worth anything. Give this the addresses they declared and it comes back with what they borrowed elsewhere, whether they gave it back, and a list of the venues nobody could check, so the thin parts of the record are visible rather than absent.

**Finance.** Exposure to a name that also borrows in three other places. The dossier states each position's venue, the amounts as exact on-chain integers, and whether anything was left unpaid after a liquidation, which is the number that ends up mattering.

**Security and audit.** A document arrives asserting things about a counterparty and you have to decide whether to believe it. Run `verify` against the evidence file it came with: every figure in the document has to trace back to a record with a transaction hash, and one that does not fails the check by arithmetic rather than by your reading it closely.

## Run it

From this directory, `plugins/probitas`:

```bash
python3 scripts/probitas.py venues

python3 scripts/probitas.py collect --entity "Acme Trading Ltd" \
  --address 0xa1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1 \
  --fixtures tests/fixtures/demo --run-id demo --out evidence.json

python3 scripts/probitas.py render evidence.json --out dossier.md

python3 scripts/probitas.py verify dossier.md evidence.json
```

Five gate lines and exit 0. `verify` exits 1 and names the gate when a dossier
breaches one, which is the only exit code worth wiring into anything.

That sequence produces [`docs/example-dossier.md`](docs/example-dossier.md)
exactly. The test suite regenerates it and compares, so the committed example
can't drift from what the tool actually does.

Drop `--fixtures` to run against the live venues instead of a synthetic
borrower.

### Two routes, and how to ask for them

`collect` gathers from two routes. The adapter route queries the venues that
ship an adapter, backed either by the network or by a fixture directory. The
archive route reads verified Alexandria releases through a disposable index,
which is where Goldfinch and Clearpool history lives. A real diligence run
usually wants both, so they combine:

```bash
python3 scripts/probitas.py collect --entity "Acme Trading Ltd" \
  --address 0xa1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1 \
  --live --alexandria-index alexandria.sqlite --out evidence.json
```

| Flags | Adapter route | Archive route |
| --- | --- | --- |
| none | live network | not run |
| `--fixtures DIR` | fixture directory | not run |
| `--alexandria-index X` | not run | archive |
| `--fixtures DIR --alexandria-index X` | fixture directory | archive |
| `--live --alexandria-index X` | live network | archive |
| `--live` | live network | not run |
| `--live --fixtures DIR` | refused, exit 2 | refused, exit 2 |

An offline end-to-end run of both routes lives in
[`tests/test_union.py`](./tests/test_union.py). It builds a disposable
Alexandria index from that plugin's checked-in demonstration, collects over the
fixture and archive routes together, renders, and puts the result through all
five gates without reaching the network.

`--live` exists because an index on its own still suppresses the adapter route,
exactly as it always has. Making the index additive by default would have
started sending requests from every command that already passes one, and a tool
whose whole claim is provenance should not widen what it reaches to save a
flag. `--fixtures` and `--live` both name what backs the adapter route, so they
contradict each other and the run says so.

Every coverage row names the route that produced it, and an archive row names
the Alexandria releases behind it. A venue some route answered for is not
reported as a gap because another route had nothing to say about it; a route
that failed still leaves one. The archive route keeps the original Goldfinch or
Clearpool venue and the Alexandria release, capture, component and row
identities on every record.

### Options

- `--entity`: The counterparty's name. Required.
- `--address`: An address they declared. Repeatable and required.
- `--inferred`: An address suspected but neither declared nor provably linked. Kept in its own section; gate 1 fails the dossier if a finding against one appears anywhere else.
- `--fixtures`: Read venue responses from a directory instead of the network. Contradicts `--live`.
- `--live`: Run the adapters against the network. Needed beside `--alexandria-index`, and the default when no index is given.
- `--alexandria-index`: Also read verified archive-backed evidence from this index. On its own it suppresses the adapter route and reaches no network.
- `--run-id`: A label for the run, printed in the dossier.
- `--timeout`: Seconds per request, default 30.
- `--out`: Where to write, or `-` for stdout.

### The fixtures

Eleven of them, covering all four shipped venues and the cases worth being sure
about.

For Wildcat: a clean record, a delinquency cured inside the grace period, a
default with penalty interest running and a withdrawal batch that expired
unpaid, and a borrower with no history at all. The cured one is the case a
hand-assembled writeup usually reads as a default.

For Morpho: a clean borrower, a liquidation the collateral covered, a
liquidation that left bad debt behind, and again an empty one. The two
liquidations are the pair that keeps the distinction honest, since only the
second one cost anybody money.

For Euler v2: an EVC owner with a borrow, repayment, interest accrual and
liquidation, plus an empty event ledger. The fixture checks that interest
accrual is omitted without losing the borrow and that liquidation debt and
collateral retain their own decimals.

For Euler v1: proxy-log borrow, repayment and liquidation events, plus an empty
history. The fixture binds each log to its block hash and keeps the debt and
collateral scales separate.

`demo` combines a Wildcat default with Morpho bad debt, and is what the
quickstart above runs.

## How it works

Two halves, doing different jobs.

The deterministic half is a Python program. It queries lending venues for the
declared addresses and writes every result into an evidence file. A record
can't enter that file without a transaction hash, a URL or a document reference
attached, because the schema won't represent one.

The model half writes the narrative, reading the evidence file and nothing
else. Then a gate checker reads the dossier and the evidence together and
decides whether the document may ship.

The split is the whole design. Ask a model to cite its sources and some
proportion of what comes back will be citation-shaped and hollow, and nothing
inside the model will notice. [The five gates](skills/probitas/references/gates.md)
covers what each check does about that.

## The gates

1. **Address provenance.** Every address is declared by the counterparty or
   provably linked on chain. Inferred addresses get their own section.
2. **Coverage is stated.** The venues checked and the block range, by name.
   Silence about a venue is a gap in the dossier, not a clean record.
3. **Sourcing is total.** Every assertion carries a transaction hash, a URL or
   a document reference, and every figure traces back to a record.
4. **Negative space is explicit.** What could not be established, in its own
   section, ahead of any summary.
5. **No score without a rubric.** If a rating is ever emitted, the rubric
   prints beside it and the inputs to each component are shown.

## What it never does

No personal data. No social handles, no employment history, no working out
which individual controls an address. A dossier that starts profiling people is
a different product and a worse one, and that line sits in the tool rather than
in whoever is operating it at two in the morning.

No score, in this version. The specification leaves the question open and leans
toward evidence without a rating, because a rating invites people to lean on it
harder than the data can bear. Gate 5 is implemented anyway, so whoever adds a
rubric later finds the check already standing.

## Venues

Fifteen in the registry, four with adapters. The other eleven appear in every
coverage table saying nobody checked, which is gate 2 working rather than an
omission.

- Wildcat: Shipped. Public Goldsky subgraph, no key.
- Morpho Blue: Shipped. Borrowing on Blue markets, keyless public API.
- Euler v1: Shipped. Canonical proxy event log through a keyless archival RPC.
- Euler v2: Shipped. Keyless V3 event ledger and liquidation API; Goldsky is not used for history.
- Centrifuge: Keyless GraphQL, introspects cleanly. The most build-ready of the gaps.
- Aave v3, Aave v4: Keyless first-party API. v4 went live on mainnet in March 2026.
- MetaMorpho vaults, Morpho Vaults V2, Morpho Midnight: Three further Morpho surfaces, all keyless, none collected.
- Maple Finance: Answers, but disables introspection and publishes no schema.
- Compound v3, Goldfinch: Need a paid Graph gateway key.
- Clearpool: Live, behind a bot challenge. An agreement is the way in, not a workaround.
- TrueFi: Restructured through a token migration; no public endpoint answered.

Six of the eleven gaps need only an adapter and nothing from anyone: Centrifuge,
both Aave versions, and Morpho's three other surfaces. The rest wait on a key,
a schema, or an agreement.

Goldfinch is worth a line of its own. It wound down in June 2026 after
defaults, which makes it a list of counterparties who did not repay, sitting on
chain and directly relevant to anyone they approach next. A dead protocol is
not a dead record.

The four that ship read differently on purpose. Wildcat is undercollateralised,
so a missed reserve ratio is about the borrower. Morpho is overcollateralised,
so a liquidation is about a price, and the dossier says so in as many words.
Bad debt is the one Morpho signal that bears on conduct, and it gets its own
line. Euler v1 reads the monolithic protocol proxy and preserves exact borrow,
repayment and liquidation amounts. Euler v2 is also overcollateralised: it records borrows and repayments
under the EVC owner, keeps the subaccount, and never labels a liquidation a
default.

[Adding a venue](docs/adding-a-venue.md) says what each gap actually is and
what closing one takes. It assumes no knowledge of Wildcat.

## Tests

From the repository root:

```bash
python3 -m unittest discover -s plugins/probitas/tests -t plugins/probitas
```

Run the tests with the exact interpreter in the suite
[pin](https://github.com/wildcat-finance/skills/blob/main/.python-version). The
implementation uses only the standard library: no install step, lockfile, or
dependency tree. Someone deciding whether to trust a counterparty should not
first have to decide whether to trust forty transitive packages.

## Reading further

- [`docs/adding-a-venue.md`](docs/adding-a-venue.md) -- every gap, what blocks
  it, and how to close one.
- [`docs/euler-goldsky-discovery.md`](docs/euler-goldsky-discovery.md) -- the
  preserved schemas, failed legacy probes, V3 event source and Euler v1
  canonical-log source.
- [`docs/euler-v1-thegraph-schema.graphql`](docs/euler-v1-thegraph-schema.graphql)
  -- the current Euler v1 schema embedded by Graph Explorer.
- [`docs/example-dossier.md`](docs/example-dossier.md) -- what the output
  looks like.
- [`audit/AUDIT.md`](audit/AUDIT.md) -- every audit round, including the
  findings that were wrong the first time.

## Licence

Apache-2.0. See [LICENSE](LICENSE).
