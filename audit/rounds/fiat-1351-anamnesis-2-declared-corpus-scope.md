## Step 1, round 1 -- 2026-09-07T12:34:30Z

Audit schema: fiat-audit-round/v2

Covered: scope-in-release-id=not-applicable; constant-removed=not-applicable; scope-both-ways=not-applicable; estate-provenance=not-applicable; private-origin-unnamed=reviewed; disclosure-assumption=reviewed; pilot-rebuild-drift=reviewed; killed-build=not-applicable; ledger-arithmetic=not-applicable; stale-prose=not-applicable; demo-status=not-applicable

Not checked: the security suite is waived for this run and the waiver is on the ledger; this step adds Markdown, JSON and Python tests and changes no Solidity, so x-ray, solidity-auditor and fizz have no target. Eight register ids name artefacts that do not exist at this commit: the scope object, the removed constant, the both-ways check and the demonstration ledger are owed by step 2, the estate specimen's provenance and the killed-build guard by step 3, the ledger row and the prose reconciliation by step 4. Also unchecked: hosted CI, the controller receipt, push and publication, and whether the study's selection is correct, which this step commits rather than establishes.

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | medium | plugins/anamnesis/docs/corpus-scope/reports/resolve.py | `main` wrote its report to the fixed relative path `.hexaemeron/reports/<candidate>-<criterion>.json`, so one rerun of the committed copy from the repository root replaced the receipted `release-policy-scope-pilot-artefacts-rebuilt.json` and `design_evidence.py --transition design-lock` refused D005 until the report was restored from the committed copy. A reproducibility script that writes into controller state cannot be rerun safely. The report is now printed and written only to a caller-named `--out` path that must not already exist | fixed in this round |
| S1-R1-02 | medium | plugins/anamnesis/docs/corpus-scope/reports/resolve.py | `pilot-artefacts-rebuilt` reran to 8 against the recorded 7 for `release-policy-scope` and 7 against 6 for `admission-policy-scope`, because the `git grep` over `plugins/anamnesis` counted the committed study copy, which quotes the pilot release id and program digest without being a pilot artefact. The grep now excludes `plugins/anamnesis/docs`; the four cells rerun to 7, 6, 0 and 1 at this tree and the 32 receipted reports are byte-identical to the committed ones | fixed in this round |

Leads not pursued: the resolver reproduces the record only at a tree where the pilot's tokens and `seed_scope` stand as the study measured them, because `scope-recovery-by-policy-edit` exits when the literal bound is absent and `estate-findings-admissible-without-widening` calls `seed_scope`, so from step 2 onward those cells rerun only at commit 0bc39f27 or ce8c84f9; the guard reruns the four `pilot-artefacts-rebuilt` cells, whose file set later steps do not change, and no other. `acceptance-check-ms` is a timing and never reproduces exactly, as the record says. A stray `.hexaemeron/reports/probe-manifest-killed-probe-recovery.json` is a Surveyor probe the record does not name and the committed set omits; it stays out of the tree. Evidence for the covered concerns: phylax and ephoros exited 0 over the 40 changed paths passed through xargs, hypomnema exited 0 over the two docs copies and the record directory, the anamnesis suite ran 203 tests with 1 skip, the root suite ran green under greenlight at the record commit, `git diff --check`, `audit_synopsis.py --check .` and `horos.py check .` exited 0, the committed study, runbook and record are byte-identical to the receipted artefacts, `elenchus.py --step 8` refuses with exit 3 and writes no report, a tampered report fails `test_s7_records`, and no committed byte names a repository, branch or path of the maintainer-held documents.

## Step 1, round 2 -- 2026-09-07T12:44:09Z

Audit schema: fiat-audit-round/v2

Covered: scope-in-release-id=not-applicable; constant-removed=not-applicable; scope-both-ways=not-applicable; estate-provenance=not-applicable; private-origin-unnamed=reviewed; disclosure-assumption=reviewed; pilot-rebuild-drift=reviewed; killed-build=not-applicable; ledger-arithmetic=not-applicable; stale-prose=not-applicable; demo-status=not-applicable

Not checked: unchanged from round 1. The suite waiver still holds and the eight not-applicable register ids are still owed by steps 2, 3 and 4. Round 2 re-ran the three lints and the check-map selection for this diff over the fixed tree (10 checks green, root suite 1623 tests in 218 s), then reviewed round 1's fix: `--out` refuses an existing path, including a symlink, with exit 2 and leaves it untouched; a rerun without `--out` prints the report and writes nothing; the exclude pathspec drops only `plugins/anamnesis/docs` from the four `pilot-artefacts-rebuilt` greps; the three guards pass on this tree and failed on the parent.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: none beyond round 1's, which stand as recorded.

