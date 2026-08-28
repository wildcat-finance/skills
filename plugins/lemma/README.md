![Lemma](./assets/characters/lemma.png)

# Lemma

<!-- marketplace-context:start -->
## In one line

Lemma turns Solidity compiler input or Markdown trees into validated, source-linked JSONL chunks with quotation, model, and embedding text kept separate.

**Current frontier.** Callable-surface ABI validation does not independently check return types or state mutability.

**Next Fiat job.** Use /hexaemeron:fiat to make callable-surface ABI validation cover return types and state mutability as well as names and input types, with any divergence rejecting the output. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose. Change a skill's Next Fiat job only when that exact frontier job completed; otherwise leave it unchanged.
<!-- marketplace-context:end -->

## Place in the collective

Lemma is a preparation step, not a retrieval system. Berean can use a pinned
document corpus built from its source-linked output, but Lemma does not embed,
index, retrieve, answer, grade, or promote an agent. Ariadne may later bind a
release to its evidence; that does not widen what the chunks themselves prove.

Synkrisis does not treat Lemma chunks as run observations or compare corpora.
Its current release only specifies a future comparison boundary and supplies a
command scaffold that refuses every operation.

Lemma turns Solidity compiler inputs and Markdown documents into JSONL chunks.
Each chunk uses the same schema and records enough source information for a
downstream system to distinguish quoted source text from assembled text.

