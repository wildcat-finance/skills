# Imprimatur demonstration ledger

Contract: [skill demonstration contract](../DEMONSTRATIONS.md)

- Current demonstration version: `imprimatur-demo-v0.1.0`
- Demo frontier status: `open`
- Demo frontier revision: `corpus-from-published-prose`
- Current demonstration: The labelled corpus freeze grades extraction over annotated specimens.
- Next demonstration job: Grade the lint over prose already published under this collective's name.

```shoggoth-demonstration
{
  "schema": "shoggoth-demonstration/v1",
  "skill": "imprimatur",
  "plugin": "hexaemeron",
  "status": "constructed",
  "claim_id": "imprimatur-labelled-corpus",
  "claim": "The registered offline path exercises imprimatur over checked-in inputs and exits zero.",
  "non_claim": "Every material input was created for this repository's own tests, so the run establishes nothing about real-world data.",
  "network": {
    "policy": "denied"
  },
  "timeout_seconds": 600,
  "sources": [
    {
      "id": "input",
      "class": "fixture",
      "path": "plugins/hexaemeron/skills/imprimatur/evals/labelled-prose-v1/candidate-freeze.json",
      "sha256": "c895b3665093bc48584a14c1a32854cb7a2c4c00bc73d30f4035438f7869345d"
    }
  ],
  "commands": [
    {
      "id": "run",
      "argv": [
        "python3",
        "-m",
        "unittest",
        "plugins.hexaemeron.tests.test_imprimatur_source_extraction"
      ],
      "expect_exit": 0
    }
  ],
  "observations": [
    "The command exits 0 in about 0.4 seconds with no network.",
    "Its last reported line is: OK"
  ],
  "frontier": {
    "version": "imprimatur-demo-v0.1.0",
    "status": "open",
    "revision": "corpus-from-published-prose",
    "sha256": "a88a10b15c8af17e60e58b796f5bf836b626e90e43b4eb51f1b4b15054b616b1",
    "current": "The labelled corpus freeze grades extraction over annotated specimens.",
    "next": "Grade the lint over prose already published under this collective's name."
  }
}
```

## History

| Version | Axis | Demo frontier revision | Demo frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `imprimatur-demo-v0.1.0` | baseline | `corpus-from-published-prose` | `a88a10b15c8af17e60e58b796f5bf836b626e90e43b4eb51f1b4b15054b616b1` | `adr/govern-real-data-demonstrations-separately` | The demonstration lane starts here. Status `constructed` is decided by the material inputs above, not by the prose. |
