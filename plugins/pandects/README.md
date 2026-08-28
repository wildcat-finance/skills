![Pandects](./assets/characters/pandects.png)

# Pandects

<!-- marketplace-context:start -->
## In one line

Pandects supplies executable credit laws, each paired with a deliberately broken specimen it is proved to catch and a replayable counterexample.

**Current frontier.** The search-record runner records only the Foundry campaign, so Echidna and Medusa results survive as audit prose rather than as records.

**Next Fiat job.** Use /hexaemeron:fiat to widen the search-record runner to the Echidna and Medusa campaigns, so every engine result ships as a record carrying its engine, configuration, sequence length and corpus digest, with a seed where the engine exposes one and a stated absence where it does not. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose. Change a skill's Next Fiat job only when that exact frontier job completed; otherwise leave it unchanged.
<!-- marketplace-context:end -->

## Place in the collective

Pandects states economic properties a credit system should preserve. Fizz or
another fuzz engine can search those properties, Janus can apply relevant laws
around a hook transition, and Hermes must preserve them when changing gas.
Pandects does not discover every protocol property, audit the whole system, or
turn a successful bounded campaign into security sign-off.

Synkrisis is specified to compare validated run observations. It cannot promote
repeated campaign outcomes into a law or a security verdict, and its current
scaffold produces no comparison at all.

Executable laws for credit contracts.

A fuzzer searches a state space. It cannot decide which economic facts must
survive that search. Generic token property libraries cover balances, approvals
and round trips; credit adds time, accrual, queues, changing terms,
delinquency, partial repayment and claims that are neither liquid nor reducible
to a token balance. Every audit rediscovers those facts in prose, implements a
subset in a local harness, and the harness dies with the engagement.

This is the corpus that survives it.

## How it works

The catalogue holds ten laws across conservation, accrual and withdrawal
claims. Nine are exact. The path-independence law carries a bound derived from
the rounding performed by linear accrual, and its tests assert the figures on
both the sound reference and the compounding specimen.

## What it ships

- one-state and transition laws written against economic observables rather
  than protocol-specific function names;
- broken specimens and replayable counterexamples for every law;
- observer, driver and differential adapters for Foundry, Echidna and Medusa;
- a reduced Wildcat market model recording where three laws need narrower
  applicability; and
- a checker, catalogue renderer, search record and tests that keep each law's
  six required parts together.

## Day to day

**Security and audit.** A credit protocol arrives and its economic invariants
have to be settled before a fuzz campaign can mean anything. Pandects supplies
the laws, the assumptions behind them, and evidence that each catches the fault
it names.

**Developers.** A change touches accrual or a withdrawal queue. Run the
applicable laws against the build and inspect the quantities behind any verdict
that moved.

## What a law is

Six parts, and the checker refuses anything with fewer:

1. **It executes.** A Solidity component, not a sentence.
2. **It catches something.** A deliberately broken contract it is proven to
   fail against.
3. **It has been reduced.** A minimal counterexample, replayable without a
   fuzzer.
4. **It says where it applies.** Accounting model, assumptions, required
   observables.
5. **Its bounds are justified.** Exact, or a tolerance naming the arithmetic
   that produces it.
6. **It judges rather than reverts.** A law returns `(bool held, string
   detail)`.

Part 2 is the one that carries the weight. A property asserting `seen() >= 0`
survives a stateful campaign of five hundred calls without complaint, and
nothing in that passing run distinguishes it from a law. The specimen is not
documentation; it is the only evidence that a law is a law.

Part 6 follows from the harness. A campaign runs with `fail_on_revert = false`,
because a credit system reverts constantly and correctly: a withdrawal past the
queue, a borrow past the reserve, a repayment of more than is owed. Under that
setting a revert carries no verdict, so a law using `require` to mean
"violated" reports nothing and is counted as silence.

## What is in the catalogue

Ten laws in three families. Each says what it means, where it means it, and
which contract it is proven to catch.

| Law | Statement | Caught in |
| --- | --- | --- |
| `value-conserved` | Assets held plus debt owed equals lender claims plus accrued fees | `MintedClaims` |
| `reserves-backed-by-claims` | Assets reserved never exceed the lender claims recorded | `OverReserved` |
| `held-assets-partitioned` | Reserved assets plus borrowable assets never exceed assets held | `OverPromised` |
| `debt-falls-only-against-payment` | Debt falls only against held assets rising by at least the fall | `DebtForgiven` |
| `no-accrual-at-rest` | At equal observation times, debt rises only against held assets leaving | `AccruesAtRest` |
| `path-independent` | One long step and the same span in equal small steps agree on debt | `CompoundsPerStep` |
| `recorded-claim-never-shrinks` | A recorded claim keeps its owed amount and never loses payment made | `ClaimHaircut` |
| `queue-order-preserved` | No claim is paid while an older claim is still owed something | `QueueJumped` |
| `reserves-cover-payable` | Reserved assets cover everything owed on the claims declared payable | `PayableBeyondReserves` |

