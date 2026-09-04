# Protasis study: reconstruct Promise Machine obligation gates

Study target: issue #884, “framework-40: Promise Machine obligations that no gate evaluates”

Starting ref: main at 7e97b5195d5b0e43146b4200f26cd41b89003413

## 1. Problem statement

### Assumptions

- The study is bound to the checked-out main commit named above. Counts and paths are facts about that tree, not forecasts about a later implementation base.
- “Gate” means an evaluator whose failure blocks the dependent transition and whose negative case is exercised. A declaration, a non-empty field, a digest of the declaration itself, or a labelled expected outcome is not by itself an evaluation.
- Existing domain-native result formats remain authoritative. A framework binding may add fields or an adapter, but it must not reinterpret a narrow domain result as stronger evidence.
- A prompt or model-backed promise remains unexercised when its only evidence is a labelled fixture. This study does not infer model behaviour from the label.
- Historical identity cannot be established from one tree alone. Any promise-ID stability claim therefore needs a base-versus-candidate transition gate or a durable retirement record.

The Promise Machine currently gives contributors a coherent declaration and coverage system, but it does not evaluate every obligation its root law states. On this base, the canonical inventory has 80 promises: 63 executable, 12 prompt-backed and 5 vendored. Consequence levels are 10 at level 0, 35 at level 1, 24 at level 2 and 11 at level 3. The coverage command is green, yet its runtime inventory has 35 entries whose 23 distinct bound sources do not emit a literal promise_id. Level 3 is selected by the same consequence-at-least-2 rule as level 2. The parser checks required field presence and vocabulary, not the truth of Evidence, Boundary, Authorises, Refuses or Recovery. All 80 current Exceptions fields say none, so stricter exception evaluation has no live waiver to migrate.

Issue #884 records ten obligation classes that can remain green without the promised fact being evaluated: result binding, level-3 separation, exception resolution, all seven composition clauses, semantic contract fields, upstream vendored identity, complete refusal reports, non-authorising unknown evidence, historical ID stability, and an enforced no-network/no-evidence-command boundary. It also names eleven promise rows whose evidence is still a labelled fixture rather than a model or domain run. The current tree confirms the substance of those observations, with two drift corrections: the runtime inventory is now 35 rather than 33, and the relevant case tests live under plugins/hexaemeron/tests and plugins/sapheneia/tests rather than the old root test path.

The users are skill authors who need to know what a green gate establishes, reviewers who need to reproduce a refusal, and the controller that must not advance a transition on declared-but-unevaluated evidence.

The prototype should demonstrate one complete, inspectable chain:

1. Every enumerated normative Promise Machine obligation has a stable obligation ID, a named evaluator, a consequence, a blocked transition and a negative guard.
2. Every level-2 or level-3 result surface emits or is deterministically adapted to a binding for its promise, subject, scope, evidence, unknowns, transition and exception.
3. Level 3 additionally requires named authority and independently inspectable evidence; a level-2-only record cannot pass it.
4. The current valid repository passes, while one minimal mutation from each obligation class fails with the expected stable finding code.
5. Prompt-backed rows distinguish labelled cases from a pinned run record. Missing runs stay visible as not-run and cannot authorise a transition.
6. The core checker remains offline, read-only and unable to execute evidence commands.
7. Root and generated Promise Machine copies remain byte-identical.

The human-readable demo is a matrix showing the obligation ID, evaluator, exercised negative case and disposition. The command-line demo first passes on the unmodified tree, then runs source-bound mutations that separately prove result-binding, level-3, exception, composition, field-semantics, upstream-provenance, refusal-shape, unknown-evidence, ID-history and no-side-effect failures.

## 2. Prior art

### Repository design and current implementation

The original Promise Machine study chose authored Markdown promises plus checked coverage records and exact generated copies. It explicitly separates structural conformance from behavioural truth: a structured record may say which evidence was reviewed, but the root checker must not pretend the promise prose proves itself. Its module sketch already separates law, inventory, identity, contracts, conformance, composition and runtime concerns. ADR-041 places framework capability promises in the root law rather than the portable router or an arbitrary plugin skill.

