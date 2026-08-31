## Step 1, round 1 -- 2026-08-31T03:48:15Z

Audit schema: fiat-audit-round/v2

Covered: source-rights=reviewed; source-byte-drift=reviewed; private-egress=reviewed; partial-release=reviewed; evidence-strengthening=not-applicable; duplicate-collapse=not-applicable; fix-state-collapse=not-applicable; many-to-many-loss=not-applicable; taxonomy-drift=not-applicable; cohort-leakage=not-applicable; adapter-overreach=not-applicable

Not checked: the security suite is waived for this step and the waiver is on the ledger. The diff adds Python, JSON schemas, Markdown and preserved Markdown specimens and changes no Solidity, so x-ray, solidity-auditor and fizz have no target. The seven not-applicable register items name mechanisms that do not exist at this commit: assertions, mappers, duplicate clusters, remediation state, relation validation, the release build and both consumer adapters are owed by runbook steps 2 and 3, and admission neither writes a release nor answers a consumer. Also unchecked: hosted CI, the controller receipt, push and publication, and whether a declared rights basis is lawful, which admission records rather than establishes.

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | medium | plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py | The refusal event stream was appended with a plain open(path, "a"). An --events path that was a symlink therefore redirected every recorded refusal into the link's target and appended to a file the run never meant to touch. The stream path is untrusted operator input, on the same filesystem boundary the step opens for sources | fixed in this round |
| S1-R1-02 | medium | plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py | The conformance report staged through a fixed "<report>.partial" name opened with open(staging, "wb"). That followed a symlink planted at the exact staging path and wrote the report body through it, and it let two concurrent runs share one staging file. The report path is caller-named under .hexaemeron/, so the staging name was predictable | fixed in this round |
| S1-R1-03 | medium | plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py | json.loads kept the last value of a duplicated key. A policy could therefore declare one source digest to anyone reading its bytes and a different one to the parser that admitted them, while the closed-key check saw a single key and passed. A corpus whose whole promise is that preserved bytes match a declared digest cannot let the declaration be ambiguous | fixed in this round |

Leads not pursued: three residual races are recorded rather than fixed, each bounded by a check that runs after it. First, read_bounded stats a source and then reopens it, and resolve_within stats each path component before that reopen, so a component could be replaced between the two; both are closed downstream by O_NOFOLLOW on the final open, the bounded cap+1 read, the exact byte-count comparison and the SHA-256 comparison, and a substitution surviving all four has to produce the declared digest. Second, os.replace promotes the report onto a caller-named path, so a symlink at the destination is replaced rather than followed, which is the intended outcome. Third, the destination directory is not held by a descriptor across that promotion; the root runner's writer does hold one and this writer does not, recorded as the narrower guarantee rather than claimed as equal. Separately, the pilot policy's max_source_bytes of 1,000,000 and the module's 8,000,000-byte ceiling and 50,000,000-byte total were reviewed as declared bounds and not measured against a hostile source larger than the ceiling, because no such specimen exists at this commit. Every fix carries its exact bad specimen in plugins/anamnesis/tests/test_s1_boundaries.py. All four guards were run against the parent commit 708f2ec919aed0712d39e7f9a80f675e4d22d756, where they fail, and against the fixed tree, where they pass with the whole 65-test suite.

## Step 1, round 2 -- 2026-08-31T03:53:50Z

Audit schema: fiat-audit-round/v2

Covered: source-rights=reviewed; source-byte-drift=reviewed; private-egress=reviewed; partial-release=reviewed; evidence-strengthening=not-applicable; duplicate-collapse=not-applicable; fix-state-collapse=not-applicable; many-to-many-loss=not-applicable; taxonomy-drift=not-applicable; cohort-leakage=not-applicable; adapter-overreach=not-applicable

Not checked: unchanged from round 1. The suite waiver still holds, the seven not-applicable items are still owed by runbook steps 2 and 3, and hosted CI, the controller receipt, push and publication are still outside this round. Round 2 re-ran the three discipline lints and the plugin suite over the round 1 fixes and then reviewed the code paths round 1 did not reach: the record loop, the total-bytes ceiling, the policy root derivation and the placement of the pilot's curation scope.

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R2-01 | low | plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py | admit refused any policy declaring fewer than 25 or more than 50 records, so the pilot's curation scope was enforced as a law of the product. The study calls that range a curation scope for the seed, not a property of a corpus, and a member whose job is custody cannot refuse a corpus for being the wrong size. The check moved to seed_scope, called by the admit-seed resolver that the design record actually scopes | fixed in this round |
| S1-R2-02 | low | plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py | Only refusals raised inside the per-source loop emitted anamnesis.source.refused. A duplicated policy key, a duplicate record id, an unknown record key, a record naming an unadmitted source and the total-bytes ceiling all refused with nothing durable written, so an operator asking why a run refused had the exit code and no event. Every refusal now passes through one recorded boundary carrying its rule, record, policy version and correlation id | fixed in this round |

