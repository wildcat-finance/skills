# Alexandria demonstration ledger

Contract: `plugins/hexaemeron/skills/DEMONSTRATIONS.md`

- Current demonstration version: `alexandria-demo-v0.2.0`
- Demo frontier status: `open`
- Demo frontier revision: `interval-history-over-preserved-usdc`
- Current demonstration: The Phase 0 rebuild reproduces its release digest from preserved bytes with no network.
- Next demonstration job: Preserve a real Ethereum USDC interval and demonstrate the collector over it end to end.

The registered record below checks `wildcat-v2-interval-v0`, the preserved
Wildcat V2 mainnet interval: its committed staging manifest, rebuild record and
expected values agree offline on the release id the collecting host rebuilt
from the preserved tree, which lives outside this repository and is bound
by digest. The `credit-history-v0` example stays in the tree and its record
stays in the history below. The demo frontier bullets keep their baseline
wording, because the frontier's own job, a preserved USDC interval, is not
taken here.

```shoggoth-demonstration
{
  "schema": "shoggoth-demonstration/v1",
  "skill": "alexandria",
  "plugin": "alexandria",
  "status": "real-data",
  "claim_id": "alexandria-wildcat-v2-interval-v0",
  "claim": "The committed staging manifest, rebuild record and expected values of the preserved Wildcat V2 mainnet interval, blocks 21,866,550 to 26,022,093 over 137 subjects, agree offline on release id sha256:2de87cbd4e80d378d53de553eac93a6389d6457f2f6a7d52785e7ef0e5d2a8a3, 137 epochs, 3,463 complete shards and an agreed two-transport reconciliation, and the manifest binds the preserved archive and each of its 125 files by byte count and SHA-256.",
  "non_claim": "It does not rebuild the release here: the staging tree is preserved outside this repository and the rebuild the record describes ran on the collecting host, from the bytes the manifest digests name. It does not establish source authenticity or canonical-chain finality, and the three collateral contracts among the 137 subjects are deployed but not in production.",
  "network": {
    "policy": "denied"
  },
  "timeout_seconds": 600,
  "sources": [
    {
      "id": "expected",
      "class": "production-run",
      "path": "plugins/alexandria/examples/wildcat-v2-interval-v0/expected.json",
      "sha256": "3d30fc07e9d1edc67b588a51f88262c9e1f6e7d7da6d6a06e64060161e0c4124"
    },
    {
      "id": "staging-manifest",
      "class": "production-run",
      "path": "plugins/alexandria/examples/wildcat-v2-interval-v0/staging-manifest.json",
      "sha256": "4f5f818753d811ff635500ef1a134eb6ca7ff855818ea584d12ef0fe5936dc21"
    },
    {
      "id": "rebuild-record",
      "class": "production-run",
      "path": "plugins/alexandria/examples/wildcat-v2-interval-v0/rebuild-record.json",
      "sha256": "27ca6f4468eee03e8fdb66ee1114e2eedd2b556a180be1340cb50337b10f4cc3"
    },
    {
      "id": "program",
      "class": "repository",
      "path": "plugins/alexandria/examples/wildcat-v2-interval-v0/demo.py",
      "sha256": "a8a0ff53fe1e226df899fb877bd43cf862ab36be0c48e551ba1ec9963434f844"
    }
  ],
  "commands": [
    {
      "id": "verify-preserved",
      "argv": [
        "python3",
        "plugins/alexandria/examples/wildcat-v2-interval-v0/demo.py",
        "verify-preserved"
      ],
      "expect_exit": 0
    }
  ],
  "observations": [
    "verify-preserved: json record.checked.release_id \"sha256:2de87cbd4e80d378d53de553eac93a6389d6457f2f6a7d52785e7ef0e5d2a8a3\"",
    "verify-preserved: json record.checked.epochs 137",
    "verify-preserved: json record.checked.shard_statuses.complete 3463",
    "verify-preserved: json record.checked.reconciliation \"agreed\"",
    "verify-preserved: json manifest.staging_files_total 125",
    "verify-preserved: json manifest.archive.sha256 \"0407fecac64ff15c23d298044cd2498180ceea2900bb6807330c104b348bd90a\""
  ],
  "frontier": {
    "version": "alexandria-demo-v0.2.0",
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
