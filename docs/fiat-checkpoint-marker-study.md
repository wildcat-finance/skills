# Repair checkpoint key-marker false positives

Assuming, unless corrected: the archive format, identity rules and saved evidence stay unchanged; the four token patterns stay unchanged; this run contains no Solidity. The coordinating agent stated these assumptions before delegation. This is ordinary Fiat generation repair for issue 1755, separate from held frontier 1212 and the interrupted service run.

## 1. Problem, user and working prototype

The released scanner refuses a checkpoint when an opaque controller member quotes matching private-key markers without a body. That prevents an operator from preserving a run even though verification passes. Two service attempts under Hexaemeron 1.6.59 and Fiat 6.67.1 ended with `secret-shaped-member`; neither published an archive. Those attempts are recorded preflight evidence, not executions by this study worker.

A working prototype accepts the two unchanged public CP3 audit files, retains the declared material and token refusals, and completes native archive creation, inspection and restore on a signed disposable run containing both files. The restored files must have their original SHA-256 values, verification must pass, and `next` must name the same semantic continuation while executing none of it.

Success has three executable boundaries. The direct guard in `plugins/hexaemeron/tests/test_checkpoint_marker_scan.py`, driven by `plugins/hexaemeron/tests/emit_fiat1755_guard_report.py`, fails by assertion on the starting controller and passes after the fix. `plugins/hexaemeron/tests/prove_checkpoint_marker_scan.py --criterion implementation-regression` resolves the product refusal, benign, streaming and resource checks before Step 3. Its `--criterion native-archive-roundtrip` operation resolves the signed demonstration before integration. The exact commands and report paths are in the design record. The registered `scripts/run_checks.py` entrypoint supplies the repository gate; a future runbook must use registered command interfaces for its Exit and Tests fields.

