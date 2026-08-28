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
  --out chunks.jsonl
```

Pass `--summary ''` for a tree without GitBook navigation. Use `--exclude`
for agent instructions, generated pages, or other files that should not enter
the corpus.

Both commands validate their output before writing it. A non-zero exit means no
JSONL file should be used.

## Output

[`schema.py`](schema.py) defines the shared `Chunk` type. The main text fields
are:

- `display_text`: source text used for quotation;
- `model_text`: text prepared for model context;
- `embed_text`: text prepared for embedding; and
- `synthesised`: true when `display_text` was assembled and must not be treated
  as a verbatim quotation.

The calling pipeline can add build provenance with `schema.stamp()`.

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
