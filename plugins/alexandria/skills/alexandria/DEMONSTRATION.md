# Alexandria demonstration ledger

Contract: `plugins/hexaemeron/skills/DEMONSTRATIONS.md`

- Current demonstration version: `alexandria-demo-v0.1.0`
- Demo frontier status: `open`
- Demo frontier revision: `interval-history-over-preserved-usdc`
- Current demonstration: The Phase 0 rebuild reproduces its release digest from preserved bytes with no network.
- Next demonstration job: Preserve a real Ethereum USDC interval and demonstrate the collector over it end to end.

```shoggoth-demonstration
{
  "schema": "shoggoth-demonstration/v1",
  "skill": "alexandria",
  "plugin": "alexandria",
  "status": "real-data",
  "claim_id": "alexandria-compound-v3-phase0",
  "claim": "The pinned Comet registry and RPC corpus rebuild offline into the same raw release digest.",
  "non_claim": "It does not establish an interval history of Compound v3, and it is a bounded method proof over two transactions.",
  "network": {
    "policy": "denied"
  },
  "timeout_seconds": 600,
  "sources": [
    {
      "id": "input",
      "class": "protocol",
      "path": "plugins/alexandria/examples/compound-v3-phase0-v0/source/corpus.json",
      "sha256": "fdafb894bc212bc23133ddf80a8ad11384332e2ac6fba871c251a8a082fe0880"
    }
  ],
  "commands": [
    {
      "id": "run",
      "argv": [
        "python3",
        "plugins/alexandria/examples/compound-v3-phase0-v0/rebuild.py"
      ],
      "expect_exit": 0
    }
  ],
  "observations": [
    "The command exits 0 in about 0.6 seconds with no network.",
    "Its last reported line is: rebuild matches sha256:73db32c8e4dac528c9352362d6b12cae71af0824d2f69c89aa7ff1edba9321ab; 5 method gates recorded"
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
| `alexandria-demo-v0.1.0` | baseline | `interval-history-over-preserved-usdc` | `233c858a1ff38ac0065eaf3f279ee6c5ad50f0f8521878c9c66d3fb085221499` | `docs/decisions/ADR-068-govern-real-data-demonstrations-separately.md` | The demonstration lane starts here. Status `real-data` is decided by the material inputs above, not by the prose. |
