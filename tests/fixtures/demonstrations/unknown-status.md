# Unknown status specimen

This record names a status outside the closed five.

```shoggoth-demonstration
{
  "schema": "shoggoth-demonstration/v1",
  "skill": "specimen",
  "plugin": "specimen",
  "status": "almost-real",
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
      "id": "replay",
      "argv": ["python3", "demo.py"],
      "expect_exit": 0
    }
  ],
  "observations": [
    "The replay reports block 13097494 and exits zero."
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
