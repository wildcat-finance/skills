# The TypeScript outline extractor, the study

This run executes Horos's held frontier job: build the TypeScript outline
extractor inside the map verb. It lexes rather than parses, quotes
declaration slices verbatim, confesses unparsed regions by count and
location, ships stdlib-only, and is developed against a dev-time
differential corpus. Two maintainer directions from this session shape it:
extractors live under a `languages/` folder built for more languages later,
and the next held job recorded at this run's close is the filetype census
mode for scan.

## Assumptions

Proceeding on these unless corrected:

1. Extractors live one folder per language at
   `plugins/horos/skills/horos/scripts/languages/<language>/<language>.py`,
   so fixtures and notes can sit beside each extractor. The existing Python
   mapper moves into `languages/python/python.py` in the same run,
   so map dispatches by suffix through one registry and the folder is the
   pattern for every later language.
2. The extractor covers `.ts` and `.tsx`. Plain JavaScript is out of the
   prototype; its lexer is nearly the same and it can join the registry
   later with its own evidence.
3. The differential oracle is the real TypeScript compiler API, driven by a
   node script kept in the repository as a dev-time tool. Node v26.6.0 is on
   this machine; the `typescript` package installs into the scratchpad for
   the corpus run and is never a plugin dependency. The corpus is the
   wildcat-app-v2 clone at `9b8b6d5d6db06428c5b539f267623277b65315cd`: 867
   hand-written `.ts`/`.tsx` files under `src/`.
4. The completed job increments evolution: `horos-v2.2.0` becomes
   `horos-v3.2.0`, generation and epoch retained.

## 1. Problem statement

`map` orients an agent in a Python file without the file being read whole.
TypeScript repositories, where the scan already does its measured best work,
get no such orientation. The refusal of 2026-08-18 stands against parsing
TypeScript or taking a parser dependency; the superseding design this run
builds needs neither.

What the extractor does, stated so a test can refuse it:

- **Lexing, not parsing.** One pass classifies every character into code,
  comment, string, template (with `${}` nesting) or regex. The
  regex-versus-division ambiguity is resolved by the previous significant
  token, guarded by the fact that a regex literal cannot contain an
  unescaped newline: a candidate regex that meets a newline before its
  closing slash is reclassified as division and rescanned.
- **Declarations, sliced verbatim.** At module depth and inside `export`,
  `namespace` and class bodies, the outliner recognises imports, exports,
  functions, classes, interfaces, type aliases, enums, namespaces, variable
  declarations with arrow or function initialisers, decorators, and class
  members. Each match is quoted as the exact source slice from the
  declaration's first token to its body brace or terminating semicolon,
  types untouched.
- **Confession, not guessing.** Any statement position the recognisers do
  not match is skipped structurally (to the balancing brace or semicolon)
  and recorded as an unparsed region with its line range. The report ends
  with declarations counted, regions confessed, and their locations. A
  lexer-level failure (an unterminated string or template) confesses the
  remainder of the file.

A working prototype means: the pinned fixture outline matches byte for
byte; the corpus run over all 867 files completes with zero crashes; the
differential against the compiler API is recorded as an evidence bundle
with every mismatch triaged (fixed, or confessed as a named unparsed
region); and every suite and lint is green.

## 2. Prior art

The map verb's Python path (this plugin) fixes the output register:
signatures, structure, first docstring lines, refusal and error paths.
Pandects' stripper tests pin the string-literal traps a lexer must not
repeat; Lemma's chunkers already walk Solidity with the same
comment-and-string discipline. Outside: aider's repo-map and Repomix
compress prove the outline's value; universal-ctags demonstrates the
lexer-plus-recognisers approach and its failure mode (silent omission),
which the confession contract exists to fix; the TypeScript compiler API is
the reference oracle. The session assessment of 2026-08-18 (recorded in the
v2.1.0 ledger row) is the design's source.

## 3. Constraints and non-goals

- Stdlib only in everything that ships. The node differential tool is
  dev-time, lives under the plugin's `dev/` directory, and nothing in the
  test suite imports or invokes it.
- The scan and check verbs do not change. The boundary format does not
  change.
- Non-goals: JavaScript, JSON, Solidity and every other language (the
  registry is the extension point, not this run); JSX structure inside
  bodies (bodies are skipped whole); type-correctness of slices (they are
  quotes, not claims); the filetype census (next held job); any cap on
  slice length beyond the source line itself.

## 4. Design options

**A. Lexer plus recognisers, slices verbatim, confession mandatory.**
Chosen, as directed. Trade: recall is bounded by the recogniser list, so
the outline understates a file the way the boundary understates a tree; the
confession line is what keeps that honest.

**B. Regex-only sketch without a lexer.** Rejected: a string or template
containing `class X {` derails it silently, which is the exact guess the
refusal named.

**C. Ship the compiler API as the extractor.** Rejected: a node subprocess
in the runtime path crosses both grounds the refusal keeps.

## 5. Risk register seed

- The regex-versus-division rule is the classic lexer trap; it gets its own
  test block, including division after `)`, after identifiers, and a regex
  containing quotes and braces. The newline guard bounds the damage of a
  wrong guess to one line.
- Template literals nest (`` `a${ {b: `c${d}`} }e` ``); depth is a stack,
  not a flag, and the tests include two levels.
- `.tsx` generics versus JSX: the outliner never enters bodies, and
  declaration headers cannot contain JSX, so the ambiguity is confined to
  regions the extractor either slices as headers or skips whole. The corpus
  run is the check that this holds on real code.
- An unterminated string must confess the remainder, never hang or raise.
- The differential's mismatches are the acceptance evidence: each one is a
  fix or a confessed region, and the bundle names the count of each.
- Moving the Python mapper must not change its pinned output; the fixture
  test from the first delivery holds unchanged.

## 6. Glossary seeds

- Extractor: one language's outline module under `languages/`.
- Registry: the suffix-to-extractor table map dispatches through.
- Slice: the verbatim source text of one declaration head.
- Confession: the recorded line ranges the outliner did not understand.
- Differential corpus: the recorded comparison of outliner declarations
  against the compiler API's, per file, dev-time only.

## 7. Boundaries

- **Always.** Both suites and the three tree lints before a commit;
  imprimatur on every shipped document; the pinned fixtures are the format
  contract.
- **Ask first.** Any runtime dependency; adding a language beyond
  TypeScript; changing the map output register; weakening the confession.
- **Never.** Import or execute scanned code; let the node tool into the
  runtime path or the test suite; report a corpus or differential run that
  did not happen; delete a failing test.

## 8. Success criteria

1. `python3 -m unittest discover -s tests` passes.
2. `python3 -m unittest discover -s plugins/horos/tests -t plugins/horos`
   passes, including the TypeScript lexer, outliner and dispatch tests, and
   the unchanged Python fixture.
3. `python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests`
   and the ephoros equivalent exit clean.
4. Demo path: `python3 plugins/horos/skills/horos/scripts/horos.py map
   plugins/horos/examples/fixture-ts/market.ts` prints the pinned outline,
   and the committed differential evidence bundle at
   `plugins/horos/docs/evidence/wildcat-app-v2-outline.md` is
   machine-checked by the suite like the two scan captures.

## 9. Sources

The v2.1.0 ledger row holding this job and the session assessment behind
it. The maintainer's directions this session: the `languages/` folder and
the filetype census as the probable next goal. The wildcat-app-v2 clone at
`9b8b6d5d6db06428c5b539f267623277b65315cd`. The TypeScript compiler API as
oracle. The map verb's existing pinned fixtures.
