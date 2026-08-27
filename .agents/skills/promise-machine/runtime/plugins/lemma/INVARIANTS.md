# Invariants

<!-- marketplace-context:start -->
> **Marketplace context: Lemma.** Lemma turns Solidity compiler input or Markdown trees into validated, source-linked JSONL chunks, keeping quotation text separate from model and embedding text. It does not embed, index, retrieve or answer; Berean is the adjacent unbuilt release discipline for a grounded protocol agent. **Current frontier:** Callable-surface ABI validation does not independently check return types or state mutability.
<!-- marketplace-context:end -->

This document states the current chunker guarantees, the classes of defect
adversarial review has found in them, and the residual weak points. A past
finding is recorded where it explains a non-obvious design decision or a
regression fixture that would otherwise look arbitrary, and dropped where it
does not.

The central risk is a citation that looks verified while pointing at the wrong
bytes, source, contract, or rendered fragment. A crash is safer because the build
stops.

## Current invariants

### Shared schema and citation invariants

**I1: display text is byte-exact source.** For every chunk with
`synthesised: false`, `display_text` is sliced from the source bytes and decoded
after slicing. Source offsets from solc are byte offsets, not Python character
offsets.

**I2: assembled chunks are labeled.** Contract headers, callable surfaces, and
document indexes combine multiple source regions. They carry
`synthesised: true` and cannot be rendered as verbatim quotes.

**I3: IDs are unique after source namespacing.** Solidity IDs include path,
contract, signature, and canonical parameter types. Markdown duplicate headings
are disambiguated. The merged pipeline rejects collisions across sources.

**I4: evidence and model input remain separate.** Comment removal changes
`model_text`; it never changes `display_text`. `embed_text` is composed from
structured state rather than parsed back from a previous rendered string.

**I5: schema validation is fatal.** Empty required fields, invalid source types
or tiers, duplicate IDs, incorrect synthesized flags, empty visible model text,
and oversize model or embedding text stop the build.

**I6: provenance is pipeline-owned.** Chunkers emit source-local facts. The
calling pipeline applies corpus build ID, resolved source ref, tier, protocol
version, deployment status, and per-document legal metadata, via
`schema.stamp()`.

### Solidity invariants

**S1: deployed inputs define the corpus.** The chunker consumes every configured
deployment `standard-input.json`. Compilation errors, unexpected solc
versions when `--expect-solc` is used, invalid source-unit paths, and empty
selections are fatal.

**S2: comment removal preserves code.** Strings containing comment delimiters,
Unicode and hex literals, escaped quotes, division, and CR line endings survive.
Only the documentation range attached by solc is retained as natspec; mid-body
`///` and `/** */` comments are ordinary comments.

**S3: signatures distinguish semantic types.** Canonical signatures preserve
struct, enum, contract, fully qualified type, array, and payable-address
distinctions while removing data-location syntax.

**S4: inheritance follows compiler order.** Exposure walks
`linearizedBaseContracts` and keeps the first definition of a signature. Public
state-variable getters occupy their signature slot, derived overrides shadow
bases, and constructors are not inherited.

**S5: compilation-unit merging only adds evidence.** Exposure is unioned across units
and override state is ORed. Absence from a separately deployed unit does not
erase evidence from another unit.

**S6: callable surfaces agree with the ABI.** Public and external functions and
getters are compared with the compiler ABI by full input signature. A divergence
stops the build.

**S7: deduplicated declarations remain retrievable.** Identical model text may
fold into one chunk, but alias IDs and breadcrumbs are preserved in structured
detail and embedding text.

### Markdown invariants

**M1: only rendered structure creates boundaries.** Headings inside code fences,
HTML comments, raw HTML blocks, inline code, lazy list continuation, and lazy
blockquote continuation do not become section boundaries.

**M2: hidden comments do not enter model text.** Comment bytes are removed while
visible text on the same line survives. Comment syntax inside a valid code span
remains visible. An unmatched or escaped backtick is literal text rather than an
unbounded hiding delimiter.

**M3: anchors follow renderer behavior.** Inline markup is reduced to rendered
text before slugging. Duplicate suffixes count every parsed heading, including
headings filtered from chunk output. Page titles have no fragment, and the
renderer-specific handling for entities, mentions, punctuation, leading digits,
and length limits is reproduced.

**M4: navigation failures are explicit.** A requested unreadable `SUMMARY.md`
or a hierarchy that places zero emitted documents is fatal. Included documents
missing from navigation and navigation entries missing from output are reported.

**M5: short documents do not disappear silently.** Section-size filtering may
remove noise, but a document with no surviving section is emitted as a
whole-document chunk. Coverage counts emitted documents rather than discovered
filenames.

**M6: pinned refs determine all bytes.** Symlinked documents, symlinked
navigation, paths outside the root, and unreadable sources are rejected.

**M7: template chrome does not enter model text.** GitBook `{% … %}` tag bytes
are removed from model text wherever they sit on a line, including after visible
prose. The visible prose they wrap survives. A live corpus chunk
carried `{% hint style="info" %}` sharing a line with prose into a delivered
answer. Tag syntax inside fenced code or a valid code span remains visible
example markup, and an unclosed `{%` is literal text rather than an unbounded
hiding delimiter. Display text still quotes the file byte-for-byte: the strip
happens in span selection for model text, never in citation bytes.

## Why the implementation has these shapes

The following defect classes were found and fixed under adversarial review.
Each fix has a regression fixture in the current suites.

### Byte and character offsets diverge

