## Step 1, round 1 -- 2026-08-25

Review basis: full diff `0f835d5..c0594e5`; Step 1 runbook SHA-256 `358277220c93b25639944a2ec11b9d3ae9324685a3e0895f64cc37a61450eb1`; risk-register SHA-256 `4615d31de2b45cb9798ff14d0ca76e93c462ed7c7b0429a750ca1c9ba2e3f28b`; security suite `waived: issue 503 changes Imprimatur source-comment extraction and Python tests; it produces no Solidity`.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | high | `plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py`, `plugins/hexaemeron/lib/typescript_lexer.py` | The `.ts` and `.tsx` adapter consumed only outer `lex()` spans. A complete template is one `template` span, so genuine line and block comments inside `${...}` were discarded and the prose gate could return clean on source comments. | fixed in this round: shared `comment_spans()` opens substitutions, including nested templates, and assertion guards cover both suffixes |
| S1-R1-02 | medium | `plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py`, `plugins/hexaemeron/lib/typescript_lexer.py` | The JavaScript lexical view did not model JSX. `//` and `/* */` in raw child text became false findings, while a closing-tag slash could begin a regex span and hide a genuine following comment; nested and self-closing elements crossed the same boundary. | fixed in this round: the shared comment consumer traverses JSX markup, child text, and code expressions while preserving the existing `lex()` contract; direct shared-library and Imprimatur guards cover each case |

Mechanical gates: Phylax 0; Ephoros 0; Hypomnema 0. Audit filter: `--audit-filter sapheneia:sapheneia`.

Leads not pursued: full parser-level validity for TypeScript and Solidity. The declared boundary is comment extraction with named lexical refusal, not executable semantics.

## Step 1, round 2 -- 2026-08-25

Review basis: full fixed Step 1 diff against base `0f835d5f5f7c95ad2716eb63bd9bdd8f68b0a841`, with round-2 fixes starting from signed round-1 commit `eeb62230b83ab99c437ae1ebc414c351bc917786`; Step 1 runbook SHA-256 `358277220c93b25639944a2ec11b9d3ae9324685a3e0895f64cc37a61450eb1b`; risk-register SHA-256 `4615d31de2b45cb9798ff14d0ca76e93c462ed7c7b0429a750ca1c9ba2e3f28b`; security suite `waived: issue 503 changes Imprimatur source-comment extraction and Python tests; it produces no Solidity`.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R2-01 | high | `plugins/hexaemeron/lib/typescript_lexer.py` | Generic JSX type arguments prevented element recognition, and a slash after `}` could open a speculative regular expression whose close consumed the first slash of a later comment. Valid `.ts` and `.tsx` inputs could therefore discard genuine trailing comments and return clean. | fixed in this round: generic JSX angle groups are traversed, the comment consumer uses a comment-safe regular-expression close, and direct guards cover both suffixes |
| S1-R2-02 | high | `plugins/hexaemeron/lib/typescript_lexer.py` | JSX classification depended on finding a future matching close. An unterminated opening tag or element was treated as code and could return clean instead of the promised named extraction failure. | fixed in this round: expression-position JSX prefixes enter the traversal directly, and missing or mismatched closes return named errors |
| S1-R2-03 | medium | `plugins/hexaemeron/lib/typescript_lexer.py` | The ASCII-only JSX name start rejected valid Unicode element names, so comment-shaped raw child text became a false finding. | fixed in this round: the JSX name boundary accepts Unicode word starts, and a Unicode child-text guard preserves only the real trailing comment |
| S1-R2-04 | medium | `plugins/hexaemeron/lib/typescript_lexer.py`, `plugins/hexaemeron/skills/imprimatur/SKILL.md` | Recursive code, template, and JSX traversal had no owned depth boundary. Deep supported input leaked `RecursionError` and a traceback instead of exit 2 with a named refusal. | fixed in this round: 64 recursively entered regions are accepted, the 65th is documented and refused by name, and a final recursion translation prevents interpreter leakage |
| S1-R2-05 | medium | `plugins/hexaemeron/lib/typescript_lexer.py` | Plain template substitutions repeatedly lexed the remaining tail, while JSX candidates searched or copied the remaining suffix. These paths were quadratic and contradicted the accepted bounded-forward-pass design for untrusted local source. | fixed in this round: one shared forward comment traversal advances by returned offsets; guards bound complete-lexer calls, tail searches, and suffix slices on repeated substitutions and valid JSX elements |
| S1-R2-06 | medium | `plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py` | Every Python docstring node scanned the complete token list, making a file with many docstrings quadratic in docstrings times tokens. | fixed in this round: source-ordered docstrings share one `string_cursor` over source-ordered tokens, with traced line-event growth guarded below quadratic |

