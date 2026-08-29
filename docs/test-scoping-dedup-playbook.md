# Test-scoping de-duplication playbook

Extricate the repo-wide test invariants that have been copied into individual
plugin suites, without losing the "fail locally first" property the plugin
authors deliberately built. One shared assertion helper becomes the single
source of truth; the root suite and any plugin suite that wants a local echo
both call it.

This is a checklist to work through, plugin by plugin, in order. Nothing here
deletes real coverage -- assertions **move into one helper** and are still
executed in both the root loop and the plugin call.

---

## 1. Scope

**In scope.** The four repo-wide invariants copied into plugin suites:

1. Promise-machine router reaches the plugin's `AGENTS.md`.
2. Host-description parity (`.claude-plugin` == `.codex-plugin` == codex
   `interface.shortDescription`, length 25--64).
3. Three-manifest version agreement (+ exact pin).
4. Marketplace entry uses the local `./plugins/<name>` source path.

**Out of scope (tracked separately, do not fold into this pass):**

- **Cross-component reach** -- e.g. `alexandria/tests/test_index.py` running the
  Probitas CLI end-to-end, `tabularium/tests/test_compound_witness.py`
  rebuilding Alexandria's release, `lazarus/tests/test_goldfinch.py:44`
  reading a Tabularium fixture. That is a different fix (own-the-artifact /
  anchor-to-digest), covered in §6b.
- **hexaemeron checker whole-tree walks** (`ephoros`, `phylax`, `hypomnema`) --
  §6a. Related mess, separate mechanism.
- **Deliberate inverse-invariants** -- do not touch (§3, bucket D).

---

## 2. The mechanism: one shared repo-contract helper

### 2a. Where it lives (and the collision to avoid)

Each plugin suite runs with its own top-level import root
(`discover -s plugins/X/tests -t plugins/X`), so inside a plugin run the name
`tests` resolves to **that plugin's** `tests/` package, not the repo-root one.
Six plugins already ship a `plugins/X/tests/support.py`
(alexandria, brevitas and sapheneia compute `REPO_ROOT` inline instead).

Therefore the helper **must not** live under any package named `tests`, or the
import will bind to the wrong one depending on how the suite was launched. Put
it at a uniquely-named top-level path:

```
<repo>/repo_contract.py
```

Every caller already computes `REPO_ROOT`. Import rule, identical everywhere:

```python
import sys
sys.path.insert(0, str(REPO_ROOT))   # REPO_ROOT = the repo root Path
from repo_contract import (
    assert_router_reaches,
    assert_host_descriptions_agree,
    assert_version_agreement,
    assert_marketplace_source_path,
)
```

The six `tests/support.py` modules already manipulate `sys.path`; add the
`REPO_ROOT` insert there so their tests import `repo_contract` for free. For
the three inline plugins, add the two lines in the test module.

### 2b. The API

Each function takes the plugin name and asserts one invariant, reading the same
files the root suite reads. Signatures and what each subsumes:

```python
def assert_router_reaches(test, name):
    """Promise-machine router links to plugins/<name>/AGENTS.md, and that
    contract references skills/<name>/**/SKILL.md. Subsumes root
    tests/test_portable_skills.py:45-69."""

def assert_host_descriptions_agree(test, name):
    """claude description == codex description == codex interface
    shortDescription, 25 <= len <= 64. Subsumes root
    tests/test_marketplace_prose.py:117-131."""

def assert_version_agreement(test, name, expected=None):
    """Both host manifests and the marketplace entry carry one version; if
    `expected` is given, it equals that. Subsumes root
    tests/test_version_propagation.py."""

def assert_marketplace_source_path(test, name):
    """Both marketplaces point the entry at ./plugins/<name>. NOT currently in
    root -- see §7; add it to the root loop when you land this."""
```

Pass the `TestCase` in (`test`) so failures report through the caller's own
suite. The root suite calls each in a loop over all 14 plugins; a plugin suite
calls it once for itself.

---

## 3. Buckets (how to classify every method you touch)

- **A -- pure duplicate.** Replace the whole method body with one helper call.
- **B -- hybrid.** Split: route the repo-wide assertion to the helper, keep the
  plugin-local assertion in place. Never delete the local half.
- **C -- local-unique.** Leave untouched.
- **D -- deliberate inverse-invariant.** Leave untouched, and add a one-line
  comment tagging it so a future cleanup pass does not "fix" it. These assert
  that the package version *differs* from the skill version -- the opposite of a
  copy.

---

## 4. Migration order (safest first)

1. Write `repo_contract.py` with brevitas + sapheneia as first consumers
   (pure bucket-A, two calls each -- smallest blast radius).
