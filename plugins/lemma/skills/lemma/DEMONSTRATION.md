# Lemma demonstration ledger

Contract: `plugins/hexaemeron/skills/DEMONSTRATIONS.md`

- Current demonstration version: `lemma-demo-v0.1.0`
- Demo frontier status: `open`
- Demo frontier revision: `chunks-from-a-shipped-corpus`
- Current demonstration: The Markdown chunker produces validated chunks from the baseline input.
- Next demonstration job: Chunk a shipped protocol corpus and show the citations it supports.

```shoggoth-demonstration
{
  "schema": "shoggoth-demonstration/v1",
  "skill": "lemma",
  "plugin": "lemma",
  "status": "constructed",
  "claim_id": "lemma-markdown-chunks",
  "claim": "The registered offline path exercises lemma over checked-in inputs and exits zero.",
  "non_claim": "Every material input was created for this repository's own tests, so the run establishes nothing about real-world data.",
  "network": {
    "policy": "denied"
  },
  "timeout_seconds": 600,
  "sources": [
    {
      "id": "input",
      "class": "fixture",
      "path": "plugins/lemma/baseline/standard_input.py",
      "sha256": "718ffddb0e9725e42eb727a57d3295b7784d470416721d8e636e8fb2f5a906d3"
    }
  ],
  "commands": [
    {
      "id": "run",
      "argv": [
        "python3",
        "plugins/lemma/tests/test_markdown.py"
      ],
      "expect_exit": 0
    }
  ],
  "observations": [
    "The command exits 0 in about 1.0 seconds with no network.",
    "Its last reported line is: 0 failure(s)"
  ],
  "frontier": {
    "version": "lemma-demo-v0.1.0",
    "status": "open",
    "revision": "chunks-from-a-shipped-corpus",
    "sha256": "44b1934d0b2e75ecd0326ca9fb552f414afd7a87862cb3727cb1cc141e3c0549",
    "current": "The Markdown chunker produces validated chunks from the baseline input.",
    "next": "Chunk a shipped protocol corpus and show the citations it supports."
  }
}
```

## History

| Version | Axis | Demo frontier revision | Demo frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `lemma-demo-v0.1.0` | baseline | `chunks-from-a-shipped-corpus` | `44b1934d0b2e75ecd0326ca9fb552f414afd7a87862cb3727cb1cc141e3c0549` | `adr/govern-real-data-demonstrations-separately` | The demonstration lane starts here. Status `constructed` is decided by the material inputs above, not by the prose. |