Negative review: Solidity literal and comment boundaries, Python docstring ownership, same-length masks and coordinates, Markdown and `--include-code` behavior, the existing `lex()` consumer contract, and frontier/version invariants remained green under their named guards and gates.

Mechanical gates: Phylax 0; Ephoros 0; Hypomnema 0. Pinned Node v26.6.0 full Hexaemeron suite 1095/1095; focused Imprimatur suite 76/76; evolution and version propagation 16/16; Promise Machine copies 14/14; `git diff --check` 0. Audit filter: `--audit-filter sapheneia:sapheneia`.

Leads not pursued: full parser-level validity for TypeScript and Solidity remains outside the declared comment-extraction boundary. Regular-expression lexical-goal ambiguity beyond the guarded comment-safe case is not elevated to parser semantics. Iterative type-argument depth remains uncapped because it is a forward non-recursive counter; the public 64-region refusal covers recursively entered code, template, and JSX regions.

## Step 1, round 3 -- 2026-08-25

Review basis: full fixed Step 1 diff against base `0f835d5f5f7c95ad2716eb63bd9bdd8f68b0a841`, with round-3 fixes starting from signed round-2 commit `3613febd0435f612185ace8c3cddd04834400d52`; Step 1 runbook SHA-256 `358277220c93b25639944a2ec11b9d3ae9324685a3e0895f64cc37a61450eb1b`; risk-register SHA-256 `4615d31de2b45cb9798ff14d0ca76e93c462ed7c7b0429a750ca1c9ba2e3f28b`; security suite `waived: issue 503 changes Imprimatur source-comment extraction and Python tests; it produces no Solidity`.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R3-01 | medium | `plugins/hexaemeron/lib/typescript_lexer.py` | The TSX generic-arrow probe accepted only a narrow comma or `extends` head. Valid defaulted or `const` type parameters and comment trivia inside or after the angle group entered JSX traversal and returned `unterminated JSX element`. | fixed in this round: the bounded probe traverses the complete angle group and recognizes trailing commas, defaults, constraints, modifiers, contextual names, and comment trivia before parameter-list entry |
| S1-R3-02 | high | `plugins/hexaemeron/lib/typescript_lexer.py` | The comment scanner derived the slash lexical goal from one undifferentiated closing-brace token and refused valid division after object, function, class, postfix, assertion, and type-expression closures. It also read declaration-following regexes as division and could reclassify an adjacent regex close plus division or comment as comment prose. | fixed in this round: bounded brace, control-head, postfix, function/class signature, type-alias newline, and adjacent-regex state separates the parser-confirmed expression and statement contexts without changing the public `lex()` contract |
| S1-R3-03 | high | `plugins/hexaemeron/lib/typescript_lexer.py`, `plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py` | LF-only comment, quote-mask, and coordinate handling absorbed code after valid source line breaks or erased those breaks. CR Python comments were omitted, TypeScript CR/LS/PS code became prose, and Solidity line-comment boundaries did not match its language rules. | fixed in this round: language-specific masks and coordinates preserve Python CR/LF and TypeScript CR/LF/LS/PS; Solidity accepts LF/VT/FF/CR and names parser-invalid NEL/LS/PS outside comments or strings as extraction refusals |
| S1-R3-04 | low | `plugins/hexaemeron/skills/imprimatur/SKILL.md` | Promise evidence said every supported suffix supplied successful source extraction even when `--include-code` intentionally bypassed extraction. | fixed in this round: evidence conditions source extraction on default masking, while the running instructions retain the whole-input meaning of `--include-code` |

### Negative review

Negative review: Solidity ordinary, hex, and Unicode string, NatSpec, and block-comment boundaries; Python docstring ownership and AST byte columns versus token code-point columns; TSX fragments, nesting, attributes, spreads, generic components, and regular-expression character classes; multi-file refusal without partial output; Markdown and `--include-code`; bounded traversal and suffix-copy behavior; exact masks and coordinates; the stable `lex()` API; and frontier/version invariants remained green.

### Mechanical gates

Mechanical gates: TypeScript 5.9.2 parsed 50/50 audit specimens; focused shared-lexer and source-extraction suites 55/55; focused Imprimatur 84/84; pinned Node v26.6.0 full Hexaemeron 1112/1112; evolution and version propagation 16/16; Promise Machine copies 14/14; root suite 350/350; root inoculation 1,258 cases, 0 crashes, 0 unexpected clean; Phylax 0; Ephoros 0; Hypomnema 0; changed-prose Imprimatur 0; Brevitas report and source comparison 0; `git diff --check` 0. Audit filter: `--audit-filter sapheneia:sapheneia`.

### Leads not pursued

