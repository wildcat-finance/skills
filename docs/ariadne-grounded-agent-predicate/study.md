# Study: implement the grounded-agent predicate

Assumptions: issue #402 means the `ariadne-next` frontier job recorded at Ariadne v2.2.0, not a generic agent-evaluation feature. The producer is a local `berean-release/v1` directory that already exists and passes Berean's own verifier. Ariadne records and checks the evidence it can derive from those bytes; it does not run an agent, query a model, make network calls, repair a Berean release, or claim that Berean's substantive gates passed merely because Ariadne could parse the release. The prototype starts from `main` at `2e2608aa2ac62c5d556478e7f93186fddc36dce3`.

## 1. Problem statement

Build `https://ariadne.wildcat.finance/grounded-agent/v1` for maintainers who need an in-toto statement joining a grounded-agent release to the corpus, preserved chain reads, recorded answers, evaluation material, promotion state, and explicit absences behind it. The predicate needs a published schema, registration, gates 2 and 5, predicate checks, conformance fixtures, a bounded local capture path, CLI wiring, and user-facing documentation consistent with Ariadne's existing release model.

A working prototype can capture `plugins/berean/examples/goldfinch-demo-v0/release` without importing Berean at runtime or reaching a network, verify the resulting statement, and refuse a one-byte-tampered declared component. The demo commands are:

```bash
python3 plugins/ariadne/scripts/ariadne.py capture-grounded-agent --release plugins/berean/examples/goldfinch-demo-v0/release --name goldfinch-demo-v0 --first-capture-reason "first Ariadne capture of this Berean release" --output /tmp/grounded-agent.intoto.json
python3 plugins/ariadne/scripts/ariadne.py verify /tmp/grounded-agent.intoto.json
```

The test suite must also demonstrate the negative path without relying on `/tmp` or mutable repository fixtures.

## 2. Prior art

The local design is already split along the right seams. `plugins/ariadne/scripts/ariadne_lib/registry.py` maps a predicate URI to its module; `core_predicate.py` owns common claims and commands; predicate modules own gates 2 and 5 plus domain checks; `schemas/*.json` publish the corresponding closed body shape; `tests/test_schema_drift.py` compares each schema with its module tables; and `tests/fixtures/conformance/` supplies minimal passing and breaching statements. `capture/state_fixture.py` is the closest bounded local adapter: it reads a sibling skill's public format without a runtime import, constrains files and paths, preserves evidence class rather than upgrading it, and constructs an Ariadne statement. `plugins/ariadne/docs/state-fixture.md` and `docs/capturing-a-state-fixture.md` separate predicate semantics from operator procedure.

The producer contract is `plugins/berean/scripts/berean_lib/release.py`. `berean-release/v1` closes its fields, defines `release_digest` as sha-256 over canonical JSON of the named identity fields, pins corpus, optional reads, answers, optional evaluation files, retention and allowlists, and treats `promotions.jsonl` as a separately verified chain. `plugins/berean/README.md` says Berean owns corpus/read/answer/evaluation verification and Ariadne may bind the finished release. The reference producer bytes are under `plugins/berean/examples/goldfinch-demo-v0/release`.

The last two merged pull requests that changed this subject were read before choosing a design:

