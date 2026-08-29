# Imprimatur source-prose extraction study

Assuming, unless corrected:

1. The target is `wildcat-finance/skills` at synchronized starting commit `0f835d5f5f7c95ad2716eb63bd9bdd8f68b0a841` on `main`.
2. Issue 503 covers the `imprimatur.py` command for `.sol`, `.py`, `.ts`, and `.tsx` files. It does not change `hook_gate.py`, add more source languages, or reinterpret ordinary Markdown.
3. Source comments and Python docstrings are prose. Executable code, ordinary string literals, TypeScript template literals, regular-expression literals, and quoted source specimens are not prose.
4. The implementation remains Python standard-library code and may reuse the checked-in Hexaemeron TypeScript lexer. No package may be added.
5. This is an ordinary `wish` delivery. The meaningful checker change advances Imprimatur's generation to `imprimatur-v2.3.0`, while frontier revision `labelled-prose-v2`, its recorded digest, and issue 422's held job remain byte-identical.

## 1. Problem statement

Imprimatur currently sends every input through Markdown code masking. A four-space-indented source comment is therefore erased before the lexicon sees it. Issue 503 demonstrates the result with an indented Solidity NatSpec line containing the banned consultant-family term `Leverage`: the command reports no finding even though the same comment at column zero is reported.

The users are contributors and agents who run Imprimatur over shipped source. A working prototype extracts prose from Solidity comments and NatSpec, Python comments and docstrings, and TypeScript or TSX comments and JSDoc. It scans that prose with the existing three passes, reports each finding at the original source line and column, ignores comment-shaped text inside code literals, and leaves Markdown behavior unchanged.

The prototype is proved by all of these checks:

- `python3 plugins/hexaemeron/skills/imprimatur/tests/run_tests.py` includes positive cases for all four suffixes, negative lexical specimens, malformed-input refusal, exact source coordinates, Markdown regression coverage, and multi-file CLI behavior.
- `python3 plugins/hexaemeron/tests/run_tests.py` passes with the shared lexer consumers unchanged.
- `python3 -m unittest discover -s tests` passes with the generation and package versions propagated as required.
- `python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py <supported-source> --max-defects 0` exits 1 for the issue specimen and labels the finding with its original path, line, and column.

## 2. Prior art

The current path is in `plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py`. `build()` calls `strip_code_blocks()` before scanning, and that Markdown helper blanks every four-space-indented line without knowing the file suffix. `plugins/hexaemeron/skills/imprimatur/tests/run_tests.py` covers Markdown fences and direct prose but has no source-language matrix.

