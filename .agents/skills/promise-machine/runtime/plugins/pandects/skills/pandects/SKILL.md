---
name: pandects
description: >
  Check a credit protocol against executable laws: conservation, accrual and
  withdrawal claims, each one a Solidity component with a broken specimen it is
  proven to catch. Use when someone asks which invariants a lending or credit
  system should hold, wants properties for a fuzzing campaign, or hands over a
  protocol and asks what could be checked mechanically. Do not use it to
  generate a harness for one repository; that is fizz. Never report a campaign
  under an engine that did not run.
metadata:
  version: "1.1.0"
---

<p align="center">
  <img src="../../assets/characters/pandects.png" width="1200">
</p>

# Pandects

## Frontier

Pandects owns its own executable-law frontier, not Hexaemeron's delivery or
Solidity frontier. Its version, held target, next job, and maturity
state live in [EVOLUTION.md](EVOLUTION.md). Do not recommend or run
another frontier pass after that ledger becomes mature.

<!-- marketplace-context:start -->
## Where this sits

Pandects supplies executable credit laws, each paired with a deliberately broken specimen it is proved to catch and a replayable counterexample.

**Current frontier.** The search-record runner records only the Foundry campaign, so Echidna and Medusa results survive as audit prose rather than as records.
<!-- marketplace-context:end -->

Fizz or another engine can search these laws, Janus can apply the relevant
ones around a hook transition, and Hermes must preserve them when changing gas.
Pandects states and tests the law; it does not generate a target-specific fuzz
harness, audit the whole protocol, or turn one bounded campaign into security
sign-off.

A fuzzer searches a state space. It cannot decide which economic facts must
survive that search. Generic token property libraries cover balances, approvals
and round trips; credit adds time, accrual, queues, changing terms,
delinquency, partial repayment and claims that are neither liquid nor reducible
to a token balance. Every audit rediscovers those facts in prose, implements a
subset in a local harness, and the harness dies with the engagement.

This is the corpus that survives it.

`$SKILL_DIR` is the directory holding this file. The tool lives at
`$SKILL_DIR/../../scripts/pandects.py`; resolve it from where you loaded this
skill.

## Day to day

**Security and audit.** A credit protocol arrives and the invariants have to be
worked out before anything can be fuzzed. The corpus states them, says which
accounting model each one assumes, and ships the broken contract each is proven
to catch, so a law that holds against your target is a law you can see working.

**Developers.** A change touches accrual or the withdrawal queue and the
question is what it might have broken. Point the corpus at the build and read
which laws stopped holding, with the quantities that were compared.

## What a law is

Six parts. Anything with fewer is not a law, and the checker refuses it:

1. **It executes.** A Solidity component, not a sentence.
2. **It catches something.** A deliberately broken contract it is proven to
   fail against. A law that has never failed may be a tautology; a property
   asserting `seen() >= 0` survives a campaign of five hundred calls without
   complaint, and nothing in that run distinguishes it from a real law.
3. **It has been reduced.** A minimal counterexample, replayable without a
   fuzzer.
4. **It says where it applies.** The accounting model, the assumptions and the
   observables it requires.
5. **Its bounds are justified.** Exact, or a tolerance naming the arithmetic
   that produces it. An epsilon chosen because it made a test pass is refused.
6. **It judges rather than reverts.** A law returns `(bool held, string
   detail)`.

That last one is the decision worth knowing about. A campaign runs with
`fail_on_revert = false`, because a credit system reverts constantly and
correctly. Under that setting a revert carries no verdict, so a law using
`require` to mean "violated" reports nothing and is counted as silence. Silence
read as assent is what this exists to prevent.

## Two shapes

Conservation is a fact about one state, so a `Law` reads one target. Accrual is
not: debt falling without payment cannot be violated by any single state,
because the violation is in the transition. A `PairLaw` judges two
`Observation`s instead, each a snapshot of everything a target reports.

Three pair laws compare a system with its own past. One compares two systems
started identically and advanced over the same span by different routes, which
is the only way to see interest compounding when it should not. A law says
which kind of pair it means in its applicability, and handed one it cannot
judge it either holds or refuses on a single rule: a pair that spans real time
is a state of the world, and a pair nobody could have meant is a mistake by
whoever built it.

## The commands

```bash
python3 scripts/pandects.py laws
python3 scripts/pandects.py check
python3 scripts/pandects.py run --out search-record.json
python3 scripts/pandects.py render
```

`laws` lists the catalogue with each law's applicability. `check` refuses a law
missing any of its six parts, naming the part rather than the file. `run`
searches and writes down how it searched. `render` writes `docs/catalogue.md`
out of the catalogue, which is the only thing that should ever write it.