The current implementation already supplies useful seams: scripts/promise_machine.py discovers promises, parses the nine contract fields, validates the coverage table, maps consequence-at-least-2 promises to runtime surfaces, compares digests and emits stable findings in text and JSON. tests/promise_machine_coverage.json binds capability records to implementation, schema, tests and docs. scripts/run_checks.py and .github/workflows/repo.yml make root checks reachable in hosted CI. The reconstruction should extend those seams instead of introducing a second policy engine.

The current gaps are also concrete. SUPPORTED_EVIDENCE_CLASSES includes unknown. REQUIRED_HANDOFFS contains only Lazarus to Berean and Berean to Ariadne, while the root law states seven composition clauses. Finding carries code, fault, path, message, remedy and optional promise_id but not consequence or blocked transition. Runtime bindings require eight non-empty descriptions but no emitted result binding. Vendored overlays compare the committed copy with its local digest but do not establish the named upstream repository, immutable revision and path. Promise IDs are checked for grammar and uniqueness only in the current revision. The checker currently imports no network or subprocess library, but no guard preserves that property.

### Last two merged pull requests touching the subject

- PR #929, merged as 7e97b519 on 2026-08-30, added the report-only dead-code capability row and digest-bound implementation, schema, tests and documentation. Carry forward its capability-record and negative-test topology. Refuse the inference that a report-only inventory row evaluates a Promise Machine obligation. The PR body names issue-437 audit-round files that are absent from this base; because neither source nor verified synopsis exists here, this study treats those audits as unavailable rather than evidence.
- PR #913, merged as d427e750 on 2026-08-30, made the root invariant suite run on every pull request. Carry forward that hosted enforcement point: a new root obligation guard will be a real CI gate. Its Promise Machine coverage change only re-pinned an existing test digest, so the PR supplies reachability, not obligation semantics.

The intervening first-parent composition commit c8cbf63f also touches the coverage file, but it is not a merged pull request. Its publisher-separation composition does not resolve any #884 obligation, so no design claim is carried from it.

### In-scope audit inventory

The inventory is intentionally bounded to audit records that review the Promise Machine framework itself or the router-run precedent issue #884 proposes reusing. Per-capability audit logs that only supplied an individual coverage row do not evaluate the ten framework obligations and are out of scope. The committed synopsis set was verified before use with:

~~~text
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
~~~

The command exited 0. The study used these verified synopses and did not substitute unverified summaries:

- audit/AUDIT_SYNOPSIS.md represents audit/AUDIT.md at SHA-256 d0be89aa23e8db7979ac29ff1613e31d59a1ee78d07131147d50eb6268e01d9d. Its Promise Machine rounds found and fixed missing-law and unrelated-discovery behaviour under scoped checks, audit-log overwrite, inventory-count overclaim, child-router and vendored-overlay symlink omissions, under-specified exception labels, vendored self-contracting, frontmatter/body and duplicate-metadata parsing, manifest/root version mismatch, router-body false refusal, absent contract declarations and an over-broad Pandects claim. Later rounds explicitly state that declarations do not prove runtime implementation, review cases do not turn human judgement into runtime proof, labelled cases do not establish future model behaviour, and runtime inventory digests do not establish operational truth. Unpursued leads include caller-owned-directory replacement races and natural-language routing outside policy language. The legacy source omits audit-schema, covered, not-checked and Elenchus-verdict fields in these rounds; those values remain unknown and are not reconstructed.
- audit/rounds/fiat-499-grade-router-selection-not-just-resolution.synopsis.md represents its source at SHA-256 650a3be519f9b83f68572b21056fb1ddddf6b3c6e202a8bccdf95b7045318386. Across ten rounds, Step 1 round 1 records S1-R1-01 fixed, S1-R1-02 fixed, S1-R1-03 accepted, S1-R1-04 accepted, S1-R1-05 fixed, S1-R1-06 accepted and S1-R1-07 initially open; round 2 records S1-R2-01 fixed and closes the carried evidence-class mismatch; rounds 3 and 4 record S1-R3-01 and S1-R4-01 fixed; round 5 is clean. Step 2 round 1 records S2-R1-01 through S2-R1-04 fixed and round 2 is clean. Step 3 round 1 records S3-R1-01 fixed, S3-R1-02 and S3-R1-03 accepted, S3-R1-04 through S3-R1-07 fixed, S3-R1-08 documented and carried, and S3-R1-09 and S3-R1-10 accepted; round 2 records S3-R2-01 fixed and S3-R2-02 and S3-R2-03 accepted; round 3 is clean. The operative lessons are digest-bound reporting, duplicate-row refusal, exact run arithmetic, prompt-template scope, explicit model/date/corpus/failure metadata, and one request per fresh context. The first 36-of-36 batch was invalidated because batching and outcome cues contaminated it; a fresh-context regrade produced 35 of 36 and left RS-33 failing. Not checked across the record includes real-agent repeatability, variance, corpus representativeness, reasoning inspection, native Windows and waived Solidity. The standing repository-wide lead is that PM036 validates only evidence-class vocabulary and does not require the declared class to be exercised. Elenchus is recorded as passed or guarded where findings were repaired and null on the final clean rounds.
- audit/rounds/fiat-904-grade-the-router-corpus-from-a-driver-rather.synopsis.md represents its source at SHA-256 665a08ed14c2432ae14fbbea0199408e487fee1965badb81355f11eb6e27cd88. Step 1 round 1 records S1-R1-01, manifest-after-prompts ordering, fixed and guarded; round 2 is clean with Elenchus null. Step 2 round 1 records S2-R1-01, duplicate answers silently taking the last value, fixed and guarded; round 2 is clean with Elenchus null. Step 3 round 1 is clean with Elenchus null. The record covers prompt leakage, packet-write ordering, corpus drift, answer binding, missing answers and answer shape. It does not establish that a context will parse or repeat the recorded answers, because the driver itself calls no model. Its refusal-reason leniency remains an explicit lead rather than being silently tightened.

