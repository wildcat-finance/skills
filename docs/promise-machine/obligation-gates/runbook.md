# Runbook: reconstruct Promise Machine obligation gates

Derived from `.hexaemeron/study.md` at exact Fiat entry ref
`7e97b5195d5b0e43146b4200f26cd41b89003413`. Seven dependency-ordered steps
implement the study's four delivery slices. The runtime, composition,
provenance, evaluation, and demonstration boundaries are separate so each
audit sees one claim surface. Every step is one pull request, starts from the
preceding green head, and leaves the repository green. This run changes the
root framework and no governed skill generation, so there is no
`version-relations` block.

## Step 1: Scaffold the obligation contract and gate bijection

**Goal.** Commit the accepted specification and establish the root-law marker,
obligation registry, production-selector, and negative-specimen scaffold.

**Entry.** Clean step branch cut from
`fiat/884-reconstruct-promise-machine-obligation-gates` at
`7e97b5195d5b0e43146b4200f26cd41b89003413`; before writing the decision
record, confirm that ADR-054 remains free on the current branch.

**Exit.** The accepted study and runbook are committed under
`docs/promise-machine/obligation-gates/`; `PROMISE_MACHINE.md` carries unique
stable markers for the structural obligations selected in this step; every
discovered marker has exactly one registry row with a production gate,
negative specimen, stable finding code, consequence, blocked transition, and
recovery; and missing, duplicate, malformed, extra, or non-failing bindings
stop by obligation id. The existing `.python-version`, `LICENSE`, and CI files
remain unchanged. Prove the exit with `python3 scripts/promise_machine.py
sync`, `python3 scripts/promise_machine.py sync --check`, `python3
scripts/portable_promise_machine.py sync`, `python3
scripts/portable_promise_machine.py check`, `python3
scripts/promise_machine.py check --only law,copies,obligations`, `python3 -m
unittest tests.test_promise_machine_contract`, `python3 tests/run_tests.py`,
`python3 scripts/run_checks.py --scope promise-machine --jobs 12`, and `git
diff --check`.

**Files.** `PROMISE_MACHINE.md`, generated `plugins/*/PROMISE_MACHINE.md`,
`scripts/promise_machine.py`, `scripts/portable_promise_machine.py`, generated
`.agents/skills/promise-machine/runtime/`,
`tests/promise_machine_obligations.json`,
`tests/test_promise_machine_contract.py`, bounded fixtures under
`tests/fixtures/promise-machine/obligations/`,
`docs/promise-machine/obligation-gates/study.md`,
`docs/promise-machine/obligation-gates/runbook.md`,
`docs/decisions/ADR-054-bind-promise-obligations-to-gates.md`, and generated
ownership or Horos boundary files only when their checked regeneration
requires them.

**Tests.** Add one clean registry case and mutations for an unmarked
obligation, malformed or duplicate marker, missing or duplicate row, unknown
selector, missing or escaping specimen, unexpected specimen finding,
duplicate JSON key, and registry-only obligation. Removing a real production
gate while retaining its row must make that row's specimen fail. Expected new
focused cases: 14 to 20. Elenchus runner contract: command `python3
tests/run_tests.py --elenchus-report {report}`; report format
`elenchus.unittest.v1`; report file
`.elenchus/promise-obligations-step-1.json`.

**Disciplines.** phylax: the checker gains bounded Markdown, JSON, and fixture
inputs and must confine paths, reject duplicate keys and symlink escapes, and
avoid execution. ephoros: stable obligation id, finding code, consequence,
blocked transition, and recovery make each refusal actionable without external
telemetry. metron: none, this step makes no performance claim. elenchus: every
accepted bad binding begins as a red specimen and remains a guard. hypomnema:
the marker and bijection design is expensive to reverse and belongs in
ADR-054, while the study and runbook are the durable build contract.

## Step 2: Enforce consequence, exception, and refusal semantics

**Goal.** Enforce distinct consequence paths, complete exception resolution,
non-authorising unknowns, structured refusals, and the core checker's
side-effect boundary.

**Entry.** Step 1's green head with obligation discovery, registry, generated
copies, and structural negative specimens passing.