- [#219, The Ariadne state-fixture predicate, and the gate 5 hole it would inherit](https://github.com/wildcat-finance/skills/pull/219), merged 2026-08-19, established the sibling-format adapter pattern, the schema and conformance surface, the evidence-count source rule, and the explicit first-capture comparison. Its applicable boundary remains: a capture reads producer evidence and may not promote it; an absent class stays explicit. Its fixed gate 5 defect remains a required regression pattern. No unrelated state-fixture work is reopened.
- [#665, Prove captured receipts against the header's receiptsRoot](https://github.com/wildcat-finance/skills/pull/665), merged 2026-08-27, added state-fixture/v2 while keeping independent proof authorities and finished with eight clean audit rounds. Its applicable boundary remains: an adapter binds the producer's recorded proof class without claiming transaction-trie proof, canonical-chain membership, or provider independence. New live RPC capture and those stronger claims remain out of scope.

The whole-set synopsis check passed before study. The in-scope Ariadne source `plugins/ariadne/audit/AUDIT.md` was read through its fresh verified `plugins/ariadne/audit/AUDIT_SYNOPSIS.md` view: source sha-256 `d8d13ef2d25c0520cd0d90e46d76b5aeb0e29db46746a22c5ef4f8c1ff764160`, synopsis sha-256 `53aacb442dbd89acb0dd3a0906aa92bb989207231760a107ba6fb46431735402`. The immediately preceding subject run `audit/rounds/fiat-383-prove-receipts-against-the-captured-header-s.md` was read through its fresh verified synopsis, source sha-256 `23e316e76b7165e68249e512bc4271a239693d89f3f29777b7f1e2641a4ef10a`, synopsis sha-256 `58da147f92b69b330ff06818a95efb187293b948cd0bbb5c84fc6248beffbc19`. It records no unresolved in-scope finding or unpursued lead after round 8. `Covered`, `Not checked`, Elenchus verdicts, leads not pursued, and status were preserved by the verified views; there were no missing legacy fields relevant to this job. Its carried exclusions are no new RPC capture, no transaction-trie or canonical-chain proof, and no provider-independence claim. The recorded security waiver applies only to that run; this run states its own waiver because issue #402 changes no Solidity.

External format anchors are the in-toto Statement v1 type already implemented in `plugins/ariadne/scripts/ariadne_lib/statement.py` and JSON Schema Draft 2020-12 as used by the published Ariadne schemas. No new external package or standard is needed.

## 3. Constraints and non-goals

The base is `main` at `2e2608aa2ac62c5d556478e7f93186fddc36dce3`. Commands use the repository's `.python-version`, CPython 3.13.15. Production code remains Python standard library only. The implementation must preserve existing predicate URIs, CLI behavior, verification results, statement envelope semantics, atomic output convention, resource caps, portable path rules, and schema-to-code drift checks. There is no Solidity; the security suite is waived for that stated reason.

Always: read only regular local files beneath the selected release root; cap JSON, line, tree, and aggregate input work; reject symlinks, special files, duplicate JSON keys, non-portable paths, digest mismatches, malformed promotion chains, and unstable reads; preserve `null` plus a reason for evidence that was not produced; construct output in memory and land it atomically; make each negative fixture one intelligible breach from a passing fixture where feasible.

Ask first: adding a dependency; changing CI, licensing, repository storage conventions, a pre-existing predicate URI or field; changing Berean's public format; widening capture to network or subprocess execution; accepting a new grounded-agent producer; or making a semantic claim stronger than the local bytes establish.

Never: import Berean at Ariadne runtime, shell out to Berean, execute agent or model output, follow a path outside the release, infer missing evidence, label an unverified producer release as verified, treat `release.json`'s file digest as its semantic `release_digest`, mutate producer bytes, or conflate a promotion record with proof of answer correctness.

Deferred past the prototype are grounded-agent/v2, multiple producer formats, detached signatures, transparency-log identity, online model evaluation, fresh chain capture, automatic release discovery, performance claims, and changes to Berean itself.

## 4. Design options

1. Bind only a recursive digest of the release directory. This is small, but consumers cannot recover which corpus, reads, answers, evaluations, promotion state, or absence the digest covered. It fails the problem statement.
2. Import Berean's verifier or invoke its CLI, then copy its verdict into Ariadne. This avoids duplicated public-shape checks, but couples two separately installed plugins, grants Ariadne a claim derived from executable foreign policy, expands subprocess/package boundaries, and makes standalone Ariadne releases brittle.
3. Add a format-bound local adapter. Ariadne independently reads the closed `berean-release/v1` shape, recomputes the canonical semantic `release_digest`, verifies every digest and declared path it records, checks the promotion chain shape it binds, and emits its own statement without claiming the complete Berean verification verdict. This duplicates a narrow public wire contract but keeps authority and installation boundaries legible.
4. Define a generic agent-release abstraction now and adapt Berean through it. This might ease a future second producer, but no second format exists; the abstraction would encode guesses as public API and increase the audit surface.

Choose option 3. It is the cheapest construction to comprehend that still exposes recoverable evidence, remains dependency-closed, and respects marketplace ownership. The duplication is bounded to the public `berean-release/v1` fields actually recorded. A compatibility fixture and schema-drift test make that cost visible.

## 5. Risk register seed

```risk-register
path-escape | untrusted paths declared by a local grounded-agent release | reject absolute, backslash, dot-segment, invisible, whitespace-only, escaping, duplicate and non-canonical paths before opening anything
special-file | release-tree reads across symlinks fifos devices and sockets | accept bounded regular files only and refuse link traversal at every component
unstable-read | bytes changing between metadata inspection digesting and statement construction | use the established bounded stable-read primitive and fail when identity or size changes
resource-exhaustion | hostile JSON trees files answer lists and promotion chains | retain explicit byte depth count line and aggregate ceilings with boundary tests
digest-confusion | semantic release digest versus release.json and component byte digests | independently recompute each named digest under its declared algorithm and keep the meanings in separate fields and subjects
evidence-upgrade | adapter interpretation of Berean corpus reads answers evaluations and promotions | record only locally established facts preserve absence and never emit a passed Berean verification claim
comparison-hole | gate 5 baseline and current identities for first and later captures | require a named digested current side and either a named digested baseline or null plus a stated first-capture reason
promotion-ambiguity | optional or malformed promotions.jsonl beside the release | distinguish absent never-promoted and valid terminal state and refuse malformed or release-mismatched records
partial-write | statement output when capture is interrupted or verification fails | build and verify before the existing atomic replacement path can expose output
schema-drift | public JSON Schema diverging from predicate code or fixtures | extend schema-to-module tables and make all registered fixtures traverse the generic runner
compatibility-regression | new registry and CLI wiring changing existing predicates | run the complete Ariadne and root suites plus all existing conformance fixtures
stale-prose | marketplace and Ariadne docs retaining the unimplemented frontier | cold-read every mutable first-party occurrence and reconcile only after the implementation and evolution gate pass
```

The audit loop must enumerate every id as reviewed or not applicable. A clean generic suite does not discharge a boundary-specific concern.

## 6. Glossary seeds

`grounded-agent release`: a local `berean-release/v1` directory whose declared corpus, reads, answers, evaluations, policy fields, retention, and promotion chain are candidates for binding.

`semantic release digest`: Berean's sha-256 over canonical JSON of the named release identity fields, excluding `release_digest`; it is not the digest of `release.json` bytes.

`component digest`: sha-256 of one declared file's exact bytes.

`promotion chain`: optional `promotions.jsonl` records whose chain and terminal relation to the release are independently represented; absence means never promoted, not unknown success.

`capture`: Ariadne's bounded local translation from existing bytes to an in-toto statement; it produces no new agent evidence.

`baseline`: an earlier grounded-agent capture named and digested for gate 5 comparison, or explicit `null` with the reason the current capture is first.

`evidence upgrade`: any claim stronger than the producer bytes and Ariadne's local checks establish.

## 7. Sources

- Issue: `https://github.com/wildcat-finance/skills/issues/402`.
- Frontier and contracts: `plugins/ariadne/skills/ariadne/EVOLUTION.md`, `plugins/ariadne/skills/ariadne/SKILL.md`, `plugins/ariadne/AGENTS.md`, root `PROMISE_MACHINE.md`.
- Ariadne implementation: `plugins/ariadne/scripts/ariadne_lib/registry.py`, `core_predicate.py`, `gates.py`, `statement.py`, `capture/state_fixture.py`, `plugins/ariadne/scripts/ariadne.py`.
- Ariadne public and test surface: `plugins/ariadne/schemas/state-fixture-v2.json`, `plugins/ariadne/docs/state-fixture.md`, `plugins/ariadne/docs/capturing-a-state-fixture.md`, `plugins/ariadne/docs/conformance.md`, `plugins/ariadne/tests/test_schema_drift.py`, `plugins/ariadne/tests/test_conformance.py`.
- Berean producer contract: `plugins/berean/README.md`, `plugins/berean/scripts/berean_lib/release.py`, `plugins/berean/scripts/berean_lib/promote.py`, `plugins/berean/examples/goldfinch-demo-v0/release`.
- Prior deliveries and evidence: GitHub pull requests #219 and #665; fresh verified Ariadne and `fiat-383` audit synopses named in item 2.
- Standards: `https://github.com/in-toto/attestation/blob/main/spec/v1/statement.md` and `https://json-schema.org/draft/2020-12/json-schema-core`.

## 8. Signals, and the questions behind them

This is a bounded interactive CLI, not an unattended service, so no persistent metrics or alerts are justified. The capture, verifier, tests, and demo still need deterministic diagnostics answering: which release and semantic digest were bound; which declared component, gate, or predicate check failed; which optional evidence was explicitly absent; and whether the current capture was compared with a baseline or marked first. CLI errors and `verify`'s ordered gate/check results are the signals. The capture and verification steps will carry these requirements under the active [Ephoros contract](/Users/kethcode/.codex/plugins/cache/wildcat-labs/hexaemeron/1.6.5/skills/ephoros/SKILL.md), without copying that contract here.

## 9. Boundaries, per capability

The parser opens an attacker-controlled local directory: bounded regular-file reads, portable confined paths, closed JSON shapes, duplicate-key rejection, stable-read checks, and fail-before-output controls close it. The adapter maps a sibling plugin's public format: no import, subprocess, network, mutation, or borrowed verifier verdict closes the authority boundary. The writer replaces one caller-selected output: validation before the existing atomic writer closes partial exposure. The CLI accepts names, reasons, release roots, previous statements, and output paths: existing portable-string, normalized-subject, and path checks apply before statement creation. This boundary inventory is governed by the active [Phylax contract](/Users/kethcode/.codex/plugins/cache/wildcat-labs/hexaemeron/1.6.5/skills/phylax/SKILL.md).

## 10. The budget, or its absence

No performance improvement or throughput claim is in scope, so there is no Metron comparison budget. Safety ceilings are correctness controls, not speed targets, and must be exact constants with boundary tests. The functional measurement is `python3 -m unittest discover -s plugins/ariadne/tests -t plugins/ariadne`; it must exit zero while the capture retains explicit input and work ceilings. This disposition follows the active [Metron contract](/Users/kethcode/.codex/plugins/cache/wildcat-labs/hexaemeron/1.6.5/skills/metron/SKILL.md).

## 11. The fail-closed posture

Malformed shape, unknown fields, missing or mismatched digests, unsafe paths, special files, changing bytes, exceeded caps, inconsistent promotion state, ambiguous absence, invalid baseline/current comparison, failed statement self-verification, or output replacement failure stops capture with nonzero status and no publishable statement. Every implementation or audit fix gets a focused guard that fails on the parent revision, passes after the fix, and also runs through the step's exact JSON-reporting Elenchus test command. Triage and guard semantics stay with the active [Elenchus contract](/Users/kethcode/.codex/plugins/cache/wildcat-labs/hexaemeron/1.6.5/skills/elenchus/SKILL.md).

## 12. Decisions and their homes

The public predicate URI and body shape, the choice to bind `berean-release/v1` without runtime coupling, the semantic-versus-byte digest distinction, the evidence/absence vocabulary, and gate 5 comparison semantics are expensive to reverse. Their durable homes are the new JSON Schema, predicate documentation, capture documentation, conformance inventory, and the completed grounded-agent row in `plugins/ariadne/skills/ariadne/EVOLUTION.md`; the next frontier row must follow the ledger's one-frontier rule. No separate ADR is justified because these are Ariadne predicate decisions with existing canonical homes, not cross-suite policy. If implementation reveals a cross-plugin contract change, work stops for an Ask-first decision rather than laundering it into code. Record placement follows the active [Hypomnema contract](/Users/kethcode/.codex/plugins/cache/wildcat-labs/hexaemeron/1.6.5/skills/hypomnema/SKILL.md).

### Amendment -- 2026-08-27

**What changed.** Prior art now includes `plugins/berean/docs/design.md`: it requires the Berean release to stay separate because Ariadne core gate 4 refuses structured conclusion keys such as `score`, `verdict`, and `grade`. The grounded-agent predicate may pin evaluation and promotion files as subjects and expose their non-conclusion identity metadata, but it may not project evaluation thresholds, result counts, or a substantive Berean verification verdict.

**Why.** This sibling design record was read after the original study receipt. Naming its constraint closes the evidence gap without changing the selected format-bound adapter: exact bytes cross the boundary; foreign conclusions do not.

**Steps touched.** Step 1.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds.