The last two merged pull requests that changed Imprimatur were [PR 291](https://github.com/wildcat-finance/skills/pull/291) and [PR 290](https://github.com/wildcat-finance/skills/pull/290). PR 291 added a narrow heading exception, advanced the generation, and recorded two clean audit rounds after fixing runtime-binding faults. PR 290 added Promise Machine evaluation cases and recorded two rounds after correcting evidence-class and portable-path faults. Neither pull request or its appended `audit/AUDIT.md` record carries a source-comment extraction lead. Earlier substantive changes are PR 79, which introduced the labelled-prose evaluation, and PR 9, which introduced the original lint.

Both in-scope audit homes were read before comparing designs. The shared `audit/AUDIT.md` contains the PR 290 and PR 291 rounds but no open comment-span item. `plugins/hexaemeron/audit/AUDIT.md` records an accepted `hook_gate.py` exemption boundary; this run does not reopen that hook decision because issue 503 names the explicit lint command.

Useful repository components already exist:

- `plugins/hexaemeron/lib/typescript_lexer.py` classifies complete TypeScript source into offset spans for code, comments, strings, templates, and regular expressions, while returning errors for unterminated constructs.
- `plugins/hexaemeron/tests/test_typescript_lexer.py` guards complete-span reconstruction and the lexical cases that keep comment markers inside literals out of comment spans.
- `plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py` has a small comment iterator for source references. Its documented approximation can miss or misclassify some literal-bound markers, so it is evidence for delimiter forms rather than a parser to copy.
- Python's standard-library [`tokenize`](https://docs.python.org/3/library/tokenize.html) exposes comment tokens and exact start and end coordinates. Python's [`ast`](https://docs.python.org/3/library/ast.html) identifies the string-expression nodes that are actual module, class, and function docstrings.
- The [ECMAScript lexical grammar](https://tc39.es/ecma262/multipage/ecmascript-language-lexical-grammar.html) separates comments from strings, templates, and regular-expression literals. The checked-in lexer already implements that distinction for this repository's bounded TypeScript surface.

No organisation-external package is needed. The standards and standard-library interfaces above supply the needed lexical boundaries.

## 3. Constraints and non-goals

The starting ref is `main` at `0f835d5f5f7c95ad2716eb63bd9bdd8f68b0a841`. The implementation uses Python 3, standard-library tests, and the repository's checked-in TypeScript lexer. It must comply with `AGENTS.md`, the Promise Machine boundary, the Imprimatur promise, and `plugins/hexaemeron/skills/VERSIONING.md`.

The source-prose mask must have exactly the same character length and newline positions as the source. Non-prose bytes become spaces, except line terminators remain line terminators. Comment and docstring delimiters become spaces. The retained prose therefore reaches existing scanners at its original offsets, and `line_col()` continues to report source coordinates without a second mapping table.

The change is limited to `.sol`, `.py`, `.ts`, and `.tsx`. Markdown, standard input without a source suffix, and other file suffixes keep their current masking rules. Lexicon contents, scoring, quote exemptions inside extracted prose, cadence rules, `hook_gate.py`, and the labelled corpus are non-goals. The run does not tune issue 422's calibration target.

Because checker behavior changes, the Imprimatur ledger and `SKILL.md` frontmatter must agree on `imprimatur-v2.3.0` with a generation row that preserves frontier revision `labelled-prose-v2`, digest `092addc4bcae8cd93d34df41146b3a3bbd3fd24a529cd84b1d16e0399d7affb4`, status `open`, and the held next job exactly. Distribution metadata receives the smallest repository-valid Hexaemeron package increment and is propagated to every manifest and version assertion; package and skill versions remain separate.

Always: run the Imprimatur, Hexaemeron, and root suites; run the required prose and structural lints on changed paths; preserve exact offsets; record the generation change without moving the frontier.

Ask first: add a dependency, change `hook_gate.py`, add a fifth source language, change Markdown masking, change a public CLI option, or alter the held frontier.

Never: import or execute inspected source, treat an extraction error as a clean scan, replace a finding's source coordinates with extracted-buffer coordinates, edit vendored code, or claim a check ran when it did not.

## 4. Design options

### Option A: marker and regular-expression extraction

Scan each line for `#`, `//`, or `/* */` and retain what follows. This is short, but comment-shaped text in strings, URLs, templates, and regular expressions becomes prose. More regular expressions would turn into an incomplete lexer whose failures are hard to name. Rejected because false findings would make the source mode untrustworthy.

### Option B: external language parsers

Use dedicated Solidity, Python, and TypeScript parser packages and walk their comment or documentation nodes. This gives language-owned syntax at the cost of new dependencies, parser version management, larger installation scope, and executable third-party setup for a small lexical task. Rejected because the added boundary is larger than the behavior requested.

### Option C: extension adapters with one offset-preserving mask

Dispatch on the exact suffix. Use Python `tokenize` for comments and `ast` only to identify true docstring expression spans. Reuse `plugins/hexaemeron/lib/typescript_lexer.py` for `.ts` and `.tsx`. Add a small Solidity state machine limited to quoted strings, escapes, `//`, and non-nesting `/* */` comments. Each adapter returns retained prose spans or a named extraction error. One helper builds a same-length mask from those spans and blanks delimiters while preserving line terminators.

This is the chosen design. It reuses the most difficult existing lexer, keeps the Solidity grammar to the comment boundary it actually needs, and uses only Python interfaces already shipped. The trade is three small adapters rather than one nominally uniform parser. That duplication is accepted because the language rules differ and each adapter can have a closed test matrix.

### Option D: use the TypeScript lexer for Solidity too

Both languages use slash comments, so a single lexer appears attractive. TypeScript regular-expression and template-literal decisions are not Solidity rules. A Solidity division expression could change the lexer's slash goal and hide or expose a later marker. Rejected because fewer functions would buy a less accurate language boundary.

## 5. Risk register seed

```risk-register
false-clean-comment | source comments and NatSpec or JSDoc entering the prose mask | indented line and block comments in all supported suffixes retain banned terms and produce findings
literal-false-hit | source strings templates regular expressions and URLs containing comment markers | hostile specimens stay blank and produce no finding
docstring-misclassification | Python string expressions at module class and function boundaries | actual docstrings are retained while assigned and later standalone strings are ignored
coordinate-drift | extracted prose passed to line_col and report rendering | every positive fixture asserts the original line and column and the mask length equals the source length
malformed-source-clean | unterminated comments strings templates or invalid Python syntax | extraction returns a named error and the CLI refuses a clean result
markdown-regression | suffix dispatch around the existing strip_code_blocks path | fenced and indented Markdown cases keep their current results
shared-lexer-regression | TypeScript adapter consuming the checked-in Hexaemeron lexer | the complete Hexaemeron lexer suite and all current Phylax and Ephoros consumers remain green
version-drift | Imprimatur generation and Hexaemeron distribution metadata | evolution and version-propagation tests prove every governed copy agrees while the frontier digest stays unchanged
```

## 6. Glossary seeds

- Source prose: comment or documentation text that a contributor ships inside a supported source file.
- Comment span: a lexer-classified source interval whose language grammar treats it as a comment.
- Docstring span: the source interval of the first string expression in a Python module, class, function, or async function body.
- Offset-preserving mask: a string equal in length to its source, with retained prose at original offsets, spaces elsewhere, and unchanged line terminators.
- Extraction error: a named lexical or syntax failure that prevents a supported source file from being reported clean.
- Prose suffix: one of `.sol`, `.py`, `.ts`, or `.tsx`, selected from the input path rather than inferred from content.

## 7. Sources

- [Issue 503](https://github.com/wildcat-finance/skills/issues/503), reproduction, scope, requested suffixes, and the explicit separation from issue 422.
- [PR 291](https://github.com/wildcat-finance/skills/pull/291) and merge `d05b64eca2bb9bdaf9b3c82f4a801ac82b489dc9`, the latest Imprimatur behavior change and its audit account.
- [PR 290](https://github.com/wildcat-finance/skills/pull/290) and merge `64aaf453a60156b94b7aeb8abf7c166b462dbe0c`, the preceding change and its audit account.
- `audit/AUDIT.md` and `plugins/hexaemeron/audit/AUDIT.md`, the in-scope historical audit records.
- `plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py` and `plugins/hexaemeron/skills/imprimatur/tests/run_tests.py`, current behavior and direct checks.
- `plugins/hexaemeron/lib/typescript_lexer.py` and `plugins/hexaemeron/tests/test_typescript_lexer.py`, the shared TypeScript span contract.
- `plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py`, the existing bounded source-comment reference scanner and its stated approximation.
- `plugins/hexaemeron/skills/imprimatur/EVOLUTION.md` and `plugins/hexaemeron/skills/VERSIONING.md`, current frontier and generation rules.
- Python standard-library [`tokenize`](https://docs.python.org/3/library/tokenize.html) and [`ast`](https://docs.python.org/3/library/ast.html) documentation.
- TC39's [ECMAScript lexical grammar](https://tc39.es/ecma262/multipage/ecmascript-language-lexical-grammar.html).

## 8. Signals, and the questions behind them

No retained telemetry is added. The command is a bounded, synchronous local lint rather than an unattended service, so there is no three-in-the-morning operator question for a log, metric, trace, or alert to answer. Its existing structured report already answers the immediate questions: which path was scanned, which family matched, and at which source line and column. This follows `plugins/hexaemeron/skills/ephoros/SKILL.md`; tests verify report fields rather than adding persistent signals.

## 9. Boundaries, per capability

The local source file is untrusted input to a parser. The value at risk is the truth of the lint result and bounded local execution. The controls are exact suffix dispatch, standard-library or checked-in lexers, no import or execution of target code, no shell or subprocess, same-length masks, and named refusal on unterminated or invalid supported source. Comment text remains data for the existing lexicon scanners and never becomes a path or command. This boundary is governed by `plugins/hexaemeron/skills/phylax/SKILL.md`.

No dependency, network host, credential, external process, new output path, or model-output boundary is introduced. Existing path reading and report output remain in place.

## 10. The budget, or its absence

No performance claim or product budget applies. Each adapter is a bounded forward pass, with Python's standard parser work over one file, and issue 503 asks for correctness rather than speed. `plugins/hexaemeron/skills/metron/SKILL.md` therefore authorizes no optimization work and requires no before-and-after measurement. The ordinary test commands in section 1 are correctness gates, not performance evidence.

## 11. The fail-closed posture

A supported source file must not be reported clean when its adapter cannot classify the bytes. Unterminated Solidity or TypeScript constructs, tokenizer failures, or Python syntax that prevents docstring classification produce a path-bearing diagnostic and non-zero CLI result. A multi-file invocation remains non-zero if any supported source extraction fails.

The issue specimen is the first regression guard. Each causal boundary gets a focused test that is observed failing against the unfixed parent and passing on the fixed tree: indented comment retention, literal exclusion, docstring ownership, coordinate preservation, malformed-source refusal, and unchanged Markdown masking. Any unexpected red test invokes `plugins/hexaemeron/skills/elenchus/SKILL.md`: preserve the command and output, reproduce, localize the mechanism, and resume only after the focused and surrounding suites pass.

## 12. Decisions and their homes

The expensive choice is the three-adapter, offset-preserving extraction contract. It belongs to the governed skill rather than a cross-repository ADR. The `imprimatur-v2.3.0` generation row in `plugins/hexaemeron/skills/imprimatur/EVOLUTION.md` will record the chosen design, the rejected parser and regex alternatives, issue 503, and the unchanged frontier revision and digest. `plugins/hexaemeron/skills/imprimatur/SKILL.md` will document the supported suffixes, source-prose boundary, coordinate promise, and extraction refusal visible to callers.

The implementation will comment only the non-obvious reason that the mask retains source length and line terminators. Function names and tests carry the mechanics. No new alert runbook, README entry, or repository-wide ADR is warranted because no interface outside Imprimatur's existing CLI and promise changes. This placement follows `plugins/hexaemeron/skills/hypomnema/SKILL.md` and avoids a second record for the same governed-skill decision.
