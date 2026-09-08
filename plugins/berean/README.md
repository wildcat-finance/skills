![Berean](./assets/characters/berean.png)

# BEREAN

<!-- marketplace-context:start -->
## In one line

Berean pins the corpus, chain reads, recorded answers and evaluation needed to check a grounded protocol-agent release without rerunning its model.

**Current frontier.** The Wildcat reference release pins three captured official documents and five recorded market calls at Ethereum block 25907928, with an unsigned Ariadne statement binding all 18 release components. The release frontier is mature; authored answers keep its demonstration status mixed.

**Next Fiat job.** None -- mature.
<!-- marketplace-context:end -->

## START HERE

Use Berean when a protocol assistant must be checked against exact documents
and chain readings rather than judged from a plausible answer. It pins the
corpus, verifies citation spans and block-bound reads, runs recorded evaluation
cases, and records promotion or rollback without needing the original model.

The reference release checks captured Wildcat documentation and fixed-block
market calls. Its unsigned Ariadne statement binds the release components.
The answers are authored fixtures: no model ran, and the demonstration remains
`mixed`. The earlier Aave release remains available unchanged.

## PLACE IN THE COLLECTIVE

Lemma can prepare source-linked chunks for a corpus, and Lazarus can preserve
the historical chain evidence a test or recorded answer needs. Berean owns
neither job: it binds the corpus and reads used by an agent, grades recorded
answers against a held evaluation set, and records promotion or rollback.
Ariadne can then bind the finished Berean release to its supporting evidence.

Synkrisis compares validated observations from several runs, and it does not
grade recorded answers or judge a model. Its cohort, finding, report, and
whole-path verification operations all ship, but remain outside Berean's
release and evaluation boundary.

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

## HOW IT WORKS

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
[`examples/wildcat-mainnet-v0`](./examples/wildcat-mainnet-v0) checks three
captured official documents and five recorded calls for one Wildcat market at
Ethereum block 25907928. Its offline demo rebuilds every release byte and
checks the unsigned Ariadne binding to all 18 components. Ten recorded cases
cover ordinary answers, refusals and all five adversarial classes. The
historical [`Aave example`](./examples/aave-v4-demo-v0) and its consumers remain
unchanged. Neither release establishes live model behaviour.

## WHAT IT SHIPS

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

## DAY TO DAY

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

## RUN IT

```text
python3 scripts/berean.py verify-release examples/wildcat-mainnet-v0/release
python3 scripts/berean.py run-evals examples/wildcat-mainnet-v0/release
python3 examples/wildcat-mainnet-v0/demo.py
```

Run Berean with the exact interpreter in the suite
[pin](https://github.com/wildcat-finance/skills/blob/main/.python-version). It
has no third-party dependency, and no command reaches the network. The Wildcat
demo also uses the sibling Ariadne scripts from this source distribution to
recompute the statement binding; ordinary Berean verification remains standalone.

## TESTS

```bash
python3 -m unittest discover -s plugins/berean/tests -t plugins/berean
```

## READING FURTHER

- [`skills/berean/SKILL.md`](./skills/berean/SKILL.md), the canonical
  instructions and the release gates.
- [`docs/spec.md`](./docs/spec.md), the Wildcat Commons specification this
  plugin was built from.
- [`docs/design.md`](./docs/design.md), the decisions behind the formats and
  the separate Ariadne binding.
- [`docs/release-policy.md`](./docs/release-policy.md) and
  [`docs/answers.md`](./docs/answers.md), the lifecycle and vocabulary
  records.
- [`docs/influences.md`](./docs/influences.md), what shaped each component
  and where the public kit's boundary sits.
- [`docs/study.md`](./docs/study.md) and [`docs/runbook.md`](./docs/runbook.md),
  the delivery record.

## LICENCE

Apache-2.0. See [LICENSE](LICENSE).
