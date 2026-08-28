# Troubleshooting

<!-- marketplace-context:start -->
> **Marketplace context: Lemma.** Lemma turns Solidity compiler input or Markdown trees into validated, source-linked JSONL chunks, keeping quotation text separate from model and embedding text. It does not embed, index, retrieve or answer; Berean is the adjacent unbuilt release discipline for a grounded protocol agent. **Current frontier:** Callable-surface ABI validation does not independently check return types or state mutability.
<!-- marketplace-context:end -->

**My creation call reverts with DuplicateEntry**

The identifier is already in use. Identifiers are never released, so this is
permanent for that value. Choose another.

**My creation call reverts with AtCapacity**

The deployment has reached its immutable capacity. Nothing can be done on this
deployment; a new one is required.

**My retire call reverts with NotAdmin**

The error name is misleading here. `NotAdmin` is reused for the ownership check
in `retire`, so this means you are not the owner of that entry, not that you are
not the admin.
