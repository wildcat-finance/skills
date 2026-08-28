---
name: lemma
description: Turn Solidity solc standard JSON inputs or Markdown document trees into validated JSONL chunks with source locations and separate quotation, model, and embedding text. Use when asked to run Lemma, invoke lemma:lemma, prepare Solidity or Markdown for retrieval, generate citation-aware chunks, or inspect Lemma output. Do not use it to embed, index, retrieve, or answer from the chunks.
metadata:
  version: "0.2.1"
---

<p align="center">
  <img src="../../assets/characters/lemma.png" width="1200">
</p>

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

Synkrisis does not treat Lemma chunks as run observations or compare corpora.
Its current release specifies a separate future comparison boundary and ships
a command scaffold that refuses every operation.

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
  --source-ref 'https://github.com/owner/repo@<commit>' \
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
  --source-ref 'https://github.com/owner/repo@<commit>' \
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

## Hand the corpus to Ariadne

`--source-ref` is required whenever `--out` is given. A run without it exits
non-zero and writes nothing, because a corpus nobody can trace back to a source
is the one thing a delivered corpus must not be.

A delivered corpus is two files in one directory: `chunks.jsonl` and the
`provenance.jsonl` record beside it, which carries the source ref, the digest
of every input, the selection and the compiler identity. The chunker then
prints the flags that match what it wrote. Copy them into Ariadne's capture,
which binds that directory into a dataset statement:

```bash
python3 plugins/ariadne/scripts/ariadne.py capture-dataset \
  --name <a name for the dataset> \
  --first-release-reason <why there is nothing to compare against> \
  <the flags the chunker printed> \
  --out /absolute/path/to/statement.json
```

Four flags are the operator's: `--name`, `--out`, and either
`--first-release-reason` or the `--previous` and `--previous-name` pair that
names an earlier release. Everything else was printed, `--release` included, so
compose nothing by hand. The Markdown chunker records its input paths relative
to `--root`, so run the capture from there.

Lemma writes no statement and signs nothing. It records what produced a corpus
and stops. Binding those bytes to a release, and attesting to them, belong to
Ariadne, and the record says the source ref was asserted by its caller rather
than resolved.

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

### lemma-corpus-provenance

- Promise: A successful chunk run delivers a corpus of two files whose provenance record binds the asserted source ref, the governed chunker version, the digest of every input, the selection and the compiler identity to a build identifier recomputed from the chunks actually written.
- Evidence: The provenance record beside the corpus, the source ref as given less any URL userinfo, the digested inputs, the include patterns with the source units present, selected and excluded, the compiler block, and the build identifier recomputed from the delivered file.
- Evidence classes: checked, recorded, recomputed
- Boundary: The record does not establish that the ref names a real object, that the ref was clean, that the compiler was honest about its own version, that an ungated compiler was the intended one, or that a citation out of the corpus is faithful.
- Authorises: Handing the corpus directory to a dataset capture that binds its bytes, and reading the recorded origin, inputs and compiler as what the run was told and observed.
- Consequence: 1
- Refuses: Writing a corpus with no recorded origin, recording a value as `unknown`, naming a prefix pin as an exact one, or leaving a record beside chunks it does not describe.
- Recovery: Supply the missing ref, remove the record the directory already holds or point `--provenance` at it, and rerun the chunker.
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
