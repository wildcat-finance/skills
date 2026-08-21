# Size catalogue

Use this list to nominate one size class. Predict the saving, then let Procrustes
measure it. A plausible compiler story is not a result, and neither is a smaller
contract that lost a check on the way down.

Every entry costs gas somewhere unless the row says otherwise. Declare the gas
regression the run will tolerate before measuring.

| Procrustes class | Candidate idea | Usual risk | Checks before trying it |
| --- | --- | --- | --- |
| `revert-strings` | Replace revert strings with custom errors | Low | Find tests and callers that match on revert data; a string moved into an error name is not a deleted check |
| `dead-code` | Remove unreachable internal functions, unused inherited contracts and unused imports | Low | Confirm nothing reaches them through inheritance, a library or an interface cast |
| `error-arguments` | Drop arguments from custom errors that nobody decodes | Low-medium | Read every off-chain consumer of the revert data first |
| `public-to-external` | Narrow `public` functions to `external`, drop generated getters nobody calls | Medium | Selectors must not move; a dropped getter is an ABI change |
| `modifier-to-function` | Move a modifier's body into an internal function so it is not inlined at every use site | Medium | The check has to remain on every path it guarded; this is the class most likely to trip the deleted-check gate by accident |
| `immutable-to-storage` | Move a rarely-read `immutable` back to storage, since its value is inlined at every use | Medium | Expect a layout change and a gas cost; frozen contracts cannot take this class |
| `constant-data` | Move a large constant array or string out of code and read it from storage or a data contract | Medium | Compare the read path's gas and confirm nothing assumed a compile-time constant |
| `library-extraction` | Move code into an external library that is linked rather than inlined | High | The bytes move behind `delegatecall`; declare the link, and account for where the size went |
| `facet-split` | Split a contract into facets behind one dispatcher, as in EIP-2535 | High | A new trust and upgrade surface, not only a size change; layouts and selectors both need holding still |
| `assembly` | Replace Solidity with a small assembly section | High | Prove memory safety, returndata handling and revert behaviour; keep this class on its own |

## Settings are their own experiment

`optimizer_runs`, `via_ir`, the Solidity version, `bytecode_hash` and
`cbor_metadata` reprice every contract at once, so they never share attribution
with a source change. Run each as its own class from a clean baseline.

Two are worth knowing about before reaching for source edits. Lowering
`optimizer_runs` tells solc to favour deployment size over call cost, which is
the whole trade in one setting. Setting `bytecode_hash = "none"` and
`cbor_metadata = false` removes the metadata trailer solc appends after the
runtime code, which is tens of bytes and no behaviour at all -- worth taking
first when the overshoot is small, and worth checking against any verification
or provenance workflow that expects the trailer to be there.

## Quick source searches

Run these from the Foundry root and adapt the names:

```bash
forge build --sizes
rg -n 'revert\("|require\([^,]+,\s*"' src
rg -n '\bmodifier\b' src
rg -n '\bimmutable\b|\bconstant\b' src
rg -n 'delegatecall|library |using .* for' src
```

`forge build --sizes` first, every time. The contract that is actually over the
limit is often not the one somebody remembers being large.

## Pick in this order

Start with the metadata trailer and revert strings, then dead code. Those are
cheap to prove and rarely controversial. Move to the getter and modifier classes
once the easy bytes are gone. Leave library extraction, facet splitting and
assembly until the overshoot is large enough to be worth their proof cost, and
never reach for them to save a few dozen bytes.