2. Adopt it in the root suite loop (prove the loop still passes for all 14).
3. alexandria → tabularium → probitas (mixed A/B).
4. lazarus (heavy local nuance; one D case).
5. berean last (carries the explicit "fail locally first" docstring; most care).
6. Then the separate fixes: §6a hexaemeron walks, §7 root corrections, §8 CI.

Run the verification protocol (§9) after every numbered step, not just at the end.

---

## 5. Per-plugin checklists

### 5a. brevitas -- `plugins/brevitas/tests/test_brevitas.py`

| method | line | bucket | action |
|---|---|---|---|
| 19 `test_*` linter behaviour tests | 33--119 | C | keep |
| `test_host_descriptions_remain_identical` | 121 | A | → `assert_host_descriptions_agree(self, "brevitas")` |
| `test_promise_machine_router_reaches_the_runtime_contract` | 133 | A | → `assert_router_reaches(self, "brevitas")` |

No `support.py`; add the import shim inline (uses `ROOT`).

### 5b. sapheneia -- `plugins/sapheneia/tests/test_sapheneia.py`

| method | line | bucket | action |
|---|---|---|---|
| `test_ranked_contract_has_exactly_ten_rules` | 13 | C | keep |
| `test_contract_applies_to_agent_replies_and_persists` | 18 | C | keep |
| `test_host_descriptions_remain_identical` | 25 | A | → helper |
| `test_promise_machine_router_reaches_the_runtime_contract` | 39 | A | → helper |

No `support.py`; add the import shim inline (uses `ROOT`).

### 5c. alexandria -- `plugins/alexandria/tests/test_scaffold.py`

| method | line | bucket | action |
|---|---|---|---|
| CLI help / usage / error tests (6) | 29--73 | C | keep |
| `test_skill_is_canonical_and_has_no_browsable_readme_shadow` | 75 | C | keep (no-shadow rule not in root) |
| `test_skill_frontmatter_matches_its_directory` | 79 | B | drop `name == dir` (root owns); keep `"Raw release and registered"` substring |
| `test_package_metadata_agrees_and_points_at_the_skill` | 87 | B | version + `name` → `assert_version_agreement(self, "alexandria", "0.2.1")`; keep `skills == "./skills/"` |
| `test_promise_machine_router_resolves_to_runtime_contract` | 108 | A | → `assert_router_reaches` |
| `test_marketplaces_use_the_local_plugin_path` | 117 | A | → `assert_marketplace_source_path` |
| `test_design_records_are_committed` | 129 | C | keep (runbook digest pin) |
| `test_scaffold_directories_and_licence_are_present` | 137 | C | keep |
| `test_all_plugin_json_files_parse` | 151 | C | keep |
| `test_tabularium_schema_defines_mapping_coverage_and_counts` | 158 | E | defer (§6b) -- own schema, cross-consumer |

No `support.py`; add the import shim inline (uses `REPO_ROOT`).

### 5d. tabularium -- `plugins/tabularium/tests/test_scaffold.py`

| method | line | bucket | action |
|---|---|---|---|
| `test_help_names_both_commands` | 27 | C | keep |
| `test_verify_help_requires_a_coverage_manifest` | 36 | C | keep |
| `test_skill_is_canonical_and_has_no_browsable_readme_shadow` | 42 | C | keep |
| `test_package_metadata_agrees_and_points_at_the_skill` | 46 | B | version+repository+description → helpers (`assert_version_agreement`, `assert_host_descriptions_agree`); keep skills-path check |
| `test_public_documents_and_audit_log_are_present` | 72 | C | keep |
| `test_public_document_links_resolve_inside_the_plugin` | 84 | C | keep (VERSIONING.md allowance is fine) |
| `test_marketplace_entries_use_the_local_plugin_path` | 102 | B | source path → `assert_marketplace_source_path`; description parity → `assert_host_descriptions_agree` |
| `test_compound_spec_fails_closed_and_keeps_collection_offline` | 120 | C | keep |

Has `support.py` -- add `REPO_ROOT` shim there.

### 5e. probitas -- `plugins/probitas/tests/test_manifests.py`

| method | line | bucket | action |
|---|---|---|---|
| `test_both_manifests_parse_and_name_the_plugin` | 56 | B | `name` subsumed by root; keep the parse as a cheap local smoke check or drop to one call |
| `test_package_versions_agree_without_moving_the_skill` | 61 | B+D | agreement → `assert_version_agreement(self, "probitas", "0.1.1")`; **keep** the `0.1.1 != skill 0.1.0` inequality (D -- tag it) |
| `test_codex_manifest_carries_an_interface` | 70 | C | keep (interface field presence) |
| `test_skills_path_exists` | 82 | B | fold into helper (skills-path invariant) or keep local |
| `test_marketplace_entries_point_at_the_plugin` | 90 | B | presence subsumed; source dir exists → `assert_marketplace_source_path` |
| `test_skill_description_states_when_to_trigger` | 103 | C | keep (`Use when` / `Do not use`) |

