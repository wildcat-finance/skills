# Hypomnema demonstration ledger

Contract: `plugins/hexaemeron/skills/DEMONSTRATIONS.md`

- Current demonstration version: `hypomnema-demo-v0.1.0`
- Demo frontier status: `open`
- Demo frontier revision: `records-from-a-shipped-decision`
- Current demonstration: The lint refuses records pointing at absent files over fixtures.
- Next demonstration job: Show the record trail of one decision this repository actually made.

```shoggoth-demonstration
{
  "schema": "shoggoth-demonstration/v1",
  "skill": "hypomnema",
  "plugin": "hexaemeron",
  "status": "constructed",
  "claim_id": "hypomnema-record-lint",
  "claim": "The registered offline path exercises hypomnema over checked-in inputs and exits zero.",
  "non_claim": "Every material input was created for this repository's own tests, so the run establishes nothing about real-world data.",
  "network": {
    "policy": "denied"
  },
  "timeout_seconds": 600,
  "sources": [
    {
      "id": "input",
      "class": "fixture",
      "path": "plugins/hexaemeron/tests/fixtures/hypomnema/source/cites_missing_record.py",
      "sha256": "0c2c78812a82477e8b66d75deb7239f8becd6a9d5bd4fef1800cbd2750045f62"
    }
  ],
  "commands": [
    {
      "id": "run",
      "argv": [
        "python3",
        "-m",
        "unittest",
        "plugins.hexaemeron.tests.test_hypomnema_checker"
      ],
      "expect_exit": 0
    }
  ],
  "observations": [
    "The command exits 0 in about 0.1 seconds with no network.",
    "Its last reported line is: OK"
  ],
  "frontier": {
    "version": "hypomnema-demo-v0.1.0",
    "status": "open",
    "revision": "records-from-a-shipped-decision",
    "sha256": "a77ced7aa42e862429f1a96a9dc2933a4385764151c0817e2ab5cc263f120979",
    "current": "The lint refuses records pointing at absent files over fixtures.",
    "next": "Show the record trail of one decision this repository actually made."
  }
}
```

## History

| Version | Axis | Demo frontier revision | Demo frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `hypomnema-demo-v0.1.0` | baseline | `records-from-a-shipped-decision` | `a77ced7aa42e862429f1a96a9dc2933a4385764151c0817e2ab5cc263f120979` | `docs/decisions/ADR-068-govern-real-data-demonstrations-separately.md` | The demonstration lane starts here. Status `constructed` is decided by the material inputs above, not by the prose. |
