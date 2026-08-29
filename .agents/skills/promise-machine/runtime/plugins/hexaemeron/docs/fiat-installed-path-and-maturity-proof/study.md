# Fiat installed-path and maturity proof

## Problem statement

Fiat has rules for resolving `hexctl.py` from the exact `SKILL.md` that
activated the run, and it has rules for refusing further frontier work after
the held job is exhausted. Both rules were added by
[skills#75](https://github.com/wildcat-finance/skills/pull/75), but Fiat's held
frontier records one remaining empirical gap: they have not been exercised
together in a completed delivery from an installed Hexaemeron plugin.

This delivery is for maintainers of the Wildcat Skills marketplace. It must
use the Fiat controller under the installed Codex plugin cache while keeping
the target repository rooted at this checkout. It must preserve the resolved
controller path and every controller transition in `.hexaemeron/`, publish a
small tracked proof, and make the required closing entry in Fiat's evolution
ledger.

A working prototype has all of these properties:

1. The active controller is
   `/Users/c0rtexzer0/.codex/plugins/cache/wildcat-labs/hexaemeron/1.0.0+codex.20260816145806/skills/fiat/scripts/hexctl.py`,
   while `--dir` names
   `/Users/c0rtexzer0/Documents/ChatGPT/Wildcat Skills`.
2. The live hash-chained ledger contains the absolute controller-path receipt
   and the receipts for each later phase. At closure, the installed
   controller's `status` says `done` and its `verify` command reports an
   intact chain and consistent state.
3. The delivery PR is merged and contains a durable proof of the installed
   run.
4. `plugins/hexaemeron/skills/fiat/EVOLUTION.md` advances once on the
   evolution axis from `fiat-v1.2.0` to `fiat-v2.2.0`, retains frontier
   revision `installed-path-and-maturity-proof`, sets `Frontier status` to
   `mature`, and sets `Next Fiat job` to `None -- mature`.
5. `plugins/hexaemeron/skills/fiat/SKILL.md` reports metadata version `2.2.0`,
   and the Hexaemeron and repository test commands required by `AGENTS.md`
   pass.

The chosen reading of "packaged plugin" is an installed cache directory with
its own plugin manifest and skill tree, not a controller read from the target
checkout. This run meets that reading. It does not claim that the cache is a
signed or independently attested distribution; that is outside Fiat's stated
frontier.

## Evidence at study time

The run started from clean `main` at
`60a01d4c6918e6d30b45da7677dcf6d63a936a3e`, which is also `origin/main`.
The installed plugin manifest identifies the cache as Hexaemeron package
`1.0.0+codex.20260816145806`. The installed Fiat skill identifies itself as
`fiat-v1.2.0`; plugin-package and skill-evolution versions are separate
namespaces.

The live state is in phase `study` and records three pre-study receipts:

- `resolved_controller_path` is the absolute installed path named in the
  prototype check above. Its ledger entry has hash
  `818952b21994aa38e9963b2aeb1284feadd7092318acfc10a43660695e4bf977`
  and follows the security-suite receipt without a chain gap.
- `security_suite` is waived because this delivery concerns Python controller
  evidence and skill prose, not Solidity.
- `labs_marketplace` is recorded as deferred. It is not an input to the Fiat
  frontier decision.

The installed and checkout copies of these files are byte-identical:

| File | SHA-256 |
| --- | --- |
| `skills/fiat/scripts/hexctl.py` | `5934bca666ca019c3837aa597cb8b2f9e861e41c11f500d37f3cfdfdeceefc9d` |
| `skills/fiat/SKILL.md` | `3b9da7eb0657b3a075d93661b9b5e72b313ff4d98ede83436e5575af79c971f9` |
| `skills/fiat/EVOLUTION.md` | `3494f39b58b488bf16241cae2fa42a0a68f6b7eaeff178dd738f9980deea8d43` |
| `tests/test_hexctl.py` | `bf196207af51016c1cb48f810dddd801094e01f664eba65248250bd2fb3a852f` |

The installed suite was run directly from
`.../hexaemeron/1.0.0+codex.20260816145806/tests/run_tests.py` with Python's
bytecode cache disabled. It passed 61 of 61 tests in 8.533 seconds. Those
tests exercise the controller as a subprocess in temporary target
directories. They cover the fixed phase order, receipt gates, concurrent
writer exclusion, crash recovery, state and ledger tamper detection, reset,
audit closure, required prose skills, and terminal push data. The evolution
tests also pin resolution from `FIAT_SKILL_FILE`, rejection of checkout- or
working-directory-based controller guesses, the mature-frontier stop, the
version counters, and the frontier digest.

Issue [skills#74](https://github.com/wildcat-finance/skills/issues/74) states
the original acceptance conditions: active-skill controller resolution, a
hard maturity stop, held-frontier integrity, and enforcement tests. Merged PR
[skills#75](https://github.com/wildcat-finance/skills/pull/75) implemented
them and reported 61 of 61 Hexaemeron tests, 55 of 55 Imprimatur tests, 14 of
14 root tests, and schema checks. GitHub reports PR #75 merged as commit
`60a01d4c6918e6d30b45da7677dcf6d63a936a3e`; its visible checks completed
successfully where applicable.

## Prior art

### In this repository

- `plugins/hexaemeron/skills/fiat/SKILL.md` lines 34-58 define active-skill
  path resolution: derive `FIAT_SKILL_DIR` from the loaded file, require its
  `scripts/hexctl.py`, and pass the target repository separately through
  `--dir`.
- The same file's frontier gate, lines 104-125, refuses mature or exhausted
  frontier runs and requires one evolution increment when a completed job
  changes the held target.
- `plugins/hexaemeron/skills/VERSIONING.md` defines the independent evolution,
  generation, and epoch counters. It also defines the exact newline-terminated
  frontier string hashed into each history row.
- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` stores state under the
  supplied target directory, serialises ledger objects into canonical JSON,
  hashes every state and ledger entry with SHA-256, and locks mutating commands
  with `fcntl.flock`.
- `plugins/hexaemeron/tests/test_hexctl.py` is a CLI-level suite. Its helper
  invokes the adjacent packaged controller as a subprocess in a temporary
  directory, which separates the controller source from its target state.
- `plugins/hexaemeron/tests/test_evolution.py` checks version-to-ledger
  agreement, digest correctness, axis increments, mature closure, exact
  active-skill path wording, and refusal of mature or exhausted work.
- `plugins/hexaemeron/tests/test_fiat_skill.py` checks workflow requirements
  that sit around the controller, including publication and closure rules.
- `plugins/hexaemeron/.codex-plugin/plugin.json` is the checkout manifest; the
  installed cache carries the corresponding manifest and complete skill and
  test trees.

### Organisation evidence

- Wildcat Skills issue #74 defines the defect, scope, and acceptance criteria
  for independent Fiat frontiers, installed-path resolution, and maturity.
- Wildcat Skills PR #75 is the implementation and merge record for those
  rules. It is also the evidence cited by Fiat's existing evolution history.
- Commit `94c0b924d9ca07836216f18019d0cd8c7c8974e4` replaced stale PID-file
  recovery with a kernel-held lock and added real-process contention tests.
- Commit `60a01d4c6918e6d30b45da7677dcf6d63a936a3e` added the governed ledgers,
  maturity rules, active installed-path wording, and Kronos.

### External standards and packages

- Python `argparse`, `json`, `hashlib`, `tempfile`, and `unittest` are the
  controller and test-suite foundations. Python's `fcntl.flock` interface
  supplies advisory locking on this Unix host.
- JSON is standardised by RFC 8259. The controller narrows valid JSON to its
  own canonical form by sorting object keys and using fixed separators before
  hashing.
- SHA-256 is specified by NIST FIPS 180-4. Fiat uses it for tamper evidence,
  not identity, signing, or third-party provenance.

No other organisation repository is needed for this bounded job. The subject,
controller, tests, manifest, history, issue, and merged implementation all
live in `wildcat-finance/skills` or the installed copy derived from it.

## Constraints and non-goals

- The entry state is clean `main` at `60a01d4c6918e6d30b45da7677dcf6d63a936a3e`.
  The user named no alternate base.
- Controller transitions belong only to the primary Fiat agent. Research and
  drafting may read `.hexaemeron/state.json` and `.hexaemeron/ledger.jsonl`
  but must not receipt or advance them.
- The active controller, Fiat instructions, Imprimatur script, and any later
  Vulgate instructions must come from the exact installed plugin tree. The
  checkout is the target repository and the place where tracked delivery
  changes are made.
- `.hexaemeron/` is ignored by its own `.gitignore`. A tracked proof therefore
  needs a repository copy, while the live controller ledger remains the
  authority for transition order.
- Python 3 is the controller toolchain. The controller uses Unix-only
  `fcntl`, so this proof covers the current macOS host and does not establish
  native Windows behavior.
- The repository's `AGENTS.md` requires
  `python3 plugins/hexaemeron/tests/run_tests.py`,
  `python3 plugins/hexaemeron/skills/imprimatur/tests/run_tests.py`, and
  `python3 -m unittest discover -s tests` for the areas this delivery is
  expected to change. Changed skill directories also need Agent Skills
  frontmatter validation.
- The Solidity suite is out of scope. The live run records the reason for its
  waiver.
- No controller feature, plugin installation, marketplace expansion, GitHub
  issue creation, Pashov-vendored file change, or cross-plugin frontier change
  is required.
- This work does not authenticate the publisher, sign the cache, prove the
  cache's build pipeline, or turn Fiat's ledger into a general release
  attestation. Ariadne or an external signing verifier owns those jobs.
- The cache manifest's package version is recorded as observed. Its timestamp
  is not treated as proof of file creation time or source commit.

## Design options

### Option 1: One evidence-and-ledger delivery

Add one tracked proof under `plugins/hexaemeron/docs/`, copy the study's
evidence into it, update the Fiat ledger to `fiat-v2.2.0` and `mature`, update
the Fiat skill metadata to `2.2.0`, then run the required checks. The final
controller and GitHub receipts close the proof.

This option changes no controller behavior. It is the cheapest construction
to understand because the missing acceptance condition is an observed run,
not a missing feature. The proof is reviewable after `.hexaemeron/` is gone,
while the live ledger remains the transition authority during the run.

### Option 2: Teach `hexctl` to record `__file__` automatically

The controller could insert its executable path during `init`. That would
reduce one manual receipt, but `__file__` proves which Python file ran, not
that the caller correctly derived it from the active `SKILL.md`. It would add
a migration and new tests to solve a problem already covered by an explicit
receipt and this delivery.

### Option 3: Add a cache-path integration test

A test could copy the plugin to a synthetic cache directory, load the skill,
and invoke the adjacent controller against a separate target. This would be a
useful host-integration fixture if path resolution later became executable
code. Today path resolution is an agent instruction and the controller suite
already invokes the adjacent controller against temporary targets. A new
fixture would duplicate the shape without proving that an installed host
actually followed it.

### Option 4: Leave the frontier open for another delivery

This would retain the same held job or replace it with a packaging-attestation
job. Repeating the installed run would add interchangeable evidence after the
acceptance condition is met. Packaging provenance is a different boundary and
would change the target without the reopening evidence required by
`VERSIONING.md`.

### Decision

Choose option 1. The current run supplies the one missing fact, the installed
suite is green, and source inspection found no unresolved controller-path or
maturity failure. After this delivery reaches `done`, another Fiat frontier
pass has no concrete chance of improving the accepted behavior. Fiat should
therefore close as mature. A later failure, requirement, dependency change,
or equivalent external evidence may reopen it through an epoch entry.

The implementation should be one bounded step. It should add
`plugins/hexaemeron/docs/fiat-installed-path-and-maturity-proof.md`, update
only Fiat's ledger and metadata plus any required discoverability link, run
the required checks, and publish and merge one PR. The ledger history row must
retain revision `installed-path-and-maturity-proof`, use axis `evolution`, and
carry the SHA-256 of the new four-field frontier line defined by
`VERSIONING.md`.

## Risk register seed

| Risk | Why it matters | Check or control |
| --- | --- | --- |
| Wrong controller source | A checkout-relative `hexctl.py` would fail the held job even if the state looked valid. | Compare the state receipt with the exact installed path; use that path for every controller call. |
| Wrong target root | An installed controller without the explicit checkout `--dir` could write state under the plugin cache. | Keep `PROJECT_ROOT` explicit and confirm the only live state is this checkout's `.hexaemeron/`. |
| Receipt fabrication or drift | A prose report alone cannot establish phase order. | Treat the hash-chained live ledger and final `verify` result as primary; copy its non-secret facts into the tracked proof. |
| Installed/checkout mismatch | Tests against one copy may not describe the controller that ran. | Retain the observed SHA-256 comparisons and run tests from the installed tree; rerun checkout tests after changes. |
| Version-axis error | Closing a frontier on the generation or epoch axis would violate the contract. | Advance `fiat-v1.2.0` to `fiat-v2.2.0`; keep generation 2 and epoch 0; run `test_evolution.py`. |
| Frontier digest error | Hand-edited history can disagree with current fields. | Compute the exact newline-terminated canonical frontier line and let `test_current_frontier_digest_matches_latest_history_row` check it. |
| Premature closure | A real failing acceptance condition would make `mature` false. | Require the installed suite, repository checks, final controller `status` and `verify`, and a merged PR. Stop rather than close if any fails. |
| Manufactured continuation | A new job chosen only to keep Kronos running defeats the maturity rule. | Record `None -- mature`; reopen only on external evidence under `VERSIONING.md`. |
| Package-version ambiguity | Plugin package `1.0.0+codex.20260816145806` and skill `fiat-v1.2.0` look comparable but are not. | Name both namespaces and retain file hashes. |
| Platform scope | `fcntl.flock` does not establish native Windows support. | State the Unix/macOS scope; do not add a Windows claim. |
| External provenance overclaim | SHA-256 chains show later edits; they do not authenticate a publisher. | Keep signing and release-attestation claims out of scope. |

## Glossary seeds

- **Active skill file:** The exact installed `fiat/SKILL.md` whose instructions
  started this run.
- **Controller path:** The absolute path to the `hexctl.py` beside the active
  skill file.
- **Project root:** The target checkout passed through the controller's
  `--dir` argument.
- **Installed plugin:** The Hexaemeron directory under the Codex plugin cache,
  with its own manifest, skills, scripts, agents, and tests.
- **Receipt:** Structured evidence written into controller state and its next
  hash-chained ledger entry.
- **Ledger:** `.hexaemeron/ledger.jsonl`, an append-only sequence whose entry
  hashes bind each event to the prior entry and current state fingerprint.
- **Frontier:** A skill's current evidenced limit and its held next job.
- **Evolution:** The first skill-version counter, incremented once when a
  completed frontier job changes the held next job or closes it.
- **Generation:** The second skill-version counter, used for behavior changes
  that do not advance the held frontier.
- **Epoch:** The third skill-version counter, used only for a provenance or
  compatibility boundary, including an evidenced mature-frontier reopening.
- **Mature:** Terminal frontier state with no held next job; further frontier
  Fiat runs are refused until external evidence reopens an epoch.
- **Tracked proof:** The repository document that preserves the installed-run
  facts after ignored controller state is no longer locally available.

## Sources

### Repository and installed sources

- `AGENTS.md` and `plugins/hexaemeron/AGENTS.md` at commit
  `60a01d4c6918e6d30b45da7677dcf6d63a936a3e`.
- `plugins/hexaemeron/skills/fiat/SKILL.md`, `EVOLUTION.md`,
  `references/study.md`, and `scripts/hexctl.py` at the same commit.
- `plugins/hexaemeron/skills/VERSIONING.md` at the same commit.
- `plugins/hexaemeron/tests/run_tests.py`, `test_hexctl.py`,
  `test_evolution.py`, and `test_fiat_skill.py` at the same commit.
- `plugins/hexaemeron/.codex-plugin/plugin.json` and the corresponding files
  under
  `/Users/c0rtexzer0/.codex/plugins/cache/wildcat-labs/hexaemeron/1.0.0+codex.20260816145806/`.
- `.hexaemeron/state.json` and `.hexaemeron/ledger.jsonl`, read during the
  study without advancing the controller.
- Git history for commits `3fbb9fb060c9d355f6c1f3ced4c7cfd340a26ea8`,
  `94c0b924d9ca07836216f18019d0cd8c7c8974e4`, and
  `60a01d4c6918e6d30b45da7677dcf6d63a936a3e`.

### GitHub evidence

- [Issue #74: Refactor Hexaemeron subsidiary frontiers and add governed skill version histories](https://github.com/wildcat-finance/skills/issues/74).
- [PR #75: Govern Hexaemeron frontiers and add Kronos](https://github.com/wildcat-finance/skills/pull/75).

### External specifications

- [Python `fcntl` documentation](https://docs.python.org/3/library/fcntl.html#fcntl.flock).
- [Python `hashlib` documentation](https://docs.python.org/3/library/hashlib.html).
- [RFC 8259: The JavaScript Object Notation Data Interchange Format](https://www.rfc-editor.org/rfc/rfc8259).
- [NIST FIPS 180-4: Secure Hash Standard](https://csrc.nist.gov/pubs/fips/180-4/upd1/final).
