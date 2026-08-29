# Runbook: gate durable agent prose before publication

This run starts at `dd23413ef6e9021bd80b930ad57e1766bf166f0b`. Each
step uses the exact branch and parent emitted by `hexctl next`. Every local
commit is signed, locally verified, authored under the repository's Shoggoth
rule, and carries each required provenance trailer once. Every pushed commit
must report GitHub verification `verified: true` with reason `valid` before a
merge.

## Step 1: Define the durable-record contract and issue publication rule

**Goal.** Give Sapheneia one bounded operation for agent-authored audit records,
GitHub issue submissions, and GitHub issue comments; publish the ordered root
rule that composes it with Imprimatur and Vulgate.

**Entry.** Exact base `dd23413ef6e9021bd80b930ad57e1766bf166f0b`; the
receipted study is Protasis-clean and Imprimatur-clean; current Sapheneia is
`sapheneia-v0.1.0` with frontier revision `cross-model-corpus`; plugin package
version is `0.1.1`; issues #421, #501, #427, #372, and #373 remain open; root,
Sapheneia, Promise Machine, evolution, and version tests pass before the branch
is cut.

**Exit.** `sapheneia-durable-record-shape` governs only the three named durable
surfaces and does not activate session-wide shaping. Its checklist preserves
the complete evidence inventory and owning host structure while allowing only
claim-neutral compression. Runtime, router, README, host metadata, Promise
fixtures, and coverage agree. Root `AGENTS.md` freezes all four issue-queue
title forms and required body structure before the ordered Sapheneia,
Imprimatur, Vulgate, Imprimatur re-lint sequence. It states that GitHub does not
enforce the rule. The tracked study and runbook equal the receipted sources;
ADR-017 records the chosen declaration-and-policy boundary. Sapheneia advances
to `sapheneia-v0.2.0` as a generation with its frontier revision, digest,
status, and Next Fiat job unchanged; package version `0.1.2` agrees across both
host manifests and both marketplaces. Horos is current. Red-before-fix tests
first show the missing promise and publication rule, then all focused and root
checks pass. Prove it with:

```bash
cmp .hexaemeron/study.md docs/durable-agent-prose-gates/study.md
cmp .hexaemeron/runbook.md docs/durable-agent-prose-gates/runbook.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/durable-agent-prose-gates/study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/durable-agent-prose-gates/runbook.md
python3 -m unittest discover -s plugins/sapheneia/tests -t plugins/sapheneia
python3 -m unittest tests.test_promise_machine_contract tests.test_marketplace_prose tests.test_evolution_contract tests.test_version_propagation
python3 scripts/promise_machine.py check
python3 plugins/horos/skills/horos/scripts/horos.py scan . --write
python3 plugins/horos/skills/horos/scripts/horos.py check .
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py AGENTS.md .agents/skills/promise-machine/SKILL.md plugins/sapheneia/AGENTS.md plugins/sapheneia/README.md plugins/sapheneia/skills/sapheneia/SKILL.md plugins/sapheneia/skills/sapheneia/EVOLUTION.md docs/decisions/ADR-017-gate-durable-agent-prose.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py AGENTS.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py plugins/sapheneia/AGENTS.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py plugins/sapheneia/README.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py plugins/sapheneia/skills/sapheneia/SKILL.md
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
python3 -m unittest discover -s tests
git diff --check
git verify-commit <each-local-commit-sha>
test "$(git show -s --format=%B <each-local-commit-sha> | grep -Fxc 'Co-authored-by: Shoggoth <shoggoth@wildcat.finance>')" -eq 1
test "$(git show -s --format=%B <each-local-commit-sha> | grep -Fxc 'Wildcat-Origin: shoggoth')" -eq 1
```

