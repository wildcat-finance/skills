# What shaped each component

<!-- marketplace-context:start -->
> **Marketplace context: Berean.** Berean pins the corpus, chain readings and evaluation record a protocol agent's answers rest on, so a release can be checked without the model that produced it. Use Lemma to produce source-linked chunks, Lazarus to preserve the chain evidence itself, and Ariadne to bind a released artefact digest to its evidence. **Current frontier:** The reference release answers against a frozen demonstration corpus and preserved Goldfinch mainnet reads; no release yet cites live Wildcat documentation or a captured Wildcat market read, and no Ariadne statement binds a berean release.
<!-- marketplace-context:end -->

The specification at [spec.md](spec.md) names three inputs: Project Aleph,
Project Null and Lemma. The first two are Wildcat Labs repositories this
public kit deliberately does not read; what they contributed here is what
the specification says they proved, and this guide keeps that boundary
visible. The rest of the marketplace contributed concrete mechanics, cited
by path.

## From the named inputs

Project Aleph, per the specification, already runs a versioned corpus,
typed mainnet reads, citations, abstention and release promotion in one
protocol agent. Berean's five formats are that decomposition made public:
the corpus manifest carries the versioned corpus, the answer record
carries citations and refusals, the release manifest carries the
promotion boundary. Nothing in this plugin was copied from Aleph's code;
the extraction is of the decisions, restated as closed formats a stranger
can verify.

Project Null, per the specification, generates and reviews adversarial
questions against Aleph. Its trace here is the shape of the evaluation
corpus: the five adversarial classes in `berean-eval-cases/v1` (prompt
injection, poisoned documents, stale state, citation mismatch, unsupported
inference) are the question families the specification says that loop
works, held as data with code graders so no model provider is coupled.

Lemma is in this repository, and its influence is directly checkable. Its
invariants (`plugins/lemma/INVARIANTS.md`) prove byte-exact quoting works:
`display_text` sliced from source bytes and decoded after slicing. Its
records deliberately stop short of what a verifier needs, carrying no byte
offsets and no digests, and that gap is exactly what
`berean-citation/v1` adds: byte start, byte end, span digest and display
text, re-sliced and re-hashed at check time.

## From the rest of the marketplace

- Ariadne (`plugins/ariadne/docs/design.md`) supplied the verification
  grammar: digest-only matching, closed field tables, named gates, and
  conformance fixtures where every rule has a committed breach. Its core
  refuses conclusion vocabulary inside a statement, which is one of the
  two reasons berean's release document stands apart rather than becoming
  a predicate; [design.md](design.md) records that decision.
- Lazarus (`plugins/lazarus/docs/preservation-release.md`) supplied the
  evidence bundle and the binding pattern: recorded reads keyed by the
  digest of their canonical request, canonical JSON with floats refused,
  and two artefacts held together by recomputation rather than by runtime
  import. The reference release's `reads.jsonl` is its goldfinch fixture's
  records, copied byte for byte and held by a drift test.
- Alexandria (`plugins/alexandria/docs/study.md`) named evidence-class
  inflation as a standing risk; berean's closed source and evidence
  vocabularies, never widened at read time, are that rule generalised.
- Tabularium (`plugins/tabularium/docs/release-policy.md`) supplied the
  release lifecycle berean's [release-policy.md](release-policy.md)
  restates: immutable published bytes, corrections as new releases,
  standing recorded rather than edited.
- Probitas (`plugins/probitas/scripts/probitas_lib/gates.py`) supplied the
  answer-side posture: a claim without a source is dropped, and the
  verifier rebuilds what a truthful document could say rather than
  trusting what this one says.
- Imprimatur's labelled corpus
  (`plugins/hexaemeron/skills/imprimatur/evals/labelled-prose-v1/`)
  supplied the frozen-evaluation discipline: pinned inputs, graders held
  by digest, and a promotion that names the evidence that earned it.

## The boundary

The Agent Skills evaluation guide already covers cases, assertions and
graders for skills in general, so berean emits that shape through
`export-cases` instead of shipping another runner. Retrieval frameworks
already split documents and return citations; berean starts where they
stop, at the release boundary: immutable corpus identity, verified spans,
block-bound reads, adversarial evidence tests and promotion records.
