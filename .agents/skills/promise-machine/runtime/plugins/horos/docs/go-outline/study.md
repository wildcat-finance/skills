# The Go outline extractor, the study

This run executes Horos's held frontier job, the first half of the
external-ingestion epoch: teach map to read Go, in the shape the TypeScript
extractor fixed. C++ follows in its own run, and the frontier is expected
to close mature after both.

## Assumptions

Proceeding on these unless corrected:

1. The extractor lives at `languages/go/go.py` behind the existing registry,
   covering `.go`. The output register, the confession contract and the
   evidence-bundle shape are the TypeScript extractor's, unchanged.
2. The differential oracle is tree-sitter's Go grammar (`tree-sitter` and
   `tree-sitter-go` in a scratchpad virtualenv, dev-time only, never a
   plugin or test dependency). The Go toolchain is absent on this machine,
   so the reference compiler is not available; tree-sitter is a
   battle-tested independent parser and the bundle names it plainly.
3. The corpus is a live external repository, per the epoch's purpose:
   ethereum/go-ethereum at `26d0b2171c17339bb8fd164d8ed6830738d3bf13`,
   1,421 `.go` files, already cloned shallow.
4. The completed job increments evolution: `horos-v4.2.1` becomes
   `horos-v5.2.1`, generation and epoch retained, and the next held job is
   the C++ extractor.

## 1. Problem statement

Go is far kinder to a lexer than TypeScript: strings never span lines
except raw backtick strings (which have no escapes at all), there is no
regex-versus-division ambiguity, and every top-level declaration is
keyword-led (`package`, `import`, `func`, `type`, `const`, `var`). The
extractor:

- Lexes line and block comments, interpreted strings, raw strings and
  rune literals; an unterminated construct confesses the remainder.
- Slices declarations verbatim: the package clause; imports (grouped
  blocks quoted first-line); functions and methods from `func` through the
  parameter list, receiver and result types, up to the body brace; `type`,
  `const` and `var` declarations, with parenthesised groups emitting one
  line per named member; struct and interface bodies skipped whole.
- Confesses anything else at statement position by line range, exactly
  as the TypeScript outliner does.

A working prototype means: the pinned Go fixture outline matches byte for
byte; the corpus run over all 1,421 files completes with zero crashes; the
differential against tree-sitter-go is recorded as a machine-checked bundle
with zero unconfessed misses and zero extras; and every suite and lint is
green.

## 2. Prior art

The TypeScript extractor fixes everything structural: the registry, the
lexer-then-recognisers shape, verbatim slicing, the confession footer, the
differential driver, the bundle format and its consistency tests. Go's own
`gofmt` discipline makes the corpus unusually regular, which the recogniser
list leans on and the confession catches when it fails. tree-sitter-go is
the oracle; the Go compiler's `go/parser` would be preferred but the
toolchain is absent, and the assumption section records that trade.

## 3. Constraints and non-goals

- Stdlib only in everything that ships; the venv stays in the scratchpad.
- No changes to scan, check, census, the boundary or the existing
  extractors beyond one registry line.
- Non-goals: cgo preambles beyond confession (a `import "C"` comment block
  is just a comment), generics-aware semantics (type parameters ride along
  verbatim in slices), struct field and interface method outlining (bodies
  are skipped whole this run), and build-tag interpretation.

## 4. Design options

**A. The TypeScript shape with a Go-sized lexer and keyword recognisers.**
Chosen. Trade: parenthesised groups need their own emitter, and skipping
struct and interface bodies understates types the way the boundary
understates a tree; the confession line and the differential hold it
honest.

**B. Line-regex sketch without a lexer.** Rejected before, rejected again:
a raw string holding `func main() {` derails it silently.

**C. Wait for a Go toolchain and use go/parser as oracle.** Rejected for
this run: it gates the epoch on a toolchain install nobody asked for;
tree-sitter is independent and present.

## 5. Risk register seed

- Raw strings have no escapes and can span lines; the lexer must treat a
  backslash inside them as a plain byte, pinned by test.
- Rune literals can hold `'"'` and `'\''`; both pinned.
- Grouped declarations (`const (` ... `)`) contain one name per line plus
  blank lines and comments; iota lines carry no type and must still emit.
- Methods carry receivers; the differential compares method names, so the
  name extractor must take the identifier after the receiver, not inside
  it.
- The oracle counts only the altitudes the outliner claims: top-level
  declarations and their grouped members, not function-body locals.
- Determinism, atomicity and the frozen fixture boundary all hold as
  before; the Python and TypeScript pinned fixtures must not move.

## 6. Glossary seeds

- Group: a parenthesised `import`, `type`, `const` or `var` block emitting
  one outline line per member.
- Receiver: the `(r *T)` between `func` and a method's name.
- Raw string: a backtick literal with no escapes, spanning lines freely.

## 7. Boundaries

- **Always.** Both suites and the three tree lints before a commit;
  imprimatur on every shipped document; pinned fixtures are the contract.
- **Ask first.** Any runtime dependency; struct-field outlining; touching
  another extractor's behaviour.
- **Never.** Import or execute scanned code; let the venv into the runtime
  or test path; report a corpus run that did not happen.

## 8. Success criteria

1. `python3 -m unittest discover -s tests` passes.
2. `python3 -m unittest discover -s plugins/horos/tests -t plugins/horos`
   passes, including the Go lexer, outliner and dispatch tests, with the
   Python and TypeScript fixtures untouched.
3. `python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests`
   and the ephoros equivalent exit clean.
4. Demo path: `python3 plugins/horos/skills/horos/scripts/horos.py map
   plugins/horos/examples/fixture-go/market.go` prints the pinned outline,
   and the committed differential bundle at
   `plugins/horos/docs/evidence/go-ethereum-outline.md` is machine-checked
   by the suite with zero unconfessed misses, zero extras, zero crashes.

## 9. Sources

The v4.2.1 epoch row and the maintainer's directions this session. The
TypeScript extractor, its differential driver and its bundle as the fixed
shape. The go-ethereum clone at
`26d0b2171c17339bb8fd164d8ed6830738d3bf13`. The Go language specification's
lexical rules for strings, runes and comments. tree-sitter-go as oracle.
