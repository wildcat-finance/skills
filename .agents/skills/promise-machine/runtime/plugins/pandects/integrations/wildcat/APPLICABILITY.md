# The corpus against a Wildcat market

<!-- marketplace-context:start -->
> **Marketplace context: Pandects.** Pandects supplies executable laws for credit contracts, each paired with a deliberately broken specimen and a reduced counterexample. Use Hexaemeron Fizz to generate a protocol-specific fuzz harness and Ariadne to carry the resulting campaign evidence with a release. **Current frontier:** The search-record runner records only the Foundry campaign, so Echidna and Medusa results survive as audit prose rather than as records.
<!-- marketplace-context:end -->

`WildcatMarketModel.sol` is a reduced model, not a reimplementation. It keeps
the shape the corpus has to survive -- withdrawals pooled into batches, a
reserve the borrower may not touch, delinquency, and a penalty rate on top of
the base one -- and nothing in it should be mistaken for the market contracts.

Ten laws. Seven apply without qualification, and one of those seven did not
until this model was corrected. Three do not, and those three are why this
integration exists: until now, applicability described what a law needs, and
here it has to describe what a design does and does not promise.

One of the three was found by Echidna rather than by reading, against the
shipped adapter, after this document had already claimed the law held. That is
worth saying plainly, because it is the whole argument for pointing a corpus at
a real design instead of at contracts written to break it.

## The seven

| Law | Holds | Because |
| --- | --- | --- |
| `conservation/value-conserved/v1` | yes | Every operation moves value between two sides, including accrual, which raises debt and claims together |
| `conservation/reserves-backed-by-claims/v1` | yes | A market cannot earmark more than lenders are owed |
| `conservation/held-assets-partitioned/v1` | yes | Borrowable liquidity is derived, and the required reserve comes out of it before the borrower is offered anything |
| `claims/reserves-cover-payable/v1` | yes | Payability is derived from what has actually been set aside, so a delinquent market declares fewer batches payable rather than lying about them |
| `accrual/debt-falls-only-against-payment/v1` | yes | Debt falls only in `repay`, against assets arriving |
| `accrual/no-accrual-at-rest/v1` | yes | Interest accrues in `advance` and nowhere else, and borrowing removes from held assets what it adds to debt |
| `claims/pooled-claims-cover-open-batches/v1` | yes, once corrected | The fee is capped against what the open batches are owed; it was capped against the earmark, and that let it reach value already promised. See below |

## The fee cap, and the law that found it

`claims/pooled-claims-cover-open-batches/v1` holds, and it did not hold when the
law arrived. This section is here because the correction is the interesting part,
not the verdict.

The model capped a protocol fee against `reserved()`, the assets set aside
against the queue. That reads as careful and is not, because an earmark cannot
exceed what the market holds. A solvent market earmarks its whole queue and the
two figures agree; a market short of liquidity earmarks what it has, the figures
part company, and the gap between them is fee the market may take out of value
already promised to lenders waiting in a batch. `delinquent` says as much in its
own comment: those two quantities differ exactly when the market is in trouble.
Nobody had joined that observation to the fee cap.

A market holding 200 against one batch owed 1000 permitted a fee of 800. Every
one of the other nine laws held on the state that left behind: the books balance,
because the value moved from claims to fees; reserves stay within claims; the
partition holds; payability is still derived from the reserves, so the market
never declared more payable than it had; debt never moved, so neither accrual law
had anything to say; and each batch kept its own recorded amount, so nothing was
written down. Only the pool behind those amounts had shrunk.

The cap now measures against what the open batches are owed. On the same market
the permitted fee is nothing, because nothing is unrequested. That is the law
working, and it is worth being plain that the law was written after the state was
found rather than the other way round.

This is a correction to a reduced model. What the deployed market contracts do
about fees while a batch is outstanding is not read here and is not established
either way by this document.

## Batch granularity, and what the ordering law means here

`claims/queue-order-preserved/v1` holds, and reading it as a per-lender promise
would be wrong.

A Wildcat market pools every withdrawal request made in the same cycle into one
batch, and pays a batch pro rata. So no lender inside a batch is ahead of any
other, and none is paid in full while another waits. Batches are paid oldest
first.

The law says no claim is paid while an older claim is still owed something. At
batch granularity that is exactly what the design guarantees, and the extension
here exposes batches rather than lenders for that reason. At lender granularity
it would be false, and trivially: a pro-rata payment leaves every lender in the
batch partly paid.

Neither reading is wrong about the design. One of them is wrong about the unit,
and a corpus that let the two blur would be quietly wrong about somebody's
protocol. `test_a_batch_paid_pro_rata_does_not_break_the_ordering` is the
assertion that the pooled case does not read as a jump.

## An open batch is not yet a recorded claim

`claims/recorded-claim-never-shrinks/v1` does not hold over an open batch, and
does hold over a closed one.

The law says a recorded claim keeps its owed amount. A Wildcat batch
accumulates while it is open: a second request in the same cycle joins the batch
and the amount owed on it rises. Echidna found that against
`WildcatMarketCampaign` within a few hundred calls, and the property is expected
to fail there.

Neither side is wrong. For a queue of individual claims, an amount that changes
after the fact is precisely the defect the law was written for -- a lender was
given a number and the number moved. For a batched design, an open batch is not
a claim that has been recorded; it is a claim still being assembled. The law
starts applying when the batch closes, which happens as soon as anything is paid
out of it, and from that moment the amount is fixed.

`test_an_open_batch_grows_and_the_claim_law_refuses_it` and
`test_a_closed_batch_satisfies_the_claim_law` are the two halves, asserted
rather than described.

Whether the law should be relaxed to say a recorded claim is never written
*down* -- which would still catch the specimen it was built for, and would hold
over an open batch -- is a real question and not one this integration should
answer on its own. It is recorded as a lead in `audit/AUDIT.md`.

## Path independence, and the condition on it

`accrual/path-independent/v1` holds while the market is solvent and stops
holding once penalty accrual is running.

Base interest is linear on principal. It never accrues on interest already
accrued, so a span costs the same however it is cut up, to within the bound the
law derives.

The penalty is different. It runs only once the market has been delinquent for
longer than the grace period, and the grace timer advances when the market is
poked. A market that crosses into delinquency mid-span therefore owes a
different penalty depending on how often somebody updated it: advanced once
across a year from a fresh delinquency, it pays no penalty at all, because the
grace was unspent at the moment the charge was computed. Advanced in two halves,
it pays the penalty for the whole second half.

That is path dependence in the plain sense, and it is not a defect in the design
or in the law. It is a design the law does not describe once that rate is on.
`test_a_penalised_market_is_not_path_independent` watches it happen rather than
describing it, and `test_a_solvent_market_is_path_independent` holds the other
half.

## Delinquency arrives with the request

Worth stating because it is the part a reader coming from a simpler model gets
wrong. Borrowing cannot make a market delinquent: the required reserve is
subtracted before the borrower is offered anything. What makes a market
delinquent is a lender asking to leave a market whose liquidity has already gone
out of the door, and no amount of care at borrow time prevents that.

This is why the model bounds a withdrawal request by the lender's claims rather
than by what the market holds. A model that refused the request would have no
way to reach the situation the whole design is built around.

## What is not modelled

Per-lender accounting, so nothing here says anything about one lender's share of
a batch. The scaling index, so amounts are in the asset throughout. Market
expiry, borrower authorisation, the sentinel, and every access control. Each of
those matters to a market and none of them changes what the laws read.
