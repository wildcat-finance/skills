# Fiat demonstration ledger

Contract: [skill demonstration contract](../DEMONSTRATIONS.md)

- Current demonstration version: `fiat-demo-v1.1.0`
- Demo frontier status: `open`
- Demo frontier revision: `success-criteria-controller-join`
- Current demonstration: A disposable Git-backed run executes the successor controller and records shared, refusal, replay and vacuous outcomes.
- Next demonstration job: Replay a preserved signed controller run from a checkpoint on a clean machine.

```shoggoth-demonstration
{"schema":"shoggoth-demonstration/v1","skill":"fiat","plugin":"hexaemeron","status":"constructed","claim_id":"fiat-success-criteria-controller","claim":"The registered offline path runs the successor controller in a disposable Git-backed fixture and records its bounded result and refusals.","non_claim":"The fixture does not establish criterion sufficiency, semantic correctness, host isolation, production performance, or remote GitHub state.","network":{"policy":"denied"},"timeout_seconds":900,"sources":[{"id":"demonstration-test","class":"fixture","path":"plugins/hexaemeron/tests/test_fiat_criteria_demonstration.py","sha256":"18cec0703b6b1d552ab27ff8cc82e6344031e91088482612b723a28ebc545765"}],"commands":[{"id":"run","argv":["python3","-m","unittest","plugins.hexaemeron.tests.test_fiat_criteria_demonstration"],"expect_exit":0}],"observations":["run: line \"OK\""],"frontier":{"version":"fiat-demo-v1.1.0","status":"open","revision":"success-criteria-controller-join","sha256":"4974cd271e051122fdf3714488d5bd72165e2ef6d6e1900313ca774efd4c2547","current":"A disposable Git-backed run executes the successor controller and records shared, refusal, replay and vacuous outcomes.","next":"Replay a preserved signed controller run from a checkpoint on a clean machine."}}
```

## History

| Version | Axis | Demo frontier revision | Demo frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `fiat-demo-v0.1.0` | baseline | `replay-a-preserved-run` | `fc4e742709eb564873abb6aacd7048bb5c09b0f9a4d0f3b5a62ae40574986955` | `adr/govern-real-data-demonstrations-separately` | The demonstration lane starts here. Status `constructed` is decided by the material inputs above, not by the prose. |
| `fiat-demo-v1.1.0` | evolution | `success-criteria-controller-join` | `4974cd271e051122fdf3714488d5bd72165e2ef6d6e1900313ca774efd4c2547` | skills#1273, [joined proof](../../../../docs/protasis-success-criteria/demonstration.md) | The successor controller now runs in a disposable Git-backed fixture and records a shared Exit, bounded refusals, read-only replay and a vacuous pass without claiming criterion sufficiency. |
