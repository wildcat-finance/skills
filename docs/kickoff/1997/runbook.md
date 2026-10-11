# Wildcat archive timestamp runbook

Build the receipted `collector-journal` design from `.hexaemeron/study.md` at starting commit `21c151b7fe0cb80589c2ba8713678dfaee52354d`. All dates remain provider-recorded evidence. Retained inputs stay immutable.

Always: preserve native bytes and exact header number/hash joins; retain row-local unsupported reasons; run the declared checks and sign commits. Ask first: fleet recapture, dependencies, CI policy changes or private payload publication. Never: infer a date from a neighbouring block, native close argument, zero or a subgraph; rewrite existing release digests; claim unrun tests.

```design-lock
schema | protasis-design-evidence/v1
sha256 | fad03e94e38ba874d9ad8a47e815433d232ba550f2772a1052fd50f96281c4e3
candidate | collector-journal
```

```command-interfaces
schema | protasis-command-interfaces/v1
plugins/tabularium/tests/prove_wildcat_timestamps.py | build_parser | step:1
```

The proof runner's `scaffold`, `capture`, `mapping` and `demonstration` cases emit `unittest-json-v1` with executed counters, complete status and actual runner exit. Its `integration` case runs the demonstration and emits the separate closed `protasis-design-report/v1` for `collector-journal` / `timestamp-demo`; a false value or nonzero test exit cannot emit a passing report. Reports and capture outputs remain outside preserved inputs. The runner source stays unchanged after its Step 1 push binding; later steps extend its imported test modules.

## Step 1: Scaffold timestamp proof and specification

**Goal.** Establish the bounded proof runner, fixture scaffold and reviewed source specifications.
**Entry.** The run branch at the pinned starting commit, with study and design receipts.
**Exit.** Runner parser and JSON-report controls pass, and legacy fixture release verification remains green:

```sh
python3 plugins/tabularium/tests/prove_wildcat_timestamps.py --case scaffold --report .hexaemeron/steps/1/scaffold.json
```

**Files.** `plugins/tabularium/tests/prove_wildcat_timestamps.py`, `plugins/tabularium/tests/wildcat_timestamp_reports.py`, `plugins/tabularium/tests/test_wildcat_timestamps.py`, `docs/kickoff/1997/study.md`, `docs/kickoff/1997/runbook.md`, `docs/kickoff/1997/design-evidence.json`, bounded portable selection reports and proposal-model evidence under `docs/kickoff/1997/`, and `docs/decisions/drafts/preserve-wildcat-event-block-timestamps.md`. Extend `tests/check-map-v1.json` only if ownership is absent. Regenerate tracked portable copies and Horos metadata through their owners when checks require them. Do not publish local custody paths or private payloads.
**Tests.** Exercise parser cases, truthful positive/failing report counters, source/output separation and old V1/V2 fixture verification. Elenchus command: `python3 plugins/tabularium/tests/prove_wildcat_timestamps.py --case scaffold --report {report}`; format: `unittest-json-v1`; report file: `.elenchus/1997-step-1.json`. Run `python3 scripts/run_checks.py` for all actual changed paths before publication.
**Disciplines.** phylax: confined report output and shell-free runner execution. ephoros: executed counters and fixed failure records expose missing tests. metron: none, no performance change. elenchus: preserve a failing guard for any discovered runner defect. hypomnema: record additive preservation and legacy compatibility as the expensive format choice.

## Step 2: Preserve bounded event-block headers

**Goal.** Add opted-in V1/V2 event-header collection with complete offline verification and recoverable capture.
**Entry.** Step 1's verified push head, with the immutable proof runner binding.
**Exit.** New constructed V1/V2 captures deduplicate selected-event block headers, preserve bounded raw envelopes, resume without changing retained prefixes and verify offline; absent opt-in retains the exact old inventory/opening replay:

```sh
python3 plugins/tabularium/tests/prove_wildcat_timestamps.py --case capture --report .hexaemeron/steps/2/capture.json
```

