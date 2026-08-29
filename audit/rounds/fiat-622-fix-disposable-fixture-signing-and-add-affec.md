## Step 1, round 1 -- 2026-08-25T21:12:24Z

Audit schema: fiat-audit-round/v2

Covered: fixture-signing-scope=reviewed; source-config-mutation=reviewed; impact-map-omission=not-applicable; dependency-cycle=not-applicable; manifest-bootstrap=not-applicable; snapshot-drift=not-applicable; snapshot-copy-boundary=not-applicable; dynamic-test-identity=not-applicable; shard-accounting=not-applicable; global-process-budget=not-applicable; timing-cache-authority=not-applicable; subprocess-output=not-applicable; report-compatibility=reviewed; timing-sensitive-contention=not-applicable; fixture-collection-count=reviewed; ordered-command-breakage=not-applicable; unstable-source-label=not-applicable

Not checked: GitHub-side signature verification and hosted CI because this branch has not been pushed; Steps 2-4 executor behaviour is outside this round.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: Brevitas report mode rejects the mandatory v2 one-heading, one-zero-row shape with B010 and B011. Fiat's stricter host schema controls this record; the pre-existing framework mismatch is outside Step 1.

## Step 2, round 1 -- 2026-08-25T23:19:43Z

Audit schema: fiat-audit-round/v2

Covered: fixture-signing-scope=not-applicable; source-config-mutation=not-applicable; impact-map-omission=not-applicable; dependency-cycle=not-applicable; manifest-bootstrap=reviewed; snapshot-drift=not-applicable; snapshot-copy-boundary=not-applicable; dynamic-test-identity=reviewed; shard-accounting=reviewed; global-process-budget=reviewed; timing-cache-authority=reviewed; subprocess-output=reviewed; report-compatibility=reviewed; timing-sensitive-contention=reviewed; fixture-collection-count=reviewed; ordered-command-breakage=not-applicable; unstable-source-label=not-applicable

Not checked: GitHub-side signature verification and hosted CI because this branch has not been pushed; Step 3's impact map, snapshot, global executor and ordered groups; a new serial full-suite sample because this audit's local execution requirement permits only 12-worker suite reruns and the earlier serial measurement is already recorded. The Solidity security suite was waived because this step changes no Solidity.

Elenchus verdict: passed

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | medium | plugins/hexaemeron/tests/run_tests.py | Private worker results affected exit handling and output replay before object, schema and result-slot validation; swapped records passed reconciliation, malformed values escaped scheduler-error handling, and byte metadata was not bound to replayed text. | fixed; four parent-red guards pass on this branch |
| S2-R1-02 | medium | plugins/hexaemeron/tests/run_tests.py | The durable summary discarded per-shard assignment, start, completion and duration evidence; total reconciliation failure also discarded workers already validated. | fixed; two parent-red guards pass on this branch |

Leads not pursued: Elenchus returned passed rather than guarded because its changed-test overlay copied the changed runner onto the parent; the independent untouched-parent run produced six assertion failures and zero errors, while the branch accounting class passed 8/8. The inherited public exit rule omits unexpected successes from its failure count on both parent and branch; the 1,191-test manifest had none and the behaviour predates Step 2. Brevitas report mode still rejects Fiat's mandatory v2 record shape with B010 and B011; the source-bound Fiat schema controls this record.

## Step 2, round 2 -- 2026-08-25T23:41:39Z

Audit schema: fiat-audit-round/v2

Covered: fixture-signing-scope=not-applicable; source-config-mutation=not-applicable; impact-map-omission=not-applicable; dependency-cycle=not-applicable; manifest-bootstrap=reviewed; snapshot-drift=not-applicable; snapshot-copy-boundary=not-applicable; dynamic-test-identity=reviewed; shard-accounting=reviewed; global-process-budget=reviewed; timing-cache-authority=reviewed; subprocess-output=reviewed; report-compatibility=reviewed; timing-sensitive-contention=reviewed; fixture-collection-count=reviewed; ordered-command-breakage=not-applicable; unstable-source-label=not-applicable

Not checked: GitHub-side signature verification and hosted CI because this branch has not been pushed; Step 3's impact map, snapshot, global executor and ordered groups; a new serial full-suite sample because this audit's local execution requirement permits only 12-worker suite reruns and the earlier serial measurement is already recorded. The Solidity security suite was waived because this step changes no Solidity.

