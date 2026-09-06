---
title: Market guide
version: 3
---

# Market guide

A fixture for the Horos Markdown outliner. Every construct below pins one
rule of the extractor; the outline is held byte for byte in
`plugins/horos/tests/test_md_outline.py`.

## Opening a market

Deploy the market, then register it.

```bash
horos map GUIDE.md
# a comment, not a heading
```

### Parameters

1. The asset.
2. The rate, as a percentage:

   ~~~solidity
   uint256 rate = 500;
   ~~~

3. The reserve ratio.

> ### Quoted note
>
> A heading behind a blockquote marker is still seen.

Closing a market
----------------

<div class="note">
## a heading-shaped line inside an HTML block
</div>

The market closes when its debt is repaid.

## Appendix

Last words.