### What is carried and what is refused

Carry forward by name:

- PM036 declared-class-only is the direct precursor to the unknown-evidence gate.
- The labelled-case and model-repeatability limits from the root audit and Fiat #499 remain open until a pinned run record exercises them.
- Fiat #904's offline packet, duplicate-key refusal and exact answer binding are the pattern for reproducible prompt evaluation.
- The root audit's path confinement, symlink, duplicate metadata and generated-copy failures are mandatory regression boundaries.
- PR #913's unconditional root invariant job is the enforcement point.

Refuse by name:

- Do not count PR #929's dead-code inventory record as behavioural proof.
- Do not infer model behaviour from expected labels or a prior score.
- Do not import OPA, Rego or a service-side decision log merely to gain an obligation table.
- Do not replace domain-native evidence with one generic result envelope.
- Do not put upstream network access or evidence-command execution into the core checker.
- Do not infer findings or verdicts from the absent PR #929 audit files or the missing legacy audit fields.

### Organisation and external prior art

A current organisation code search for promise-machine/v1 and promise_id found only this repository and a same-commit private marketplace mirror. There is no independent Wildcat organisation implementation to adopt.

Open Policy Agent is useful conceptual prior art: policy is evaluated as code, CI can test it, and decision logs bind a decision identifier to policy, input and result. The narrow idea worth adopting is that an evaluated decision emits its identity and result binding. Adopting OPA itself would add another language, runtime and operational surface to a small offline repository checker, so it is not the lowest-comprehension viable design.

## 3. Constraints and non-goals

### Constraints

- Exact starting point: main and HEAD are 7e97b5195d5b0e43146b4200f26cd41b89003413 on branch fiat/884-reconstruct-promise-machine-obligation-gates.
- Toolchain: .python-version pins CPython 3.14.6. The implementation must remain standard-library compatible unless a later, separately justified decision changes that contract.
- The root PROMISE_MACHINE.md is the authored law. Plugin-local and installed copies are generated and must remain byte-identical through the existing sync check.
- The checker is offline, deterministic, read-only and repository-confined. It must not execute a command named by evidence.
- Existing canonical skills own their domain results. The framework may validate a binding to those results but may not promote their evidence class.
- Empty discovery, a missing evaluator, an unexercised required class, a stale digest, an expired or unresolved exception, an unexplained composition strengthening, an unknown positive evidence class or an unrecorded ID transition must fail closed.
- JSON inputs reject duplicate keys. Inputs are bounded regular files, may not be symlinks, and remain below the repository root after resolution.
- A base-versus-candidate ID gate must receive exact local refs and refuse an absent or unrelated base; it must not fetch implicitly.
- Current migration scale is bounded and observable: 80 promises, 35 runtime entries, 23 distinct runtime sources, 11 level-3 promises, seven law-level composition clauses and no active exception.
- The study output does not authorise implementation, controller receipt, publication, commit or push.

