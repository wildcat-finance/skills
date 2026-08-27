# Study: a law that stops a fee eating queued withdrawals

Topic: `Pandects: withdrawal-batch-fee law`. Base: `loop/2026-08-18-kronos` at
`9ad3c59`.

## Problem statement

Pandects ships nine laws. None of them notices when a fee takes value that has
already been promised to a lender who asked to leave.

That is not a reading of the code. It is a state, reached in five calls against
the plugin's own Wildcat model:

| | claims | owed on open batches | reserved | held | fees |
| --- | --- | --- | --- | --- | --- |
| deposit 1000, borrow 1000, request 1000 | 1000 | 1000 | 200 | 200 | 0 |
| then `accrueFee` | **200** | **1000** | 200 | 200 | 800 |

The market is delinquent, holds 200 because the borrow left the twenty per cent
required reserve, and owes 1000 on one open batch. The fee takes 800 of it. The
protocol has taken four fifths of what a departing lender is owed and the corpus
has no opinion.

Every law was executed against that pair rather than argued about. The five
single-state laws each return `held = true` on the second row.
`claims/recorded-claim-never-shrinks/v1` holds, because a fee touches neither
`owed` nor `paid` on any batch. Both accrual pair laws hold, because they read
debt and a fee does not move it. `accrual/path-independent/v1` also returns held,
and that verdict carries no weight either way: it compares two systems advanced
over the same span by different routes, so a single system's before and after is
not the comparison it describes.

This is a finding about the reduced model in `integrations/wildcat/`, and about
the corpus being silent on the state it reaches. Nothing here is a claim about the
deployed Wildcat market contracts. They are not read, and this study establishes
nothing either way about how they account for fees.

The sound reference does the same thing on a shorter path: `deposit(100)`,
`borrow(50)`, `reserve(100)`, `reserve(100)`, `accrueFee` lands on claims 50
against 100 owed, with all five single-state laws and all four pair laws holding,
again by execution.

**Working prototype.** A tenth law, `claims/pooled-claims-cover-open-batches/v1`,
carrying all six parts, and both models corrected so they hold it. It works when
this runs offline and green:

```bash
forge test                        # every law against every specimen
python3 scripts/pandects.py laws  # ten laws with their applicability
python3 scripts/pandects.py check # the six parts, enforced
```

with the new specimen caught by the new law and by no other, the diagonals in
`test/Corpus.t.sol` and `test/Pairs.t.sol` still exact, and the counterexample
replaying with no fuzzer. The demo is not that the law passes. It is that the
specimen written to break it does break it, and that nothing else in the corpus
fires on the same state.

**Baseline, measured on `9ad3c59` before any change.** `forge test`: 72 passed,
0 failed, across 10 suites. `python3 -m unittest discover -s plugins/pandects/tests
-t plugins/pandects`: 106 passed. Repository suite `-s tests`: 20 passed.
`pandects.py check`: nine laws, every part present. `forge 1.7.1`, `solc 0.8.28`,
Echidna 2.3.3, Medusa 1.5.1, Slither 0.11.6, crytic-compile 0.4.2, all present
locally.

## Why nine laws miss it

Three come close. Each misses for a different reason, and separating them matters,
because two of those reasons constrain the design.

`conservation/value-conserved/v1` cannot see it by construction. A fee moves value
from claims to fees, both on the right-hand side of the equality, so the sums agree
before and after. Conservation says value went somewhere, not that it was allowed
to go there.

`conservation/reserves-backed-by-claims/v1` bounds reserved from above by pooled
claims. `claims/reserves-cover-payable/v1` bounds reserved from below by what is
outstanding on the payable prefix. Composed, they give `claims >= outstanding on
the payable prefix`. That is strictly weaker than what is needed, and the gap is
exactly where the money goes: `payableThrough` is derived in both models from what
has actually been set aside, so an illiquid system declares fewer batches payable
rather than more, and the prefix shrinks to match the reserves while the batches
behind it stay owed. In the table above the payable prefix covers 200 and the
other 800 sits outside every existing bound.

