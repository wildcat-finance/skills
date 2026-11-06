# Both Wildcat estates, rebuilt offline

`build` reproduces both preserved Wildcat releases and builds the current
Compound release from its preserved staging bytes in the same invocation.
It checks the nine recorded Compound coverage rows, all capture field names,
the exact two-subject intersection, foreign-emitter refusals, all 16 V1 source
identities and their checkout caveat, 12 missing deployment blocks, and every
release component and staging journal against the 67,108,864-byte ceiling.
Unknown venues, wrong registry formats and changed registry pins must exit 1.

Both Wildcat staging trees are preserved outside this repository. Set
`ALEXANDRIA_WILDCAT_V1_STAGING` and `ALEXANDRIA_WILDCAT_V2_STAGING` to their
unpacked directories as the [V1](../wildcat-v1-interval-v0/README.md) and
[V2](../wildcat-v2-interval-v0/README.md) instructions describe. From the repository root:

```bash
python3 plugins/alexandria/examples/wildcat-estates-interval-v0/demo.py build --output /tmp/wildcat-estates-proof
python3 plugins/alexandria/examples/wildcat-estates-interval-v0/demo.py verify /tmp/wildcat-estates-proof
```

`verify` recomputes the proof from the releases, checks both staging trees,
reruns the refusal probes, and compares the complete result with `expected.json`.
Both operations deny Python socket construction; this is an observed Python
boundary, not operating-system isolation. An existing output refuses unchanged.
A failed build removes only its newly created output.

The public runner uses the smaller operation below, which checks the committed
manifest and rebuild metadata for both estates. It neither reads either archive
nor rebuilds a release, and explicitly returns `rebuild_performed: false`.

```bash
python3 plugins/alexandria/examples/wildcat-estates-interval-v0/demo.py verify-preserved
```

The full proof keeps Sentinel's observed zero logs in both intervals. Constructed
positive examples remain separate tests. Targeted transaction traces exclude
transactions without a matching subject log. Agreement and digest checks do not
prove source completeness, publisher identity or canonical-chain finality.
The [delivery proof](../../docs/wildcat-interval/proof.md) records the criteria,
measurement limits and the unchanged reconciliation frontier.
