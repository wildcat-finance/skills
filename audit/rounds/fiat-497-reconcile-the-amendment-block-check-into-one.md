## Step 1, round 1 -- 2026-08-29T23:25:15Z

Audit schema: fiat-audit-round/v2

Covered: false-clean=reviewed; scanner-drift=not-applicable; field-extraction=not-applicable; prefix-continuity=not-applicable; fence-semantics=reviewed; interface-stability=reviewed; partial-write=not-applicable; frontier-arithmetic=not-applicable

Not checked: Fiat controller parsing and durable mutation or recovery, plus Protasis frontier and version publication, are Step 2; the Solidity security suite was waived for this non-Solidity Python-and-prose step.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: Step 2 owns controller extraction, prefix and write recovery, and frontier or version publication; those four packet risks are not applicable here. Solidity and EVM behavior, authorization, network or RPC access, credentials, dependency changes, subprocess creation, persistent state, concurrency, and unattended telemetry are absent or waived. The `9e25b995bf4be019195596d2af2ff65ba896a4..2358663f376546e680b1904a5957c45365f0f4da` range was reviewed for acceptance, input grammar, fence state, date and field validation, bounds, diagnostics, CLI and JSON behavior, compatibility, generated-copy parity, tests, documents, and provenance. The parent returned clean for all five omission fixtures; this tree returned S008 for each, passed 97 of 97 focused tests and 1,989 of 1,989 Hexaemeron tests with 5 fixture-blocked by design. The exact host record also ran through Brevitas report mode, which exited 1 on B010 and B011 because `fiat-audit-round/v2` requires one heading and the canonical one-row zero-finding table; changing either would violate the controller grammar, so host structure took precedence. The narrative-only projection exited 0; the full record is not claimed Brevitas-clean. No Step 1 finding, fix, or unguarded product lead remains.

## Step 2, round 1 -- 2026-08-30T01:55:38Z

Audit schema: fiat-audit-round/v2

Covered: false-clean=reviewed; scanner-drift=reviewed; field-extraction=reviewed; prefix-continuity=reviewed; fence-semantics=reviewed; interface-stability=reviewed; partial-write=reviewed; frontier-arithmetic=reviewed

Not checked: The bundled Solidity security suite was waived for this non-Solidity Python checker and frontier work. Controller receipts, GitHub push, pull-request, issue, merge and publication operations, network or RPC access, credentials, and live-service behavior were outside this round.

Elenchus verdict: unguarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | low | .horos/boundary.json | The final audit source and synopsis increased the tracked-file census after Horos regeneration, so the boundary count was stale and the root currency test failed. | fixed in Warden commit |

Leads not pursued: The `2358663f376546e680b1904a5957c45365f0f4da..d3e77a85460eb0339c3312280406a24ea2082eb8` product range was reviewed for the pre-mutation Protasis boundary, exact captured-byte handling, fixed subprocess arguments, bounded output and cleanup, accepted-field extraction, prefix and state joins, recovery, diagnostics, interface compatibility, canonical/runtime parity, frontier arithmetic, version propagation, generated documents, and marketplace continuity. The focused suite passed 473 of 473 tests; the full Hexaemeron suite passed 1,989 of 1,989 with 5 fixture-blocked by design; the root suite passed 495 of 495 with 3 skips; both Promise Machine checks and the six-check affected-scope runner exited 0. Direct Imprimatur, Phylax, Ephoros, Hypomnema, Horos, frontmatter, copy-parity, and diff checks were clean. Protasis is `5.9.0` with mature frontier digest `ca34e050ea7b11b33b1fa1f9575e398f481e20a6e33c7f4edc85cad0d19d5299`; Fiat is `5.38.1`; Hexaemeron is `1.6.12`; the generated PDF digest is `e562f12cbfbff650316c4f00a56f9f2ba474290940061d32752480cd553cbdf6`. For S2-R1-01, `tests/test_boundary_currency.py:155` failed with `.horos/boundary.json#counts` on the staged audit tree; regenerating Horos changed only `files_walked` from 2,059 to 2,061, and the same test then passed. The source-bound Elenchus mechanism sees no changed test file in the admitted fix, so its verdict is `unguarded`; the already-existing guard and its observed red-to-green result remain direct evidence. The exact host record ran through Brevitas report mode, which exited 1 on B010 and B011 because the append-only history has two required round headings and each schema-required findings table has fewer than three rows; changing that host structure would violate `fiat-audit-round/v2`, so the host grammar took precedence. The Step 2 narrative-only projection exited 0; the full record is not claimed Brevitas-clean. `plugins/hexaemeron/README.md:31` begins a pre-existing Synkrisis scaffold description that conflicts with the current root marketplace description; it is unrelated to issue 497, outside the amended Step 2 Files, and remained unchanged. No other Step 2 finding, fix, or unguarded admitted-scope lead remains.
