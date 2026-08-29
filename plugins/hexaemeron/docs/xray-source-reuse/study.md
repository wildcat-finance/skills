# Study: reuse source-bound X-Ray analysis across Fiat audit rounds

## Assuming, unless corrected

1. The run starts from `main` at `5489863196006d8e8b45799d74b56208cac65e4d`, the fast-forwarded base recorded by Fiat.
2. Issue #510 asks for one working prototype: reuse validated preparation facts between X-Ray runs without narrowing the current scope or weakening the four required outputs.
3. The bundled Pashov X-Ray remains upstream-owned and byte-identical. Its current `SKILL.md` SHA-256 is `b23bb94517805c1b8ce717d0e1e0282b0b5c14c7b16f4c32e73940292d3d4a41`, matching the Hexaemeron overlay.
4. The implementation uses Python's standard library and the repository's existing unittest conventions. No dependency is added.
5. Fiat remains the controller and receipt store. No source facts, cache keys, analysis payloads, or cache verdicts enter Fiat state or its ledger.
6. This is an ordinary issue-backed delivery, not a held skill-frontier job. No `EVOLUTION.md` frontier row is owed by this run.

## 1. Problem statement

Repeated Fiat audit rounds give X-Ray the complete current step scope. X-Ray then repeats its source inventory and per-source preparation even when a fix changed only one source. Build a first-party Hexaemeron adapter that can reuse validated, source-bound preparation entries while forcing fresh work for changed or transitively affected sources.

A working prototype has one checked scope format, one cache format, a dry-run plan, candidate assembly, and an atomic promotion boundary. It demonstrates two runs over a multi-contract fixture: the second unchanged run reuses every eligible preparation entry, a body-only change dirties that source, dependency drift dirties reverse dependants, removed sources disappear, write-site drift rebuilds the current complete write set, and corrupt or mismatched cache material falls back to full recomputation. Every run regenerates `architecture.json`, `x-ray.md`, `entry-points.md`, and `invariants.md` from the union of fresh and still-valid facts.