## Step 2, round 1 -- 2026-09-07T20:44:39Z

Audit schema: fiat-audit-round/v2

Covered: scope-in-release-id=reviewed; constant-removed=reviewed; scope-both-ways=reviewed; estate-provenance=not-applicable; private-origin-unnamed=reviewed; disclosure-assumption=not-applicable; pilot-rebuild-drift=reviewed; killed-build=reviewed; ledger-arithmetic=not-applicable; stale-prose=reviewed; demo-status=reviewed

Not checked: the security suite is waived for this run and the waiver is on the ledger; this step changes Python, JSON and Markdown and no Solidity, so x-ray, solidity-auditor and fizz have no target. Two register ids name artefacts this step does not create: the estate sources and their rights statement are owed by step 3, and the ledger row by step 4. Also unchecked: hosted CI, the controller receipt, push and publication; whether the declared bounds of 25 to 50 are the right bounds for the pilot, which the study declares rather than establishes; and whether the pilot's 41 findings are the right 41, which stays a non-goal.

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | medium | plugins/anamnesis/docs/corpus-scope/reports/resolve.py | Step 1's guard is red on this tree: `pilot-artefacts-rebuilt` reran to 8 for `release-policy-scope` against the recorded 7, because `plugins/anamnesis/tests/test_s8_scope.py` quotes the new curation policy version `curation-2026-09-06`. `run_checks.py --base <step 1>` reported `anamnesis-suite failed` and outcome red, so CI refuses this step as committed. Round 1 of step 1 recorded that the four cells would stay reproducible because later steps leave their file set alone; that was wrong, and this is the step that falsified it. The study enumerates the seven files the criterion counts, and a guard pinning a value is no more one of them than the study copy under `docs`, so the grep now excludes `plugins/anamnesis/tests` as well; the four cells rerun to 7, 6, 0 and 1, no test carried those tokens at 0bc39f27, and the 32 receipted reports stay byte-identical | fixed in this round |
| S2-R1-02 | low | plugins/anamnesis/docs/decisions/ADR-006-declared-corpus-scope.md | The Consequences section omits the compatibility boundary the new `A077` check creates: a release built before this decision carries no `policy.scope`, so `verify` now refuses it rather than passing it. The tree's only Anamnesis release is the pilot and this step rebuilds it, so nothing here breaks, but a reader of the record could not see that a release held elsewhere stops verifying until it is rebuilt. The section now says so | fixed in this round |

Leads not pursued: three observations carry forward rather than changing code. The study's section 8 lists `A077` among the codes raised inside the `refusals_recorded` boundary, and `verify_release` takes no events sink, so `A077` emits no durable refusal event while `A073` to `A076` do; its seven neighbours in that function (`A103`, `A104`, `A105`, `A117`, `A118`, `A119`, `A123`) emit none either, so the code is consistent with the function it sits in and the study's sentence overreaches, and the study is receipted and immutable. Nothing loads `schemas/policy-v1.json` to validate a policy and the check map's `schemas` scope declares no checks, so the schema and `check_scope_shape` are held in agreement by review alone; both were compared field by field this round and agree on the identifier pattern, the 64-byte and 300-byte caps, the non-empty unique source list and the integer bounds. The declared record bounds are checked at admission, curation, release and rebuild but not at verify, because a manifest carries derived counts rather than the declared record list, and the study's construction names only the both-ways source check there. Evidence for the covered concerns: a one-byte change to any scope field changes the release id and a guard holds it; `seed_scope` and the literal bound are absent from the program; `A074` and `A075` each have their own specimen and run at build and at verify through `A077`; the pilot's admission policy, three sources, both event streams and four policy-free release components are byte-identical to step 1, checked file by file; the killed-build guards `A100` and `A103` still run over the pilot; the demonstration stays `real-data` with its frontier revision and digest unmoved; and no committed byte names a repository, branch or path of the maintainer-held documents.

## Step 2, round 2 -- 2026-09-07T21:04:06Z

Audit schema: fiat-audit-round/v2

Covered: scope-in-release-id=reviewed; constant-removed=reviewed; scope-both-ways=reviewed; estate-provenance=not-applicable; private-origin-unnamed=reviewed; disclosure-assumption=not-applicable; pilot-rebuild-drift=reviewed; killed-build=reviewed; ledger-arithmetic=not-applicable; stale-prose=reviewed; demo-status=reviewed

