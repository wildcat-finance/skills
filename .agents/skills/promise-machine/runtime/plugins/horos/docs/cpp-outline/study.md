# The C++ outline extractor, the study

This run executes Horos's held frontier job, the second half of the
external-ingestion epoch: teach map to read C++, in the extractor shape now
fixed twice. At its close the frontier is expected to go mature, absent
further evidence, per the maintainer's direction on the ledger.

## Assumptions

Proceeding on these unless corrected:

1. The extractor lives at `languages/cpp/cpp.py` behind the registry,
   covering `.cpp`, `.cc`, `.cxx`, `.hpp`, `.hh` and `.h`. A C header
   under `.h` outlines through the same recognisers; C is close enough to
   the subset the outliner claims that the confession absorbs the rest.
2. The differential oracle is tree-sitter's C++ grammar, already in the
   scratchpad virtualenv, dev-time only. clang is present on this machine
   but its AST dump demands compilable translation units with resolvable
   includes, which an ingested tree does not owe us; tree-sitter parses
   files standalone, exactly as the outliner must.
3. The corpus is ethereum/solidity at
   `60dfdc91f476fcab91513f5aa6694c0fdc6271ed`, 842 C++ files, already
   cloned shallow.
4. The compared altitudes are declared narrowly, because C++ declarator
   grammar is the hardest of the four languages: named types (class,
   struct, union, enum), namespaces, and named functions and methods,
   excluding operator overloads and destructors on both sides. Variables
   and fields are outlined but not differentially compared; the bundle
   says so.
5. The completed job increments evolution: `horos-v5.2.1` becomes
   `horos-v6.2.1`, generation and epoch retained. If the differential
   closes with zero unconfessed misses and zero extras at the declared
   altitudes, the frontier closes mature with `None -- mature`; any other
   outcome holds a job naming the residue.

## 1. Problem statement

C++ is the hardest lexing target of the four languages and the one where
the confession contract earns most. The extractor:

- Lexes line and block comments, strings and character literals with
  escapes, raw strings with custom delimiters (`R"delim(...)delim"` and
  its encoding prefixes), and preprocessor directives as their own span
  kind, honouring backslash continuations.
- Slices declarations verbatim at translation-unit, namespace and class
  depth: namespaces (recursed), `extern "C"` blocks (recursed), class,
  struct, union and enum heads with their bodies walked for members,
  template prefixes riding into the declaration they introduce, using and
  typedef lines, function definitions and declarations from their first
  token to the body brace or semicolon, and variables cut before their
  initialisers. `#include` and `#define` heads are quoted from the
  preprocessor spans; other directives are skipped silently.
- Confesses everything else by line range, and confesses the remainder on
  any unterminated literal.

A working prototype means: the pinned C++ fixture outline matches byte for
byte; the corpus run over all 842 files completes with zero crashes; the
differential at the declared altitudes is recorded with zero unconfessed
misses and zero extras; and every suite and lint is green.

## 2. Prior art

The TypeScript and Go extractors fix the shape end to end; the class-member
dispatch is the TypeScript one generalised. Preprocessor conditionals are
the known structural hazard (an `#if`/`#else` pair can leave brace depth
lying); the lexer removes directives from the structural mask entirely,
which contains the damage to the confession the differential will price.
universal-ctags and tree-sitter-cpp are the outside ancestors.

## 3. Constraints and non-goals

- Stdlib only in everything that ships; the venv stays in the scratchpad.
- No changes to the other extractors, scan, check or census.
- Non-goals: preprocessor evaluation, macro expansion, template semantics,
  overload resolution, operator and destructor naming in the differential,
  Objective-C and CUDA dialects, and any promise that a C header outlines
  as well as a C++ source file: the confession line is the contract.

## 4. Design options

**A. The fixed extractor shape with directives lexed out of the mask.**
Chosen. Trade: code hidden behind `#if` branches still counts toward brace
structure only as written, so a conditional that unbalances braces
mis-slices until the next recogniser; the confession and the corpus price
it, and the bundle reports it.

**B. A preprocessor-aware structural pass.** Rejected: evaluating
conditions is compiler work, and guessing them is the sketch this
marketplace refuses.

**C. clang as oracle.** Rejected: it demands resolvable includes an
ingested tree does not owe us; tree-sitter parses standalone files, which
is the outliner's own situation.

## 5. Risk register seed

- Raw-string delimiters are arbitrary (`R"x(...)x"`); the scanner must
  match the exact close sequence, pinned with a nested-parenthesis case.
- A directive with a backslash continuation is one span; `#define X {`
  must not leak a brace into the mask, pinned.
- Class members dispatch on the first structural character at depth zero,
  as in TypeScript; constructors and conversion operators have no return
  type and must still slice.
- Access labels (`public:`) are member noise, skipped without confession.
- Template prefixes (`template <typename T>`) attach to the following
  declaration's slice, including multiline forms.
- The differential's altitude declaration carries the comparison: both
  sides must exclude operators and destructors, and the driver must
  reconcile confessed regions exactly as before.

## 6. Glossary seeds

- Directive: one preprocessor line including its continuations, lexed as
  its own span kind and absent from the structural mask.
- Raw string: `R"delim(...)delim"` with an arbitrary delimiter and no
  escapes.
- Declared altitudes: the set of declaration kinds the differential
  compares, named in the bundle.

## 7. Boundaries

- **Always.** Both suites and the three tree lints before a commit;
  imprimatur on every shipped document; pinned fixtures are the contract.
- **Ask first.** Any runtime dependency; widening the compared altitudes;
  Objective-C or CUDA suffixes.
- **Never.** Import or execute scanned code; evaluate preprocessor
  conditions by guesswork; report a corpus run that did not happen; close
  mature over an unexplained differential residue.

## 8. Success criteria

1. `python3 -m unittest discover -s tests` passes.
2. `python3 -m unittest discover -s plugins/horos/tests -t plugins/horos`
   passes, including the C++ lexer and outliner tests, with the Python,
   TypeScript and Go fixtures untouched.
3. `python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests`
   and the ephoros equivalent exit clean.
4. Demo path: `python3 plugins/horos/skills/horos/scripts/horos.py map
   plugins/horos/examples/fixture-cpp/market.hpp` prints the pinned
   outline, and the committed differential bundle at
   `plugins/horos/docs/evidence/solidity-outline.md` is machine-checked by
   the suite with zero unconfessed misses and zero extras at the declared
   altitudes, zero crashes.

## 9. Sources

The v5.2.1 ledger row holding this job and the v4.2.1 epoch behind it. The
TypeScript and Go extractors and their differential bundles as the fixed
shape. The solidity clone at `60dfdc91f476fcab91513f5aa6694c0fdc6271ed`.
tree-sitter-cpp as oracle. The C++ standard's lexical rules for raw
strings and the preprocessor's continuation rule.
