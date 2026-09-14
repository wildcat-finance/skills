# Homologia demonstration ledger

Contract: `plugins/hexaemeron/skills/DEMONSTRATIONS.md`

- Current demonstration version: `homologia-demo-v0.1.0`
- Demo frontier status: `open`
- Demo frontier revision: `mirror-a-deployed-computation`
- Current demonstration: The checker refuses malformed manifests and vectors over fixtures.
- Next demonstration job: Mirror one deployed Wildcat computation against its pinned vectors.

```shoggoth-demonstration
{
  "schema": "shoggoth-demonstration/v1",
  "skill": "homologia",
  "plugin": "homologia",
  "status": "constructed",
  "claim_id": "homologia-wad-interest-mirror",
  "claim": "The registered offline path exercises homologia over checked-in inputs and exits zero.",
  "non_claim": "Every material input was created for this repository's own tests, so the run establishes nothing about real-world data.",
  "network": {
    "policy": "denied"
  },
  "timeout_seconds": 600,
  "sources": [
    {
      "id": "input",
      "class": "fixture",
      "path": "plugins/homologia/tests/fixtures/check/malformed-manifest.json",
      "sha256": "160bfc9279ee6dbe0287202ce89a10520259ed999078f2b0d308738ab27df3e1"
    }
  ],
  "commands": [
    {
      "id": "run",
      "argv": [
        "python3",
        "-m",
        "unittest",
        "discover",
        "-s",
        "plugins/homologia/tests",
        "-t",
        "plugins/homologia"
      ],
      "expect_exit": 0
    }
  ],
  "observations": [
    "The command exits 0 in about 0.8 seconds with no network.",
    "Its last reported line is: OK"
  ],
  "frontier": {
    "version": "homologia-demo-v0.1.0",
    "status": "open",
    "revision": "mirror-a-deployed-computation",
    "sha256": "d6c3d9ec7e9bb6dcf8f8416e74f40de0e30ff0482533610820a008bb7ae2a0e5",
    "current": "The checker refuses malformed manifests and vectors over fixtures.",
    "next": "Mirror one deployed Wildcat computation against its pinned vectors."
  }
}
```

## History

| Version | Axis | Demo frontier revision | Demo frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `homologia-demo-v0.1.0` | baseline | `mirror-a-deployed-computation` | `d6c3d9ec7e9bb6dcf8f8416e74f40de0e30ff0482533610820a008bb7ae2a0e5` | `adr/govern-real-data-demonstrations-separately` | The demonstration lane starts here. Status `constructed` is decided by the material inputs above, not by the prose. |