The proof commands are:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_xray_reuse
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
```

The demonstration path is the fixture runner added under `plugins/hexaemeron/tests/fixtures/xray-reuse/`; it records extraction counts and output digests for a full run, unchanged reuse, body-only drift, dependency drift, write-site drift, removal, and corrupt-cache recovery.

## 2. Prior art and current evidence

Issue #510 is open, unassigned, has no matching branch or pull request predating this run, and its 26 August review says the capability is still absent at `ab611eb96a6a`. The run rechecked that state before `hexctl init`. Issue #622 cross-references #510 only to exclude it: #622 selects repository tests, while #510 reuses X-Ray preparation facts.

The current vendored X-Ray is version 2 and explicitly runs a single sequential three-phase pipeline. It enumerates the complete source boundary, extracts per-source entry points, guards, delta writes, transitions, call facts and invariant inputs, then writes all four outputs. It has no manifest, incremental planner, reusable fact entry, reverse-dependency closure, or cache recovery. Its Promise Machine overlay authorises the four scoped orientation artefacts and refuses missing artefacts, hidden exclusions, and stale instruction digests. Reuse must preserve that promise rather than create a stronger one.

Fizz Sync supplies the closest shipped lifecycle: retain a previous snapshot, rebuild current inputs, diff drift, regenerate only affected handlers, and refresh the snapshot only after the reconciled harness builds. Its ABI-centred invalidation is insufficient here because a Solidity body-only change can alter guards, calls, deltas, transitions, or write sites without ABI drift.

The last two merged pull requests touching the X-Ray distribution were #66 and #64. PR #66 removed browsing-only README copies and reconciled rolling-frontier prose; PR #64 rewrote marketplace and attribution prose. Neither added runtime analysis reuse. Their boundaries carry forward: canonical vendored instructions remain upstream-owned, host discovery prose is not a runtime contract, and first-party behaviour belongs outside the vendored tree.

`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .` exited zero at the run base. The in-scope verified views are `audit/AUDIT_SYNOPSIS.md` for repository-wide history and `plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md` for the plugin. The root synopsis retains its historical unknown fields and contains no accepted X-Ray cache design. The plugin synopsis records the controller-state integrity fixes and says the vendored Pashov skills were not exercised against non-Solidity plugin work; it supplies no cache authority. Those synopses were read as views after the whole-set currency check, not represented as their source files.

The upstream X-Ray `VERSION` endpoint also reports `2`. No upstream capability was imported or modified by this study. A later upstream implementation can supersede the adapter through a deliberate digest reconciliation; this prototype does not predict that design.

## 3. Constraints and non-goals

**Starting state.** `main@5489863196006d8e8b45799d74b56208cac65e4d`; Python standard library; current repository and Hexaemeron suites; X-Ray overlay digest above. The active Codex install registry was unavailable, so Fiat recorded controller currency as `unknown`; the installed and checked-in Fiat files were independently byte-identical at `fiat-v5.26.1`.

**Always.** Preserve the complete logical scope; regenerate all four final outputs; validate every external JSON object before use; keep paths inside the selected project and cache roots; use atomic candidate promotion; run focused, Hexaemeron, and root suites; lint shipped prose; compare the vendored X-Ray digest before and after.

**Ask first.** Add a dependency, edit an upstream-owned X-Ray file, change a public Promise Machine shape, add a selectable skill or plugin, place cache material in Fiat state, or widen source reads beyond the operator's declared scope.

**Never.** Treat cache validity as evidence that a fact was originally correct; cache a final security conclusion; retain a removed source through old rows; pass model output into a shell or filesystem path; promote a partial candidate after a failed run; weaken or skip the four X-Ray outputs; describe fewer extractor calls as a security improvement.

**Non-goals.** Editing Pashov's X-Ray, changing X-Ray's evidence class, making Fiat an artefact store, caching audit findings or final reports, proving Solidity semantic dependency closure, replacing a compiler dependency graph, speeding coverage or git-history analysis, introducing a daemon, or generalising the adapter to non-Solidity analyzers.

## 4. Design options

1. **Edit the vendored X-Ray instruction and scripts.** This gives the shortest invocation and a single apparent owner. Rejected: the repository must keep upstream bytes unchanged, and a local fork would make the overlay digest and future upstream reconciliation dishonest.
2. **Store cache content and keys in Fiat state.** This makes round identity easy to find. Rejected: it gives the delivery controller ownership of analysis validity, expands the receipt schema, and directly contradicts issue #510's boundary.
3. **Add a new selectable first-party skill.** This gives the adapter a canonical user-facing identity. Rejected for the prototype: it widens router, marketplace, installation, versioning, and skill-count surfaces for an internal composition operation that users do not invoke separately.
4. **Add a first-party Hexaemeron adapter around digest-pinned X-Ray. Chosen.** A standard-library adapter outside the vendored tree owns scope, source digests, dependency closure, entry validation, candidate assembly, and atomic cache promotion. A first-party overlay and Fiat audit reference bind it to X-Ray's existing full-output promise. Trade: the audit path gains an extra manifest protocol and a second piece of code to maintain, but ownership remains explicit and neither upstream bytes nor Fiat receipts are distorted.

The adapter caches only bounded per-source preparation entries. Global write-site maps, lifted property inputs, cross-contract relations, economic derivations, and all four final outputs are rebuilt from the current union every run. That choice spends synthesis work to avoid stale conclusions; the reusable unit is deliberately smaller than a report.

The protocol has four transitions:

1. `plan` validates the declared scope and dependency graph, hashes every source, compares the prior manifest, and emits a complete current plan. A missing, malformed, wrong-version, wrong-analyser, wrong-instruction, wrong-config, unsafe, incomplete, or uncertain cache yields a named full-recompute plan rather than reuse.
2. The X-Ray worker extracts fresh entries for every dirty path. Each entry repeats its path, source digest, analyser identity, instruction digest, bounded fact shape, and direct dependencies.
3. `assemble` validates all fresh and reused entries, refuses a missing dirty entry or stale reusable entry, discards removed paths, and writes one candidate union. Complete per-variable write sets and every derived property record are then regenerated from that union.
4. `promote` requires the four current outputs and their recorded digests before atomically replacing the cache. A kill or failed output leaves the previous cache untouched.

## 5. Risk register seed

```risk-register
scope-paths | operator-declared source paths crossing into filesystem reads | reject absolute traversal symlinked non-files oversized and out-of-root paths before reading
cache-poisoning | untrusted prior manifest and preparation entries | bounded duplicate-key JSON parsing closed schemas exact digests and full-recompute fallback prevent authority from stale bytes
dependency-closure | declared imports and inheritance determining reverse dependants | missing unknown cyclic or out-of-scope dependency facts force full recomputation and fixtures cover transitive invalidation
body-only-drift | source semantics changing without ABI or storage-layout drift | byte digests dirty the changed source regardless of interface stability
removed-source | old rows surviving after a contract leaves scope | current scope is authoritative and assembly refuses or drops every row absent from it
write-set-drift | one changed write site affecting global maps and invariants | every run rebuilds complete variable write sets and all derived invariants from the current fact union
partial-write | interruption between candidate assembly outputs and cache replacement | candidate directories and atomic replacement preserve the prior valid cache until all four output digests exist
output-scope | reuse accidentally narrowing the final X-Ray reports | all four outputs are regenerated and their source inventory must equal the current plan before promotion
model-output | agent-produced fact entries crossing into paths or executable authority | model text is validated as bounded data and never controls a shell command or unvalidated path
fiat-authority | analysis cache content leaking into controller state or receipts | tests assert no cache field or payload is added to Fiat state ledger or audit-round receipt shapes
vendored-integrity | first-party work changing upstream-owned X-Ray bytes | exact tree and instruction digest checks run before and after the implementation
measurement-overclaim | fewer repeated extractor calls presented as stronger or universally faster analysis | Metron records only fixture extraction counts timing spread and unchanged correctness outputs
```

## 6. Glossary seeds

- `Scope manifest` is the operator-declared current source set, direct dependency edges, analyser identity, instruction digest, and compiler/configuration identity.
- `Preparation entry` is one validated, source-bound collection of per-source facts used as input to current synthesis.
- `Dirty source` is a source that must be extracted again because it or an affecting input changed.
- `Reverse dependant` is a current source whose declared dependency closure reaches a dirty source.
- `Current union` combines fresh entries for dirty sources with validated entries for reusable sources, with no removed source.
- `Candidate cache` is a complete replacement assembled beside, but not yet promoted over, the prior valid cache.
- `Full recomputation` is a named safe recovery in which no prior preparation entry is reused.
- `Final outputs` are X-Ray's required `architecture.json`, `x-ray.md`, `entry-points.md`, and `invariants.md` for the complete current scope.

## 7. Sources

- `https://github.com/wildcat-finance/skills/issues/510`, current review and original acceptance contract.
- `plugins/hexaemeron/skills/x-ray/SKILL.md` and `VERSION`, vendored X-Ray v2 instruction and current single-pass pipeline.
- `plugins/hexaemeron/PROMISES.md`, `hexaemeron-x-ray-preaudit` overlay and digest.
- `plugins/hexaemeron/skills/fizz/skills/fizz-sync/SKILL.md`, snapshot and drift precedent.
- `plugins/hexaemeron/skills/fiat/references/audit-loop.md` and `plugins/hexaemeron/agents/warden.md`, current round orchestration and source-bound packet.
- `plugins/hexaemeron/skills/protasis/SKILL.md`, study and runbook content contract.
- `audit/AUDIT_SYNOPSIS.md` and `plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md`, used only after the zero-exit whole-set synopsis currency check.
- Merged pull requests `wildcat-finance/skills#66` and `#64`, the last two merged changes touching the X-Ray distribution.
- `wildcat-finance/skills#622`, explicit neighbouring-scope exclusion.
- `pashov/skills` X-Ray `VERSION`, observed as `2` during the study.