**Exit.** Levels zero through three take distinct evidence and authority
paths; level three refuses level-two-only evidence; `unknown`, `not-run`,
missing evidence, and unresolved declarations cannot authorise a positive
transition; exceptions require resolvable authority, promise and gate,
subject, scope, durable record, expiry, and revocation state; and every refusal
reports promise id, obligation id when known, finding code, consequence,
blocked transition, and recovery in text and canonical JSON. Static and
behavioural guards refuse network, credential, shell, general subprocess, and
evidence-command execution in the core checker. Prove the exit with `python3
scripts/promise_machine.py check --only
obligations,structure,contracts,exceptions,imports`, the same command with
`--json`, `python3 -m unittest tests.test_promise_machine_contract`, `python3
plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests`, `python3
plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests`, and
`python3 scripts/run_checks.py --scope promise-machine --jobs 12`.

**Files.** `PROMISE_MACHINE.md`, generated Promise Machine copies and portable
runtime, `scripts/promise_machine.py`,
`tests/promise_machine_obligations.json`,
`tests/test_promise_machine_contract.py`, any schema introduced for structured
records, and focused fixtures under
`tests/fixtures/promise-machine/{consequences,exceptions,imports,findings}/`.

**Tests.** Add positive and negative cases for every consequence level;
level-three replay of level-two evidence; unknown, not-run, absent, and stale
evidence; missing or mismatched authorising declarations; absent, expired,
revoked, unresolvable, subject-mismatched, and scope-mismatched exceptions;
calendar-invalid timestamps; forbidden imports and calls; and text/JSON
finding parity. Expected new focused cases: 24 to 36. Elenchus runner contract:
command `python3 tests/run_tests.py --elenchus-report {report}`; report format
`elenchus.unittest.v1`; report file
`.elenchus/promise-obligations-step-2.json`.

**Disciplines.** phylax: exception and evidence records are untrusted local
inputs and the core checker must remain standard-library-only, offline,
bounded, read-only, and non-executing. ephoros: this step owns the stable
refusal payload used to locate and recover a stopped transition. metron: none,
the parsers make no speed claim. elenchus: each currently accepted malformed
or over-authorising record is captured red before repair and retained.
hypomnema: ADR-054 and the root law record the distinct level-three and
complete exception semantics.

## Step 3: Bind runtime promises to domain-native evidence

**Goal.** Replace descriptive runtime coverage with executable bindings to
domain-native results or explicit small adapters, without a universal result
envelope.

**Entry.** Step 2's green head with consequence, exception, refusal, and
side-effect semantics enforced; the exact required runtime set is discovered
from `tests/promise_machine_coverage.json` at this entry.

**Exit.** Every required level-two or level-three runtime row names a
resolvable reader and positive and negative specimens; each reader resolves
promise identity, subject, scope, evidence references and classes, unknowns,
transition, exception state, and source digest from its native result or a
bounded adapter. Level-three rows additionally resolve authority and
independently inspectable evidence. Mutating any required field produces the
row's stable refusal. The readers establish structural binding only and never
claim that the underlying campaign, audit, conversion, sync, placement, or
transformation ran. Prove the exit with `python3 scripts/promise_machine.py
coverage --check`, `python3 scripts/promise_machine.py check --only
obligations,contracts,coverage,runtime`, `python3 -m unittest
tests.test_promise_machine_contract`, the affected domain suites discovered by
the coverage rows, and `python3 scripts/run_checks.py --scope promise-machine
--jobs 12`.

**Files.** `scripts/promise_machine.py`,
`tests/promise_machine_coverage.json`,
`tests/promise_machine_obligations.json`,
`tests/test_promise_machine_contract.py`, exact coverage-declared source or
adapter paths that need a binding surface, and bounded specimens under
`tests/fixtures/promise-machine/runtime/`; generated portable runtime,
ownership map, and Horos boundary files only when checked regeneration
requires them.