Every one is independent of the others: a state or a transition can break any
one while the rest hold, which is what makes a specimen per law possible at all.
`test/Corpus.t.sol` and `test/Pairs.t.sol` assert that diagonal, so a law
broader than its statement fails the suite rather than passing review.

## Two shapes, because the facts have two shapes

Conservation is a fact about one state: the sums agree or they do not, and no
history is needed to say which. So a `Law` reads one target and judges what it
finds.

Accrual is not. Debt falling without payment cannot be violated by any single
state, however wrong that state is, because the violation is in the transition.
So a `PairLaw` judges two observations, where an `Observation` is a snapshot of
everything a target reports. Three of them compare a system with its own past.
The fourth compares two systems started identically and advanced over the same
span by different routes, which is the only way to see interest that compounds
when it should not.

There is no third shape, and a law says in its applicability which kind of pair
it means. Handed one it cannot judge, it follows one rule: a pair that spans
real time is a state of the world, so hold and say why; a pair nobody could
have meant is a mistake by whoever built it, so refuse and say why.

## The one tolerance

Nine of the ten laws are exact. `path-independent` is not, and its bound is
derived rather than chosen: linear accrual on principal truncates once per
step, so `n` small steps and one long step over the same span differ by at most
`n - 1` units.

At a hundred thousand borrowed over a year, the sound reference lands exactly
one unit apart across two half-year steps, which is the bound. The compounding
specimen lands two hundred and forty-nine away.
`test/counterexamples/Accrual.t.sol` asserts all four figures, so the bound can
be checked rather than believed.

## Run it

From this directory, `plugins/pandects`:

```bash
python3 scripts/pandects.py laws
python3 scripts/pandects.py check
python3 scripts/pandects.py run
forge test
```

`laws` lists the catalogue with each law's applicability. `check` refuses a law
missing any of its six parts, naming the part. `run` searches and writes down
how. `forge test` runs the corpus: both diagonals, the counterexamples, the
adapters, and a campaign over the sound reference.

## Pointing it at your own protocol

The specimen harnesses prove the laws catch what they claim to. `adapters/` is
the other direction: the laws, and your address.

```solidity
import {CorpusObserver} from "pandects/adapters/CorpusBase.sol";

CorpusObserver observer = new CorpusObserver(ICreditObservables(yourSystem));
observer.coreHolds();   // conservation, whatever else is driving that contract
observer.explainCore(); // and why, in the laws' own words
```

That is the observing form, and it offers the one-state laws only. A pair law
needs the state as it was before the last call, and nothing observes a call it
does not sit in front of. An observer offering them would report them holding
forever, for the same reason a law that never fires reports holding.

For those, extend `CorpusDriver` -- or `DrivenCorpusInvariants`,
`DrivenCorpusEchidna`, `DrivenCorpusMedusa`, depending on the engine -- write
your protocol's entry points, and put `records` on every one that changes
state. The entry points are yours to write because they are yours to name: a
base cannot proxy a surface it has never seen.

Nothing catches a forgotten `records`. What it looks like is three succession
laws holding and saying nothing, which reads exactly like a system behaving.
So `recordedCalls` is public and `successionExercised` reads it: zero recorded
calls means those laws searched nothing, whatever they reported. Read the two
together or the first is worth nothing.

Path independence is not in either adapter. It compares two systems advanced
over the same span by different routes, and an adapter fronts one target;
routing calls through it buys a past, not a second system.
`PathIndependenceProbe` takes both, because only you can build two instances of
your own system from the same start.

| Adapter | Laws | Reach |
| --- | --- | --- |
| `CorpusObserver` | 5 one-state | any address |
| `CorpusDriver` | 5 one-state, 3 succession | a target you front |
| `PathIndependenceProbe` | 1 differential | two targets you built |

`adapters/echidna/echidna.yaml` and `adapters/medusa/medusa.json` carry
settings and leave the target empty, because the target is the only part that
is yours.

## Saying how it was searched

A campaign result without its settings is an anecdote. `run` searches and
writes down what it did:

```bash
python3 scripts/pandects.py run --out search-record.json
```

The record names the engine, the argv, the determinism class, the
configuration read out of `foundry.toml` rather than restated, the sequence
length, and a digest of the corpus that was searched.

`run` knows one engine, and it is Foundry. It emits no entry for Echidna or
Medusa, and an engine that did not run is absent from a record rather than
present and empty, so a campaign under either of those is not recorded by this
command at all. Write it down where the run is reported. That gap is the corpus's
held frontier, stated at the top of this file. It is shaped as an
`ariadne` command entry, so a result drops into a release statement without
translation -- shaped as, not built by: the two plugins share no code and a
test pins the shape from this side.