Leads not pursued: full parser-level validity for TypeScript and Solidity remains outside the declared comment-extraction boundary. The TypeScript compiler was an audit oracle for the 50 named valid forms, not a repository dependency. Solidity NEL, LS, and PS outside comments or strings and a 65th recursively entered TypeScript code, template, or JSX region use the documented named-refusal boundary rather than speculative parsing.

## Step 1, round 4 -- 2026-08-25

Review basis: full fixed Step 1 diff against base `0f835d5f5f7c95ad2716eb63bd9bdd8f68b0a841`, with round-4 fixes starting from signed round-3 commit `3303a92514f886cfb56a12be9f3aa12c7fcce1ea`; Step 1 runbook SHA-256 `358277220c93b25639944a2ec11b9d3ae9324685a3e0895f64cc37a61450eb1b`; risk-register SHA-256 `4615d31de2b45cb9798ff14d0ca76e93c462ed7c7b0429a750ca1c9ba2e3f28b`; security suite `waived: issue 503 changes Imprimatur source-comment extraction and Python tests; it produces no Solidity`.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R4-01 | high | `plugins/hexaemeron/lib/typescript_lexer.py` | TypeScript 5.9.2 accepted declarations for which the comment scanner carried the division goal across ASI. Generic defaults ended type-alias state, while static imports, re-exports, ambient or uninitialised declarations, and bodyless functions did not end at their declaration boundary. Valid source could return a named refusal or retain regex bytes as comment prose. | fixed in this round: bounded type, module, variable, and body-declaration state restores the declaration-following regex goal; direct and Imprimatur guards cover plain `.ts` and `.tsx`, nested signatures, sequential statements, division controls, and declaration-following regexes |
| S1-R4-02 | high | `plugins/hexaemeron/lib/typescript_lexer.py` | Declaration candidates leaked into expression contexts. Contextual identifiers and ASI-separated class member names could hide a later real division comment, and dynamic `import()` was mistaken for a static import whose completion allowed a following division slash to consume a real block-comment opener. | fixed in this round: member and object contexts cannot start declarations, contextual assignments clear pending declarations, and `import(` cancels static-import state; parser-confirmed expression and semicolon controls guard both supported suffixes |
| S1-R4-03 | medium | `plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py` | `Path.read_text()` translated CRLF and lone CR before default source extraction. A real source path therefore reached the same-length mask with changed length and terminators, contrary to the documented source view and Promise evidence. | fixed in this round: default supported-source paths opt into untranslated newline reads; Markdown and `--include-code` keep universal-newline behavior; actual-file and dispatch guards cover all three paths |

### Negative review

TypeScript 5.9.2 returned empty `parseDiagnostics` for 58/58 primary audit specimens and 35/35 independent transition specimens. The valid forms covered aliases with nested defaults, static imports and re-exports, ambient and multi-declarator variables, bodyless and implemented generic functions, generic classes and return types, comments and newlines inside signatures, declaration and expression closures, labels, case/default and control heads, optional chaining, postfix and non-null division, adjacent regex division/comments, sequential statements, templates, TSX fragments, generic arrows, spreads, attributes, and CR/LF/LS/PS boundaries. Invalid division controls remained refusals instead of widening the regex goal. The comment traversal remained forward and bounded, and extraction errors still discard every accumulated prefix before CLI output.

Python 3.12.3 probes covered Unicode before token and AST columns, CR/CRLF input, true concatenated docstrings, later standalone string expressions, PEP 701 f-string comments, and the shared linear string-token cursor. Solidity 0.8.30 comparison covered LF, VT, FF, CR, NEL, LS, and PS outside literals, in line and block comments, and in strings, plus multi-file no-partial-output behavior. The compiler's VT/FF validity result was not elevated because the Promise explicitly says successful extraction does not establish source validity; the documented retained VT/FF mask and named NEL/LS/PS refusal remained unchanged. Markdown masking, `--include-code`, the complete-span `lex()` API, recursion and angle-depth boundaries, coordinates, and frontier/version invariants remained green.

### Mechanical gates

Mechanical gates: focused shared-lexer and source-extraction suites 69/69; focused Imprimatur 93/93; pinned Node v26.6.0 full Hexaemeron 1126/1126; evolution and version propagation 16/16; Promise Machine copies 14/14; root suite 350/350; root inoculation 1,258 cases, 0 crashes, 0 unexpected clean; Phylax 0; Ephoros 0; Hypomnema 0; changed-prose Imprimatur 0; Brevitas report and protected-source comparison 0; `git diff --check` 0. Audit filter: `--audit-filter sapheneia:sapheneia`.

### Leads not pursued

Full parser-level validity for TypeScript and Solidity remains outside the declared comment-extraction boundary. TypeScript 5.9.2 and Solidity 0.8.30 were audit oracles, not repository dependencies. The bounded repair does not attempt a full parser.