**Tests.** Discover the required runtime rows independently, execute each row,
and mutate every required binding field. Add refusals for duplicate keys,
wrong promise id, subject or scope mismatch, missing or unsupported satisfying
evidence, absent reference, hidden unknown, wrong transition, malformed
exception state, missing level-three authority, escaping path, symlink,
non-file, oversize, and invalid UTF-8. Elenchus runner contract: command
`python3 tests/run_tests.py --elenchus-report {report}`; report format
`elenchus.unittest.v1`; report file
`.elenchus/promise-obligations-step-3.json`.

**Disciplines.** phylax: readers cross heterogeneous local-file boundaries and
must parse bounded data without invoking the owning skill or following paths
outside the checkout. ephoros: row id, source, missing field, evidence class,
consequence, blocked transition, and recovery survive in each refusal. metron:
none, no performance claim is made. elenchus: every field mutation is first
observed red and remains a row-specific guard. hypomnema: ADR-054 records why
native readers and small adapters are used instead of a universal envelope.

## Step 4: Enforce every declared composition handoff

**Goal.** Register and execute all seven root-law producer-to-consumer
relations so required fields and unknowns survive composition.

**Entry.** Step 3's green head with every required runtime row resolving its
own structural evidence and high-consequence binding.

**Exit.** The checker discovers the seven law-named relations, requires each
to name producer, consumer, preserved fields, consumer transition, and refused
overclaim, and evaluates composed specimens. Removing a relation, producer
evidence, required preserved field, unknown, conflict, or consumer refusal
stops that transition by stable relation and promise ids. Composition never
upgrades recorded evidence into checked, measured, recomputed, or proved
evidence. Prove the exit with `python3 scripts/promise_machine.py coverage
--check`, `python3 scripts/promise_machine.py check --only
obligations,coverage,composition`, `python3 -m unittest
tests.test_promise_machine_contract`, the affected producer and consumer
suites, and `python3 scripts/run_checks.py --scope promise-machine --jobs 12`.

**Files.** `PROMISE_MACHINE.md`, generated Promise Machine copies and portable
runtime, `scripts/promise_machine.py`,
`tests/promise_machine_coverage.json`,
`tests/promise_machine_obligations.json`,
`tests/test_promise_machine_contract.py`, affected existing producer/consumer
fixtures, and cross-skill specimens under
`tests/fixtures/promise-machine/composition/`.

**Tests.** Execute one passing and at least one failing specimen for each of
the seven relations. Mutate producer identity, evidence references, unknowns,
conflicts, subject, scope, consequence, preserved fields, consumer transition,
and refused-overclaim declaration; remove each relation in turn; and prove a
recorded or model-graded producer cannot satisfy a stronger domain-operation
claim. Expected new focused cases: 21 to 30. Elenchus runner contract: command
`python3 tests/run_tests.py --elenchus-report {report}`; report format
`elenchus.unittest.v1`; report file
`.elenchus/promise-obligations-step-4.json`.

**Disciplines.** phylax: composition consumes two bounded local result
surfaces and must preserve both boundaries without running either producer or
consumer. ephoros: every stop names relation, producer, consumer, lost field,
blocked transition, and recovery. metron: none, no performance claim.
elenchus: each removed relation or field is an observed guard. hypomnema:
ADR-054 owns the composition contract, so no second decision record is needed.

## Step 5: Preserve vendored provenance and promise-id continuity

**Goal.** Bind vendored overlays to an upstream identity and make promise ids
an append-only checked interface with explicit retirement, rename, and split
records.

**Entry.** Step 4's green head with current promises, obligations, runtime
bindings, and composition relations discoverable by the checker.

**Exit.** Each vendored overlay records repository URI, immutable full commit,
path, upstream blob digest, local digest, and verification status without
strengthening an unresolved publisher-authentication unknown. The offline core
validates committed provenance shape and local consistency; a separate bounded
command verifies upstream bytes only for affected vendored paths and never
runs from the core check. The history file is seeded from the Fiat entry ref,
contains every current promise id once, and requires explicit continuity for
retirement, rename, or split. Missing provenance, mutable-only identity,
silent id removal, duplicate history id, active id without a declaration, or
one id reused for split semantics fails by stable code. Prove the exit with
`python3 scripts/promise_machine.py check --only
obligations,overlays,history`, the bounded upstream-verification command named
by the implementation with its network denied in the normal core path,
`python3 -m unittest tests.test_promise_machine_contract`, `python3
plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests`, `python3
plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md
.agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md
plugins docs`, and `python3 scripts/run_checks.py --scope promise-machine
--jobs 12`.

