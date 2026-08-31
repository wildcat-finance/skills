<!-- Source: .hexaemeron/study.md; SHA-256: e22d60952c40bade2e24a605a6780e15b2be3af4cd4d00cfd598903e6504e92f. Relative discipline links were adjusted for this durable location. -->

# Study: validate Homologia manifests, vectors and expected-answer provenance

Assuming, unless corrected:

1. This run delivers Step 2 of the accepted Homologia runbook and does not execute a contract or mirror.
2. The repository's Python 3.14.6 and standard library remain the only runtime dependencies.
3. A Lazarus artefact reference is an opaque repository-relative identifier at this step; Homologia checks its presence and path form but does not open or prove the artefact.
4. Existing limits remain fixed: 16 vector sets, 100,000 vectors per set, 8 MiB per input file and 64 MiB across the manifest and vector files.
5. No workflow file or other new CI surface is needed for this bounded step.

## 1. Problem statement

Homologia needs its first substantive operation for maintainers who have one pinned on-chain computation, one pinned off-chain mirror and expected integer answers. The prototype is `homologia.py check`: it admits one closed manifest plus declared JSONL vector sets, rejects malformed identity, scale, provenance, tolerance, path and cap data before writing state, and writes one canonical checked-inputs record atomically. It neither runs an implementation nor calls a network.

The working demo is:

```bash
python3 plugins/homologia/scripts/homologia.py check \
  --manifest plugins/homologia/examples/wad-interest-v0/manifest.json \
  --out build/homologia/checked-inputs.json
shasum -a 256 build/homologia/checked-inputs.json
python3 plugins/homologia/scripts/homologia.py check \
  --manifest plugins/homologia/examples/wad-interest-v0/manifest.json \
  --out build/homologia/checked-inputs-second.json
shasum -a 256 build/homologia/checked-inputs-second.json
cmp build/homologia/checked-inputs.json build/homologia/checked-inputs-second.json
```

A working prototype exits zero, emits byte-identical records twice, and has at least 20 focused cases including the four held-job refusals: bare `proved`, missing or unequal scale, every cap breach before output, and nondeterministic example bytes.

## 2. Prior art