Elenchus verdict: passed

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R2-01 | medium | plugins/hexaemeron/tests/run_tests.py | The round-1 event repeated raw assigned, started, completed and duration IDs in every shard beneath only per-worker caps; accepted 400-ID records extrapolated to 19,239,156 bytes at 12 shards and 410,435,328 bytes at `MAX_JOBS`. | fixed; the manifest is recorded once beneath a 327,680-byte cap, canonical indices plus sequence bindings retain recoverable evidence, the event refuses above 2,097,152 bytes, and three exact-parent guards are red and branch-green |
| S2-R2-02 | medium | plugins/hexaemeron/tests/run_tests.py | After one valid worker and one missing worker, the durable shard proved one execution while `summary.execution` still recorded zero tests, starts and completions and omitted the shard's outcome counters. | fixed; only validated records supply compact shard and partial execution counts, and the exact-parent guard is red and branch-green |

Leads not pursued: Elenchus returned passed rather than guarded because its changed-test overlay copied the changed runner onto the parent; independent overlays on exact `b181c99b862528644108b0519b8a027394760c4e` produced four assertion failures and zero errors, while the branch accounting class passed 10/10 and its module passed 25/25. Explicit and automatic 12-worker runs each passed 1,193/1,193 with manifest `166edaa18c4cc3d940d5ca212f6813bfd7f8f08407436cc774b07b64f82844ee`; automatic capacity derived 12 and both runs observed at most 12 live children. The inherited public exit rule still omits unexpected successes from its failure count; both full runs had none and the behaviour predates Step 2. Brevitas report mode rejects Fiat's mandatory small v2 tables with B011; the source-bound Fiat schema controls this record.

## Step 2, round 3 -- 2026-08-26T00:13:56Z

Audit schema: fiat-audit-round/v2

Covered: fixture-signing-scope=not-applicable; source-config-mutation=not-applicable; impact-map-omission=not-applicable; dependency-cycle=not-applicable; manifest-bootstrap=reviewed; snapshot-drift=not-applicable; snapshot-copy-boundary=not-applicable; dynamic-test-identity=reviewed; shard-accounting=reviewed; global-process-budget=reviewed; timing-cache-authority=reviewed; subprocess-output=reviewed; report-compatibility=reviewed; timing-sensitive-contention=reviewed; fixture-collection-count=reviewed; ordered-command-breakage=not-applicable; unstable-source-label=not-applicable

Not checked: GitHub-side signature verification and hosted CI because this branch has not been pushed; Step 3's impact map, snapshot, global executor and ordered groups; a new serial full-suite sample because this audit's local execution requirement permits only 12-worker suite reruns and the earlier serial measurement is already recorded. The Solidity security suite was waived because this step changes no Solidity.

Elenchus verdict: passed

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R3-01 | medium | plugins/hexaemeron/tests/run_tests.py | Truncated worker output was accepted when it contained only the expected marker, without the complete bounded head and tail; replacement decoding expanded the retained bytes before replay. | fixed; three exact-parent assertions are red and branch-green |
| S2-R3-02 | medium | plugins/hexaemeron/tests/run_tests.py | A valid bounded manifest plus valid bounded test output exceeded the 2,097,152-byte private result limit after JSON encoding. | fixed; parallel text now uses coordinator-bounded pipes, accounting JSON uses bounded UTF-8 encoding, and two exact-parent assertions are red and branch-green |
| S2-R3-03 | medium | plugins/hexaemeron/tests/run_tests.py | Timing-cache reads traversed a linked parent outside the invocation directory. A checked parent remained replaceable before path-based temporary replacement. | fixed; one no-follow directory-descriptor walk binds read, temporary creation, replacement and cleanup. Two exact-parent assertions are red and branch-green |
| S2-R3-04 | medium | plugins/hexaemeron/tests/run_tests.py | Excessive JSON nesting raised `RecursionError` outside the cache and worker parse-refusal outcomes. | fixed; strict JSON parsing translates only `RecursionError` to the existing parse refusal, and one exact-parent assertion is red and branch-green |