## Step 1, round 5 -- 2026-08-25

Review basis: full fixed Step 1 diff `0f835d5f5f7c95ad2716eb63bd9bdd8f68b0a841..0d20abe905ecc3906237609367236d47e5491fb5`; Step 1 runbook SHA-256 `358277220c93b25639944a2ec11b9d3ae9324685a3e0895f64cc37a61450eb1b`; risk-register SHA-256 `4615d31de2b45cb9798ff14d0ca76e93c462ed7c7b0429a750ca1c9ba2e3f28b`; security suite `waived: issue 503 changes Imprimatur source-comment extraction and Python tests; it produces no Solidity`.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R5-01 | high | `plugins/hexaemeron/lib/typescript_lexer.py` | TypeScript 5.9.2 accepted `break`, `continue`, their labelled forms, and `debugger` when ASI ended them at CR, LF, LS, PS, or a comment-held line break. The scanner retained its division goal, so a following regular-expression body containing `/*...*/` became comment prose. | fixed in this round: explicit restricted-statement state restores the regular-expression goal only after the language-owned line break; member, property, expression-division, and comment controls guard state reset |
| S1-R5-02 | medium | `plugins/hexaemeron/lib/typescript_lexer.py` | The same restricted-statement state prevented TSX element recognition after ASI. Raw JSX child `//` or `/*...*/` text then became source-comment prose. | fixed in this round: the completed restricted statement also admits the TSX element path; raw-child and JSX-expression controls guard the transition |
| S1-R5-03 | high | `plugins/hexaemeron/lib/typescript_lexer.py` | A generic-typed uninitialised variable or bodyless function ending in `>` finished before a following type alias, class, or bodyless function in accepted sequences. The old state cleared, but the `>` still made the next `class` or `function` look like an expression and prevented the next declaration boundary from restoring the regular-expression goal. Valid ordered declarations could expose `/*...*/` bytes from a later regular expression as prose. | fixed in this round: a local completed-declaration marker wins only when tracked declaration state ended; 324 ordered declaration pairs and a binary `>` plus class-expression division control guard both sides |

### Negative review

TypeScript 5.9.2 returned empty `parseDiagnostics` for 17/17 new restricted-statement, declaration-sequence, TSX, Unicode-terminator, and binary-expression controls. All 324/324 parser-valid ordered declaration pairs produced only their genuine trailing comment. Ten nearby statement, member, property, division, block, declaration, and TSX controls matched their expected comments. A 30,079-byte accumulated-state specimen yielded 201 comments and 0 errors after 200 declaration/expression clusters and one 64-region tail.

Python probes retained true concatenated module and function docstrings, PEP 701 f-string comments, Unicode coordinates, CR and CRLF comments, and rejected later string expressions. Solidity probes kept NatSpec and ordinary comments, excluded ordinary, Unicode, and hex string contents, preserved the documented LF, VT, FF, and CR coordinates, and refused NEL, LS, and PS outside a comment or string. Multi-file failure still emitted no partial standard output. Markdown, `--include-code`, same-length masks, original coordinates, recursion refusal, the complete-span `lex()` API, and Imprimatur frontier and version invariants stayed unchanged.

### Mechanical gates

Mechanical gates: focused shared-lexer and source-extraction suites 73/73; focused Imprimatur 95/95; pinned Node v26.6.0 full Hexaemeron 1130/1130; evolution and version propagation 16/16; Promise Machine copies 14/14; root suite 350/350; root inoculation 1,258 cases, 0 crashes, 0 unexpected clean; Phylax 0; Ephoros 0; Hypomnema 0; changed-prose Imprimatur 0; Brevitas report and protected-source comparison 0; `git diff --check` 0. Audit filter: `--audit-filter sapheneia:sapheneia`.

### Leads not pursued

Full parser-level TypeScript and Solidity validity remains outside the declared comment-extraction contract. TypeScript 5.9.2 was an audit oracle and is not a repository dependency. No full parser was added.

## Step 1, round 6 -- 2026-08-25

