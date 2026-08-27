# Elenchus evolution ledger

Policy: [../VERSIONING.md](../VERSIONING.md)

- Current version: `elenchus-v1.3.0`
- Frontier status: `mature`
- Frontier revision: `observed-failure-root-cause`
- Current frontier: A check overlays a fix's changed tests onto the parent and classifies unittest, Forge and Node guards from fresh runner-owned reports, while diagnostics remain inert evidence.
- Next Fiat job: None -- mature

## History

| Version | Axis | Frontier revision | Frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `elenchus-v0.1.0` | baseline | `observed-failure-root-cause` | `82ba62d430f8c7d248bcef1b2678aca9c56eefd21282a54cbce24d78e444cd8a` | [fiat audit loop reference](../fiat/references/audit-loop.md) | Elenchus starts here, holding root-cause work on failures that have already been observed. |
| `elenchus-v1.1.0` | evolution | `observed-failure-root-cause` | `08e77bae576b3351d6f38e60ce9da88327014bcaa7459e319b8e51d79caeda8b` | [structured runner fixtures](../../tests/test_elenchus_checker.py), [study](../../docs/elenchus-structured-runner-reports/study.md) | The guard check replaces diagnostic matching with fresh unittest, Forge and Node report adapters; no evidenced next frontier remains. |
| `elenchus-v1.2.0` | generation | `observed-failure-root-cause` | `08e77bae576b3351d6f38e60ce9da88327014bcaa7459e319b8e51d79caeda8b` | [audit-round verdict study](../../docs/elenchus-audit-round-verdict/study.md), [runner fixture](../../tests/test_elenchus_checker.py) | A Fiat Warden takes the exact test command, report format, and report file from its source-bound runbook step and returns the four-state Elenchus verdict unchanged. The receipt records that declaration rather than attesting report bytes; stronger evidence binding remains issue 453. |
| `elenchus-v1.3.0` | generation | `observed-failure-root-cause` | `08e77bae576b3351d6f38e60ce9da88327014bcaa7459e319b8e51d79caeda8b` | [replay guard example](../../tests/test_elenchus_rpc_boundary_fixture.py), [study](../../../../docs/elenchus-rpc-boundary-fixtures/study.md) | The skill file gains `## Pin an RPC-boundary failure into a fixture`, a seven-step procedure that names the exact exchange, writes the plan with each request marked required or optional, captures with the endpoint URL held in the environment, verifies, guards behind `lazarus replay` with a `-32070` miss read as a failed test, commits plan, fixture and test together, and says what a fixture cannot pin. The example demonstrates the offline half against the shipped Goldfinch fixture over loopback and skips by name where the Lazarus dependencies are absent; no Lazarus file changed. A reference document beside the skill, an example inside the skill tree, a synthetic fixture carrying a recorded provider error and a fake-provider capture round trip were rejected in the linked study. The mature frontier and `None -- mature` stay. |
