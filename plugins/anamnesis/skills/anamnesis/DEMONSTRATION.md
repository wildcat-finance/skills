# Anamnesis demonstration ledger

Contract: `plugins/hexaemeron/skills/DEMONSTRATIONS.md`

- Current demonstration version: `anamnesis-demo-v0.1.0`
- Demo frontier status: `open`
- Demo frontier revision: `second-preserved-audit-corpus`
- Current demonstration: The pilot specimen runs the whole admission-to-projection path over preserved bytes.
- Next demonstration job: Admit a second independent audit corpus so the path is shown over more than one producer.

```shoggoth-demonstration
{
  "schema": "shoggoth-demonstration/v1",
  "skill": "anamnesis",
  "plugin": "anamnesis",
  "status": "real-data",
  "claim_id": "anamnesis-corpus-demo",
  "claim": "The pilot audit specimen admits, curates and projects offline from preserved producer bytes.",
  "non_claim": "It does not establish that the corpus is complete, that any finding is real, or that any remediation is correct.",
  "network": {
    "policy": "denied"
  },
  "timeout_seconds": 600,
  "sources": [
    {
      "id": "input",
      "class": "audit",
      "path": "plugins/anamnesis/specimens/pilot/policy.json",
      "sha256": "5de0d04c338776fd29cc6e27a902fac498a1335700dce1eae7b364ba67cf8901"
    },
    {
      "id": "program",
      "class": "repository",
      "path": "plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py",
      "sha256": "6318f3ae4cd74e35354d706a1216fa76fea2b6446a2fc2f5b45ad1a61401e645"
    }
  ],
  "commands": [
    {
      "id": "run",
      "argv": [
        "python3",
        "plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py",
        "demo",
        "--specimen",
        "plugins/anamnesis/specimens/pilot"
      ],
      "expect_exit": 0
    }
  ],
  "observations": [
    "run: line \"1. two fresh builds agree on 079ed18d172d6031551cbda55d25a2c064d255186cd8e27a62e90d26da06ae56 across 7 components\"",
    "run: line \"2. the committed release verifies: 41 finding(s), 31 round(s), 12 with no findings\"",
    "run: line \"3. Elenchus analogues for severity high: 2; verdict None\"",
    "run: line \"4. Synkrisis cohort cohort:079ed18d172d6031: 41 included against 41 findings; 0 exclusion(s), 144 unknown(s)\""
  ],
  "frontier": {
    "version": "anamnesis-demo-v0.1.0",
    "status": "open",
    "revision": "second-preserved-audit-corpus",
    "sha256": "04859403f738c0e6c358e794307f9db5abecd53f5ec8ec2dd7a2863886086374",
    "current": "The pilot specimen runs the whole admission-to-projection path over preserved bytes.",
    "next": "Admit a second independent audit corpus so the path is shown over more than one producer."
  }
}
```

## History

| Version | Axis | Demo frontier revision | Demo frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `anamnesis-demo-v0.1.0` | baseline | `second-preserved-audit-corpus` | `04859403f738c0e6c358e794307f9db5abecd53f5ec8ec2dd7a2863886086374` | `adr/govern-real-data-demonstrations-separately` | The demonstration lane starts here. Status `real-data` is decided by the material inputs above, not by the prose. |
