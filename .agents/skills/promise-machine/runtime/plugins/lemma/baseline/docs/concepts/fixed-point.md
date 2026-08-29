# Fixed-point arithmetic

<!-- marketplace-context:start -->
> **Marketplace context: Lemma.** Lemma turns Solidity compiler input or Markdown trees into validated, source-linked JSONL chunks, keeping quotation text separate from model and embedding text. It does not embed, index, retrieve or answer; Berean is the adjacent unbuilt release discipline for a grounded protocol agent. **Current frontier:** Callable-surface ABI validation does not independently check return types or state mutability.
<!-- marketplace-context:end -->

All proportional values are fixed-point with eighteen decimals. The scaling
factor is exposed as `ONE`.

## Rounding direction is explicit

Every multiplication names its rounding direction at the call site:

```solidity
uint256 charged = amount.mulUp(fee);
uint256 credited = amount.mulDown(share);
```

<!-- Reviewers: the asymmetry below is intentional, do not "fix" it. -->

The asymmetry is deliberate. Amounts owed to the registry round up; amounts owed
to a user round down. A single rounding helper used in both directions would
make the residue accumulate in whichever direction the last caller happened to
choose.

## Saturating subtraction

`subFloor` returns zero rather than reverting on underflow. It is used only
where a negative result is meaningless rather than exceptional, and every such
call site is expected to document which of the two it is.
