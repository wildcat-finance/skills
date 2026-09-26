# Alexandria demonstration ledger

Contract: `plugins/hexaemeron/skills/DEMONSTRATIONS.md`

- Current demonstration version: `alexandria-demo-v0.5.0`
- Demo frontier status: `open`
- Demo frontier revision: `interval-history-over-preserved-usdc`
- Current demonstration: The Phase 0 rebuild reproduces its release digest from preserved bytes with no network.
- Next demonstration job: Preserve a real Ethereum USDC interval and demonstrate the collector over it end to end.

The registered operations check committed metadata for both Wildcat estates
and for each preserved Aave V3 segment. They read no external staging and
perform no rebuild. The separate `build` and `verify` commands exercise the
whole offline path once the staging trees are unpacked. The held USDC
demonstration frontier is unchanged.

```shoggoth-demonstration
{
  "schema": "shoggoth-demonstration/v1",
  "skill": "alexandria",
  "plugin": "alexandria",
  "status": "real-data",
  "claim_id": "alexandria-wildcat-estates-interval-v0",
  "claim": "The committed manifests, rebuild records and expected values of both preserved Wildcat mainnet intervals and of each preserved Aave V3 Ethereum segment agree offline on their release identities: V1 has 16 epochs and 667 complete shards; V2 has 137 epochs and 3,463 complete shards; Aave segment 4 has 257 epochs and 2,544 complete shards. Each manifest binds its external archive and staging files by byte count and SHA-256.",
  "non_claim": "This registered operation checks committed metadata only. It neither reads the external staging archives nor rebuilds a release. The separate build and verify commands require the external staging trees. Eleven of the twelve Aave segments are not yet preserved and are counted, not checked. Provider agreement does not establish completeness, publisher identity or canonical-chain finality. Targeted traces exclude transactions without a matching subject log.",
  "network": {
    "policy": "denied"
  },
  "timeout_seconds": 600,
  "sources": [
    {
      "id": "v1-expected-json",
      "class": "production-run",
      "path": "plugins/alexandria/examples/wildcat-v1-interval-v0/expected.json",
      "sha256": "a8fd1d7e785fec89ab4f9a5668b3f20a1bc275413bf42433c2c1ca2d3b2839cb"
    },
    {
      "id": "v1-staging-manifest-json",
      "class": "production-run",
      "path": "plugins/alexandria/examples/wildcat-v1-interval-v0/staging-manifest.json",
      "sha256": "00752ca3ffaad58de7e8930e3acc58cf0b91b45d4546704988951fcd60c40faf"
    },
    {
      "id": "v1-rebuild-record-json",
      "class": "production-run",
      "path": "plugins/alexandria/examples/wildcat-v1-interval-v0/rebuild-record.json",
      "sha256": "501b719983c3502ce68d55a02a7cd0f72bcc5de7bc11a64ba512b751e977fc83"
    },
    {
      "id": "v1-demo-py",
      "class": "repository",
      "path": "plugins/alexandria/examples/wildcat-v1-interval-v0/demo.py",
      "sha256": "f64b5a355f52354f3762d90a498c25a096a27113a77732d37e0bade2d0f8e1f3"
    },
    {
      "id": "v2-expected-json",
      "class": "production-run",
      "path": "plugins/alexandria/examples/wildcat-v2-interval-v0/expected.json",
      "sha256": "3d30fc07e9d1edc67b588a51f88262c9e1f6e7d7da6d6a06e64060161e0c4124"
    },
    {
      "id": "v2-staging-manifest-json",
      "class": "production-run",
      "path": "plugins/alexandria/examples/wildcat-v2-interval-v0/staging-manifest.json",
      "sha256": "4f5f818753d811ff635500ef1a134eb6ca7ff855818ea584d12ef0fe5936dc21"
    },
    {
      "id": "v2-rebuild-record-json",
      "class": "production-run",
      "path": "plugins/alexandria/examples/wildcat-v2-interval-v0/rebuild-record.json",
      "sha256": "7fd19c69e642a29b966ee73787723f8e0165199be986379271c13430e854ac43"
    },
    {
      "id": "v2-demo-py",
      "class": "repository",
      "path": "plugins/alexandria/examples/wildcat-v2-interval-v0/demo.py",
      "sha256": "a8a0ff53fe1e226df899fb877bd43cf862ab36be0c48e551ba1ec9963434f844"
    },
    {
      "id": "combined-demo-py",
      "class": "repository",
      "path": "plugins/alexandria/examples/wildcat-estates-interval-v0/demo.py",
      "sha256": "ccb62a23e94248a923aca80d6ab04c3cc6318464bf35cde38fe0671378dafa06"
    },
    {
      "id": "combined-expected-json",
      "class": "production-run",
      "path": "plugins/alexandria/examples/wildcat-estates-interval-v0/expected.json",
      "sha256": "7ef4c04af038a37d936704f6dab2aae140b46189bd4c405fe202a3607e5820ce"
    },
    {
      "id": "aave-segment-table-json",
      "class": "repository",
      "path": "plugins/alexandria/examples/aave-v3-interval-v0/segments.json",
      "sha256": "65130bfb6e4a4cecc9a007aec55f873fa046cbf8e85fe34c419be7f2c5909863"
    },
    {
      "id": "aave-segment-4-expected-json",
      "class": "production-run",
      "path": "plugins/alexandria/examples/aave-v3-interval-v0/segments/4/expected.json",
      "sha256": "4c0441e7c0a997698fb2c47174ca467c5df5f48f3571c7db9e5a6667c7888aed"
    },
    {
      "id": "aave-segment-4-staging-manifest-json",
      "class": "production-run",
      "path": "plugins/alexandria/examples/aave-v3-interval-v0/segments/4/staging-manifest.json",
      "sha256": "cfbe5a70b2e889071f3d5e1c47e8f6af581a6b3babaddf45e7d7ac8e3c707e2f"
    },
    {
      "id": "aave-segment-4-rebuild-record-json",
      "class": "production-run",
      "path": "plugins/alexandria/examples/aave-v3-interval-v0/segments/4/rebuild-record.json",
      "sha256": "a4fb479f67ba3364b6445571905e1118dc684ceb3ef4d532f1ef9207c185a1ae"
    },
    {
      "id": "aave-demo-py",
      "class": "repository",
      "path": "plugins/alexandria/examples/aave-v3-interval-v0/demo.py",
      "sha256": "1a6373734075eb36f69c24206af1437a0fba9f9ad29d2073279984ccdfce3773"
    }
  ],
  "commands": [
    {
      "id": "verify-preserved",
      "argv": [
        "python3",
        "plugins/alexandria/examples/wildcat-estates-interval-v0/demo.py",
        "verify-preserved"
      ],
      "expect_exit": 0
    },
    {
      "id": "aave-verify-preserved",
      "argv": [
        "python3",
        "plugins/alexandria/examples/aave-v3-interval-v0/demo.py",
        "verify-preserved"
      ],
      "expect_exit": 0
    }
  ],
  "observations": [
    "verify-preserved: json scope \"committed-metadata-only\"",
    "verify-preserved: json rebuild_performed false",
    "verify-preserved: json estates.wildcat-v1.epochs 16",
    "verify-preserved: json estates.wildcat-v2.epochs 137",
    "aave-verify-preserved: json scope \"committed-metadata-only\"",
    "aave-verify-preserved: json rebuild_performed false",
    "aave-verify-preserved: json segments_with_rebuild_record 1",
    "aave-verify-preserved: json segments.4.epochs 257"
  ],
  "frontier": {
    "version": "alexandria-demo-v0.5.0",
    "status": "open",
    "revision": "interval-history-over-preserved-usdc",
    "sha256": "233c858a1ff38ac0065eaf3f279ee6c5ad50f0f8521878c9c66d3fb085221499",
    "current": "The Phase 0 rebuild reproduces its release digest from preserved bytes with no network.",
    "next": "Preserve a real Ethereum USDC interval and demonstrate the collector over it end to end."
  }
}
```

