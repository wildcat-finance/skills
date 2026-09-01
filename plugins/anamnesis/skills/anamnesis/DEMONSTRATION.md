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
  "non_claim": "It does not establish that any finding is real or that any remediation is correct.",
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
    "The command exits 0 in about 0.1 seconds with no network.",
    "Its last reported line is: 5. baseline, not a threshold: 0.01s wall clock, peak resident 30392320 bytes. No budget is declared for either, so neither gates."
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
| `anamnesis-demo-v0.1.0` | baseline | `second-preserved-audit-corpus` | `04859403f738c0e6c358e794307f9db5abecd53f5ec8ec2dd7a2863886086374` | `docs/decisions/ADR-068-govern-real-data-demonstrations-separately.md` | The demonstration lane starts here. Status `real-data` is decided by the material inputs above, not by the prose. |
