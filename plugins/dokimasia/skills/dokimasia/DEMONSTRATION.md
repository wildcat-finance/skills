# Dokimasia demonstration ledger

Contract: `plugins/hexaemeron/skills/DEMONSTRATIONS.md`

- Current demonstration version: `dokimasia-demo-v0.1.0`
- Demo frontier status: `open`
- Demo frontier revision: `rebuild-from-preserved-primary-inputs`
- Current demonstration: The committed wildcat-app-v2 scrutiny is internally consistent across its real coverage record, scrutiny record, and rendered report.
- Next demonstration job: Preserve the pinned application and workbook inputs, then rebuild the scrutiny from those primary bytes.

```shoggoth-demonstration
{
  "schema": "shoggoth-demonstration/v1",
  "skill": "dokimasia",
  "plugin": "dokimasia",
  "status": "real-data",
  "claim_id": "dokimasia-wildcat-app-v2-scrutiny",
  "claim": "The committed wildcat-app-v2 coverage record, scrutiny record, and rendered report agree on the examined real application and workbook evidence.",
  "non_claim": "The pinned application checkout and workbook bytes are not preserved here, so this does not regenerate the scrutiny from its primary inputs or state that any route or workbook case passed; the rendered report leaves 59 of 261 scoped items without a disposition.",
  "network": {
    "policy": "denied"
  },
  "timeout_seconds": 120,
  "sources": [
    {
      "id": "coverage",
      "class": "production-run",
      "path": "plugins/dokimasia/docs/evidence/wildcat-app-v2.coverage.json",
      "sha256": "833867da0900f38b179afbf79077378b216c6280bb61f96063bf102c7262c7b4"
    },
    {
      "id": "scrutiny",
      "class": "production-run",
      "path": "plugins/dokimasia/docs/evidence/wildcat-app-v2.scrutiny.json",
      "sha256": "4d7640be8d19b2d568c691d095ff00fb7f0417614e00b7549ca3738d626437be"
    },
    {
      "id": "report",
      "class": "production-run",
      "path": "plugins/dokimasia/docs/evidence/wildcat-app-v2-scrutiny.md",
      "sha256": "f0555ad692e46c86965b0d4eaf363a41602510a27d51fd10587b5fbecb2c4264"
    }
  ],
  "commands": [
    {
      "id": "check",
      "argv": [
        "python3",
        "plugins/dokimasia/scripts/dokimasia.py",
        "demonstrate",
        "--check"
      ],
      "expect_exit": 0
    }
  ],
  "observations": [
    "check: line \"dokimasia demonstrate: check clean; a scrutiny is deterministic, each moved identity names its own cause, an unexplained move is reported, and the committed evidence regenerates\""
  ],
  "frontier": {
    "version": "dokimasia-demo-v0.1.0",
    "status": "open",
    "revision": "rebuild-from-preserved-primary-inputs",
    "sha256": "cf452282ed53f21054beab6fb964cc8393057c690fea51b19be0c76e9630ac53",
    "current": "The committed wildcat-app-v2 scrutiny is internally consistent across its real coverage record, scrutiny record, and rendered report.",
    "next": "Preserve the pinned application and workbook inputs, then rebuild the scrutiny from those primary bytes."
  }
}
```

## History

| Version | Axis | Demo frontier revision | Demo frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `dokimasia-demo-v0.1.0` | baseline | `rebuild-from-preserved-primary-inputs` | `cf452282ed53f21054beab6fb964cc8393057c690fea51b19be0c76e9630ac53` | `adr/govern-real-data-demonstrations-separately` | The demonstration lane starts here. Status `real-data` describes the preserved production-run records; the non-claim keeps the absent primary inputs visible. |
