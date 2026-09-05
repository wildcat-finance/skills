# Kronos demonstration ledger

Contract: [skill demonstration contract](../DEMONSTRATIONS.md)

- Current demonstration version: `kronos-demo-v0.1.0`
- Demo frontier status: `open`
- Demo frontier revision: `ranking-over-recorded-passes`
- Current demonstration: The scoreboard validates, records and refuses passes over fixtures.
- Next demonstration job: Rank a real frontier from recorded passes and show the selection it made.

```shoggoth-demonstration
{
  "schema": "shoggoth-demonstration/v1",
  "skill": "kronos",
  "plugin": "hexaemeron",
  "status": "constructed",
  "claim_id": "kronos-scoreboard-pass",
  "claim": "The registered offline path exercises kronos over checked-in inputs and exits zero.",
  "non_claim": "Every material input was created for this repository's own tests, so the run establishes nothing about real-world data.",
  "network": {
    "policy": "denied"
  },
  "timeout_seconds": 600,
  "sources": [
    {
      "id": "input",
      "class": "fixture",
      "path": "plugins/hexaemeron/tests/test_kronos_scoreboard.py",
      "sha256": "0fd6c9c81a9211ff07911333c5989b3766aaaeab13d48da50de2033e688cc0f1"
    }
  ],
  "commands": [
    {
      "id": "run",
      "argv": [
        "python3",
        "-m",
        "unittest",
        "plugins.hexaemeron.tests.test_kronos_scoreboard"
      ],
      "expect_exit": 0
    }
  ],
  "observations": [
    "The command exits 0 in about 4.2 seconds with no network.",
    "Its last reported line is: OK"
  ],
  "frontier": {
    "version": "kronos-demo-v0.1.0",
    "status": "open",
    "revision": "ranking-over-recorded-passes",
    "sha256": "e20ad39e4642589901a592ea224ce869aedd97973c5754a9cd588b4ab9d8af99",
    "current": "The scoreboard validates, records and refuses passes over fixtures.",
    "next": "Rank a real frontier from recorded passes and show the selection it made."
  }
}
```

## History

| Version | Axis | Demo frontier revision | Demo frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `kronos-demo-v0.1.0` | baseline | `ranking-over-recorded-passes` | `e20ad39e4642589901a592ea224ce869aedd97973c5754a9cd588b4ab9d8af99` | `adr/govern-real-data-demonstrations-separately` | The demonstration lane starts here. Status `constructed` is decided by the material inputs above, not by the prose. |
