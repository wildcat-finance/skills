# Oversized output demonstration ledger

The child writes two mebibytes to stdout, past the runner's one-mebibyte cap.

- Current demonstration version: `specimen-demo-v0.1.0`
- Demo frontier status: `open`
- Demo frontier revision: `second-preserved-source`
- Current demonstration: One preserved chain view replays offline and reports the named block identity.
- Next demonstration job: Add a second preserved source so the replay covers two independent captures.

```shoggoth-demonstration
{
  "schema": "shoggoth-demonstration/v1",
  "skill": "specimen",
  "plugin": "specimen",
  "status": "real-data",
  "claim_id": "specimen-chain-replay",
  "claim": "The recorded block view replays offline and reports the captured block identity.",
  "non_claim": "It does not establish that the chain state is still current.",
  "network": {
    "policy": "denied"
  },
  "timeout_seconds": 300,
  "sources": [
    {
      "id": "block-view",
      "class": "chain",
      "chain": "ethereum",
      "block": 13097494,
      "anchor": "0x41119192a8acdaae5ab06ca8f1d5943fd7ca2fb0a14323642dd6daf74eed2cfc"
    }
  ],
  "commands": [
    {
      "id": "run",
      "argv": [
        "python3",
        "-c",
        "import sys; sys.stdout.write('x' * 2097152)"
      ],
      "expect_exit": 0
    }
  ],
  "observations": [
    "run: line \"unreached\""
  ],
  "frontier": {
    "version": "specimen-demo-v0.1.0",
    "status": "open",
    "revision": "second-preserved-source",
    "sha256": "06537e5ff330c910783d7bda6c61e3e585b9ae9e41b2f08fe36568d7f24fcc5b",
    "current": "One preserved chain view replays offline and reports the named block identity.",
    "next": "Add a second preserved source so the replay covers two independent captures."
  }
}
```
