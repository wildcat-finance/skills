# Deferred runner binding

Design home for [skills#1944](https://github.com/wildcat-finance/skills/issues/1944): when Step 1 creates a gate-command runner, Fiat binds it at Step 1's push. The decision record is `docs/decisions/drafts/bind-a-step-created-runner-at-its-push.md`.

## Contents

- `study.md`, `runbook.md` and `design-evidence.json`: the accepted study, runbook and design record, byte-identical to their receipts. `tests/test_deferred_runner_scaffold.py` pins their digests.
- `reports/`: the 28 selection reports. The design record holds each one's digest.
- `probe.py`: the Surveyor policy specimens that produced those reports. It is not the product controller.
- `proof.py`: the resolver for the five pending conformance cells of `creating-step-binding`.
- `demonstration.md`: what the `joined-demonstration` resolver ran and observed, and what that evidence leaves unclaimed.

## Rerun the selection

From the repository root:

```bash
python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py docs/deferred-runner-binding/design-evidence.json --transition design-lock
python3 docs/deferred-runner-binding/probe.py --candidate <candidate> --criterion <criterion> --report <new relative path>
python3 docs/deferred-runner-binding/probe.py --hostile-cases
```

The first command checks the record and its 28 reports and selects `creating-step-binding`. The second remeasures one selection cell. Its value is a fixture measurement. The third prints the binding model's refusals and writes nothing. The probe reads the released adapter from commit `e992a54b4e3e4671bae98b448d57690de8dfa044` with `git show`, so the clone needs that commit. Its reports name `.hexaemeron/design/probe.py`, the path it ran from during the study.

## Resolve a conformance cell

From the repository root:

```bash
python3 docs/deferred-runner-binding/proof.py --candidate creating-step-binding --criterion <criterion> --report .hexaemeron/reports/creating-step-binding-<criterion>.json
```

`proof.py` accepts only its three flags, each once, and only the cell's own report path. It creates the report exclusively: if any entry already holds that path, it refuses. Step 2 added the handlers for `validator-deferred-contract`, `released-adapter-replay` and `successor-replay-milliseconds`, Step 3 the one for `controller-binding-custody` and Step 4 the one for `joined-demonstration`. A criterion without a handler refuses with `operation-not-implemented:<criterion>:step-<N>`.

`joined-demonstration` also writes `.hexaemeron/reports/creating-step-binding-joined-demonstration.evidence.json`, before the report and under the same rule. The evidence file records the report's SHA-256. The resolver refuses if either path is already taken.
