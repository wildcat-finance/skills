# Runbook: honest step-branch extensions after push receipts

Derived from `.hexaemeron/study.md`, whose Study receipt binds SHA-256
`f04eaa0963cb1ff461193c4d3565f40829fa9cb20f58c079ae3e8db67bc32992`.
The run starts from `main` at
`7e97b5195d5b0e43146b4200f26cd41b89003413`. Two steps keep the accepted
specification separate from the controller change while requiring the
classification, executable guard, durable guidance, generated copy, and
version record to ship as one product change.

```version-relations
fiat | plugins/hexaemeron/skills/fiat/EVOLUTION.md | next-generation-after-integration-base
```

The relation is not a reservation. The implementation may project the next
ordinary generation while building, but integration resolves the row against
one exact integration base. The held issue #363 frontier, its digest, and every
unrelated carryover remain unchanged.

## Step 1: Commit the receipted specification

**Goal.** Put the current run's accepted Study and Runbook in stable repository
locations before controller behaviour changes.

**Entry.** Run branch
`fiat/923-honest-step-branch-extensions-after-push-rec` at
`7e97b5195d5b0e43146b4200f26cd41b89003413`, with the Study receipt and
post-spec marketplace receipt recorded, both ignored artefacts mechanically
clean, and no tracked worktree change.

**Exit.** `docs/fiat-step-branch-extensions-study.md` matches the receipted
Study under one exact presentation-only transformation: terminal two-space
Markdown hard breaks on physical lines 3, 4, and 5 become terminal `<br>`
tags. `docs/fiat-step-branch-extensions-runbook.md` is byte-identical to
`.hexaemeron/runbook.md`. Relative links resolve from their tracked locations.
Protasis accepts both tracked files, Imprimatur finds no defect, Hypomnema
accepts their pointers, the checked repository runner selects and passes every
owner required by the diff, and the tree has no undeclared tracked change.
Prove the exit with:

```bash
cmp <(sed '3,5s/  $/<br>/' .hexaemeron/study.md) docs/fiat-step-branch-extensions-study.md
cmp .hexaemeron/runbook.md docs/fiat-step-branch-extensions-runbook.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/fiat-step-branch-extensions-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/fiat-step-branch-extensions-runbook.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-step-branch-extensions-study.md docs/fiat-step-branch-extensions-runbook.md
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs/fiat-step-branch-extensions-study.md docs/fiat-step-branch-extensions-runbook.md
python3 scripts/run_checks.py
git diff --check
```

**Files.** `docs/fiat-step-branch-extensions-study.md`,
`docs/fiat-step-branch-extensions-runbook.md`,
`audit/rounds/fiat-923-honest-step-branch-extensions-after-push-rec.md`, its
generated synopsis, and `.horos/boundary.json` only when the deterministic
scan earns a change.

**Tests.** No product test changes in this step. Run the exact transformed
Study comparison, byte-identical Runbook comparison, Protasis in both modes,
Imprimatur, Hypomnema, the checked runner, and diff check from the Exit. The
source-bound audit-fix runner is
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`;
the CLI report format is `unittest-json-v1`, the report file is
`.elenchus/fiat-923-step-1.json`, and the expected JSON schema is
`elenchus.unittest.v1`. The `{report}` placeholder occurs exactly once.

**Disciplines.** phylax: no executable boundary changes; the two bounded UTF-8
documents add no dependency, process, URL fetch, credential, or model action.
ephoros: no runtime signal changes; the Study already names the later operator
questions. metron: none, because this step makes no performance change or
claim. elenchus: no failure is repaired in this step, so no new guard is
claimed. hypomnema: the tracked copies preserve the design source, while the
governed Fiat generation row remains the standing decision record written in
Step 2.

## Step 2: Classify descendant tips and reverify their complete range

**Goal.** Let a waiting step branch continue only when its receipted head is
still in native history, while retaining every later signature, provenance,
GitHub, author, committer, pull-request, order, and integration gate.

**Entry.** Step 1's signed, audited, green head on the exact branch named by
the Step 2 implement directive. The tracked Study and Runbook match their
receipts, the run remains before integration, Fiat v5.38.1's author/publisher
split is unchanged, and `refuse_rewritten_stack` still rejects every unequal
waiting tip.

**Exit.** Equality remains the zero-relation-call path. After legacy
abbreviated identity resolution, an unequal waiting tip passes the topology
guard only when native `git merge-base --is-ancestor <recorded> <tip>` answers
status 0. Status 1 refuses with both exact commits and the branch without
asserting an unobserved GitHub cause; a missing object, timeout, start failure,
output cap, or any other status refuses as unknown. Fixed argv disables
replacement objects, lazy fetch, prompts, and inherited `GIT_*` substitution.
Current and already merged steps retain their existing skip rules. Every
refusal occurs before state or ledger mutation.

The focused real-repository fixture proves `P -> E`, equality without a
relation call, unrelated history, unavailable ancestry, replacement-ref
resistance, hostile inherited Git state, legacy abbreviated ancestor and
non-ancestor cases, skip behaviour, and byte-identical refusal state. The
descendant's later `done merge-step` proof records a repaired `effective_push`
for the exact live range after local signature/trailer and GitHub verification,
with author and committer attribution re-derived together, while the original
push receipt stays unchanged. Existing rewritten-stack, stack-topology, PR
head/base, run-branch movement, attribution, publisher-separation, and final
integration tests remain green.

The operator rule is aligned in `push-discipline.md`; ADR-021 is narrowed only
where it equated every unequal tip with a rewrite; the Fiat skill and Promise
Machine wording distinguish topology admission from current effective-push
evidence. ADR-052 remains unchanged. A proof document records the focused
red-on-parent and green-on-head results plus the three issue-904 ancestry
checks. The Fiat generation row records the chosen ancestry rule, the deferred
merge-time verification trade, the rejected re-receipt, repeated-preflight,
and permanent-equality options, the public issue and delivery links, and the
unchanged held frontier. The governed skill metadata matches the resolved row.
Hexaemeron package metadata advances by the repository's package-version rule,
portable runtime copies and their manifest are regenerated, Promise Machine
coverage agrees, and Horos reaches a deterministic fixpoint.

Prove the exit with:

```bash
python3 -m unittest discover -s plugins/hexaemeron/tests -p 'test_step_branch_extensions.py' -v
python3 plugins/hexaemeron/tests/test_push_receipt_identity.py -v
python3 plugins/hexaemeron/tests/test_stack_topology.py -v
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/portable_promise_machine.py check
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 -m unittest discover -s tests -p 'test_evolution_contract.py'
python3 -m unittest discover -s tests -p 'test_version_propagation.py'
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-step-branch-extensions-study.md docs/fiat-step-branch-extensions-runbook.md docs/fiat-step-branch-extensions-proof.md docs/decisions/ADR-021-land-a-rewritten-stack-from-the-original-commits.md plugins/hexaemeron/skills/fiat/SKILL.md plugins/hexaemeron/skills/fiat/EVOLUTION.md plugins/hexaemeron/skills/fiat/references/push-discipline.md
python3 scripts/run_checks.py
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