**Files.** `plugins/alexandria/scripts/usdc_interval.py`, a narrowly owned event-header helper under `plugins/alexandria/scripts/alexandria_lib/`, relevant V1/V2 venue modules only where the selected design requires them, `plugins/alexandria/tests/` fixture and capture tests, imported timestamp test modules, `plugins/alexandria/docs/usdc-interval-collector.md`, and owner-generated portable/Horos metadata. Register every new path in the check map when existing patterns do not own it.
**Tests.** Exact opted-in plan marker, number/hash relation, deduplicated requests, byte/request/time/partition bounds, incomplete inventory, tampered checkpoints, interruption/resume, credentials-free errors, non-Wildcat refusal and unchanged old releases. Elenchus command: `python3 plugins/tabularium/tests/prove_wildcat_timestamps.py --case capture --report {report}`; format: `unittest-json-v1`; report file: `.elenchus/1997-step-2.json`. Run selected repository checks over actual source changes.
**Disciplines.** phylax: bounded RPC envelopes, no-follow filesystem admission and credential sanitation. ephoros: header counts, partial coverage and fixed refusals expose capture progress. metron: record added request counts and byte bounds on identical fixtures, with no speed claim. elenchus: guard each failed capture/verification mechanism before fixing it. hypomnema: document marker, journal inventory and interruption recovery at the producer.

## Step 3: Propagate row-local archive dates

**Goal.** Join preserved header timestamps in Tabularium and carry date, provenance and gaps through Probitas.
**Entry.** Step 2's verified push head; new opted-in header inventory is available and old releases verify.
**Exit.** All four archive families use a header with exactly the native event's number/hash; valid timestamp zero is handled as recorded zero only when actually supplied, never as fallback; unsupported rows remain undated and specifically explained:

```sh
python3 plugins/tabularium/tests/prove_wildcat_timestamps.py --case mapping --report .hexaemeron/steps/3/mapping.json
```

**Files.** `plugins/tabularium/scripts/tabularium_lib/wildcat_view.py`, narrow timestamp helpers if required, `plugins/probitas/scripts/probitas_lib/wildcat_archive.py`, existing view/archive tests, imported timestamp tests, `plugins/tabularium/docs/wildcat-archive.md`, Probitas's existing Wildcat venue reference, and owner-generated portable/Horos metadata.
**Tests.** Supported and missing/wrong-number/wrong-hash/malformed/conflicting headers; exact response/component selector digests; mixed dated/undated rows; Probitas integer dates, render and verification; native `MarketClosed` timestamp remains a separate value; unchanged canonical schema-3 behaviour. Elenchus command: `python3 plugins/tabularium/tests/prove_wildcat_timestamps.py --case mapping --report {report}`; format: `unittest-json-v1`; report file: `.elenchus/1997-step-3.json`. Run selected repository checks over actual changed paths.
**Disciplines.** phylax: strict quantity/hash parsing and confined raw inventory reads. ephoros: row-local support counts and missing reasons remain visible. metron: none, no speed optimization. elenchus: reproduce and guard any admitted wrong date or lost gap. hypomnema: document timestamp support/provenance and evidence class at both consumers.

## Step 4: Demonstrate capture-to-dossier timestamp boundaries

**Goal.** Prove the bounded V1/V2 path and publish the reproduction instructions and explicit retained-input limits.
**Entry.** Step 3's verified push head; collection and consumer checks pass.
**Exit.** Constructed capture-to-view-to-dossier demonstrations and legacy negative controls pass, and production conformance emits the selected design report before integration:

```sh
python3 plugins/tabularium/tests/prove_wildcat_timestamps.py --case demonstration --report .hexaemeron/steps/4/demonstration.json
python3 plugins/tabularium/tests/prove_wildcat_timestamps.py --case integration --report .hexaemeron/reports/collector-journal-timestamp-demo.json
```

**Files.** Imported timestamp integration tests and report helper if needed, `docs/kickoff/1997/reproduction.md`, portable bounded demonstration results, public retained-input census summaries without local custody paths, and owner-generated metadata. Keep the Step 1 runner parser/source unchanged.
**Tests.** Both generations and all four families; socket-denied offline rebuild/verification; wrong hash, incomplete new journal, mixed old header availability and Probitas evidence/render roundtrip; command and source identity in reports. Measure supported/unsupported rows on available retained raw releases without changing them. Elenchus command: `python3 plugins/tabularium/tests/prove_wildcat_timestamps.py --case demonstration --report {report}`; format: `unittest-json-v1`; report file: `.elenchus/1997-step-4.json`. Run selected repository checks and the clean Linux checkpoint proof required for Alexandria changes. Retained Lazarus payload verification stays unknown unless the exact payload is independently located and verified.
**Disciplines.** phylax: offline execution and source/output separation hold across the whole path. ephoros: demonstration reports expose counts, refusals and coverage. metron: measure bounded added requests/bytes without claiming fleet latency. elenchus: negative controls establish the named timestamp boundaries. hypomnema: record reproduction commands, controller version gap and retained-input limitations where readers start.
