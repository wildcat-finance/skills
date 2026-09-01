## Step 1, round 1 -- 2026-09-01T00:10:39Z

Audit schema: fiat-audit-round/v2

Covered: selection-binding=reviewed; block-shape=reviewed; path-confinement=reviewed; home-classification=reviewed; duplicate-home=reviewed; legacy-scope=reviewed; mirror-drift=reviewed; ledger-arithmetic=reviewed; prose-reconciliation=reviewed

Not checked: repository-wide semantic duplicate detection, where the same decision sits in two homes and the study declares one, which SKILL.md and the `hypomnema-pointer-gate` boundary exclude by design; behaviour on a platform without `os.O_NOFOLLOW` or `os.O_DIRECTORY`, where `getattr` supplies 0 and the intermediate-component no-follow guarantee degrades silently, the final component staying covered by the `follow_symlinks=False` stat and `S_ISREG` check.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: a record path that exists on disk but resolves outside the supplied `--repo-root` refuses as `is unavailable or not an ordinary non-symlink file`, which is true relative to that root but does not separate absent from out-of-root; the message is not false and a change would churn substring assertions in the focused suite. `AGENTS.md` line 305 keeps the ordinary walk as the required lint scope and does not add study mode; that matches the `hypomnema-v4.4.0` reasoning against making a ledger a permanent gate, so it is deliberate rather than stale.