## History

| Version | Axis | Demo frontier revision | Demo frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `alexandria-demo-v0.1.0` | baseline | `interval-history-over-preserved-usdc` | `233c858a1ff38ac0065eaf3f279ee6c5ad50f0f8521878c9c66d3fb085221499` | `adr/govern-real-data-demonstrations-separately` | The demonstration lane starts here. Status `real-data` is decided by the material inputs above, not by the prose. |
| `alexandria-demo-v0.2.0` | generation | `interval-history-over-preserved-usdc` | `233c858a1ff38ac0065eaf3f279ee6c5ad50f0f8521878c9c66d3fb085221499` | skills#1731, [wildcat-v2-interval-v0](../../examples/wildcat-v2-interval-v0/README.md) | The registered record moves from the credit-history rebuild to the preserved Wildcat V2 mainnet interval: its committed manifest, rebuild record and expected values agree offline on one release id, 137 epochs, 3,463 complete shards and an agreed reconciliation, while the staging tree itself is preserved outside this repository and bound by digest. Status `real-data` is decided by the material inputs above. The demo frontier does not move. |
| `alexandria-demo-v0.3.0` | generation | `interval-history-over-preserved-usdc` | `233c858a1ff38ac0065eaf3f279ee6c5ad50f0f8521878c9c66d3fb085221499` | skills#1731, [wildcat-v1-interval-v0](../../examples/wildcat-v1-interval-v0/README.md) | Register the preserved V1 interval: 16 epochs, 667 complete shards and an agreed reconciliation. Its manifest binds 107 externally preserved staging files; the recorded rebuild agrees with the release pin. The held demonstration frontier is unchanged. |
| `alexandria-demo-v0.4.0` | generation | `interval-history-over-preserved-usdc` | `233c858a1ff38ac0065eaf3f279ee6c5ad50f0f8521878c9c66d3fb085221499` | [both estates](../../examples/wildcat-estates-interval-v0/README.md) | Register the paired metadata check and document the separate complete offline rebuild. The held frontier remains unchanged. |
| `alexandria-demo-v0.5.0` | generation | `interval-history-over-preserved-usdc` | `233c858a1ff38ac0065eaf3f279ee6c5ad50f0f8521878c9c66d3fb085221499` | skills#1872, [aave-v3-interval-v0](../../examples/aave-v3-interval-v0/README.md) | Register the Aave V3 segment metadata check beside the Wildcat one: segment 4 has 257 epochs, 2,544 complete shards and an agreed reconciliation, its manifest binds 2,550 externally preserved staging files, and its recorded rebuild agrees with the release pin. The other eleven segments are counted as not yet preserved. The held frontier is unchanged. |