`claims/recorded-claim-never-shrinks/v1` is the interesting one, because its
docstring has already ruled out the pooled total: claims fall legitimately every
time a fee is taken, so a *pair* law over `totalLenderClaims` either admits fees
and restates conservation, or refuses them and fails against every correct system.
That argument is correct and it is about pair laws. It says nothing about a
single-state lower bound, and the frontier names precisely the bound it leaves
open.

## Prior art

**In this plugin.** The five laws above, `src/Law.sol` for the returning shape,
`src/IWithdrawalQueueObservables.sol` for the queue extension, and
`specimens/Sound.sol` as the reference each specimen inherits. `docs/writing-a-law.md`
fixes the seven-step method this study follows, including the instruction to check a
statement against the reference before writing Solidity, which is what caught the
first draft below.

Two comments already in the tree describe the defect without a law behind them.
`Sound.accrueFee` says that value earmarked against a recorded withdrawal has been
promised to a lender who asked for it, and that a protocol taking its fee out of it
is taking money it already owed. `WildcatMarketModel.delinquent` says that
`reserved` and `unpaidBatches` differ exactly when the market is in trouble. Put
together those two comments are the bug: the fee is capped against `reserved`, and
`reserved` falls below what is owed precisely when the market is delinquent.

**In this repository.** `plugins/ariadne` carries the search record for any campaign
this produces. `tests/test_marketplace_prose.py` gates the prose reconciliation the
held job asks for, so that half of the job is machine-checked rather than eyeballed.

The frontier is also not a fresh idea. `plugins/pandects/audit/AUDIT.md` closes its
last round carrying, among its leads not pursued, the fee that can drop pooled
claims below what is owed on open batches. The defect was seen during the original
delivery's audit loop, judged not worth another round then, and written down instead
of dropped. This run is that lead being taken up.

**Outside.** `crytic/properties` covers ERC-20 and ERC-4626 and has no withdrawal
queue, so there is no upstream property to adopt or contribute back to here.
The a16z and OpenZeppelin ERC-4626 suites bound redemption against shares rather
than against a recorded queue, which is a different fact about a different design.

## Constraints and non-goals

**Starting point.** `loop/2026-08-18-kronos` at `9ad3c59`. Every pull request in
this run targets that branch and not `main`.

**Toolchain.** Solidity 0.8.28 under `forge 1.7.1`, no external Solidity
dependency. Python 3.9 through 3.13, standard library only. Both fixed by the
existing CI matrix in `.github/workflows/pandects.yml`.

**No new observable.** `ICreditObservables` does not grow. Everything the law needs
is already readable through it and the queue extension, and adding a fee-history
observable for one law would put a quantity in the interface that only one law can
use.

**Ruled out.** Per-lender accounting inside a batch, which the Wildcat integration
already declares out of model. The seven deferred property families. The
"claim paid beyond what it was owed" defect that `reserves-cover-payable` names and
deliberately leaves uncovered; folding it in here would make this law broader than
its statement, which is what the diagonal exists to fail.

## Design options

**A. A single-state `Law`: pooled lender claims cover everything still owed on open
withdrawal batches.** `totalLenderClaims() >= sum over recorded claims of
(owed - paid)`, exact, needing the queue extension. **Chosen.** A single state is
enough to see the violation -- claims 200 against 1000 owed is already evidence, and
no history is needed to say so -- which is the corpus's own test for which shape a
law takes. Of the four it is also the cheapest to comprehend: a sum and a
comparison, the same shape as `reserves-cover-payable` with two quantities
changed.

**B. A `PairLaw` over the fall in pooled claims.** Bound the fall by payments
recorded against the queue plus whatever was unqueued at the earlier observation.
Rejected. It answers a question nobody needs: what is wrong is the state, not the
transition into it, and a pair law would hold on a system that was already in the
bad state when first observed. It also inherits the difficulty
`recorded-claim-never-shrinks` documents, and it would need the earlier observation
to be trustworthy about a queue the harness may not have read.

**C. Narrow the bound to the payable prefix.** Rejected, and this is the option that
looks right and is not. `claims >= outstanding on the payable prefix` is implied by
the conjunction of two shipped laws, as shown above. A law implied by laws already
in the corpus has no specimen of its own: anything breaking it breaks one of them
first, and the diagonal fails. Being unable to write a specimen for it is the proof
that it is not a law.

