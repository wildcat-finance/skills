# Stale source demonstration ledger

The declared source digest does not match the bytes on disk; the record is refused before any command starts.

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
      "id": "corpus",
      "class": "audit",
      "path": "tests/fixtures/demonstrations/valid-ledger.md",
      "sha256": "0000000000000000000000000000000000000000000000000000000000000000"
    }
  ],
  "commands": [
    {
      "id": "run",
      "argv": [
        "python3",
        "-c",
        "print('ok')"
      ],
      "expect_exit": 0
    }
  ],
  "observations": [
    "run: line \"ok\""
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