**Files.** `plugins/hexaemeron/PROMISES.md`, other discovered vendored overlays
owned by the current inventory, `scripts/promise_machine.py`, the separate
bounded upstream verifier if one is required,
`tests/promise_machine_id_history.json`,
`tests/test_promise_machine_contract.py`, focused fixtures under
`tests/fixtures/promise-machine/{history,upstream-provenance}/`,
`docs/decisions/ADR-003-bind-vendored-promises-with-digests.md`, and ADR-054
when its cross-reference needs the final record name.

**Tests.** Add a clean seeded history and mutations for deletion, duplicate
id, missing current declaration, undeclared active id, malformed entry ref,
unrecorded retirement, rename, split, and semantic split under one id. For
each vendored overlay, require repository, commit, path, upstream bytes, and
local digest and reject missing, mutable-only, malformed, duplicate,
host-switched, redirected, oversized, or local-digest-mismatched evidence.
Keep the normal core verification offline. Elenchus runner contract: command
`python3 tests/run_tests.py --elenchus-report {report}`; report format
`elenchus.unittest.v1`; report file
`.elenchus/promise-obligations-step-5.json`.

**Disciplines.** phylax: history and local metadata are bounded inputs, while
the separate verifier allowlists HTTPS host, repository, immutable commit, and
path, caps time and bytes, uses fresh temporary storage, and follows no
cross-host redirect. ephoros: failures name overlay or promise id, expected
continuity action, blocked transition, and recovery. metron: none, no
performance claim. elenchus: each silent history or provenance loss starts as
a red mutation and remains a guard. hypomnema: the changed vendored-identity
meaning amends ADR-003, while ADR-054 owns continuity semantics.

## Step 6: Record prompt and campaign evidence without substitution

**Goal.** Generalise the existing one-context emit-and-tally boundary for the
eleven fixture-only promises while keeping model grades separate from domain
operation evidence.

**Entry.** Step 5's green head with stable promise identities, runtime readers,
composition semantics, and vendored provenance checks.

**Exit.** A dependency-free driver discovers exactly the eleven fixture-only
promises, emits one request per isolated case and a manifest written last, and
tallies a closed answer sheet into a run record bound to full model id, prompt
template digest, corpus digest, tree digest, date, raw answer identities, and
the exact case set. Missing, duplicate, extra, edited, leaked, partial,
interrupted, or `not-run` answers refuse. A grade satisfies only its declared
evaluation gate; any promise that claims a campaign, audit, conversion, sync,
pre-audit, placement, or transformation remains blocked without the owning
skill's real record. Prove the exit with the driver's `emit`, `tally`, and
`verify` commands over committed demonstration answers, `python3
scripts/promise_machine.py coverage --check`, `python3
scripts/promise_machine.py check --only
obligations,coverage,evaluation`, `python3 -m unittest
tests.test_promise_evaluation_driver tests.test_promise_machine_contract`, the
affected Hexaemeron and Sapheneia suites, and `python3 scripts/run_checks.py
--scope promise-machine --jobs 12`.

**Files.** `tests/promise_evaluation_driver.py`,
`tests/test_promise_evaluation_driver.py`,
`tests/promise_machine_coverage.json`, the existing Hexaemeron and Sapheneia
Promise Machine evaluation corpora and tests, shared fixtures under
`tests/fixtures/promise-machine/evaluation/`, committed demonstration answers
and run records under `docs/promise-machine/obligation-gates/`, ADR-066, and
`tests/check-map-v1.json` if ownership of a new driver is not already covered.

