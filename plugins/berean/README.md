![Berean](./assets/characters/berean.png)

# Berean

<!-- marketplace-context:start -->
## In one line

Berean pins the corpus, chain reads, recorded answers and evaluation needed to check a grounded protocol-agent release without rerunning its model.

**Current frontier.** The reference release answers against a frozen demonstration corpus and preserved Goldfinch mainnet reads; no release yet cites live Wildcat documentation or a captured Wildcat market read, and no Ariadne statement binds a berean release.

**Next Fiat job.** Use /hexaemeron:fiat to ship the first berean release grounded in captured Wildcat documentation and Wildcat market reads, replacing the demonstration corpus in the reference deployment. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose. Change a skill's Next Fiat job only when that exact frontier job completed; otherwise leave it unchanged.
<!-- marketplace-context:end -->

## Place in the collective

Lemma can prepare source-linked chunks for a corpus, and Lazarus can preserve
the historical chain evidence a test or recorded answer needs. Berean owns
neither job: it binds the corpus and reads used by an agent, grades recorded
answers against a held evaluation set, and records promotion or rollback.
Ariadne can then bind the finished Berean release to its supporting evidence.

A protocol agent can answer from documentation, contract state and its own
synthesis in one paragraph. Unless those sources stay separate, the reader
cannot tell which parts are historical, which are live, which came from a
document and which the model supplied. Berean is the release contract that
keeps them separate and checkable.

A Berean release declares an immutable corpus version and digest, byte-exact
citations, typed read records with the block behind each value, the rules
separating document claims from chain readings from calculations from
user-supplied facts, the question families it supports, the conditions under
which it refuses, its evaluation cases and graders, and the promotion record
that made it active. The verifier checks corpus identity, citation spans,
read provenance and evaluation coverage offline, without the model that
produced the answers.

Three rules hold a release together:

1. Citations identify bytes, not search results. A quote passes only when
   re-slicing the pinned file reproduces its digest and its display text.
2. Live values name a block. A current value with no chain and no block is
   not evidence, and a document claim that disagrees with a later chain
   state is reported beside it rather than silently replaced.
3. Promotion is evidence. A release becomes active through a record naming
   the evaluation corpus, thresholds and results that allowed it, and
   rollback is a new record naming the restored release.

## How it works

`build-corpus` pins a document tree: one entry per file with its byte count
and sha256, and a corpus digest over the sorted listing. `check-citation`
and `check-answer` prove or refuse quotes, source classes, chain reads, time
domains and refusals against those pins. `verify-release` runs the release
gates by name. `run-evals` grades recorded answer documents against the
release's ordinary and adversarial cases, refusing to start when any pinned
digest disagrees with what is on disk. `promote` and `rollback` append
records to the promotion chain; nothing edits a published release in place.

Chain evidence arrives as preserved read records in the Lazarus record
shape, held by recomputed request keys. The shipped reference release under
[`examples/goldfinch-demo-v0`](./examples/goldfinch-demo-v0) answers,
refuses and discloses a time-domain disagreement against a frozen
demonstration corpus and preserved Goldfinch mainnet reads at block
13097494, entirely offline. Its `reads.jsonl` is the Lazarus goldfinch
fixture's records copied byte for byte, held by a drift test.

## What it ships

- Five versioned JSON schemas: corpus manifest, answer record, eval case,
  release manifest and promotion record, each with a closed field table.
- One stdlib CLI, `scripts/berean.py`, with build, check, verify, eval,
  export and promotion commands.
- An ordinary and adversarial evaluation corpus covering prompt injection,
  poisoned documents, stale state, citation mismatch, unsupported inference
  and expected refusals.
- The reference release and its demonstration script.
- Conformance fixtures, one passing and at least one breaching per verifier
  gate, under `tests/fixtures/`.
- Design records in [`docs/`](./docs), including the Commons specification
  the plugin was built from.

## Day to day

**Developers.** Your support agent quotes the docs and reads contract state.
Pin the docs tree with `build-corpus`, record the reads it may use, and ship
answers as `berean-answer/v1` documents; `check-answer` then tells you which
sentence lost its source before a user does.

**Security and audit.** An agent's answer is a claim about documents and
chain state. `verify-release` and `run-evals` re-check every span, key and
threshold from bytes on disk, so reviewing the agent does not require
trusting the vendor's harness, and the adversarial corpus shows what happens
when a document tries to steer the agent.

**Business development.** An integration answer that cites an agreement
version and a block can be handed to a counterparty with its evidence
attached. The promotion chain says which release produced it and what
evaluation that release passed.

## Run it

```text
python3 scripts/berean.py verify-release examples/goldfinch-demo-v0/release
python3 scripts/berean.py run-evals examples/goldfinch-demo-v0/release
python3 examples/goldfinch-demo-v0/demo.py
```

Run Berean with the exact interpreter in the suite
[pin](https://github.com/wildcat-finance/skills/blob/main/.python-version). It
has no other dependency, and no command reaches the network.

## Tests

```bash
python3 -m unittest discover -s plugins/berean/tests -t plugins/berean
```

## Reading further

- [`skills/berean/SKILL.md`](./skills/berean/SKILL.md), the canonical
  instructions and the release gates.
- [`docs/spec.md`](./docs/spec.md), the Wildcat Commons specification this
  plugin was built from.
- [`docs/design.md`](./docs/design.md), the decisions behind the formats and
  the deferred Ariadne binding.
- [`docs/release-policy.md`](./docs/release-policy.md) and
  [`docs/answers.md`](./docs/answers.md), the lifecycle and vocabulary
  records.
- [`docs/influences.md`](./docs/influences.md), what shaped each component
  and where the public kit's boundary sits.
- [`docs/study.md`](./docs/study.md) and [`docs/runbook.md`](./docs/runbook.md),
  the delivery record.

## Licence

Apache-2.0. See [LICENSE](LICENSE).
