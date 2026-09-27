# Deferred runner binding

Design home for [skills#1944](https://github.com/wildcat-finance/skills/issues/1944): Fiat binds a gate-command runner that Step 1 creates, at Step 1's push. The decision record is `docs/decisions/drafts/bind-a-step-created-runner-at-its-push.md`.

## Contents

- `study.md`, `runbook.md` and `design-evidence.json`: the accepted study, runbook and design record, byte-identical to their receipts. `tests/test_deferred_runner_scaffold.py` pins their digests.
- `reports/`: the 28 selection reports. The design record holds each one's digest.
- `probe.py`: the Surveyor policy specimens that produced those reports. It is not the product controller.
- `proof.py`: the resolver for the five pending conformance cells of `creating-step-binding`.

## Rerun the selection

From the repository root:

```bash
python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py docs/deferred-runner-binding/design-evidence.json --transition design-lock
python3 docs/deferred-runner-binding/probe.py --candidate <candidate> --criterion <criterion> --report <new relative path>
python3 docs/deferred-runner-binding/probe.py --hostile-cases
```

The first command checks the record and its 28 reports and selects `creating-step-binding`. The second remeasures one selection cell; the value is a fixture measurement. The probe reads the released adapter from commit `e992a54b4e3e4671bae98b448d57690de8dfa044` with `git show`, so the clone needs that commit, and its reports name `.hexaemeron/design/probe.py`, the path it ran from during the study. The third prints the binding model's refusals and writes nothing.

## Resolve a conformance cell

From the repository root:

```bash
python3 docs/deferred-runner-binding/proof.py --candidate creating-step-binding --criterion <criterion> --report .hexaemeron/reports/creating-step-binding-<criterion>.json
```

`proof.py` accepts only its three flags, each once, and only the cell's own report path. It creates the report exclusively and refuses when any entry already holds that path. A criterion refuses with `operation-not-implemented:<criterion>:step-<N>` until step N adds its handler: `validator-deferred-contract`, `released-adapter-replay` and `successor-replay-milliseconds` in Step 2, `controller-binding-custody` in Step 3 and `joined-demonstration` in Step 4.
