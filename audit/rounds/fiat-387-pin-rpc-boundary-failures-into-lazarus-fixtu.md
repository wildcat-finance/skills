## Step 1, round 1 -- 2026-08-26T01:44:58Z

Audit schema: fiat-audit-round/v2

Covered: replay-subprocess-argv=reviewed; replay-loopback-port=reviewed; replay-teardown=reviewed; provider-url-absent=reviewed; capture-credential-env=reviewed; dependency-guard-skip=reviewed; recorded-response-exact=reviewed; miss-asserted-closed=reviewed; write-method-refused=reviewed; prose-guard-red-first=reviewed; no-lazarus-edits=reviewed; lazarus-frontier-untouched=reviewed; ledger-integrity=reviewed; version-surfaces=reviewed; prose-matches-lazarus=reviewed; error-text-is-data=reviewed; hexaemeron-stdlib-only=reviewed; skip-visible-in-report=reviewed; partial-run=reviewed

Not checked: the waived Pashov suite (x-ray, solidity-auditor, fizz) by design, since no Solidity changed; a live capture against a provider and the recorded-provider-error path, which only Lazarus's own test_capture.py exercises; the replay class on Python 3.9.6, which skips there for want of the Lazarus dependencies; hosted CI; the controller receipt, push and publication; the report-byte binding issue 453 owns

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: the study and runbook count fourteen synopsis pairs where audit_synopsis.py --check . lists thirteen at this tree (the fiat-447 audit branch carries the fourteenth), an entry-state observation in digest-bound text that only a study amendment could change; the loopback guard's ipaddress.ip_address(address[0]) would raise ValueError rather than the intended AssertionError for a non-numeric host, which no path in the module produces and which is a non-pass either way; a miss fragment whose params carry a moving block tag is schema-valid yet refused by capture at plan validation, which step 2's fixed block already forecloses; on a 3.9 interpreter that did carry the dependencies the replay subprocess would fail at Lazarus's 3.11 floor and the class would error with the captured stderr rather than skip, a fail-closed outcome no interpreter here reaches
