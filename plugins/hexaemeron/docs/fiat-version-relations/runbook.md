# Runbook: resolve runbook target versions at integrate time

Derived from `.hexaemeron/study.md` at SHA-256
`4f379dac26ed32af4310bcd55ebaef7ca91774da7ca53f69f2d3a6401e8942c7`.
The run starts from `main` at
`8e6480230a5f43c57aef4f9a6c52f4c602d86790` on
`fiat/556-resolve-runbook-target-versions-at-integrate`. Four steps keep the
runbook declaration, Fiat's anchor, terminal resolution, and durable version
record separately reviewable. Each step begins and ends green, permits only
its declared paths, and includes the run's append-only audit record.

```version-relations
fiat | plugins/hexaemeron/skills/fiat/EVOLUTION.md | next-generation-after-integration-base
protasis | plugins/hexaemeron/skills/protasis/EVOLUTION.md | next-generation-after-integration-base
```

The two rows are relations, not reservations. No concrete future label is a
runbook criterion. A projection may appear in a source-bound controller packet,
but only the exact integration-base relation chooses the final labels. This run
is ordinary generation work with `frontier: null`; it never uses `--frontier`
and leaves both held frontier targets byte-identical.

The active controller and checker predate the capability they are building.
They receipt this run under their existing contracts. Product tests must prove
the new behaviour, but this run must not claim that its own terminal transition
earned the new version-resolution Promise. If either projection is consumed,
the only current-run correction is a signed two-parent `sync-run` change with
complete affected-path revalidation, or a halt.

## Step 1: Define and check the runbook relation contract

**Goal.** Give Protasis one optional closed `version-relations` declaration,
one admitted relation, and a mechanical rule that prevents a declared target
from also being pinned to a concrete future label.

**Entry.** The run branch at
`8e6480230a5f43c57aef4f9a6c52f4c602d86790`, with the study receipted, this
runbook not yet committed, the active Protasis checker green on both ignored
artefacts, and no tracked change in the run worktree.

**Exit.** The tracked study and runbook are byte-identical to their receipted
sources. `protasis.py` reports P006 for a present-but-malformed relation block,
a duplicate target or path, an unsafe path, an unknown relation, a blank row,
or a concrete governed target token outside the block. It accepts no block,
one valid block before Step 1, partial target coverage, and fenced decoys. The
Protasis contract states that this is a structure verdict, not a suitability or
version-allocation verdict. Prove the exit with:

```bash
cmp .hexaemeron/study.md plugins/hexaemeron/docs/fiat-version-relations/study.md
cmp .hexaemeron/runbook.md plugins/hexaemeron/docs/fiat-version-relations/runbook.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study .hexaemeron/study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py .hexaemeron/runbook.md
python3 -m unittest plugins.hexaemeron.tests.test_protasis_checker
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
```

**Files.** `plugins/hexaemeron/docs/fiat-version-relations/study.md`,
`plugins/hexaemeron/docs/fiat-version-relations/runbook.md`,
`plugins/hexaemeron/skills/protasis/SKILL.md`,
`plugins/hexaemeron/skills/protasis/scripts/protasis.py`,
`plugins/hexaemeron/tests/test_protasis_checker.py`,
`plugins/hexaemeron/tests/test_fiat_skill.py`,
`tests/promise_machine_coverage.json`,
`audit/rounds/fiat-556-resolve-runbook-target-versions-at-integrate.md`, and
`.horos/boundary.json` only if a deterministic Horos scan changes it.

**Tests.** Add focused P006 fixtures for the valid block, absent legacy block,
partial target list, second block, malformed field count, duplicate id,
duplicate path, unsafe path forms, unknown relation, blank row, fenced decoy,
target/directory mismatch, and every concrete-token position. Preserve the
first genuine pre-fix failures before changing the parser. The audit-fix runner
is `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`;
the CLI report format is `unittest-json-v1`, the report file is
`tmp/elenchus/fiat-556-step-1.json`, and the expected JSON schema is
`elenchus.unittest.v1`. The `{report}` placeholder occurs exactly once.

