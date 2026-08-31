---
name: probitas
description: >
  Build a sourced dossier on a counterparty who wants an undercollateralised
  market: what they borrowed across lending venues, whether they gave it back,
  and what could not be established. Use when someone names an entity and the
  wallet addresses it has declared and asks for diligence, borrowing history,
  repayment record, delinquency history, or an underwriting writeup. Do not use
  for questions about a single market's own numbers, and never to work out
  which individual controls an address.
metadata:
  version: "1.2.0"
---

<p align="center">
  <img src="../../assets/characters/probitas.png" width="1200">
</p>

# Probitas

## Frontier

Probitas owns its own counterparty-diligence frontier, not Hexaemeron's delivery or
Solidity frontier. Its version, held target, next job, and maturity
state live in [EVOLUTION.md](EVOLUTION.md). Do not recommend or run
another frontier pass after that ledger becomes mature.

<!-- marketplace-context:start -->
## Where this sits

Probitas builds a sourced dossier of borrowing and repayment across lending venues from addresses the counterparty declared, without identifying a person or issuing a Wildcat verdict.

**Current frontier.** Morpho Midnight fixed-maturity coverage now ships API-scoped on Base; secondary-market borrow exits stay refused as unattributable and Morpho curation remains uncollected.
<!-- marketplace-context:end -->

Wildcat lends without collateral. Nothing stands between a lender and a total
loss except a judgement about the borrower, so the counterparty record is the
whole of the security. This assembles that record from public sources and hands
it over without a verdict attached.

Alexandria preserves venue captures and Tabularium maps supported records into
rebuildable credit events. Probitas consumes that evidence at the counterparty
level. It keeps gaps visible and never infers undeclared identity, blesses a
borrower, sets terms, or replaces the lender's judgement.

Synkrisis does not compare counterparties or dossiers. Its subject is
validated agent-run observations, its delivered operations build a checked
cohort and infer bounded findings over one, and neither skill can make an
underwriting decision.

`$SKILL_DIR` is the directory holding this file. The tool lives at
`$SKILL_DIR/../../scripts/probitas.py`; resolve it from where you loaded this
skill.

## Day to day

**Business development.** A counterparty asks for a market and someone has to
decide whether their word is worth anything. Give this the addresses they
declared and it comes back with what they borrowed elsewhere, whether they gave
it back, and a list of the venues nobody could check, so the thin parts of the
record are visible rather than absent.

**Finance.** Exposure to a name that also borrows in three other places. The
dossier states each position's venue, the amounts as exact on-chain integers,
and whether anything was left unpaid after a liquidation, which is the number
that ends up mattering.

**Security and audit.** A document arrives asserting things about a
counterparty and you have to decide whether to believe it. Run `verify` against
the evidence file it came with: every figure in the document has to trace back
to a record with a transaction hash, and one that does not fails the check by
arithmetic rather than by your reading it closely.

## The sequence

Four commands, in this order. Do not skip the fourth.

```bash
python3 scripts/probitas.py venues

python3 scripts/probitas.py collect \
  --entity "<name>" --address 0x... [--address 0x...] \
  [--inferred 0x...] --out evidence.json

python3 scripts/probitas.py render evidence.json --out dossier.md

python3 scripts/probitas.py verify dossier.md evidence.json
```

`collect` runs every venue adapter over the declared addresses and writes the
evidence file. A record cannot enter that file without a transaction hash, a
URL or a document reference, because the schema will not represent one.

`collect` gathers from two routes. The adapter route queries the venues that
ship an adapter, backed by the network or by a fixture directory. The archive
route reads verified Alexandria releases through an explicit disposable index.
Ask for both in one run:

```bash
python3 scripts/probitas.py collect \
  --entity "<name>" --address 0x... \
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

An index on its own still suppresses the adapter route and reaches no network,
so no invocation that worked before starts making requests. `--live` is how a
run asks for the network beside an index, and it contradicts `--fixtures`.

Every coverage row names the route that produced it: `live`, `fixtures`,
`archive`, or `none` for a venue nobody reached. An archive row also names the
Alexandria releases behind it. A venue some route answered for is not reported
as a gap because another route had nothing to say about it; a route that failed
still leaves one.

The archive route keeps Goldfinch and Clearpool as venue IDs and records
Alexandria's release, component, capture, row and evidence identities. It
combines per-chain coverage conservatively and leaves every unharvested
registry venue visible as a gap. A zero-row venue is empty only when complete
archive coverage includes every requested address, venue, chain and time
boundary and the mapping has no unsupported records. It does not infer a
person, default, full repayment or current balance.

The checked-in Alexandria `credit-history-v0` example exercises this explicit
index path offline and checks the resulting evidence and dossier against fixed
receipts. It does not alter the normal live and fixture routes.

Morpho Midnight coverage is Base chain id 8453 through its own keyless REST API
alone. Every cursor page is exhausted once, the coverage row states the
observation time and the returned index bound, and the API's history lower
bound is unpublished, so the claim is API-scoped history rather than
archive-chain completeness. An incomplete, ambiguous or out-of-bounds response
returns no records and a named gap instead of a partial answer, and a
secondary-market borrow exit is refused because its account-attributed debt
units are unproved. An overdue maturity closed by liquidation reads as settled
late through liquidation, never as voluntary repayment.

`render` builds the document in the order the specification sets: coverage and
what could not be established stand ahead of anything that reads like a
conclusion, and findings against addresses the counterparty did not declare sit
in their own section at the end.

`verify` reads both together and checks the five gates, printing one line each.
Exit 0 means the dossier may ship. Exit 1 names the gate that stopped it.

## Your part, and its limit

Write the narrative sections from the evidence file and nothing else. The
summary, and any commentary on a venue, are yours. Everything above them is
rendered from records.

You may not introduce a figure the evidence does not contain. Gate 3 rebuilds,
from the evidence alone, every number and hash a truthful dossier could carry,
and fails the document on any it finds that is not in that set. An invented
transaction hash, a rounded amount, a market that was never there: each of
those fails the run rather than shipping in it. This is not a formality to work
around. It is the reason a lender who did not run the tool can trust the
output.

If the evidence is thin, say it is thin. A borrower who used a fresh address
for every market has a short record, and a short record is not a bad one. The
dossier has to say which of those it is looking at.

## The five gates

1. **Address provenance.** Declared, provably linked, and inferred stay in
   separate sections. An inferred address never feeds a conclusion.
2. **Coverage is stated.** Every venue in the registry gets a row, and a venue
   that was queried says over what block range. Silence about a venue would be
   an omission; a row saying nobody checked is a gap, and a gap is not a clean
   record.
3. **Sourcing is total.** Every assertion carries a transaction hash, a URL or
   a document reference, and every figure in the document traces back to a
   record.
4. **Negative space is explicit.** What could not be established gets its own
   section, ahead of any summary.
5. **No score without a rubric.** This version emits no rating, following the
   specification's own lean toward evidence without one. The gate is
   implemented anyway, so whoever adds a rubric later finds the check standing.

See [the gates](references/gates.md) for what each one does mechanically, and
[venue coverage](references/venues.md) for what is checked and what is not.

## What this never does

- **No personal data.** No names of individuals, no social handles, no
  employment history, and no attempt to work out which human is behind an
  address. The evidence schema refuses a value key that names a person, so this
  is a property of the tool rather than a rule you have to remember at two in
  the morning.
- **No social graph.** The counterparty graph covers relationships the
  counterparty declared and relationships visible on chain between the declared
  addresses. Nothing is inferred from off-chain association.
- **No unsourced assertion.** A claim without a citation is dropped, not
  softened into a hedge.
- **No verdict from Wildcat.** The lender reaches their own conclusion. Wildcat
  Labs does not vet borrowers, and a dossier that arrives with our judgement
  attached would make us the underwriter we chose not to be.

If someone asks you to work out who is behind an address, say plainly that
probitas covers entities and addresses and that a dossier which starts
profiling people is a different product and a worse one. Then carry on with the
part you can do.

## When a gate fails

Fix the document, not the gate. A gate 3 failure naming a figure means the
narrative asserts something the evidence does not support: cut the sentence or
find the record. A gate 2 failure means coverage is incomplete, which is a
collection problem rather than a writing one. Never edit `verify` to make a
dossier pass.

## Promise Machine contract

### probitas-evidence-collection

- Promise: A successful `collect` writes evidence only for declared entity addresses and separately labelled inferred addresses, with one source reference per record, one coverage row for each venue and route that answered, one row for each venue no route reached, every row naming its source class, and explicit coverage or gap for every registered venue.
- Evidence: The exact entity and address inputs, the routes the invocation selected, the venue registry, adapter responses and any verified Alexandria index with the release identities behind each archive row, the evidence schema, source references and emitted `evidence.json`.
- Evidence classes: recorded, checked
- Boundary: Collection does not establish human identity, source completeness, default, full repayment, current balance, creditworthiness or a Wildcat decision, and a source class names the route that answered rather than vouching for what it returned.
- Authorises: Rendering a dossier from the collected evidence while keeping address provenance, route provenance, venue scope and gaps separate.
- Consequence: 1
- Refuses: Feeding inferred addresses into conclusions, omitting an unqueried venue, admitting an unsourced record, admitting a coverage row that does not name its source, naming a release on a row no archive produced, treating an archive gap as clean history, or reaching the network because an archive index was supplied.
- Recovery: Correct the declared inputs, the selected routes or the source adapter, collect again and retain any unresolved venue or interval as an explicit gap.
- Exceptions: none

### probitas-dossier-rendering

- Promise: A successful `render` derives the dossier's factual tables from the evidence file and places coverage and unknowns before narrative conclusions.
- Evidence: The validated evidence JSON, deterministic rendered sections, exact figures and source references, and the emitted dossier bytes.
- Evidence classes: recorded, recomputed
- Boundary: Rendering does not validate later human narrative, infer identity, create a rating or decide whether a counterparty should receive a market.
- Authorises: Completion of narrative sections using only the same evidence and submission of the dossier to `verify`.
- Consequence: 1
- Refuses: Introducing a figure, hash, market, identity claim or venue conclusion absent from the evidence file.
- Recovery: Remove the unsupported narrative or obtain a source record through a fresh collection, rerender and rerun verification.
- Exceptions: none

### probitas-dossier-verification

- Promise: A successful `verify` establishes that the exact dossier and evidence file pass address provenance, coverage, total sourcing, visible negative space and rating-rubric gates.
- Evidence: The dossier bytes, evidence JSON, reconstructed allowed figures and hashes, five named gate results and zero exit status.
- Evidence classes: checked, recomputed, recorded
- Boundary: Verification establishes dossier conformance, not factual completeness beyond recorded coverage, personal identity, a credit score, underwriting approval or a Wildcat Labs verdict.
- Authorises: With the decision-maker's separate authority, release of the sourced dossier for an independent lending decision.
- Consequence: 3
- Refuses: Shipping a dossier after any gate fails, hiding a gap, allowing inferred-address evidence into a conclusion or presenting the document as Wildcat approval.
- Recovery: Fix the evidence or dossier named by the failed gate, preserve unresolved gaps and rerun all five gates before release.
- Exceptions: none

### probitas-statement-emission

- Promise: A successful `verify --statement-out` emits a canonical unsigned in-toto Statement v1 only when all five gates passed, with one statement-level subject array binding the exact checked dossier and evidence bytes by SHA-256; absence of that statement authorises nothing.
- Evidence: The exact dossier and evidence bytes read once, their SHA-256 digests and byte counts, the five named passed gate results, canonical statement bytes and successful atomic output.
- Evidence classes: recorded, checked, recomputed
- Boundary: The statement records the pair binding and gate results. It does not sign, verify a signature or upgrade `verify` into release authority; `probitas-dossier-verification` keeps that authority, and Ariadne gates 2 and 5 remain unchecked for this unregistered predicate type.
- Authorises: Hand-off of the unsigned statement bytes for Ariadne core-gate inspection or downstream cosign signing without strengthening the dossier's evidence claims.
- Consequence: 1
- Refuses: Emitting after any gate fails, naming stdout or either input as the output, exceeding Ariadne's bounded-input limit, or treating a missing statement or unchecked signature as authority.
- Recovery: Repair the failed dossier or evidence, choose a distinct file output, rerun all five gates and retain only the successful replacement.
- Exceptions: none
