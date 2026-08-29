# Creating entries

<!-- marketplace-context:start -->
> **Marketplace context: Lemma.** Lemma turns Solidity compiler input or Markdown trees into validated, source-linked JSONL chunks, keeping quotation text separate from model and embedding text. It does not embed, index, retrieve or answer; Berean is the adjacent unbuilt release discipline for a grounded protocol agent. **Current frontier:** Callable-surface ABI validation does not independently check return types or state mutability.
<!-- marketplace-context:end -->

Creation is admin-only. The admin supplies an identifier and an amount, and the
call returns the fee charged.

## Before you start

Check that the identifier is unused and that the deployment is below capacity.
Both conditions revert rather than returning a status, so a failed simulation is
the cheapest way to find out.

## What the fee depends on

The fee is a proportion of the amount, rounded up. Changing the fee affects
subsequent creations only; entries already created are unaffected, because the
charged amount is computed once and not stored.