Has `support.py`.

### 5f. lazarus -- `plugins/lazarus/tests/test_scaffold.py`

| method | line | bucket | action |
|---|---|---|---|
| `test_host_manifests_parse_and_agree` | 12 | B | name/skills/version/description → helpers; **keep** `license == "MIT"` |
| `test_the_host_manifests_follow_the_package_and_not_the_skill_or_writer` | 22 | **D** | keep + tag (package ≠ skill ≠ `__version__`) |
| `test_the_writer_version_is_the_one_the_fixture_records` | 44 | C | keep (fixture provenance) |
| `test_skill_is_canonical_and_has_no_readme_shadow` | 53 | C | keep |
| `test_promise_machine_router_reaches_the_runtime_contract` | 57 | B | router → `assert_router_reaches`; **keep** alias checks (`/lazarus:lazarus`, `$lazarus`) |
| `test_runtime_contract_documents_planned_entrypoints_and_boundaries` | 67 | C | keep |
| `test_requirements_are_exact_direct_pins` | 76 | C | keep |
| `test_transitive_runtime_environment_is_locked` | 87 | C | keep |
| `test_reviewed_design_documents_are_committed` | 102 | C | keep |
| `test_cli_and_step_five_modules_exist` | 110 | C | keep |

Has `support.py`. Lazarus is mostly local -- expect only two routed assertions.

### 5g. berean -- `plugins/berean/tests/test_scaffold.py`

