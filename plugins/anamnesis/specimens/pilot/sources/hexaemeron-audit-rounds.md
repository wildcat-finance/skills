# Audit log: the plugin itself

<!-- marketplace-context:start -->
> **Record status.** This is a historical audit record; findings and dispositions below are preserved as evidence. Hexaemeron runs an explicit, receipted delivery loop and also exposes its fuzzing, audit-readiness, security-review and prose skills on their own. Use Hermes for measured gas work, Pandects for reviewed credit laws, and Lemma when the output needed is source-linked retrieval chunks. **Current frontier:** The bundled Solidity audit suite has not yet been exercised in a published end-to-end Fiat delivery.
<!-- marketplace-context:end -->

Day-5 treatment applied to hexaemeron's own executable surfaces before
shipping: `hexctl.py` (the controller), `imprimatur.py` (the vendored
lint), and `hook_gate.py` (the optional write hook). The vendored Pashov
suite targets Solidity and was not in this environment when round 1 ran;
the tool that did run is a purpose-built fuzz harness (four generators:
controller grammar sequences, ledger/state tamper soundness, adversarial
lint inputs, adversarial hook payloads) plus a manual read of every code
path. What ran is exactly what is claimed here, nothing else.

## Step 0 (the plugin), round 1 -- 15 August 2026

Coverage: 300 random command sequences, 120 single-byte ledger flips, 5
hand-edits of `state.json`, 150 adversarial lint inputs (binary, invalid
UTF-8, 60k-char lines, 30k backticks, pattern-bait sweeps), 200 hook
payloads, plus 20 targeted probes at file-parsing and config-poisoning
paths the grammar generator cannot reach.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| F-01 | medium | hexctl.py | `verify` proved the ledger chain but not the state: five hand-edits of `state.json` (skip the audit close, forge a waiver, swap the voice skill, erase rounds, alter findings) all passed, against the documented claim | fixed: every ledger entry now carries a fingerprint of the state it committed; `verify` recomputes and compares |
| F-02 | medium | hook_gate.py | non-dict payload or non-dict `tool_input` raised AttributeError, exit 1 -- outside the 0/2 hook contract and the file's own "never break the session" promise | fixed: shape guards plus a fail-open wrapper around extraction |
| F-03 | low | hexctl.py | corrupt `state.json` produced a raw traceback on every command | fixed: clean exit-1 diagnosis |
| F-04 | low | hexctl.py | corrupt or hashless ledger line produced tracebacks in both append and `verify` instead of "chain broken at line i" | fixed in both paths |
| F-05 | low | hexctl.py | `done runbook` with an existing but invalid steps JSON file produced a traceback | fixed: clean exit-2 with the parse error |
| F-06 | low | hexctl.py | non-integer `audit.max_rounds` crashed `audit-round`; zero wedged the step (round refused as over-cap, close refused as round-less) with contradictory `next` directives | fixed: one validated read, integer >= 1 enforced with a plain error |
| F-07 | low | hexctl.py | non-string configured skill ids crashed the `done prose` error path | fixed: ids coerced to strings before comparison |
| F-08 | low | hexctl.py | blank step titles were accepted; control characters in titles reached the terminal raw through `status` | fixed: blank titles refused, control characters stripped on display |
| F-09 | low | hexctl.py | `record` could shadow the `study` and `runbook` phase receipts in the shared namespace (ledger-visible, but a footgun) | fixed: those keys reserved to their `done` commands |
| F-10 | info | hook_gate.py | fail-open on malformed JSON and on an `imprimatur:ignore-file` marker inside written content -- a draft can exempt itself from the hook (not from the workflow's explicit lint) | accepted: documented escape hatches; the alternative is a hook that can block every write in a session |

Also verified clean in round 1: the grammar surface (no tracebacks, exit
codes within contract across all 300 sequences), tamper soundness on the
ledger (120/120 flips detected), `verify` green after every successful
mutation, and the lint under every adversarial input including a bounded
runtime check against pattern backtracking (no input exceeded the 12s
guard).

Fixes: applied in place with 9 regression tests pinning F-01 through F-09
(suite grew 23 to 32). No stacked branch exists because the plugin is not
yet a git repository; the fixes and this log ship in the same artefact.

Leads not pursued: `os.replace` atomicity across filesystems if a user
symlinks the state directory elsewhere (self-created directory, judged not
worth a round); timing of concurrent hexctl invocations against one state
dir (the loop is single-driver by design); ANSI passthrough via
`status --json` (JSON output is machine-facing by contract).

## Step 0 (the plugin), round 2 -- 15 August 2026

Same four harnesses plus the regression suite against the fixed tree, after
the Pashov suite was vendored and the entry skill renamed.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

All five state-edit probes and all ledger flips detected; no tracebacks on
any surface; hook exits confined to 0/2; controller suite 32/32; vendored
lint suite 55/55. One round-1 harness defect was found and fixed during
verification (its fifth state edit wrote the value already present, a
no-op the content fingerprint rightly ignores).

Leads not pursued: the vendored Pashov skills themselves were not
exercised against this plugin -- they audit Solidity and the plugin is
Python; their first real outing is the first run with Solidity in it.
