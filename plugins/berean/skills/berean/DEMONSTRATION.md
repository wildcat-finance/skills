# Berean demonstration ledger

Contract: `plugins/hexaemeron/skills/DEMONSTRATIONS.md`

- Current demonstration version: `berean-demo-v0.1.0`
- Demo frontier status: `open`
- Demo frontier revision: `replace-the-model-answer-records`
- Current demonstration: The Goldfinch corpus is real and the graded answers beside it are records written for the example.
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
      "path": "plugins/berean/examples/goldfinch-demo-v0/release/corpus-manifest.json",
      "sha256": "279484f479e78d1391e9974d21f856a6130875cad74e8ceec75f48ae5076a99e"
    },
    {
      "id": "input-2",
      "class": "model-record",
      "path": "plugins/berean/examples/goldfinch-demo-v0/release/answers/grounded.json",
      "sha256": "a36cd2fccc2c6211a78c2cb1783e6d5e650390c613069404f47b8f267473fab5"
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
    "The command exits 0 in about 0.3 seconds with no network.",
    "Its last reported line is: OK (skipped=1)"
  ],
  "frontier": {
    "version": "berean-demo-v0.1.0",
    "status": "open",
    "revision": "replace-the-model-answer-records",
    "sha256": "f85cd906ca7a3de69891703de54cc6710c1b223d3960ebaeca627808fb457543",
    "current": "The Goldfinch corpus is real and the graded answers beside it are records written for the example.",
    "next": "Record answers from an actual agent run so no material input is written for the demonstration."
  }
}
```

## History

| Version | Axis | Demo frontier revision | Demo frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `berean-demo-v0.1.0` | baseline | `replace-the-model-answer-records` | `f85cd906ca7a3de69891703de54cc6710c1b223d3960ebaeca627808fb457543` | `adr/govern-real-data-demonstrations-separately` | The demonstration lane starts here. Status `mixed` is decided by the material inputs above, not by the prose. |
