# Anamnesis demonstration ledger

Contract: `plugins/hexaemeron/skills/DEMONSTRATIONS.md`

- Current demonstration version: `anamnesis-demo-v0.5.0`
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
      "sha256": "5674de5f5a21e47d7b614c2d9bcb0f8ec1f0d3b1290571e77a08e8660b67deed"
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
    "run: line \"1. two fresh builds agree on 41d640fb168049d5061e12c9d7282dafad2266343eeb0be2a078db8797c0bfbf across 7 components\"",
    "run: line \"2. the committed release verifies: 41 finding(s), 31 round(s), 12 with no findings\"",
    "run: line \"3. Elenchus analogues for severity high: 2; verdict None\"",
    "run: line \"4. Synkrisis cohort cohort:41d640fb168049d5: 41 included against 41 findings; 0 exclusion(s), 144 unknown(s)\""
  ],
  "frontier": {
    "version": "anamnesis-demo-v0.5.0",
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
| `anamnesis-demo-v0.2.0` | generation | `second-preserved-audit-corpus` | `04859403f738c0e6c358e794307f9db5abecd53f5ec8ec2dd7a2863886086374` | `adr/declared-corpus-scope`, [test_s8_scope.py](../../tests/test_s8_scope.py) | The pilot was re-released under a declared corpus scope and the record re-pinned to the new program digest and release id without moving the demo frontier. |
| `anamnesis-demo-v0.3.0` | generation | `second-preserved-audit-corpus` | `04859403f738c0e6c358e794307f9db5abecd53f5ec8ec2dd7a2863886086374` | `issue/1465`, [test_s8_scope.py](../../tests/test_s8_scope.py) | `verify` takes an optional event sink, so the declared-scope refusal leaves the durable event an operator is told to read. The record is re-pinned to the new program digest; the release id, the observations and the demo frontier are unmoved. |
| `anamnesis-demo-v0.4.0` | generation | `second-preserved-audit-corpus` | `04859403f738c0e6c358e794307f9db5abecd53f5ec8ec2dd7a2863886086374` | `issue/1464`, [test_s11_registry.py](../../tests/test_s11_registry.py) | The curation policy's declared mapper is resolved through a module-level registry: an unresolved name refuses `A078` before any record is written, and every assertion records the entry that ran. The record is re-pinned to the new program digest; both shipped release ids, the observations and the demo frontier are unmoved. |
| `anamnesis-demo-v0.5.0` | generation | `second-preserved-audit-corpus` | `04859403f738c0e6c358e794307f9db5abecd53f5ec8ec2dd7a2863886086374` | `issue/1464`, [test_s12_synopsis.py](../../tests/test_s12_synopsis.py) | A second registry entry reads `fiat-audit-synopsis/v1`, refusing `A079` on a missing or non-matching schema header before any row, and a third specimen preserves the pilot's same 41 findings through it. The record is re-pinned to the new program digest; both shipped release ids, the observations and the demo frontier are unmoved. |
