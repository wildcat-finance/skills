# Wildcat parameter and access reproduction

Adapter `1.2.0` maps native parameter/access events while preserving the recorded
`1.0.0` examples. Constructed coverage exercises all 29 required contexts and
58 concrete ABI declarations. It establishes no historical occurrence.

## Reproduce

From the repository root, rebuild each public specimen and verify every release
byte:

```bash
python3 plugins/tabularium/examples/wildcat-v1-parameters-v0/rebuild.py
python3 plugins/tabularium/examples/wildcat-v2-parameters-v0/rebuild.py
python3 plugins/tabularium/tests/emit_wildcat_parameter_report.py --step 3 --report .hexaemeron/parameter-step-3.json
```

The Step 3 report executes constructed retained controls, custody/output
refusals, interrupted-build cleanup, native-state disposition mutations and
historical example replay. Ordinary discovery needs no retained custody.

## Retained evidence

The separate retained criterion requires both operator-provided staging trees:

```bash
python3 plugins/tabularium/tests/prove_wildcat_parameters.py --candidate native-fields --criterion retained-conformance --report .hexaemeron/parameter-retained.json
```

`ALEXANDRIA_WILDCAT_V1_STAGING` and `ALEXANDRIA_WILDCAT_V2_STAGING` name the
private trees. The resolver rejects linked staging ancestors, validates both
complete staging inventories, rebuilds the pinned Alexandria releases, then
builds and verifies fresh canonical releases under explicit adapter `1.2.0`.
Each generation must contain an observed required target. Every present required
record maps, and every present final-group record keeps its signature-specific
unsupported reason. The private temporary releases are removed on success,
false conformance, refusal and build interruption.

`retained-observations.json` contains only release identifiers, digests and
pass booleans. The per-declaration presence/absence inventory stays private;
its digest binds it to this result. Missing custody refuses with status 2 and
no scalar success report. Verification disagreement yields false conformance.
Historical absences remain absences from these inputs. User acceptance of
missing historical positives remains required before integration.

## Meaning

Exact ABI field names survive in `mapping_records[].decoded`. State events have
empty financial amounts. A marketless hooks/controller event gains no inferred
pool, and numeric roles gain no labels. The result supplies no financial
conversion, access-policy replay, sanctions standing, identity, settlement,
chain proof, publisher authentication or historical-completeness claim.