Leads not pursued: Elenchus returned passed rather than guarded because its changed-test overlay copied the changed runner onto the parent; the independent exact `af32a2d640528ede18480bcd97b3cc09e98e707e` tests-only run produced eight assertion failures and zero errors, while the branch module passed 34/34. Explicit and automatic 12-worker runs each passed 1,202/1,202 with manifest `93774e967cdd39968ebc1a079e970ba231cc83295b2c7d0803570176181459ac`. Each observed at most 12 live children. They completed in 64.115 and 59.922 seconds respectively. The inherited public exit rule still omits unexpected successes from its failure count; both full runs had none and the behaviour predates Step 2. Brevitas report mode rejects Fiat's mandatory small v2 tables with B011; the source-bound Fiat schema controls this record.

## Step 2, round 4 -- 2026-08-26T00:32:25Z

Audit schema: fiat-audit-round/v2

Covered: fixture-signing-scope=not-applicable; source-config-mutation=not-applicable; impact-map-omission=not-applicable; dependency-cycle=not-applicable; manifest-bootstrap=reviewed; snapshot-drift=not-applicable; snapshot-copy-boundary=not-applicable; dynamic-test-identity=reviewed; shard-accounting=reviewed; global-process-budget=reviewed; timing-cache-authority=reviewed; subprocess-output=reviewed; report-compatibility=reviewed; timing-sensitive-contention=reviewed; fixture-collection-count=reviewed; ordered-command-breakage=not-applicable; unstable-source-label=not-applicable

Not checked: GitHub-side signature verification and hosted CI because this branch has not been pushed; Step 3's impact map, snapshot, global executor and ordered groups; a new serial full-suite sample because the earlier control remains recorded. The Solidity security suite was waived because this step changes no Solidity.

Elenchus verdict: passed

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R4-01 | medium | plugins/hexaemeron/tests/run_tests.py | Worker validation assumed outcome events could not exceed top-level `testsRun`; legitimate multiple failing subtests were changed from test-failure evidence into scheduler-error. | fixed; one exact-parent assertion is red and branch-green |
| S2-R4-02 | medium | plugins/hexaemeron/tests/run_tests.py | Coordinator pipe read and close errors were discarded inside drain threads, so the reproduced failure dropped bounded subprocess output without refusing green. | fixed; one exact-parent assertion is red and branch-green |

Leads not pursued: Elenchus overlays the changed runner with its changed tests and is expected to return passed rather than guarded; an independent tests-only overlay on exact `51e53d55b917cf8019124b6e7acc5cc7d6e78fbb` produced two assertion failures and zero errors, while the branch module passed 36/36. The inherited public exit rule still omits unexpected successes from its failure count; both comprehensive runs had none and the behaviour predates Step 2. Brevitas report mode rejects Fiat's mandatory small v2 table with B011; the source-bound Fiat schema controls this record.

## Step 2, round 5 -- 2026-08-26T00:57:06Z

Audit schema: fiat-audit-round/v2

Covered: fixture-signing-scope=not-applicable; source-config-mutation=not-applicable; impact-map-omission=not-applicable; dependency-cycle=not-applicable; manifest-bootstrap=reviewed; snapshot-drift=not-applicable; snapshot-copy-boundary=not-applicable; dynamic-test-identity=reviewed; shard-accounting=reviewed; global-process-budget=reviewed; timing-cache-authority=reviewed; subprocess-output=reviewed; report-compatibility=reviewed; timing-sensitive-contention=reviewed; fixture-collection-count=reviewed; ordered-command-breakage=not-applicable; unstable-source-label=not-applicable

Not checked: GitHub-side signature verification and hosted CI because this branch has not been pushed; Step 3's impact map, snapshot, global executor and ordered groups; a new serial full-suite sample because the earlier control remains recorded; a live suite near `MAX_TESTS`, because the limit was exercised with valid synthetic protocol records; non-macOS capacity and cgroup execution paths. The Solidity security suite was waived because this step changes no Solidity.