**Disciplines.** phylax: the fenced block admits repository-relative paths, so
the checker closes lexical path and target-identity ambiguity without opening
files. ephoros: none, this local checker has no unattended runtime; its stable
P006 findings are the operator signal. metron: none, no speed claim.
elenchus: the new hostile fixtures must fail on the signed parent and pass only
after the parser cause is fixed. hypomnema: the canonical Protasis contract and
the two tracked source documents are the lasting explanation; no decision
record is due until Step 4.

## Step 2: Capture relation anchors and preserve literal compatibility

**Goal.** Let a future Fiat controller receipt one exact relation source and
compatibility anchor at `done runbook` while leaving literal-only runbooks and
legacy version-1 states unchanged.

**Entry.** Step 1's signed, audited, green head on the exact branch named by
the Step 2 implement directive, with P006 and the tracked source copies already
present and Promise Machine checks green.

**Exit.** `done runbook` parses at most one valid relation block, reads each
declared ledger and matching `SKILL.md` from the exact starting commit, and
records the closed `fiat-version-relations/v1` anchor all-or-nothing. The
anchor binds the runbook and block digests, exact commit, label counters,
frontier tuple digests, ledger blob, and matching metadata blob without
reserving a result. State verification, status, and every worker packet
distinguish absent legacy data, a valid anchor, and malformed data. A runbook
without the block produces the prior receipt and directive shapes and performs
no new remote version read. Prove the exit with:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_version_relations
python3 -m unittest plugins.hexaemeron.tests.test_hexctl plugins.hexaemeron.tests.test_fiat_skill
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
```

**Files.** `plugins/hexaemeron/skills/fiat/SKILL.md`,
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/tests/test_version_relations.py`,
`plugins/hexaemeron/tests/test_fiat_skill.py`,
`tests/promise_machine_coverage.json`,
`tests/test_promise_machine_contract.py` only if the changed declaration shape
requires its existing population assertions to move,
`audit/rounds/fiat-556-resolve-runbook-target-versions-at-integrate.md`, and
`.horos/boundary.json` only if a deterministic Horos scan changes it.

**Tests.** Cover one and two targets; source-order versus sorted receipt order;
no block; partial target coverage; exact starting-commit reads despite later
worktree and ref drift; label arithmetic; ledger/SKILL mismatch; unsafe,
missing, tree, symlink, submodule, non-UTF-8, and oversized objects; every
anchored compatibility field; all-or-nothing capture; packet reconstruction;
legacy state replay; and byte-identical legacy directives. The audit-fix runner
is `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`;
the CLI report format is `unittest-json-v1`, the report file is
`tmp/elenchus/fiat-556-step-2.json`, and the expected JSON schema is
`elenchus.unittest.v1`. The `{report}` placeholder occurs exactly once.

**Disciplines.** phylax: runbook-controlled paths cross into bounded Git blob
reads, so fixed argv, regular-blob checks, UTF-8 and size caps, no symlink
following, and content-free failures apply. ephoros: status and packets must
label anchor, projection, exact commit, and explicit null without saying a
number is reserved. metron: none, caps are correctness limits and no latency
target exists. elenchus: the #555 stale-literal state and hostile object/legacy
fixtures are the red specimens. hypomnema: the Fiat contract owns the receipt
meaning; the expensive versioning decision remains Step 4's ADR addendum.

## Step 3: Resolve versions at integration and guard the remaining race

**Goal.** Resolve every declared generation against one coherent exact
integration base and candidate head, retain append-only recovery evidence, and
withhold terminal integration whenever the relation or GitHub parent pair is
stale.

**Entry.** Step 2's signed, audited, green head on the exact branch named by
the Step 3 implement directive, with valid anchors, legacy behaviour, and all
complete suites green.

