# Wildcat reference handoff

The offline demo rebuilds 18 release components byte for byte, checks the
unsigned Ariadne binding and exercises citation, block and missing-read
refusals. Ten recorded cases pass across all five adversarial classes. No model
ran. The demonstration is `mixed`; its actual-agent-answer job remains open.

## Identities

- Release: `plugins/berean/examples/wildcat-mainnet-v0/release/`.
  Semantic digest: `063f677f19f6cdd1ac45b7dad64d02325d332d4b82240367423caffa9e76e36c`.
- Statement: `plugins/berean/examples/wildcat-mainnet-v0/grounded-agent.intoto.json`.
  File SHA-256: `0d315ca32edb9169de0f592fea631293813ccb4c8d6d5d17222465b0fa003c8a`.
- Documentation: `wildcat-finance/wildcat-docs` commit
  `636b1dcba90c816e699c0d876c22d39be2c58b06`; three captured files, 40,001 bytes.
- Market: `0x90772c109adc8d216967a2782eae8271b4e46c1e`, Ethereum chain 1,
  block 25907928, hash
  `0x33600dbb40dec3fbfa5898f65b80ba4dfea2873b2281db62dd3dc7dd9fc51b70`.
- Lazarus fixture digest:
  `539aa993cc0831253d207f8bce8fd5500cf085e133532e479afd37cb779a8391`.

## Consumer boundary

The five calls remain `recorded-rpc`. The account proof and header do not prove
call results, canonical-chain membership or provider independence. The
statement is unsigned, with no publisher identity claim. Its recorded producer
version `0.2.0` remains fixed even though the skill now advances to `1.2.0`.

The official documents are unchanged; constructed stale-state and poisoned
specimens occupy a separate corpus directory. Authored answers establish no
live model behaviour. The release establishes no current delinquency, default,
lender position, claimable withdrawal, other market or source-to-bytecode
equality. Linked upstream pages outside the three captured files remain absent.

[Issue #1144](https://github.com/wildcat-finance/skills/issues/1144) may inspect
these exact inputs after delivery. This handoff does not resume its halted
controller or supply its separate evaluation work.

## Reproduce

Use the interpreter pinned in [`.python-version`](../../.python-version) and a full source checkout:

```sh
python3 plugins/berean/examples/wildcat-mainnet-v0/demo.py
python3 scripts/demonstrations.py run --record plugins/berean/skills/berean --report tmp/demo/wildcat-reference.json
```

The report path must not exist. The demonstration runner denies Python socket
operations within its documented process boundary; the demo itself calls no
endpoint. The original release and statement are inputs and remain unchanged.

The fixed design matrix selected `selected-docs`. Its original resolver ran as
`python3 .hexaemeron/design_probe.py selected-docs`, and
`design_evidence.py --transition integration` accepted the retained final report.
The [report](design-reports/selected-docs-final-release.json) records that result;
the original matrix and selection reports retain their exact bytes.
