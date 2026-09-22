# Alexandria demonstration ledger

Contract: `plugins/hexaemeron/skills/DEMONSTRATIONS.md`

- Current demonstration version: `alexandria-demo-v0.3.0`
- Demo frontier status: `open`
- Demo frontier revision: `interval-history-over-preserved-usdc`
- Current demonstration: The Phase 0 rebuild reproduces its release digest from preserved bytes with no network.
- Next demonstration job: Preserve a real Ethereum USDC interval and demonstrate the collector over it end to end.

The registered record checks the preserved Wildcat V1 mainnet interval's
committed manifest, rebuild record and expected values. It reads no staging
archive and performs no rebuild. The collecting host's separately recorded
rebuild binds the externally preserved bytes. The V2 and credit-history examples
remain available, and their demonstration history stays below. The held USDC
demonstration frontier is unchanged.

```shoggoth-demonstration
{
  "schema": "shoggoth-demonstration/v1",
  "skill": "alexandria",
  "plugin": "alexandria",
  "status": "real-data",
  "claim_id": "alexandria-wildcat-v1-interval-v0",
  "claim": "The committed staging manifest, rebuild record and expected values of the preserved Wildcat V1 mainnet interval, blocks 18,743,513 to 22,074,622 over 16 subjects, agree offline on release id sha256:eee71d1e9e656b8d14bc855cce201f9981e65aeec54076d132a089b24fa51d69, 16 epochs, 667 complete shards and an agreed two-transport reconciliation, and the manifest binds the preserved archive and each of its 107 files by byte count and SHA-256.",
  "non_claim": "This check does not rebuild the release or read its externally preserved staging tree. The collecting host recorded the rebuild from those digest-bound bytes. Provider agreement does not establish completeness, publisher identity or canonical-chain finality. Targeted traces exclude transactions without a matching subject log.",
  "network": {
    "policy": "denied"
  },
  "timeout_seconds": 600,
  "sources": [
    {
      "id": "expected",
      "class": "production-run",
      "path": "plugins/alexandria/examples/wildcat-v1-interval-v0/expected.json",
      "sha256": "a8fd1d7e785fec89ab4f9a5668b3f20a1bc275413bf42433c2c1ca2d3b2839cb"
    },
    {
      "id": "staging-manifest",
      "class": "production-run",
      "path": "plugins/alexandria/examples/wildcat-v1-interval-v0/staging-manifest.json",
      "sha256": "00752ca3ffaad58de7e8930e3acc58cf0b91b45d4546704988951fcd60c40faf"
    },
    {
      "id": "rebuild-record",
      "class": "production-run",
      "path": "plugins/alexandria/examples/wildcat-v1-interval-v0/rebuild-record.json",
      "sha256": "501b719983c3502ce68d55a02a7cd0f72bcc5de7bc11a64ba512b751e977fc83"
    },
    {
      "id": "program",
      "class": "repository",
      "path": "plugins/alexandria/examples/wildcat-v1-interval-v0/demo.py",
      "sha256": "f64b5a355f52354f3762d90a498c25a096a27113a77732d37e0bade2d0f8e1f3"
    }
  ],
  "commands": [
    {
      "id": "verify-preserved",
      "argv": [
        "python3",
        "plugins/alexandria/examples/wildcat-v1-interval-v0/demo.py",
        "verify-preserved"
      ],
      "expect_exit": 0
    }
  ],
  "observations": [
    "verify-preserved: json record.checked.release_id \"sha256:eee71d1e9e656b8d14bc855cce201f9981e65aeec54076d132a089b24fa51d69\"",
    "verify-preserved: json record.checked.epochs 16",
    "verify-preserved: json record.checked.shard_statuses.complete 667",
    "verify-preserved: json record.checked.reconciliation \"agreed\"",
    "verify-preserved: json manifest.staging_files_total 107",
    "verify-preserved: json manifest.archive.sha256 \"25322e603679a24a4d9410f24aca07696cdf83ed0349b9f86b900d246b76a687\""
  ],
  "frontier": {
    "version": "alexandria-demo-v0.3.0",
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
