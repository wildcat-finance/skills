# Study: Tabularium canonical-event-v3 and coverage-manifest-v3 with enums that match shipped adapter emissions

Task issue: [wildcat-finance/skills#1362](https://github.com/wildcat-finance/skills/issues/1362). Packet handle: `fiat-1362-study-surveyor`. Starting commit `1d131b98a78c888b571f302e5b4c899aa2e47caf` (origin/main tip at init). Run branch `fiat/1362-tabularium-canonical-event-v3-and-coverage`, integrating into `main`. Every repository link below is pinned to that commit.

## 1. Problem statement, user, working prototype and demo path

### Assumptions

Assuming, unless corrected:

1. The exact interpreter is `.python-version` 3.14.6 (`pyproject.toml` pins `==3.14.*`) with stdlib `unittest`; Tabularium's runtime stays standard-library only.
2. `jsonschema` 4.25.1 is available to tests but is not a Tabularium runtime dependency. It is pinned in `plugins/lazarus/requirements.lock`, which `.github/workflows/plugins.yml:83-84` installs in every CI shard including `tabularium`; the local `/opt/homebrew/bin/python3` has it too. Repository precedent is `skipTest("jsonschema is not installed")` at `plugins/ariadne/tests/test_schema_agreement.py:96-99`; this study follows it for the parity tests and requires the reporter in section 1 to exit non-zero instead of skipping.
3. The release policy at `plugins/tabularium/docs/release-policy.md` governs: a published release is immutable; a schema change gets a new version and a new release directory with a new release identifier; source bytes may be reused only at an unchanged digest.
4. The held Tabularium frontier job (Compound v3 Phase 1) is not changed. `plugins/tabularium/docs/compound-v3-preservation.md:225-228` already says Phase 1 takes "schema v3, or the next available version if another release lands first", so Phase 1 will take v4 after this run.
5. No Solidity exists; the security suite waiver recorded at init stands. No live network is used anywhere.
6. The four `v0` release directories (`aave-v4-v0`, `euler-v1-v0`, `euler-v2-v0`, `compound-v3-phase0-v0`) keep every byte. The Compound Phase 0 witness carries its own `compound-v3-witness-manifest-v1` and `compound-v3-execution-fact-v1` schemas and is outside this topic.

### Problem

The two checked-in JSON Schemas describe a shipped ledger they reject. At `1d131b98` the `aave-v4` adapter emits `venue`, `provenance.adapter` and `provenance.protocol_generation` equal to `aave-v4` and `provenance.adapter_version` equal to `2.0.0`, while `canonical-event-v2.json` admits only `euler-v1`, `euler-v2` and `1.0.0`. Nothing runs the JSON Schema: `plugins/tabularium/tests/test_schemas.py` reads the documents structurally (5 tests, no `jsonschema` import anywhere under `plugins/tabularium`), and build and verify run the Python validator in `release_v2.py`, which binds each field to the adapter module's constants and therefore accepts what the adapters emit. Measured with `jsonschema` 4.25.1 at the starting commit: all 500 rows of `aave-v4-v0/events.jsonl` fail the v2 event schema with four errors each (`venue`, `provenance/adapter`, `provenance/adapter_version`, `provenance/protocol_generation`); `aave-v4-v0/coverage.json` fails the v2 coverage schema with three errors (`source/protocol_generation`, `versions/adapter/name`, `versions/adapter/version`); the Euler releases pass both.

Issue line references re-resolved at `1d131b98`: `canonical-event-v2.json:34` is `venue`, `:134` is `provenance.adapter`, `:135` is `adapter_version` (`const "1.0.0"`), `:136` is `protocol_generation`; `coverage-manifest-v2.json:38` is `source.protocol_generation`, `:82` is `versions.adapter.name`. The issue omits `coverage-manifest-v2.json:83`, `versions.adapter.version` `const "1.0.0"`, which also rejects `2.0.0`. All six cited lines still hold what the issue says; the seventh is added here.

### User

Anyone who validates a Tabularium release outside the Python tool: Alexandria's derived-index adapter and Miskatonic's native-action importer (issue comment of 2026-09-13), Probitas dossiers, and any auditor who takes `schemas/*.json` as the contract. In this repository no code reads the JSON Schema files; the README links them and `test_schemas.py` opens them. Miskatonic is not in this repository.

### Working prototype

A working prototype means, at the tip of the run:

1. `plugins/tabularium/schemas/canonical-event-v3.json` and `coverage-manifest-v3.json` exist, draft 2020-12, with `schema_version` `const 3` and the closed adapter tuple table in section 4 as `enum` values plus a `oneOf` binding per adapter.
2. `build` emits `schema_version` 3 by default; `verify` accepts a release whose coverage manifest says 2 or 3 and refuses any other value or a mixed release.
3. Three superseding release directories `examples/aave-v4-v1`, `examples/euler-v1-v1`, `examples/euler-v2-v1` carry schema 3, built from the byte-identical v0 `source.json` bytes, each with `README.md`, `DATA-DICTIONARY.md` and `rebuild.py`. The three v0 directories are unchanged and still verify and rebuild.
4. `tests/test_schemas.py` validates every shipped `events.jsonl` row and `coverage.json` against the JSON Schema its `schema_version` names (v0 against corrected v2, v1 against v3), and carries unknown-value, wrong-version and malformed-provenance fixtures that both the JSON Schema and the Python validator reject with a named cause.
5. The v2 schema files carry `"deprecated": true` and a description naming v3 and the supersession date, and their enums are corrected to what the v2 Python validator admitted, so the immutable v0 releases validate under the schema that describes them.
6. `plugins/tabularium/docs/release-policy.md` states the v2 read-only policy and the v3 migration: verify reads 2 and 3; build writes 3; `--event-schema 2` exists only to reproduce a published v2 release; consumers select by `schema_version`.

### Success criteria and demo path

Every criterion is a command from the repository root; `TMPDIR` must point under `/private/tmp` or the run worktree on this host.

```text
python3 -m unittest discover -s plugins/tabularium/tests -t plugins/tabularium
python3 plugins/tabularium/examples/aave-v4-v1/rebuild.py
python3 plugins/tabularium/examples/euler-v1-v1/rebuild.py
python3 plugins/tabularium/examples/euler-v2-v1/rebuild.py
python3 plugins/tabularium/examples/aave-v4-v0/rebuild.py
python3 plugins/tabularium/examples/euler-v1-v0/rebuild.py
python3 plugins/tabularium/examples/euler-v2-v0/rebuild.py
python3 plugins/tabularium/scripts/tabularium.py verify plugins/tabularium/examples/aave-v4-v1/coverage.json
python3 plugins/tabularium/tests/prove_schema_v3.py --candidate superseding-releases --criterion rejection-parity --report <abs>/.hexaemeron/reports/superseding-releases-rejection-parity.json
python3 plugins/tabularium/tests/prove_schema_v3.py --candidate superseding-releases --criterion shipped-ledgers-validate-v3 --report <abs>/.hexaemeron/reports/superseding-releases-shipped-ledgers-validate-v3.json
python3 plugins/tabularium/tests/prove_schema_v3.py --candidate superseding-releases --criterion legacy-v0-verify --report <abs>/.hexaemeron/reports/superseding-releases-legacy-v0-verify.json
python3 plugins/tabularium/tests/prove_schema_v3.py --candidate superseding-releases --criterion suite-wall-time --report <abs>/.hexaemeron/reports/superseding-releases-suite-wall-time.json
python3 scripts/plugin_release.py --base 1d131b98a78c888b571f302e5b4c899aa2e47caf --head "$(git write-tree)"
python3 -m unittest discover -s tests
```

`prove_schema_v3.py` is a new reporter (created in step 3) writing one closed `protasis-design-report/v1` object per criterion; it exits non-zero when `jsonschema` is absent rather than skipping. The exact `<abs>` prefix is the run worktree; the design record already binds the absolute resolver strings.

Baseline at the starting commit: 137 Tabularium tests pass in 3.65 s; all three v0 rebuilds match (`490d3f63…`, `40346228…`, `f563baa0…`); `verify` of `aave-v4-v0` takes 0.10 s; validating 500 v3-draft rows with `jsonschema` takes 93 ms.

### Proposed step layout

The design record's pending cells name step numbers, so the runbook must keep this order.

1. Scaffold: commit the study, runbook, design record and reports under `docs/tabularium-schema-v3/`; add the v3 schema files and the corrected, deprecated v2 files; extend `test_schemas.py` document tests; bump the plugin package version (section 3). Green: existing suite plus new document tests.
2. Library: schema-version-aware adapters, builder `--event-schema {2,3}` default 3, verifier reading 2 and 3, explicit row-level tuple validation in Python with named refusals, v0 `rebuild.py` passing `--event-schema 2`. Green: suite plus the three v0 rebuilds.
3. Parity: `jsonschema` validation of every shipped ledger in `test_schemas.py`, the three rejection fixtures checked by both validators, the reporter, and the `rejection-parity` report (blocks `step:4`).
4. Releases and prose: build and commit the three v1 directories with their prose; supersession notes on the v0 READMEs; plugin README, `SKILL.md`, `adding-an-adapter.md`, `release-policy.md`, `AGENTS.md`; the ledger generation row; Horos boundary rescan; the `shipped-ledgers-validate-v3` and `legacy-v0-verify` reports (block `step:5`).
5. Demonstrate: run the whole demo path above, produce the `suite-wall-time` report (blocks `integration`), record the observations.

## 2. Prior art

### Last two merged pull requests that changed the subject

Subject: `plugins/tabularium/schemas/` and the Python validators (`release_v2.py`, `verifier.py`, `builder.py`). Git history at `1d131b98` shows the last two merged pull requests that changed them:

1. [PR #1183](https://github.com/wildcat-finance/skills/pull/1183), merged 2026-09-04 at `a46f3b508a2740520f4b31a664c9a3e2800cf76a` (commits `bcbeb995`, `d2f3e6fa`). Added the `aave-v4` adapter at version `2.0.0`, deleted `release.py` and canonical schema v1, kept the v2 JSON Schema enums unchanged. This is where the gap opened: the Python validator gained `aave-v4` through `ADAPTERS`, the JSON files did not. Its body records the accepted loss of the writer-`0.1.0` compatibility artefact and that #1139 (a complete Aave research packet) stays open. Neither is in scope here; #1139 remains open by name.
2. [PR #67](https://github.com/wildcat-finance/skills/pull/67), merged 2026-08-17 at `4651b1b2acec809e3f23db945b85222878bae74d`. Introduced canonical event v2, coverage manifest v2, the Euler adapters at `1.0.0`, and the rule that the Euler V2 protocol generation and the Euler V3 source API are separate fields. It carried nothing forward; its five audit rounds are the Euler rounds in the record below.

[PR #70](https://github.com/wildcat-finance/skills/pull/70), merged 2026-08-17 at `25b38af4`, added the two Compound Phase 0 schema files to the same directory and stated that Compound "gets a new schema version rather than changing Euler's published v2 meaning". Carried forward here as assumption 4: Phase 1 takes the next number after v3.

Later merges that touched `plugins/tabularium/` changed only prose and package versions: [PR #1690](https://github.com/wildcat-finance/skills/pull/1690) (2026-09-16, package `0.3.3`) lists `tabularium-schema-enums | duplicate | #1362` in its carryover block, which this run answers; #1638, #1153 and #1330 touched `PROMISE_MACHINE.md`, `README.md`, `DEMONSTRATION.md` and `test_release.py` only.

### Audit records

In-scope audit source: `plugins/tabularium/audit/AUDIT.md` (262 lines, 13 rounds). `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .` ran from the target root and exited 0 with `committed=match` for every pair, including `plugins/tabularium/audit/AUDIT.md` at source SHA-256 `1de310b5df5784d7e623ea9dbda83ae77e02cb1798b3aeedffc5d0c715f8e3a7` and synopsis `2432d6fd11be15a838d62ab067a190314a1a63011a67e106682f700cc3447e6c`. The authoritative source was read in full, not only the synopsis, because the synopsis marks every round `[missing legacy field: audit-schema]`, `[missing legacy field: covered]`, `[missing legacy field: not-checked]` and `[missing legacy field: elenchus-verdict]`; those fields remain unknown. No `audit/rounds/*` file names Tabularium, and the root `audit/AUDIT.md` (14,172 lines) has no Tabularium, Euler or Aave heading. The run's own record will be `audit/rounds/fiat-1362-tabularium-canonical-event-v3-and-coverage.md`, which does not exist yet.

Findings, all `fixed`, `Leads not pursued: none` in every round:

| id | severity | file | status |
| --- | --- | --- | --- |
| E1-R1-01 | medium | `adapters/euler_v2.py` | fixed in `83b3b58f` |
| E1-R1-02 | medium | `adapters/euler_v2.py` | fixed in `83b3b58f` |
| E1-R1-03 | medium | `release_v2.py` | fixed in `83b3b58f` |
| E1-R2-01 | medium | `examples/euler-v1-v0/capture.json`, `release_v2.py` | fixed in `ea8bcead` |
| E1-R3-01 | medium | `adapters/euler_v2.py` | fixed in `2feeb85d` |
| E1-R3-02 | medium | `adapters/euler_v1.py`, `adapters/euler_v2.py` | fixed in `2feeb85d` |
| E1-R4-01 | medium | `adapters/euler_v2.py` | fixed in `e1e3fb71` |
| S2-R1-01 | medium | `core.py`, `builder.py` | fixed in `f6131579` |
| S3-R1-01 | low | `core.py` | fixed in `dbcaf19c` |
| S3-R2-01 | low | `paths.py` | fixed in `307fa255` |
| S3-R2-02 | low | `verifier.py` | fixed in `307fa255` |
| S4-R1-01 | medium | `release.py` (deleted by PR #1183) | fixed in `87cb45b2` |

Rounds Step 1 round 1, Euler round 5, Step 2 round 2, Step 3 round 3 and Step 4 round 2 are clean. No finding is open, so this study carries no inventory block and the runbook derives no assignment. E1-R2-01 matters to step 4: a v1 `capture.json` must keep the exact `request` object including `"id": 1`, changing only `release`.

### Repository inventory at the starting commit

Adapter constants and emitted values (`scripts/tabularium_lib/adapters/*.py:19-26`, `release_v2.py:18-22`, `MAPPINGS` tables):

| adapter module | `venue` = `provenance.adapter` = `protocol_generation` | `adapter_version` | `source_api` | `evidence_class` | mapping rules |
| --- | --- | --- | --- | --- | --- |
| `aave_v4.py` | `aave-v4` | `2.0.0` | `ethereum-json-rpc` | `native-log` | `aave-v4.borrow.v2`, `aave-v4.repay.v2` |
| `euler_v1.py` | `euler-v1` | `1.0.0` | `ethereum-json-rpc` | `hosted-rpc-reported-log-scope` | `euler-v1.borrow.v1`, `euler-v1.repay.v1`, `euler-v1.liquidation.v1` |
| `euler_v2.py` | `euler-v2` | `1.0.0` | `euler-v3` | `hosted-indexer-reported-query-scope` | `euler-v2.borrow.v1`, `euler-v2.repay.v1`, `euler-v2.liquidation.v1`, `euler-v2.debt-socialized.v1`, `euler-v2.pull-debt.v1`, `euler-v2.interest-accrued.v1` |

Every emitted row sets `venue`, `provenance.adapter` and `provenance.protocol_generation` from the same `ADAPTER` or `PROTOCOL_GENERATION` constant (`aave_v4.py:150-187`, `euler_v1.py:88-116`, `euler_v2.py:129-157`); `chain` is always `ethereum-mainnet`; `schema_version` is the literal `2` in each adapter. Shipped ledgers: `aave-v4-v0` 500 rows, `euler-v1-v0` 1 row, `euler-v2-v0` 2 rows; each `coverage.json` has `schema_version` 2 and `versions.event_schema` 2; each `capture.json` has its own `schema_version` 2, which is the capture manifest format and is not changed by this topic. `scripts/tabularium_lib/__init__.py:3-4` still declares `EVENT_SCHEMA_VERSION = 1` and `ADAPTER_VERSION = "1.0.0"`; nothing imports them. Existing tests already cover Python wrong-version refusal: `tests/test_verify.py:127-146` set a row or manifest version to 3 and expect refusal; both flip meaning under v3 and must move to 4.

Where validation runs today: JSON Schema, nowhere; Python, `builder.py:79-97` (`validate_capture_v2`, `validate_manifest_v2`) and `verifier.py:75-84` plus the per-row checks at `verifier.py:103-108` that require `schema_version == 2` and `provenance.adapter == manifest adapter`, followed by a byte-for-byte rebuild. The CLI `tabularium.py:27-32` restricts `--adapter` to the three names. The suite is declared in `tests/check-map-v1.json` as `python3 -m unittest discover -s plugins/tabularium/tests -t plugins/tabularium`, scope `tabularium` in `.github/workflows/plugins.yml`.

Prose that names schema v2 and must move with the code: `plugins/tabularium/README.md:105-106` (schema links) and `:113` ("134 tests", already stale against 137), `skills/tabularium/SKILL.md`, `docs/adding-an-adapter.md:30-34`, `docs/release-policy.md`, `examples/aave-v4-v0/README.md:5`, the three `DATA-DICTIONARY.md` files, `docs/euler-preservation-study.md:19` and `docs/euler-preservation-runbook.md:25` (historical, stay), `docs/compound-v3-preservation.md:225-228` (already anticipates a later number).

### Organisation and outside

Alexandria ships its own `alexandria-tabularium-view/v1` derivation (`plugins/alexandria/scripts/alexandria_lib/derivation.py:27`) and a `SUPPORTED_VENUES = {"aave-v4", "clearpool"}` set in `probitas.py:8`; neither reads Tabularium's JSON Schema files. Lazarus validates with `jsonschema.Draft202012Validator` at `plugins/lazarus/scripts/lazarus_lib/schemas.py:11-12`; Ariadne and the root `tests/test_harness_manifest.py` use it in tests with a skip when absent. Outside: JSON Schema draft 2020-12 (the `$schema` both files declare) and the `jsonschema` PyPI package 4.25.1.

## 3. Constraints and non-goals

Starting ref `1d131b98a78c888b571f302e5b4c899aa2e47caf`. Toolchain: Python 3.14.6 from `.python-version`, stdlib `unittest`, `jsonschema` 4.25.1 for tests only, Git. Work only inside the run worktree; no `git stash`; `TMPDIR` under `/private/tmp` or the worktree.

Versioning findings, stated as asked:

- Package version. `scripts/plugin_release.py`, run as a required gate by `.github/workflows/repo.yml:56`, requires a newer package version for every plugin whose Git tree changed. This forces `plugins/tabularium/.claude-plugin/plugin.json` and `.codex-plugin/plugin.json` from `0.3.3` to `0.3.4` in step 1, propagated to both marketplace listings.
- Skill ledger. `plugins/hexaemeron/skills/VERSIONING.md` says the generation counter increments "for a meaningful change to scripts, checks, ordering, decisions, or other behaviour that is not a completed frontier advance". A new schema version, a changed builder default and a widened verifier are such a change, so this study plans one generation row `tabularium-v0.4.0` in `plugins/tabularium/skills/tabularium/EVOLUTION.md` in step 4, retaining frontier revision `compound-v3-phase-1`, frontier SHA-256 `c3aac484a13f97742a45f07a4d3ca42cec29e4e4a9666cfd2701d825e4752d6e`, the current frontier text and the held Next Fiat job byte for byte, and moving `SKILL.md` `metadata.version` from `0.3.0` to `0.4.0` as `tests/test_evolution_contract.py` requires. No mechanical test forces the row; the contract text does. This is not a frontier advance and the Next Fiat job is not edited.
- Demonstration ledger. `skills/tabularium/DEMONSTRATION.md` pins `aave-v4-v0/events.jsonl` at `490d3f63…`; the v0 bytes do not change, so that ledger is untouched.

Non-goals:

- No Compound Phase 1 fields, no new venue, no new adapter, no Wildcat mapping. A future adapter registers its tuple in the table and in v3 by an ordinary change; this run admits no value nobody emits.
- No unrestricted strings anywhere in v3.
- No change to the capture manifest format (`capture.json` `schema_version` 2 stays).
- No Solidity audit; no live capture; no Miskatonic or Alexandria code change.
- No rewrite of any v0 release file; documentation notes only.
- No cleanup of the unused constants at `tabularium_lib/__init__.py:3-4` beyond removing them if the dead-code check does not object; deferred if it does.

Boundaries the build must state:

- Always: the Tabularium suite and the root suite before every commit; the Imprimatur lint on every shipped Markdown; the three v0 rebuilds after any adapter edit.
- Ask first: adding a runtime dependency (none planned); changing the capture manifest format; touching CI; editing a v0 release file; changing the held frontier text.
- Never: rewrite published `source.json`, `capture.json`, `events.jsonl` or `coverage.json` bytes under a v0 directory; commit credentials; delete a failing test; claim a command ran when it did not.

## 4. Design options

The design record `.hexaemeron/design-evidence.json` (SHA-256 `512a0b64fd17b5e46768e250dca7c9ace5f6c69febf4fc800c326313187cb595`) holds four candidates, ten criteria and forty cells; `.hexaemeron/design-probe.py` produced the twenty-four selection reports under `.hexaemeron/reports/` from the tree at `1d131b98` and one closed declaration table. `design_evidence.py --transition design-lock` exited 0 with `clean`; selection rule `unique-frontier`; survivor `superseding-releases`.

Closed adapter tuple table that every candidate's forward schema encodes (measured by the probe from the adapter modules; 506 documents checked, all admitted):

| `venue` | `provenance.adapter` | `adapter_version` | `protocol_generation` | `source_api` | `evidence_class` |
| --- | --- | --- | --- | --- | --- |
| `aave-v4` | `aave-v4` | `2.0.0` | `aave-v4` | `ethereum-json-rpc` | `native-log` |
| `euler-v1` | `euler-v1` | `1.0.0` | `euler-v1` | `ethereum-json-rpc` | `hosted-rpc-reported-log-scope` |
| `euler-v2` | `euler-v2` | `1.0.0` | `euler-v2` | `euler-v3` | `hosted-indexer-reported-query-scope` |

Candidates and the trade each makes:

1. `superseding-releases` (selected). v3 schemas carry the enums above plus a `oneOf` per adapter binding the five provenance fields and the `mapping_rule` enum, so `aave-v4` with `1.0.0` or `euler-v2` with `ethereum-json-rpc` is refused by the JSON Schema exactly as the Python validator refuses it. `build` writes 3 by default and 2 only under `--event-schema 2`; `verify` reads 2 and 3. Three v1 release directories supersede the v0 ones from identical source bytes; the v2 files are corrected and marked deprecated. Trade: 1,710,643 bytes of duplicated release files (1,695,929 of them the Aave source and ledger) against a tree that honours the immutability policy, keeps PR #1183's published digests and the demonstration ledger pin, and ships v3 examples that consumers can validate.
2. `in-place-migration`. Rewrite the v0 directories to 3 and drop v2. Zero added bytes. Fails `published-release-bytes-unchanged`: migrating any row changes the canonical digest, shown by the probe; fails `legacy-v2-read-path`. Rejected mechanically.
3. `repair-v2-only`. Correct the v2 enums in place, add parity tests, cut nothing. Zero added bytes, smallest diff. Fails `v3-schema-files-declared` and `shipped-v3-ledgers` (0 of 3): the issue's done condition names v3 files and v2 marked superseded. Rejected mechanically.
4. `v3-without-shipped-examples`. Cut v3 and the read path but ship no v3 release; v3 is exercised only from fixtures in temporary builds. Zero added bytes. Fails `shipped-v3-ledgers` (0 of 3). Rejected mechanically.

Selection criteria (stage `selection`, all block `design-lock`): `emitted-values-admitted` (correctness gate, all four pass), `shipped-v3-ledgers` (correctness gate, at least 3), `published-release-bytes-unchanged` (compatibility gate), `v3-schema-files-declared` (compatibility gate), `legacy-v2-read-path` (recovery gate), `added-example-bytes` (space metric, minimise; 1,710,643 for the survivor, 0 for the three eliminated candidates). Conformance criteria, pending for every candidate with the resolver `python3 plugins/tabularium/tests/prove_schema_v3.py --candidate <id> --criterion <id> --report <abs>/.hexaemeron/reports/<candidate>-<criterion>.json`: `rejection-parity` (correctness, blocks `step:4`), `shipped-ledgers-validate-v3` (correctness, blocks `step:5`), `legacy-v0-verify` (recovery, blocks `step:5`), `suite-wall-time` (time, at most 60,000 ms, blocks `integration`). Only the survivor's resolvers are expected to run.

Design details the runbook inherits:

- v3 event schema: `additionalProperties: false` everywhere as in v2; `schema_version` `const 3`; `venue`, `provenance.adapter`, `provenance.protocol_generation` `enum` of the three names; `adapter_version` `enum ["1.0.0", "2.0.0"]`; `source_api` `enum ["ethereum-json-rpc", "euler-v3"]`; `mapping_rule` `enum` of the eleven rules; a top-level `oneOf` of three branches, each pinning `venue` and the five provenance fields to one tuple row. Everything else identical to v2.
- v3 coverage schema: `schema_version` `const 3`, `versions.event_schema` `const 3`, `source.protocol_generation`, `source.source_api`, `source.evidence_class`, `versions.adapter.name` and `versions.adapter.version` as enums, with a `oneOf` binding `source.protocol_generation`, `source.source_api`, `source.evidence_class` and `versions.adapter` to one row. `known_gaps` keeps `minItems 4` (shipped counts 6, 4, 5).
- v2 files: keep `$id`, add `"deprecated": true` and a `description` naming v3 and the supersession date, widen the four enums and the two `const` versions to the table so the v0 releases validate; nothing narrower than the v2 Python validator admitted.
- Python: one `SUPPORTED_EVENT_SCHEMAS = frozenset({2, 3})`, `CURRENT_EVENT_SCHEMA = 3`; `map_source(source, capture, schema_version)` in each adapter; `make_manifest` and `validate_manifest` take the version; a row-level `validate_event_row(row, adapter_module, schema_version)` that refuses an unknown value, a wrong version or a malformed provenance with a `TabulariumError` naming the field, run by `verify` before the byte rebuild so the refusal names the cause rather than "canonical bytes do not match"; `verify` requires manifest `schema_version == versions.event_schema` and every row to match it.
- v1 releases: identifiers `aave-v4-mainnet-credit-window-v1`, `euler-v1-borrow-block-14531589-v1`, `euler-v2-owner-activity-1786933919-v1`; `source.json` byte-identical to v0 (digests `1d88fdb5…`, `1241cbed…`, `10f5c8e8…`); `capture.json` identical except `release`; `coverage.json` and `events.jsonl` rebuilt at 3. Each `README.md` names the superseded v0 release and states that only `schema_version` and the two version fields differ.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | superseding-releases
record | plugins/tabularium/skills/tabularium/EVOLUTION.md
```

## 5. Risk register

Concerns for Warden. Python: untrusted release files, filesystem writes, fixtures, and the test-only dependency. Ids are stable for the run.

```risk-register
tuple-drift | the adapter constants and the v3 schema enums | a test derives the tuple table from the adapter modules and fails when the JSON enums, the oneOf branches or the Python tuple check disagree
version-mixing | verify across coverage schema_version, versions.event_schema and every row | a manifest at 3 with a row at 2, or the reverse, is refused before the byte rebuild
legacy-write | the build default and --event-schema 2 | build without the flag never writes 2; the flag is documented as reproduction only and the three v0 rebuild demos are the only callers in the tree
v0-immutability | the twelve committed v0 release files | their digests at 1d131b98 are asserted by a test and by the legacy-v0-verify report; no step edits them
source-reuse | v1 source.json and capture.json | source bytes equal the v0 digest; capture differs only in release and keeps request id 1 (E1-R2-01)
schema-parity | the jsonschema path and the Python row validator | the three rejection fixtures are refused by both, with the field named, and every shipped document passes both
skip-invisibility | tests that need jsonschema | parity tests skip only with a named reason; the reporter exits non-zero without jsonschema; CI installs the lock
partial-write | building the v1 directories | write_bytes_atomic is used; a killed build leaves no half-written events.jsonl or coverage.json
path-confinement | rebuild.py temporary directories and reporter output paths | fixed argv, no shell, outputs below the declared directory, symlinks refused as today
prose-drift | README, SKILL.md, dictionaries, adapter guide, release policy, AGENTS.md | every v2 mention is updated in step 4 and the Imprimatur lint passes on each file
```

## 6. Glossary seeds

- adapter tuple: the closed row of `venue`, `adapter`, `adapter_version`, `protocol_generation`, `source_api`, `evidence_class` and mapping rules one adapter module emits.
- forward schema: the JSON Schema a newly built release is validated against; v3 after this run.
- legacy read path: `verify` accepting a `schema_version` 2 release without being able to build one by default.
- superseding release: a new directory with a new identifier, identical source bytes and a newer schema, beside the release it supersedes.
- parity: the JSON Schema and the Python validator accept and refuse the same documents.
- reporter: `plugins/tabularium/tests/prove_schema_v3.py`, which writes `protasis-design-report/v1` objects for the conformance criteria.

## 7. Sources

Repository files at `1d131b98a78c888b571f302e5b4c899aa2e47caf`:

- [canonical-event-v2.json](https://github.com/wildcat-finance/skills/blob/1d131b98a78c888b571f302e5b4c899aa2e47caf/plugins/tabularium/schemas/canonical-event-v2.json), [coverage-manifest-v2.json](https://github.com/wildcat-finance/skills/blob/1d131b98a78c888b571f302e5b4c899aa2e47caf/plugins/tabularium/schemas/coverage-manifest-v2.json)
- [release_v2.py](https://github.com/wildcat-finance/skills/blob/1d131b98a78c888b571f302e5b4c899aa2e47caf/plugins/tabularium/scripts/tabularium_lib/release_v2.py), [verifier.py](https://github.com/wildcat-finance/skills/blob/1d131b98a78c888b571f302e5b4c899aa2e47caf/plugins/tabularium/scripts/tabularium_lib/verifier.py), [builder.py](https://github.com/wildcat-finance/skills/blob/1d131b98a78c888b571f302e5b4c899aa2e47caf/plugins/tabularium/scripts/tabularium_lib/builder.py), [tabularium.py](https://github.com/wildcat-finance/skills/blob/1d131b98a78c888b571f302e5b4c899aa2e47caf/plugins/tabularium/scripts/tabularium.py)
- [aave_v4.py](https://github.com/wildcat-finance/skills/blob/1d131b98a78c888b571f302e5b4c899aa2e47caf/plugins/tabularium/scripts/tabularium_lib/adapters/aave_v4.py), [euler_v1.py](https://github.com/wildcat-finance/skills/blob/1d131b98a78c888b571f302e5b4c899aa2e47caf/plugins/tabularium/scripts/tabularium_lib/adapters/euler_v1.py), [euler_v2.py](https://github.com/wildcat-finance/skills/blob/1d131b98a78c888b571f302e5b4c899aa2e47caf/plugins/tabularium/scripts/tabularium_lib/adapters/euler_v2.py)
- [test_schemas.py](https://github.com/wildcat-finance/skills/blob/1d131b98a78c888b571f302e5b4c899aa2e47caf/plugins/tabularium/tests/test_schemas.py), [test_verify.py](https://github.com/wildcat-finance/skills/blob/1d131b98a78c888b571f302e5b4c899aa2e47caf/plugins/tabularium/tests/test_verify.py)
- [aave-v4-v0/coverage.json](https://github.com/wildcat-finance/skills/blob/1d131b98a78c888b571f302e5b4c899aa2e47caf/plugins/tabularium/examples/aave-v4-v0/coverage.json), [euler-v1-v0/coverage.json](https://github.com/wildcat-finance/skills/blob/1d131b98a78c888b571f302e5b4c899aa2e47caf/plugins/tabularium/examples/euler-v1-v0/coverage.json), [euler-v2-v0/coverage.json](https://github.com/wildcat-finance/skills/blob/1d131b98a78c888b571f302e5b4c899aa2e47caf/plugins/tabularium/examples/euler-v2-v0/coverage.json), [aave-v4-v0/rebuild.py](https://github.com/wildcat-finance/skills/blob/1d131b98a78c888b571f302e5b4c899aa2e47caf/plugins/tabularium/examples/aave-v4-v0/rebuild.py)
- [release-policy.md](https://github.com/wildcat-finance/skills/blob/1d131b98a78c888b571f302e5b4c899aa2e47caf/plugins/tabularium/docs/release-policy.md), [adding-an-adapter.md](https://github.com/wildcat-finance/skills/blob/1d131b98a78c888b571f302e5b4c899aa2e47caf/plugins/tabularium/docs/adding-an-adapter.md), [compound-v3-preservation.md](https://github.com/wildcat-finance/skills/blob/1d131b98a78c888b571f302e5b4c899aa2e47caf/plugins/tabularium/docs/compound-v3-preservation.md)
- [SKILL.md](https://github.com/wildcat-finance/skills/blob/1d131b98a78c888b571f302e5b4c899aa2e47caf/plugins/tabularium/skills/tabularium/SKILL.md), [EVOLUTION.md](https://github.com/wildcat-finance/skills/blob/1d131b98a78c888b571f302e5b4c899aa2e47caf/plugins/tabularium/skills/tabularium/EVOLUTION.md), [DEMONSTRATION.md](https://github.com/wildcat-finance/skills/blob/1d131b98a78c888b571f302e5b4c899aa2e47caf/plugins/tabularium/skills/tabularium/DEMONSTRATION.md), [AUDIT.md](https://github.com/wildcat-finance/skills/blob/1d131b98a78c888b571f302e5b4c899aa2e47caf/plugins/tabularium/audit/AUDIT.md), [README.md](https://github.com/wildcat-finance/skills/blob/1d131b98a78c888b571f302e5b4c899aa2e47caf/plugins/tabularium/README.md), [plugin.json](https://github.com/wildcat-finance/skills/blob/1d131b98a78c888b571f302e5b4c899aa2e47caf/plugins/tabularium/.claude-plugin/plugin.json)
- [VERSIONING.md](https://github.com/wildcat-finance/skills/blob/1d131b98a78c888b571f302e5b4c899aa2e47caf/plugins/hexaemeron/skills/VERSIONING.md), [plugin_release.py](https://github.com/wildcat-finance/skills/blob/1d131b98a78c888b571f302e5b4c899aa2e47caf/scripts/plugin_release.py), [repo.yml](https://github.com/wildcat-finance/skills/blob/1d131b98a78c888b571f302e5b4c899aa2e47caf/.github/workflows/repo.yml), [plugins.yml](https://github.com/wildcat-finance/skills/blob/1d131b98a78c888b571f302e5b4c899aa2e47caf/.github/workflows/plugins.yml), [check-map-v1.json](https://github.com/wildcat-finance/skills/blob/1d131b98a78c888b571f302e5b4c899aa2e47caf/tests/check-map-v1.json), [test_evolution_contract.py](https://github.com/wildcat-finance/skills/blob/1d131b98a78c888b571f302e5b4c899aa2e47caf/tests/test_evolution_contract.py)
- [lazarus requirements.lock](https://github.com/wildcat-finance/skills/blob/1d131b98a78c888b571f302e5b4c899aa2e47caf/plugins/lazarus/requirements.lock), [ariadne test_schema_agreement.py](https://github.com/wildcat-finance/skills/blob/1d131b98a78c888b571f302e5b4c899aa2e47caf/plugins/ariadne/tests/test_schema_agreement.py), [alexandria probitas.py](https://github.com/wildcat-finance/skills/blob/1d131b98a78c888b571f302e5b4c899aa2e47caf/plugins/alexandria/scripts/alexandria_lib/probitas.py)

Issues and pull requests: [#1362](https://github.com/wildcat-finance/skills/issues/1362) and its consumer-handoff comment of 2026-09-13; [PR #1183](https://github.com/wildcat-finance/skills/pull/1183); [PR #67](https://github.com/wildcat-finance/skills/pull/67); [PR #70](https://github.com/wildcat-finance/skills/pull/70); [PR #1690](https://github.com/wildcat-finance/skills/pull/1690).

Outside: [JSON Schema draft 2020-12](https://json-schema.org/draft/2020-12/schema); [jsonschema 4.25.1 on PyPI](https://pypi.org/project/jsonschema/4.25.1/).

Run artefacts: `.hexaemeron/design-evidence.json`, `.hexaemeron/design-probe.py`, `.hexaemeron/reports/selection-observations.json` and the twenty-four report files beside it.

## 8. On-call questions and signals

This is a command-line tool with no unattended run, so no alert or metric is proposed; the observation contract in `plugins/hexaemeron/skills/ephoros/SKILL.md` applies to what the commands print. Questions someone will ask from a failed CI shard or a downstream rejection:

1. Which schema version did `verify` accept? Step 2 adds the version to the success line: `verified <release> offline: <n> event(s), schema 3, sha256 <digest>`.
2. Was a refusal a version mismatch, an unknown value or a malformed provenance? Step 2's row validator names the row index and field in the `TabulariumError` text that `tabularium.py` prints on stderr at exit 1.
3. Did the parity tests run or skip? The unittest summary counts skips; step 3 gives every skip the reason `jsonschema is not installed`, and the reporter exits 1 with the same text so a design gate can never pass on a skip.
4. Which release supersedes which? Each v1 README names its v0 release; each v0 README names its v1 successor; `verify` prints the release identifier.

## 9. Trust boundaries and controls

Boundaries per capability, controls per `plugins/hexaemeron/skills/phylax/SKILL.md`:

| Capability | Boundary | Control |
| --- | --- | --- |
| Read a release from disk | Untrusted JSON and JSONL under a declared directory | Existing `loads_json` refuses duplicate keys and non-finite numbers; `resolve_artifact_path` confines paths; the new row validator refuses before the rebuild |
| Validate against JSON Schema | Test-only import of `jsonschema` | No runtime import; version pinned by the Lazarus lock CI installs; schema documents are `check_schema`-validated before use |
| Build a v1 release | Writes into a new directory | `write_bytes_atomic`, alias refusal, output never overlaps a v0 file |
| Run rebuild demos and the reporter | Subprocess with fixed argv | No shell, `sys.executable`, temporary directory, outputs below the declared report directory |
| Read fixtures | Committed hostile rows | Fixtures are data, never executed; each names its expected refusal |
| Credentials and network | None | No endpoint is contacted; `captured_at` and `endpoint` are preserved bytes |

Widening: none. The set of admitted values is smaller after the run than the strings v2 admitted for `mapping_rule` and `evidence_class`.

## 10. Performance budget

Budget: the Tabularium suite completes in at most 60,000 ms, measured by `python3 plugins/tabularium/tests/prove_schema_v3.py --candidate superseding-releases --criterion suite-wall-time --report <abs>/.hexaemeron/reports/superseding-releases-suite-wall-time.json`, which times `python3 -m unittest discover -s plugins/tabularium/tests -t plugins/tabularium` in a subprocess and records milliseconds. Baseline 3,650 ms for 137 tests; the JSON Schema pass over 500 rows costs 93 ms and `verify` of the Aave release 100 ms, so the added cost is expected under 2,000 ms including the new v1 rebuilds. No other budget: a schema is not a hot path. Metron's before-and-after rule in `plugins/hexaemeron/skills/metron/SKILL.md` applies only if implementation claims a speed change, which none does.

## 11. Fail-closed posture and Elenchus guard convention

What stops the run: `verify` refuses a coverage manifest whose `schema_version` is not 2 or 3, whose `versions.event_schema` differs from it, or any row whose `schema_version` differs from the manifest; it refuses a row whose tuple is not in the table or whose provenance lacks a field, before any byte comparison; `build` refuses `--event-schema` outside `{2, 3}` and never emits 2 without the flag; the reporter exits non-zero on a missing `jsonschema`, a failing document or a fixture that either validator accepts. A skipped parity test is not a pass for any design gate.

Guard convention per `plugins/hexaemeron/skills/elenchus/SKILL.md`: every refusal has one test named `test_<cause>_refused` in the Tabularium suite that fails on the parent tree and passes with the fix; a fix to a rejection case is claimed only through the runbook's exact Elenchus command, `python3 plugins/tabularium/tests/prove_schema_v3.py --case <finding-id> --report {report}` with report format `unittest-json-v1`, which the runbook binds per step. No known failure is open, so no inventory assignment exists.

## 12. Expensive-to-reverse decisions and homes

1. A schema version change is delivered as superseding release directories, never in place, and the superseded version stays readable. Home: `plugins/tabularium/docs/release-policy.md`, which already holds the immutability rule and gains the schema-version clause in step 4; the ledger generation row in `plugins/tabularium/skills/tabularium/EVOLUTION.md` names it, which is the design-bridge record above. Not a cross-cutting decision, so no new record under `docs/decisions/` and no ADR reference is invented here.
2. The admitted vocabulary is the closed adapter tuple table, derived from the adapter modules and mirrored in the JSON Schema; a new value enters by registering an adapter, not by widening a string. Home: `plugins/tabularium/docs/adding-an-adapter.md` step 3 and the v3 schema files themselves.
3. `build` writes the current version only; `--event-schema 2` exists to reproduce a published release. Home: `plugins/tabularium/skills/tabularium/SKILL.md` build section and `release-policy.md`.
4. Compound Phase 1 takes the next number after 3. Home: already written at `plugins/tabularium/docs/compound-v3-preservation.md:225-228`; no edit.

Per `plugins/hexaemeron/skills/hypomnema/SKILL.md`, comments in the new code explain why v2 stays readable and why the flag exists, not what the code does.