Review basis: full fixed Step 1 diff against base `0f835d5f5f7c95ad2716eb63bd9bdd8f68b0a841`, with round-6 repairs starting from signed round-5 tip `ea04d5fffc0fa86c073f6e3179b54133539ac8b9`; Step 1 runbook SHA-256 `358277220c93b25639944a2ec11b9d3ae9324685a3e0895f64cc37a61450eb1b`; risk-register SHA-256 `4615d31de2b45cb9798ff14d0ca76e93c462ed7c7b0429a750ca1c9ba2e3f28b`; security suite `waived: issue 503 changes Imprimatur source-comment extraction and Python tests; it produces no Solidity`.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R6-01 | high | `plugins/hexaemeron/lib/typescript_lexer.py` | The expression-goal table omitted declaration-to-JSX, keyword-property, for-of, spread, decorator, class-heritage, prefix-operator, line-break `!`, and byte-order-mark transitions. Valid TypeScript or TSX could expose comment-shaped regex or JSX bytes as prose, or hide a genuine division comment. | fixed in this round: one expression-goal transition table and declaration-boundary reset now cover the parser-backed matrix; sequential state, binding, prefix/postfix, raw-JSX and real-comment guards preserve both sides |
| S1-R6-02 | high | `plugins/hexaemeron/lib/typescript_lexer.py` | Treating contextual `await` and `yield` as unconditional regex goals could hide division comments; the first repair also refused safe complete regexes followed by their own comments. | fixed in this round: `ambiguous slash after contextual identifier` is returned only when the two readings move a comment delimiter; safe post-regex line and block comments remain supported |
| S1-R6-03 | high | `plugins/hexaemeron/lib/typescript_lexer.py` | An unterminated regex in an established expression goal fell through as code and could return clean. | fixed in this round: `unterminated regular expression literal` is a named extraction failure and the CLI exits 2 |
| S1-R6-04 | medium | `plugins/hexaemeron/lib/typescript_lexer.py` | Valid TSX single-parameter generic function types such as `<T>(value: T) => T` entered JSX traversal and were refused, while identical prefixes in object values and labelled statements had to remain JSX. | fixed in this round: an explicit known-type goal feeds the existing generic-arrow probe for variable, ambient, parameter, return, alias and class-member types; expression-position JSX remains outside prose |
| S1-R6-05 | medium | `plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py` | A 10,000-operator Python expression made `ast.parse()` raise `MemoryError` and leak a traceback. | fixed in this round: parser and tokenizer `MemoryError` or `RecursionError` becomes `Python parser resource limit exceeded` at 1:1 |
| S1-R6-06 | high | `plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py` | Supported source paths decoded with replacement, had no byte ceiling, admitted FIFO or device paths, and leaked read exceptions. Invalid UTF-8 carried a false-clean risk; large or non-regular input carried exhaustion or stall risk. | fixed in this round: default source mode requires a regular file, reads at most 1,048,577 bytes to enforce a cap of 1,048,576 bytes, decodes strict UTF-8, reports invalid bytes with suffix-owned line rules and translates path errors before output |
| S1-R6-07 | medium | `plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py` | Solidity 0.8.34 accepts backslash string continuation across LF, CR and CRLF, but the scanner consumed only the backslash and CR and refused the LF half of CRLF. | fixed in this round: CRLF is consumed as one three-character string transition; comment-shaped string bytes remain excluded and following NatSpec retains 3:5 |

### Negative review

TypeScript 5.9.2 matched 343/343 parser-valid operator, trivia and state specimens plus 8/8 known-type and JSX controls. All 324/324 ordered declaration pairs and the 200-cluster sequential state-reset specimen stayed green. Solidity 0.8.34 accepted LF, CR and CRLF string continuations. Python 3.12.3 resource, Unicode-coordinate and docstring-ownership guards passed.

Solidity ordinary, Unicode and hex strings, comments and NatSpec; Python docstrings and token coordinates; TypeScript templates, regexes, JSX, declarations, contextual identifiers and all four line terminators; same-length masks; Markdown and `--include-code`; multi-file no-partial-output behavior; the stable `lex()` API; recursion and complexity boundaries; and Promise and frontier identities received negative review with no other finding.

### Mechanical gates

End-to-end issue specimen exit 1 with original coordinate 2:17; focused shared-lexer and source-extraction 92/92; focused Imprimatur 108/108; pinned Node v26.6.0 full Hexaemeron 1,149/1,149; evolution and version propagation 16/16; Promise Machine copies 14/14; root suite 350/350; root inoculation 1,258 cases, 0 crashes, 0 unexpected clean; Phylax 0; Ephoros 0; Hypomnema 0; changed-prose Imprimatur 0; Brevitas report and protected-source comparison 0; `git diff --check` 0. Audit filter: `--audit-filter sapheneia:sapheneia`.

### Leads not pursued

Full parser-level TypeScript and Solidity validity remains outside the source-comment extraction contract. TypeScript 5.9.2 and Solidity 0.8.34 were audit oracles, not repository dependencies. The contextual slash refusal is limited to cases where the two readings move a comment delimiter. No full parser or new runtime dependency was added.

## Step 1, round 7 -- 2026-08-25

