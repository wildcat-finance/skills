# G4 composition with the landed fee adapter

## Version boundary

The composition combines the audited #2090 product
`1fc459082a4ff185dab7f464b48cc53982834b41` with landed #2089 at
`8228f0d73ad74f957589051ce4b6563f6f3a8441`. Adapter `1.0.0` keeps the
qualified starting-tree interpretation. Adapter `1.1.0` keeps fees and its
generic unsupported limitations. Adapter `1.2.0` retains those fee meanings
and adds the 29 native parameter/access contexts and their specific
unsupported reasons. Sanctions asset-routing joins remain outside this delivery.

Four constructed controls were executed against the exact landed fee runtime:
required native events and final-group events, for each generation. Their input,
mapping and generated-file digests are in
[`wildcat-parameter-fee-parent.json`](../../../tests/fixtures/wildcat-parameter-fee-parent.json).
The composed runtime reproduces each control under `1.1.0` byte for byte.
[`test_wildcat_version_composition.py`](../../../plugins/tabularium/tests/test_wildcat_version_composition.py)
also checks the feature matrix, both rule-table projections and recorded-version
manifest defaults alongside an explicit version override.

## Executed checks

The complete Tabularium suite passed 656 tests. Existing constructed releases
retain their committed bytes. The schema check passes 49 tests; the new
composition module passes four. Promise Machine coverage, evaluation and runtime
checks report zero findings, including 11 evaluation cases and 55 runtime
bindings. Those checks recompute repository evidence; no model benchmark ran.

The initial focused invocation used an incorrect test package path. Subsequent
runs exposed stale version expectations and a schema-enum ordering change in
an unrelated adapter branch. The expectations now reflect the supported feature
matrix; the unrelated branch was restored from the landed parent. The failed
runs remain separate from the successful reruns. No production failure guard
is claimed for those corrections.

The later selected run on signed commit
`31e1d28be2eaf535c29cfd9ac1dc0ea2f52a3c43` passed 16 checks and failed
Tabularium's exact bundle-membership assertion because this record and the two
fresh retained files were absent from its expected set. All 6,200 snapshot
entries remained intact and every check group drained cleanly. The unchanged
assertion reproduced the failure. Its expected set now names exactly those
three additions; original receipted hashes and privacy assertions are preserved.
That red run remains red. The repair changes no production mapper or schema.

## Retained evidence and acceptance

The fresh [integration retained report](executed/integration-retained-conformance.json)
and its [bounded observations](executed/integration-retained-conformance.observations.json)
rebuild and verify both preserved raw releases under the combined `1.2.0`
interpretation. Both passed. These are fresh outputs; the earlier step reports
and observations remain unchanged. The new V2 digests include the fee meanings
that landed through #2089.

Every observed required parameter/access event must map, and every observed
final-group event retains its declared unsupported disposition. These results
establish no historical occurrence for absent signatures. Constructed coverage
cannot supply that evidence. At this execution, the separate user decision required by the study for absent
historical positives remains pending before integration and merge.
