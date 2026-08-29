# The TypeScript outline extractor, the runbook

Five steps, dependency order, one pull request each. The study committed
beside this runbook is the spec; both land in step 1.

## Step 1: Commit the frontier spec and the languages folder

**Goal.** The spec is in the tree, and the Python mapper lives at
`languages/python/python.py` behind a suffix registry, output unchanged.
**Entry.** The run branch, cut from `main` at `f68c247`.
**Exit.** Both suites green with the Python map fixture untouched; three
tree lints clean; imprimatur clean on both documents.
**Files.** `plugins/horos/docs/ts-outline/study.md` and `runbook.md`;
`plugins/horos/skills/horos/scripts/languages/__init__.py` (the registry);
`plugins/horos/skills/horos/scripts/languages/python/python.py` (moved
mapper, one folder per language);
`horos.py` dispatching map through the registry.
**Tests.** The pinned Python fixture holds unchanged; the refusal message
moves to the registry and its test moves with it, asserting the supported
list is named.

## Step 2: The TypeScript lexer

**Goal.** One pass classifies every character of a `.ts`/`.tsx` source:
code, line comment, block comment, string, template with `${}` nesting,
regex.
**Entry.** Step 1's exit state.
**Exit.** Plugin suite green; the lexer test block passes.
**Files.**
`plugins/horos/skills/horos/scripts/languages/typescript/typescript.py`
(lexer half); `plugins/horos/tests/test_ts_lexer.py`.
**Tests.** Strings with escapes; templates nested two deep; line and block
comments; regex after `=`, `(`, `return` and `,`; division after `)`,
identifiers and numbers; the newline guard reclassifying a false regex; an
unterminated string confessing the remainder. Expected count: about
twelve.

## Step 3: The outliner

**Goal.** Declarations sliced verbatim at module, export, namespace and
class depth; everything unmatched skipped structurally and confessed by
line range; map wired for `.ts`/`.tsx`.
**Entry.** Step 2's exit state.
**Exit.** Plugin suite green; the pinned TypeScript fixture outline matches
byte for byte.
**Files.** `languages/typescript/typescript.py` (outliner half);
`plugins/horos/examples/fixture-ts/market.ts` (the pinned fixture);
`plugins/horos/tests/test_ts_outline.py`.
**Tests.** Imports and exports; function, class with methods and
decorators, interface, type alias, enum, namespace, const arrow function;
an unmatched statement confessed with its lines; the confession footer
format; the fixture pin. Expected count: about ten.

## Step 4: The differential corpus

**Goal.** The outliner is held against the compiler API over all 867
hand-written `.ts`/`.tsx` files in the wildcat-app-v2 clone, and the result
is recorded as a machine-checked evidence bundle.
**Entry.** Step 3's exit state.
**Exit.** Zero crashes over the corpus; every name-level mismatch triaged
as a fix or a confessed region; the bundle's machine lines checked by the
suite; `python3 -m unittest plugins.horos.tests.test_evidence -v` green.
**Files.** `plugins/horos/dev/ts_oracle.mjs` (the dev-time node tool, never
imported by the suite); `plugins/horos/docs/evidence/wildcat-app-v2-outline.md`
and its committed per-file results JSON;
`plugins/horos/tests/test_evidence.py` extended; fixes to
`languages/typescript/typescript.py` as the corpus demands.
**Tests.** Bundle-consistency checks in the shape of the two scan
captures. Expected count: about three.

## Step 5: Reledger and reconcile

**Goal.** The ledger advances to `horos-v3.2.0` holding the filetype-census
job the maintainer named, and every surface agrees.
**Entry.** Step 4's exit state.
**Exit.** Study success criteria 1 through 4 all pass as written.
**Files.** `EVOLUTION.md` (evolution row, script-computed digest);
`SKILL.md` (metadata `3.2.0`, frontier text, the map section describing
both languages and the confession contract); `plugins/horos/README.md`;
`.agents/skills/horos/SKILL.md`; root `README.md`.
**Tests.** None new; the evolution and marketplace-prose contracts are the
check.