**Exit.** `done resolve-versions` reads stable remote base and run refs, exact
Git objects, every target history, and the product or active-sync head. It
accepts generation-only drift under the anchored tuple, requires the head
ledger to extend the base by exactly one matching generation row and matching
`SKILL.md` metadata, and records all targets atomically under
`fiat-version-resolution/v1`. Eight append-only receipts are retained; a ninth
refuses. A subject-labelled pending record recovers every state/ledger write
window exactly once. `next` withholds integration on no, malformed, stale, or
incompatible resolution. `done integrate` replays the actual merge's
`[base, candidate]` parents and refuses a post-check base move. Any post-step
product correction travels only through the existing signed `[product, base]`
sync and complete affected-path revalidation. Prove the exit with:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_version_relations
python3 -m unittest plugins.hexaemeron.tests.test_hexctl plugins.hexaemeron.tests.test_fiat_skill
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
```

**Files.** `plugins/hexaemeron/skills/fiat/SKILL.md`,
`plugins/hexaemeron/skills/fiat/references/push-discipline.md`,
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/tests/test_version_relations.py`,
`plugins/hexaemeron/tests/test_hexctl.py`,
`plugins/hexaemeron/tests/test_fiat_skill.py`,
`tests/promise_machine_coverage.json`,
`tests/test_promise_machine_contract.py`,
`audit/rounds/fiat-556-resolve-runbook-target-versions-at-integrate.md`, and
`.horos/boundary.json` only if a deterministic Horos scan changes it.

**Tests.** Build the #555 topology and prove the literal fixture cannot finish
after a concurrent generation while the relation fixture can resolve only when
the candidate tree carries the newly selected row and metadata. Cover zero,
one, and several compatible generations; each incompatible tuple field;
rewritten histories; partial targets; ref changes around reads; missing or
oversized objects; sync parent, signature, head, path, and green-check faults;
stale runbook/base/head/blob evidence; eight retained receipts and ninth
refusal; exact pre-merge and terminal merge-parent replay; malformed state and
ledger entries; and every pending/ledger/state/clear interruption window. The
audit-fix runner is
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`; the
CLI report format is `unittest-json-v1`, the report file is
`tmp/elenchus/fiat-556-step-3.json`, and the expected JSON schema is
`elenchus.unittest.v1`. The `{report}` placeholder occurs exactly once.

**Disciplines.** phylax: exact remote refs, Git objects, runbook paths, and
GitHub responses are untrusted bounded inputs; use no shell, fixed commands,
stable rereads, caps, strict shapes, and no raw response or credential in
state. ephoros: state, controller-ledger events, status, and packets must answer
which relation/base/head is active, why it is stale, and whether a projection
or resolution is being shown. metron: none, the bounded reads have no time
budget or performance claim. elenchus: the halted #555 collision, ref races,
history rewrites, post-check base move, and interrupted receipt are causal
guards. hypomnema: the Fiat Promise and push discipline own the transition and
recovery; the versioning rationale is recorded in Step 4.

## Step 4: Record the decision, generations, and complete demonstration

**Goal.** Publish the durable relation-versus-resolution decision, update the
two governed generation records without changing either held frontier, and
demonstrate the full capability and legacy boundary on the final product tree.

**Entry.** Step 3's signed, audited, green head on the exact branch named by
the Step 4 implement directive, with relation parsing, anchor capture,
resolution, recovery, sync carriage, and final merge-parent guards already
green.

**Exit.** ADR-006 carries one dated issue-556 addendum defining a generation
relation separately from its resolved label. Fiat and Protasis each have one
new generation row and matching `SKILL.md` metadata selected by the declared
relation from the exact integration base; evolution, epoch, frontier status,
revision, digest, current-frontier text, and held next-job text remain exact.
No literal future label is introduced into this runbook. The tracked study and
runbook still match their receipts, Promise Machine copies and coverage agree,
the complete #555/concurrent-generation demonstration passes, the run's own
audit record is append-only, and every repository gate below is green:

```bash
cmp .hexaemeron/study.md plugins/hexaemeron/docs/fiat-version-relations/study.md
cmp .hexaemeron/runbook.md plugins/hexaemeron/docs/fiat-version-relations/runbook.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study .hexaemeron/study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py .hexaemeron/runbook.md
python3 -m unittest plugins.hexaemeron.tests.test_version_relations plugins.hexaemeron.tests.test_protasis_checker
python3 -m unittest discover -s tests -p 'test_evolution_contract.py'
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
python3 scripts/promise_machine.py sync --check
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