Solc reports byte offsets. Slicing decoded Python strings corrupted Solidity
after non-ASCII text while still producing plausible code. A later variant used
a byte length as a character length when preserving natspec and could extend the
trusted documentation range into a function body. Source and documentation
slicing now remain in bytes until the selected region is decoded.

### Self-derived checks can certify the wrong object

Several green checks measured a proxy rather than the production value:

- the oversize guard measured `model_text` although the embedder receives the
  larger `embed_text`;
- callable-surface validation compared ABI names instead of signatures;
- Markdown hierarchy coverage counted discovered files rather than emitted
  documents; and
- merge tests reproduced the merge loop instead of calling it.

Current validation targets the actual embedded string, full ABI input
signatures, emitted document paths, and production entry points.

### Re-parsing generated text creates attacker-controlled delimiters

Embedding text once reconstructed its base by splitting on a human-readable
marker that natspec could contain. Text after the marker disappeared from
retrieval while the citation remained intact. Embedding text is now composed
from the chunk's model text, breadcrumb, exposure, and alias fields on every
update.

### Handwritten syntax approximations need fail-safe direction

The Markdown scanner historically mistook raw HTML, setext thematic breaks,
lazy continuation, multi-line code spans, and closing tags for structure. The
current state machine covers the constructs that affect heading or comment
visibility. Where inline interpretation remains ambiguous, it resolves toward
not-code, which can remove visible text from model context but does not admit
reader-hidden instructions.

### Compiler facts should replace lexical guesses

Natspec was initially identified by `///` or `/** */` syntax. That preserved
documentation-shaped comments in function bodies. Solc has already decided
which documentation attaches to a declaration, so the chunker now preserves
only the compiler-reported documentation range.

The same principle applies to inheritance order and ABI surfaces: compiler
linearization and ABI output are stronger evidence than a parallel source-level
approximation.

### Fail-open selection creates plausible incomplete corpora

Typoed include patterns, unreadable navigation, zero emitted documents, and
empty model text once produced successful commands. Each now stops the build.
Warnings remain for non-fatal coverage information, but absence of the selected
corpus is not a warning condition.

## Recorded baseline

Produced by `baseline/regenerate` over the synthetic corpus in `baseline/`, with
solc 0.8.25, the version `solc-container`'s pinned digest resolves to. The
corpus is invented and small; the point is that these numbers can be reproduced
from a clone rather than taken on trust.

The Solidity figures depend on the compiler, because the AST is the compiler's
output. `regenerate` therefore passes `--expect-solc`, so a compiler change
fails the run rather than quietly printing different numbers (S1). As it
happens this corpus produces byte-identical chunks on 0.8.25 and 0.8.26, which
says the corpus does not exercise a difference between those two releases, not
that the output is compiler-independent.

```text
Solidity
  25 chunks from 1 compilation unit
  0 duplicate bodies folded; 0 alias IDs retained
  5 synthesised chunks
  13 chunks attributed to a concrete contract
  0 unreachable public/external functions
  model p99 761 characters; maximum 761; limit 24,000
  by kind: Enum 1, Error 3, Event 2, Function 12, Modifier 1, Struct 1,
           contract 2, interface 1, library 1, surface 1

Markdown
  38 chunks from 9 documents
  9/9 emitted documents placed
  9 synthesised document indexes
  34 chunks placed in the SUMMARY hierarchy
  median 141 characters; p99 568; maximum 568
```

A change that moves these figures should move the recorded baseline in the same
commit. A change that moves them unexpectedly is what the corpus is for.

## A note on numbering

The `S*` and `M*` identifiers above number the *invariants* in this document.
They are not the same scheme as the case identifiers the test suites print:
`test_solidity.py` prints `I4` through `I29`; `test_markdown.py` prints `M1`
through `M24`.
The Markdown prefix collides by accident. An invariant is usually covered by
several cases rather than one, so do not read `M3` here as `M3` there.

Both suites print a per-run assertion total. Treat it as a regression signal;
adding source legitimately changes it.

## Residual weak points

**Include matching uses `fnmatch`.** Patterns such as `src/**` do not have shell
globstar semantics. The manifest's current selections are tested, but every
pattern change should inspect the resolved file list.

**Assembly has no special chunk.** Inline assembly remains inside its enclosing
function and may embed poorly when opcode-heavy.

**ABI comparison is not total.** Callable-surface validation compares callable
names and input types. It does not independently check return types or state
mutability.

**The Markdown inline scanner is intentionally incomplete.** It is not a full
CommonMark inline parser; link titles, autolinks, and reference definitions are
not modeled. The covered boundary is hidden text and heading structure.

**Anchor behavior is empirical.** GitBook publishes no slug specification.
`verify_anchors.py` compares pinned sources with the live site through the same
`assign_anchors()` implementation. A live site that has advanced beyond the
pinned ref reduces the comparable denominator, so fewer verified pages indicates
docs drift rather than proof of correctness.

**Whole-document fallbacks use a different grain.** A short document emitted as
one chunk has no overlapping sections, but retrieval quality for these coarse
chunks has not been measured separately.

**Compiler pinning depends on invocation.** `--expect-solc` checks a version and
the build records the compiler. Only `./solc-container` pins the compiler
artifact by image digest; a developer can deliberately pass a local binary.

**The oversize limit has headroom rather than operational history.** The current
maximums are well below the limit. Synthetic fixtures exercise rejection, but no
pinned source has approached it.

## Verification commands

```bash
python3 tests/test_markdown.py
python3 tests/test_solidity.py --solc ./solc-container
```

Run the renderer fit after a docs or platform change:

```bash
python3 tools/verify_anchors.py --help
```
