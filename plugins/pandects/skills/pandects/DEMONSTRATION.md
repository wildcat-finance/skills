# Pandects demonstration ledger

Contract: `plugins/hexaemeron/skills/DEMONSTRATIONS.md`

- Current demonstration version: `pandects-demo-v0.1.0`
- Demo frontier status: `open`
- Demo frontier revision: `laws-over-a-deployed-market`
- Current demonstration: The catalogue renders its executable laws and their broken specimens.
- Next demonstration job: Run the catalogue against a deployed credit market and report the campaign.

```shoggoth-demonstration
{
  "schema": "shoggoth-demonstration/v1",
  "skill": "pandects",
  "plugin": "pandects",
  "status": "constructed",
  "claim_id": "pandects-law-catalogue",
  "claim": "The registered offline path exercises pandects over checked-in inputs and exits zero.",
  "non_claim": "Every material input was created for this repository's own tests, so the run establishes nothing about real-world data.",
  "network": {
    "policy": "denied"
  },
  "timeout_seconds": 300,
  "sources": [
    {
      "id": "input",
      "class": "fixture",
      "path": "plugins/pandects/catalogue/pandects.json",
      "sha256": "0bdca07560610ab4b237499db1ae7b85be8c07fd7ddf7aa22617e17c5161c725"
    }
  ],
  "commands": [
    {
      "id": "run",
      "argv": [
        "python3",
        "plugins/pandects/scripts/pandects.py",
        "laws"
      ],
      "expect_exit": 0
    }
  ],
  "observations": [
    "The command exits 0 in about 0.0 seconds with no network.",
    "Its last reported line is:                                             applies to: a pooled lender claim denominated in one asset, with withdrawals recorded as an ordered queue of individual claims that keep"
  ],
  "frontier": {
    "version": "pandects-demo-v0.1.0",
    "status": "open",
    "revision": "laws-over-a-deployed-market",
    "sha256": "1a79abe5a57ced1b8954c2ebac2503958da24fbb051cbd67de37316122193ae3",
    "current": "The catalogue renders its executable laws and their broken specimens.",
    "next": "Run the catalogue against a deployed credit market and report the campaign."
  }
}
```

## History

| Version | Axis | Demo frontier revision | Demo frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `pandects-demo-v0.1.0` | baseline | `laws-over-a-deployed-market` | `1a79abe5a57ced1b8954c2ebac2503958da24fbb051cbd67de37316122193ae3` | `docs/decisions/ADR-068-govern-real-data-demonstrations-separately.md` | The demonstration lane starts here. Status `constructed` is decided by the material inputs above, not by the prose. |