Review basis: full fixed Step 1 diff against base `0f835d5f5f7c95ad2716eb63bd9bdd8f68b0a841`, with round-7 repairs starting from signed round-6 tip `1a1b50c779567149cc1d72d0b6d80e1782f0a71f`; Step 1 runbook SHA-256 `358277220c93b25639944a2ec11b9d3ae9324685a3e0895f64cc37a61450eb1b`; risk-register SHA-256 `4615d31de2b45cb9798ff14d0ca76e93c462ed7c7b0429a750ca1c9ba2e3f28b`; security suite `waived: issue 503 changes Imprimatur source-comment extraction and Python tests; it produces no Solidity`.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R7-01 | high | `plugins/hexaemeron/lib/typescript_lexer.py` | A completed bodyless function left a return-type token behind. A following `async function` was then treated as an expression, so a later regex or JSX body could become comment prose. | fixed in this round: a declaration-prefix boundary now survives `export`, `default`, `declare`, `abstract`, and `async` only from a statement start; declaration and function-expression controls guard both goals |
| S1-R7-02 | high | `plugins/hexaemeron/lib/typescript_lexer.py` | A completed `do ... while` had no distinct statement state. A following type alias could inherit the control-head goal and expose regex or JSX bytes as comments, including nested, labelled, conditional, and block-bodied forms. | fixed in this round: a nested `do` state records body completion, binds the matching `while (...)`, and emits one `do-while)` statement boundary; parser-backed controls cover ordinary `while` and division |
| S1-R7-03 | medium | `plugins/hexaemeron/lib/typescript_lexer.py` | Valid TSX nested generic function types such as `F<<U>(value: U) => U>` entered JSX traversal because the known type goal stopped at the outer angle. Valid declarations, calls, and instantiation expressions were refused. | fixed in this round: declaration-angle and nested type-argument depth carry the known type goal; comparison, shift, and raw-JSX controls preserve expression parsing |
| S1-R7-04 | medium | `plugins/hexaemeron/lib/typescript_lexer.py` | Each successful TSX generic-arrow probe rescanned all nested constraints. Character reads grew from 12,664 at depth 24 to 47,932 at depth 48. | fixed in this round: the recognized head end is reused while the forward scanner crosses it; the same specimens now take 2,031 and 4,095 reads, and a structural access-count guard holds the bound |
| S1-R7-05 | high | `plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py` | The regular-file check used `Path.stat()` before `Path.open()`. Replacing the path with a FIFO or device between those calls bypassed the check and could stall the lint. | fixed in this round: default source mode requires a nonblocking no-follow open, checks that same descriptor with `fstat()`, applies the size bound before and during the descriptor read, and refuses hosts without no-follow support; FIFO, symlink, directory, device, oversize, UTF-8, and swap guards are green |
| S1-R7-06 | low | `plugins/hexaemeron/skills/imprimatur/SKILL.md`, `plugins/hexaemeron/skills/imprimatur/EVOLUTION.md` | The running prose said every malformed supported source was refused even though the Promise boundary disclaims parser-level source validity. | fixed in this round: the public text names the extraction failures that are refused and keeps full source validity outside the Promise |

### Negative review

TypeScript 5.9.2 matched 2,215/2,215 parser-valid generated compositions, 10,595 parser-valid cases from a 13,107-case two-statement model with 2,512 parser-invalid cases excluded, and 1,125/1,125 parser-valid app-corpus files, with zero scanner errors or comment mismatches. The matrices cover declaration prefixes, return types, `do` placement and nesting, regex/division/JSX suffixes, type-depth 1 through 16, shift controls, malformed lexical refusal, coordinates, and sequential state reset.

Python 3.12.3 AST ownership, token coordinates, Unicode byte columns, CR and CRLF, concatenated docstrings, parser resource translation, and linear token walking remained green. Solidity 0.8.34 accepted 44/44 independent ordinary, single-quoted, Unicode, hex, escaped, and continued string specimens paired with line, NatSpec, block, or doc comments; extraction had zero errors or mismatches. Descriptor-first reads refused FIFO, symlink, directory, device, oversize, invalid UTF-8, and the simulated check/open swap without partial output. Markdown, standard input, `--include-code`, same-length masks, original coordinates, recursion refusal, the complete-span `lex()` API, and frontier identities stayed unchanged.

### Mechanical gates

End-to-end issue specimen exit 1 at 2:17; focused shared-lexer and source-extraction tests 100/100; focused Imprimatur 110/110; pinned Node v26.6.0 full Hexaemeron 1,157/1,157; root suite 350/350; root inoculation 1,258 cases with 0 crashes and 0 unexpected clean; evolution and version propagation 16/16; Promise Machine copies 14/14; Phylax 0; Ephoros 0; Hypomnema 0; changed-prose Imprimatur 0; Brevitas report and protected-source comparison 0; `git diff --check` 0. Audit filter: `--audit-filter sapheneia:sapheneia`.

### Leads not pursued