**Files.** `AGENTS.md`; `.agents/skills/promise-machine/SKILL.md`;
`plugins/sapheneia/AGENTS.md`; `plugins/sapheneia/README.md`;
`plugins/sapheneia/skills/sapheneia/SKILL.md`;
`plugins/sapheneia/skills/sapheneia/EVOLUTION.md`;
`plugins/sapheneia/skills/sapheneia/agents/openai.yaml`;
`plugins/sapheneia/tests/test_sapheneia.py`;
`plugins/sapheneia/tests/fixtures/promise-machine/cases.json`;
`plugins/sapheneia/.claude-plugin/plugin.json`;
`plugins/sapheneia/.codex-plugin/plugin.json`;
`.claude-plugin/marketplace.json`; `.agents/plugins/marketplace.json`;
`tests/promise_machine_coverage.json`; `tests/test_promise_machine_contract.py`;
`tests/test_marketplace_prose.py`; `tests/test_version_propagation.py`;
`docs/durable-agent-prose-gates/study.md`;
`docs/durable-agent-prose-gates/runbook.md`;
`docs/decisions/ADR-017-gate-durable-agent-prose.md`;
`.horos/boundary.json`; and `audit/AUDIT.md` only when the audit round is
recorded.

**Tests.** Extend Sapheneia contract and Promise fixtures with positive,
missing-evidence, wrong-subject, overclaim, and recovery cases. Assert that the
portable router reaches the new durable-record operation and that root
instructions name the three surfaces, all four queue forms, the exact pass
order, protected evidence, and the GitHub enforcement boundary. Add the new
promise id to both coverage authorities. Check the skill generation and package
version independently. Capture focused failures before implementation, then run
the focused, root, Promise Machine, Protasis, prose, tree, version, and Horos
checks above. Verify every local commit and both trailers; after push, check
each exact GitHub SHA.

**Disciplines.** protasis: the receipted study fixes the three surfaces and the
non-goals. phylax: no network or subprocess publisher is added; protected
content is the trust boundary. ephoros: no unattended runtime exists, so tests
and explicit boundary text are the useful signals. metron: none, no performance
claim. elenchus: missing promise, route, queue protection, and package agreement
begin as focused failing tests. hypomnema: ADR-017 holds the cross-plugin
decision; the Sapheneia generation row holds its contract change; study and
runbook remain run inputs.

## Step 2: Gate Fiat audit receipts and task-issue comments

**Goal.** Make every new Fiat audit round declare the bounded Sapheneia pass,
and route Fiat's task-issue closing comment through the repository's ordered
publication rule.

**Entry.** Step 1's signed head; tracked study and runbook still match their
receipts; Sapheneia's new promise and root publication rule are green; current
Fiat is `fiat-v5.13.1` with frontier revision `receipted-lint-rounds`; current
Hexaemeron package version is `1.5.6`; PR #509 is still treated as an external
overlap and its schema work is not copied.