## 8. Signals, and the questions behind them

Ephoros (`plugins/hexaemeron/skills/ephoros/SKILL.md`) owns retained telemetry. This adapter is an invoked CLI, not a daemon or scheduled service, so it adds no metrics, alerts, traces, or retained logs. Its machine-readable result must still answer four operator questions: Was this a full or reuse plan, and why? Which sources are dirty, reused, removed, or reverse-invalidated? Did assembly cover the exact current scope? Were all four outputs present and digest-bound before promotion? `plan`, `assemble`, and `promote` answer those questions through bounded JSON fields and stable exit codes; those are operation results, not telemetry claims.

## 9. Boundaries, per capability

Phylax (`plugins/hexaemeron/skills/phylax/SKILL.md`) owns the boundary review. The scope manifest and cache are external JSON: bounded reads, duplicate-key rejection, closed shapes, exact digest checks, and no coercion control them. Scope paths cross into filesystem reads: lexical relative-path checks, `resolve`, root containment, regular-file and symlink refusal, source-count and byte caps control them. Agent-produced fact entries are untrusted model output: their closed schema and source identity are validated before assembly, and no entry supplies a command or unchecked path. Candidate writes cross the durable filesystem boundary: same-directory staging and atomic replacement leave either the old complete cache or the new complete cache. No subprocess is constructed from source or cache data, and no dependency or credential boundary is added.