Two things are absent rather than empty, and both are one rule. An engine that
did not run has no entry, because a reader counting entries is counting
searches. And what nobody could read -- a seed Foundry does not report, a
version a binary would not give -- is absent rather than null, because null
says there is nothing to find rather than asking you to go and find it. A
campaign that was killed by the timeout is neither passed nor failed; it
carries an outcome of its own.

The corpus digest covers the catalogue, the law components and the specimens,
with comments stripped and string literals kept. It moves when a law moves and
holds still when somebody improves a docstring.

## Running an engine over it

`src/campaigns/Specimens.sol` carries one harness per specimen, each declaring
both `echidna_` and `property_` prefixes because Echidna looks for the first
and Medusa defaults to the second. A harness with only one of them is silent
under the other engine.

```bash
echidna . --contract SoundCampaign --test-limit 20000
medusa fuzz --compilation-target . --target-contracts SoundCampaign
```

Eight of the ten harnesses are expected to fail, and the expectation is the
point: a campaign reporting every property holding against a contract built to
break one has not searched hard enough. Replay a failing sequence and call
`explain()` for the reason, in the law's own words.

Two harnesses pass. `SoundCampaign` is the sound specimen.
`CompoundsPerStepCampaign` also passes every property under both engines, but
the contract underneath it is broken. Its defect is path independence, which
compares two systems advanced by different routes; a campaign drives one
system along one route and can never see it. That is what a passing campaign
is worth on its own.

Exit codes: 0 success, 1 a check failed, 2 usage or validation error.

## What a law may read

`ICreditObservables`: the asset, total assets held, total debt, total lender
claims, reserved and borrowable assets, accrued fees, and the time the
observation describes. A target implements it, or a thin adapter does, and that
adapter is the only place a protocol's own names appear.

A system with a withdrawal queue also implements
`IWithdrawalQueueObservables`, which adds the claim count, each claim's owed and
paid amounts, and the bound through which the system declares claims payable.
It is a separate interface rather than three more members on the core, because
a system with no queue would have to implement all three and mean none of them,
and an observable that means nothing is worse than an absent one: it reports
zero, and zero reads like an answer. The three laws that need it say so in their
applicability, and a target without it reverts on the read -- which is no
verdict rather than a false one.

A property written against one protocol's function names is a property about one
codebase. The corpus exists because the same economic facts hold across
codebases that share nothing else.

## The demo, end to end

From a clean checkout, in `plugins/pandects`. Nothing here reaches the network
and there is no dependency to fetch.

```bash
python3 scripts/pandects.py laws
python3 scripts/pandects.py check
forge test
python3 scripts/pandects.py run --out search-record.json
```

`laws` prints ten laws with their applicability. `check` reports every part
present. `forge test` runs both diagonals, the counterexamples, the adapters and
the Wildcat model. `run` searches and writes the record.

Then watch a law fire against a contract built to break it:

```bash
echidna . --contract ClaimHaircutCampaign --test-limit 20000 --seed 20260816
```

`recorded_claim_never_shrinks` fails and nothing else does. Replay the sequence
it prints and call `explain()` for the reason in the law's own words.

And the case the corpus was built for -- laws written against no protocol in
particular, pointed at a real design:

```bash
forge test --match-contract WildcatTest
```

`integrations/wildcat/` models a market with batched withdrawals, a reserve the
borrower may not touch, delinquency and penalty accrual.
[`APPLICABILITY.md`](./integrations/wildcat/APPLICABILITY.md) is the operative
source. Six laws apply flatly. `queue-order-preserved` applies at batch
granularity and says nothing per lender. `path-independent` holds while the
market is solvent and stops holding once the penalty is running. And
`recorded-claim-never-shrinks` does not hold over a batch that is still open,
which Echidna found against the shipped adapter after that document had already
claimed it did.

None of those three is a yes or a no, which is what an applicability contract is
for, and the third is the argument for pointing a corpus at a real design rather
than only at contracts written to break it.

## The documents

- [The catalogue](./docs/catalogue.md), rendered for a reader. A test fails if
  it and `catalogue/pandects.json` stop naming the same laws.
- [Writing a law](./docs/writing-a-law.md), the six parts in the order somebody
  adding one meets them.
- [Applicability](./docs/applicability.md), the rules stated once: what a law
  may read, the two shapes, what a pair law does with a pair it cannot judge,
  and what a revert means.

## Dependencies

None. Foundry's invariant runner works on a bare contract, so there is no
`lib/`, no submodule, and nothing to fetch at build or test time. The catalogue
checker is standard-library Python on 3.9 through 3.13.

## What this is not

Not a fuzzer, not a harness generator, and not a generic assertion library.
Echidna, Medusa and Foundry search; this says what to look for.
[`fizz`](https://github.com/wildcat-finance/skills/tree/main/plugins/hexaemeron/skills/fizz)
generates a harness for one repository and can select and adapt these laws;
it stays useful where no public law describes the protocol.

The corpus never says a protocol is safe. It says a law held under a search
that is described.

## Licence

Apache-2.0. See [LICENSE](./LICENSE).
