# Synkrisis report: cross-run-v0

Producer contract `promise-machine-run-observation/v1`. Cohort digest `b27afaf63ddfa37ea7e8f0d11b08f971ae4a124a519c21a157eb36269910063d`. Rule
catalogue digest `259bb4e56556392cd38caafd605ef5b9f71eedeb18dbb9ded7eb3723dfe4b7ce`. Every claim below is recomputed from
named observation events; the report adds no number, run or verdict of
its own.

## Findings

### late-boundary-consultation/v1

- Fingerprint: `cfd51ed7461f02a95a4c48efca56947e779bad1cffcd960b58122b9b19184783`
- Subject: `cross-run-v0/worker/mason`
- Evidence class: inferred
- Observed relation: In 2 of 2 orderable run pairs, the run that first read repository.boundary.read after half its events recorded more output tokens than a run that read it earlier; 2 late and 1 early runs were compared.
- Runs and events: run-alpha (evt-2); run-beta (evt-6); run-gamma (evt-8)
- Counterevidence: none recorded
- Unknown runs: run-epsilon
- Nearest forbidden claim, not made: Late boundary consultation raises token spend. The recorded events support an association between two observations in this cohort, not a mechanism.
- Suggested handoff: horos (Horos owns the reading boundary; a person may ask it whether earlier orientation output would change the observed association.)

### unchanged-retry-before-handoff/v1

- Fingerprint: `70ac6dd4d920a5eef5af4239b5ac4d8920d913b469bb3ee23009855833d6ed03`
- Subject: `cross-run-v0/worker/mason`
- Evidence class: inferred
- Observed relation: 1 run(s) scheduled at least 2 retries of one unchanged capability before recording a handoff to elenchus.
- Runs and events: run-gamma (evt-4, evt-7, evt-10)
- Counterevidence: none recorded
- Unknown runs: run-epsilon
- Nearest forbidden claim, not made: Retrying without a change wastes the run. The recorded events support only that unchanged retries preceded the handoff in these runs.
- Suggested handoff: elenchus (Elenchus owns failure triage; a person may ask it whether the retried capability deserved a cause-first path instead of repetition.)

## Boundary

Findings are bounded inferred relations between recorded events. They
carry no cause, no model judgement, no completeness claim and no
action; a person selects what, if anything, happens next.
