# Decision: Admit a run's starting-commit gate bindings

## Status

Accepted, 2026-09-30, for the skills#2042 study. Step 1 publishes it in the canonical numberless draft home. It has no ADR number.

## Context

`hexctl` runs `verify` before every mutating command. That replays the run's gate receipt under the adapter beside the running controller, `plugins/hexaemeron/skills/protasis/scripts/gate_commands.py`. The adapter admits a registered module only under its own `MODULE_BINDINGS` pin, and a receipt only under a reviewed adapter digest in `REPLAY_COMPATIBLE_ADAPTERS`. A run initialised under an older release, whose registered modules and adapter are unchanged since its starting commit, refuses `controller-pin-skew` under the controller built from `main`, and the recorded controller lacks `supersede-commit` (PR #2039). Run #1872, at Step 7's push under Hexaemeron 1.6.77, is the case [skills#2042](https://github.com/wildcat-finance/skills/issues/2042) names. Three registered pins moved between 1.6.77 and 1.6.92; that runbook names one of them, `protasis.py`.

`init` records no module binding. The starting commit carries them: `d162d095:plugins/hexaemeron/skills/protasis/scripts/gate_commands.py` has the receipt's adapter digest `ac527913…` and the pins the run was validated under.

## Decision

When the running controller's pin refuses a registered module, `hexctl` reads that module's blob and the adapter blob at the run's recorded starting commit through bounded Git, takes the historical `MODULE_BINDINGS` from the adapter blob by parsing one assignment as data, and admits the module only when the worktree bytes equal the base blob and its AST digest equals the base pin. Replay admits a receipt's adapter digest when it equals the digest of the base adapter blob, and keeps the reviewed list for every other digest. Every other field of a receipt must still equal current validation. The adapter stays inert: it receives what the caller derived through one new keyword and reads no Git.

This is trust on first use pinned to a commit, the way `pip --require-hashes` pins to a reviewed hash and SSH `known_hosts` keeps the first key. Here the first use is the run's own signed starting commit, which the ledger already anchors.

It fails closed. An absent or unreadable base adapter blob, a module whose bytes differ from the base blob, a base pin that disagrees with the module, and a receipt adapter that is neither the base adapter's nor reviewed each keep today's refusal: `controller-pin-skew`, `module-edited-in-run`, `module-pin-unverified` or `gate-receipt-drift`. A module is admitted whole or not at all, and the adapter digest likewise.

## Alternatives

The study's resolver, `docs/starting-commit-gate-bindings/resolve.py`, measured four candidates against a replica of run #1872: the tree at `5d5ec5e142d83140a0967fe13ad3498df3df2015` with the run's state snapshot beside it. Two hand experiments framed them. Adding `ac527913…` to the reviewed list alone still refused `unregistered-cli-module-bindings`; adding the `protasis.py` prior pin as well made `verify` exit 0 in 1.31 s. All 24 selection cells are digest-bound in `docs/starting-commit-gate-bindings/design-evidence.json`.

| candidate | replays 1872 | edited refuses | unknown refuses | bytes written | verify ms | rows per release |
| --- | --- | --- | --- | --- | --- | --- |
| `base-commit-bindings` | true | true | true | 0 | 1,378 | 0 |
| `reviewed-prior-pins` | true | true | true | 0 | 1,313 | 2 |
| `runbook-scoped-pins` | false | true | true | 0 | 632 | 0 |
| `recorded-controller-fork` | false | true | true | 0 | 1,324 | 0 |

- `reviewed-prior-pins` adds `ac527913…` to `REPLAY_COMPATIBLE_ADAPTERS` and a `PRIOR_MODULE_BINDINGS` triple for `protasis.py`, generalising `prior_runner_bindings`. No Git reads, a small diff, and it verifies the replica. But every later older controller needs another reviewed row set, and the list is already three releases behind the plugin cache: 2 rows per release against 0.
- `runbook-scoped-pins` keeps the pin check scoped to the modules the runbook names, which is already the case, and changes only the diagnosis so it says which skewed modules the runbook names. A truthful message and no admission; the replica still refuses because `protasis.py` is named.
- `recorded-controller-fork` rebuilds the recorded controller from `d162d095` with `git archive` and backports `supersede-commit` into it. The run finishes on a controller no release shipped, `main`'s controller still refuses it at integration, and the backport is the porting the issue rules out. Its own rebuilt controller verifies the replica in 1,324 ms; `main`'s does not.

Time is a gate of at most 5,000 ms rather than a metric: the 65 ms spread between the two admitting candidates' single measurements (1,313 and 1,378 ms) is small against a per-release maintenance duty. The study reports run-to-run variation of the same size across three runs; the retained evidence holds one run per cell. Between the two survivors the one metric decides, 0 rows against 2. Selection rule `unique-frontier`; `design_evidence.py --transition design-lock` exits 0. The trade the selected rule accepts: two bounded Git reads on the refusal path only, and one adapter keyword threaded through `validate`, `validate_with_criteria`, `replay`, `interface` and `parser_bindings`, passed by `hexctl` and `criteria_execution.py` at every adapter call site. No table grows per release.

## Consequences

Three decisions here are expensive to reverse.

1. Replay provenance comes from the run's starting commit, not only from a reviewed list. This changes the doctrine [gate-commands.md](https://github.com/wildcat-finance/skills/blob/dd2e6939ed460dcd987457a398a2765822349588/plugins/hexaemeron/skills/protasis/references/gate-commands.md) states at lines 163 to 169, that `REPLAY_COMPATIBLE_ADAPTERS` "does not admit an unknown adapter" and that "adding another digest requires review of that released source and regression evidence", and the sentence at lines 185 to 188 that the 1.6.72 to 1.6.78 adapter `ac527913dc737184f2a918cdd693aa4be2e16d813736060f870a17b98fdfd119` "is not admitted". After this decision that adapter is admitted for a run whose starting commit carries it, and for no other. The reference, the Fiat SKILL "Runbook command evidence" section, the Protasis `protasis-gate-command-validation` stanza and both `EVOLUTION.md` generation rows record the consequence; this draft carries the reasoning and the alternatives.
2. The adapter's public keywords grow by one: the admitted bindings the caller derived. Home: this draft and the reference's keyword list.
3. `status --field gate_command_status` gains a `provenance` object when a replay admitted starting-commit bindings, holding the starting commit, the base adapter digest and the admitted module paths, and each skewed module entry says whether the runbook names it. Home: the reference's inspection paragraph and the Fiat SKILL section.

Step 2 built the adapter half. The keyword is `starting_bindings`, default `None`, on `validate`, `validate_with_criteria`, `replay`, `interface`, `validate_command` and `parser_bindings`. Its closed shape is one object with exactly `adapter_sha256` and `modules`; `modules` holds at most one entry per registered module path, each with exactly `ast_sha256` and `source_sha256`; every digest is 64 lowercase hexadecimal characters. A module whose AST digest left the current pin is admitted only when both digests equal its entry, and replay substitutes a receipt's adapter digest only when it equals `adapter_sha256`; every other receipt field must still equal current validation. A value outside the shape admits nothing. No new cause token exists, the reviewed list is unchanged, and the result schema `protasis-gate-commands/v1` is unchanged.

Step 3 built the controller half. `hexctl` derives the bindings only after its own pin refuses a registered module: it reads that module and the adapter at `state.base` through `bounded_run`, with fixed argv, no shell and the existing timeout and output cap, once `COMMIT_RE` has matched the base; it takes `MODULE_BINDINGS` from the adapter blob with `ast.parse` and one `ast.literal_eval` of the single assignment, never an import; and the adapter's own `parser_bindings` decides admission from the exact pair. A run whose modules match this controller's pins takes the fast path: no Git read and the result of before. `status --field gate_command_status` carries a `provenance` object, the starting commit, the base adapter digest and the admitted module paths, when a replay used the bindings, and each skewed module entry carries `named_by_runbook`. The derivation, the refusal diagnosis and `status` read the same bindings, so they name the same modules. Two controllers must not drive one run after a supersession is recorded: the 1.6.77 reader is blind to a `commit:supersede` entry, while this reader refuses a record that disagrees with its receipts.

What this leaves in place. The reviewed list stays authoritative for an adapter that is not a run's own base, and the repository check that fails when an adapter change leaves its predecessor digest neither admitted nor refused stays with [skills#1968](https://github.com/wildcat-finance/skills/issues/1968). A run initialised under 1.6.92 replays identically, with no Git read. A run without `contracts.gate_commands` stays legacy. Applying the fix to run #1872 stays with that run. Two controllers must not drive one run after a supersession is recorded: the 1.6.77 reader is blind to a `commit:supersede` entry, and the fixed reader refuses a record that disagrees with its receipts.

Integration assigns the number against the actual base; until then, the standing home is `docs/decisions/drafts/admit-starting-commit-gate-bindings.md`. Step 4 adds the measured results of the three conformance cells: `older-controller-supersession-fixture`, `base-commit-controller-demonstration` and `released-adapter-tests-green`.