### Non-goals

- Rewriting every skill result into a framework-owned schema.
- Claiming that all 80 domain promises are substantively true.
- Replacing Fizz, Solidity Auditor, Hypomnema, Sapheneia or Vulgate domain evaluation with a framework assertion.
- Measuring general model quality, repeatability or population performance.
- Making the normal root checker contact an upstream host.
- Authenticating an upstream publisher when the vendored source offers no signature; the design can bind repository, immutable revision, path and bytes and must preserve that authentication unknown.
- Recovering Promise Machine ID history before the repository record begins.
- Turning every sentence in the root law into a natural-language policy parser. The governed set is the law's explicitly tagged normative obligations.
- Changing queue semantics, router selection, Fiat controller authority or the domain semantics of existing skills.

## 4. Design options

### Option A: ten bespoke assertions

Add one checker branch and one test for each issue bullet. This is the smallest patch and would close several cheap gaps quickly. It is rejected as the complete design because nothing makes a newly added law obligation join the set; omission would recur, and the relationship among law text, evaluator, negative case and transition would remain implicit.

### Option B: one universal result envelope

Require every skill to emit the same full Promise Machine result object. This gives one parser and a superficially simple gate. It is rejected because the fields would either erase domain distinctions or duplicate native records. It also contradicts the original structural-versus-behavioural separation: a generic envelope cannot make a fuzz campaign, audit report, rewrite or human judgement equivalent.

### Option C: OPA/Rego policy execution

Translate obligations into Rego and use OPA tests and decision logs. This is strong prior art for explicit policy evaluation. It is rejected here because it adds a policy language, binary/runtime, dependency and operational logging model while the repository already has a deterministic Python checker and CI gate. The extra mechanism does not solve model-run provenance or native evidence semantics.

### Option D: additive obligation ledger, native result bindings and direct evaluators

This is the chosen design because it adds one explicit completeness layer to existing components.

1. Tag each enumerated normative root-law obligation with a stable obligation ID. A versioned committed ledger maps that ID to its law anchor, evaluator, applicable promise or composition boundary, consequence, blocked transition and negative guard. The checker discovers tagged law obligations and ledger rows independently, then requires a one-to-one set match. It never tries to infer obligations from unrestricted prose.
2. Register evaluator functions in scripts/promise_machine.py. A row is not covered merely because an evaluator name exists: a source-bound negative fixture must make that evaluator emit the row's expected stable finding code.
3. Preserve domain-native records and add a compact Promise Machine binding header or deterministic adapter. For each level-2 or level-3 result it carries promise_id, subject, scope, evidence references and classes, unknowns, authorised transition, exception reference and source digest. Level 3 additionally carries the authorising identity or policy and an independently inspectable evidence reference. A level-2 record therefore cannot satisfy a level-3 gate.
4. Split declared evidence classes from transition-satisfying classes. unknown remains available only as an explicit unknown or negative state; it never contributes positive satisfaction. A labelled expected outcome remains a fixture until a pinned run record says it was exercised.
5. Replace free-form exception sufficiency with a structured reference that resolves authority, promise and gate, subject and scope, durable reason record, expiry rule and revocation or recovery. The checker rejects a missing record, scope mismatch, expired record or unresolved revocation. With all current promises declaring none, this can land without translating a live exception.
6. Turn each of the seven Composition bullets into a named obligation with negative fixtures: Lemma retrieval material cannot become truth; Lazarus recorded RPC cannot become proved without its named proof; Berean gates cannot become truth or model quality; Janus bounded results cannot become general hook safety; Ariadne without an external signature verifier cannot become author identity; Fiat observation bindings cannot become event truth or delivery evidence; Synkrisis recomputability cannot become cause, model quality or authority to act. Retain the two existing explicit handoff bindings as narrower instances, not as the whole composition gate.
7. Extend every refusal finding with obligation_id when known, consequence, blocked_transition and recovery. Text and JSON reports derive from the same Finding object and must remain equivalent.
8. Add a transition check over an exact base and candidate. An active ID may remain, or move to a durable retired entry that names its replacement if any and preserves its former meaning. Silent deletion or semantic reuse fails. The ordinary single-tree check validates current ledger shape; it does not claim history.
9. Add an upstream provenance record for vendored skills: repository URL, immutable commit, path, upstream blob digest, local digest and verification time or recorded unknown. The offline checker validates the committed record and local bytes. A separate explicit verify-upstream command may fetch only on vendored changes under the controls in item 9; it is never called by the core checker.
10. Reuse the Fiat #904 driver pattern for prompt-backed evaluations: pinned template, model, date, corpus digest, one fresh context per case, raw answer binding and named failures. Deterministic prompt rules may use executable negative fixtures. Model-dependent and campaign promises remain not-run until their relevant model or domain command evidence exists; a classification run cannot substitute for the promised fuzz or audit campaign.

