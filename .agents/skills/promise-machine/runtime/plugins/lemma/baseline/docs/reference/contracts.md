# Contract surface

<!-- marketplace-context:start -->
> **Marketplace context: Lemma.** Lemma turns Solidity compiler input or Markdown trees into validated, source-linked JSONL chunks, keeping quotation text separate from model and embedding text. It does not embed, index, retrieve or answer; Berean is the adjacent unbuilt release discipline for a grounded protocol agent. **Current frontier:** Callable-surface ABI validation does not independently check return types or state mutability.
<!-- marketplace-context:end -->

## Registry

The concrete deployment. Inherits everything on `RegistryBase`.

### create

Creates an entry. Admin only. Reverts on a duplicate identifier or at capacity.

### retire

Retires an entry. Owner only.

### setFee

Sets the creation fee. Admin only. Takes effect from the next creation.

## RegistryBase

Abstract. Holds storage and access control, and is not deployed on its own.

### entry

Returns the stored entry for an identifier, or a zeroed entry if none exists.

### total

Returns the number of entries ever created.
