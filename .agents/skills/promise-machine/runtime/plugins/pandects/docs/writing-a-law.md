# Writing a law

<!-- marketplace-context:start -->
> **Marketplace context: Pandects.** Pandects supplies executable laws for credit contracts, each paired with a deliberately broken specimen and a reduced counterexample. Use Hexaemeron Fizz to generate a protocol-specific fuzz harness and Ariadne to carry the resulting campaign evidence with a release. **Current frontier:** The search-record runner records only the Foundry campaign, so Echidna and Medusa results survive as audit prose rather than as records.
<!-- marketplace-context:end -->

Six parts, in the order you meet them. A law with fewer is refused by
`python3 scripts/pandects.py check`, which names the missing part rather than
the file.

## 1. Decide what shape it is

Ask whether a single state can violate it.

Conservation can: the sums agree or they do not, and no history is needed. That
is a `Law`, and it reads one target.

Accrual cannot. Debt falling without payment is invisible in any one state,
however wrong that state is, because the violation is in the transition. That
is a `PairLaw`, and it judges two `Observation`s.

Three of the pair laws compare a system with its own past. One compares two
systems started identically and advanced over the same span by different
routes. Say which you mean in the applicability, because reading a law the
wrong way round is the mistake available to everybody who uses it.

## 2. State it in terms a law may read

`ICreditObservables`, and `IWithdrawalQueueObservables` if it needs a
withdrawal queue. Nothing else, ever.

This is where most first attempts fail, and the failure is not obvious. "Debt
never decreases between repayments" cannot be checked: nothing a target reports
says a repayment happened, so the law would need the harness to tell it, and a
law that trusts the harness is a law about the harness. The observable form is
that held assets rose by at least the fall, which is what a repayment looks
like from outside and what a write-off does not.

Check the statement against the sound reference before writing any Solidity.
Two laws in the accrual family were written, checked, and found false of a
correct system before a line of them existed.

## 3. Write the component

It returns `(bool held, string detail)` and never reverts to mean violated.

The reason is the harness rather than taste. A campaign runs with
`fail_on_revert = false`, because a credit system reverts constantly and
correctly. Under that setting a revert carries no verdict, so a law using
`require` to mean "violated" reports nothing and is counted as silence. The
checker greps for `require`, `assert` and `revert` in a component and refuses
it.

Sums go in an `unchecked` block with the overflow reported as a violation. In
0.8 an overflow reverts, and a law that overflowed would fall silent exactly
where the numbers went furthest wrong.

The detail is for the reader who finds the failure six months later. Name the
quantities that were compared.

## 4. Write the specimen

A contract that breaks this law and no other, inheriting from `Sound` so the
defect is the diff rather than a paragraph claiming there is one. Say
"deliberately broken" in it; the checker looks for those words, because a
broken credit contract that does not say so gets copied.

The one-law-only part is the work. A specimen that breaks two laws proves
neither, and the diagonal in `test/Corpus.t.sol` and `test/Pairs.t.sol` fails
when it happens. Getting there usually means finding the compensating move that
keeps every other law satisfied: the write-off specimen charges itself against
accrued fees, so conservation holds across the transition that loses a
borrower's debt.

## 5. Reduce the failure

A deterministic replay under `test/counterexamples/`, running with no fuzzer,
no seed and no engine. Derive it by hand, then check it against the engines --
two of the conservation counterexamples got smaller that way, because Echidna
shrank sequences that had been written at a hundred units down to one.

Assert the intermediate quantities, not just the verdict. A counterexample that
only asserts the law fires stops being evidence the moment somebody changes the
specimen.

## 6. Say where it applies, and what it costs

The applicability carries the accounting model, the assumptions and the
observables required. Write the assumptions that would make the law false if
they did not hold, not the ones that sound careful.

Bounds are `exact` or an object naming the arithmetic that produces the
tolerance. An epsilon chosen because it made a test pass is the thing being
refused. The corpus has one tolerance, and it reads: linear accrual on
principal truncates once per step, so `n` steps and one step over the same span
differ by at most `n - 1`.

## 7. File it

Add the entry to `catalogue/pandects.json` and the rendering to
`docs/catalogue.md`. A component in `src/laws/` that no entry claims is a
finding, and so is a document that names a law the catalogue does not have.

Then extend the campaign harness in `src/campaigns/Specimens.sol` so the
specimen is reachable by Echidna and Medusa under both prefixes, and run both.