The option's named trade is more migration work across 35 runtime entries and the prompt-backed corpus in exchange for a complete, reviewable boundary. It avoids a second policy runtime and avoids making one schema own every domain result. The work decomposes into four green slices: obligation completeness and direct cheap gates; runtime and level-3 bindings; composition and vendored provenance; then prompt and campaign run evidence.

## 5. Risk register seed

~~~risk-register
declaration-only-coverage | A ledger row can exist without executing its claimed evaluator | Mutate each obligation's minimal fixture and require the named stable finding code
result-binding-drift | A runtime source can change while its coverage description and digest stay superficially valid | Remove or mismatch one emitted binding and require refusal against the source and promise
level3-authority-collapse | A level-2 evidence record can pass a level-3 transition | Replay a valid level-2 record at level 3 and require the authority-and-evidence failure
history-blind-id-change | A promise ID can disappear or be reused between revisions | Compare exact related base and candidate refs and require a retirement or explicit compatible continuity
unknown-positive-transition | unknown can be declared and accidentally counted as satisfying evidence | Supply unknown as the only evidence and require the dependent transition to remain blocked
exception-staleness | A syntactically complete exception can be expired, revoked or scoped elsewhere | Exercise missing record, expiry, revocation and subject-scope mismatch cases
composition-promotion | A consumer can strengthen one of the seven producer boundaries | Run one negative transformation fixture for every root-law composition obligation
vendored-origin-spoof | A local copy digest can be presented as upstream provenance | Verify repository, immutable revision, path and upstream bytes in the separate constrained provenance job
checker-side-effect | A future checker change can add network or evidence-command execution | AST-scan imports and calls, then guard the checker in an offline environment with denied subprocess and socket access
prompt-fixture-substitution | A labelled expected answer can be counted as a model or campaign run | Require a pinned run block and raw answer binding before exercised status
migration-partial-green | Some runtime sources can adopt bindings while omitted sources remain green | Discover required sources independently and compare the complete expected and emitted sets
refusal-shape-drift | Text or JSON can omit the consequence, blocked transition or recovery | Assert both renderers against the same structured finding and compare their semantic fields
input-confinement-regression | A ledger, result, exception or provenance path can escape through a symlink or oversized file | Exercise regular-file, root-confinement, duplicate-key and byte-limit guards at exact boundaries
generated-copy-divergence | Root law obligation tags can change without generated installation copies | Run sync check and mutate one generated copy to prove the mismatch is caught
evidence-semantic-presence | Required contract fields can be non-empty yet fail to identify usable evidence or a bounded transition | Feed present-but-unresolvable references and over-broad scope values to their typed evaluators
~~~

## 6. Glossary seeds

- Binding header: the small framework-owned part of a domain result that identifies the promise, subject, scope, evidence, unknowns, transition and exception without replacing the domain record.
- Blocked transition: the exact state change or claim a failed promise prevents; broader inspection and recovery remain available.
- Declared evidence class: the vocabulary named by a promise contract before any evidence is inspected.
- Evaluated obligation: a tagged normative rule with a named evaluator and an exercised negative guard, not merely a present ledger row.
- Evidence reference: a typed, resolvable pointer and digest for the evidence a result relies on.
- Exercised: supported by the evaluator or run the promise names, with its subject and scope bound. A labelled fixture is not exercised.
- Level 3: a high-consequence transition that, in addition to level-2 binding, requires named authority and independently inspectable evidence.
- Native result: the skill-owned report, record, campaign output or receipt whose domain semantics the framework preserves.
- Obligation ID: the stable identity of one explicitly tagged root-law requirement, distinct from the promise ID it may constrain.
- Prompt run block: a record binding template, model, date, corpus, per-case raw answers and failures for one grading.
- Retirement: a durable historical record that an obligation or promise ID no longer remains active, without allowing its old meaning to be silently reused.
- Satisfying evidence class: an evidence state allowed to authorise the named transition after the referenced evidence has actually been evaluated.
- Upstream provenance: repository, immutable revision, path and upstream bytes, kept distinct from the local copied-file digest.

