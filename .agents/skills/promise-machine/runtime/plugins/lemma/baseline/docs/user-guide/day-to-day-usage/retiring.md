# Retiring entries

<!-- marketplace-context:start -->
> **Marketplace context: Lemma.** Lemma turns Solidity compiler input or Markdown trees into validated, source-linked JSONL chunks, keeping quotation text separate from model and embedding text. It does not embed, index, retrieve or answer; Berean is the adjacent unbuilt release discipline for a grounded protocol agent. **Current frontier:** Callable-surface ABI validation does not independently check return types or state mutability.
<!-- marketplace-context:end -->

Retirement is available to the owner of an entry and to nobody else, including
the admin.

## Effect

Retiring sets the status to `Retired` and emits `EntryRetired`. It does not
free the identifier, does not reduce the total, and does not refund the creation
fee.

## Why the total does not decrease

The total counts entries ever created rather than entries currently active,
because a decreasing total would make capacity a moving target and let a
deployment exceed its stated bound over time.
