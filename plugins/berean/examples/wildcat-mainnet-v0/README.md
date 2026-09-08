# Wildcat mainnet reference inputs

This directory preserves the inputs for the Wildcat Berean reference release.
Step 1 contains captured evidence and the specification; the release, recorded
answers and demonstration are not built yet.

The source subject is `wildcat-finance/wildcat-docs` at commit
`636b1dcba90c816e699c0d876c22d39be2c58b06`. The deployed subject is market
`0x90772c109adc8d216967a2782eae8271b4e46c1e` on Ethereum chain `1`, block
`25907928`, hash
`0x33600dbb40dec3fbfa5898f65b80ba4dfea2873b2281db62dd3dc7dd9fc51b70`.
The documentation commit does not establish deployed bytecode equality.

## Layout

- `inputs/fixtures/docs/` holds the three unchanged official Markdown blobs.
  `inputs/docs-provenance.json` gives their original paths, commit, byte counts
  and SHA-256 digests. Relative links to other upstream pages are uncaptured;
  the fixtures directory keeps captured quotations outside authored-prose walks.
- `inputs/lazarus-fixture/` holds the finite Lazarus fixture;
  `inputs/capture-plan.json` and `inputs/capture-result.json` retain its capture
  plan and producer result. The five calls remain `recorded-rpc`; the account
  proof and header do not prove those call results.
- `inputs/blockscout-anchor.json` and `inputs/blockscout-provenance.json` retain
  the response captured on `2026-09-06T00:39:04Z`. The later request returned
  HTTP 403. The preserved response is recorded provenance, with no canonical
  chain or provider independence claim.
- [Study and runbook](../../../../docs/berean-wildcat-reference/) retain the
  selected design, selection reports and original experiment source.

## Verify the inputs

Use CPython `3.14.6`, as pinned in the repository's `.python-version`. From the
repository root, with the existing Lazarus dependencies available, run:

```sh
python3 plugins/lazarus/scripts/lazarus.py verify plugins/berean/examples/wildcat-mainnet-v0/inputs/lazarus-fixture
python3 scripts/run_checks.py --base origin/main
```

The expected fixture digest is
`539aa993cc0831253d207f8bce8fd5500cf085e133532e479afd37cb779a8391`.
Verification reports one account proof, one header and five recorded calls.
Document verification compares each blob's bytes and SHA-256 against
`inputs/docs-provenance.json`; the captured documents total `40,001` bytes.
A passing check establishes only the named input relation. No release or
frontier advancement is claimed by this scaffold.

## Licence and experiment record

First-party scaffold code and prose use the repository's [Apache-2.0 licence](../../../../LICENSE).
Captured source bytes retain their upstream authorship and provenance; this
scaffold makes no claim to relicense them. The existing CI and dependencies
apply; no workflow or dependency is added.

`docs/berean-wildcat-reference/design_probe.py` is the unchanged historical
experiment source. Its original execution used `.hexaemeron/` and a local
`wildcat-docs` checkout, as recorded in the study and reports. It is retained
for inspection, not presented as a portable command from its copied location.
The design matrix still marks final-release conformance pending.