## 7. Sources

### Issue and pull requests

- Current issue evidence: https://github.com/wildcat-finance/skills/issues/884
- Last merged subject-touching PR: https://github.com/wildcat-finance/skills/pull/929
- Previous merged subject-touching PR: https://github.com/wildcat-finance/skills/pull/913

The issue and both pull-request bodies were fetched live for this study. Commit and tree claims were then checked against the local starting ref rather than accepted from the bodies.

### Repository sources at the starting ref

- AGENTS.md and plugins/hexaemeron/AGENTS.md: repository and plugin boundaries.
- .horos/boundary.json: reading boundary consulted before repository reading; classified sinks were not read.
- PROMISE_MACHINE.md and .agents/skills/promise-machine/SKILL.md: root law and portable router.
- scripts/promise_machine.py: parser, coverage, runtime and reporting implementation.
- tests/promise_machine_coverage.json: promise and capability evidence rows.
- plugins/hexaemeron/tests/test_promise_evaluation_cases.py and plugins/sapheneia/tests/test_promise_machine_cases.py: current labelled evaluation cases.
- docs/promise-machine/study.md and docs/decisions/ADR-041-grade-router-selection-as-a-root-capability.md: original design and root capability placement.
- docs/router-selection-driver/study.md: offline one-context-per-case grading precedent.
- .github/workflows/repo.yml, scripts/run_checks.py and tests/check-map-v1.json: hosted and local gate topology.
- audit/AUDIT_SYNOPSIS.md for audit/AUDIT.md, source SHA-256 d0be89aa23e8db7979ac29ff1613e31d59a1ee78d07131147d50eb6268e01d9d.
- audit/rounds/fiat-499-grade-router-selection-not-just-resolution.synopsis.md, source SHA-256 650a3be519f9b83f68572b21056fb1ddddf6b3c6e202a8bccdf95b7045318386.
- audit/rounds/fiat-904-grade-the-router-corpus-from-a-driver-rather.synopsis.md, source SHA-256 665a08ed14c2432ae14fbbea0199408e487fee1965badb81355f11eb6e27cd88.

### External primary sources

- OPA policy language: https://www.openpolicyagent.org/docs/policy-language
- OPA decision logs: https://www.openpolicyagent.org/docs/management-decision-logs
- OPA CI/CD guidance: https://www.openpolicyagent.org/docs/cicd

These sources support only the policy-ID, evaluation and decision-record comparison. They do not establish that OPA fits this repository, and the chosen design does not adopt it.

## 8. Signals, and the questions behind them

This is offline CI tooling, not an unattended service, so it needs bounded command evidence rather than exported telemetry.

- “Which obligation failed?” Emit stable finding code, obligation_id, promise_id when applicable, path and failed field or evidence reference.
- “What did the failure prevent?” Emit consequence and blocked_transition from the governed record, not inferred prose.
- “How can a contributor recover?” Emit the specific recovery action while leaving inspect, repair, rerun and safe exit available.
- “Did every obligation execute?” Emit discovered, ledgered, evaluated, passed, refused and unexercised counts; require discovered equals ledgered equals evaluated for structural gates.
- “Are high-consequence results distinct?” Emit level-3-required, level-3-bound and level-3-refused counts.
- “Did runtime adoption omit a source?” Emit required binding sources, observed bindings and missing or duplicate source identities.
- “Did identity change?” Emit active, retained, retired, replaced and unrecorded ID counts for the exact compared refs.
- “Is prompt evidence a fixture or a run?” Emit evidence status, model, date, template digest, corpus digest, answer count and named failures without copying full prompts into normal CI logs.