Not checked: unchanged from round 1, and one thing about this step's own order. The implementing worker was lost before it receipted, so round 1's review ran while the step was still in the implement phase and its first fix, a23c34f0, is inside the receipted implementation range rather than after it; the round's declared fixes commit is a73c7972, which completes that fix by moving its regression guard into the suite this step's runner contract actually runs. The suite waiver still holds, the estate sources and the ledger row are still owed by steps 3 and 4, and hosted CI, the receipt, push and publication remain outside every round. Round 2 asked one question round 1 did not: what does a declared scope leave unconstrained. Four answers, none a defect: a scope id is unique within its policy and nothing compares ids across corpora, which is what an id inside a hashed policy can promise; `ingest` reads admitted sources without a curation policy and so performs no scope check, exactly as the study's construction names admit-seed, curate, release and the rebuild and no other command; a rebuild refuses `A073` when the record count leaves the declared bounds, so the bounds bind the whole build path and not only admission; and one byte of `preserves` changes the release id, so the declaration cannot drift without the id moving.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: round 1's three stand as recorded. Nothing new was found.

## Step 3, round 1 -- 2026-09-07T21:25:33Z

Audit schema: fiat-audit-round/v2

Covered: scope-in-release-id=reviewed; constant-removed=not-applicable; scope-both-ways=reviewed; estate-provenance=reviewed; private-origin-unnamed=reviewed; disclosure-assumption=reviewed; pilot-rebuild-drift=reviewed; killed-build=reviewed; ledger-arithmetic=not-applicable; stale-prose=reviewed; demo-status=reviewed

Not checked: the security suite is waived for this run and the waiver is on the ledger; this step adds Markdown, JSON and one test file and changes no Solidity, so x-ray, solidity-auditor and fizz have no target. The ledger row is owed by step 4. Also unchecked: hosted CI, the controller receipt, push and publication; whether the seventeen preserved findings are true, which is the producer's claim and not this corpus's; whether the maintainer's written permission is legally sufficient, which admission records rather than establishes; and whether these seventeen are the right seventeen to have kept, which a declared scope states and does not justify.

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R1-01 | low | plugins/anamnesis/specimens/estate/events/admit.jsonl | The specimen ships a committed event stream that nothing regenerates or compares, so a later change to the admission policy or to the correlation-id derivation would leave it stale in silence. The pilot's projections carry a guard for exactly this reason and its event streams do not. A guard now compares the committed stream against a fresh admission and holds each event's kind, disclosure and correlation-id length. The stream was already correct, so this guard passes against the parent commit: it prevents drift rather than repairing it | fixed in this round |
| S3-R1-02 | low | plugins/anamnesis/docs/demo.md | The document described the demo path over one corpus, and this step commits a second. A reader following it would run the pilot and never learn that the estate exists, which is the corpus the declared scope was built to make possible. The document now names both specimens, their scopes and bounds, states that they rebuild to different release ids and that neither builds under the other's scope, and its not-established section covers both. Its guard fails against the parent commit | fixed in this round |

Leads not pursued: four observations carry forward. Pointing the Hypomnema walk at `plugins/anamnesis/specimens` reports `H001` on the pilot's preserved `pandects-audit-rounds.md:27`, whose producer wrote a link to `../docs/design.md` that resolves to nothing here; the corpus preserves that byte unchanged by contract, the walk skips specimens by default and the repository's declared lint scope exits 0, so the finding belongs to the producer's own record and is not repaired. The estate ships no refused-event example, while the pilot ships one recording rule `A057`; nothing requires a second, and the refusal paths this corpus can exercise are covered by the step's own `A074` and `A075` specimens rather than by a committed stream. `SKILL.md` names the pilot in every command example and `README.md` describes one corpus; both are marketplace prose that step 4's cold read owns, and changing them here would move bytes the ledger step is required to reconcile. The seventeen preserved findings are quotations of what their producer wrote, so their numbers, ratings and verbatim strings were compared against the originals field by field this round and not otherwise judged. Evidence for the covered concerns: the estate rebuilds twice to `509239765f9fa2db782d3bc70fadea3b05411fc0638402fe5e0a43882f0063e3` across 7 components with 17 findings, 4 rounds, 0 remediations and 4 verifications all unknown; each source records basis `permission`, disclosure `public`, holder Wildcat Labs and the written permission of 7 September 2026, and names its original by date, section, line range and SHA-256 with no repository, branch, path or URL, held by a guard that fails when one is introduced; the estate under the pilot's curation policy refuses `A074` and the pilot under the estate's refuses `A074`, a scope source nobody admitted refuses `A075`, and 17 records sit outside the pilot's declared 25 to 50; a build into an occupied destination refuses `A100`; a taxonomy without `unrated` quarantines those records rather than mapping them; a probe making one source restricted withheld its 4 findings from the cohort and counted them; the pilot specimen is byte-identical to step 2; and `anamnesis.py` is unchanged since step 2's exit.

