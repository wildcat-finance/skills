# Answer records

<!-- marketplace-context:start -->
> **Marketplace context: Berean.** Berean pins the corpus, chain readings and evaluation record a protocol agent's answers rest on, so a release can be checked without the model that produced it. Use Lemma to produce source-linked chunks, Lazarus to preserve the chain evidence itself, and Ariadne to bind a released artefact digest to its evidence. **Current frontier:** The reference release answers against a frozen demonstration corpus and preserved Aave v4 mainnet reads; no release yet cites live Wildcat documentation or a captured Wildcat market read, and no Ariadne statement binds a berean release.
<!-- marketplace-context:end -->

The `berean-answer/v1` vocabulary, and why each enum is closed. The schema
is [answer-v1.json](../schemas/answer-v1.json); the checks live in
`scripts/berean_lib/answers.py`.

## Source classes

Four, and exactly four: `document`, `chain_read`, `calculation`,
`user_supplied`. Every factual sentence carries one. The set is closed at
read time because widening it is how a fifth class appears in one answer,
verifies nowhere, and reads to a human as though it verified somewhere.

- `document` sentences cite byte-exact citations into the pinned corpus.
- `chain_read` sentences cite preserved read records by recomputed request
  key, and the read names the chain and block the release declared.
- `calculation` sentences derive from evidence already in the answer, so a
  number with no visible inputs has nowhere to hide.
- `user_supplied` sentences name the spans of the recorded question they
  rest on, as `question:<start>-<end>` byte ranges in `evidence`. They
  still cite no artefact: the fact came from the asker, and attaching an
  artefact to it would dress a claim as a check. Their retention is the
  release's declaration, not the answer's.

The classes never upgrade. A recorded read does not become proof-backed
here, and a document claim does not become a chain reading because the
chain happens to agree with it.

## Question spans

A span reference is `question:<start>-<end>`: two decimal offsets with no
sign, no leading zero and at most seven digits each, matched in full before
either is parsed. The offsets count bytes of the UTF-8 encoding of
`question`, the unit citations already use, and the checker re-slices them:
`start` is below `end`, `end` is within the encoded length, the slice
decodes as whole UTF-8 and is not blank. Offsets are read only after
`question` itself proves encodable. A question with no UTF-8 encoding,
which a lone-surrogate escape in the JSON produces, fails `answer-shape`
before any span is read, for either kind of document. A sentence may name
several spans. No citation or read id may begin with `question:`, so one
evidence string resolves to one kind of thing whichever sentence cites it.

The check proves that the sentence points at real, whole, non-blank bytes
of the asker's question. It does not prove that the sentence rests on them
honestly; that stays with gate 6 and the evaluation corpus, as a citation
that resolves can still fail to support its sentence.

## Time domains

A document speaks as of its version; a read speaks as of its block. When
the two disagree about a subject, the answer carries a `discrepancies`
entry naming the citation, the read and the disagreement. The checker
proves both sides exist and resolve; whether an answer that stayed silent
should have declared one is an evaluation question, and the eval corpus
carries those cases.

## Refusals

A refusal is `kind: "refusal"` with a named boundary and nothing else: no
sentences, no citations, no reads. The emptiness is enforced, because a
refusal that also answers is an answer that dodged its evidence rules.

## Evidence hygiene

Ids are unique, every evidence reference resolves, and evidence nothing
cites is refused. An answer carries only the evidence it uses, so a reader
auditing one sentence is never sent through artefacts the answer merely
decorated itself with.
