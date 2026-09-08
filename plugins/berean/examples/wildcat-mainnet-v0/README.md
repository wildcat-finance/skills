# Wildcat mainnet reference release

This release checks authored answer fixtures against captured Wildcat documents
and five fixed-block market calls. It runs offline and executes no model.
The demonstration and reference-default change belong to the next delivery step.

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
A passing input check establishes only the named input relation. The release
adds recorded answers and evaluations; no frontier advancement is claimed here.

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

## Rebuild and check

From the repository root, choose a destination that does not exist, beneath an
existing directory. Use a physical path without symlink ancestors (on macOS,
`/private/tmp` meets that condition). The default destination is the committed
`release/`, so invoking the builder without a fresh destination refuses.

```sh
python3 plugins/berean/examples/wildcat-mainnet-v0/rebuild.py --release /private/tmp/wildcat-reference-new
python3 plugins/berean/scripts/berean.py verify-release plugins/berean/examples/wildcat-mainnet-v0/release
python3 plugins/berean/scripts/berean.py run-evals plugins/berean/examples/wildcat-mainnet-v0/release
python3 plugins/ariadne/scripts/ariadne.py verify plugins/berean/examples/wildcat-mainnet-v0/grounded-agent.intoto.json
python3 -m unittest discover -s plugins/berean/tests -t plugins/berean -p test_wildcat_reference.py
```

`--inputs` selects a local copy of the preserved input directory; it must match
all fixed component digests. The builder checks file types, path confinement,
byte limits, chain, block, request keys, methods, targets, calldata and ABI
words before writing. It stages and verifies the release, then uses an
exclusive rename on macOS or Linux. Unsupported platforms refuse. An existing
destination, including an empty directory or promotion chain, remains untouched.
The destination parent must be trusted against concurrent directory renames.

The release's `corpus/fixtures/docs/official/` contains exactly the three upstream blobs,
`40,001` bytes. `corpus/constructed/` separately contains two authored specimens:
a fictional earlier grace period and hostile instruction text. Neither is
upstream documentation or historical Wildcat evidence. They let the existing
stale-state and poisoned-document graders exercise their citation paths.
The other adversarial cases cover prompt injection, citation mismatch and
unsupported inference. All ten cases grade recorded answers, not model behaviour.

Each call result is exactly one 32-byte ABI word. Integers decode unsigned;
addresses require zero padding; the registration boolean must be zero or one.
At block `25907928`, the configured delinquency fee reads `0` basis points and
the grace period `172800` seconds. Registration returns `true`; the asset is
`0xdac17f958d2ee523a2206206994597c13d831ec7` and the borrower is
`0xde8845ff1d67b84e755a57481097e712460ac21b`. These readings establish no
current delinquency, default, lender position or claimable withdrawal.

The builder's JSON output names completion with the release digest, or refusal
with the failed stage and reason. A failed stage leaves no partial new release.
The promotion record belongs to these authored fixtures and their evaluation;
rebuilding cannot erase an earlier promotion chain.

`grounded-agent.intoto.json` is outside the release's exact file inventory.
Ariadne captured it through its existing adapter after the producer command
`python3 plugins/berean/examples/wildcat-mainnet-v0/rebuild.py` ran successfully.
The statement is unsigned and claims no author. It binds component identities;
it does not regrade the answers or prove the calls. The retained Aave example
is unchanged.