Full parser-level TypeScript and Solidity validity remains outside the source-comment extraction contract. TypeScript 5.9.2 and Solidity 0.8.34 were audit oracles, not repository dependencies. The finite grammar states and parser-backed closure above support the bounded repair, but do not establish equivalence with a full TypeScript parser; no new token-specific suffix rule or runtime dependency was added.

## Step 1, round 8 -- 2026-08-25

Review basis: full fixed Step 1 diff against base `0f835d5f5f7c95ad2716eb63bd9bdd8f68b0a841`, with round-8 repairs starting from signed round-7 tip `5de2900ddda7cda5ce11aa6a35ee557c89ba1276`; Step 1 runbook SHA-256 `358277220c93b25639944a2ec11b9d3ae9324685a3e0895f64cc37a61450eb1b`; risk-register SHA-256 `4615d31de2b45cb9798ff14d0ca76e93c462ed7c7b0429a750ca1c9ba2e3f28b`; security suite `waived: issue 503 changes Imprimatur source-comment extraction and Python tests; it produces no Solidity`.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R8-01 | high | `plugins/hexaemeron/lib/typescript_lexer.py` | A parenthesized class or function expression left its body candidate live after the real body and semicolon. The next unrelated brace consumed that stale candidate, so later regular-expression or raw JSX bytes containing comment markers became comment prose. | fixed in this round: a stack carries parenthesis depth, declaration role, angle depth and function-return-type state, pops only the matching body and clears stale entries at a semicolon; shared-scanner and Imprimatur guards cover both observed failures plus nested function-default and class-heritage controls |
| S1-R8-02 | medium | `plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py` | A valid Python UTF-8 byte-order mark decoded to U+FEFF, which `ast.parse(str)` rejected even though Python consumes the bytes as an encoding marker. Default source mode therefore refused valid Python. | fixed in this round: AST and tokenizer work use a same-length form-feed parser view while spans and coordinates retain the original text; a Python 3.12.3 matrix matched 100/100 compiler-valid BOM, cookie, line-ending, owner, comment, docstring and literal cases with 0 extraction mismatches |
| S1-R8-03 | medium | `plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py` | Hard, gated and structural findings rescanned the source prefix for each coordinate; gated hits also repeated sentence lookup and evidence work. At 512 hits in 4,609 characters, the parent performed 1,177,344 indexed reads, or 255.4x the input. | fixed in this round: one line-start index, binary coordinate and sentence lookup, and same-sentence evidence caches reduce the probe to 4,609 reads, or 1.0x; assertion guards cover all three passes and 20,000 parent-versus-fixed prose cases had 0 report mismatches |

### Negative review

Babel parser 7.29.2 matched 11,968/11,968 systematic valid TS/TSX compositions, 50,000/50,000 deterministic random compositions and 1,125/1,125 parser-valid application-corpus files with 0 scanner errors and 0 comment-range mismatches. All 128/128 intentional malformed counterparts returned a named refusal. Indexed and legacy coordinates matched 1,000/1,000 random texts for each language-owned line-terminator set.

Solidity 0.8.34 retained only expected prose in 60/60 compiler-valid ordinary, single-quoted, Unicode, hex, escaped, concatenated and LF, CR or CRLF-continued string/comment compositions; 20/20 compiler-invalid controls were excluded from compatibility claims. Descriptor-first reads still refuse FIFO, symlink, directory, device, oversize, invalid UTF-8 and simulated path replacement before output. Markdown, standard input, `--include-code`, multi-file no-partial-output behavior, same-length masks, original coordinates, recursion refusal and the complete-span `lex()` API received negative review with no other finding. `imprimatur-v2.3.0`, frontier revision `labelled-prose-v2`, digest `092addc4bcae8cd93d34df41146b3a3bbd3fd24a529cd84b1d16e0399d7affb4`, status `open` and the held job remain unchanged.

### Mechanical gates

End-to-end issue specimen exit 1 at 2:17; focused shared-lexer and source-extraction tests 104/104; focused Imprimatur 112/112; pinned Node v26.6.0 full Hexaemeron 1,161/1,161; root suite 350/350, including 1,258 inoculation cases with 0 crashes and 0 unexpected clean; evolution and version propagation 16/16; Promise Machine copies 14/14; Phylax 0; Ephoros 0; Hypomnema 0; changed-prose Imprimatur 0; Brevitas report and protected-source comparison 0; `git diff --check` 0. Audit filter: `--audit-filter sapheneia:sapheneia`.

### Leads not pursued

Full parser equivalence remains outside the source-comment extraction contract. Babel parser 7.29.2 and Solidity 0.8.34 were audit oracles, not repository dependencies. Hosts without `O_NOFOLLOW` retain the named fail-closed refusal; this round adds no less-safe fallback. No external parser or new runtime dependency was added.

## Step 2, round 1 -- 2026-08-26