Read the module docstring first; it defends the local echoes. The helper
preserves that property (the calls still fail in berean's own run), so the
docstring stays true -- update its wording to say the echo now routes through
`repo_contract`.

| method | line | bucket | action |
|---|---|---|---|
| `PackagingTests.test_pinned_release_corpora_are_not_fuzzer_output` | 30 | C | keep |
| `ManifestTests.test_the_three_manifests_agree` | 51 | B | version → `assert_version_agreement(self, "berean", "0.1.1")`; description parity → `assert_host_descriptions_agree` |
| `test_the_openai_interface_carries_the_same_description` | 67 | C | keep (openai.yaml is a 4th surface, not in root -- or extend the helper to cover it repo-wide) |
| `LedgerTests.test_the_ledger_digest_reproduces` | 93 | C | keep (local digest reproduction) |
| `test_the_skill_version_matches_the_ledger` | 112 | B | ledger↔skill version equality overlaps root `test_evolution_contract`; keep only the berean-specific reproduction or route |
| `FrontierTests.test_every_marketplace_block_carries_the_same_frontier` | 123 | B | overlaps root marketplace-prose frontier agreement; keep as a local subtree check or route |

---

## 6. Related messes (separate mechanisms, same effort)

### 6a. hexaemeron checker whole-tree walks

`ephoros`, `phylax`, `hypomnema` each contain an "the shipped tree is clean"
unit test that walks the entire `plugins/`(+`docs/`) tree and asserts zero
findings -- so touching hexaemeron re-audits all 13 siblings.

- `plugins/hexaemeron/tests/test_ephoros_checker.py:295`
- `plugins/hexaemeron/tests/test_phylax_checker.py:341`
- `plugins/hexaemeron/tests/test_hypomnema_checker.py:352` **and** `:557`
  (a redundant pair -- same walk target, same assertion; fold into one)

Action: move the whole-tree "shipped tree is clean" assertions into **one
repo-wide lint job** (a single `tests/` case, or a dedicated CI workflow
path-gated to `plugins/**` + `docs/**`). Keep each checker's behaviour tests on
their local fixtures. Rewrite `hypomnema` `:471` (the fixture-skip proof)
against a synthetic tempdir instead of the live tree.

### 6b. cross-component byte re-verification

Move each "rebuild/verify a sibling's release" test to the plugin that owns the
artifact, or re-anchor it to a recorded digest instead of a live sibling
rebuild:

- `alexandria/tests/test_index.py:426-471` (runs Probitas end-to-end) → Probitas suite.
- `tabularium/tests/test_compound_witness.py:113-144` (rebuilds Alexandria) → Alexandria suite.
- `lazarus/tests/test_goldfinch.py:44-54` (reads a Tabularium fixture) → assert against a digest.
- `berean`/`ariadne` → lazarus reads are already `skipTest`-guarded; re-anchor to a digest.

---

## 7. Root-suite corrections

Two plugin-specific checks are sitting in the root suite and fire on every
gated change to any plugin -- the inverse of the plugin-side mess. Move them down:

- `tests/test_marketplace_prose.py:276` (pandects law counts) → `plugins/pandects/tests`.
- `tests/test_marketplace_prose.py:317` (lazarus release-README digest) → `plugins/lazarus/tests`.

When `assert_marketplace_source_path` lands, add a root case that loops it over
all 14 plugins (it is not currently a repo-wide invariant, only a per-plugin one).

Path-gate the pure prose/metadata invariants so a Solidity-only change does not
run them: `test_marketplace_prose`, `test_shipped_prose_lints` should be tied to
`**/*.md`; `test_version_propagation`, `test_evolution_contract` to manifests
and `EVOLUTION.md`. `test_boundary_currency` and `test_portable_skills` stay
always-on (code-sensitive / cheap structural).

---

## 8. CI corrections

- **Double-run.** `janus.yml`, `lazarus.yml`, `pandects.yml` run the full root
  suite first, then the plugin suite. Once plugin suites stop re-asserting the
  repo-wide invariants (this playbook), the double-run is no longer wasteful --
  but also split the whole-repo invariant suite into its own workflow so it is
  not a side-effect of whichever of the three code plugins happened to change.
- **Ungated plugins.** alexandria, ariadne, berean, brevitas, hermes, horos,
  lemma, probitas, sapheneia, tabularium have no CI workflow -- their suites
  (and the root invariants) only run under the manual AGENTS.md rule. A single
  repo-wide workflow that runs the root suite on any `plugins/**` change closes
  that gap and makes the per-plugin echoes unnecessary for CI purposes.
- **pandects `corpus` forge job** fires on every pandects change including
  doc-only edits -- path-gate it to `plugins/pandects/**/*.sol` + catalogue.

---

## 9. Verification protocol (run after every step in §4)

1. **Baseline once, before touching anything:**
   ```bash
   python3 -m unittest discover -s tests
   python3 -m unittest discover -s plugins/<X>/tests -t plugins/<X>
   ```
   Record pass counts per suite.
2. **After the helper lands and root adopts it:** the root suite pass count is
   equal or higher (the loop now runs the routed assertions for all 14).
3. **After each plugin edit:** run *that* plugin suite **and** the root suite.
   The plugin suite's count drops only by the number of assertions you routed
   (they now execute inside the helper call, so net executed assertions are
   preserved); the root suite is unchanged.
4. **No net coverage loss check:** every assertion removed from a plugin file
   appears either (a) in `repo_contract.py`, called by both root and that
   plugin, or (b) already in the root suite for all plugins. If neither, it was
   bucket C/D and must not have been removed -- restore it.
5. Confirm the frontmatter of every changed skill still validates and that the
   AGENTS.md `Suites` block still lists each plugin suite.

---

## 10. Rollout checklist

Status: the core de-duplication (helper + root adoption + all 7 plugins) and
the §7 test moves are done and green on branch `fiat/test-scoping-dedup`. The
remaining items (§6a, §6b, and the CI/path-gating parts of §7--§8) are not yet
started.

- [x] `repo_contract.py` written at repo root, four functions, import rule documented in-file.
- [x] Root suite routes host-description, version, and (new) source-path through the helper over all 14 plugins. Router stays the root set-equality check (stronger); the helper's per-plugin router check is for plugin suites.
- [x] brevitas, sapheneia (pure A) routed and green.
- [x] alexandria, tabularium, probitas (A/B) routed/split and green.
- [x] lazarus routed; the one D case left intact (its own docstring is the tag).
- [x] berean routed; docstring updated; D/inverse cases untouched.
- [x] §7 test moves: pandects law-counts → `plugins/pandects/tests/test_prose_counts.py`; lazarus example digest → `plugins/lazarus/tests/test_example_readme_digest.py`; source-path invariant added to the root loop.
- [x] §7 remainder: the repo-wide invariant suite now lives in its own workflow (§8). Per-test-type path-gating within one unittest suite is not native to GitHub Actions and the suite is cheap, so it runs as a unit rather than being split further.
- [x] §6a hexaemeron whole-tree walks moved to tests/test_shipped_tree_lints.py; hypomnema pair folded; fixture-skip proof rewritten as a tempdir. (PR #666)
- [x] §6b lazarus's orphaned tabularium peek removed; tabularium/alexandria/berean/ariadne couplings determined inherent or skipTest-guarded and left, with reasoning. (PR #666)
- [x] §8 CI: repo.yml runs the invariant suite on any plugin/tests/meta/docs change (closes the 10-plugin ungated gap and ends the janus/lazarus/pandects double-run); forge split into janus-forge.yml and pandects-forge.yml, each gated to Solidity paths.
- [x] Verification green for the landed work; no bucket-C/D assertion lost (root 104→103, pandects 116→117, all touched suites pass; lazarus/berean pre-existing dependency failures confirmed unrelated).