The native demonstration uses the controller built by this run at `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, with its digest in the report. Its source command is the pending native-roundtrip resolver, which must invoke actual `checkpoint archive`, `checkpoint inspect`, `checkpoint restore --archive`, `verify`, `status` and `next` commands in disposable roots. Existing `SignedRunFixture` uses real disposable OpenPGP signatures with simulated GitHub/ref observations. Reusing it proves that fixture boundary; it does not prove a live GitHub service run. Preserve that distinction in the demonstration report.

The positive observation joins both source digests and the semantic continuation. Negative observations plant material or token shapes one at a time, assert `secret-shaped-member`, assert no published ZIP/sidecar, and verify unchanged controller state and ledger. Also inspect a tampered archive and require the existing refusal. A successful fixture does not prove universal secret detection, cloud access, operating-system concurrency isolation or service implementation admission.

## 2. Prior art and audit reading

The subject already ships in `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`: the constants beginning at line 942, `_checkpoint_archive_secret_shaped` at line 26569, and `_checkpoint_archive_scan` immediately after it. The scanner reads 65,536-byte chunks with a 10,079-byte carry. A whole body line can begin within 1,792 bytes after a header; a matching footer alone can occur within 9,984 bytes. Only the two CP3 public Markdown files were positive among the 180 audit Markdown files in the coordinating agent's preflight scan.

The two latest relevant merged PR bodies were read from the captured GitHub source records. PR 1754 preserves unchanged gate receipts across released adapter updates and carries service admission to issue 1676. PR 1740 adds SSH and OpenPGP archive support and includes the repairs associated with PRs 1744, 1745 and 1746; its carryover says none. PR 1746's complete body was also read: the fixture has its own signer, and an unsigned observation cannot publish a joined proof. The study retains those controls. Earlier full bodies 1528, 1572 and 1634 explain the deliberate footer refusal, shared inspector, restore transaction and surviving carryover.

Whole-set synopsis currency was checked from this worktree with `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`, exit 0 for 95 sources. The command, output digests and output are under `.hexaemeron/reports/audit-synopsis-currency.*`. Currency establishes the generated views' bytes, not that every audit was read.

The in-scope plugin source is `plugins/hexaemeron/audit/AUDIT.md`, read through its complete verified `AUDIT_SYNOPSIS.md`. F-01 through F-09 remain fixed; F-10 remains accepted. Missing legacy audit-schema, Covered, Not checked and Elenchus fields remain unknown. Its unresolved leads concern same-account concurrency, cross-filesystem state placement, machine-facing JSON control characters and the unexercised vendored Solidity suite. This repair changes none of those boundaries.

The in-scope run source is `audit/rounds/fiat-861-outer-checkpoint-archive-export-and-restore.md`, read through its verified sibling synopsis with these scopes: current Step 2 rounds 1 to 4, current Step 5 round 1, all current finding ids, the Step 1 and Step 2 status rows, and the Step 3/4 status summaries, Elenchus and lead passages. Step 2's required fields were read; the other rounds were scoped context reads, not a full reading of all 27 current rounds. The preflight scanner suite ran eight tests with one documented expected failure; that is recorded baseline evidence, not a suite rerun by this worker. The authoritative source and view remain unchanged. Original Step 2 rounds 1 to 8 are absent from the current reconstruction and were read directly at commit `70bcb261dec0503344a722174b6a91a1dbc9076e`, through their finding ids, severities, statuses, Covered, Not checked, Elenchus and lead fields. Round 1 and round 2 finding prose was also read; later mechanism claims were joined to the dated study amendments and current guards. They remain historical evidence, not current receipts or repeated tests.

The scanner history determines the regression set. S2-R1-04 and S2-R1-05 closed the missing OpenPGP header and fixed carry derivation. S2-R2-02 replaced header-only refusal after the scanner rejected its own specification. S2-R3-01, S2-R4-02 and S2-R6-01 closed escaped LF, CRLF and numeric-escape failures. S2-R7-01 separated body-start and footer reaches; its closing round records real keys through 8,192 bits and geometry twins above that, with no real 16,384-bit key proved. The original eight Elenchus values remain `null`, `guarded`, `null`, `passed`, `guarded`, `guarded`, `null`, `passed`. Original rounds reviewed exporter controls only; restore and inspector controls were not yet implemented. Their short-line, escaped-solidus, indented-body, same-account mutation, diagnostic, orphan-stage and environment leads are retained as limits or probes here, not silently marked fixed.

Current S2-R1b-01 is open on policy and closed on its validation-gap half: the adjacent-marker refusal is deliberate and its test passes. This run changes that policy only after a dated append-only amendment to `docs/fiat-checkpoint-archive-study.md`. The existing prose-only `footer_only` specimen must become an explicit benign case; neither it nor the adjacent-marker test may disappear without a replacement assertion. Current S2-R1b-02 remains open reconstruction residue, concerning a count-valued design criterion where its old Exit described a boolean. S2-R1b-03 and S2-R1b-04 remain fixed in `25e17506`; S2-R3-01's docstring correction remains fixed in `a6d1bea3`. The current four Step 2 Elenchus values remain `null`, `guarded`, `guarded`, `passed`. They did not run the command against real controller contents. Their Covered/Not checked distinction and all carried leads remain attached to the source.

S1-R3b-01's old runbook preamble and S2-R1b-02's reconstructed design record are historical limitations, outside this repair. The inspector and restore findings retain the statuses in their source records and PRs 1572/1634. Existing signing-key diagnostics, destination custody and concurrency remain with issues 1647, 1648 and 1649. The service-admission work remains with 1676. Native Codex currency observation remains unknown at init; a separate comparison recorded all 587 installed plugin files equal to the public starting tree. Issue 1756 owns the native observation gap. None is added to this implementation.

Outside the repository, RFC 7468 sections 2 and 3 describe base64 material between textual boundaries, generated 64-character lines, varying newline conventions and permissive readers. That supports testing alternative line widths; it does not make this scanner a complete PEM, OpenPGP or SSH parser. Source: [RFC 7468, sections 2 and 3](https://www.rfc-editor.org/rfc/rfc7468.html). No organisation-wide repository survey or general secret-scanner evaluation was performed.

## 3. Constraints, versions and non-goals

The starting ref is `main` at `e2307ed5966e18727434b3e49bec89db736f7b17`. Use `/home/kethcode/.local/bin/python3.14`, version 3.14.6, and the repository's standard-library unittest tooling. The installed controller is Hexaemeron 1.6.59, Fiat 6.67.1 and Protasis 6.14.1. Its native currency receipt is honestly unknown; do not edit the installed cache or registry to turn it into a native current verdict.

Always preserve audit source and synopsis bytes, receipts, ledger history, state and existing archive/schema identities; retain all four token patterns; run the affected checked-runner scope and applicable prose/derived-file checks. Build fixtures in disposable directories, with no real credential payload in committed evidence. Leave the service run and its saved refusal evidence read-only.

Ask first if evidence requires a dependency, archive-format change, broader trust boundary, destructive history rewrite or a change to the declared scanning scope. Existing authorization covers the bounded scanner policy repair, its amendment, tests and release. Never exempt a path, Markdown fence, quotation or string value; suppress a scan; redact saved evidence; remove a capsule member to pass; forge a receipt; or treat verification as implementation admission.

No new archive format is required by the measurements. Existing archives still face the same digest, signature, identity, schema and controller-version admission. A newer repaired inspector can accept benign bytes an old inspector refuses. An old inspector may stop at its older controller-version admission before reaching its footer rule. Keep the compatibility set explicit for the starting Fiat generation and the eventual released generation; neither schema stability nor a producer success promises old-reader acceptance. Do not relabel an old archive to bypass admission.

The package advances by a patch release at integration. Fiat's governed decision belongs to its next generation after the integration base; keep the frontier and held target unchanged. A runbook may use the supported version relation instead of predicting an integration-base token now.

## 4. Designs, measurements and selection

The closed record is `.hexaemeron/design-evidence.json`. Four candidates were executed, each against the same 436 refusal specimens and 119 benign specimens. Selection includes actual unchanged public bytes, a seeded 3,072-bit RSA key whose arithmetic round trip was checked, syntax variants under seven recognized private-key labels, 8,192-bit geometry fixtures, 1- and 8-character rewrapping, bounded PEM/PGP metadata, escaped solidi, repeated markers and chunk splits. Relabelled RSA bytes establish lexical scanner behaviour for those labels, not valid EC, DSA, SSH or PGP key structure.

| Candidate | Missed refusals / 436 | Benign refusals / 119 | Median ceiling, ms | Traced peak, bytes |
| --- | --- | --- | --- | --- |
| footer-proximity | 117 | 114 | 92 | 155656 |
| whole-lines-only | 231 | 0 | 77 | 159103 |
| bounded-material | 0 | 0 | 196 | 173277 |
| complete-decoder | 229 | 0 | 60 | 158877 |

`footer-proximity` preserves the existing predicate and therefore the false refusal. `whole-lines-only` removes the footer branch but loses forms that branch protected. `complete-decoder` requires a footer and a strictly decodable base64 body; it loses truncated material and does not establish cryptographic key validity. `bounded-material` retains the current independent whole-line witness and replaces footer-only evidence with a bounded lexical material witness. It is the sole candidate passing both correctness gates, so `unique-frontier` selects it. All four passed the four token probes and the deterministic input-preservation check. The selected prototype costs 196 ms against the released predicate's 92 ms and 17,621 additional traced bytes in these samples. That is the measured trade for the expanded material coverage, not a claim about full archive latency.

The selected witness starts at a recognized header, skips horizontal edge whitespace, admitted line breaks and up to seven recognized armour metadata lines, then accumulates at least 16 base64 glyphs. Raw LF, CRLF and CR; their short JSON escapes; and the numeric escapes in either hex case are admitted. An escaped solidus counts as one glyph. A line break may join short body segments; ordinary prose with spaces inside a segment stops the prefix. The first body byte must begin fewer than 1,792 original bytes of the header end, each metadata line is at most 256 original content bytes, and all reads stay within the existing 9,984-byte lookahead. Metadata names are `Version`, `Comment`, `MessageID`, `Hash`, `Charset`, `Proc-Type` and `DEK-Info`. Blank lines and edge spaces consume the same bound. No matching footer, quote context or filename can replace material evidence.

Keep the existing whole-line witness independently sufficient, including missing footers and its current 1,792-byte start bound. Keep 65,536-byte chunks and the 10,079-byte carry derived from the longest admitted header and lookahead. The implementation must avoid repeated whole-buffer body searches per header and keep temporary reads bounded. Ten additional observed boundary probes at `.hexaemeron/reports/boundary-observations.json` cover 15/16 glyphs, 256/257-byte metadata lines, seven/eight metadata lines, 1,791/1,792-byte starts, the 16,384-bit geometry and a conservative false positive. Production tests must retain both sides of those bounds. The experimental code is a measured construction, not product code or a production-edit authorization.

This witness also refuses the old 16,384-bit stripped geometry specimen by its early material prefix, without extending the lookahead. The amendment must withdraw that particular expected-failure claim and convert its assertion into an ordinary guard, retaining the geometry evidence. It does not establish every key size or encoding. Fewer than 16 material glyphs, unrecognized labels, overlong armour prefixes, encoded boundary text, arbitrary Unicode/base64-character escapes and nested encodings remain outside the declared recognition rule. A long ordinary base64-shaped word immediately following a header can still refuse; so can the pre-existing whole-line witness near a quoted header. This is a bounded shape detector with stated false positives, not a proof that content contains or lacks a secret.

Twenty-four resolved cells cover correctness, time, space, compatibility and recovery; eight conformance cells remain pending, two for each candidate. Only the selected candidate's later gates authorize progression. `implementation-regression` blocks `step:3`; `native-archive-roundtrip` blocks `integration`. Each pending cell names its exact resolver and future report. None asserts a result that has not run.

The intended sequence is Step 1 scaffold and historical policy amendment, Step 2 guarded implementation, Step 3 signed demonstration. Scaffold must remain green before the inoculation guard is applied. The guard is assigned to Step 2. The controller derives and checks the exact runbook; this study writes no receipt.

## 5. Risks the audit must enumerate

```risk-register
marker-without-material | body classification | both unchanged public files and empty or prose-only pairs pass without a path or quoting exception
material-without-footer | independent body and prefix witnesses | truncated and absent-footer specimens refuse across all declared encodings
short-lines-and-metadata | lexical body grammar | seeded key widths 1 and 8 and bounded PEM or PGP metadata retain refusal
chunk-carry | streaming scan | markers and material crossing 65536-byte boundaries refuse with the derived 10079-byte carry
repeated-markers | bounded CPU and memory | header-dense input stays within the declared regression budget without a whole-buffer search per header
token-parity | four self-delimiting patterns | original patterns and refusal results remain unchanged
evidence-custody | public files and controller records | source digests match before archive and after restore while state and ledger are unchanged by a refusal
archive-admission | shared inspect and restore path | existing schemas, digest, signature, identity and version checks still decide admission
diagnostic-content | CLI reports and stderr | only bounded refusal metadata is emitted, with no member contents or key bytes
policy-amendment | historical study and tests | dated append precedes behaviour change and explicitly replaces empty-pair, prose-only and old residue expectations
demo-boundary | signed disposable fixture | actual native commands and semantic next are observed while simulated GitHub reads remain labelled
release-and-retry | installed controller and service run | release, install and new-chat refresh precede a separately recorded service checkpoint retry
```

## 6. Glossary

A marker is a recognized private-key armour boundary. A whole-line witness is the existing base64-line rule. A material prefix is the selected bounded sequence of body glyphs after a header and optional armour lines. A carry is the prior chunk suffix retained for the next scan. A geometry twin has measured encoded size but does not prove a working keypair. Semantic continuation means the same `next` directive after relocation, allowing its documented path changes.

## 7. Sources and known-failure handoff

Repository paths above refer to the starting tree at https://github.com/wildcat-finance/skills/tree/e2307ed5966e18727434b3e49bec89db736f7b17. The historical source is https://github.com/wildcat-finance/skills/blob/70bcb261dec0503344a722174b6a91a1dbc9076e/audit/rounds/fiat-861-outer-checkpoint-archive-export-and-restore.md. PR bodies are https://github.com/wildcat-finance/skills/pull/1754, https://github.com/wildcat-finance/skills/pull/1740, https://github.com/wildcat-finance/skills/pull/1746, https://github.com/wildcat-finance/skills/pull/1528, https://github.com/wildcat-finance/skills/pull/1572 and https://github.com/wildcat-finance/skills/pull/1634.

The accepted task and preflight are at https://github.com/wildcat-finance/skills/issues/1755 and `/home/kethcode/scratch/fiat-checkpoint-repairs/issue-1755/preflight/`. The public source has 376,713 bytes and SHA-256 `bce008b201071b1ded3e656e24c0bfabb67923932a2cb3a994cb260172d6709c`; its synopsis has 378,244 bytes and SHA-256 `86bab9bce5db6b37a67527336bbfb1f65036a4f3ff504e50914be416be3934b2`. Selection code, per-cell reports, raw observations and environment details are `.hexaemeron/measure_design.py` and `.hexaemeron/reports/`.

The one known failure is S2-R1b-01's marker-only refusal. The independent expected id is `kf-1755-s2-r1b-01`. The inventory is a study handoff: the controller must check it against the exact later runbook and obtain a real Elenchus inoculation result before production work. It has not run in this study packet.

```known-failure-inventory
{
  "schema": "protasis-known-failure-inventory/v1",
  "source_views": [
    {
      "id": "cp3-marker-policy",
      "path": "audit/rounds/fiat-861-outer-checkpoint-archive-export-and-restore.synopsis.md",
      "source_sha256": "bce008b201071b1ded3e656e24c0bfabb67923932a2cb3a994cb260172d6709c",
      "view_sha256": "86bab9bce5db6b37a67527336bbfb1f65036a4f3ff504e50914be416be3934b2"
    }
  ],
  "findings": [
    {
      "id": "kf-1755-s2-r1b-01",
      "source_ref": "cp3-marker-policy: S2-R1b-01, current Step 2 rounds 1 to 4, source lines 207 and 249",
      "failure": "The pure scanner refuses unchanged public audit quotations containing matching private-key markers without key body material.",
      "guard_paths": [
        "plugins/hexaemeron/tests/test_checkpoint_marker_scan.py",
        "plugins/hexaemeron/tests/emit_fiat1755_guard_report.py"
      ],
      "test_command": "python3 plugins/hexaemeron/tests/emit_fiat1755_guard_report.py --case kf-1755-s2-r1b-01 --report {report}",
      "report_format": "unittest-json-v1",
      "report_file": ".elenchus/issue-1755-kf-1755-s2-r1b-01.json",
      "expected_guard_verdict": "guarded",
      "green_command": "python3 plugins/hexaemeron/tests/emit_fiat1755_guard_report.py --case kf-1755-s2-r1b-01 --report .elenchus/issue-1755-kf-1755-s2-r1b-01-green.json",
      "consuming_step": 2
    }
  ],
  "no_known_findings": null
}
```

## 8. Signals and operator questions

Use `plugins/hexaemeron/skills/ephoros/SKILL.md`. No new alerting service is needed for this bounded local command. The operator needs three answers: did it refuse before publication, which declared class refused, and did the restored run verify with the expected continuation? Existing exit status, `secret-shaped-member`, archive digest, timing fields, inspector findings and restore `verify`/`status`/`next` answers provide them. Step 2 pins the refusal and empty publication directory; Step 3 records command exits, digests and the continuation. Reports carry case identifiers and counts, never member contents.

## 9. Trust boundaries and controls

Use `plugins/hexaemeron/skills/phylax/SKILL.md`. Controller members are untrusted bytes; the recognizer consumes bounded byte windows without evaluating strings or interpreting Markdown. A recognized label alone grants no acceptance, and a matching footer alone grants no refusal. The scanner does not decode a private key into a cryptographic library or spawn a parser. Existing archive input confinement, digest joins, signature verification, destination handling and atomic publication remain their current owners' controls.

Synthetic bodies and seeded fixture keys are generated in memory or disposable fixture directories and never copied into study reports. Tests that generate working signing keys retain the fixture's temporary-home isolation. Diagnostic checks assert the existing fixed refusal, with no matched-byte excerpt. Inspection and restore must continue using the same product predicate, so producer and consumer cannot disagree through separate implementations.

## 10. Performance budget and measurement

Use `plugins/hexaemeron/skills/metron/SKILL.md`. The selection workload totals 2,852,105 bytes: 1 MiB plain filler, approximately 1 MiB repeated headers, and the two unchanged public files. Timing is the ceiling of the median of five sequential samples; exact samples are recorded. Allocation is Python `tracemalloc` peak during scanning, with input allocation and imported modules excluded. It is not process RSS or a 1 GiB archive benchmark.

The pre-receipt measurement command is `python3 .hexaemeron/measure_design.py --candidate bounded-material --criterion scan-time --report .hexaemeron/reports/bounded-material-scan-time.json`; substitute `peak-allocation` in both positions for allocation. These selection reports become immutable when receipted; later product measurements go to new conformance paths. Replay the committed measurement source on the pinned starting tree `e2307ed5966e18727434b3e49bec89db736f7b17`, copying it to `.hexaemeron/measure_design.py` and choosing new report paths. It imports that tree's controller and fixture helpers; running it against repaired code cannot reproduce the released baseline.

The product conformance resolver must compare the released and implemented scanner on this same workload, on the same host, with five samples each. Require the implemented median no greater than four times its same-run baseline and traced peak below 1,048,576 bytes, with unchanged chunk and carry limits. The selected prototype is within those limits in this study. Existing native archive budgets remain unchanged; the final native resolver records elapsed commands and exercises their existing checks. Host timing is measured evidence about those inputs, not a universal latency claim.

## 11. Refusal, guards and recovery

Use `plugins/hexaemeron/skills/elenchus/SKILL.md`. The current classifier's acceptance regression must fail by assertion against the parent. The dedicated six-argument reporter runs a direct pure-scanner unittest and emits a complete `unittest-json-v1` result with nonzero executed tests, zero errors, zero skips and zero expected failures. A subprocess custody error, missing fixture or old expected failure is not a guard. Keep the reporter's guard-path set closed to its test and reporter files; do not pull product changes into the inoculation overlay.

Before narrowing behaviour, append the dated historical study amendment. After implementation, keep positive and negative cases separate so one refusing member cannot mask another member's result. Each refusal leaves the original files and saved service evidence intact. Missing or stale reports block only their named transition. A failed native demonstration leaves integration blocked; inspection, correction and rerun remain available.

After a signed release, install it and refresh the host with the required new chat before retrying the preserved service checkpoint. Verify that run before and after the retry and compare state/ledger hashes. Record its archive result separately from service Step 2, which remains blocked on issue 1676 and admission. Issue 1756's currency repair remains separate. The study and fixture cannot complete that later operational acceptance.

## 12. Decisions and their homes

Use `plugins/hexaemeron/skills/hypomnema/SKILL.md`. This is a Fiat-local policy decision, so `plugins/hexaemeron/skills/fiat/EVOLUTION.md` owns the release decision; no second ADR is required. The historical contract change appends to `docs/fiat-checkpoint-archive-study.md` before product code. The public recognition rule, bounds, compatibility and residue belong in `plugins/hexaemeron/skills/fiat/references/checkpoint-archive.md`; comments explain why footer-only refusal was removed and why the independent body witness remains.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | bounded-material
record | plugins/hexaemeron/skills/fiat/EVOLUTION.md
```

Scaffold commits byte-identical copies of this study and the controller-derived runbook at `docs/fiat-checkpoint-marker-study.md` and `docs/fiat-checkpoint-marker-runbook.md`, plus the measured design record and reports under `docs/fiat-checkpoint-marker/` and the byte-identical measurement source at `docs/fiat-checkpoint-marker-measure-design.py`. Preserve the original script bytes; its replay instructions require the pinned starting tree and `.hexaemeron` placement. The owned demonstration helper and its digest-bound transcript preserve the native evidence. Generated source bindings, portable copies and Horos artefacts follow their existing generators. The short delivery is complete only after the later conformance gates, independent audit and signed release; the separate service retry remains an explicit operational handoff.
