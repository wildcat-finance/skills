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
