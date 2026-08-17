# Lemma

<!-- marketplace-context:start -->
## In one line

Lemma turns Solidity compiler input or Markdown trees into validated, source-linked JSONL chunks, keeping quotation text separate from model and embedding text.

**Try something else when.** It does not embed, index, retrieve or answer; Berean is the adjacent unbuilt release discipline for a grounded protocol agent.

**Current frontier.** Callable-surface ABI validation does not independently check return types or state mutability.

**Next Fiat job.** Use /hexaemeron:fiat to make callable-surface ABI validation cover return types and state mutability as well as names and input types, with any divergence rejecting the output. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose. Change a skill's Next Fiat job only when that exact frontier job completed; otherwise leave it unchanged.
<!-- marketplace-context:end -->

Lemma turns Solidity compiler inputs and Markdown documents into JSONL chunks.
Each chunk uses the same schema and records enough source information for a
downstream system to distinguish quoted source text from assembled text.

It does not embed, index, retrieve, or answer from the chunks. Python 3.10 or
later is the only runtime dependency. Solidity chunking also needs `solc`; the
included wrapper can run the pinned compiler with Docker or Podman.

The plugin is Lemma; its skill is `chunk`, giving the qualified name
`lemma:chunk` (`/lemma:chunk` in Claude Code). The name states the operation
instead of repeating the plugin name in the call.
`lemmatise` was avoided because it already means reducing words to dictionary
forms in natural-language processing, which this plugin does not do.

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
