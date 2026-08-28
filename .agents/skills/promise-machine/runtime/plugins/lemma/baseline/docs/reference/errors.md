# Errors

<!-- marketplace-context:start -->
> **Marketplace context: Lemma.** Lemma turns Solidity compiler input or Markdown trees into validated, source-linked JSONL chunks, keeping quotation text separate from model and embedding text. It does not embed, index, retrieve or answer; Berean is the adjacent unbuilt release discipline for a grounded protocol agent. **Current frontier:** Callable-surface ABI validation does not independently check return types or state mutability.
<!-- marketplace-context:end -->

Every revert in the registry is a custom error. There are no string reverts.

## DuplicateEntry

Raised by `create` when the identifier is already in use.

## AtCapacity

Raised by `create` when the total has reached the immutable capacity.

## NotAdmin

Raised by the `onlyAdmin` modifier, and also by `retire` when the caller is not
the entry owner. The reuse is a known wart and is documented in the
troubleshooting guide.