Elenchus verdict: passed

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R5-01 | medium | plugins/hexaemeron/tests/run_tests.py | The accepted manifest and private worker-result limits did not compose: a 327,675-byte manifest with 54,604 one-character Unicode IDs and duration `0.00012345678901234567` produced a valid 2,992,593-byte accounting record against the 2,097,152-byte result cap. | fixed; the 5,527,104-byte cap is derived from every bounded variable field plus a 16,384-byte fixed reserve, and two exact-parent assertions are red and branch-green |
| S2-R5-02 | medium | plugins/hexaemeron/tests/run_tests.py | Parseable integers of 309 digits or more raised `OverflowError` from `math.isfinite` before duration and wall-time validation could produce the stable scheduler-error outcome. | fixed; one bounded numeric predicate rejects token, type, value and overflow failures, and two exact-parent assertions are red and branch-green |

Leads not pursued: Elenchus overlays the changed runner with its changed tests and is expected to return passed rather than guarded; an independent tests-only overlay on exact `e3fd4d01a558b24c3f42f47d3c90b36428708f12` produced four assertion failures and zero errors, while the branch module passed 38/38. Explicit and automatic comprehensive runs each passed 1,206/1,206 with manifest `c2ac24d89492e6c1c6f3e93f78b042bb43004f80828486cee2a4e091efa45a82`, complete assignment, start and completion accounting, and no unexpected successes; they completed in 59.371 and 59.323 seconds. The inherited public exit rule still omits unexpected successes from its failure count; neither comprehensive run had one and the behaviour predates Step 2. Brevitas report mode rejects Fiat's mandatory small v2 table with B011; the source-bound Fiat schema controls this record.

## Step 2, round 6 -- 2026-08-26T01:31:43Z

Audit schema: fiat-audit-round/v2

Covered: fixture-signing-scope=not-applicable; source-config-mutation=not-applicable; impact-map-omission=not-applicable; dependency-cycle=not-applicable; manifest-bootstrap=reviewed; snapshot-drift=not-applicable; snapshot-copy-boundary=not-applicable; dynamic-test-identity=reviewed; shard-accounting=reviewed; global-process-budget=reviewed; timing-cache-authority=reviewed; subprocess-output=reviewed; report-compatibility=reviewed; timing-sensitive-contention=reviewed; fixture-collection-count=reviewed; ordered-command-breakage=not-applicable; unstable-source-label=not-applicable

Not checked: GitHub-side signature verification and hosted CI because this branch has not been pushed; Step 3's impact map, snapshot, global executor and ordered groups; a new serial full-suite sample because the earlier control remains recorded; a live suite near `MAX_TESTS`; non-macOS capacity and cgroup execution paths; automatic capacity on a host with more than 256 usable processors. The Solidity security suite was waived because this step changes no Solidity.

Elenchus verdict: passed

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R6-01 | medium | plugins/hexaemeron/tests/run_tests.py | A parseable timing-cache integer of 309 digits or more reached `math.isfinite` and raised `OverflowError` instead of producing the visible neutral corrupt-entry cache-miss outcome. | fixed; bounded numeric validation rejects the entry, reports `partial` and `corrupt-entry`, uses no cached timings, and rewrites without the rejected value |
| S2-R6-02 | medium | plugins/hexaemeron/tests/run_tests.py | Public `--jobs 1` ran the suite in the coordinator process, so raw file-descriptor and child-process output bypassed bounded capture while the summary reported no live worker. | fixed; the same coordinator pipe mechanism now runs exactly one private worker, and a child-originated 300,000-byte raw-output guard proves bounded replay, ordering, and one effective, queued and live worker |
| S2-R6-03 | medium | plugins/hexaemeron/tests/run_tests.py | Individually valid worker outcome counters could sum above Python's sequence-size limit, causing `AggregateResult` to raise `OverflowError` while materialising public result sequences. | fixed; aggregate counters are bounded before sequence construction, an uneven valid total of `sys.maxsize` remains accepted, and legitimate multiple failing subtests remain ordinary test failures |

