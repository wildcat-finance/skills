## Step 1, round 1 -- 2026-09-30T14:44:00Z

Audit schema: fiat-audit-round/v2

Covered: base-ref-trust=not-applicable; historical-adapter-parse=not-applicable; module-equality=not-applicable; adapter-provenance=not-applicable; current-run-unchanged=not-applicable; legacy-isolation=reviewed; diagnostic-honesty=not-applicable; dual-controller=not-applicable; fixture-history-dependency=reviewed; version-surfaces=not-applicable; partial-write=reviewed; replay-list-lag=reviewed

Not checked: The security suite is waived (no Solidity), so x-ray, solidity-auditor and fizz did not run. The commit edits no file under plugins/hexaemeron/, so hexctl.py and gate_commands.py carry no new control; the not-applicable ids belong to Steps 2 to 4. resolve.py did not run end to end because its #1872 snapshot is untracked; only its argument, exclusive-create and absent-snapshot paths ran, through the scaffold test. The 24 selection measurements were not re-run; each report's digest and its bytes against .hexaemeron/reports/design/ were checked. Imprimatur and Brevitas on the study, runbook and draft belong to the prose phase and did not run here.

Elenchus verdict: unguarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | info | docs/starting-commit-gate-bindings/resolve.py:290 | The resolver writes its evidence sidecar .hexaemeron/design/evidence/<candidate>-<criterion>.json with write_text (lines 290 to 292) before it creates the report with mode x (lines 303 to 306). A rerun with a fresh report path rewrites the sidecar in place, and a failed report create leaves it rewritten, against the register's "nothing under .hexaemeron/ is rewritten". Read from source, not run. Impact: one untracked sidecar, no digest-bound report. Accepted: the resolver copy must stay byte-identical to the receipted run resolver (step Exit, RESOLVER_SHA256); the sidecar rewrite is resolver-internal evidence under git-ignored .hexaemeron/design/evidence/ and never touches a report, because reports are created with mode x; the register's "nothing under .hexaemeron/ is rewritten" is a product-step property that this scaffold copy does not carry. | accepted |
| S1-R1-02 | low | docs/decisions/drafts/admit-starting-commit-gate-bindings.md:36 | The draft justifies treating time as a gate by "run-to-run noise of one candidate, 1,313 to 1,378 ms across three runs". Each committed report and each .hexaemeron/design/evidence sidecar holds one run, and the range equals the two candidates' own single values (1,313 and 1,378), so the three-run series is retained nowhere and the claim is unverified. Study section 4 (line 87) also says "3 per cent" where 65/1,313 is 4.95%; the draft omits that. The 0-against-2 rows metric decides the selection either way. Fix a95cb1a52 changes no test file, so elenchus.py returns unguarded without running the runner; run_tests.py has no verdict field and reported 3968 tests, 0 failures, 0 errors, 5 skipped on a95cb1a52, so unguarded is the tool's classification, not a runner value. No test pins the clause: changing a draft figure passed all 11 scaffold tests, the hand counterfactual. | fixed in a95cb1a52 |

