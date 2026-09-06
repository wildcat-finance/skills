# Alexandria demonstration ledger

Contract: `plugins/hexaemeron/skills/DEMONSTRATIONS.md`

- Current demonstration version: `alexandria-demo-v0.1.0`
- Demo frontier status: `open`
- Demo frontier revision: `interval-history-over-preserved-usdc`
- Current demonstration: The Phase 0 rebuild reproduces its release digest from preserved bytes with no network.
- Next demonstration job: Preserve a real Ethereum USDC interval and demonstrate the collector over it end to end.

The registered record below runs `credit-history-v0`, the complete offline path
over the preserved Goldfinch and Clearpool inputs. The demo frontier bullets
keep their baseline wording until the lane advances.

```shoggoth-demonstration
{
  "schema": "shoggoth-demonstration/v1",
  "skill": "alexandria",
  "plugin": "alexandria",
  "status": "real-data",
  "claim_id": "alexandria-credit-history-v0",
  "claim": "The preserved Goldfinch and Clearpool inputs rebuild offline through release, index, query and the Probitas handoff to the recorded derived release id, and the rebuilt output verifies.",
  "non_claim": "It does not establish source authenticity, complete venue coverage or canonical-chain finality; Goldfinch coverage stays partial and the 14 unqueried venue rows are stated gaps, not clean venues.",
  "network": {
    "policy": "denied"
  },
  "timeout_seconds": 600,
  "sources": [
    {
      "id": "plan",
      "class": "protocol",
      "path": "plugins/alexandria/examples/credit-history-v0/demo-plan.json",
      "sha256": "5e5e3b8d3cf4f07cbb973a7dc631d9f158d8611ac90e6d28605948efe7192751"
    },
    {
      "id": "goldfinch-source",
      "class": "protocol",
      "path": "plugins/tabularium/examples/goldfinch-v0/source.json",
      "sha256": "644b706804b6e28d69b1028b87937e0e36c882f703419d0e2bf568b056892bc9"
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
    "build: line \"sha256:d57f0b009d40a804e5f760e8cde4a6b1eb1ada1cc9dbf858e0494c1e750e840c\"",
    "verify: line \"sha256:d57f0b009d40a804e5f760e8cde4a6b1eb1ada1cc9dbf858e0494c1e750e840c\""
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