Text and JSON must be views of the same structured findings. Counts are bounded by discovered repository entries. CI's non-zero exit and file annotation are the alert; there is no remote metric backend, trace exporter or paging rule. Rejected payload contents, credentials and raw model prompts stay out of diagnostics.

## 9. Boundaries, per capability

- Obligation discovery and ledger parsing: read only fixed repository-relative paths; reject symlinks, non-regular files, oversized files, duplicate JSON keys, duplicate IDs and resolved paths outside the root. Discover law tags and ledger rows independently so neither can define away the other.
- Result binding: resolve only a coverage-declared source or adapter under the repository root. Bound bytes, require exact source digest and typed fields, reject duplicate result identities, and never execute a command named by the record.
- Exception resolution: treat exception records as untrusted input. Require exact promise, gate, subject and scope agreement; parse the expiry form; resolve the durable record; and make revocation status explicit. An error or unknown is a refusal.
- Base-versus-candidate identity: accept exact local Git object IDs, verify ancestry or an explicit comparison relation, and refuse missing objects or an unrelated base. Do not fetch, rewrite the worktree or trust a branch name.
- Core checker side effects: preserve a standard-library, offline implementation. Add a focused AST guard against subprocess, shell helpers, socket or HTTP clients and dynamic execution paths. Run the checker in a test environment that denies network and child processes as a behavioural backstop.
- Vendored upstream verification: keep it outside the core checker as an explicit command invoked only for affected vendored paths. Allowlist HTTPS hosts and declared repositories, require an immutable full commit and exact path, apply time and byte bounds, use a fresh temporary directory, pass no repository credentials, follow no cross-host redirect, and compare upstream and local digests. The resulting committed provenance record retains any publisher-authentication unknown.
- Prompt-run packet and tally: follow the source-bound Fiat #904 pattern. Write prompts before a final manifest, bind exact case IDs and corpus digest, reject duplicate answers and extra or missing IDs, keep one context per request, and never let expected labels enter the prompt. The driver may prepare and tally but does not itself claim to have called a model.
- Diagnostics: escape and bound path and value excerpts, render one finding per line, and avoid echoing rejected record bodies, prompts, secrets or environment variables.

These are the capability-specific applications of Phylax. The canonical Phylax contract remains the source for subprocess, URL, credential, dependency and model-output handling rather than being copied into a second local policy.

## 10. The budget, or its absence

No Metron performance gate is warranted. Issue #884 is a correctness and evidence-completeness failure, and the proposed inputs are already small and bounded: 80 promises, 35 runtime entries, seven composition obligations and repository-local records. Inventing a latency threshold would not choose among the designs.

Implementation should still record the duration of the focused Promise Machine scope and the root suite before and after each slice as observational evidence. A surprising regression triggers a Metron study before optimisation; it does not justify weakening a gate. Functional exit commands remain:

~~~text
python3 scripts/promise_machine.py coverage --check --json
python3 scripts/run_checks.py --scope promise-machine
python3 -m unittest discover -s tests
~~~

The runbook must use the actual scope name supported at implementation time and may not turn an unavailable command into a passing result.

## 11. The fail-closed posture

Missing, malformed, duplicated, stale, mismatched, expired, revoked, unexercised or unknown evidence blocks only the dependent transition. The checker reports the obligation, consequence, transition and recovery, returns non-zero, and leaves source bytes untouched. A missing base object, absent evaluator, missing negative guard, unavailable upstream proof or not-run model record is not silently downgraded to a warning when the transition requires it.

Structural checks cannot promote behavioural evidence. A valid binding proves that a result and promise agree on identity and boundary; only the named domain evaluator can establish the domain disposition. Level 3 cannot fall back to level 2. An exception cannot manufacture missing evidence or strengthen its class. A consumer cannot erase a conflict, unknown or refusal inherited from a producer.

Every defect found during implementation follows the Elenchus convention:

1. Preserve the failing input and exact starting commit.
2. Reproduce it with the smallest source-bound fixture.
3. Localise the failure to one obligation or parser boundary.
4. Add a focused test that fails before the fix with the expected finding code.
5. Fix the cause, rerun the focused test, the full Promise Machine scope, generated-copy check and root suite.
6. Record base SHA, fixed SHA, command, fixture digest, expected and actual code, and guarded verdict.

