# Berean demonstration ledger

Contract: `plugins/hexaemeron/skills/DEMONSTRATIONS.md`

- Current demonstration version: `berean-demo-v0.1.0`
- Demo frontier status: `open`
- Demo frontier revision: `replace-the-model-answer-records`
- Current demonstration: The Aave v4 chain reads are real and the graded answers beside them are records written for the example.
- Next demonstration job: Record answers from an actual agent run so no material input is written for the demonstration.

```shoggoth-demonstration
{
  "schema": "shoggoth-demonstration/v1",
  "skill": "berean",
  "plugin": "berean",
  "status": "mixed",
  "claim_id": "berean-goldfinch-grounded-answers",
  "claim": "The grounded-agent example releases and verifies answers whose citations resolve to exact corpus bytes.",
  "non_claim": "The answers are model records written for the example, so the run does not establish live agent behaviour.",
  "network": {
    "policy": "denied"
  },
  "timeout_seconds": 900,
  "sources": [
    {
      "id": "input-1",
      "class": "protocol",
      "path": "plugins/berean/examples/aave-v4-demo-v0/release/corpus-manifest.json",
      "sha256": "5e7bd0585af5ae4ce077123c84a105e018e0133d6c4c193f6bf01b67634bfcc6"
    },
    {
      "id": "input-2",
      "class": "model-record",
      "path": "plugins/berean/examples/aave-v4-demo-v0/release/answers/grounded.json",
      "sha256": "d872c7398bbffbca9ffb56a40a2083e3ccd2ed5032d747a79cfa48ec7d6e9951"
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
        "plugins/berean/tests",
        "-t",
        "plugins/berean"
      ],
      "expect_exit": 0
    }
  ],
  "observations": [
    "The command exits 0 in about 0.5 seconds with no network.",
    "Its last reported line is: OK (skipped=1)"
  ],
  "frontier": {
    "version": "berean-demo-v0.1.0",
    "status": "open",
    "revision": "replace-the-model-answer-records",
    "sha256": "b026ea251c0eea0b54710a31ca7222d404eca6eb813844a041b5a529dc3d1c04",
    "current": "The Aave v4 chain reads are real and the graded answers beside them are records written for the example.",
    "next": "Record answers from an actual agent run so no material input is written for the demonstration."
  }
}
```

## History

| Version | Axis | Demo frontier revision | Demo frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `berean-demo-v0.1.0` | baseline | `replace-the-model-answer-records` | `b026ea251c0eea0b54710a31ca7222d404eca6eb813844a041b5a529dc3d1c04` | `adr/govern-real-data-demonstrations-separately` | The demonstration lane starts here. Status `mixed` is decided by the material inputs above, not by the prose. |