The accepted plugin study and five-step runbook are `plugins/homologia/docs/homologia-study.md` and `plugins/homologia/docs/homologia-runbook.md`. Step 1 landed in [PR #851](https://github.com/wildcat-finance/skills/pull/851); it left a help-only CLI and the exact Step 2 boundary used here. The last two merged pull requests that touched Homologia were [PR #1003](https://github.com/wildcat-finance/skills/pull/1003), which rewrote public descriptions while retaining the unfinished frontier, and [PR #996](https://github.com/wildcat-finance/skills/pull/996), which refreshed Homologia's installed Promise Machine copy but added no Homologia behaviour. Neither carries unfinished Step 2 implementation to reuse.

The in-scope audit source is `audit/AUDIT.md`; Homologia has no plugin-local audit record. The whole-set currency check exited zero at starting commit `0987aa37f5110501b2c7a440f42370f81d58afe5`, so `audit/AUDIT_SYNOPSIS.md` was read as the verified view. Its Homologia Step 1 round reports no finding. `audit-schema`, `Covered`, `Not checked` and `Elenchus verdict` are marked as missing legacy fields and remain unknown. Its leads not pursued were the non-verdict `--version` success path, an unspent Homologia workflow gate, two repaired ADR-001 shape defects, and historical whole-log prose findings outside the Step 1 path. This step keeps `--version`, adds no workflow, preserves ADR shape, and scopes prose checks to changed material while the checked runner covers the repository dependency closure. The later amendment warns that receipts describe exact bytes at an exact base; this run therefore records its own starting commit and reruns current checks.

Relevant standards and local precedents are JSON Lines for vectors, JSON Schema draft 2020-12 for published closed shapes, `plugins/lazarus/skills/lazarus/SKILL.md` for the producer boundary of proved chain answers, and the descriptor-safe, bounded JSON readers already used by Promise Machine and Protasis. Fizz may produce vectors; Homologia only consumes declared files. Pandects owns economic laws. No part of their charters moves here.

## 3. Constraints and non-goals

The starting ref is `0987aa37f5110501b2c7a440f42370f81d58afe5`. The exact interpreter is Python 3.14.6 from `.python-version`; tests use standard-library `unittest`. Input is UTF-8 JSON for the manifest and UTF-8 JSONL for vectors. Paths are repository-relative, lexical, non-symlink regular files beneath the manifest's directory. Reads use one descriptor, refuse replacement races and enforce caps before decoding or field access. Output is canonical UTF-8 JSON with sorted keys and a trailing newline, placed by an atomic same-directory replacement.

The manifest is closed and declares pair identity, mirror scale, vector-set descriptors and optional tolerance declarations. Each vector-set descriptor has a unique id, unique path and a scale exactly equal to the mirror scale. Each vector has a unique id, integer-string inputs, one integer-string expected answer and one of three closed provenance forms: `proved` with a Lazarus artefact reference, `recorded` with chain and block identity, or `asserted` with a named author. A vector may name a tolerance only when its set declares the same bounded absolute tolerance.

Always run the focused Homologia suite, the repository checked runner selected from the diff, Promise Machine checks, Protasis, Imprimatur, Phylax, Ephoros, Hypomnema and Horos before publication. Ask before changing a cap, adding a dependency, adding a CI workflow or broadening the three provenance forms. Never contact a chain, execute a mirror, infer correctness from agreement, follow a symlink, accept an absolute or parent path, or leave partial output after refusal.

Deferred work remains Step 3 mirror execution, Step 4 comparison/render/verification, and Step 5 scale measurement and public completion. This step does not validate Lazarus artefact contents, decide whether expected answers are true, generate vectors, calculate an answer or produce an agreement verdict.

## 4. Design options

`strict-stdlib-validator` uses one standard-library traversal to enforce the closed manifest and vector grammars, semantic identities, provenance and caps, then writes one canonical record atomically. It keeps the existing zero-dependency contract and performs one validation pass, at the cost of maintaining explicit field checks beside the published JSON Schemas.

`schema-library-validator` would add a JSON Schema dependency for structural validation and keep a second handwritten pass for paths, scale identity, provenance relationships, caps and the atomic write. It shortens some shape code, but introduces one runtime dependency and two validation passes without removing the semantic validator.

The checked record at `.hexaemeron/design-evidence.json` selects `strict-stdlib-validator` by a unique non-dominated frontier: both designs satisfy closed shape, the 8 MiB file limit and atomic refusal, while the selected design uses one pass and no new dependency instead of two passes and one dependency. The report commands were run before their digests were bound.

## 5. Risk register seed

The audit loop enumerates every line below and records reviewed or not applicable.

```risk-register
path-containment | manifest and vector paths at the filesystem boundary | lexical absolute parent backslash and symlink paths are refused before open
descriptor-race | each named input between stat open read and final identity check | one no-follow descriptor is bounded and the named identity must stay unchanged
cap-before-decode | manifest and vector bytes supplied by an untrusted caller | file aggregate set and vector caps stop the read before JSON decoding or state writing
duplicate-json-key | closed JSON objects before semantic validation | duplicate keys and non-finite numbers are rejected rather than overwritten by the decoder
scale-identity | manifest mirror scale and every vector-set scale | missing or unequal id and decimals are refused
proved-provenance | an expected answer labelled proved | the closed provenance object requires one repository-relative Lazarus artefact reference
provenance-strengthening | recorded asserted and proved expected-answer labels | each class keeps its own required fields and cannot inherit a stronger claim
tolerance-declaration | per-vector tolerance use against its vector-set declaration | use without an exactly matching declared absolute tolerance is refused
partial-write | checked-inputs output during any refusal or interruption | validation completes before a same-directory temporary file is atomically replaced
deterministic-record | repeated checks of the same admitted bytes | canonical ordering input digests counts and trailing newline make both output bytes equal
```

## 6. Glossary seeds

Checked inputs: the canonical record of admitted pair identity, vector metadata, source digests and expected answers; it is not a verdict.

Mirror scale: the named integer unit and decimal count that every vector set must match exactly.

Proved answer: an expected integer whose provenance names a Lazarus artefact reference; the label does not make Homologia the proof producer.

Recorded answer: an expected integer tied to a declared chain id, block number and block hash without a Lazarus proof claim.

Asserted answer: an expected integer attributed to a named author without a chain-record or proof claim.

Tolerance declaration: a vector-set-level absolute integer bound that a vector may opt into by exact value; comparison remains deferred.

## 7. Sources

- Issue [#458](https://github.com/wildcat-finance/skills/issues/458), including the owner approval comment.
- `plugins/homologia/skills/homologia/SKILL.md` and `plugins/homologia/skills/homologia/EVOLUTION.md` for the canonical boundary and held job.
- `plugins/homologia/docs/homologia-study.md`, `plugins/homologia/docs/homologia-runbook.md` and `plugins/homologia/docs/decisions/ADR-001-one-charter-for-numeric-agreement.md` for the accepted architecture.
- `plugins/homologia/AGENTS.md`, root `PROMISE_MACHINE.md` and `.agents/skills/promise-machine/SKILL.md` for runtime and transition ownership.
- `audit/AUDIT_SYNOPSIS.md`, admitted after `audit_synopsis.py --check .` verified it against `audit/AUDIT.md`.
- PRs [#851](https://github.com/wildcat-finance/skills/pull/851), [#996](https://github.com/wildcat-finance/skills/pull/996) and [#1003](https://github.com/wildcat-finance/skills/pull/1003).
- JSON Schema draft 2020-12 and JSON Lines as the published shape conventions; the standard-library validator remains authoritative for this prototype.

## 8. Signals, and the questions behind them

Three unattended questions govern this command: Which boundary refused the input? Which file and object id caused it? What admitted bytes and counts produced the checked record? The implementation step emits one stable `HOM-CHECK-*` refusal code with a repository-relative subject and a one-line recovery action on standard error, or a success summary with the manifest digest, vector-set count, vector count and output digest on standard error. The canonical checked-inputs record carries the same identities and source digests for later steps. This follows the cited [Ephoros contract](../../../hexaemeron/skills/ephoros/SKILL.md); no service metric or dashboard is warranted because `check` is a local finite command.

## 9. Boundaries, per capability

Manifest ingestion is worth path escape, oversized input, decoder ambiguity and identity substitution; closed fields, lexical containment, descriptor-safe bounded reads, duplicate-key rejection and post-read identity checks close it. Vector ingestion adds aggregate exhaustion, repeated set paths, excess rows, malformed JSONL, scale drift, provenance strengthening and undeclared tolerance; pre-write caps, unique ids and paths, exact scale equality and closed class-specific validators close those boundaries. Output is worth partial or misleading state; validation completes first and one canonical byte string is atomically installed. This follows the cited [Phylax contract](../../../hexaemeron/skills/phylax/SKILL.md). The Lazarus reference stays opaque here, so opening or verifying a foreign artefact is not a new capability.

## 10. The budget, or its absence

There is no performance budget in this step because it does not make a speed claim and the accepted runbook reserves scale measurement for Step 5. The safety budgets are input caps rather than throughput targets; focused tests construct boundary-sized metadata and refusal specimens. If performance is changed later, the cited [Metron contract](../../../hexaemeron/skills/metron/SKILL.md) requires a recorded baseline and the same measurement before and after.

## 11. The fail-closed posture

Any unreadable or mutable path, invalid UTF-8, duplicate key, non-canonical integer, unknown field, missing identity, scale mismatch, invalid provenance, undeclared tolerance, duplicate id or path, cap breach, or output-install failure exits nonzero and leaves the target absent or byte-identical to its pre-run state. Stable error codes separate bad invocation from refused input. Each discovered failure is first preserved as a focused red test, reduced to the smallest fixture, repaired at cause and retained as the guard described by the cited [Elenchus contract](../../../hexaemeron/skills/elenchus/SKILL.md).

## 12. Decisions and their homes

The expensive decision becoming real is that chain answers enter Homologia as evidence-classed input rather than being produced by an EVM call; it lives at `plugins/homologia/docs/decisions/ADR-002-chain-answers-are-evidence.md`. The public closed manifest and vector shapes, their cap table, canonical output and compatibility promise live at `plugins/homologia/docs/schema-compatibility.md` with machine-readable schemas under `plugins/homologia/references/`. Stable refusal codes belong beside the CLI implementation and in that compatibility document because they are an operational interface, not a separate architectural choice. The cited [Hypomnema contract](../../../hexaemeron/skills/hypomnema/SKILL.md) governs the ADR shape and placement.
