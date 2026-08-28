# Baseline corpus

<!-- marketplace-context:start -->
> **Marketplace context: Lemma.** Lemma turns Solidity compiler input or Markdown trees into validated, source-linked JSONL chunks, keeping quotation text separate from model and embedding text. It does not embed, index, retrieve or answer; Berean is the adjacent unbuilt release discipline for a grounded protocol agent. **Current frontier:** Callable-surface ABI validation does not independently check return types or state mutability.
<!-- marketplace-context:end -->

A small invented corpus, used to produce the numbers recorded in
[`../INVARIANTS.md`](../INVARIANTS.md).

It exists because a baseline you cannot reproduce is not evidence. Everything
here is fabricated for the purpose: four Solidity sources describing a registry
that does not exist, and nine Markdown documents describing how to use it. None
of it corresponds to a deployed system, and the prose is written to be chunked
rather than to be read.

```bash
baseline/regenerate --solc /path/to/solc
```

`standard-input.json` is built from `solidity/src/` on each run rather than
committed, because that file embeds a copy of every source. A committed copy
would sit next to `src/` with nothing keeping the two in agreement, and the
failure is silent: you edit a contract, the chunker reads the stale copy, and
every chunk cites bytes no longer in the file it names. `standard_input.py`
does the build, and doubles as the shortest worked example of the input format
the Solidity chunker consumes.

## What it is chosen to exercise

The Solidity side covers an interface, an abstract base, a concrete contract
inheriting from it, and a library: natspec on declarations and on parameters,
custom errors, an event, an enum, a struct, a modifier, public immutables and a
public constant that compile to getters, an `@inheritdoc` override, and a
`using ... for` directive. That is enough for the surface chunk, the inheritance
attribution and the ABI cross-check to all have something to do.

The Markdown side is shaped like a GitBook: a `SUMMARY.md` with three nav
sections and a nested entry, headings at several levels, a fenced code block, an
HTML comment, a table, and a troubleshooting page written as standalone bold
paragraphs rather than headings. `SUMMARY.md` is excluded from the chunked set,
because it is navigation rather than content.

## The compiler is gated

The figures in `INVARIANTS.md` were recorded with solc 0.8.25, which is
what `solc-container`'s pinned digest resolves to. `regenerate` passes
`--expect-solc 0.8.25` by default, so a compiler that is not the pinned one
fails the run with a non-zero exit rather than quietly printing different
numbers.

If you change the digest in `solc-container`, change the default in
`regenerate` in the same commit, and re-record the figures.

```bash
baseline/regenerate --expect 0.8.26   # record against a different compiler
baseline/regenerate --no-expect       # see what an ungated run produces
```

## Regenerating after a change

If a change to either chunker moves these numbers, that is expected and the
recorded baseline should move with it in the same commit. If a change moves them
and you did not expect it, that is the signal this corpus exists to give you.