Leads not pursued: Elenchus overlays the changed runner with its changed tests and is expected to return passed rather than guarded; an independent tests-only overlay on exact `e7b11ac9f30540567c6a0ba498476e857e3d9a10` produced four assertion failures and zero errors, while the branch runner module passed 42/42 and the Elenchus-checker module passed 30/30. Explicit and automatic comprehensive runs each passed 1,210/1,210 with manifest `8b2fed70d2849d2eef46b4dd80defc7e78513af42b73a2e5e99a382f162f4f71`, complete assignment, start and completion accounting, and no scheduler errors or unexpected successes. They completed in 58.668 and 62.281 seconds and observed at most 12 live workers. The automatic-capacity path on a host with more than 256 usable processors remains an unexercised operational lead; this round does not change `MAX_JOBS` or scheduling policy. The first comprehensive attempt exposed a short-write test double that intercepted assignment writes before the report write; the test now scopes that double to `write_report`, with production report handling unchanged. The inherited public exit rule still omits unexpected successes from its failure count; neither comprehensive run had one and the behaviour predates Step 2. Brevitas report mode rejects Fiat's mandatory small v2 table with B011; the source-bound Fiat schema controls this record.

## Step 2, round 7 -- 2026-08-26T02:01:28Z

Audit schema: fiat-audit-round/v2

Covered: fixture-signing-scope=not-applicable; source-config-mutation=not-applicable; impact-map-omission=not-applicable; dependency-cycle=not-applicable; manifest-bootstrap=reviewed; snapshot-drift=not-applicable; snapshot-copy-boundary=not-applicable; dynamic-test-identity=reviewed; shard-accounting=reviewed; global-process-budget=reviewed; timing-cache-authority=reviewed; subprocess-output=reviewed; report-compatibility=reviewed; timing-sensitive-contention=reviewed; fixture-collection-count=reviewed; ordered-command-breakage=not-applicable; unstable-source-label=not-applicable

Not checked: GitHub-side signature verification and hosted CI because this branch has not been pushed; Step 3's impact map, snapshot, global executor and ordered groups; a new serial full-suite sample because the earlier control remains recorded; a live suite near `MAX_TESTS`; non-macOS capacity and cgroup execution paths; automatic capacity on a host with more than 256 usable processors. The Solidity security suite was waived because this step changes no Solidity.

Elenchus verdict: passed

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R7-01 | medium | plugins/hexaemeron/tests/run_tests.py | Cross-worker outcome totals above Python's sequence-size limit were refused during reconciliation, then the scheduler-error handler rebuilt the same oversized partial aggregate and let a second `SchedulerError` escape the public boundary. | fixed; the partial aggregate remains neutral while validated shard evidence and both refusal reasons remain visible, and one exact-parent guard is red and branch-green |
| S2-R7-02 | medium | plugins/hexaemeron/tests/run_tests.py | The human summary subtracted failure and error events from top-level `testsRun`; one test with two legitimate failing subtests therefore printed a negative passed-test count. | fixed; failing runs name top-level tests and exact outcome-event counts without inferring passed tests, and one exact-parent guard is red and branch-green |
| S2-R7-03 | medium | plugins/hexaemeron/tests/run_tests.py | The structured-summary size refusal retained the oversized scheduler-error sequence and immediately encoded it again, so its fallback raised the same size refusal instead of emitting one bounded event. | fixed; the refusal keeps one explicit error plus count, encoded size and digest evidence for the omitted ordered sequence, and one exact-parent guard is red and branch-green |
| S2-R7-04 | medium | plugins/hexaemeron/tests/run_tests.py | Manifest flattening recursed through nested suites and materialised every test before enforcing `MAX_TESTS`, allowing valid deep nesting to raise `RecursionError` and oversized discovery to read past its item bound. | fixed; iterative depth-first flattening preserves order, rejects active-path cycles and enforces the item limit during discovery, and two exact-parent guards are red and branch-green |

Leads not pursued: Elenchus overlays the changed runner with its changed tests and is expected to return passed rather than guarded; an independent tests-only overlay on exact `4c6eaca6f62c2db903fb867c09b30de8444f1ad9` made all five focused guards red with two assertion failures and three errors, while the branch runner module passed 47/47 and the Elenchus-checker module passed 30/30. Explicit and automatic comprehensive runs each passed 1,215/1,215 with manifest `28e17c47fa2883676e4a1f880de64baf1f82aaed0addc4a0e78faaf9a05ed06a`, complete assignment, start and completion accounting, and no scheduler errors or unexpected successes; they completed in 66.531 and 65.691 seconds. The Promise Machine contract suite passed 73/73 and the root suite passed 396/396. The automatic-capacity path on a host with more than 256 usable processors remains an unexercised operational lead; this round does not change `MAX_JOBS` or scheduling policy. The inherited public exit rule still omits unexpected successes from its failure count; neither comprehensive run had one and the behaviour predates Step 2. Brevitas report mode rejects Fiat's mandatory small v2 table with B011; the source-bound Fiat schema controls this record.

