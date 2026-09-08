# aave-v4-demo-v0

<!-- marketplace-context:start -->
> **Marketplace context: Berean.** Berean pins the corpus, chain readings and evaluation record a protocol agent's answers rest on, so a release can be checked without the model that produced it. Use Lemma to produce source-linked chunks, Lazarus to preserve the chain evidence itself, and Ariadne to bind a released artefact digest to its evidence. **Current frontier:** The Wildcat reference release pins three captured official documents and five recorded market calls at Ethereum block 25907928, with an unsigned Ariadne statement binding all 18 release components. The release frontier is mature; authored answers keep its demonstration status mixed.
<!-- marketplace-context:end -->

The historical Aave reference release. Its documents are written for the demonstration and
say so; its chain evidence is real.

## What it holds

`release/reads.jsonl` is a byte-for-byte copy of the Lazarus aave-v4-spoke-v0
preservation fixture's recorded RPC responses for the contract
`0x973a023a77420ba610f06b3858ad991df6d85a08` at Ethereum mainnet block
25870892, and a plugin test holds the copy identical to its source
whenever both are in the tree. The records stay recorded-rpc evidence
here; nothing upgrades them, and the Lazarus release's own plan records
the block hash provenance.

The release under [`release/`](./release) carries three frozen corpus
documents, three pinned answers (one grounded, one refusal, one disclosing
a document-against-chain disagreement), an evaluation corpus of seven
cases covering all five adversarial classes, the graded report, and a
promotion chain with one earned record. Its retention declaration is
`none`, and the verifier holds the answers to that.

## Run it

From the repository root, no network needed:

```text
python3 plugins/berean/scripts/berean.py verify-release plugins/berean/examples/aave-v4-demo-v0/release
python3 plugins/berean/scripts/berean.py run-evals plugins/berean/examples/aave-v4-demo-v0/release
python3 plugins/berean/examples/aave-v4-demo-v0/demo.py
```

The demo verifies the gates, grades the corpus, replays the promotion
chain, then tampers with copies three ways and shows each named gate
refuse.

## Rebuild it

[`rebuild.py`](./rebuild.py) regenerates everything under `release/`
except the preserved `reads.jsonl` from the texts it carries,
deterministically; a test compares its output to the committed bytes. The
corpus files carry no rolling marketplace prose on purpose: their bytes
are pinned by the corpus manifest, and prose that moves under a frontier
refresh cannot live inside a digest.
