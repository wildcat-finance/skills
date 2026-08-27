---
name: lemma
description: Turn Solidity solc standard JSON inputs or Markdown document trees into validated JSONL chunks with source locations and separate quotation, model, and embedding text. Use when asked to run Lemma, invoke lemma:lemma, prepare Solidity or Markdown for retrieval, generate citation-aware chunks, or inspect Lemma output. Do not use it to embed, index, retrieve, or answer from the chunks.
metadata:
  version: "0.1.1"
---

# Lemma

## Frontier

Lemma owns its own chunking and validation frontier, not Hexaemeron's delivery or
Solidity frontier. Its version, held target, next job, and maturity
state live in [EVOLUTION.md](EVOLUTION.md). Do not recommend or run
another frontier pass after that ledger becomes mature.

<!-- marketplace-context:start -->
## Where this sits

Lemma turns Solidity compiler input or Markdown trees into validated, source-linked JSONL chunks with quotation, model, and embedding text kept separate.

**Current frontier.** Callable-surface ABI validation does not independently check return types or state mutability.
<!-- marketplace-context:end -->

Use Lemma to create chunks. Stop at the JSONL output unless the user separately
asks for another system to consume it. Berean may use a pinned corpus prepared
from the output, and Ariadne may later bind a release to evidence; Lemma itself
does not embed, index, retrieve, answer, evaluate, or attest.

`$SKILL_DIR` is the directory containing this file. Resolve `$PLUGIN_ROOT` as
`$SKILL_DIR/../..` and run the bundled commands from there.

## Choose the chunker

- Use `chunkers/solidity.py` for one or more solc standard JSON input files.
- Use `chunkers/markdown.py` for a directory of Markdown documents.
- If the request is only to inspect or validate an existing JSONL file, read
  `schema.py` and apply its `Chunk` and `validate()` contract. Do not rerun a
  chunker without its source input.

Read the target repository's instructions before writing output. Keep generated
JSONL outside the plugin directory unless the plugin repository itself is the
named target.

## Chunk Solidity

Prefer the included pinned compiler wrapper when Docker or Podman is available:

```bash
cd "$PLUGIN_ROOT"
python3 chunkers/solidity.py \
  --input /absolute/path/to/standard-input.json \
  --solc ./solc-container \
  --include 'src/**' \
  --out /absolute/path/to/chunks.jsonl
```

Repeat `--input` to merge compilation units and repeat `--include` for more
source patterns. Use `--expect-solc VERSION` when the requested corpus pins a
compiler version. Use `--solc solc` only when the user asks for a local compiler
or the container runtime is unavailable and the local compiler version is
acceptable.

The first container run may fetch the pinned image. The compiler process itself
runs without network access.

## Chunk Markdown

For a GitBook tree:

```bash
cd "$PLUGIN_ROOT"
python3 chunkers/markdown.py \
  --root /absolute/path/to/docs \
  --summary SUMMARY.md \
  --exclude SUMMARY.md \
  --out /absolute/path/to/chunks.jsonl
```

Pass `--summary ''` when the tree has no GitBook navigation. Add an `--exclude`
for every instruction file, generated directory, or unrelated subtree that
must not enter the corpus. When a compatible manifest already declares the
exclusions, pass it with `--manifest` and select its source with `--source`.

Markdown anchors follow GitBook behavior. Do not claim that they match another
renderer without checking that renderer separately.

## Accept the result

Both chunkers validate before writing. Accept the JSONL only when the command
exits zero and reports that it wrote the requested file. On failure, report the
named error and do not use an earlier or partial output.

Preserve these distinctions downstream:

- `display_text` holds source text used for quotation;
- `model_text` holds text prepared for model context;
- `embed_text` holds text prepared for embedding; and
- `synthesised: true` means the chunk is assembled and is not a verbatim quote.

Read [`INVARIANTS.md`](../../INVARIANTS.md) when changing the chunkers, judging a
guarantee, or investigating unexpected output. Run the two bundled test files
after any code change.

## Promise Machine contract

### lemma-solidity-chunks

- Promise: A successful Solidity chunk run emits schema-valid JSONL whose chunks resolve to the named standard-JSON sources and preserve separate quotation, model and embedding text.
- Evidence: The exact compiler inputs, selected includes, compiler identity and output, source locations, chunk records and successful built-in validation before write.
- Evidence classes: checked, recomputed
- Boundary: The output does not establish source truth, retrieval quality, semantic completeness, independent ABI return or mutability validation, or correctness under another compiler.
- Authorises: Use of the generated JSONL as source-linked retrieval material for the pinned Solidity compilation inputs.
- Consequence: 1
- Refuses: Writing or using partial output after compiler, source-location, schema, include or expected-version failure.
- Recovery: Correct the pinned input, include set or compiler selection, remove the failed output and rerun the chunker.
- Exceptions: none

### lemma-markdown-chunks

- Promise: A successful Markdown chunk run emits schema-valid JSONL whose chunks resolve to the selected document tree and preserve source locations, exclusions and synthesised-text labels.
- Evidence: The exact Markdown tree, navigation or manifest, exclusion set, GitBook anchor method, chunk records and successful built-in validation before write.
- Evidence classes: checked, recomputed
- Boundary: The output does not establish document truth, corpus completeness outside the selected tree, compatibility with another renderer, retrieval quality or answer correctness.
- Authorises: Use of the generated JSONL as source-linked retrieval material for the named Markdown corpus.
- Consequence: 1
- Refuses: Including excluded or escaped content, hiding a synthesised chunk as quotation, or using partial output after parsing or validation failure.
- Recovery: Correct the root, navigation, manifest or exclusions, remove the failed output and rerun the chunker.
- Exceptions: none

### lemma-chunk-validation

- Promise: A successful direct schema validation establishes that every supplied record satisfies Lemma's `Chunk` shape and field invariants.
- Evidence: The exact JSONL records, `schema.py` contract, per-record validation and zero validation failures.
- Evidence classes: checked
- Boundary: Schema validation does not reproduce chunks without their source input or establish that locations, text and digests match an unavailable corpus.
- Authorises: Structural inspection or hand-off of the existing JSONL with its source-verification status stated separately.
- Consequence: 0
- Refuses: Rechunking without source input or describing schema-valid records as source-verified when their corpus was not checked.
- Recovery: Obtain the named source input and rerun the appropriate chunker, or report the result as schema-only validation.
- Exceptions: none
