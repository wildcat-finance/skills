# ADR-042: Record corpus provenance beside the chunks

## Status

Accepted, 2026-08-27.

## Context

A delivered Lemma corpus is a `chunks.jsonl` file. Nothing in it says which
source ref it was built from, which compiler produced the AST the Solidity
chunk boundaries came from, or which version of the chunker cut them. The
`Chunk` dataclass declares `source_ref` and `corpus_build_id`, and
`schema.stamp()` exists to fill them, but no production caller invokes it: its
only two call sites are in the Solidity test suite. So the fields are null in
every corpus anyone has received.

Two readers need those values. The one holding a `chunks.jsonl` who has to
decide whether a citation out of it can be trusted, and the one rebuilding the
corpus two years later who has to know which compiler to use.

Ariadne already publishes a registered dataset predicate and a `capture-dataset`
command that walks a release directory, digests every file it finds, and binds
each digest as a subject of a signed statement. Gate 2 of that predicate refuses
any digested file that is not a statement subject. So a file placed in the
release directory has its bytes bound by a check that already exists.

What that command cannot do is read a value out of a corpus. It derives exactly
two things per file, a `sha256` and a record count for line-delimited formats,
and refuses to guess the count for anything else. Everything else it records is
typed by the operator on the command line. `producer.parameters_digest` digests
the parameters without carrying their values, so a `--parameter solc=0.8.25` is
unreadable afterwards. The predicate's field list is closed and its schema sets
`additionalProperties: false`, so none of the four values can be added as a new
predicate field without changing Ariadne.

That leaves one seam: a file inside the release directory whose digest becomes a
subject.

## Decision

Each chunker writes one line of JSON to `provenance.jsonl` beside its `--out`
file. A delivered corpus is those two files in one directory.

The record's shape is `lemma-corpus-provenance/v1`, published in
`plugins/lemma/schema.py` as `provenance_record()` with `validate_provenance()`
holding it to that shape, and stated as a guarantee at invariant I6 in
`plugins/lemma/INVARIANTS.md`. It carries the schema id, the chunker and its
version, the source ref, the corpus build id recomputed from the chunks
actually written, the digested inputs, the selection, the compiler block and the
chunk count.

The per-chunk half is kept. `source_ref` and `corpus_build_id` are stamped onto
every chunk through the existing `schema.stamp()`, from the pipeline above
`chunk()` and never from inside it. What does not go on a chunk is the compiler
identity and the chunker version, because those are one fact per corpus and
`schema.py` already argues against a top-level field that is identical on every
record and meaningless on half of them.

Lemma writes no statement, signs nothing and shells out to nothing. It produces
the bytes; the operator runs `capture-dataset` over the directory and Ariadne
binds them.

The record says what it does not know. No field is ever written as the string
`unknown`. A compiler that does not apply is an absence with a reason. A
compiler that applies but was gated on nothing records the version it reported
with a null pin and a reason. A gated compiler records its pin as a prefix pin,
because the gate compares with `startswith` and a gate on `0.8.25` accepts any
commit hash after it. A source ref is recorded as asserted by the caller,
because nothing fetches or resolves it. A ref spelled as a URL loses its whole
userinfo on the way to disk, whatever shape that userinfo has, under the rule
Ariadne's own audit established.

## Alternatives

- **Fill only the per-chunk provenance fields.** Call `stamp()` from the CLI and
  stop. Cheapest, and it closes half the gap. It cannot carry the compiler
  identity or the chunker version without adding two top-level fields to the
  type every consumer reads, for two facts identical on every record, and it
  cannot carry the include patterns or the input digests at all, so a reader
  still cannot tell which source units the corpus describes. Its per-chunk half
  is kept inside this decision.
- **Have Lemma write the statement.** Emit a dataset-predicate statement beside
  the chunks, filled from the build rather than from typed flags. That is the
  strongest form of the promise and it is ruled out by the marketplace boundary:
  `AGENTS.md` says Lemma stops at chunks and the skill says it does not attest,
  while Ariadne owns the capture path. A landed peer took exactly this shape and
  its own documentation records the result, an unregistered predicate whose
  gates went unchecked. Reusing the registered type would avoid that particular
  outcome and would put a second implementation of Ariadne's capture rules
  inside Lemma, where nothing holds the two in agreement.
- **Give the dataset predicate a corpus block.** Add the field to the schema and
  the predicate, gate it, add conformance fixtures, update the drift test and
  extend `capture-dataset` to fill it. This is the only option under which
  Ariadne checks the compiler and the ref rather than binding bytes that assert
  them, and that difference is real. It is also the most expensive option that
  meets the same criterion: an Ariadne evolution with its own ledger row, audit
  surface and conformance fixtures. Named here with its one genuine advantage so
  a later run can reopen it on evidence rather than on preference.

## Consequences

Nothing in Ariadne changes and no new predicate type is registered. The record's
bytes are bound by a gate that already refuses an unbound file, and its record
count derives automatically because the file is line-delimited with one line.

A consumer that reads only `chunks.jsonl` sees the ref and the build id on every
chunk and does not see the compiler. To learn which compiler produced the AST it
has to open the file beside it. That is the cost of not repeating one fact
several thousand times, and it is the reason this is a record rather than a
comment: once a consumer reads `provenance.jsonl`, moving those fields into
`Chunk` means changing the type every consumer reads.

Two files under one `--out` is a window a single file did not have. A run that
failed after writing one of them would leave a directory a capture could read as
a whole corpus. Everything is therefore computed before anything is written, the
chunks land first, and the build id in the record is recomputed from the chunks
on disk.

The userinfo strip is a defence against an accident rather than against a
determined caller. What it removes is the userinfo, whatever shape that has:
`ssh://git@host/o/r.git` loses the `git` as surely as a token. A credential
spelled any other way reaches the file, and a digest over that file binds bytes
rather than the truth of what they say.