Review basis: full Step 2 diff `10b4d7f04ca52abfe6aeafa0e8c2c0db5dcdf566..536d8d25dae60888fc2ec55d3715d47a1546adfe`; Step 2 runbook SHA-256 `358277220c93b25639944a2ec11b9d3ae9324685a3e0895f64cc37a61450eb1b`; baseline/effective block SHA-256 `081fc96a3a0f5967e9261b898e43907dbed06663e279c3df24501d70412eef6d`; risk-register SHA-256 `4615d31de2b45cb9798ff14d0ca76e93c462ed7c7b0429a750ca1c9ba2e3f28b`; security suite `waived: issue 503 changes Imprimatur source-comment extraction and Python tests; it produces no Solidity`.

Findings: 0.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| none | none | package metadata | No version-propagation finding. | clean |
| none | none | `plugins/hexaemeron/docs/imprimatur-source-prose-extraction/proof.md` | No proof-accuracy finding. | clean |
| none | none | full Step 2 diff | No risk-register finding. | clean |

### Risk-register review

| lane | evidence | status |
| --- | --- | --- |
| `false-clean-comment` | Recreated `.sol`, `.py`, `.ts`, and `.tsx` fixtures reported only retained comments and Python docstrings at `2:17`; `1:4`, `4:8`, `5:7`; `2:4`; and `2:5`. | passed |
| `literal-false-hit` | The recreated string controls added no finding; the 112-test focused suite also covered TypeScript templates, regular expressions, and URLs. | passed |
| `docstring-misclassification` | The recreated module and function docstrings were retained while the assigned string was ignored; focused guards also covered class docstrings and later standalone strings. | passed |
| `coordinate-drift` | Recreated coordinates matched the proof, and focused guards checked source-length masks and language-owned line terminators. | passed |
| `malformed-source-clean` | The recreated unterminated Solidity comment exited `2` at `2:5` with no partial report; focused guards covered invalid Python and unterminated Solidity, TypeScript template, TSX, and regular-expression input. | passed |
| `markdown-regression` | The recreated indented Markdown fixture exited `0` with `0` defects; focused guards retained Markdown and `--include-code` behavior. | passed |
| `shared-lexer-regression` | The pinned Node `v26.6.0` Hexaemeron suite passed `1161/1161`; Phylax and Ephoros both exited `0`. | passed |
| `version-drift` | Hexaemeron is `1.5.10` in both manifests, both marketplace listings, and `tests/test_version_propagation.py`; Promise Machine and root propagation tests passed while `imprimatur-v2.3.0`, `labelled-prose-v2`, and frontier SHA-256 `092addc4bcae8cd93d34df41146b3a3bbd3fd24a529cd84b1d16e0399d7affb4` stayed unchanged. | passed |

### Package, proof, and gates

All six fixture SHA-256 values in `plugins/hexaemeron/docs/imprimatur-source-prose-extraction/proof.md` matched recreated LF-terminated bytes. The recorded CLI exits, findings, coordinates, exclusions, cadence count `3`, and malformed-input refusal matched. The signed entry commit `10b4d7f04ca52abfe6aeafa0e8c2c0db5dcdf566` and signed Step 2 commit `536d8d25dae60888fc2ec55d3715d47a1546adfe` both verified against `/tmp/fiat-503-allowed-signers`.

| command | exit | result |
| --- | ---: | --- |
| `python3 scripts/promise_machine.py check` | `0` | `14` plugins and `14` copies |
| `python3 -m unittest discover -s tests` | `0` | `350/350`; `1258` inoculation cases, `0` crashes, `0` unexpected clean |
| `PATH=/home/kethcode/.local/share/mise/installs/node/26.6.0/bin:$PATH python3 plugins/hexaemeron/tests/run_tests.py` | `0` | `1161/1161` |
| `python3 plugins/hexaemeron/skills/imprimatur/tests/run_tests.py` | `0` | `112/112` |
| `python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests` | `0` | clean |
| `python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests` | `0` | clean |
| `python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs` | `0` | clean |
| `python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/docs/imprimatur-source-prose-extraction/study.md plugins/hexaemeron/docs/imprimatur-source-prose-extraction/runbook.md plugins/hexaemeron/docs/imprimatur-source-prose-extraction/proof.md --max-defects 0` | `0` | `0` defects in all three files |
| `python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py plugins/hexaemeron/docs/imprimatur-source-prose-extraction/proof.md --mode report` | `0` | clean |
| `git diff --check` | `0` | no whitespace errors |

Audit filter: `--audit-filter sapheneia:sapheneia`. Fixes commit: none. Elenchus verdict: none.

Leads not pursued: full parser equivalence for TypeScript and Solidity remains outside the source-comment extraction contract; no package or proof lead remains open.
