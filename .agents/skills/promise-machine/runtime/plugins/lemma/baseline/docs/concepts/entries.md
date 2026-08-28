# Entries

<!-- marketplace-context:start -->
> **Marketplace context: Lemma.** Lemma turns Solidity compiler input or Markdown trees into validated, source-linked JSONL chunks, keeping quotation text separate from model and embedding text. It does not embed, index, retrieve or answer; Berean is the adjacent unbuilt release discipline for a grounded protocol agent. **Current frontier:** Callable-surface ABI validation does not independently check return types or state mutability.
<!-- marketplace-context:end -->

An entry is the unit of state in the registry. Every entry has an identifier
that is unique for the lifetime of the deployment, and identifiers are never
reused after retirement.

## Identifier assignment

Identifiers are supplied by the caller rather than derived, because deriving
them would make the registry responsible for a namespace it does not own. The
creation call reverts with `DuplicateEntry` if the identifier is taken.

## Status transitions

An entry moves through three states.

| Status | Meaning | Set by |
| --- | --- | --- |
| `Pending` | Reserved but not yet usable | Construction only |
| `Active` | Usable | `create` |
| `Retired` | Permanently closed | `retire` |

Transitions are one-way. There is no path from `Retired` back to `Active`, and
the absence of that path is deliberate.

## Capacity

Capacity is immutable and fixed at construction. A deployment that reaches
capacity cannot be extended; a new deployment is required. This trades
flexibility for a guarantee that the entry count cannot grow without a new
address to point at.