**Tests.** Cover exact eleven-promise discovery; one-context-per-case packet
isolation; request-only prompts; manifest-last atomicity; digest and tree
binding; existing-directory, symlink, escape, non-file, oversize, invalid
UTF-8, missing, duplicate, extra, closed-vocabulary, partial, interrupted, and
edited answer refusals; deterministic tally; no corpus rewrite; and explicit
refusal when a grade is supplied without real domain evidence. Elenchus runner
contract: command `python3 tests/run_tests.py --elenchus-report {report}`;
report format `elenchus.unittest.v1`; report file
`.elenchus/promise-obligations-step-6.json`.

**Disciplines.** phylax: emit and tally open bounded write and untrusted-answer
boundaries, so they use confined paths, exclusive atomic creation, closed
schemas, and no model, credential, network, or subprocess client. ephoros: the
run record retains model, template, corpus, tree, date, case, and outcome
counts without logging requests, expected labels, credentials, or unrelated
context. metron: none, external model latency and cost are outside this
offline tool. elenchus: contamination, partial-write, and
evidence-substitution failures start red and remain guards. hypomnema: ADR-066
records the evaluation boundary and cites the existing router driver.

## Step 7: Demonstrate every gate from a clean tree

**Goal.** Reproduce the issue's complete mutation matrix and record one clean,
bounded framework demonstration with honest remaining limits.

**Entry.** Step 6's green head with every focused and affected suite passing
and no uncommitted product change.

