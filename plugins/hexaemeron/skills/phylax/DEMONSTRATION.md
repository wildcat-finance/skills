# Phylax demonstration ledger

Contract: `plugins/hexaemeron/skills/DEMONSTRATIONS.md`

- Current demonstration version: `phylax-demo-v0.1.0`
- Demo frontier status: `open`
- Demo frontier revision: `boundaries-from-a-shipped-surface`
- Current demonstration: The lint refuses unbounded reads and shell forms over fixtures.
- Next demonstration job: Harden one shipped off-chain surface and show the boundary it gained.

```shoggoth-demonstration
{
  "schema": "shoggoth-demonstration/v1",
  "skill": "phylax",
  "plugin": "hexaemeron",
  "status": "constructed",
  "claim_id": "phylax-boundary-lint",
  "claim": "The registered offline path exercises phylax over checked-in inputs and exits zero.",
  "non_claim": "Every material input was created for this repository's own tests, so the run establishes nothing about real-world data.",
  "network": {
    "policy": "denied"
  },
  "timeout_seconds": 600,
  "sources": [
    {
      "id": "input",
      "class": "fixture",
      "path": "plugins/hexaemeron/tests/test_phylax_checker.py",
      "sha256": "476d87e7a9d78446e0d6b799e29fc3f9b249b310850443c4ac3083a4abecf062"
    }
  ],
  "commands": [
    {
      "id": "run",
      "argv": [
        "python3",
        "-m",
        "unittest",
        "plugins.hexaemeron.tests.test_phylax_checker"
      ],
      "expect_exit": 0
    }
  ],
  "observations": [
    "The command exits 0 in about 0.1 seconds with no network.",
    "Its last reported line is: OK"
  ],
  "frontier": {
    "version": "phylax-demo-v0.1.0",
    "status": "open",
    "revision": "boundaries-from-a-shipped-surface",
    "sha256": "7117a04cafee1c2871140396f8af7ff9694c7757ca6aabf366acb76f3b549383",
    "current": "The lint refuses unbounded reads and shell forms over fixtures.",
    "next": "Harden one shipped off-chain surface and show the boundary it gained."
  }
}
```

## History

| Version | Axis | Demo frontier revision | Demo frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `phylax-demo-v0.1.0` | baseline | `boundaries-from-a-shipped-surface` | `7117a04cafee1c2871140396f8af7ff9694c7757ca6aabf366acb76f3b549383` | `docs/decisions/ADR-068-govern-real-data-demonstrations-separately.md` | The demonstration lane starts here. Status `constructed` is decided by the material inputs above, not by the prose. |
