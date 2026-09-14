# Alexandria demonstration ledger

Contract: `plugins/hexaemeron/skills/DEMONSTRATIONS.md`

- Current demonstration version: `alexandria-demo-v0.1.0`
- Demo frontier status: `open`
- Demo frontier revision: `interval-history-over-preserved-usdc`
- Current demonstration: The Phase 0 rebuild reproduces its release digest from preserved bytes with no network.
- Next demonstration job: Preserve a real Ethereum USDC interval and demonstrate the collector over it end to end.

The registered record below runs `credit-history-v0`, the complete offline path
over the preserved Aave v4 and Clearpool inputs. The demo frontier bullets
keep their baseline wording until the lane advances.

```shoggoth-demonstration
{
  "schema": "shoggoth-demonstration/v1",
  "skill": "alexandria",
  "plugin": "alexandria",
  "status": "real-data",
  "claim_id": "alexandria-credit-history-v0",
  "claim": "The preserved Aave v4 and Clearpool inputs rebuild offline through release, index, query and the Probitas handoff to the recorded derived release id, and the rebuilt output verifies.",
  "non_claim": "It does not establish source authenticity, complete venue coverage or canonical-chain finality; Clearpool coverage stays partial and the 14 unqueried venue rows are stated gaps, not clean venues.",
  "network": {
    "policy": "denied"
  },
  "timeout_seconds": 600,
  "sources": [
    {
      "id": "plan",
      "class": "protocol",
      "path": "plugins/alexandria/examples/credit-history-v0/demo-plan.json",
      "sha256": "60369dfba4e9bea4f547a3b63ba5126a4cc063badcbd7def641207b4edd8bfb1"
    },
    {
      "id": "aave-v4-source",
      "class": "protocol",
      "path": "plugins/tabularium/examples/aave-v4-v0/source.json",
      "sha256": "1d88fdb5bca293995fd02e5a59f060d74541c80405e7bf1987544e5f334a8744"
    },
    {
      "id": "clearpool-source",
      "class": "protocol",
      "path": "plugins/alexandria/examples/credit-history-v0/sources/clearpool.json",
      "sha256": "946fbfbad93271b17d5343afad03847992290bf20635d58755b61aa3e56f7509"
    },
    {
      "id": "program",
      "class": "repository",
      "path": "plugins/alexandria/examples/credit-history-v0/demo.py",
      "sha256": "956367805a48218adadbfbfafe345f43bfded3d40caef5609c5d264aceb694c5"
    }
  ],
  "commands": [
    {
      "id": "build",
      "argv": [
        "python3",
        "plugins/alexandria/examples/credit-history-v0/demo.py",
        "build",
        "--output",
        "{work}/credit-history-v0"
      ],
      "expect_exit": 0
    },
    {
      "id": "verify",
      "argv": [
        "python3",
        "plugins/alexandria/examples/credit-history-v0/demo.py",
        "verify",
        "{work}/credit-history-v0"
      ],
      "expect_exit": 0
    }
  ],
  "observations": [
    "build: line \"sha256:fccc014cd400f553814b58911bb06cd450f395e6145e21c0071a06b092b181ec\"",
    "verify: line \"sha256:fccc014cd400f553814b58911bb06cd450f395e6145e21c0071a06b092b181ec\""
  ],
  "frontier": {
    "version": "alexandria-demo-v0.1.0",
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
