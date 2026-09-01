# Brevitas demonstration ledger

Contract: `plugins/hexaemeron/skills/DEMONSTRATIONS.md`

- Current demonstration version: `brevitas-demo-v0.1.0`
- Demo frontier status: `open`
- Demo frontier revision: `corpus-from-shipped-prose`
- Current demonstration: The held corpus grades the linter over labelled specimens.
- Next demonstration job: Grade the linter over prose actually shipped from this repository.

```shoggoth-demonstration
{
  "schema": "shoggoth-demonstration/v1",
  "skill": "brevitas",
  "plugin": "brevitas",
  "status": "constructed",
  "claim_id": "brevitas-held-corpus",
  "claim": "The registered offline path exercises brevitas over checked-in inputs and exits zero.",
  "non_claim": "Every material input was created for this repository's own tests, so the run establishes nothing about real-world data.",
  "network": {
    "policy": "denied"
  },
  "timeout_seconds": 600,
  "sources": [
    {
      "id": "input",
      "class": "fixture",
      "path": "plugins/brevitas/skills/brevitas/evals/corpus.json",
      "sha256": "ca152210fa7c4ffa12d15e31eb89da5b749cbb60c2a9f0a10e5b9eb64fac05e1"
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
        "plugins/brevitas/tests",
        "-t",
        "plugins/brevitas"
      ],
      "expect_exit": 0
    }
  ],
  "observations": [
    "The command exits 0 in about 0.8 seconds with no network.",
    "Its last reported line is: OK"
  ],
  "frontier": {
    "version": "brevitas-demo-v0.1.0",
    "status": "open",
    "revision": "corpus-from-shipped-prose",
    "sha256": "8e0d96b600634737063d530322aa2bd2333ce72727c6e6ed0cb74e35a6585e1b",
    "current": "The held corpus grades the linter over labelled specimens.",
    "next": "Grade the linter over prose actually shipped from this repository."
  }
}
```

## History

| Version | Axis | Demo frontier revision | Demo frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `brevitas-demo-v0.1.0` | baseline | `corpus-from-shipped-prose` | `8e0d96b600634737063d530322aa2bd2333ce72727c6e6ed0cb74e35a6585e1b` | `docs/decisions/ADR-068-govern-real-data-demonstrations-separately.md` | The demonstration lane starts here. Status `constructed` is decided by the material inputs above, not by the prose. |