## 10. The budget, or its absence

Metron (`plugins/hexaemeron/skills/metron/SKILL.md`) owns the measurement. The acceptance condition is reduction in repeated extraction work, not a universal wall-time target. The fixture demo records full-run fresh-entry count, unchanged-run fresh/reused counts, identical final-output digests, three same-command wall-time samples, and spread. The unchanged run is kept only when all final outputs remain byte-equivalent and fresh extraction falls from the complete fixture count to zero. Body and dependency drift must show the expected nonzero dirty closure instead of optimizing it away. The exact command will be the focused fixture test in `plugins.hexaemeron.tests.test_xray_reuse`; its proof record preserves environment, counts, timings, and variance without generalising beyond that fixture.

## 11. The fail-closed posture

Elenchus (`plugins/hexaemeron/skills/elenchus/SKILL.md`) owns observed failures and guards. Unsafe or unreadable scope input refuses the run because the current boundary is unknown. Invalid, incomplete, corrupt, mismatched, or uncertain prior cache material yields a named full-recompute plan and never partial reuse. Assembly refuses any missing dirty entry, stale reusable entry, duplicate source, scope mismatch, or unsafe candidate path. Promotion refuses before mutation unless all four outputs exist and match the current inventory record. A killed command leaves the prior cache. Every defect found during implementation gets a focused test that fails on the unfixed parent, then the focused suite and both repository suites run before resuming.

## 12. Decisions and their homes

Hypomnema (`plugins/hexaemeron/skills/hypomnema/SKILL.md`) owns record placement. The expensive cross-cutting choice, a first-party adapter outside the vendored X-Ray tree with no Fiat-state cache and fresh global synthesis, goes in the next numbered record under `docs/decisions/`. The adapter's checked claim and refusal boundary go in `plugins/hexaemeron/PROMISES.md`. Its operator protocol belongs in `plugins/hexaemeron/skills/fiat/references/xray-reuse.md`, beside the audit loop that invokes it. Public CLI arguments, results, and failures live in source docstrings and `--help`. The accepted study and runbook are committed under `plugins/hexaemeron/docs/xray-source-reuse/`. No governed-skill `EVOLUTION.md` changes because this run is not closing a held frontier.
