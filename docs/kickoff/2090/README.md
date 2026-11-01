# Wildcat parameter and access event design

Issue [#2090](https://github.com/wildcat-finance/skills/issues/2090) adds native parameter and access meanings under Wildcat adapter `1.2.0`, preserving historical `1.0.0` replay. Step 1 ships the checked design and proof interfaces. Mapping, schema compatibility and retained conformance remain pending.

## Evidence

`study.md`, `runbook.md` and `design-evidence.json` preserve the receipted bytes. `design/event-inventory.json` records the 29 required generation, role and signature contexts across 58 concrete ABI declarations. `design/selection_probe.py` and ten reports compare the declared policy models; their count metrics measure contextual work in that model, with no production speed or memory claim.

## Native meaning

The selected `native-fields` design keeps exact ABI names and values in `mapping_records[].decoded`, empty financial amounts and only emitted additional parties. Marketless hooks/controller events gain no inferred pool. Numeric roles stay uninterpreted. The standing decision is `adr/keep-wildcat-parameter-events-as-native-state`.

## Run

Run the scaffold from the repository root:

```bash
python3 plugins/tabularium/tests/emit_wildcat_parameter_report.py --step 1 --report .hexaemeron/step-1-check.json
```

Both runner interfaces use closed argument choices and create-only bounded JSON outputs. They support Python safe-path and isolated imports. An unimplemented step or conformance criterion exits 2 without a success report. Constructed tests establish runner behaviour only; retained payloads, staging paths, counts and per-signature absence inventories remain private. Historical positives cannot be inferred from constructed events, and acceptance of absent historical positives remains due before integration.
