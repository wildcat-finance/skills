# The Go outline extractor, the runbook

Four steps, dependency order, one pull request each. The study committed
beside this runbook is the spec; both land in step 1.

## Step 1: Commit the frontier spec

**Goal.** The study and runbook are in the tree the later steps build on.
**Entry.** The run branch, cut from `main` at `ab1101b`.
**Exit.** Both suites green, three tree lints clean, imprimatur clean on
both documents.
**Files.** `plugins/horos/docs/go-outline/study.md` and
`plugins/horos/docs/go-outline/runbook.md`.
**Tests.** None new; the existing suites hold.

## Step 2: The lexer and the outliner

**Goal.** map reads `.go`: comments, interpreted strings, raw strings and
runes lexed; keyword-led declarations sliced verbatim with grouped blocks
emitting one line per member; everything else confessed.
**Entry.** Step 1's exit state.
**Exit.** Plugin suite green; the pinned Go fixture outline matches byte
for byte; the Python and TypeScript fixtures untouched.
**Files.** `plugins/horos/skills/horos/scripts/languages/go/go.py`;
`languages/__init__.py` gains one registry line;
`plugins/horos/examples/fixture-go/market.go`;
`plugins/horos/tests/test_go_outline.py`.
**Tests.** Raw strings spanning lines with backslashes as plain bytes; rune
literals holding quotes; a func keyword inside a raw string never a
declaration; methods with receivers; grouped const with iota; grouped
imports; an unmatched statement confessed; an unterminated string
confessing the remainder; the fixture pin. Expected count: about twelve.

## Step 3: The differential corpus

**Goal.** The outliner is held against tree-sitter-go over all 1,421 files
of the go-ethereum clone and the result recorded as a machine-checked
bundle.
**Entry.** Step 2's exit state.
**Exit.** Zero crashes; zero unconfessed misses; zero extras;
`python3 -m unittest plugins.horos.tests.test_evidence -v` green.
**Files.** `plugins/horos/dev/go_oracle.py` (dev-time, venv-run, never
imported by the suite);
`plugins/horos/docs/evidence/go-ethereum-outline.md` and its results JSON;
`plugins/horos/tests/test_evidence.py` extended; fixes to
`languages/go/go.py` as the corpus demands.
**Tests.** Bundle-consistency checks in the shape of the TypeScript
differential's. Expected count: about three.

## Step 4: Reledger and reconcile

**Goal.** The ledger advances to `horos-v5.2.1` holding the C++ extractor
as the next job, and every surface agrees.
**Entry.** Step 3's exit state.
**Exit.** Study success criteria 1 through 4 all pass as written.
**Files.** `EVOLUTION.md`; `SKILL.md` (metadata `5.2.1`, map's three
languages); `plugins/horos/README.md`; `.agents/skills/horos/SKILL.md`;
root `README.md`.
**Tests.** None new; the evolution and marketplace-prose contracts are the
check.
