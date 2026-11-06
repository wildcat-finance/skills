# Study: emitter-versus-declaration check at a pinned commit

Task: [#1361](https://github.com/wildcat-finance/skills/issues/1361),
`kickoff/solidity-auditor-11`. Surveyor wrote this study under Protasis for
Fiat run 1361.

Assuming, unless corrected:

1. The target repository for the delivery is `wildcat-finance/skills`. The
   audited source is `wildcat-finance/v2-protocol`, read at a pinned commit and
   never copied into this repository.
2. The scoped target is the registry row `wildcat-v2-ethereum-mainnet` in
   `docs/kickoff/1359/targets.md`, the row #1361 is named against. The
   prerequisite [#1482](https://github.com/wildcat-finance/skills/issues/1482)
   closed on 2026-09-13 and its epoch follow-up
   [#1590](https://github.com/wildcat-finance/skills/issues/1590) closed on
   2026-09-18, so the input record exists.
3. "The target's assembly emitter library" means the two files that build logs
   by hand in assembly: `src/libraries/MarketEvents.sol` and
   `src/spherex/SphereXProtectedEvents.sol`. Contracts that emit through
   Solidity `emit` are outside the check, because the compiler derives their
   logs from the declaration.
4. The check is static. It reads source text and recorded compiler output. It
   runs no target code and makes no claim about runtime fidelity, bytecode
   identity or capture completeness.
5. The interpreter is the one in `.python-version`, 3.14.6, with the standard
   library only. No dependency is added.
6. Building the table needs a local `v2-protocol` clone or HTTPS access to
   `raw.githubusercontent.com`. The root suite runs offline and does not need
   either.

## 1. Problem statement

An assembly emitter writes topic0, the topic count and the data region by hand.
If any of those drifts from the `event` declaration a decoder uses, every
decode still succeeds and returns wrong values. #1361 asks for the check to be
recomputed, before any audit of the emitter library, against the exact source
whose logs a capture decodes, with the result committed beside the audit
scope.

Who uses it: the Solidity Auditor delivery owner, who needs the pinned static
map before reviewing the emitters; Tabularium (#1378), which consumes the
reviewed event semantics; and the Miskatonic decoder review named in the
[issue comment](https://github.com/wildcat-finance/skills/issues/1361), which
checks that every relied-on signature, indexed position and data layout names
its source epoch.

A working prototype here is:

- `docs/kickoff/1361/emitters.json`: one row per pair of an assembly emitter
  and a same-named `event` declaration at the pin. Each row carries the
  qualified declaration, the declaration and emitter locations, the canonical
  signature, the computed topic0, the emitter's topic0 literal, the anonymous
  flag, the `logN` arity, the indexed count and order, the data encoding, the
  compiler-ABI cross-check, the deployed contracts that reach the emitter, any
  mismatch classes and any notes. Separate lists hold the mismatches, the
  unreviewed emitters and the declarations with no assembly emitter.
- `docs/kickoff/1361/emitters.md`: the same table for a reader, rendered from
  the JSON, with the source binding and the limits.
- `scripts/emitter_declarations.py`: `build` regenerates the table from a clone
  or a digest-verified HTTPS fetch; `check` regenerates it and exits 1 on any
  byte difference from the committed file.
- `tests/test_emitter_declarations.py` in the root suite.

The demo path, run in the last step:

1. `python3 scripts/emitter_declarations.py check --from-git <clone> --table docs/kickoff/1361/emitters.json`
   exits 0 at `f5a26146987926f4811b72a795d662813dedfe85`.
2. The same command with `--ref bea503c2736d47de7fd34130c64f10783dc35b39`
   (the unreleased `release/v2.5` candidate recorded in
   `docs/kickoff/1372/eventdecision.md`) exits 1 and names the source digests
   that moved. That is the rejection case: branch drift is told apart from a
   finding.
3. `python3 -m unittest tests.test_emitter_declarations` passes offline, and
   each seeded specimen class fails for its named reason.

The design probe already recorded, at the pin, 27 emitters and 38 declaration
rows with no mismatch class. That is study evidence from a prototype. The
committed table re-establishes it; this study does not.

## 2. Prior art

**Input record.** `docs/kickoff/1359/targets.md`, section
`wildcat-v2-ethereum-mainnet`, pins the emitter source at
`wildcat-finance/v2-protocol@f5a26146987926f4811b72a795d662813dedfe85`, from
[PR #1460](https://github.com/wildcat-finance/skills/pull/1460). Its "Estate
map, 2026-09-18" states that every emitter, interface and hooks-base path has
the same blob at the pin, at tag v2.0.0
(`a70f297fbd1b1ab597e0e9a3458a2d13a34b4657`), at the deploy-era commit
`8dc8e449`, at v2.1.0 and at the plasma-line commits `5838b2f3` and
`e1f77540`. It records 22 `logN` sites in `MarketEvents.sol` (9 `log1`, 9
`log2`, 4 `log3`) and 5 `log1` sites in `SphereXProtectedEvents.sol`.

**Source-to-deployment relationship, resolved here.** One source epoch covers
every deployed V2 contract that runs an assembly emitter. Evidence gathered for
this study from a clone of `v2-protocol`:

- The eight files the check reads have one blob each across `f5a26146`,
  `a70f297f`, `8dc8e449`, `c7be4039` (v2.1.0), `5838b2f3`, `e1f77540` and the
  `mainnet` head `26242045`: `MarketEvents.sol` `80d93961`,
  `SphereXProtectedEvents.sol` `d5415f1c`, `IMarketEventsAndErrors.sol`
  `dd6d3838`, `SphereXConfig.sol` `1656e5bc`, `IERC20.sol` `9ee5c3ae`,
  `SphereXProtectedRegisteredBase.sol` `fec029bf`,
  `ISphereXProtectedRegisteredBase.sol` `8e9078e8`,
  `IWildcatArchController.sol` `2ee945fb`.
- Two deployed builds compile the emitters. The WildcatMarket verification
  input (SHA-256
  `f9a92fe4072d8f44406448377730c4b38b908571fa3db6b8ff3a81719e801346`) carries
  `MarketEvents.sol`, `SphereXProtectedEvents.sol` and
  `SphereXProtectedRegisteredBase.sol` byte-equal to the pin. Its call sites
  are in the five `src/market/*.sol` files. The HooksFactory input (SHA-256
  `63dabbfdd5b7c140c314a0892baa639e217b0a15b20a51e604ecd2bd10ad4309`) carries
  `SphereXProtectedEvents.sol` and `SphereXProtectedRegisteredBase.sol`, also
  byte-equal. The registry records that both inputs reproduce the deployed
  bytecode. This study relies on that record and does not repeat it.
- The compiler ABI recorded beside those inputs, `output.json` at the tag
  (SHA-256
  `d1a748bff6dec5a52571e432288d967fe40b9787b98b223fe68a6b812d4b8281` for
  WildcatMarket,
  `fea058a27a5bea99ceb4032ad711b285247ade23ff56efca2361114e1e256598` for
  HooksFactory), lists 25 and 7 events. `AccountSanctioned` is declared and
  in the market ABI, but no `src/` file emits it; the withdrawn #1354 audit
  record says the same.
- Correction to the input record: the market and factory take their SphereX
  event declarations from `SphereXProtectedRegisteredBase.sol`, not from
  `SphereXConfig.sol`. `SphereXConfig.sol` enters only the MarketLens build
  and the V2 tree's `WildcatArchController.sol`. The deployed arch controller
  is built from the V1 repository at `da74452a`, so `emit_SpherexAdminTransferStarted`,
  `emit_SpherexAdminTransferCompleted` and `emit_NewAllowedSenderOnchain` are
  reached from no deployed V2 contract. They still get rows, marked unreached.

The table therefore names `f5a26146` as its commit and binds each scanned file
to the two verification inputs by SHA-256. That is the "exact commit whose
logs a capture decodes" for every V2 market and the factory.

**Last two merged pull requests on the subject.**
[PR #1601](https://github.com/wildcat-finance/skills/pull/1601) shipped the
Fizz differential harness at `plugins/hexaemeron/harness/` for #1354. Its
carryover block has three rows. `hermes-cmp10-acceptance` was filed as #1597,
which is now closed; nothing here depends on it. `upstream-uint32-narrowing`
is carried into this study as a row note on
`SanctionedAccountAssetsQueuedForWithdrawal`, where the emitter takes `uint32
expiry` and the declaration says `uint256 expiry`. It is recorded, not graded,
and changing it stays the protocol maintainer's decision.
`elenchus-overlay-new-source-import` does not apply: this delivery adds no
Solidity. [PR #1735](https://github.com/wildcat-finance/skills/pull/1735)
completed the estate map and the emitter-pin binding used above. Its body
carries no carryover block. The later registry PRs, #1736, #1750 and #1751,
touch the fee recipient and the V1 row, not the emitter paths.

**Harness prior art.** `plugins/hexaemeron/harness/fetch_protocol.py` and its
`PROVENANCE.json` already hold 11 `v2-protocol` files by identity at the pin
and fetch them over HTTPS or from a clone with digest verification.
`docs/decisions/ADR-095-deliver-the-emitter-fidelity-suite-as-a-first-party-harness.md`
records that target source is held by identity only. This delivery reuses
both decisions. It does not reuse the harness itself: the harness is a forge
root and a runtime differential, and this issue asks for a static record the
root suite can hold.

**Keccak.** `plugins/tabularium/scripts/tabularium_lib/keccak.py` is a
stdlib Keccak-256. The generator carries its own copy under root scope, since
a root script importing a plugin's private library couples two release lines,
and pins it with test vectors.

**Audit records.** `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`
ran from the target root and exited 0, with every source reporting
`committed=match`. Sources in scope and how each was read:

- `audit/AUDIT.md`, through its verified `audit/AUDIT_SYNOPSIS.md`, grepped
  for `topic0`, `MarketEvents` and `emitter`. The hits concern report
  emitters in the Fiat tooling, not event emitters. Nothing carries forward.
- `audit/rounds/fiat-1731-venue-agnostic-interval-capture-for-both-wi.md`,
  through its verified synopsis, grepped the same way. It is the capture run
  for both Wildcat estates. No finding concerns event signatures.
- `plugins/hexaemeron/audit/AUDIT.md` and `plugins/tabularium/audit/AUDIT.md`,
  through their verified synopses. Grepping for `harness`, `emitter-fidelity`,
  `topic0` and `Wildcat V2` found nothing.
- The withdrawn #1354 run's record,
  `audit/rounds/fiat-1354-fizz-4-emitter-fidelity-differential-suite.md`, is
  not on `main` and has no synopsis. Its branch
  `fiat/1354-fizz-4-emitter-fidelity-differential-suite` no longer exists on
  the remote. The source was read directly, grepped for finding rows and
  `Leads not pursued`, at the step-4 audit head
  `073fcc168850c068ff52609e2bb06fe77c2deaac` (140 lines, SHA-256
  `b473f54429fe09a5fa6b4dfc3a7f091a5854bb78aa242d72968d7aaa163c3154`). Findings
  S1-R1-01 through S4-R1-03 all concern that run's own documents, harness
  comparator and PR bodies, and each is marked fixed there. Two leads carry
  forward as content. The step-3 lead says the three narrow-typed call sites
  are `WildcatMarketBase.sol:602`, `WildcatMarketWithdrawals.sol:264` and
  `WildcatMarket.sol:314`, and that only the last can pass an uncleaned
  `uint32`. The step-4 lead says `AccountSanctioned` is emitted nowhere under
  `src/`. Both become row notes, not mismatches.

No known-failure inventory fence is carried: none of these records names a
failure this delivery must guard before product work.

## 3. Constraints and non-goals

- Starting ref: `main` at `e9e95b891b3ae642516e017c46b97a18a1480164`. The run
  branch is `fiat/1361-emitter-versus-declaration-check-at-a-pinne`. The
  controller is pinned at Hexaemeron 1.6.77.
- Audited source: `wildcat-finance/v2-protocol` at
  `f5a26146987926f4811b72a795d662813dedfe85`, with the recorded compiler
  output read at tag v2.0.0, `a70f297fbd1b1ab597e0e9a3458a2d13a34b4657`.
- Toolchain: Python 3.14.6 stdlib; `git` for the `--from-git` path. No
  `solc`, `forge` or `cast` in the check or its tests.
- Suites: `python3 -m unittest discover -s tests` (root suite) and
  `python3 scripts/run_checks.py`, whose map already routes `scripts/`,
  `tests/` and `docs/` to the root suite. No map edit is expected. If a
  step's plan shows an unowned path, the fix goes into
  `tests/check-map-v1.json` in that same step.
- Generated artefacts `.horos/census.json` and `.horos/boundary.json` are
  regenerated and staged in every step that changes tracked files.

Non-goals, each with its reason:

- The unreleased `release/v2.5` candidate `bea503c2`. The issue says an
  unreleased branch gets a separate report, and the registry excludes
  unreleased Wildcat code. The generator takes `--ref`, so that report is one
  command away. It is proposed below as a carryover item.
- The V1 row and the deployed arch controller, built from
  `wildcat-finance/wildcat-protocol` at `da74452a`. That is a different
  repository and generation. Its own report belongs to a V1 consumer.
- Events emitted through Solidity `emit`, which covers HooksFactory's own
  events, the hooks templates, MarketLens and the one `emit
  ProtocolFeeBipsUpdated` in `WildcatMarketConfig.sol`. The compiler derives
  those logs from the declaration.
- Whether each call site passes the right argument in the right position. The
  check compares an emitter's parameter list with the declaration, not each
  caller's bindings. That is a source review for the Solidity Auditor's own
  audit.
- Runtime fidelity. That belongs to the #1601 differential, attached as
  supplemental evidence and never cited as this table's proof.
- Sub-word cleaning of `uint32`, `bool` and `address` values written by
  `mstore`. It is recorded as a note on each row, not graded.

Boundaries:

- Always: run the root suite and `python3 scripts/run_checks.py` before a
  commit; run the Imprimatur lint on every shipped document; regenerate both
  Horos scans; verify every fetched file's size and SHA-256 before parsing it.
- Ask first: adding a dependency; widening the fetch beyond
  `raw.githubusercontent.com`; changing the table's `schema` value once a
  consumer binds it; moving the pin.
- Never: commit a `v2-protocol` source file; call a row clean when its
  comparison did not run; drop a mismatched row; claim runtime fidelity from
  this table; write to `.hexaemeron/state.json` or a receipted report.

## 4. Design options

Three constructions, all static.

1. `source-text`. Parse the two emitter files and every `event` declaration
   under `src/` at the pin. Compute the canonical signature and Keccak-256 in
   Python and compare topic0, arity, indexed order and data layout. Trade: it
   is the smallest read, but the only declaration view is the one it parsed
   itself, so a parsing error in declarations and emitters can cancel out.
2. `source-and-abi`. The same scan, plus a second comparison of every emitter
   against the compiler ABI recorded beside the WildcatMarket and HooksFactory
   verification inputs. The same step records which deployed contract reaches
   each emitter. Trade: it reads 411,050 more upstream bytes (1,203,623 against 792,573), but the ABI is the view a
   decoder uses, and it exposes the `SphereXConfig` versus
   `SphereXProtectedRegisteredBase` difference above.
3. `solc-ast`. Compile the deployed standard inputs with solc 0.8.25 and read
   `eventSelector` and the Yul log calls from the compiler AST. Trade: it is
   the most faithful parser, but it needs a compiler binary in the check, and
   solc is not on this host's `PATH`, so nothing is produced.

### Design evidence

The record is `.hexaemeron/design-evidence.json`. The probe
`python3 .hexaemeron/design/probe.py --clone <v2-protocol clone>` measured
every selection cell and wrote its reports under `.hexaemeron/design/reports/`.

| Criterion | Concern | Form | source-text | source-and-abi | solc-ast |
| --- | --- | --- | --- | --- | --- |
| `emitters-scanned` | correctness | gate, at least 27 | 27 | 27 | 0, fail |
| `specimen-classes-caught` | correctness | gate, at least 5 | 5 | 5 | 0, fail |
| `abi-checked-rows` | correctness | metric, maximise | 0 | 32 | 0 |
| `regeneration-ms` | time | gate, at most 10000 | 633 | 745 | 0 |
| `upstream-bytes` | space | gate, at most 2097152 | 792573 | 1203623 | 386194 |
| `extra-binaries` | compatibility | gate, at most 0 | 0 | 0 | 1, fail |
| `rerun-identical` | recovery | gate, equals true | true | true | false, fail |
| `committed-table-regenerates` | correctness | conformance gate, blocks `integration` | pending | pending | pending |

The five specimen classes are a changed topic0 literal, a dropped topic, two
swapped indexed topics, a short data region and a declaration marked
`anonymous`. `solc-ast` fails four selection gates. Between the two
survivors, `source-and-abi` dominates on the single comparative metric, so
the rule is `unique-frontier` and the selected candidate is `source-and-abi`.

The conformance cell stays pending for each candidate. Its resolver is
`python3 .hexaemeron/design/resolve_conformance.py --clone <v2-protocol clone> --candidate <id>`.
The resolver runs the delivered `check` and writes one report, refusing to
overwrite. It is due at `integration`, so it runs before the final
`done merge-step`. `design_evidence.py --transition design-lock` exits 0.

## 5. Risk register seed

```risk-register
emitter-parse-miss | the text scan of each emitter body in the two scoped files | every logN site is counted; a body with zero or several sites becomes an unreviewed row and never a silent skip
declaration-miss | event discovery across every src file at the pin | every same-named event yields its own row; a non-elementary parameter type fails closed as unreviewed
oracle-independence | where expected topic0, arity and layout come from | the expected values derive from declaration text and the compiler ABI, never from the emitter literal under test
keccak-correctness | the stdlib Keccak-256 copy | pinned vectors for the empty input and the ERC-20 Transfer signature pass
abi-view-disagreement | source declaration against compiler ABI | a disagreement is recorded as a row problem, not resolved by preferring one view
deployed-binding | the claim that the pin is the deployed source | each scanned file is byte-equal to, or absent from, the WildcatMarket and HooksFactory inputs whose SHA-256 values the table records
source-drift | bytes read from a clone or over HTTPS | size and SHA-256 match the table's source block before parsing; the host is fixed and a redirect elsewhere refuses
vendored-source | the repository tree | no v2-protocol source file is committed; only paths, blobs, digests, line numbers and derived signatures
subprocess-git | the git show argv | a fixed argv list, no shell, ref and path from the table, bounded timeout
partial-write | the JSON and Markdown outputs | written through a temporary file and os.replace; check mode writes nothing
md-json-drift | emitters.md against emitters.json | the Markdown table is rendered from the JSON and a test compares the bytes
runtime-overclaim | prose in emitters.md and PR bodies | static only; the #1601 differential is named as supplemental, and no runtime, bytecode or capture claim appears
subword-note | uint32, bool and address values written by mstore | recorded as a note per row and never graded as a pass or a mismatch
horos-currency | .horos/census.json and .horos/boundary.json | both scans are regenerated and staged in each step that changes tracked files
```

## 6. Glossary seeds

- Emitter: a free function `emit_<Name>` that writes a log with an assembly
  `logN`.
- Declaration row: one pair of an emitter and a same-named `event`
  declaration at the pin; one emitter can have several.
- Arity: the `N` in `logN`, the number of topics including topic0.
- Mismatch class: one named disagreement: `topic0`, `log-arity`,
  `indexed-order`, `data-length`, `data-order`, `parameter-count` or
  `anonymous-declared`, prefixed `abi:<contract>:` when found against the ABI.
- Unreviewed emitter: one the scan could not compare, listed by name with the
  reason.
- Reached-by: the deployed contracts whose verification input carries the
  emitter file and calls the emitter.
- Source block: the table's record of each read file's path, ref, blob,
  bytes and SHA-256, plus the two verification inputs it is bound to.

## 7. Sources

- Issue: https://github.com/wildcat-finance/skills/issues/1361 and its
  2026-09-13 Miskatonic comment.
- Registry: `docs/kickoff/1359/targets.md`, `docs/kickoff/1359/targets.json`
  at `e9e95b89`.
- Harness: `plugins/hexaemeron/harness/PROVENANCE.json`,
  `plugins/hexaemeron/harness/fetch_protocol.py`; PR
  https://github.com/wildcat-finance/skills/pull/1601.
- Decision record: `docs/decisions/ADR-095-deliver-the-emitter-fidelity-suite-as-a-first-party-harness.md`.
- Estate map PR: https://github.com/wildcat-finance/skills/pull/1735.
- Proposed revision record: `docs/kickoff/1372/eventdecision.md`.
- Upstream source:
  https://github.com/wildcat-finance/v2-protocol/tree/f5a26146987926f4811b72a795d662813dedfe85
  and the tag at
  https://github.com/wildcat-finance/v2-protocol/tree/a70f297fbd1b1ab597e0e9a3458a2d13a34b4657.
- Withdrawn #1354 audit record: commit `073fcc168850c068ff52609e2bb06fe77c2deaac`
  in `wildcat-finance/skills`, path
  `audit/rounds/fiat-1354-fizz-4-emitter-fidelity-differential-suite.md`.
- Study probe and resolver: `.hexaemeron/design/probe.py`,
  `.hexaemeron/design/resolve_conformance.py`.

## 8. Signals, and the questions behind them

None for an unattended process, because nothing here runs unattended: the
generator is a command a person or a step exit runs. The one question a later
reader asks, "does this table still describe the source a capture decodes?",
is answered by `check`: exit 0, or exit 1 with each changed path, digest or
row named on stderr. The table's `schema`, commit and input digests let a
consumer answer it without rerunning anything. See the Ephoros contract.

## 9. Boundaries, per capability

- HTTPS fetch. Taken at it: a substituted or truncated file. Control: fixed
  host `raw.githubusercontent.com`, pinned commit in the URL, redirect check,
  size cap, SHA-256 check before parsing, as `fetch_protocol.py` does.
- Local clone read. Taken at it: a clone at another commit, or an argv
  injection through a path. Control: fixed `git` argv list, no shell, ref and
  paths only from the table's source block, digest check on the output.
- Untrusted Solidity text. Taken at it: input that makes the scan skip an
  emitter or hang. Control: a byte cap per file, patterns with no nested
  quantifiers, and an unreviewed row, not a skip, when a body does not parse.
- File writes. Taken at it: a half-written table. Control: temporary file
  plus `os.replace`, with `check` writing nothing.

No credential, secret or model output is involved. These feed the risk
register above. See the Phylax contract.

## 10. The budget, or its absence

One budget. `check` against a local clone finishes within 10 s, and the
offline test module within 5 s. The probe measured 745 ms for the selected
construction. Metron command:
`/usr/bin/time -p python3 scripts/emitter_declarations.py check --from-git <clone> --table docs/kickoff/1361/emitters.json`,
and `/usr/bin/time -p python3 -m unittest tests.test_emitter_declarations`.
No budget is set for the HTTPS path, which depends on the network. See the
Metron contract.

## 11. The fail-closed posture

`build` and `check` exit 1 on a missing file, a size or digest mismatch, a
source file larger than its cap, or a verification input whose digest
differs from the table. A found mismatch never fails `build`: the row is
written with its classes, because the issue calls a mismatch a finding to
preserve. `check` exits 1 on any byte difference between the regenerated and
committed table. Exit 2 is a usage error.

Guard convention: a fix found in audit gets a test in
`tests/test_emitter_declarations.py` that fails on the parent. The Elenchus
runner is `python3 tests/emit_emitter_declarations_report.py {report}` in
`unittest-json-v1`, reusing the confined writer in
`tests/emit_run_observation_report.py` as
`tests/emit_contributors_report.py` does. See the Elenchus contract.

## 12. Decisions and their homes

- Hold target source by identity only. This was already decided in
  `docs/decisions/ADR-095-deliver-the-emitter-fidelity-suite-as-a-first-party-harness.md`,
  and this delivery follows it. No new record.
- Where the table lives: `docs/kickoff/1361/`, beside the registry it
  consumes. This is cheap to reverse: one directory, no consumer yet. It is
  recorded in `docs/kickoff/1361/emitters.md`.
- The table schema `wildcat.emitter-declarations.v1`. A consumer such as #1378
  will bind it. Its `schema` field versions it and a new version is additive,
  so it is not expensive to reverse. It is documented in the same Markdown
  file.
- The declaration oracle is the source text plus the compiler ABI. This is
  the design choice above, recorded in `.hexaemeron/design-evidence.json` and
  in the committed study copy.

None of these earns a new ADR, because none is expensive to reverse. See the
Hypomnema contract.

Carryover candidates for the integration PR's `## Carried forward` block:

- `release-v2-5-separate-report`: the unreleased `bea503c2` candidate's own
  table, which the issue asks for separately; it needs a filing or a stated
  `none`.
- `spherexconfig-declaration-source`: the correction to the input record's
  statement that the SphereX declarations are in `SphereXConfig.sol`; it
  needs a `docs/kickoff/1359/targets.md` edit or a filing.
- `upstream-uint32-narrowing`: carried from PR #1601 unchanged, with
  disposition `none` for the same reason.