**D. Add a fee-history observable and name the fee directly.** Rejected. It widens
the interface for one law, and it is unnecessary: the state after the fee is
evidence enough, which is what option A uses.

## The first draft was false of the reference

`docs/writing-a-law.md` says to check the statement against the sound reference
before writing any Solidity, on the grounds that two accrual laws were written,
checked, and found false of a correct system. The same thing happened here, and it
changed the work.

The statement in option A, tested against `Sound` as shipped, fails on a path that
has nothing to do with fees. `deposit(100)`, `reserve(100)`, `reserve(100)` leaves
claims at 100 and the queue owed 200, because `Sound.reserve` caps a new claim at
`min(claims, held)` rather than against the pooled claim not already queued. The
same pool is queued twice.

So the law is not the whole job. Both models need correcting before either can hold
it, and the corrections are the interesting part of the change:

1. **`Sound.reserve`** must cap a new claim against the pooled claim not already
   queued. The Wildcat model already does this correctly in `requestWithdrawal`,
   which caps at `claims - unpaidBatches()`, so the fix is to bring the reference
   into line with the integration rather than to invent anything.
2. **`Sound.accrueFee` and `WildcatMarketModel.accrueFee`** must cap the fee at the
   pooled claim not already queued, rather than at `claims - reserved`. `reserved`
   is `min(outstanding, claims, held)`, so it equals what is outstanding only while
   the system holds enough to earmark the whole queue. In the illiquid case -- the
   undercollateralised case the corpus exists for -- it sits below, and the cap
   leaks by exactly the difference.

Both corrections are tightenings: they shrink the set of reachable states and
neither weakens an existing law. `reserved <= claims` survives because the new cap
is at or below the old one.

The consequence worth stating plainly: **the specimen for this law is the current
behaviour of the reference and of the shipped Wildcat model.** The specimen
reinstates as its single deliberate defect what both files do today.

## The build

**The law.** `src/laws/PooledClaimsCoverOpenBatches.sol`, id
`claims/pooled-claims-cover-open-batches/v1`, family `claims`, exact. Reads the
queue by casting the target, as its two siblings do. Sums unchecked with the
overflow reported as a violation, because a revert carries no verdict under
`fail_on_revert = false`. Traversal is unbounded and the applicability says so, in
the same words the two sibling queue laws already use.

**The specimen.** `specimens/FeeFromQueued.sol`, inheriting `Sound`, overriding
`accrueFee` alone to restore the cap at `claims - reserved`. One function, so the
defect is the diff. It must break this law and no other, and the state above is the
evidence that it does: five single-state laws holding, debt untouched, each batch's
`owed` and `paid` untouched. Reachable in five calls, which is well inside a
fuzzer's depth.

**The counterexample.** A deterministic replay added to
`test/counterexamples/Claims.t.sol`, asserting the intermediate quantities and not
only the verdict, then checked against Echidna to see whether it shrinks smaller.

**The catalogue.** An entry in `catalogue/pandects.json` and a rendering in
`docs/catalogue.md`. `pandects.py check` refuses either one alone.

**The campaign.** `src/campaigns/Specimens.sol` extended so the new specimen is
reachable under both the `echidna_` and `property_` prefixes, then both engines run.
Echidna reports its seed and Medusa does not, so a Medusa record states the engine,
configuration digest, sequence length and corpus digest and says the seed is
unavailable.

**The prose.** Twelve files carry the frontier sentence and around ten places claim
"nine laws". `tests/test_marketplace_prose.py` gates the marketplace-context blocks.
`integrations/wildcat/APPLICABILITY.md` needs the most care: it opens on "Nine laws.
Six apply without qualification. Three do not", and the new law arrives as one the
model holds only after the fee cap is corrected, which is a fact about the model and
belongs in that document. The audit log's historical rounds are records and stay as
written; only its marketplace-context block is mutable.

## Risk register seed

What the audit loop should look hardest at, in the order they are most likely to
bite:

1. **The reference corrections changing reachable states under existing tests.**
   Around twenty call sites drive `reserve` and `accrueFee`, including repeated
   `reserve(1); reserve(1)` pairs in `test/Corpus.t.sol`, `test/Adapters.t.sol` and
   the counterexamples. A tighter cap can silently turn one of those into a no-op
   and leave a test asserting a state it no longer reaches. Every existing
   counterexample must still replay for the reason it was written.
2. **A specimen that breaks two laws.** The diagonal is the check, and the state
   above says the specimen is clean, but it says so at one point. The specimen has
   to break only this law across everything the campaign reaches, not only at the
   state derived by hand.
3. **`Sound` no longer reaching states other laws need.** The corrections remove the
   double-queue path. If any existing specimen depended on it to exhibit its own
   defect, that specimen stops proving its law and the loss is invisible: the test
   still passes.
4. **The law reverting instead of judging.** Arithmetic in the sum, a read past the
   end of the queue, an underflow on `owed - paid` where a claim was paid beyond
   what it was owed. That last case is real: `reserves-cover-payable` skips such
   claims deliberately, and this law must make the same choice explicitly rather
   than subtract and revert.
5. **Overflow in the sum.** Reported as a violation, never reverted, for the reason
   `ValueConserved` gives.
6. **A tolerance appearing.** There is none. The law is a sum and a comparison, and
   any epsilon that shows up is a defect being hidden.
7. **The Wildcat applicability claim.** The document will say the model holds ten
   laws. It must say so because the fee cap was corrected, not by quietly counting
   the new law among the six that always held.
8. **Unbounded traversal.** The same limit the sibling queue laws carry, stated in
   the applicability and not worked around in the law.
9. **Prose drifting from the catalogue.** A law count in one document and not
   another is the failure `test_marketplace_prose.py` exists to catch; the ten-vs-nine
   claims sit outside the gated blocks and need reading by hand.

## Glossary seeds

- **Open batch.** A recorded withdrawal claim still owed something: `paid < owed`.
- **Outstanding on the queue.** The sum of `owed - paid` over every recorded claim.
- **Pooled lender claim.** What `totalLenderClaims()` reports: everything lenders
  may eventually withdraw, including amounts already queued and not yet paid.
- **Unqueued claim.** The part of the pooled claim not owed on any open batch, and
  the only part a fee may take.
- **Payable prefix.** The claims at indices below `payableThrough`, which the system
  declares it can settle now.
- **Earmark.** What a model sets aside against the queue, bounded by what it holds,
  and therefore below what is outstanding whenever it is illiquid.
- **Delinquent.** A market holding less than what its open batches are owed plus its
  required reserve.

## Recorded readings

Where the held job left a choice, this is the reading taken.

- **"Open withdrawal batches" means every recorded claim still owed something**,
  not the payable prefix. The prefix reading is option C, and it is not a law.
- **"Fees cannot reduce" is enforced as a state bound rather than a fee bound.** The
  law never mentions fees. A fee is what puts a system into the state, and the state
  is what is checkable through the observables; a law that named the fee would need
  the harness to tell it a fee happened, and a law that trusts the harness is a law
  about the harness.
- **Both models get corrected in this run.** The alternative was to add the law,
  qualify the Wildcat applicability to say the model does not hold it, and leave the
  reference broken. That fails on its own terms: the reference must hold every law,
  or no specimen means anything.
- **The specimen restores the reference's current fee cap.** It is the honest
  specimen, it is one line of diff, and it is a defect a real system has had.

## Sources

- `plugins/pandects/docs/design.md` and `docs/writing-a-law.md`, for the method and
  the six parts.
- `plugins/pandects/src/laws/*.sol` and `catalogue/pandects.json`, for the nine
  shipped laws and the entry shape.
- `plugins/pandects/specimens/Sound.sol` and
  `integrations/wildcat/WildcatMarketModel.sol`, for the two models corrected here.
- `plugins/pandects/integrations/wildcat/APPLICABILITY.md`, for the six-and-three
  split this run changes.
- `tests/test_marketplace_prose.py` and `.github/workflows/pandects.yml`, for what
  is gated and what CI runs.
- `crytic/properties`, `a16z/erc4626-tests`, at `github.com/`, checked for a
  withdrawal-queue property to adopt. There is none.
- Local toolchain, versions recorded in the baseline above.