## Step 3, round 2 -- 2026-09-07T21:34:04Z

Audit schema: fiat-audit-round/v2

Covered: scope-in-release-id=reviewed; constant-removed=not-applicable; scope-both-ways=reviewed; estate-provenance=reviewed; private-origin-unnamed=reviewed; disclosure-assumption=reviewed; pilot-rebuild-drift=reviewed; killed-build=reviewed; ledger-arithmetic=not-applicable; stale-prose=reviewed; demo-status=reviewed

Not checked: unchanged from round 1. The suite waiver still holds, the ledger row is still owed by step 4, and hosted CI, the receipt, push and publication stay outside every round. Round 2 asked one question round 1 did not: what can a corpus of open findings assert through its projections that it has no right to assert. Six readings, none a defect. The Elenchus view carries `verdict` null and no analogue carries a remediation at all, because neither source records one, so there is no state for a past result to travel through. Every finding and every submission reads adjudication `unknown`, which is what a source that adjudicates nothing establishes, and all four verifications read `unknown` rather than passed. The Synkrisis view carries ten denominators, five counted unknown families and an empty exclusion list, and states what it does not establish. Nothing in either view converts an open finding into a judged one.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: round 1's four stand as recorded. Nothing new was found.

## Step 4, round 1 -- 2026-09-07T22:02:19Z

Audit schema: fiat-audit-round/v2

Covered: scope-in-release-id=not-applicable; constant-removed=not-applicable; scope-both-ways=not-applicable; estate-provenance=not-applicable; private-origin-unnamed=reviewed; disclosure-assumption=not-applicable; pilot-rebuild-drift=reviewed; killed-build=not-applicable; ledger-arithmetic=reviewed; stale-prose=reviewed; demo-status=reviewed

Not checked: the security suite is waived for this run and the waiver is on the ledger; this step changes Markdown and two test files and no Solidity, so x-ray, solidity-auditor and fizz have no target. Six register ids name work completed in steps 2 and 3 and re-checked there rather than here. Also unchecked: hosted CI, the controller receipt, push, the base integration and the issue closure, all of which follow this round; whether the new held job is the most valuable one a reader could choose, which the ledger asserts and this round does not; and whether the next job's acceptance condition can be met, which depends on a foreign-format corpus the ledger declares absent.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: three observations carry forward. The plugin package version stays `0.3.0` while the skill moves to `anamnesis-v4.1.0`, so a marketplace consumer already holding `0.3.0` is not served the changed skill by a version-gated installer; the study declared moving it a non-goal, `tests/test_version_propagation.py` pins the current value, and the house convention agrees, with `horos` at package `0.1.1` against skill `horos-v12.3.3` over eighteen ledger rows and `synkrisis` at `0.5.1` against `synkrisis-v4.2.0`, so this is a repository-wide property rather than a defect of this step. The new held job's claim was verified rather than assumed and is sharper than the ledger states it: the module defines `MAPPER = {"name": "warden-audit-round-markdown", "version": "1"}` at one line and references it nowhere, `parse_source` is the only parser, and `curate` reads `policy["mapper"]` into every assertion, so the one place naming the implementation that actually runs is dead while the policy's declaration is what every record attests. The demonstration ledger's own held job asks for a second corpus from more than one producer and the estate corpus is one, but the registered demonstration still runs the pilot alone; the study's section 12 records why the estate is not added as a command, so the demo frontier stays where step 2 left it. Evidence for the covered concerns: the evolution counter moved once from 3.1.0 to 4.1.0 with generation and epoch retained, the `v3.1.0` row keeps revision `corpus-scope` and digest `1da8d2f843cb3b0ff1fd6dac5d41d4cafb5746388635c3f1ba5e41adde1d1f77`, the new frontier digest recomputes over its exact four-field line and differs from the prior row's, five history rows survive and only header lines changed; the frontmatter reads `4.1.0`, the front-door card names `anamnesis-v4.1.0`, the same current-frontier sentence stands in the landing README, `AGENTS.md` and the skill file, and the only surviving mention of a resolver-side constant is inside the append-only `v3.1.0` history row, which records what was true when it was written; both demo paths exit 0 and the pilot still rebuilds to `41d640fb`; and the declared-inputs block is one valid row naming the absent corpus the next job needs.
