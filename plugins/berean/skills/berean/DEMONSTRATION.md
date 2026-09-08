# Berean demonstration ledger

Contract: `plugins/hexaemeron/skills/DEMONSTRATIONS.md`

- Current demonstration version: `berean-demo-v0.2.0`
- Demo frontier status: `open`
- Demo frontier revision: `replace-the-model-answer-records`
- Current demonstration: The Wildcat documents and five fixed-block market calls are captured sources; the ten graded answer cases are authored fixtures.
- Next demonstration job: Record answers from an actual agent run so no material input is written for the demonstration.

```shoggoth-demonstration
{
  "schema": "shoggoth-demonstration/v1",
  "skill": "berean",
  "plugin": "berean",
  "status": "mixed",
  "claim_id": "berean-wildcat-grounded-answers",
  "claim": "The offline Wildcat demo rebuilds all 18 release components, checks its unsigned Ariadne binding and exercises citation, block and missing-read refusals.",
  "non_claim": "Authored answers and constructed adversarial specimens keep the demonstration mixed; it establishes no live agent behaviour, current market state, canonical-chain membership or proof of call results.",
  "network": {
    "policy": "denied"
  },
  "timeout_seconds": 120,
  "sources": [
    {
      "id": "docs",
      "class": "protocol",
      "path": "plugins/berean/examples/wildcat-mainnet-v0/inputs/docs-provenance.json",
      "sha256": "2538cd5a485a92213bc543fa4183e23abb51ac96f613c2d54ab2676453865589"
    },
    {
      "id": "calls",
      "class": "protocol",
      "path": "plugins/berean/examples/wildcat-mainnet-v0/release/reads.jsonl",
      "sha256": "18b9ead3058f27f8e5260d0b65b50e27dea89951bca69fb85319481a01f7af95"
    },
    {
      "id": "answers",
      "class": "model-record",
      "path": "plugins/berean/examples/wildcat-mainnet-v0/release/answers/grounded.json",
      "sha256": "6ece153f0a313432b124f5be4379c81e2f605963a64881a2df272cbaa74a48d5"
    },
    {
      "id": "adversarial",
      "class": "fixture",
      "path": "plugins/berean/examples/wildcat-mainnet-v0/release/corpus/constructed/poison.md",
      "sha256": "a9cdd0b6c01928f720cbc597fc89746eddb3736cb6593f9ff2e5e2d8e6544f15"
    },
    {
      "id": "demo",
      "class": "repository",
      "path": "plugins/berean/examples/wildcat-mainnet-v0/demo.py",
      "sha256": "df6ea2af04724903dfacf2b875176282104c288098673aa92356e7f7957a4337"
    },
    {
      "id": "statement",
      "class": "repository",
      "path": "plugins/berean/examples/wildcat-mainnet-v0/grounded-agent.intoto.json",
      "sha256": "0d315ca32edb9169de0f592fea631293813ccb4c8d6d5d17222465b0fa003c8a"
    }
  ],
  "commands": [
    {
      "id": "run",
      "argv": [
        "python3",
        "plugins/berean/examples/wildcat-mainnet-v0/demo.py"
      ],
      "expect_exit": 0
    }
  ],
  "observations": [
    "run: json components 18",
    "run: json cases 10",
    "run: json status \"mixed\"",
    "run: json model_executed false",
    "run: json refusals {\"block\":\"answer-reads\",\"citation\":\"answer-citations\",\"missing-read\":\"answer-reads\"}"
  ],
  "frontier": {
    "version": "berean-demo-v0.2.0",
    "status": "open",
    "revision": "replace-the-model-answer-records",
    "sha256": "7ec4787d28c3f804c9ffa4ec2464e1dbd16fc9e73845ecb7bfdcabaf88c85caa",
    "current": "The Wildcat documents and five fixed-block market calls are captured sources; the ten graded answer cases are authored fixtures.",
    "next": "Record answers from an actual agent run so no material input is written for the demonstration."
  }
}
```

## History

| Version | Axis | Demo frontier revision | Demo frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `berean-demo-v0.1.0` | baseline | `replace-the-model-answer-records` | `b026ea251c0eea0b54710a31ca7222d404eca6eb813844a041b5a529dc3d1c04` | `adr/govern-real-data-demonstrations-separately` | The demonstration lane starts here. Status `mixed` is decided by the material inputs above, not by the prose. |
| `berean-demo-v0.2.0` | generation | `replace-the-model-answer-records` | `7ec4787d28c3f804c9ffa4ec2464e1dbd16fc9e73845ecb7bfdcabaf88c85caa` | [Wildcat demo](../../examples/wildcat-mainnet-v0/demo.py) | Captured Wildcat documents and calls replace the reference demonstration inputs; authored answers retain mixed status and the actual-agent-answer job remains open. |
