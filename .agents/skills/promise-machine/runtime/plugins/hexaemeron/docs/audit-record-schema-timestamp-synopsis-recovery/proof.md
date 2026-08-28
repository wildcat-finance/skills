# Issue 429 recovery proof

This proof covers the recovered pull request #552 product, the composed
controller released as Fiat 5.25.1, and the Hexaemeron 1.6.1 package. The replay
ran the checked-in controller and synopsis generator against a fresh temporary
Git repository. It did not run the active recovery controller, change the
active `.hexaemeron` state or ledger, retain temporary files, print signature
material, or expose a credential.

## Bound release bytes

| Subject | SHA-256 or Git object | Role |
| --- | --- | --- |
| product head | `f11fe174161f46bf79080422169ad943214e1b4f` | imported signed product |
| pinned base | `c4650f02a979e859ce36374779eac9cd70744288` | current-generation composition base |
| product-first composition | `0fb3bcfba14a36c623f380105504d41d1eb66c86` | two-parent compatibility join |
| Step 1 pushed head | `dda57e8a3258b5c26891fe0b6a39396ce13b9490` | signed Step 1 recovery/audit head |
| checked controller, `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | `2c29f696f2b368a334eb4a880e745fa3cd468cc9c385e36346000aed7c91ba9f` | sole controller runtime |
| checked generator, `plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py` | `2972258d0c363bee0cc7e97668da96bcbb5ea19421fc278eefdae60ddcde9d75` | sole synopsis runtime |
| recovery study | `14576e2985024efc8e950b9ad2a22977fb9f2d6e6c64a7460996d63b577056d2` | receipted assumptions and risks |
| recovery runbook | `e2a2488af4cab26db47275c8ac0c9dbf9aa2278b9ca91279005168e87f039e75` | receipted build packet |
| composition manifest | `9f061ed1feae0b057e8bca54af3383d0573d16122ec38586bf37d7cbbdbd93ca` | sixteen overlap decisions |

The composition has #552 as first parent and `c4650f0` as second parent. Its
OpenPGP signature verifies, and its message contains one exact
`Co-authored-by: Shoggoth <shoggoth@wildcat.finance>` trailer and one exact
`Wildcat-Origin: shoggoth` trailer.

The proof file's raw SHA-256 is checked from
`plugins/hexaemeron/tests/test_issue_429_recovery.py`. The digest is kept
outside this file because a file cannot contain its own raw digest without
changing it.

## Disposable checked-controller replay

The fixture started at the composition, where nine audit sources exist. The
controller receipted signed commits `ab9e70d142fdad70b089268615e107f1733f7900`
and `dda57e8a3258b5c26891fe0b6a39396ce13b9490`, then accepted one clean
`fiat-audit-round/v2` source as source ten. The imported product source supplied
29 `fiat-audit-round/v1` records. The writer and checker each returned ten
different destinations and byte-identical fresh output.

| Source | Output | Source lines | Output lines | v1 / v2 | Verdicts / leads | Terminal verdict | Source SHA-256 | Output SHA-256 |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `audit/AUDIT.md` | `audit/AUDIT_SYNOPSIS.md` | 14,079 | 425 | 0 / 0 | 1 / 326 | `unguarded` (legacy prose) | `c271237691dc76a95059651f08710411e9d095b12d92b3d5f960182e357bb9fa` | `b9fe6925729395a72433e0f5918ddba785cc1905b2acc8926a94a6a23b1bc6e6` |
| `audit/rounds/fiat-429-audit-record-schema-timestamp-synopsis.md` | `audit/rounds/fiat-429-audit-record-schema-timestamp-synopsis.synopsis.md` | 574 | 30 | 29 / 0 | 29 / 29 | `null` | `51891eaf4a387acb79ab65c9508c09cb84828cb40c475a3b363fddcecd74fe8d` | `937417919bb6c27ab5a47a8d5adadef2eb088592d2937f0154e7868a133f0a50` |
| `audit/rounds/fiat-576-give-each-fiat-run-its-own-audit-log-path.md` | `audit/rounds/fiat-576-give-each-fiat-run-its-own-audit-log-path.synopsis.md` | 430 | 10 | 0 / 0 | 0 / 9 | none | `ba74d5c959d0d06afc0e18ede1770d9b779cfb25f039ed375e6fa4b9a2e4801e` | `98f073960bfcbb22a0072269798e666fe1f975df4760dac7d0747db6a92411b3` |
| `audit/rounds/fiat-594-bind-a-step-merge-to-the-pull-request-the-di.md` | `audit/rounds/fiat-594-bind-a-step-merge-to-the-pull-request-the-di.synopsis.md` | 194 | 5 | 0 / 0 | 0 / 4 | none | `ef8b9ccc14580841ba8aff9613a3f6ffd6e40085c35b49bb54ae571dc648125c` | `59c464b3f1e91f9b2fd4925753b9b934f75f6ade9a99efd90a30ea9b0c371b57` |
| `audit/rounds/fiat-issue-429-proof.md` | `audit/rounds/fiat-issue-429-proof.synopsis.md` | 15 | 2 | 0 / 1 | 1 / 1 | `null` | `b7e3e69342bef4fe8b976501e4a38e1bc17fc10552c76d4bdd0fbfabc5c818df` | `2240e09f72a2c12d594ffede9549a38dc9f9cece5ef4ffaa183d28926dcf8b04` |
| `plugins/ariadne/audit/AUDIT.md` | `plugins/ariadne/audit/AUDIT_SYNOPSIS.md` | 466 | 22 | 0 / 0 | 0 / 21 | none | `d8d13eb238b6e270fb9f89ec11fea797b4a3aa27025b5a62a7f36ac2642617af` | `53aacbb59bc9bc1455ce580ce484cbcb16802f7faa41b2b12f65c3ce614d1b4a` |
| `plugins/hexaemeron/audit/AUDIT.md` | `plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md` | 71 | 3 | 0 / 0 | 0 / 2 | none | `8acff29ed567c97902941a85d72e41171c10850de6aa898b5d50564248eac28f` | `2e919d920cd952a837bee6069251b710a9543df37514d7248a996d61766138cd` |
| `plugins/pandects/audit/AUDIT.md` | `plugins/pandects/audit/AUDIT_SYNOPSIS.md` | 696 | 18 | 0 / 0 | 0 / 16 | none | `66908cb68630f3c3cbea432aec6cf6efc305bcab85ccf5fadb278c535635edf9` | `ecde800e07ed8b1bc94b5a55714e3b01fbe0dfb1283bdafc88be170357dd32f1` |
| `plugins/probitas/audit/AUDIT.md` | `plugins/probitas/audit/AUDIT_SYNOPSIS.md` | 842 | 25 | 0 / 0 | 0 / 23 | none | `ba532815ae3abe13be3494b96044bf5d874cfb23842249d8e1cd867186e486c9` | `5eab3774f4d66147e8a4fc18a1014b181f7b1f2309003a93a1dfffb0ff4891a1` |
| `plugins/tabularium/audit/AUDIT.md` | `plugins/tabularium/audit/AUDIT_SYNOPSIS.md` | 262 | 14 | 0 / 0 | 0 / 13 | none | `1de310b5df5784d7e623ea9dbda83ae77e02cb1798b3aeedffc5d0c715f8e3a7` | `2432d6fd11be15a838d62ab067a190314a1a63011a67e106682f700cc3447e6c` |

Every output met `100 * output_lines < 15 * source_lines`. The strict v2
receipt stored timestamp `2026-08-25T12:00:00Z`, the source digest, its end
offset, and its current synopsis digest.

## Refusal matrix

Each controller refusal started from the same state and ledger bytes for that
case. The candidate source and every synopsis destination also had identical
bytes before and after the controller call. The collision planner wrote no
destination. The release-predecessor case made no release edit.

| Boundary | Cases replayed | Result |
| --- | --- | --- |
| required fields | schema, Covered, Not checked, verdict, table, leads | 6 refusals; no state, ledger, source or destination drift |
| timestamp | malformed shape, invalid calendar date | 2 refusals; no drift |
| grammar | unknown schema, v1 heading with v2 schema, missing terminal LF | 3 refusals; no drift |
| risk ids | missing, duplicate, unknown, invalid disposition | 4 refusals; no drift |
| finding count | non-zero row beside zero declaration, zero row beside one declaration | 2 refusals; no drift |
| verdict | `guarded` record beside a no-fix receipt | refusal; no drift |
| synopsis | stale committed sibling | refusal; no drift |
| paths | wrong configured path, symlinked source, `..` escape | 3 refusals; no drift |
| collision | two planned sources forced to one sibling | refusal before writing |
| composition | reversed product/base parents | refusal |
| signature | unsigned implementation with both trailers | refusal; no state or ledger drift |
| trailers | validly signed `43babf204a0a21435f49a6681d355b692232b1f5` with no Shoggoth trailers | refusal; no state or ledger drift |
| release predecessor | one Hexaemeron surface changed from 1.6.0 to 1.6.1 before allocation | refusal before editing |

There were 27 named refusals. The successful replay ran 214 bounded subprocess
calls in 9.313 seconds. Its largest combined captured stdout and stderr was
444,522 bytes, below the 2,097,152-byte cap. Elapsed time and output size are
diagnostic observations, not performance claims. The temporary root was gone
after the run, and the active recovery state and ledger retained their original
digests.

## Inherited product commits

The proof read the exact 52-object range `c4650f0..f11fe174`. Every row passed
local `git verify-commit`, GitHub reported `verified: true` with reason `valid`,
both exact trailers occurred once, and the commit remained reachable from the
recovery head. Raw verifier output was neither printed nor retained.

| Commit | Local | GitHub | Trailer counts | Reachable |
| --- | --- | --- | ---: | --- |
| `f11fe174161f46bf79080422169ad943214e1b4f` | valid | valid | 1 + 1 | yes |
| `288aaf3bd815608a3e73566a7643e6f230e13eb3` | valid | valid | 1 + 1 | yes |
| `7ef0df81646fd517b464321aa8d0349e57859a5b` | valid | valid | 1 + 1 | yes |
| `e9ca4ecb74f8b5de2a312c9296723c3c4eed5b00` | valid | valid | 1 + 1 | yes |
| `9acaaf4be600e87b0348b965a5c924e60877d0d4` | valid | valid | 1 + 1 | yes |
| `5a67f3aae07f7ff302097fa81e9fa82c30f837ec` | valid | valid | 1 + 1 | yes |
| `4b78dfa8b35efe4da794a200096682eb7495c3b3` | valid | valid | 1 + 1 | yes |
| `29a1d8db18c7770efdd42302ea3592130af34fe9` | valid | valid | 1 + 1 | yes |
| `fed0de5e9e24f3a66f3e2b53ea85643a3840dfa9` | valid | valid | 1 + 1 | yes |
| `fa944305db3b16e739af9374cca1cb3f305c9a84` | valid | valid | 1 + 1 | yes |
| `bb71c03194b6393fe9068b7efc4ca0b2d37af330` | valid | valid | 1 + 1 | yes |
| `00db9c0daaa11f6bc7cafe47f1e92a88efdccefa` | valid | valid | 1 + 1 | yes |
| `eb13998601fc24d9e356c46e867de8b72b454b8d` | valid | valid | 1 + 1 | yes |
| `becd36a48e041d5141d442a8b2008494b18081ff` | valid | valid | 1 + 1 | yes |
| `0802d9ffe6fcd04410e182d14f4ea4d33c40a6c8` | valid | valid | 1 + 1 | yes |
| `e4617679b19bbe1775becd703cf10ea6efd01146` | valid | valid | 1 + 1 | yes |
| `0119394e8fa37417d9634bd41084600bec8ac2f3` | valid | valid | 1 + 1 | yes |
| `08e311969f2f13c6b9f846bdf711824c2f12dd87` | valid | valid | 1 + 1 | yes |
| `601648401abeaf084530adc3c882df6a44c8dbe3` | valid | valid | 1 + 1 | yes |
| `6bdcc8be4ca73ac51cd82b68a8117823ea4ae664` | valid | valid | 1 + 1 | yes |
| `d96cb0fb6a33a29d9f2ebbeb23e3a9c1dc7b2211` | valid | valid | 1 + 1 | yes |
| `abc65441b9018709a0a4431f7c8bf00b73c125bb` | valid | valid | 1 + 1 | yes |
| `90439da54ef979f5cd11d04ff2d0281ecc3c27cb` | valid | valid | 1 + 1 | yes |
| `5e1baffa709d3d2619322227ec9324b25f5ed22c` | valid | valid | 1 + 1 | yes |
| `37860b9e0567ade42afe0151561fbaa9e6ce4e17` | valid | valid | 1 + 1 | yes |
| `6c9c60c0fca28c6f8e4b2b659a10160ba2209274` | valid | valid | 1 + 1 | yes |
| `c3c3f97fa7956542a610267e1faf3197a7cda2c9` | valid | valid | 1 + 1 | yes |
| `7c30bc5cbc9f96629a73b117e13d33c27734aeb8` | valid | valid | 1 + 1 | yes |
| `b6344f9a88f244bc7b05aa348fe69b1e0b169ee0` | valid | valid | 1 + 1 | yes |
| `3a9ba9a42dbc7aedadded73c2ed58f7f4e6f8ad3` | valid | valid | 1 + 1 | yes |
| `f5b4f2ed1374839c5c8d6e5f2b640dec70e32808` | valid | valid | 1 + 1 | yes |
| `686dc86e80ae0b9f3c99c40d021fcf25e57c9e86` | valid | valid | 1 + 1 | yes |
| `7eca88769eb3778b39de8831afb563bb81d5901e` | valid | valid | 1 + 1 | yes |
| `13cd55e339fa9c835c5b14b7b5723595aceaa779` | valid | valid | 1 + 1 | yes |
| `57e1dfe6b4d2a17553b44fa92084566b84846647` | valid | valid | 1 + 1 | yes |
| `d926d4eb581e8a86cfcfc802bd95b34ff56c1bfb` | valid | valid | 1 + 1 | yes |
| `6bf02c5e203487a5e7ec06c71f754e4b92a1913a` | valid | valid | 1 + 1 | yes |
| `60697037cfa9c3929797301616c86f8c7f6fbe80` | valid | valid | 1 + 1 | yes |
| `8bacc040f34ae4c2b57dc571fdaf0b4510e12e0f` | valid | valid | 1 + 1 | yes |
| `2ea2f58bc41e5fa78c8f49bb66d2dddf6c3d1326` | valid | valid | 1 + 1 | yes |
| `72f133f74a347f741b463166f1a6bb05de092c91` | valid | valid | 1 + 1 | yes |
| `1f82d9f4a879dc46a70ee8cbc1fd00cc755629dc` | valid | valid | 1 + 1 | yes |
| `566ccc7371a4f40e6037683bfa9cec5368b039ac` | valid | valid | 1 + 1 | yes |
| `459bb083bf428e6e45fc0c0e977356d1185a633d` | valid | valid | 1 + 1 | yes |
| `cfbc1374617aadd18e4f24f8e0e344c0a4475800` | valid | valid | 1 + 1 | yes |
| `79224b6984bcfdf342b22a6e8a5faef89f8f6d64` | valid | valid | 1 + 1 | yes |
| `07f6ec985963abdd591fb605909dff89e6a81d38` | valid | valid | 1 + 1 | yes |
| `b9d9e381d59961c873d8d8d5f7ae046f979eae65` | valid | valid | 1 + 1 | yes |
| `c394a9eb6146e77ea2c62fae70befd9351d2e045` | valid | valid | 1 + 1 | yes |
| `5e2ec0f85ad3528246373d3408dec4852ce6bf90` | valid | valid | 1 + 1 | yes |
| `b18b13defdd90943c0e976dae6eb8e305192dfa0` | valid | valid | 1 + 1 | yes |
| `402a975a392524dcff0a7c7aefc5d9fd1d4f1ff1` | valid | valid | 1 + 1 | yes |

Counts: 52 local-valid, 52 hosted-valid, 52 with both exact trailers, and 52
reachable.

## Released ten-source tree

The disposable v2 source above is synthetic and was deleted. At the pre-audit
Step 2 implementation candidate observed by this proof, the release tree had
the current recovery Warden source instead. The checked-in generator returned
the following separate ten-source set in `--check` mode.

| Source | Output | Source lines | Output lines | v1 / v2 | Verdicts / leads | Terminal verdict | Source SHA-256 | Output SHA-256 |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `audit/AUDIT.md` | `audit/AUDIT_SYNOPSIS.md` | 14,079 | 425 | 0 / 0 | 1 / 326 | `unguarded` (legacy prose) | `c271237691dc76a95059651f08710411e9d095b12d92b3d5f960182e357bb9fa` | `b9fe6925729395a72433e0f5918ddba785cc1905b2acc8926a94a6a23b1bc6e6` |
| `audit/rounds/fiat-429-audit-record-schema-timestamp-synopsis.md` | `audit/rounds/fiat-429-audit-record-schema-timestamp-synopsis.synopsis.md` | 574 | 30 | 29 / 0 | 29 / 29 | `null` | `51891eaf4a387acb79ab65c9508c09cb84828cb40c475a3b363fddcecd74fe8d` | `937417919bb6c27ab5a47a8d5adadef2eb088592d2937f0154e7868a133f0a50` |
| `audit/rounds/fiat-429-recover-issue-429-from-pull-request-552.md` | `audit/rounds/fiat-429-recover-issue-429-from-pull-request-552.synopsis.md` | 31 | 3 | 0 / 2 | 2 / 2 | `null` | `6133082583d107c07dbb7b473c638cc65fc44254ef63c881e37462043686531e` | `a90d29934ab7f295f561f82c0b6deea311cf385d5163535daddca3e84fbcd56b` |
| `audit/rounds/fiat-576-give-each-fiat-run-its-own-audit-log-path.md` | `audit/rounds/fiat-576-give-each-fiat-run-its-own-audit-log-path.synopsis.md` | 430 | 10 | 0 / 0 | 0 / 9 | none | `ba74d5c959d0d06afc0e18ede1770d9b779cfb25f039ed375e6fa4b9a2e4801e` | `98f073960bfcbb22a0072269798e666fe1f975df4760dac7d0747db6a92411b3` |
| `audit/rounds/fiat-594-bind-a-step-merge-to-the-pull-request-the-di.md` | `audit/rounds/fiat-594-bind-a-step-merge-to-the-pull-request-the-di.synopsis.md` | 194 | 5 | 0 / 0 | 0 / 4 | none | `ef8b9ccc14580841ba8aff9613a3f6ffd6e40085c35b49bb54ae571dc648125c` | `59c464b3f1e91f9b2fd4925753b9b934f75f6ade9a99efd90a30ea9b0c371b57` |
| `plugins/ariadne/audit/AUDIT.md` | `plugins/ariadne/audit/AUDIT_SYNOPSIS.md` | 466 | 22 | 0 / 0 | 0 / 21 | none | `d8d13eb238b6e270fb9f89ec11fea797b4a3aa27025b5a62a7f36ac2642617af` | `53aacbb59bc9bc1455ce580ce484cbcb16802f7faa41b2b12f65c3ce614d1b4a` |
| `plugins/hexaemeron/audit/AUDIT.md` | `plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md` | 71 | 3 | 0 / 0 | 0 / 2 | none | `8acff29ed567c97902941a85d72e41171c10850de6aa898b5d50564248eac28f` | `2e919d920cd952a837bee6069251b710a9543df37514d7248a996d61766138cd` |
| `plugins/pandects/audit/AUDIT.md` | `plugins/pandects/audit/AUDIT_SYNOPSIS.md` | 696 | 18 | 0 / 0 | 0 / 16 | none | `66908cb68630f3c3cbea432aec6cf6efc305bcab85ccf5fadb278c535635edf9` | `ecde800e07ed8b1bc94b5a55714e3b01fbe0dfb1283bdafc88be170357dd32f1` |
| `plugins/probitas/audit/AUDIT.md` | `plugins/probitas/audit/AUDIT_SYNOPSIS.md` | 842 | 25 | 0 / 0 | 0 / 23 | none | `ba532815ae3abe13be3494b96044bf5d874cfb23842249d8e1cd867186e486c9` | `5eab3774f4d66147e8a4fc18a1014b181f7b1f2309003a93a1dfffb0ff4891a1` |
| `plugins/tabularium/audit/AUDIT.md` | `plugins/tabularium/audit/AUDIT_SYNOPSIS.md` | 262 | 14 | 0 / 0 | 0 / 13 | none | `1de310b5df5784d7e623ea9dbda83ae77e02cb1798b3aeedffc5d0c715f8e3a7` | `2432d6fd11be15a838d62ab067a190314a1a63011a67e106682f700cc3447e6c` |

All ten committed outputs matched fresh bytes and passed the strict physical
line inequality. The two #429 round sources map to different siblings. No
synopsis file was rediscovered as an input.

This table is a time-bound observation, not a claim that every digest remains
the final audited-head byte set. A later Warden round appends to the same
recovery audit source and regenerates its sibling, so that source's and
sibling's digest and line counts intentionally change. The final audit and
synopsis-currency receipts bind those resulting bytes.

## Release allocation and boundary

Immediately before release editing, remote `main` was
`55c60852ead94812596cb9ea91ca11bf1b08f260`. Fiat's current and newest row was
`fiat-v5.24.1`; it retained open frontier revision `state-shape-validation`,
frontier digest
`e413d6041edb34b3807a54019489605814a591f60547755f8f66f01830f643aa`,
and issue #363 as its held target. Both Hexaemeron plugin manifests and both
marketplace manifests said 1.6.0. No `fiat-v5.25.1` or Hexaemeron 1.6.1
successor was occupied.

The release therefore adds one generation row for `fiat-v5.25.1`, sets Fiat
metadata to 5.25.1, and sets both plugin manifests and both marketplace entries
to Hexaemeron 1.6.1. All six Promise Machine runtime bindings continue to name
the released controller digest
`2c29f696f2b368a334eb4a880e745fa3cd468cc9c385e36346000aed7c91ba9f`.
The row changes neither the frontier revision and digest nor its open status and
issue #363 target.

This release does not implement issues #557, #608, #453, #369, or #363. It
does not alter the lost #429 controller ledger, push a branch, change a pull
request, change an issue, merge, or claim a deployment.