Leads not pursued: two observations carry forward rather than changing code. The A025 duplicate-key refusal is raised while parsing the policy, before the policy version and digest are known, so its event records the rule and reason with a null record and a correlation id derived from the policy bytes alone; naming the version in that event would require trusting a field from the document being refused. The seed_scope bound of 25 to 50 is now a resolver-side constant rather than a policy field, which is right for the seed the runbook fixes and wrong for a second pilot; making the scope a declared policy field is step 2's to decide when the release policy schema lands. Round 2 added four guards to plugins/anamnesis/tests/test_s1_boundaries.py and moved two to the resolver boundary in plugins/anamnesis/tests/test_s1_admission.py; three of the four fail against parent commit 6ff91f01188f4ccb49ceef438daf9346491b44b6 and the fourth passed there already, because a source-level refusal was the one path that always recorded an event. The suite is 71 tests and green, the three discipline lints exit zero, the exact pending resolver writes its report and design_evidence --transition step:2 exits zero.

## Step 1, round 3 -- 2026-08-31T04:04:04Z

Audit schema: fiat-audit-round/v2

Covered: source-rights=reviewed; source-byte-drift=reviewed; private-egress=reviewed; partial-release=reviewed; evidence-strengthening=not-applicable; duplicate-collapse=not-applicable; fix-state-collapse=not-applicable; many-to-many-loss=not-applicable; taxonomy-drift=not-applicable; cohort-leakage=not-applicable; adapter-overreach=not-applicable

Not checked: unchanged from rounds 1 and 2. Round 3 re-ran the plugin suite, the three discipline lints, both Promise Machine checks and the whitespace check over the round 2 fixes, and looked at what those fixes left behind rather than at the source paths already reviewed twice.

Elenchus verdict: passed

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R3-01 | low | .agents/skills/promise-machine/runtime/MANIFEST.json | The generated portable runtime still carried the pre-fix copies of anamnesis.py and hypomnema.py, so a copy-mode install would have shipped code the source tree had already corrected and the manifest bound bytes that no longer existed upstream. Rounds 1 and 2 changed both scripts and neither resynced the mirror | fixed in this round |

Leads not pursued: one flake is recorded rather than fixed, because it is pre-existing and not this step's. tests/test_python_contract.py walks ROOT.rglob("*.md") without excluding tmp/, which is where scripts/run_checks.py stages its disposable snapshot, so running the root suite while a check run is in flight reports the snapshot's own copy of docs/promise-machine/evidence/2026-08-20-self-demonstration.md as stale runtime prose. The finding is transient, names a path under the gitignored run home rather than a tracked file, and disappears when the snapshot does; the same test passes against this tree with no check run in flight. It belongs to whoever owns the check runner's scratch boundary, not to a step that adds a plugin.

## Step 1, round 4 -- 2026-08-31T04:27:41Z

Audit schema: fiat-audit-round/v2

Covered: source-rights=reviewed; source-byte-drift=reviewed; private-egress=reviewed; partial-release=reviewed; evidence-strengthening=not-applicable; duplicate-collapse=not-applicable; fix-state-collapse=not-applicable; many-to-many-loss=not-applicable; taxonomy-drift=not-applicable; cohort-leakage=not-applicable; adapter-overreach=not-applicable

Not checked: unchanged from rounds 1 to 3. This round re-ran the whole battery over the round 3 fix and found nothing new in the step's scope.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: one red check is recorded and is not this step's. The selected check plan run at this commit reports lazarus-suite failed; the same suite fails identically on the unmodified base checkout, and this run changes no file under plugins/lazarus. The cause is environmental rather than a regression: on macOS the TMPDIR the suite writes into resolves through /var to /private/var, and lazarus_lib/release.py refuses a statement path containing a symlink, so every release test raises PathError before it reaches its assertion. It belongs to Lazarus, is reproducible from a clean clone on this platform, and would fail whatever this step contained. The step's own battery is green: 71 Anamnesis tests, 776 root tests, phylax, ephoros and hypomnema each exit 0, promise_machine check reports 17 plugins and 17 copies clean, portable_promise_machine check reports no drift, git diff --check is clean, the pending resolver writes its report and design_evidence --transition step:2 exits zero.