**Files.** `docs/decisions/ADR-006-skill-ledgers-are-not-semver.md`,
`plugins/hexaemeron/skills/fiat/EVOLUTION.md`,
`plugins/hexaemeron/skills/fiat/SKILL.md`,
`plugins/hexaemeron/skills/protasis/EVOLUTION.md`,
`plugins/hexaemeron/skills/protasis/SKILL.md`,
`plugins/hexaemeron/tests/test_fiat_skill.py`,
`tests/test_evolution_contract.py`,
`tests/promise_machine_coverage.json`,
`tests/test_promise_machine_contract.py`,
`audit/rounds/fiat-556-resolve-runbook-target-versions-at-integrate.md`, and
`.horos/boundary.json` only if a deterministic Horos scan changes it.

**Tests.** Re-run every focused case from Steps 1 through 3, both complete
suites, evolution and Promise Machine contracts, all three non-Solidity audit
lints, per-file Imprimatur then Brevitas for changed prose, receipt byte
comparisons, relative-link checks, Python compilation, Horos, and diff checks.
Preserve a source-runner red report from the pinned parent and a fresh green
report from the exact final tree. The audit-fix runner is
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`; the
CLI report format is `unittest-json-v1`, the report file is
`tmp/elenchus/fiat-556-step-4.json`, and the expected JSON schema is
`elenchus.unittest.v1`. The `{report}` placeholder occurs exactly once.

**Disciplines.** phylax: final checks prove the bounded input controls from
Steps 1 through 3 still compose; no new boundary is added here. ephoros: final
status and packet fixtures prove the relation, exact evidence, staleness, and
bootstrap limitation remain visible. metron: none, no performance claim.
elenchus: the complete parent-red/final-green report and focused regressions
demonstrate the prototype rather than substituting prose for it. hypomnema:
ADR-006 is the durable home for the non-SemVer relation decision; the ledgers
record behaviour and the tracked study/runbook preserve its source contract.

## Integration boundary

The final step does not claim that this self-hosted run used the new receipt.
Before publication, reread `origin/main` and resolve both relation rows against
that exact commit. If either product projection changed, put only the required
ledger/header/metadata correction in the signed two-parent sync merge, include
every changed target path in `fiat-integration-revalidation/v1`, and rerun the
covering checks. If evolution, epoch, or any held frontier field changed, or if
the existing controller cannot carry a necessary correction through its
already-governed sync path, halt. The integration PR uses a merge commit; its
final parent pair and GitHub verification are checked before the existing
controller's terminal receipt.

The closing issue comment must name this bootstrap boundary, any signed sync
correction, the exact test/report evidence, and the items still owned by #555,
#557, #508, the held Fiat job, and the held Protasis job. It follows
Sapheneia, Imprimatur, Vulgate, Imprimatur, is posted verbatim, and is read back
before issue closure is receipted.

### Amendment -- 2026-08-24

**What changed.** Complete replacement Exit: The tracked study at
`docs/fiat-version-relations-study.md` and the tracked runbook at
`plugins/hexaemeron/docs/fiat-version-relations/runbook.md` are byte-identical
to their currently receipted sources. The misplaced
`plugins/hexaemeron/docs/fiat-version-relations/study.md` copy is absent. From
the study's direct-root-docs location, all five `../plugins/...` links resolve
to their canonical skill files. `protasis.py` reports P006 for a
present-but-malformed relation block, a duplicate target or path, an unsafe
path, an unknown relation, a blank row, or a concrete governed target token
outside the block. It accepts no block, one valid block before Step 1, partial
target coverage, and fenced decoys. The Protasis contract states that this is
a structure verdict, not a suitability or version-allocation verdict. Prove
the exit with:

```bash
cmp .hexaemeron/study.md docs/fiat-version-relations-study.md
cmp .hexaemeron/runbook.md plugins/hexaemeron/docs/fiat-version-relations/runbook.md
test ! -e plugins/hexaemeron/docs/fiat-version-relations/study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study .hexaemeron/study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py .hexaemeron/runbook.md
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs/fiat-version-relations-study.md plugins/hexaemeron/docs/fiat-version-relations/runbook.md
python3 -m unittest plugins.hexaemeron.tests.test_protasis_checker
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
```

Complete replacement Files: `docs/fiat-version-relations-study.md`,
`plugins/hexaemeron/docs/fiat-version-relations/study.md` for removal of the
misplaced copy,
`plugins/hexaemeron/docs/fiat-version-relations/runbook.md`,
`plugins/hexaemeron/skills/protasis/SKILL.md`,
`plugins/hexaemeron/skills/protasis/scripts/protasis.py`,
`plugins/hexaemeron/tests/test_protasis_checker.py`,
`plugins/hexaemeron/tests/test_fiat_skill.py`,
`tests/promise_machine_coverage.json`,
`audit/rounds/fiat-556-resolve-runbook-target-versions-at-integrate.md`, and
`.horos/boundary.json` only if a deterministic Horos scan changes it.

**Why.** The study must remain byte-identical to its receipt, so its five
relative links cannot be rewritten. At the plugin-local docs path each
`../plugins/...` target resolves under `plugins/hexaemeron/docs/plugins/`,
which does not exist. A direct child of root `docs/` makes the same bytes
resolve under root `plugins/`. The runbook contains no relative Markdown link,
so moving it would add path churn without repairing evidence. Step 4's baseline
Exit repeats the old study path and is therefore marked broken below. After
Step 1 is complete, a separate Step-4-only amendment must replace that distinct
Exit; combining two different complete Exit values here is not admitted by the
one-value-per-field amendment grammar.

**Steps touched.** Step 1.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit broken.

### Amendment -- 2026-08-28

**What changed.** Complete replacement Exit: ADR-006 carries one dated
issue-556 addendum defining a generation relation separately from its resolved
label. Fiat and Protasis each have one new generation row and matching
`SKILL.md` metadata selected by the declared relation from the exact
integration base; evolution, epoch, frontier status, revision, digest,
current-frontier text, and held next-job text remain exact. No literal future
label is introduced into this runbook. The tracked study at
`docs/fiat-version-relations-study.md` and the tracked runbook at
`plugins/hexaemeron/docs/fiat-version-relations/runbook.md` are byte-identical
to their currently receipted sources. The misplaced
`plugins/hexaemeron/docs/fiat-version-relations/study.md` copy is absent. From
the study's direct-root-docs location, all five `../plugins/...` links resolve
to their canonical skill files. Promise Machine copies and coverage agree,
the complete #555/concurrent-generation demonstration passes, the run's own
audit record remains append-only, and every repository gate below is green:

```bash
cmp .hexaemeron/study.md docs/fiat-version-relations-study.md
cmp .hexaemeron/runbook.md plugins/hexaemeron/docs/fiat-version-relations/runbook.md
test ! -e plugins/hexaemeron/docs/fiat-version-relations/study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study .hexaemeron/study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py .hexaemeron/runbook.md
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs/fiat-version-relations-study.md plugins/hexaemeron/docs/fiat-version-relations/runbook.md
python3 -m unittest plugins.hexaemeron.tests.test_version_relations plugins.hexaemeron.tests.test_protasis_checker
python3 -m unittest discover -s tests -p 'test_evolution_contract.py'
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
python3 scripts/promise_machine.py sync --check
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

**Why.** Step 1's receipted amendment moved the byte-identical study to the
direct root `docs/` path so its five unchanged relative links resolve. Step
4's baseline Exit retained the old plugin-local study path and was therefore
recorded as broken. This replacement keeps the complete Step 4 decision,
generation, demonstration, and repository-gate contract while correcting its
publication-path checks. No other Step 4 field changes.

**Steps touched.** Step 4.

**Still holding.** Step 4: entry holds; exit holds.
