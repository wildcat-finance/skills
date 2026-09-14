# App-v2 boundary CI delivery for issue 1357

[Issue #1484](https://github.com/wildcat-finance/skills/issues/1484) remains
open as of 2026-09-14. Delivery is held before the production release.
The boundary repair is in develop and passes CI.
[Release PR #428](https://github.com/wildcat-finance/wildcat-app-v2/pull/428)
requires a new review before merging to main. This record supplies no completion claim for #1484 or
its parent, [#1357](https://github.com/wildcat-finance/skills/issues/1357).

## Ownership and approvals

Shoggoth, via Codex, produced this record and the repair under Dave Coleman's
instructions. Dave raised the production-branch boundary on 2026-09-14;
this delivery stops before merging the app release or making further app-v2
changes. The Skills draft and issue status preserve the handoff.

Dave (`kethcode`) and `allend13` approved release head
`3e6cfec64cc883ffb1757a29f61b75e6bb82bcc3` on 2026-09-09. Their
[first](https://github.com/wildcat-finance/wildcat-app-v2/pull/428#pullrequestreview-5155491551)
and [second](https://github.com/wildcat-finance/wildcat-app-v2/pull/428#pullrequestreview-5158099057)
reviews are now marked `DISMISSED`. GitHub reports `REVIEW_REQUIRED` for the
updated release head; no replacement approval is recorded.

PR #428's body discloses that adding or removing tracked files requires
regenerating the boundary. The new review must cover that recurring cost;
this work records no new human decision or permission to bypass a gate.

## Existing delivery and repair

The marking from [PR #360](https://github.com/wildcat-finance/wildcat-app-v2/pull/360)
merged into develop as `b15b9e459648ba9be92f90e61eecdbda9875e3fc`.
The workflow from [PR #426](https://github.com/wildcat-finance/wildcat-app-v2/pull/426)
merged there as `4799e59cf24cf973747972a4417e6e08f9fc14cf`.
Main remains at `564a189bb9cdc9394b3fd4f444531a261ada99b3`, without #426.

The signed [repair commit](https://github.com/wildcat-finance/wildcat-app-v2/commit/c58d5418c115e89f0a3e871b0f129a3dca033f6e)
regenerates the boundary and census after a tracked test arrived. It reached
develop through a signed fast-forward update to the existing release PR's
head. No separate repair PR was needed.
`counts.files_walked` changes from 1,063 to 1,064. All 13 boundary entries,
their 13,407,206 bytes, the 117 candidates, the marking and the workflow are
preserved. The census records 1,136 files and 17,166,393 bytes.

## Verification

The classifier is the existing CI pin,
`wildcat-finance/skills@12cbe2e6ed95decd6d9d355740f2dbd052956abe`.
The app validation on 2026-09-14 used `python3` reporting `3.12.3`, matching
the minor version declared in the app's workflow.

| Check | Subject | Exit/result |
| --- | --- | --- |
| Original boundary | Develop head above | 1: file-count drift |
| Regenerated boundary | Repair tree | 0 |
| Changed entry | Lockfile byte count increased by one | 1: entry drift |
| Added tracked file | Temporary staged probe | 1: file-count drift |
| Restored tree | Repair tree | 0 |

The hosted [PR boundary job](https://github.com/wildcat-finance/wildcat-app-v2/actions/runs/34809688062/job/103868368559)
and [develop boundary job](https://github.com/wildcat-finance/wildcat-app-v2/actions/runs/34809685094/job/103868359697)
passed at `c58d5418c115e89f0a3e871b0f129a3dca033f6e`.
[`appci.json`](appci.json) preserves commands, outputs, input/output SHA-256
digests, source revisions, reviews and CI links. These checks establish the
repair's stated behaviour. The parent records historical TypeScript extractor
coverage of 2,237 of 2,239 declarations, with 2 confessed misses and zero
unconfessed misses. This repair did not rerun that compiler comparison.

## Remaining acceptance

Both required Snyk contexts pass on the updated head. `code/snyk (wildcat-app)`
reports `No new Code Analysis issues found` at 2026-09-14T05:27:51Z; the
September 9 quota error is superseded. The Open Source context reports no
manifest changes, rather than a new full dependency scan. The release still
has non-required commitlint and Netlify failures, preserved in the JSON record.

The app maintainer owns the remaining release work after this stop:

1. Obtain a new GitHub review for release PR #428. Both earlier approvals
   are dismissed, and the current review decision blocks merging.
2. Merge #428 through the protected release route, then record the actual
   main integration SHA and a green boundary job on that exact SHA. Both
   fields remain null. This draft's PR must link the completed record
   before #1484 can close.

Creating a separate repair PR returned HTTP 403 under the available tokens.
Updating the existing release PR through SSH resolved that delivery step.