Leads not pursued: The scaffold test never asserts the draft's figures: changing 1,378 to 1,379 in a scratch copy passed all 11 tests; I compared the draft's four table rows and its other figures with the study and the 24 reports by hand, and all match. The test calls two private Hypomnema helpers, _design_bridge_block and _read_stable_adr, so a refactor there breaks it. The draft (line 9) and study section 10 say verify runs before "every mutating command", while study section 1 lists five exceptions: init, halt, resume, reset and amend runbook; the draft also lowercases "Adding" inside a quotation of gate-commands.md. A later amend runbook leaves docs/starting-commit-gate-bindings/runbook.md and the pinned digest in the test stale, and the test fails loudly (the #1731 precedent, study section 2).

## Step 1, round 2 -- 2026-09-30T19:25:34Z

Audit schema: fiat-audit-round/v2

Covered: base-ref-trust=not-applicable; historical-adapter-parse=not-applicable; module-equality=not-applicable; adapter-provenance=not-applicable; current-run-unchanged=not-applicable; legacy-isolation=reviewed; diagnostic-honesty=not-applicable; dual-controller=not-applicable; fixture-history-dependency=reviewed; version-surfaces=not-applicable; partial-write=reviewed; replay-list-lag=reviewed

Not checked: The security suite is waived (no Solidity), so x-ray, solidity-auditor and fizz did not run. This round has no fixes commit, so no Elenchus ran. The range from dd2e6939e to the stacked head edits no file under plugins/hexaemeron/, so hexctl.py and gate_commands.py carry no new control; the not-applicable ids belong to Steps 2 to 4. resolve.py still did not run end to end because its #1872 snapshot is untracked, and the 24 selection measurements were not re-run; only digests and bytes were checked. Imprimatur and Brevitas on the study and runbook belong to the prose phase and did not run here.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: Round 1's leads stand unchanged. The draft differs from 68489fc9c only in the ruled clause, and the round-1 rows are untouched. No new lead arose.

## Step 2, round 1 -- 2026-10-01T07:32:28Z

Audit schema: fiat-audit-round/v2

Covered: base-ref-trust=not-applicable; historical-adapter-parse=not-applicable; module-equality=reviewed; adapter-provenance=reviewed; current-run-unchanged=reviewed; legacy-isolation=reviewed; diagnostic-honesty=not-applicable; dual-controller=not-applicable; fixture-history-dependency=reviewed; version-surfaces=reviewed; partial-write=reviewed; replay-list-lag=reviewed

Not checked: The security suite is waived (no Solidity), so x-ray, solidity-auditor and fizz did not run. The Step 3 derivation does not exist, so base-ref-trust, historical-adapter-parse, diagnostic-honesty and dual-controller are not-applicable; this diff constrains them: the closed shape admits only 64-lowercase-hex digests under registered paths, hexctl.py:15157 still calls parser_bindings without a source digest so no pair can admit there until Step 3 passes digest(data), and the result carries no provenance member so status honesty must come from the caller. run_checks.py was not rerun; Mason's .hexaemeron/reports/step-2-checked.json (outcome green, 15 checks passed, base dd2e6939e) was read, not reproduced. The proof reporter's real released-adapter run was not repeated; its green path is mocked in every test. Imprimatur, Brevitas and Vulgate on the four prose files belong to the prose phase and did not run here. Mason's test_checkpoint_authority_* load reds were not reproduced; they do not touch the adapter.

Elenchus verdict: passed

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | low | plugins/hexaemeron/tests/test_gate_starting_commit_bindings.py:309 | Every digest the module compares with the supplied adapter digest or module pair differs from it at the first character ('cd'*32, '0'*64, 90ad7967..., the current pin), so four mutants of gate_commands.py passed all 27 tests on a scratch copy: replay substituting on a 16- or 63-character prefix of adapter_sha256 (lines 909 to 912), and parser_bindings comparing a 63-character prefix of ast_sha256 or of source_sha256 (line 317). Relaxing type(x) is dict or type(x) is str to isinstance also passed. The adapter is correct; the guard on adapter-provenance and module-equality was not. Mutants admitting on the AST digest alone, on the source digest alone, on any path's pair, on uppercase hex and on extra keys were each killed by the original tests. Fix: near_miss() flips the last and the first hexadecimal character of the adapter digest, the AST digest and the source digest; one new test; dict and str subclass specimens in the malformed list; 28 tests, every mutant above killed. The size-cap mutant (len(modules) > 8 removed) survives as an equivalent mutant: the path check already refuses a ninth entry. The hardened tests pass on the parent adapter (Ran 28, OK; the fix changes no adapter line), so the verdict cannot be guarded. | fixed in 11f03de83bf0316d78b51ac8502ae244c8a23d27 |

Leads not pursued: StartingRefParityTests read dd2e6939e:gate_commands.py from Git history (digest 90ad7967... checked before loading), following the 1.6.69 precedent at test_gate_commands.py:613; a shallow clone fails those three tests by name, and run_checks.py snapshots through git clone (scripts/run_checks.py:1652), so study section 4's "the checked runner's snapshot carries no Git history" is inaccurate while Mason's run_checks stayed green. gate-commands.md:212 "and for no other run" is a property of the Step 3 derivation, not of the adapter, which enforces digest equality only; the SKILL.md Boundary says so. A malformed bindings value on a run with no skewed module is ignored without a signal (by design, no new cause); Step 3 owes the caller-side signal. fiat_starting_commit_bindings_proof.py:72 creates parent directories before the O_EXCL open (as resolve.py:303), the subprocess inherits the environment (no -I), and the recorded command joins arguments unquoted; its real run recurses into no test because ProofReporterTests mock subprocess.run. portable_promise_machine.py check exited 1 on the git-ignored runtime mirror until sync; no tracked byte moved. Commit 28c5fc94 has one 119-character body line; Mason's notes count 7 ProofReporterTests where there are 6.

## Step 2, round 2 -- 2026-10-01T07:44:59Z

Audit schema: fiat-audit-round/v2

Covered: base-ref-trust=not-applicable; historical-adapter-parse=not-applicable; module-equality=reviewed; adapter-provenance=reviewed; current-run-unchanged=reviewed; legacy-isolation=reviewed; diagnostic-honesty=not-applicable; dual-controller=not-applicable; fixture-history-dependency=reviewed; version-surfaces=reviewed; partial-write=reviewed; replay-list-lag=reviewed

Not checked: The security suite is waived (no Solidity), so x-ray, solidity-auditor and fizz did not run. This round has no fixes commit, so no Elenchus ran. run_checks.py was not rerun, the proof reporter's real released-adapter run was not repeated, and Imprimatur, Brevitas and Vulgate on the four prose files belong to the prose phase. The Step 3 derivation does not exist, so base-ref-trust, historical-adapter-parse, diagnostic-honesty and dual-controller stay not-applicable under the round-1 constraints.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: The range 28c5fc94 to 46de63d1 changes test_gate_starting_commit_bindings.py, .horos/census.json, this record and its synopsis, and no file under plugins/hexaemeron/skills/ or hexctl.py. Against the final 28 tests on a scratch copy, 24 of 25 gate_commands.py mutants are red: the five round-1 mutants (AST-only, source-only, any path, uppercase hex, prefix), the 63-character prefix and dict and str subclass set, and a hostile set (consulting the pair for an unmoved module, popping an admitted entry, dropping the digest type check, substituting any receipt digest when bindings are present, skipping the shape check in parser_bindings or in replay, swapping the pair fields, breaking the thread in interface, validate_command, validate_with_criteria or replay, accepting an unregistered path, accepting extra pair fields); only the size-cap mutant survives, as an equivalent. Direct probes: bool, int, bytes and nested digests, a mappingproxy, int and tuple keys, None and list modules, and 65-character, newline and Unicode-digit digests each return None without raising; an empty modules table and a str-subclass key equal in text to a registered path are admitted, harmlessly, because the adapter looks up its own path and reads only the pair; the bindings dict is unchanged after validate, replay and validate again, and no module global retains it. Round 1's malformed-bindings lead is an accepted, documented design: gate_commands.py:134-135, gate-commands.md:136 and EVOLUTION.md:43 each say a value outside the shape admits nothing, names no new cause and leaves every result unchanged, and SKILL.md:774 lists the shape under Refuses in the Promise sense of not admitted. Round 1's other leads stand unchanged.
