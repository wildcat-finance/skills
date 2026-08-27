# The C++ outline extractor, the runbook

Four steps, dependency order, one pull request each. The study committed
beside this runbook is the spec; both land in step 1.

## Step 1: Commit the frontier spec

**Goal.** The study and runbook are in the tree the later steps build on.
**Entry.** The run branch, cut from `main` at `6182d24`.
**Exit.** Both suites green, three tree lints clean, imprimatur clean on
both documents.
**Files.** `plugins/horos/docs/cpp-outline/study.md` and
`plugins/horos/docs/cpp-outline/runbook.md`.
**Tests.** None new; the existing suites hold.

## Step 2: The lexer and the outliner

**Goal.** map reads C++: comments, strings, characters, raw strings with
custom delimiters and continuation-aware directives lexed; declarations
sliced verbatim at translation-unit, namespace and class depth; directives'
include and define heads quoted; everything else confessed.
**Entry.** Step 1's exit state.
**Exit.** Plugin suite green; the pinned C++ fixture outline matches byte
for byte; the other three fixtures untouched.
**Files.** `plugins/horos/skills/horos/scripts/languages/cpp/cpp.py`;
`languages/__init__.py` gains the suffix lines;
`plugins/horos/examples/fixture-cpp/market.hpp`;
`plugins/horos/tests/test_cpp_outline.py`.
**Tests.** Raw strings with custom delimiters holding parentheses and
quotes; a brace inside a define never in the mask; a multiline directive
one span; template prefixes riding into class and function slices;
constructors and access labels inside a class body; namespaces recursed;
an unmatched statement confessed; an unterminated raw string confessing
the remainder; the fixture pin. Expected count: about fourteen.

## Step 3: The differential corpus

**Goal.** The outliner is held against tree-sitter-cpp over all 842 files
of the solidity clone at the declared altitudes and recorded as a
machine-checked bundle.
**Entry.** Step 2's exit state.
**Exit.** Zero crashes; zero unconfessed misses and zero extras at the
declared altitudes; `python3 -m unittest plugins.horos.tests.test_evidence
-v` green.
**Files.** `plugins/horos/dev/cpp_oracle.py` (dev-time, venv-run);
`plugins/horos/docs/evidence/solidity-outline.md` and its results JSON;
`plugins/horos/tests/test_evidence.py` extended; fixes to
`languages/cpp/cpp.py` as the corpus demands.
**Tests.** Bundle-consistency checks in the shape of the prior
differentials'. Expected count: about three.

## Step 4: Reledger, reconcile, close

**Goal.** The ledger advances to `horos-v6.2.1`; if the differential closed
clean at the declared altitudes the frontier goes mature with `None --
mature`, otherwise it holds a job naming the residue; every surface agrees.
**Entry.** Step 3's exit state.
**Exit.** Study success criteria 1 through 4 all pass as written.
**Files.** `EVOLUTION.md`; `SKILL.md` (metadata `6.2.1`, map's four
languages); `plugins/horos/README.md`; `.agents/skills/horos/SKILL.md`;
root `README.md`.
**Tests.** None new; the evolution and marketplace-prose contracts are the
check.
