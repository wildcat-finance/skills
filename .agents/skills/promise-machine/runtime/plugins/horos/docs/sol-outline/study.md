# The Solidity outline extractor, the study

This run executes the first of the reopened frontier's three named jobs:
teach map to read Solidity, in the extractor shape now fixed three times.
The classifier refinement and the three-repository boundary marking follow
in their own runs.

## Assumptions

Proceeding on these unless corrected:

1. The extractor lives at `languages/solidity/solidity.py` behind the
   registry, covering `.sol`. The output register, confession contract and
   bundle shape are unchanged from the other extractors.
2. The differential oracle is tree-sitter's Solidity grammar
   (`tree-sitter-solidity`, already in the scratchpad virtualenv, dev-time
   only). The corpus is the v2-protocol clone at
   `c7be4039f8f383a9dda4e45f63331c17d63f9ed9`: 151 `.sol` files, contracts
   and Foundry tests alike.
3. Lemma's Solidity chunker (`plugins/lemma/chunkers/solidity.py`) is the
   in-repo prior art for the comment-and-string discipline; its
   `strip_comments(code, keep_ranges=())` walks the same hazards. Horos
   does not import it: the extractors are self-contained by pattern, and
   the two skills ship independently.
4. The completed job increments evolution: `horos-v6.2.2` becomes
   `horos-v7.2.2`, generation and epoch retained, and the next held job is
   the classifier refinement from the maintainer's committed specification.

## 1. Problem statement

Solidity lexes like a small C++ without the preprocessor: line and block
comments, single- and double-quoted strings with escapes, hex and unicode
string literals, and no regex or raw-string ambiguity at all. Its
declarations are keyword-led like Go's: `pragma`, `import`, `contract`,
`interface`, `library`, `abstract contract`, `function`, `constructor`,
`modifier`, `event`, `error`, `struct`, `enum`, `type`, `using`, and
state-variable declarations inside contract bodies.

The extractor:

- Lexes comments and all string forms; an unterminated literal confesses
  the remainder.
- Slices declarations verbatim: pragma and import lines; contract,
  interface, library and abstract-contract heads to their body brace, with
  inheritance lists riding along, then bodies walked for members; function,
  constructor, receive, fallback and modifier heads through their parameter
  lists and attribute chains up to the body brace or semicolon; event,
  error, struct, enum, type and using declarations; state variables cut
  before their initialisers.
- Confesses anything else at statement position by line range, exactly as
  the other extractors do.

A working prototype means: the pinned fixture outline matches byte for
byte; the corpus run over all 151 files completes with zero crashes; the
differential against tree-sitter-solidity is recorded as a machine-checked
bundle with zero unconfessed misses and zero extras at declared altitudes;
and every suite and lint is green.

## 2. Prior art

The three shipped extractors fix everything structural. Lemma's Solidity
chunker and Pandects' stripper tests pin the comment-and-string traps in
this exact language, in this exact marketplace. tree-sitter-solidity is the
oracle; solc's own AST would demand import resolution the ingested tree
does not owe us, the same trade the C++ study recorded.

## 3. Constraints and non-goals

- Stdlib only in everything that ships; the venv stays in the scratchpad.
- No changes to the other extractors, scan, check or census.
- Non-goals: assembly block internals (`assembly { ... }` bodies are
  skipped whole like any body), NatSpec interpretation (comments are
  comments), version-pragma semantics, and Yul as a separate suffix.

## 4. Design options

**A. The fixed extractor shape with Go-style keyword recognisers.** Chosen.
Trade: recall is bounded by the recogniser list; unusual top-level
constructs confess rather than slice, and the differential prices it.

**B. Reuse Lemma's chunker inside Horos.** Rejected: a cross-plugin import
couples two independently shipped skills for fifty lines of lexer; the
pattern stays, the code does not.

**C. solc as oracle.** Rejected: import resolution and version pinning an
ingested tree does not owe us; tree-sitter parses standalone files.

## 5. Risk register seed

- Hex and unicode string literals (`hex"00ff"`, `unicode"..."`) lex as
  strings with their prefixes, pinned by test.
- Function attribute chains (visibility, mutability, `virtual`,
  `override(A, B)`, custom modifiers with arguments) ride in the head
  slice up to the body brace or semicolon, pinned with a multiline case.
- `using X for Y;` and file-level `type U is V;` slice whole.
- An `unchecked { ... }` or `assembly { ... }` block inside a body never
  reaches the walker: bodies are skipped whole from the head's brace.
- The declared altitudes for the differential: contract-level types
  (contract, interface, library), their members (functions, constructors
  treated as named by their contract? no: constructors are anonymous and
  excluded on both sides, like C++ destructors), events, errors, structs,
  enums, and file-level functions, errors, structs and enums. State
  variables outlined but not compared, like C++ fields.
- The corpus's Foundry tests import forge-std from uninitialised
  submodules; imports are lines, not resolutions, so nothing breaks.

## 6. Glossary seeds

- Attribute chain: everything between a function's parameter list and its
  body brace or semicolon.
- Declared altitudes: the declaration kinds the differential compares,
  named in the bundle.

## 7. Boundaries

- **Always.** Both suites and the three tree lints before a commit;
  imprimatur on every shipped document; pinned fixtures are the contract.
- **Ask first.** Any runtime dependency; widening the compared altitudes;
  a Yul suffix.
- **Never.** Import or execute scanned code; import Lemma's chunker; report
  a corpus run that did not happen.

## 8. Success criteria

1. `python3 -m unittest discover -s tests` passes.
2. `python3 -m unittest discover -s plugins/horos/tests -t plugins/horos`
   passes, including the Solidity tests, with the other four fixtures
   untouched.
3. `python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests`
   and the ephoros equivalent exit clean.
4. Demo path: `python3 plugins/horos/skills/horos/scripts/horos.py map
   plugins/horos/examples/fixture-sol/Market.sol` prints the pinned
   outline, and the committed differential bundle at
   `plugins/horos/docs/evidence/v2-protocol-outline.md` is machine-checked
   by the suite with zero unconfessed misses, zero extras, zero crashes.

## 9. Sources

The v6.2.2 epoch row and the maintainer's reopening directive. The three
shipped extractors and their bundles. Lemma's Solidity chunker and
Pandects' stripper tests as in-repo prior art. The v2-protocol clone at
`c7be4039f8f383a9dda4e45f63331c17d63f9ed9`. tree-sitter-solidity as oracle.