Exit codes: 0 success, 1 a check failed, 2 usage or validation error.

```bash
forge test
```

runs every law against every specimen and asserts the diagonal: each law fails
the specimen written for it and holds against the others. The corpus takes no
external Solidity dependency: there is no `lib/`, no submodule and nothing to
fetch.

The catalogue holds ten laws in three families. Conservation: value is
conserved across held assets, debt, claims and fees; assets reserved never
exceed the claims recorded; and reserved plus borrowable never exceed what is
held. Accrual: debt falls only against assets arriving, rises at rest only
against assets leaving, and the same span costs the same however it is cut up.
Withdrawal claims: a recorded claim is never written down smaller, nobody is
paid ahead of somebody who has waited longer, and what a system declares
payable it has set aside.

Eight are exact. The ninth carries the corpus's only tolerance, and the bound
is derived rather than chosen: linear accrual on principal truncates once per
step, so `n` small steps differ from one long step by at most `n - 1` units.

To point another engine at it, `src/campaigns/Specimens.sol` carries a harness
per specimen declaring both `echidna_` and `property_` prefixes, since Echidna
looks for the first and Medusa defaults to the second. Every entry point
snapshots the system on the way in, which is what lets a pair law read a past.
`explain()` returns each law's reason for the current state, so a failing
sequence gives up its reason rather than making somebody derive it from a call
trace.

One harness passes everything and the contract underneath it is broken.
`CompoundsPerStepCampaign` cannot see its own defect, because path independence
compares two systems advanced by different routes and a campaign drives one
along one route. It is the plainest illustration here of what a clean campaign
is worth on its own.

## Pointing it at a protocol

`adapters/` is where the corpus meets somebody else's system. Two shapes, and
the difference is a limit rather than a convenience.

`CorpusObserver` holds any address and offers the five one-state laws. Nothing
routes calls through it, so it offers no pair law: one that never sees a call
has no past to compare with, and would report holding forever.

`CorpusDriver` takes the calls. Extend it, write the protocol's entry points,
put `records` on every one that changes state, and the three succession laws
run as well. Nothing catches a forgotten `records` -- it looks like three laws
holding quietly -- so `recordedCalls` is public and `successionExercised` reads
it. Zero recorded calls means those laws searched nothing, whatever they
reported.

Path independence is in neither, because it compares two systems and an adapter
fronts one. `PathIndependenceProbe` takes both.

## Saying how it was searched

A campaign result without its settings is an anecdote, which is the same
refusal the corpus already makes of a tolerance that does not name its
arithmetic. `run` writes a record naming the engine, the argv, the determinism
class, the configuration read out of `foundry.toml` rather than restated, the
sequence length and a digest of the corpus searched. It is shaped as an
`ariadne` command entry, so a result drops into a release statement without
translation.

An engine that did not run is absent from the record, not present and empty.
What nobody could read is absent rather than null. And a campaign killed by the
timeout is neither passed nor failed: it ran, searched less than it was asked
to, and says so.

## What a law may read

`ICreditObservables`. It names economic roles: the asset, total assets held,
total debt, total lender claims, reserved and borrowable assets, accrued fees,
and the time the observation describes. A target implements it, or a thin
adapter does, and that adapter is the only place a protocol's own names appear.

A system with a withdrawal queue also implements
`IWithdrawalQueueObservables`: the claim count, each claim's owed and paid
amounts, and the bound through which the system declares claims payable. Kept
separate because a system with no queue would implement three members and mean
none of them, and an observable that means nothing reports zero, which reads
like an answer. A target that lacks it reverts on the read, and a revert is no
verdict rather than a false one.

This is enforced rather than requested. A property written against one
protocol's function names is a property about one codebase, and the corpus
exists because the same economic facts hold across codebases that share nothing
else.

## Pointed at a real design

`integrations/wildcat/` is the corpus against a codebase it was not written
for: a reduced model of a Wildcat market with batched withdrawals, a reserve
the borrower may not touch, delinquency and penalty accrual.

Six laws apply flatly. Three do not, and the three are what the integration is
for.

`queue-order-preserved` applies at batch granularity and says nothing per
lender, because a batch is paid pro rata. `path-independent` holds while the
market is solvent and stops once penalty accrual runs, because the grace timer
advances when the market is poked. And `recorded-claim-never-shrinks` does not
hold over a batch that is still open: a batch accumulates while open, so the
amount owed on it rises, and the law says a recorded claim keeps its amount.