It does not embed, index, retrieve, or answer from the chunks. Its only runtime
dependency is the exact interpreter in the suite
[pin](https://github.com/wildcat-finance/skills/blob/main/.python-version).
Solidity chunking also needs `solc`; the included wrapper can run the pinned
compiler with Docker or Podman.

The plugin and its canonical skill are both named `lemma`, giving the qualified
name `lemma:lemma` (`/lemma:lemma` in Claude Code). The repeated name keeps
discovery and invocation consistent with the rest of the marketplace.

## What it ships

- a Solidity chunker driven by the compiler AST;
- a Markdown chunker that splits on rendered heading structure;
- schema validation and an invented baseline corpus; and
- a pinned `solc` container wrapper for reproducible compiler output.

It stops after chunking. It does not embed, index, retrieve, or answer from the
output.

Its one skill is `lemma`, giving the qualified name `lemma:lemma`.

## Day to day

**Developers.** A documentation or verified-contract corpus needs source-linked
JSONL before it can enter a retrieval system. Lemma creates that file and
rejects chunks that fail its schema checks.

## Solidity

Pass one or more solc standard JSON input files:

```bash
python3 chunkers/solidity.py \
  --input path/to/standard-input.json \
  --solc ./solc-container \
  --include 'src/**' \
  --source-ref 'https://github.com/owner/repo@<commit>' \
  --out chunks.jsonl
```

Use `--solc solc` to call a local compiler. Add `--expect-solc 0.8.25` when the
build must refuse another compiler version.

## Markdown

Pass a document root and, for GitBook documentation, its `SUMMARY.md`:

```bash
python3 chunkers/markdown.py \
  --root docs \
  --summary SUMMARY.md \
  --exclude SUMMARY.md \
  --source-ref 'https://github.com/owner/repo@<commit>' \
  --out chunks.jsonl
```

Pass `--summary ''` for a tree without GitBook navigation. Use `--exclude`
for agent instructions, generated pages, or other files that should not enter
the corpus.

Both commands validate their output before writing it. A non-zero exit means no
JSONL file should be used.

## The record beside the chunks

Both chunkers take two more flags:

- `--source-ref REF` names what was chunked: a tag, a commit or a URL. It is
  required whenever `--out` is given. A run without it exits non-zero and
  writes nothing, because a corpus nobody can trace back to a source is the one
  thing a delivered corpus must not be. The ref is recorded as given, less any
  userinfo in a URL; nothing fetches it and nothing checks that it names a real
  object.
- `--provenance PATH` puts the record somewhere other than `provenance.jsonl`
  beside the file `--out` names.

A delivered corpus is therefore two files in one directory. `chunks.jsonl`
carries what a citation quotes; `provenance.jsonl` carries one line of JSON
saying what produced it: the schema identity, which chunker ran and at which
governed version, the source ref, a build identifier recomputed from the chunks
actually written, how many chunks are beside it, the digest of every input, the
selection (the include patterns and the source units present, selected and
excluded), and the compiler.

The compiler entry is the part worth reading twice. Solidity records the
`--solc` argument as given, the version the compiler reported for itself, and
either the `--expect-solc` pin or the reason nothing was pinned. A recorded
pin is named a prefix pin, because that is how the gate compares. Markdown
records that no compiler applies, with the reason. No field is ever written as
`unknown`: an absent value is recorded as an absence that says why.

Every chunk in `chunks.jsonl` also carries the source ref and the build
identifier, stamped by the pipeline above the chunker rather than by the
chunker itself.

## From a corpus to a dataset statement

Each chunker prints the flags Ariadne's `capture-dataset` needs for the corpus
it just wrote: the release directory, the producer and its governed version,
the include patterns, the coverage bounds with any gaps, and one input per
digested file. Copy them. The operator adds only `--name`, `--out` and either
`--first-release-reason` or the `--previous` release to compare against.

Solidity, run from `plugins/lemma`:

```bash
python3 chunkers/solidity.py \
  --input /tmp/w/standard-input.json \
  --solc solc \
  --expect-solc 0.8.35 \
  --include 'src/**' \
  --source-ref 'https://github.com/owner/repo@<commit>' \
  --out /tmp/w/corpus/chunks.jsonl

python3 ../ariadne/scripts/ariadne.py capture-dataset \
  --name my-solidity-corpus-v0 \
  --first-release-reason 'the first corpus built from this input' \
  --release /tmp/w/corpus \
  --producer-tool lemma \
  --producer-version 0.2.1 \
  --producer-command python3 \
  --producer-command chunkers/solidity.py \
  --parameter 'include=src/**' \
  --coverage-dimension 'source unit' \
  --coverage-start 1 \
  --coverage-end 4 \
  --input 'name=/tmp/w/standard-input.json,locator=https://github.com/owner/repo@<commit>,file=/tmp/w/standard-input.json' \
  --out /tmp/w/statement.json

python3 ../ariadne/scripts/ariadne.py verify /tmp/w/statement.json
```

`verify` exits zero, and the statement carries both `chunks.jsonl` and
`provenance.jsonl` under `dataset_subjects`, each with a digest and the second
with a record count of one.

Markdown takes the same shape with one difference: its recorded input paths are
relative to `--root`, so the capture runs from there.

```bash
python3 chunkers/markdown.py \
  --root /tmp/w/docs \
  --summary SUMMARY.md \
  --exclude SUMMARY.md \
  --source-ref 'https://github.com/owner/repo@<commit>' \
  --out /tmp/w/corpus-docs/chunks.jsonl

cd /tmp/w/docs
python3 /path/to/skills/plugins/ariadne/scripts/ariadne.py capture-dataset \
  --name my-docs-corpus-v0 \
  --first-release-reason 'the first corpus built from this tree' \
  --release /tmp/w/corpus-docs \
  --producer-tool lemma \
  --producer-version 0.2.1 \
  --producer-command python3 \
  --producer-command chunkers/markdown.py \
  --parameter 'include=**/*.md' \
  --coverage-dimension 'source unit' \
  --coverage-start 1 \
  --coverage-end 10 \
  --gap 'start=2,end=2,reason=present in the input and not selected under include **/*.md' \
  --input 'name=README.md,locator=https://github.com/owner/repo@<commit>,file=README.md' \
  --out /tmp/w/docs-statement.json
```

The chunker prints one `--input` per selected document; one is shown here.
Coverage reads the source unit dimension. The bounds span the sorted units the
input declared, and every excluded unit is a gap naming the pattern the
selection was made under, because an interval with no gaps reads as complete.

Lemma writes no statement and signs nothing. It records what produced a corpus
and stops there.

## Output

[`schema.py`](schema.py) defines the shared `Chunk` type. The main text fields
are:

- `display_text`: source text used for quotation;
- `model_text`: text prepared for model context;
- `embed_text`: text prepared for embedding; and
- `synthesised`: true when `display_text` was assembled and must not be treated
  as a verbatim quotation.

Build provenance is applied with `schema.stamp()` from the pipeline above
the chunker, which is why `chunk()` leaves those fields unset.

## Checks

Run the standard-library tests from `plugins/lemma`:

```bash
python3 tests/test_markdown.py
python3 tests/test_solidity.py
```

Compiler-dependent Solidity tests are opt-in:

```bash
python3 tests/test_solidity.py --solc ./solc-container
```

[`INVARIANTS.md`](INVARIANTS.md) records the guarantees, known limitations,
and reproducible baseline. `baseline/regenerate` rebuilds that baseline.

## Licence

Apache-2.0. See [LICENSE](LICENSE).