**Exit.** From a clean tree, the demonstration exercises every discovered
obligation specimen, all ten issue-listed gate classes, every required runtime
binding, all seven composition relations, all vendored provenance rows, the
complete promise-id history, and the eleven-case evaluation record. Generated
copies and the Horos boundary are current, all selected repository checks
pass, and a durable record states exact counts, digests, commands, evidence
classes, unknowns, and non-goals. No model grade is reported as domain
execution and the demonstration makes no GitHub mutation. Prove the exit with
`test -z "$(git status --porcelain)"`, `python3 scripts/promise_machine.py
check`, `python3 scripts/promise_machine.py coverage --check`, the evaluation
driver's `verify` command over the committed run, `python3
scripts/promise_machine.py sync --check`, `python3
scripts/portable_promise_machine.py check`, `python3
plugins/horos/skills/horos/scripts/horos.py scan . --write`, a second clean
status check, `python3 scripts/run_checks.py --full --jobs 12 --report
.reports/issue-884-full.json`, Imprimatur over every shipped prose file,
Hypomnema over its complete tree arguments, and `python3
plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`.

**Files.** The final demonstration run record and evidence report under
`docs/promise-machine/obligation-gates/`, the evaluation driver and answers
only if reproduction exposes a defect, `.horos/boundary.json` only when
deterministic regeneration changes it, and audit source and synopsis files
only through the Fiat audit phase rather than this implementation step.

**Tests.** The commands above are the release demonstration. Record exact pass
counts for obligation markers, registry rows, negative specimens, runtime
rows, composition relations, history rows, provenance rows, evaluation cases,
and repository checks, plus every unresolved limit. Rerun the root and
affected plugin suites, whole check graph, generated-copy drift, Horos
currency, prose lints, and audit-synopsis currency. Elenchus runner contract:
command `python3 tests/run_tests.py --elenchus-report {report}`; report format
`elenchus.unittest.v1`; report file
`.elenchus/promise-obligations-step-7.json`.

**Disciplines.** phylax: the demo uses only committed bounded local inputs and
must not fetch, invoke a model, expose credentials, or follow an escaping path.
ephoros: the evidence report answers which gate failed, which transition
stopped, which evidence was checked, and how to recover while preserving
unknowns. metron: record durations only as observation; no budget or
optimisation claim exists. elenchus: any demo failure is reproduced at the
narrowest owning test before repair and retained as a guard. hypomnema: the
evidence report preserves commands, counts, digests, limits, and decision
references needed to reproduce the framework claim.

### Amendment -- 2026-08-30

**What changed.** Complete replacement Entry: A clean step branch cut from `fiat/884-reconstruct-promise-machine-obligation-gates` at `7e97b5195d5b0e43146b4200f26cd41b89003413`; before writing the decision record, confirm that ADR-054 remains free. Before any product edit, run the generated-copy checks, `python3 -m unittest tests.test_promise_machine_contract`, `python3 tests/run_tests.py`, and `python3 scripts/run_checks.py --scope promise-machine --jobs 12`. The first three must exit zero. Record and independently reproduce every failure from the aggregate command. The accepted pinned-parent exception set is exactly five pre-existing failures: macOS path exhaustion in `HexctlCheckpointTests.test_resource_limits_refuse_before_publish`; the stale root-audit digest in `Issue429RecoveryTests.test_root_audit_is_the_exact_pinned_base_blob`; fourteen unowned Homologia paths in `CheckMapContractTests.test_every_tracked_path_has_exactly_one_owner`; Python 3.14 accepting the deeply nested JSON used by `HexctlCheckpointTests.test_duplicate_state_and_ledger_keys_refuse`; and absent fixture Git objects in `IncidentAggregateTests`. No other baseline failure is accepted. Complete replacement Exit: The accepted study and runbook are committed under `docs/promise-machine/obligation-gates/`; `PROMISE_MACHINE.md` carries unique stable markers for the structural obligations selected in this step; every discovered marker has exactly one registry row with a production gate, negative specimen, stable finding code, consequence, blocked transition, and recovery; and missing, duplicate, malformed, extra, or non-failing bindings stop by obligation id. The existing `.python-version`, `LICENSE`, and CI files remain unchanged. Prove the affected surface with `python3 scripts/promise_machine.py sync`, `python3 scripts/promise_machine.py sync --check`, `python3 scripts/portable_promise_machine.py sync`, `python3 scripts/portable_promise_machine.py check`, `python3 scripts/promise_machine.py check --only law,copies,obligations`, `python3 -m unittest tests.test_promise_machine_contract`, `python3 tests/run_tests.py`, `python3 scripts/run_checks.py --scope promise-machine --plan`, `python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests`, `python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests`, `python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs`, `python3 plugins/horos/skills/horos/scripts/horos.py scan . --write`, a second `python3 scripts/promise_machine.py sync --check`, and `git diff --check`. Rerun `python3 scripts/run_checks.py --scope promise-machine --jobs 12` as a non-authorising baseline comparison: the only permitted failures are the same five pinned-parent failures named in the replacement Entry, and any additional or changed failure blocks the step.
**Why.** The exact pinned-parent aggregate failed before reconstruction and all five failures reproduced without a product edit. Four require unrelated Hexaemeron or historical-fixture changes; the fifth is generated ownership debt that cannot make the other four green. Broadening Step 1 would mix base repair into the obligation scaffold. The replacement keeps every affected Promise Machine, root, lint, generated-copy, and boundary check green while retaining the full aggregate as explicit negative evidence rather than calling its non-zero exit a pass.
**Steps touched.** Step 1.
**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds. Step 6: entry holds; exit holds. Step 7: entry holds; exit holds.

### Amendment -- 2026-08-30

**What changed.** Complete replacement Exit: The accepted study and runbook are committed under `docs/promise-machine/obligation-gates/`; `PROMISE_MACHINE.md` carries unique stable markers for the structural obligations selected in this step; every discovered marker has exactly one registry row with a production gate, negative specimen, stable finding code, consequence, blocked transition, and recovery; and missing, duplicate, malformed, extra, or non-failing bindings stop by obligation id. The existing `.python-version`, `LICENSE`, and CI files remain unchanged. Prove the affected surface with `python3 scripts/promise_machine.py sync`, `python3 scripts/promise_machine.py sync --check`, `python3 scripts/portable_promise_machine.py sync`, `python3 scripts/portable_promise_machine.py check`, `python3 scripts/promise_machine.py check --only law,copies,obligations`, `python3 -m unittest tests.test_promise_machine_contract`, `python3 tests/run_tests.py`, `python3 scripts/run_checks.py --scope promise-machine --plan`, `python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests`, `python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests`, `python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs`, `python3 plugins/horos/skills/horos/scripts/horos.py scan . --write`, a second `python3 scripts/promise_machine.py sync --check`, and `git diff --check`. Rerun `TMPDIR=/private/tmp python3 scripts/run_checks.py --scope promise-machine --jobs 12` as a non-authorising base comparison. The only permitted non-zero results are the following failures independently reproduced on exact pinned parent `7e97b5195d5b0e43146b4200f26cd41b89003413`: the five named Hexaemeron failures from the replacement Entry, with the Homologia ownership detail narrowed from fourteen to thirteen paths solely because the changed generated `plugins/homologia/PROMISE_MACHINE.md` now has its required Promise Machine owner; Synkrisis `BudgetCommandTests.test_small_budget_run_passes_and_records_its_method`, where macOS peak-RSS units are interpreted against the 512 MiB budget as 28,992 MiB or another host-run value; ten Goldfinch receipt-proof cases that stop at Lazarus's existing macOS `platform cannot anchor fixture stage` refusal; and the two `push` and `pull_request` subcases of Lazarus `ScaffoldTests.test_fixed_shell_ci_scope_toolchain_and_licence_remain_in_place`, whose current workflow-path parser finds no match. The Lazarus comparison must report exactly 599 tests and twelve failures with `TMPDIR=/private/tmp`. Any additional failure, missing expected pass, product-caused change outside the one Homologia ownership reduction, or unrecorded platform result blocks the step.
**Why.** The Step-owned ownership-map edit makes the aggregate select every current scope, revealing Synkrisis and Lazarus defects that the narrower pinned-parent plan did not execute. Both reproduce without the Step 1 product: Synkrisis fails on Python 3.14.6 because macOS reports peak RSS in bytes, and Lazarus reports the same twelve failures from the clean parent with a real-path temporary root. The replacement removes avoidable `/var` symlink noise, retains exact negative evidence for the remaining base defects, and does not authorise repairs outside the obligation scaffold.
**Steps touched.** Step 1.
**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds. Step 6: entry holds; exit holds. Step 7: entry holds; exit holds.

### Amendment -- 2026-08-31

**What changed.** Complete replacement Disciplines: phylax: readers cross heterogeneous local-file boundaries and must parse bounded data without invoking the owning skill or following paths outside the checkout. ephoros: row id, source, missing field, evidence class, consequence, blocked transition, and recovery survive in each refusal. metron: none, no performance claim is made. elenchus: every field mutation is first observed red and remains a row-specific guard. hypomnema: ADR-062 records why native readers and small adapters are used instead of a universal envelope.
**Why.** The pinned base had ADR-054 free, but the current default branch now uses ADR-054 for an unrelated decision and uses ADR-055 through ADR-061. The Step 3 study amendment receipts ADR-062 as the next collision-free identifier without changing the reader design or exit.
**Steps touched.** Step 3.
**Still holding.** Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds. Step 6: entry holds; exit holds. Step 7: entry holds; exit holds.

### Amendment -- 2026-08-31

**What changed.** Complete replacement Files: `scripts/promise_machine.py`, `tests/promise_machine_coverage.json`, `tests/promise_machine_obligations.json`, `tests/test_promise_machine_contract.py`, exact coverage-declared source or adapter paths that need a binding surface, bounded specimens under `tests/fixtures/promise-machine/runtime/`, `plugins/hexaemeron/tests/test_issue_429_recovery.py` and `plugins/hexaemeron/tests/test_phylax_model_proxy.py` only to replace assertions whose source-digest assumptions are superseded by the Step 3 runtime binding, and `docs/promise-machine/obligation-gates/runbook.md` only as the byte-identical repository copy of this receipted runbook; generated portable runtime, ownership map, and Horos boundary files only when checked regeneration requires them.
**Why.** Round 1 joined each runtime row to its declared positive evidence source and selector. Two affected Hexaemeron compatibility tests still require the earlier universal controller digest or a Phylax skill digest in runtime rows, so the domain suite now fails even though the production checker correctly requires the declared positive evidence digest. This amendment permits only those stale assertions and the checked-in runbook copy to move; it does not widen a runtime reader or claim that a domain operation ran.
**Steps touched.** Step 3.
**Still holding.** Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds. Step 6: entry holds; exit holds. Step 7: entry holds; exit holds.

### Amendment -- 2026-08-31

**What changed.** Complete replacement Disciplines: phylax: composition consumes two bounded local result surfaces and must preserve both boundaries without running either producer or consumer. ephoros: every stop names relation, producer, consumer, lost field, blocked transition, and recovery. metron: none, no performance claim. elenchus: each removed relation or field is an observed guard. hypomnema: ADR-066 owns the obligation and composition contract, so no second decision record is needed.
**Why.** The current default branch now owns ADR-062 through ADR-065, so the root uniqueness check rejects the previously receipted ADR-062 identifier. The study amendment records ADR-066 as the next collision-free standing identifier. This replacement changes only Step 4's decision reference; its entry, exit, files, tests, evidence boundaries, and seven-relation design remain unchanged.
**Steps touched.** Step 4.
**Still holding.** Step 4: entry holds; exit holds. Step 5: entry holds; exit holds. Step 6: entry holds; exit holds. Step 7: entry holds; exit holds.

### Amendment -- 2026-08-31

**What changed.** Complete replacement Files: `PROMISE_MACHINE.md`, generated Promise Machine copies and portable runtime, `scripts/promise_machine.py`, `tests/promise_machine_coverage.json`, `tests/promise_machine_obligations.json`, `tests/test_promise_machine_contract.py`, affected existing producer and consumer fixtures, and cross-skill specimens under `tests/fixtures/promise-machine/composition/`; `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, `plugins/hexaemeron/tests/test_hexctl_checkpoint.py`, `plugins/hexaemeron/tests/test_issue_429_recovery.py`, and `tests/check-map-v1.json` only for the exact upstream-established repairs to the five already receipted baseline defects; `docs/decisions/ADR-066-bind-promise-obligations-to-gates.md` and the byte-identical checked-in study and runbook copies for the collision-free standing decision and these amendments; generated runtime, ownership map, runtime specimen, coverage digest, and Horos boundary files only when checked regeneration requires them.
**Why.** The Step 4 exit requires the complete Hexaemeron and root dependencies selected by `python3 scripts/run_checks.py --scope promise-machine --jobs 12`. The five baseline defects already named in the receipted Step 1 amendments now have accepted fixes in upstream commit `4217f707fbb9174fcd13bca3cf6030771a50a693`; the incident fixture needs only its recoverable public Git object. Porting the narrow accepted path, depth, append-safe audit, and Homologia ownership hunks makes 1,990 of 1,990 Hexaemeron tests pass without changing a composition promise. The current default branch also owns ADR-062 through ADR-065, so ADR-066 and its append-only receipts are required for the root dependency. No Lazarus, Synkrisis, or other unrelated baseline is changed.
**Steps touched.** Step 4.
**Still holding.** Step 4: entry holds; exit holds. Step 5: entry holds; exit holds. Step 6: entry holds; exit holds. Step 7: entry holds; exit holds.