Mutation guards operate in a temporary copy and never patch the working source merely to demonstrate failure. A clean audit round records Elenchus as null, not guarded without a reproduced defect.

## 12. Decisions and their homes

The selected owner for Fiat's skills field is promise-machine. Issue #884 upgrades the root Promise Machine framework, not Protasis and not all governed skills as separate owners. Protasis evaluates this study; domain skills remain consumers of the binding layer unless a later implementation changes one of their own promises.

The design decomposes internally into four delivery slices:

1. Obligation IDs and ledger completeness, evidence-class separation, exception resolution, refusal shape, no-side-effect guard and base-versus-candidate ID history.
2. Additive native-result bindings across the independently discovered 35-entry runtime inventory, including distinct level-3 authority and evidence.
3. Seven-clause composition evaluation and separate vendored-upstream provenance verification.
4. Prompt and campaign run records using the one-context driver pattern, followed by a complete mutation matrix and root demonstration.

Each slice must enter and leave with the existing root suite green, must carry its own negative guards, and must not claim the later slices. If a slice cannot preserve a green intermediate state, Protasis must amend the runbook before implementation rather than silently merging steps.

Decision homes are:

- ADR-054, free at this base: the additive obligation ledger and binding layer; rejected hard-coded-only, universal-envelope and OPA designs; structural-versus-behavioural boundary; offline core and separate upstream verifier.
- PROMISE_MACHINE.md: tagged normative obligations, level-3 distinction, satisfying evidence rule, composition and refusal semantics. Existing generated copies change only through the canonical sync mechanism.
- schemas/promise-machine-obligations-v1.schema.json: ledger and retirement-record shape.
- tests/promise_machine_obligations.json: active obligation-to-evaluator and negative-guard inventory, if the runbook confirms tests is the repository's accepted home for governed machine records.
- scripts/promise_machine.py: discovery, evaluation, result-binding, exception and reporting logic.
- tests/test_promise_machine_obligations.py: focused positive, negative, exact-limit, duplicate-key, symlink, history and renderer-equivalence guards.
- docs/promise-machine/obligations-v1.md: operator-readable contract, evidence meanings and migration guide.
- docs/promise-machine/obligations-runbook.md: explicit upstream verification and prompt-run procedures, including recovery.
- tests/promise_machine_coverage.json: digest bindings for the new capability surfaces; it records the implementation but does not define the obligation universe.

No plugin EVOLUTION.md entry is owed merely because the framework begins checking an existing promise more honestly. A plugin-specific evolution entry becomes necessary only if that plugin's own canonical promise or result semantics changes.

### Amendment -- 2026-08-31

**What changed.** The standing decision record for the additive obligation ledger and native binding layer moves from ADR-054 to ADR-062. The exact pinned implementation base had ADR-054 free when the record was written, but the current default branch now owns ADR-054 through a different merged decision and owns ADR-055 through ADR-061 as well. The decision, rejected alternatives, structural-versus-behavioural boundary, offline core, and separate upstream verifier remain unchanged.
**Why.** Keeping the old number would make this branch collide with an unrelated default-branch decision and fail the repository's decision-record uniqueness gate. ADR-062 is the next number absent from both this branch and the current default branch.
**Steps touched.** Step 3.
**Still holding.** Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds. Step 6: entry holds; exit holds. Step 7: entry holds; exit holds.

### Amendment -- 2026-08-31

**What changed.** The standing decision record identifier for the current and pending obligation-gate work moves from ADR-062 to ADR-066. Earlier ADR-054 and ADR-062 references remain historical bytes in the receipted prefix; ADR-066 is the standing record for the unchanged obligation ledger, native binding layer, composition contract, rejected alternatives, structural-versus-behavioural boundary, offline core, and separate upstream verifier.
**Why.** The current default branch now owns ADR-062 through ADR-065, and the root uniqueness check reports the ADR-062 collision. ADR-066 is absent from both this branch and the exact current default branch. Renumbering the record and current-step reference resolves the collision without changing the selected design, evidence boundary, entry, or exit.
**Steps touched.** Step 4.
**Still holding.** Step 4: entry holds; exit holds. Step 5: entry holds; exit holds. Step 6: entry holds; exit holds. Step 7: entry holds; exit holds.
