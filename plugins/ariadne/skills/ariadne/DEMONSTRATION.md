# Ariadne demonstration ledger

Contract: `plugins/hexaemeron/skills/DEMONSTRATIONS.md`

- Current demonstration version: `ariadne-demo-v0.1.0`
- Demo frontier status: `open`
- Demo frontier revision: `attest-a-preserved-release`
- Current demonstration: The escrow statement and its gap report verify from checked-in fixtures.
- Next demonstration job: Attest a preserved Wildcat release so the statement covers real artefacts.

```shoggoth-demonstration
{
  "schema": "shoggoth-demonstration/v1",
  "skill": "ariadne",
  "plugin": "ariadne",
  "status": "constructed",
  "claim_id": "ariadne-escrow-statement",
  "claim": "The registered offline path exercises ariadne over checked-in inputs and exits zero.",
  "non_claim": "Every material input was created for this repository's own tests, so the run establishes nothing about real-world data.",
  "network": {
    "policy": "denied"
  },
  "timeout_seconds": 300,
  "sources": [
    {
      "id": "input",
      "class": "fixture",
      "path": "plugins/ariadne/examples/escrow-v1.1.0.json",
      "sha256": "38ecb1b4510722fe4e3e2107e073917eff87887c883e8893de754c3fe7532159"
    }
  ],
  "commands": [
    {
      "id": "run",
      "argv": [
        "python3",
        "plugins/ariadne/scripts/ariadne.py",
        "verify",
        "plugins/ariadne/examples/escrow-v1.1.0.json"
      ],
      "expect_exit": 0
    }
  ],
  "observations": [
    "The command exits 0 in about 0.0 seconds with no network.",
    "Its last reported line is: check deployments: pass -- 1 deployment(s), 1 unconfirmed against a chain"
  ],
  "frontier": {
    "version": "ariadne-demo-v0.1.0",
    "status": "open",
    "revision": "attest-a-preserved-release",
    "sha256": "1fac0ef4395a2891b715385217898220d271f0ae40aec7069c77ee081427a5d7",
    "current": "The escrow statement and its gap report verify from checked-in fixtures.",
    "next": "Attest a preserved Wildcat release so the statement covers real artefacts."
  }
}
```

## History

| Version | Axis | Demo frontier revision | Demo frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `ariadne-demo-v0.1.0` | baseline | `attest-a-preserved-release` | `1fac0ef4395a2891b715385217898220d271f0ae40aec7069c77ee081427a5d7` | `docs/decisions/ADR-068-govern-real-data-demonstrations-separately.md` | The demonstration lane starts here. Status `constructed` is decided by the material inputs above, not by the prose. |