### Amendment -- 2026-08-31

**What changed.** Complete replacement Files: `tests/promise_evaluation_driver.py`, `tests/test_promise_evaluation_driver.py`, `scripts/promise_machine.py`, `tests/test_promise_machine_contract.py`, `tests/promise_machine_coverage.json`, the existing Hexaemeron and Sapheneia Promise Machine evaluation corpora and tests, shared fixtures under `tests/fixtures/promise-machine/evaluation/`, committed demonstration answers and run records under `docs/promise-machine/obligation-gates/`, the six existing runtime specimens whose bound Hexaemeron evaluation-test source digest changes, ADR-066, `scripts/portable_promise_machine.py`, `tests/test_skills_sh_package.py`, and `tests/check-map-v1.json`; generated portable runtime and Horos boundary files only when checked regeneration requires them. Step 6's Hypomnema reference is ADR-066 rather than the superseded ADR-054 name.
**Why.** Moving model identity out of the labelled corpora changes the owning Hexaemeron case-test bytes. Six existing runtime rows bind that exact test source, so their source and specimen digests must move together even though every record continues to say `domain-operation-not-run` and `operation_ran: false`. ADR-066 is the already receipted collision-free standing decision; changing the reference does not mint another decision or widen the evaluation gate.
**Steps touched.** Step 6.
**Still holding.** Step 6: entry holds; exit holds. Step 7: entry holds; exit holds.
