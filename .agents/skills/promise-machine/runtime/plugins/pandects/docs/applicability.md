# Applicability

<!-- marketplace-context:start -->
> **Marketplace context: Pandects.** Pandects supplies executable laws for credit contracts, each paired with a deliberately broken specimen and a reduced counterexample. Use Hexaemeron Fizz to generate a protocol-specific fuzz harness and Ariadne to carry the resulting campaign evidence with a release. **Current frontier:** The search-record runner records only the Foundry campaign, so Echidna and Medusa results survive as audit prose rather than as records.
<!-- marketplace-context:end -->

The rules a law obeys, stated once here rather than nine times in nine
docstrings.

## What a law may read

`ICreditObservables` names economic roles: the asset, total assets held, total
debt, total lender claims, reserved and borrowable assets, accrued fees, and
the time the observation describes. A target implements it, or a thin adapter
does, and that adapter is the only place a protocol's own names appear.

`IWithdrawalQueueObservables` adds the claim count, each claim's owed and paid
amounts, and the bound through which the system declares claims payable. It is
separate because a system with no queue would implement three members and mean
none of them, and an observable that means nothing is worse than an absent one:
it reports zero, and zero reads like an answer.

A law that named a protocol's own functions would be a law about one codebase.
The corpus exists because the same economic facts hold across codebases that
share nothing else.

## The two shapes

A `Law` judges one observed state. A `PairLaw` judges two observations.

Nothing else. The shape follows from the fact: if a single state can violate
it, it is a `Law`, and if the violation lives in a transition, it is a
`PairLaw`.

Three pair laws compare a system with its own past. One compares two systems
advanced over the same span by different routes. A law says which in its
applicability, because reading one the wrong way round is the mistake available
to everyone.

## A pair a law cannot judge

Ask whose mistake the pair is.

A pair that spans real time, or that shows a system somewhere the law says
nothing about, is a state of the world. Hold, and say why.

A pair nobody could have meant -- two runs that never reached the same moment,
a queue law handed observations with no queue in them -- is a mistake by
whoever built it. Refuse, and say why. Holding there would report a comparison
nobody made.

## What a revert means

Nothing. Not a violation and not a pass.

A campaign runs with `fail_on_revert = false`, because a credit system reverts
constantly and correctly: a withdrawal past the queue, a borrow past the
reserve, a repayment of more than is owed. Under that setting a revert carries
no verdict.

So a law returns `false` to mean violated and never reverts to mean it. The
converse is a limit rather than a guarantee: if the target reverts on a read,
the law reverts with it, the state could not be observed, and the harness
counts a revert. What an unobservable state means is the adapter's decision.

## What a bound means

Exact, or a tolerance naming the arithmetic that produces it.

The distinction is not pedantry. An epsilon chosen because it made a test pass
will absorb the next real defect that lands under it, and nobody will be able
to say whether it should have.

## Applicability is a contract in two directions

A law's applicability says what a design must provide for the law to mean
anything. That is the direction it is usually read.

The other direction is what `integrations/wildcat/` is for. Pointed at a real
design, the same contract has to say which laws that design supports and under
what conditions, and two of the answers there are not yes or no.

`claims/queue-order-preserved/v1` is true of a Wildcat market at batch
granularity and says nothing per lender, because a batch is paid pro rata and
no lender in one is ahead of another. The law is right; the unit is the whole
finding, and a corpus that let the two readings blur would be quietly wrong
about somebody's protocol.

`accrual/path-independent/v1` holds for a solvent market and stops holding once
penalty accrual is running, because the grace timer advances when the market is
poked. That is a condition, not a verdict, and the applicability note carries
it.

A law with no applicability contract is not in the corpus. A law whose contract
says only "yes" has not met a real design.