## Step 2, round 8 -- 2026-08-26T02:30:28Z

Audit schema: fiat-audit-round/v2

Covered: fixture-signing-scope=not-applicable; source-config-mutation=not-applicable; impact-map-omission=not-applicable; dependency-cycle=not-applicable; manifest-bootstrap=reviewed; snapshot-drift=not-applicable; snapshot-copy-boundary=not-applicable; dynamic-test-identity=reviewed; shard-accounting=reviewed; global-process-budget=reviewed; timing-cache-authority=reviewed; subprocess-output=reviewed; report-compatibility=reviewed; timing-sensitive-contention=reviewed; fixture-collection-count=reviewed; ordered-command-breakage=not-applicable; unstable-source-label=not-applicable

Not checked: GitHub-side signature verification and hosted CI because this branch has not been pushed; Step 3's impact map, snapshot, global executor and ordered groups; a new serial full-suite sample because the earlier control remains recorded; a live suite near `MAX_TESTS`; non-macOS capacity and cgroup execution paths; automatic capacity on a host with more than 256 usable processors; a background descendant that never closes an inherited output descriptor. The Solidity security suite was waived because this step changes no Solidity.

Elenchus verdict: passed

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R8-01 | medium | plugins/hexaemeron/tests/run_tests.py | A passing test that printed the reserved `HEXAEMERON-RUN` prefix produced a second machine-shaped summary beside the genuine terminal event. | fixed; reserved-prefix stdout and stderr lines remain visible under `HEXAEMERON-TEST-OUTPUT`, and one exact-parent guard is red and branch-green |
| S2-R8-02 | medium | plugins/hexaemeron/tests/run_tests.py | Ordinary exceptions raised while opening or advancing a discovered suite iterator escaped with exit 1, a traceback and no structured scheduler outcome. | fixed; ordinary iterator failures become bounded scheduler refusals while process-control exceptions remain untouched, and two exact-parent subcases are red and branch-green |
| S2-R8-03 | medium | plugins/hexaemeron/tests/run_tests.py | An ordinary exception raised by a discovered test's `id()` callback escaped with exit 1, a traceback and no structured scheduler outcome. | fixed; identifier callback failures become bounded scheduler refusals, and one exact-parent guard is red and branch-green |
| S2-R8-04 | medium | plugins/hexaemeron/tests/run_tests.py | `MAX_TESTS` counted only test leaves, allowing a lazy suite to yield an unbounded sequence of `None` or nested suite items without consuming the discovery limit. | fixed; every yielded suite item consumes the existing incremental limit, the deep and cyclic cases remain valid, and one exact-parent guard is red and branch-green |

Leads not pursued: An independent tests-only overlay on exact `f2a2d35cfba19d0674b613892605b33e7835b616` made all four new methods red with five assertion failures and zero errors, while the branch runner module passed 51/51 and the Elenchus-checker module passed 30/30. Explicit and automatic comprehensive runs each passed 1,219/1,219 with manifest `ea1d932593c6a6fab72d9a1557311a7ea4cb7366097a48b5751549e9f2580a72`, complete assignment, start and completion accounting, and no failures, errors, unexpected successes or scheduler errors; they completed in 71.232 and 66.848 seconds. A maximal 327,679-byte synthetic manifest produced a 1,185,782-byte complete summary beneath the 2,097,152-byte event limit. The Promise Machine contract suite passed 73/73 and the root suite passed 396/396. Elenchus's existing unittest report reader rejects an accurate one-test report containing two failing subtest events because their category count exceeds `testsRun`; that consumer is outside the Step 2 runner file set and remains a carryover lead. A short-lived background descendant retained an inherited output descriptor and delayed coordinator drain until it closed; Step 2 defines no child-lifetime or timeout policy. The automatic-capacity path on a host with more than 256 usable processors remains unexercised and this round does not change policy. The inherited public exit rule still omits unexpected successes from its failure count; neither comprehensive run had one and the behaviour predates Step 2. Brevitas report mode rejects Fiat's mandatory small v2 table with B011; the source-bound Fiat schema controls this record.