That third one was found by Echidna against the shipped adapter, after the
applicability notes had already claimed the law held. Reading found two
conditions; running the corpus against a real design found the third, in a
document that had already got it wrong.

None of the three is a yes or a no.
`integrations/wildcat/APPLICABILITY.md` carries all of them with their reasons.

## The documents

`docs/catalogue.md` renders every law for a reader, and it is a rendering
rather than a second source: `pandects render` writes it, and a test compares
the committed bytes with what the renderer produces. `docs/writing-a-law.md`
has the six parts in the order somebody adding a law meets them.
`docs/applicability.md` states the rules once -- what a law may read, the two
shapes, what a pair law does with a pair it cannot judge, and what a revert
means.

## What this never does

- Replace an engine. Echidna, Medusa and Foundry search; the corpus says what
  to look for.
- Generate a harness for one repository. That is `fizz`, which can select and
  adapt these laws and stays useful where no public law describes the protocol.
- Report a campaign under an engine that did not run. A result carries its
  engine, configuration, seed, sequence length and corpus digest, or it is an
  anecdote.
- Present Wildcat-shaped law as universal law. Every law states the accounting
  model it assumes, and a law with no applicability contract is not in the
  corpus.
- Decide whether a law is true. The checker decides whether something is a law
  at all, which is a lower bar and the one worth enforcing mechanically.

## Promise Machine contract

### pandects-law-contract

- Promise: A successful `pandects.py check` establishes that every discovered catalogue entry has the six required executable-law parts.
- Evidence: The law registry, Solidity component and broken-specimen references, reduced counterexample, applicability, justified bound, judgement interface and zero-exit checker diagnostics.
- Evidence classes: checked
- Boundary: The check establishes that an entry has the law contract; it does not establish that the law is true, applies to a target or catches its specimen.
- Authorises: Treating the entry as structurally eligible for the separate specimen, rendering and campaign checks.
- Consequence: 1
- Refuses: Admitting an entry missing executable judgement, a broken specimen, reduction, applicability, observables or justified bounds.
- Recovery: Supply the named missing part and rerun `check` before any dependent operation.
- Exceptions: none

### pandects-catalogue-render

- Promise: A successful `pandects.py render` followed by the catalogue-byte regression check reproduces `docs/catalogue.md` from the checked authored registry.
- Evidence: The checked law registry, deterministic render output, committed catalogue bytes and passing byte-comparison test.
- Evidence classes: checked, recomputed
- Boundary: Rendering establishes agreement with the registry; it does not establish law truth, applicability to a target or specimen coverage.
- Authorises: Publication of the regenerated catalogue as a derived view of the checked law records.
- Consequence: 1
- Refuses: Hand-editing the rendered catalogue, publishing drifted bytes or using rendering as evidence that a law holds.
- Recovery: Correct the authored registry, rerun `check` and `render`, then rerun the exact catalogue comparison.
- Exceptions: none

### pandects-broken-specimen

- Promise: A green `forge test` establishes the shipped diagonal relation: each law fails its named broken specimen and holds against the other shipped specimens under the deterministic harness.
- Evidence: The exact law and specimen Solidity, reduced replay, compiled harness and complete passing Foundry test result.
- Evidence classes: checked, recomputed
- Boundary: The diagonal establishes the named fixture relation only; it is not a formal proof, a verdict on another protocol or evidence that a search engine explored a target.
- Authorises: Presenting the law as demonstrated to catch its shipped defect and using the specimen as a regression oracle.
- Consequence: 1
- Refuses: Calling a law proven to catch a defect when its diagonal test did not run, failed or was replaced by a tautological campaign result.
- Recovery: Reduce the failing relation, correct the law or specimen without weakening the oracle and rerun the full diagonal.
- Exceptions: none

### pandects-search-record

- Promise: A successful `pandects.py run` records the engine that actually ran, its argv, configuration, determinism, sequence length, disposition and corpus digest.
- Evidence: The executed engine command, captured configuration, search output, timeout or result status and generated search-record JSON.
- Evidence classes: measured, recorded, checked
- Boundary: The record establishes what the named campaign searched and reported; it does not decide law truth, cover an absent engine, prove universal safety or make a non-applicable law fit a target.
- Authorises: Reporting the bounded campaign result or attaching its command record to an Ariadne release statement.
- Consequence: 3
- Refuses: Inventing an engine result, treating timeout as pass or fail, hiding zero succession calls, or presenting target-specific applicability as universal credit law.
- Recovery: Correct the adapter or applicability record, run the intended engine with explicit settings and preserve a new search record.
- Exceptions: none
