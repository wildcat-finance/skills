# Router quotation regrade

The marketplace review corrected Homologia's description to its shipped
manifest and expected-integer admission boundary. Router case RS-38 now quotes
that current statement, including the refusal of execution and parity verdicts.
The quoted sentence contributes to the corpus digest, so its recorded grade
needed the owner's regrade operation.

This directory preserves `prior-corpus.json` exactly from Step 2 commit
`f05365a5980dcbe5bab9ebad789dad5ad5a3c89e`, including the original recorded run.
`recorded-answers.json` is an unchanged copy of the existing 41 recorded
selections in `docs/router-selection-driver/demonstration-answers.json`.

The owner driver emitted a new packet and tallied those same selections. It
observed 39 passes and two failures, unchanged: RS-33 selected Elenchus and
RS-38 refused as uncovered. The source model remains `codex-subagent-gpt-5`
and its recorded date remains `2026-09-05`. The separate `regraded_at` field in
`regrade.json` records this tally's time. No new model executed, and this tally
says nothing about how the model would route after the prose changes.

`manifest.json` is the emitted packet manifest. `regrade.json` retains both run
blocks, the answer digest and the exact commands. Case IDs, requests,
expectations, the prompt template and recorded answers remain unchanged.
Outside RS-38's deciding sentence, only the owner-produced `runs` block changed
in the main corpus. The two negative guard fixtures retain their deliberate
faults and receive only the same quotation refresh.