**Files.** `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/tests/test_step_branch_extensions.py`,
`plugins/hexaemeron/tests/test_push_receipt_identity.py`,
`plugins/hexaemeron/skills/fiat/references/push-discipline.md`,
`docs/decisions/ADR-021-land-a-rewritten-stack-from-the-original-commits.md`,
`docs/fiat-step-branch-extensions-proof.md`,
`plugins/hexaemeron/skills/fiat/EVOLUTION.md`,
`plugins/hexaemeron/skills/fiat/SKILL.md`,
`plugins/hexaemeron/.claude-plugin/plugin.json`,
`plugins/hexaemeron/.codex-plugin/plugin.json`,
`.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`,
`tests/test_version_propagation.py`,
`tests/test_child_or_golden_retriever_primer.py`,
`plugins/hexaemeron/tests/test_phylax_model_proxy.py`,
`tests/promise_machine_coverage.json`,
`.agents/skills/promise-machine/runtime/` as generated by
`scripts/portable_promise_machine.py`,
`audit/rounds/fiat-923-honest-step-branch-extensions-after-push-rec.md`, its
generated synopsis, and `.horos/boundary.json` as generated by Horos. No other
product path is in scope.

**Tests.** First preserve the raw-equality failure against Step 2's entry and
then the passing implementation result. Run every focused case and complete
suite named above without skips being counted as executed. The source-bound
audit-fix runner is
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report} plugins/hexaemeron/tests/test_step_branch_extensions.py`;
the CLI report format is `unittest-json-v1`, the report file is
`.elenchus/fiat-923-step-2.json`, and the expected JSON schema is
`elenchus.unittest.v1`. The `{report}` placeholder occurs exactly once. Warden
must return the Elenchus verdict without translating an inconclusive report
into a guard.

**Disciplines.** phylax: review exact remote-ref and native local-graph inputs,
fixed argv, the scrubbed Git environment, `--no-replace-objects`, status
0/1/error separation, timeout/output bounds, and the unchanged later GitHub
evidence boundary. ephoros: refusals name the step, branch, recorded head,
observed tip, and whether the answer is non-ancestor or unknown; they claim no
unobserved rewrite cause and add no persistent telemetry. metron: no
performance claim; equality remains zero-call and each unequal waiting branch
gets at most one bounded local relation call. elenchus: reproduce issue 904's
raw-equality failure in a minimal real `P -> E` graph, observe the new focused
test red on the unfixed parent and green on the implementation, and keep every
neighbouring test green. hypomnema: the Fiat generation row is the one durable
decision home; ADR-021 and operator guidance are aligned without a duplicate
ADR, ADR-052 stays separate, and interface comments explain the deferred
evidence boundary rather than restating code.

## Integration boundary

Before integration, reread `origin/main` and resolve the declared Fiat relation
against that one exact commit. If the projected generation or package metadata
is stale, use only the controller's signed `sync-run` path with a complete
affected-path revalidation receipt. Halt if any evolution epoch, maturity,
frontier status, held target, or digest changed unexpectedly, or if the current
controller cannot carry the correction without rewriting product history.

Merge Step 1 and then Step 2 into the run branch in controller order. Open one
run-level pull request to `main` whose exact body contains
`Closes wildcat-finance/skills#923`. Shoggoth remains the Git author; Laurence
Day is the explicitly authorised committer and signer under key
`B83B60AE16F5DD1A`; the `shoggoth-wildcat-labs[bot]` application publishes the
pull requests and issue comment. The closing comment carries the four relation
outcomes, exact guard and suite evidence, the merge-time verification-window
qualification, the unchanged issue #363 frontier, and every unrelated PR-922
carryover as outside this delivery. Shape it with Sapheneia, then run
Imprimatur, Vulgate with content held fixed, and Imprimatur again on the exact
posted bytes. Read every publication back without credentials and require HTTP
200 before receipting integration.
