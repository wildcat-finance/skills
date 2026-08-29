# The Solidity outline extractor, the runbook

Four steps, dependency order, one pull request each. The study committed
beside this runbook is the spec; both land in step 1.

## Step 1: Commit the frontier spec

**Goal.** The study and runbook are in the tree the later steps build on.
**Entry.** The run branch, cut from `main` at `c17bc05`.
**Exit.** Both suites green, three tree lints clean, imprimatur clean on
both documents.
**Files.** `plugins/horos/docs/sol-outline/study.md` and
`plugins/horos/docs/sol-outline/runbook.md`.
**Tests.** None new; the existing suites hold.

## Step 2: The lexer and the outliner

**Goal.** map reads `.sol`: comments and all string forms lexed;
keyword-led declarations sliced verbatim at file and contract depth with
attribute chains riding along; everything else confessed.
**Entry.** Step 1's exit state.
**Exit.** Plugin suite green; the pinned Solidity fixture outline matches
byte for byte; the other four fixtures untouched.
**Files.** `plugins/horos/skills/horos/scripts/languages/solidity/solidity.py`;
`languages/__init__.py` gains one registry line;
`plugins/horos/examples/fixture-sol/Market.sol`;
`plugins/horos/tests/test_sol_outline.py`.
**Tests.** Hex and unicode strings; a contract keyword inside a string
never a declaration; inheritance lists in contract heads; multiline
function heads with attribute chains and override lists; events, errors,
structs, enums, using-for and file-level type declarations; state variables
cut before initialisers; an assembly block skipped with its body; an
unmatched statement confessed; an unterminated string confessing the
remainder; the fixture pin. Expected count: about thirteen.

## Step 3: The differential corpus

**Goal.** The outliner is held against tree-sitter-solidity over all 151
`.sol` files of the v2-protocol clone at declared altitudes and recorded as
a machine-checked bundle.
**Entry.** Step 2's exit state.
**Exit.** Zero crashes; zero unconfessed misses and zero extras at the
declared altitudes;
`python3 -m unittest plugins.horos.tests.test_evidence -v` green.
**Files.** `plugins/horos/dev/sol_oracle.py` (dev-time, venv-run);
`plugins/horos/docs/evidence/v2-protocol-outline.md` and its results JSON;
`plugins/horos/tests/test_evidence.py` extended; fixes to
`languages/solidity/solidity.py` as the corpus demands.
**Tests.** Bundle-consistency checks in the shape of the prior
differentials'. Expected count: about three.

## Step 4: Reledger and reconcile

**Goal.** The ledger advances to `horos-v7.2.2` holding the classifier
refinement as the next job, and every surface agrees.
**Entry.** Step 3's exit state.
**Exit.** Study success criteria 1 through 4 all pass as written.
**Files.** `EVOLUTION.md`; `SKILL.md` (metadata `7.2.2`, map's five
languages); `plugins/horos/README.md`; `.agents/skills/horos/SKILL.md`;
root `README.md`.
**Tests.** None new; the evolution and marketplace-prose contracts are the
check.
