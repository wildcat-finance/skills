# Alexandria demonstration ledger

Contract: `plugins/hexaemeron/skills/DEMONSTRATIONS.md`

- Current demonstration version: `alexandria-demo-v0.7.0`
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
  "claim": "The committed manifests, rebuild records and expected values of both preserved Wildcat mainnet intervals and of the twelve preserved Aave V3 Ethereum segments agree offline on their release identities: V1 has 16 epochs and 667 complete shards; V2 has 137 epochs and 3,463 complete shards; the Aave segments have 32,437 complete shards in all, each segment with an agreed reconciliation, and segment 4 has 257 epochs. Each manifest binds its external archive and staging files by byte count and SHA-256.",
  "non_claim": "This registered operation checks committed metadata only. It neither reads the external staging archives nor rebuilds a release. The separate build and verify commands require the external staging trees. The twelve Aave staging trees are one archive held outside this repository, and the check does not read it. Provider agreement does not establish completeness, publisher identity or canonical-chain finality. Targeted traces exclude transactions without a matching subject log.",
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
      "sha256": "6a59ff584c7c11ffff1a2d20853c46a4c8845c3c6df3c5005bab5c72c0554fbc"
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
      "sha256": "65cb34fec26f50806961276c3cd975acce4ecd6111cd26b0d5c9b6cba02d00f5"
    },
    {
      "id": "aave-staging-manifest-json",
      "class": "production-run",
      "path": "plugins/alexandria/examples/aave-v3-interval-v0/staging-manifest.json",
      "sha256": "69be6ef51ea4c4a73c5ed06b74943092079551f151de8761c76a0894e9e5e497"
    },
    {
      "id": "aave-segment-0-expected-json",
      "class": "production-run",
      "path": "plugins/alexandria/examples/aave-v3-interval-v0/segments/0/expected.json",
      "sha256": "41025f1b23aa0246be0997c54fa7a46e25c8a35ac0e2ff807eca1a15ea09f1d5"
    },
    {
      "id": "aave-segment-1-expected-json",
      "class": "production-run",
      "path": "plugins/alexandria/examples/aave-v3-interval-v0/segments/1/expected.json",
      "sha256": "6d168b06c3d65768bcfd7d2df56efb5513213a0ec6c682529ceb99382873b6a3"
    },
    {
      "id": "aave-segment-2-expected-json",
      "class": "production-run",
      "path": "plugins/alexandria/examples/aave-v3-interval-v0/segments/2/expected.json",
      "sha256": "b35f79b1990c2531c6de5bcb188461a8dc52676c061355166fbf2886b2be3ab3"
    },
    {
      "id": "aave-segment-3-expected-json",
      "class": "production-run",
      "path": "plugins/alexandria/examples/aave-v3-interval-v0/segments/3/expected.json",
      "sha256": "ee2069c6706fd5bcac7b8fb1fff86641bdf967479ef230fcc0c69dd8a649ec6d"
    },
    {
      "id": "aave-segment-4-expected-json",
      "class": "production-run",
      "path": "plugins/alexandria/examples/aave-v3-interval-v0/segments/4/expected.json",
      "sha256": "4ddbc1edfb7eb7469b710f468673d42ff967dd197b71cfe60680519193957e7b"
    },
    {
      "id": "aave-segment-5-expected-json",
      "class": "production-run",
      "path": "plugins/alexandria/examples/aave-v3-interval-v0/segments/5/expected.json",
      "sha256": "48e84abade7660d62d2215c308e72de927c6a5752ef08edcfd89bebdfb3f701d"
    },
    {
      "id": "aave-segment-6-expected-json",
      "class": "production-run",
      "path": "plugins/alexandria/examples/aave-v3-interval-v0/segments/6/expected.json",
      "sha256": "4417661a7c46c84e56a2a79f9e81ee534e538378632be48c7cc31ac8da74bdc2"
    },
    {
      "id": "aave-segment-7-expected-json",
      "class": "production-run",
      "path": "plugins/alexandria/examples/aave-v3-interval-v0/segments/7/expected.json",
      "sha256": "241cfd5841d16616d3c79110c0e4b7ce8383d96b44f4a61aeeb5aa943c25cbb2"
    },
    {
      "id": "aave-segment-8-expected-json",
      "class": "production-run",
      "path": "plugins/alexandria/examples/aave-v3-interval-v0/segments/8/expected.json",
      "sha256": "cb2a2b13faa7ac18de6828058de3670c6edcb402223aee7666ceb5d963450c54"
    },
    {
      "id": "aave-segment-9-expected-json",
      "class": "production-run",
      "path": "plugins/alexandria/examples/aave-v3-interval-v0/segments/9/expected.json",
      "sha256": "d9f6fd1dc2457909343d818c584e4ff043f477b9a007d96e20df0e2533c7203d"
    },
    {
      "id": "aave-segment-10-expected-json",
      "class": "production-run",
      "path": "plugins/alexandria/examples/aave-v3-interval-v0/segments/10/expected.json",
      "sha256": "5f173ebeac5141be670c8b58bf64712b97460a53e173b638995e6b0b2c6ec2ab"
    },
    {
      "id": "aave-segment-11-expected-json",
      "class": "production-run",
      "path": "plugins/alexandria/examples/aave-v3-interval-v0/segments/11/expected.json",
      "sha256": "02e83942c944774b11bde06b12ad161a1c6aafa40a758edbf8f510c9f6d27242"
    },
    {
      "id": "aave-demo-py",
      "class": "repository",
      "path": "plugins/alexandria/examples/aave-v3-interval-v0/demo.py",
      "sha256": "dd5a8ccecb483d4e0ad40fe0f69d3f6a3c24ae459aaf1d4fdfa9779d024b0cb2"
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
    "aave-verify-preserved: json segments_with_rebuild_record 12",
    "aave-verify-preserved: json segments.4.epochs 257"
  ],
  "frontier": {
    "version": "alexandria-demo-v0.7.0",
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
| `alexandria-demo-v0.6.0` | generation | `interval-history-over-preserved-usdc` | `233c858a1ff38ac0065eaf3f279ee6c5ad50f0f8521878c9c66d3fb085221499` | skills#1872, [aave-v3-interval-v0](../../examples/aave-v3-interval-v0/README.md) | Register all twelve Aave V3 segments: 32,437 complete shards, an agreed reconciliation for each, one committed manifest binding the single external staging archive and 61,577 staged files, and a recorded rebuild per segment that agrees with its release pin. The held frontier is unchanged. |
| `alexandria-demo-v0.7.0` | generation | `interval-history-over-preserved-usdc` | `233c858a1ff38ac0065eaf3f279ee6c5ad50f0f8521878c9c66d3fb085221499` | skills#1872 | Restore the Wildcat V1 and V2 rebuild-record pins that v0.5.0 dropped; 25 of 32 sources now bind both estates and all twelve Aave segments. The ledger holds one record, so the Aave segments stay in it. The held frontier is unchanged. |
