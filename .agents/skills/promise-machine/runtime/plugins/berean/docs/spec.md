# berean

<!-- marketplace-context:start -->
> **Marketplace context: Berean.** Berean pins the corpus, chain readings and evaluation record a protocol agent's answers rest on, so a release can be checked without the model that produced it. Use Lemma to produce source-linked chunks, Lazarus to preserve the chain evidence itself, and Ariadne to bind a released artefact digest to its evidence. **Current frontier:** The reference release answers against a frozen demonstration corpus and preserved Goldfinch mainnet reads; no release yet cites live Wildcat documentation or a captured Wildcat market read, and no Ariadne statement binds a berean release.
<!-- marketplace-context:end -->

This is the Wildcat Commons specification the v0.1.0 prototype was built
from, preserved as written apart from this header block, whose original text
said only that Berean remained unbuilt. The status line below is the
specification's own, kept as a record of where the work started.

Release evidence-backed protocol agents with citation, time and live-data
boundaries that can be tested independently of the model running them.

**Desk:** developer relations, support and agent engineering. **Status:**
unbuilt spec.

## Naming

In Acts, the Bereans receive a claim and check it against the scriptures each
day to see whether it is so. The important part is not scepticism for its own
sake. It is the habit of returning to the named source before accepting the
answer.

## Why this exists

A protocol agent can answer from documentation, contract state, indexed data
and prior conversation in one paragraph. Unless those sources remain
separate, the reader cannot tell which parts are historical, which are live,
which came from a document and which were supplied by the model.

General agent evaluations can score answers and tool use. They do not define
how a protocol agent pins a changing corpus, proves a citation span, separates
a block reading from prose, or refuses a question whose evidence boundary it
cannot satisfy.

## Why this belongs to Wildcat Labs

Project Aleph already uses a versioned corpus, typed mainnet reads, citations,
abstention and release promotion. Project Null generates and reviews
adversarial questions against it. Lemma preserves byte-exact document chunks
for display and model use.

Those repositories contain useful decisions, but a new team has to infer the
system from three codebases. The public contribution is a small release
contract, reference implementation and test corpus extracting the parts that
deal with evidence. It should leave chat UI, model vendor and protocol-specific
answers out.

Wildcat can demonstrate the kit against a real protocol whose answers often
depend on a particular market, agreement version and block. That prevents the
reference case from becoming a static documentation bot with easy citations.

## What it does

A Berean release declares:

- Immutable corpus version and digest.
- Document identity, version, byte offsets and display text for every cited
  span.
- Typed live-data functions, their chain and contract allowlists, and the
  block associated with each result.
- Rules separating document claims, live readings, calculations and model
  synthesis.
- Supported question families and explicit refusal conditions.
- Evaluation cases, assertions, graders and expected evidence shape.
- Adversarial cases for prompt injection, poisoned documents, stale state,
  citation mismatch and unsupported inference.
- Promotion and rollback records for the active release.

The verifier can check corpus identity, citation spans, live-read provenance
and assertion coverage without needing the model that originally produced the
answer.

## Gates

1. **Every factual sentence has a source class.** Document, chain read,
   calculation or user-supplied fact. Unclassified assertions fail evaluation.
2. **Citations identify bytes, not search results.** The cited text is checked
   against the pinned corpus artefact.
3. **Live values name a block.** A current value with no chain and block is not
   accepted as evidence.
4. **Time domains do not blur.** A document statement and a later chain state
   may disagree. The answer reports both rather than choosing silently.
5. **Unsupported questions refuse cleanly.** The evaluation set includes cases
   where no answer is the correct result.
6. **Retrieved text remains untrusted.** Instructions inside documents cannot
   alter tool policy, corpus scope or citation rules.
7. **Promotion is evidence-based.** A release records the evaluation corpus,
   thresholds and result that allowed it to become active.
8. **Conversation retention is declared.** Tests check that private user data
   does not enter the public corpus or evaluation output.

## What ships with it

- A release-manifest schema and verifier.
- A small model-neutral reference agent.
- Corpus builder with byte-exact citation support.
- Typed EVM read boundary and sample functions.
- Adversarial and ordinary evaluation corpus.
- Promotion and rollback CLI.
- Reference deployment against Wildcat documentation and selected mainnet
  reads.
- A guide showing how Aleph, Null and Lemma informed each component.

## Prior art and boundary

The [Agent Skills evaluation guide](https://agentskills.io/skill-creation/evaluating-skills)
already covers test cases, assertions, graders and comparison with and without
a skill. Existing runners can exercise local models and tool calls. Berean
should emit compatible cases where possible instead of supplying another
general runner.

Retrieval frameworks already split documents and return citations. The work
here is the release boundary: immutable corpus identity, verified spans, typed
and block-bound live reads, adversarial evidence tests and promotion records.

## Open questions

- Whether the manifest can extend Ariadne directly or should remain a separate
  predicate referenced by an Ariadne release statement.
- How to score an answer that is correct but cites a weaker source than the one
  available.
- Which calculations need a machine-readable derivation rather than source
  citations alone.
- How much of Project Null's generator/reviewer loop is reusable without
  coupling the kit to one model provider.