**Exit.** Every audit-round directive and Warden packet names
`--audit-filter sapheneia:sapheneia`. `audit-round` refuses a missing or
different value before state or ledger mutation, then records the accepted
identifier in the round receipt and hash-chained event. The audit-loop reference
defines the compact, evidence-preserving Sapheneia pass before append and calls
the flag an operator declaration rather than semantic proof. Fiat's final
task-issue comment is drafted during the prose work, preserves the issue URL,
PR URL, identifiers, status, and any unresolved work, passes Sapheneia,
Imprimatur, Vulgate, then an Imprimatur re-lint, is posted verbatim, and is read
back before closure is reported. Tests hold the audit obligation and the
comment instructions. Fiat advances to `fiat-v5.14.1` as a generation with its
frontier revision, digest, status, and Next Fiat job unchanged. Hexaemeron
package version `1.5.7` agrees across both host manifests and both marketplaces.
The checked-in controller proves the new gate against the active run state. If
PR #509 or another main change lands first, rebase, reconcile the combined
audit grammar and declarations, advance versions from the new base, and rerun
every check. Red-before-fix tests become green, all repository and plugin gates
pass, and every local and remote signature is valid. Prove it with:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_hexctl plugins.hexaemeron.tests.test_fiat_skill plugins.hexaemeron.tests.test_evolution
python3 -m unittest tests.test_evolution_contract tests.test_marketplace_prose tests.test_version_propagation tests.test_promise_machine_contract
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s plugins/sapheneia/tests -t plugins/sapheneia
python3 -m unittest discover -s tests
python3 scripts/promise_machine.py check
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/durable-agent-prose-gates/study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/durable-agent-prose-gates/runbook.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/agents/warden.md plugins/hexaemeron/skills/fiat/SKILL.md plugins/hexaemeron/skills/fiat/EVOLUTION.md plugins/hexaemeron/skills/fiat/references/audit-loop.md plugins/hexaemeron/skills/fiat/references/prose-pass.md plugins/hexaemeron/skills/fiat/references/push-discipline.md plugins/hexaemeron/README.md plugins/hexaemeron/AGENTS.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py plugins/hexaemeron/agents/warden.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py plugins/hexaemeron/skills/fiat/SKILL.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py plugins/hexaemeron/skills/fiat/references/audit-loop.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py plugins/hexaemeron/skills/fiat/references/prose-pass.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py plugins/hexaemeron/skills/fiat/references/push-discipline.md
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
python3 plugins/horos/skills/horos/scripts/horos.py scan . --write
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
python3 plugins/hexaemeron/skills/fiat/scripts/hexctl.py --dir . verify
git verify-commit <each-local-commit-sha>
test "$(git show -s --format=%B <each-local-commit-sha> | grep -Fxc 'Co-authored-by: Shoggoth <shoggoth@wildcat.finance>')" -eq 1
test "$(git show -s --format=%B <each-local-commit-sha> | grep -Fxc 'Wildcat-Origin: shoggoth')" -eq 1
gh api repos/wildcat-finance/skills/commits/<each-pushed-or-github-merge-sha> --jq '.commit.verification | select(.verified == true and .reason == "valid")'
```

**Files.** `plugins/hexaemeron/agents/warden.md`;
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py`;
`plugins/hexaemeron/skills/fiat/SKILL.md`;
`plugins/hexaemeron/skills/fiat/EVOLUTION.md`;
`plugins/hexaemeron/skills/fiat/references/audit-loop.md`;
`plugins/hexaemeron/skills/fiat/references/prose-pass.md`;
`plugins/hexaemeron/skills/fiat/references/push-discipline.md`;
`plugins/hexaemeron/skills/fiat/agents/openai.yaml`;
`plugins/hexaemeron/tests/test_hexctl.py`;
`plugins/hexaemeron/tests/test_fiat_skill.py`;
`plugins/hexaemeron/tests/test_evolution.py`;
`plugins/hexaemeron/README.md`; `plugins/hexaemeron/AGENTS.md`;
`plugins/hexaemeron/.claude-plugin/plugin.json`;
`plugins/hexaemeron/.codex-plugin/plugin.json`;
`.claude-plugin/marketplace.json`; `.agents/plugins/marketplace.json`;
`tests/test_marketplace_prose.py`; `tests/test_version_propagation.py`;
`tests/test_evolution_contract.py`; `tests/promise_machine_coverage.json` if the
Fiat Promise wording changes; `.horos/boundary.json`; and `audit/AUDIT.md` when
audit rounds are recorded.

**Tests.** Add focused CLI cases for missing, wrong, and exact audit-filter
values; unchanged state and ledger after refusal; receipt and ledger retention;
deterministic `next` and Warden packet fields; and compatibility with clean,
finding, fix, non-Solidity, and legacy-state paths. Add prose-contract cases for
the ordered task-issue comment path, protected content, verbatim publication,
and remote readback without claiming controller attestation. Capture each
missing guard as a failing test before the change. Run the checked-in controller
against a temporary copy of the active state to prove the new required flag
without corrupting the installed-controller ledger. Run all focused, root,
Hexaemeron, Sapheneia, Promise Machine, Protasis, prose, tree, evolution,
version, Horos, controller, signature, and GitHub checks above.

**Disciplines.** protasis: the exact declaration, receipt boundary, and
publication sequence come from the accepted study. phylax: one bounded CLI
value is added; no audit prose, credential, shell, or network input enters the
controller. ephoros: `next`, Warden brief, refusal text, state, and ledger name
the obligation without printing record content. metron: none, one constant
comparison and receipt field carry no performance claim. elenchus: missing and
wrong declarations, state drift, packet omission, and comment-path omissions
start as red guards and close at their causes. hypomnema: audit-loop and push
discipline own the operating rules, Fiat's generation row owns the controller
change, and ADR-017 remains the cross-plugin decision home.
