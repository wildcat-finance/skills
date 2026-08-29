#!/usr/bin/env python3
"""Verify the complete issue-622 carryover before product checks run.

The published packet and patch are independent inputs.  The checked-in record
cannot replace either one: their public digests, the one permitted path
transform, the archive identity, the finding families, and the current-base
cause guards are fixed here.  A successful invocation establishes only that
the named current tree agrees with those inputs and identities.
"""

import argparse
import ast
from collections import Counter
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys


SCHEMA = "wildcat.issue-622-inoculation.v1"
EXPECTED_PACKET_SHA256 = (
    "615cbef52cd6436db8ddbf445ffa68d12e20beb3fffa4de18b17fcfe13724d62"
)
EXPECTED_PATCH_SHA256 = (
    "c5d8074f06121a56f441329b228c51f21add9e530bf02f13ecd51a7c2b4fc5f8"
)
EXPECTED_CURRENT_BASE = "b245d68e7e8c9d07b0dbbaa67e57b05cd00b18ef"
EXPECTED_PATCH_BASE = "f1458dcefa24ac26a4a550178f43514bc775e4e8"
EXPECTED_CUMULATIVE_COMMIT = "a60e688d7d4dacccf6eb5be8c88a8444e620b7f8"
EXPECTED_CUMULATIVE_TREE = "8ed805f1546e525469a923217dd85798294e48a6"
EXPECTED_ARCHIVE_REF = "archive/622-affected-scope-parallel-runner-attempt-1"
EXPECTED_ARCHIVE_COMMIT = "f78f6b4c990c41629f4b77ceafe4977f016aeba1"
EXPECTED_ARCHIVE_TREE = "7507f0e13b3c6f846adf9fe7d075a8ce0e7baa82"
TRANSFORM_ID = "adr-035-selector-to-adr-041"
ADR_SOURCE = (
    "docs/decisions/"
    "ADR-035-select-and-schedule-repository-checks-from-one-graph.md"
)
# The packet and patch record the live scheduling decision at the ADR-037
# path.  Current main already holds an unrelated
# ADR-037-prove-receipts-with-a-full-ordered-witness.md, so the live decision
# is physically renamed to the next free number; only this one packet path
# reads from a different current location.
PACKET_ADR_PATH = (
    "docs/decisions/"
    "ADR-037-select-and-schedule-repository-checks-from-one-graph.md"
)
ADR_TARGET = (
    "docs/decisions/"
    "ADR-045-select-and-schedule-repository-checks-from-one-graph.md"
)
RUNNER_PATH = "plugins/hexaemeron/tests/run_tests.py"
PARALLEL_GUARD_PATH = "plugins/hexaemeron/tests/test_parallel_test_runner.py"
EXPECTED_FINDING_OWNER = RUNNER_PATH
VERIFIER_PATH = "scripts/verify_issue_622_inoculation.py"
INOCULATION_GUARD_PATH = (
    "plugins/hexaemeron/tests/test_issue_622_inoculation.py"
)
SIGNING_GUARD_PATH = "plugins/hexaemeron/tests/test_disposable_git_signing.py"
DECISION_GUARD_PATH = "tests/test_decision_records.py"
PROMISE_COVERAGE_PATH = "tests/promise_machine_coverage.json"
RECORD_PATH = "tests/fixtures/issue-622-inoculation-v1.json"
GUARD_PATH_BY_OWNER = {
    RUNNER_PATH: PARALLEL_GUARD_PATH,
    VERIFIER_PATH: INOCULATION_GUARD_PATH,
    INOCULATION_GUARD_PATH: INOCULATION_GUARD_PATH,
    SIGNING_GUARD_PATH: SIGNING_GUARD_PATH,
    ADR_TARGET: DECISION_GUARD_PATH,
    PROMISE_COVERAGE_PATH: INOCULATION_GUARD_PATH,
}
# Identity-mapped targets must remain byte-identical to the fixed archive.
# These paths are the complete reviewed logical-target divergence set on the
# current reconstruction: the ADR rewrite, imported runbook references,
# reviewed runner causes, fixture signing isolation and the Promise Machine
# reporter binding.
# Keeping their identities here prevents the record and target from changing
# together and then vouching for each other.
# Current-main overlap dispositions for this rebind:
# - tests/promise_machine_coverage.json is the sole current-main path overlap;
#   the current map and rows are retained and only the reviewed reporter
#   digest for the reconstructed runner is refreshed.
# - The later #700 composition retains that map and adds the reviewed Phylax
#   model-proxy promise digest without changing the archived source bytes.
# - The live scheduling decision is physically renamed from the packet's
#   ADR-037 path to the then-free number 038 because current main introduced
#   an unrelated ADR-037 decision after the patch preimage; the logical
#   ADR-035 source and every immutable audit prefix keep their recorded
#   bytes.
# - The same collision kept recurring: current main took numbers 038
#   through 044 for unrelated decisions, so the live decision moved with
#   each advancement, settling at ADR-045, the next free number across
#   both branches.  The heading moves with the
#   filename, so the current digest changes with the rename while the
#   archived ADR-035 source bytes stay fixed.
EXPECTED_CHANGED_CURRENT_SHA256 = {
    "docs/affected-scope-test-runner/runbook.md": (
        "295358d66202f3e36e906c28e4e8544d52722edd3db2356460b01ad0ebe02caa"
    ),
    ADR_SOURCE: (
        "244a89e377c50c74e6a94b9b129e7c2607a2b6d0789213272b61997f73b350e7"
    ),
    RUNNER_PATH: (
        "3c83bfaa7f067f00f304eeac64867f4710846caa913d6ce14e6eca7024b5d63f"
    ),
    PARALLEL_GUARD_PATH: (
        "3c53e894ae17ccfb97cc64c22e84092bedc08f82d22017ff081ef493d4662fc4"
    ),
    "plugins/hermes/skills/hermes/scripts/test_hermes.py": (
        "cbd8ea125cabd63943eb82737d13e7acb18e9d9a8b434ca2ea2e373186d2c05b"
    ),
    SIGNING_GUARD_PATH: (
        "a99e726b0ca3cda5a0a7487fb00243b66075a4352e1e6eea781adaf09d3cf7e0"
    ),
    "plugins/hexaemeron/tests/test_elenchus_checker.py": (
        "377d40130cd0f64b66872fd27374e23874d0f9903d71f03e5454eea987c7ad44"
    ),
    "plugins/hexaemeron/tests/test_hexctl.py": (
        "a5d22f2d488856dfbefbd7c9bde899aeeeade4570d01bc0104a277cbe13abd7f"
    ),
    "plugins/hexaemeron/tests/test_kronos_scoreboard.py": (
        "0fd6c9c81a9211ff07911333c5989b3766aaaeab13d48da50de2033e688cc0f1"
    ),
    "plugins/horos/tests/test_demonstration.py": (
        "242053e3fa14f1a4de435fb3e604647d01cc191e287db5c725cf8da6e4e7ed35"
    ),
    "plugins/horos/tests/test_scoped_entry.py": (
        "2aba2ac960f89dc92a2f9450d7d66636613c80fe71b4deec4bf08ae0760b4477"
    ),
    "plugins/horos/tests/test_universe.py": (
        "9d4b41e0c539e0edb8bda9b8a0cd9b2b9cebb46d6bc639894d727bbb6de804a7"
    ),
    "tests/promise_machine_coverage.json": (
        "1cbd633bf9bdb80040a3b49a1200502236fb6fdfdf287b56dcce5802e3e78b7c"
    ),
    "tests/test_boundary_currency.py": (
        "8e12caa36efec6779d918fb7988f41229b961b097c3a1747b4d8edddcbfa2ae5"
    ),
}
ADDITIONAL_CURRENT_PATHS = frozenset({
    "audit/rounds/fiat-622-carryover-2-implementation-continuation.md",
    "audit/rounds/fiat-622-carryover-2-implementation-continuation.synopsis.md",
    "audit/rounds/fiat-622-carryover-inoculate-affected-scope-runner.md",
    "audit/rounds/fiat-622-carryover-inoculate-affected-scope-runner.synopsis.md",
    "docs/affected-scope-test-runner/replacement-runbook.md",
    "docs/affected-scope-test-runner/replacement-study.md",
    INOCULATION_GUARD_PATH,
    VERIFIER_PATH,
    RECORD_PATH,
})
# These are the only current-source or bootstrap rebindings permitted to
# diverge from the round-8 bytes in the published 27-path table.  Checks in
# this file are what a caller already chose to execute, so
# verify_cumulative_targets binds the execution path
# scripts/verify_issue_622_inoculation.py instead of asking this file to
# vouch for its own digest.
EXPECTED_CUMULATIVE_REBIND_SHA256 = {
    "plugins/hermes/skills/hermes/scripts/test_hermes.py": (
        "cbd8ea125cabd63943eb82737d13e7acb18e9d9a8b434ca2ea2e373186d2c05b"
    ),
    RUNNER_PATH: (
        "3c83bfaa7f067f00f304eeac64867f4710846caa913d6ce14e6eca7024b5d63f"
    ),
    SIGNING_GUARD_PATH: (
        "a99e726b0ca3cda5a0a7487fb00243b66075a4352e1e6eea781adaf09d3cf7e0"
    ),
    "plugins/hexaemeron/tests/test_elenchus_checker.py": (
        "377d40130cd0f64b66872fd27374e23874d0f9903d71f03e5454eea987c7ad44"
    ),
    "plugins/hexaemeron/tests/test_hexctl.py": (
        "a5d22f2d488856dfbefbd7c9bde899aeeeade4570d01bc0104a277cbe13abd7f"
    ),
    "plugins/hexaemeron/tests/test_kronos_scoreboard.py": (
        "0fd6c9c81a9211ff07911333c5989b3766aaaeab13d48da50de2033e688cc0f1"
    ),
    PARALLEL_GUARD_PATH: (
        "3c53e894ae17ccfb97cc64c22e84092bedc08f82d22017ff081ef493d4662fc4"
    ),
    "plugins/horos/tests/test_demonstration.py": (
        "242053e3fa14f1a4de435fb3e604647d01cc191e287db5c725cf8da6e4e7ed35"
    ),
    "plugins/horos/tests/test_scoped_entry.py": (
        "2aba2ac960f89dc92a2f9450d7d66636613c80fe71b4deec4bf08ae0760b4477"
    ),
    "plugins/horos/tests/test_universe.py": (
        "9d4b41e0c539e0edb8bda9b8a0cd9b2b9cebb46d6bc639894d727bbb6de804a7"
    ),
    INOCULATION_GUARD_PATH: (
        "46085b12fdac754fd73a50d972c273d82e83395af142b0fe69055f907e486a3f"
    ),
    RECORD_PATH: (
        "6c456d9dea4ac6e276f30b8db93465e92ea565e4fc337ac96d072099042c5af9"
    ),
    "tests/promise_machine_coverage.json": (
        "1cbd633bf9bdb80040a3b49a1200502236fb6fdfdf287b56dcce5802e3e78b7c"
    ),
    "tests/test_boundary_currency.py": (
        "8e12caa36efec6779d918fb7988f41229b961b097c3a1747b4d8edddcbfa2ae5"
    ),
    "docs/affected-scope-test-runner/replacement-study.md": (
        "2f04503d78b0631500c6bae1b8c82e5174c9c448c49075c6dbba4a68c29de917"
    ),
    "docs/affected-scope-test-runner/replacement-runbook.md": (
        "64a70c6d5486559c3551ef87b083bfdd9e196c0a4ef92f1345a5a64931ea20a4"
    ),
    PACKET_ADR_PATH: (
        "244a89e377c50c74e6a94b9b129e7c2607a2b6d0789213272b61997f73b350e7"
    ),
}
EXPECTED_GUARD_SHA256 = {
    PARALLEL_GUARD_PATH: EXPECTED_CHANGED_CURRENT_SHA256[PARALLEL_GUARD_PATH],
    INOCULATION_GUARD_PATH: (
        "46085b12fdac754fd73a50d972c273d82e83395af142b0fe69055f907e486a3f"
    ),
    SIGNING_GUARD_PATH: EXPECTED_CHANGED_CURRENT_SHA256[SIGNING_GUARD_PATH],
    DECISION_GUARD_PATH: (
        "0bee37b6b1c095aeee8049d270635778fbbc985a35b7cf386a4d35204fc00caf"
    ),
}
EXPECTED_FAMILIES = frozenset({
    "aggregate-accounting",
    "bounded-output",
    "cache-path-boundary",
    "discovery-boundary",
    "malformed-json",
    "numeric-boundary",
    "private-result-validation",
    "report-framing",
    "result-cap-composition",
    "single-worker-parity",
    "structured-evidence",
    "structured-summary-bounds",
    "unittest-outcomes",
})
EXPECTED_PACKET_CAUSES = {
    "archive-git-replace-substitution": {
        "owner": VERIFIER_PATH,
        "guards": [
            "test_archive_reads_ignore_local_git_replace_objects"
        ],
        "family": "private-result-validation",
    },
    "archive-object-content-identity": {
        "owner": VERIFIER_PATH,
        "guards": [
            "test_archive_object_reads_recompute_git_identity"
        ],
        "family": "private-result-validation",
    },
    "automatic-capacity-safety-cap": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_automatic_capacity_respects_safety_cap_after_headroom"
        ],
        "family": "structured-summary-bounds",
    },
    "custom-suite-execution-semantics": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_custom_suite_run_behavior_cannot_disappear"
        ],
        "family": "discovery-boundary",
    },
    "custom-suite-metaclass-attribute-proof": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_custom_suite_metaclass_cannot_hide_execution_override"
        ],
        "family": "discovery-boundary",
    },
    "custom-suite-fixture-transition-hooks": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_custom_suite_fixture_transition_hooks_cannot_disappear"
        ],
        "family": "discovery-boundary",
    },
    "current-base-adr-number-uniqueness": {
        "owner": ADR_TARGET,
        "guards": [
            "test_no_number_collides_with_one_already_on_the_default_branch"
        ],
        "family": "private-result-validation",
    },
    "detached-descendant-boundary": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_detached_descendant_is_red_bounded_and_not_claimed_terminated"
        ],
        "family": "bounded-output",
    },
    "descendant-output-descriptor-lifetime": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_descendant_cannot_hold_worker_output_descriptor_open"
        ],
        "family": "bounded-output",
    },
    "unexpected-success-non-green": {
        "owner": RUNNER_PATH,
        "guards": ["test_unexpected_success_is_non_green"],
        "family": "unittest-outcomes",
    },
    "fixture-blocked-unittest-accounting": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_class_fixture_skip_is_accounted_without_execution",
            "test_module_fixture_skip_is_accounted_without_execution",
            "test_fixture_errors_and_unrecognised_holders_remain_scheduler_errors",
            "test_fixture_blocked_record_refuses_overlap_duplicate_and_unproved_missing",
        ],
        "family": "aggregate-accounting",
    },
    "fixture-domain-sharding-semantics": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_class_fixture_domain_is_not_split_across_workers",
            "test_import_registered_module_cleanup_keeps_one_suite_domain",
            "test_module_fixture_domain_is_not_split_across_workers",
            "test_unfixtured_tests_retain_fine_grained_distribution",
        ],
        "family": "discovery-boundary",
    },
    "fixture-domain-runtime-cleanup-registration": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_runtime_registered_standard_cleanups_cannot_split_domains"
        ],
        "family": "discovery-boundary",
    },
    "fixture-domain-worker-rediscovery-binding": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_worker_rediscovery_cannot_widen_fixture_domain_across_assignments"
        ],
        "family": "discovery-boundary",
    },
    "fixture-domain-dynamic-lookup-proof": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_dynamic_module_fixture_lookup_cannot_split_domain"
        ],
        "family": "discovery-boundary",
    },
    "fixture-domain-class-descriptor-proof": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_stateful_class_fixture_descriptor_cannot_split_domain"
        ],
        "family": "discovery-boundary",
    },
    "fixture-skip-origin-binding": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_test_object_cannot_forge_fixture_blocked_disposition"
        ],
        "family": "aggregate-accounting",
    },
    "guard-discovery-static-proof": {
        "owner": VERIFIER_PATH,
        "guards": [
            "test_guard_ast_proof_refuses_runtime_discovery_decoys"
        ],
        "family": "discovery-boundary",
    },
    "guard-discovery-control-flow-proof": {
        "owner": VERIFIER_PATH,
        "guards": [
            "test_guard_ast_refuses_control_flow_discovery_hooks"
        ],
        "family": "discovery-boundary",
    },
    "guard-discovery-namespace-proof": {
        "owner": VERIFIER_PATH,
        "guards": [
            "test_guard_ast_refuses_class_namespace_mutation"
        ],
        "family": "discovery-boundary",
    },
    "guard-discovery-runtime-mutation-proof": {
        "owner": VERIFIER_PATH,
        "guards": [
            "test_guard_ast_refuses_runtime_namespace_hooks"
        ],
        "family": "discovery-boundary",
    },
    "guard-discovery-module-namespace-mutation": {
        "owner": VERIFIER_PATH,
        "guards": [
            "test_guard_ast_refuses_module_namespace_update"
        ],
        "family": "discovery-boundary",
    },
    "guard-discovery-import-time-helper-mutation": {
        "owner": VERIFIER_PATH,
        "guards": [
            "test_guard_ast_refuses_import_time_helper_mutation"
        ],
        "family": "discovery-boundary",
    },
    "guard-discovery-implicit-runtime-hooks": {
        "owner": VERIFIER_PATH,
        "guards": [
            "test_guard_ast_refuses_implicit_discovery_and_descriptor_hooks"
        ],
        "family": "discovery-boundary",
    },
    "inoculation-bounded-read-content-binding": {
        "owner": VERIFIER_PATH,
        "guards": [
            "test_bounded_read_detects_in_place_content_substitution"
        ],
        "family": "private-result-validation",
    },
    "inoculation-bounded-read-inode-binding": {
        "owner": VERIFIER_PATH,
        "guards": [
            "test_bounded_read_cannot_switch_inodes_between_check_and_open"
        ],
        "family": "private-result-validation",
    },
    "inoculation-target-self-authorisation": {
        "owner": VERIFIER_PATH,
        "guards": [
            "test_paired_current_target_and_record_substitution_is_refused"
        ],
        "family": "private-result-validation",
    },
    "inoculation-record-json-resource-boundary": {
        "owner": VERIFIER_PATH,
        "guards": [
            "test_deep_record_json_is_a_stable_refusal"
        ],
        "family": "malformed-json",
    },
    "inoculation-guard-discoverability": {
        "owner": VERIFIER_PATH,
        "guards": [
            "test_required_guard_must_be_one_discovered_unittest_case"
        ],
        "family": "discovery-boundary",
    },
    "cgroup-v2-membership-quota-resolution": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_nested_cgroup_v2_membership_limits_automatic_capacity"
        ],
        "family": "structured-summary-bounds",
    },
    "cgroup-v2-mount-root-quota-resolution": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_cgroup_v2_mount_root_limits_automatic_capacity"
        ],
        "family": "structured-summary-bounds",
    },
    "cgroup-v1-membership-quota-resolution": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_nested_cgroup_v1_membership_limits_automatic_capacity"
        ],
        "family": "structured-summary-bounds",
    },
    "worker-process-group-identity-lifetime": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_process_group_identity_is_retained_until_cleanup_signals_finish"
        ],
        "family": "bounded-output",
    },
    "worker-protocol-checkout-interference": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_worker_protocol_directory_is_outside_invocation_checkout"
        ],
        "family": "private-result-validation",
    },
}
EXPECTED_CURRENT_CAUSES = {
    **EXPECTED_PACKET_CAUSES,
    "capacity-integer-division-boundary": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_capacity_arithmetic_never_rounds_through_float"
        ],
        "family": "numeric-boundary",
    },
    "fixture-domain-imported-cleanup-alias": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_imported_module_cleanup_alias_cannot_split_domain"
        ],
        "family": "discovery-boundary",
    },
    "fixture-domain-transitive-imported-cleanup": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_transitive_imported_cleanup_helpers_cannot_split_domain"
        ],
        "family": "discovery-boundary",
    },
    "fixture-domain-callable-cleanup-wrapper": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_callable_wrapped_cleanup_registration_cannot_split_domains"
        ],
        "family": "discovery-boundary",
    },
    "fixture-domain-referenced-callable-cleanup": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_referenced_callable_cleanup_registration_cannot_split_domain"
        ],
        "family": "discovery-boundary",
    },
    "fixture-domain-opaque-callable-overgrouping": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_referenced_opaque_callable_does_not_create_fixture_domain"
        ],
        "family": "discovery-boundary",
    },
    "guard-discovery-runtime-confirmation": {
        "owner": VERIFIER_PATH,
        "guards": [
            "test_guard_verification_rejects_import_time_decorator_erasure"
        ],
        "family": "discovery-boundary",
    },
    "guard-discovery-testcase-execution-entrypoints": {
        "owner": VERIFIER_PATH,
        "guards": [
            "test_guard_ast_refuses_custom_testcase_execution_entrypoints"
        ],
        "family": "discovery-boundary",
    },
    "guard-discovery-testcase-method-dispatch": {
        "owner": VERIFIER_PATH,
        "guards": [
            "test_guard_ast_refuses_custom_testcase_method_dispatch"
        ],
        "family": "discovery-boundary",
    },
    "guard-discovery-fixture-execution-probe": {
        "owner": VERIFIER_PATH,
        "guards": [
            "test_runtime_guard_probe_refuses_fixture_skipped_method"
        ],
        "family": "discovery-boundary",
    },
    "guard-discovery-method-lookup-execution-probe": {
        "owner": VERIFIER_PATH,
        "guards": [
            "test_runtime_guard_probe_refuses_replaced_test_method_lookup"
        ],
        "family": "discovery-boundary",
    },
    "guard-discovery-descendant-result-drain": {
        "owner": VERIFIER_PATH,
        "guards": [
            "test_runtime_discovery_result_drain_ignores_inherited_writer"
        ],
        "family": "bounded-output",
    },
    "fixture-domain-nested-cleanup-registration": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_nested_cleanup_helpers_and_context_registration_cannot_split_domains"
        ],
        "family": "discovery-boundary",
    },
    "fixture-domain-callable-bound-cleanup-state": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_callable_bound_cleanup_state_cannot_split_domain"
        ],
        "family": "discovery-boundary",
    },
    "guard-discovery-method-outcome-probe": {
        "owner": VERIFIER_PATH,
        "guards": [
            "test_runtime_guard_probe_refuses_method_level_skip"
        ],
        "family": "discovery-boundary",
    },
    "guard-discovery-dunder-method-metadata-mutation": {
        "owner": VERIFIER_PATH,
        "guards": [
            "test_guard_ast_refuses_direct_dunder_namespace_mutation"
        ],
        "family": "discovery-boundary",
    },
    "fixture-domain-cross-class-cleanup-registration": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_cross_class_cleanup_registration_cannot_split_domain"
        ],
        "family": "discovery-boundary",
    },
    "fixture-domain-inherited-cleanup-registration": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_inherited_cleanup_registrars_cannot_split_domains"
        ],
        "family": "discovery-boundary",
    },
    "fixture-domain-unresolved-class-cleanup-target": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_dynamic_cross_class_cleanup_target_cannot_split_domain"
        ],
        "family": "discovery-boundary",
    },
    "promise-reporter-release-surface-binding": {
        "owner": PROMISE_COVERAGE_PATH,
        "guards": [
            "test_promise_reporter_release_surface_binds_current_runner"
        ],
        "family": "private-result-validation",
    },
    "inoculation-preopen-inode-identity-binding": {
        "owner": VERIFIER_PATH,
        "guards": [
            "test_bounded_read_refuses_regular_inode_switch_before_open"
        ],
        "family": "private-result-validation",
    },
    "fixture-signing-command-scope-isolation": {
        "owner": SIGNING_GUARD_PATH,
        "guards": [
            "test_command_scope_cannot_reenable_fixture_commit_signing"
        ],
        "family": "private-result-validation",
    },
    "worker-protocol-ambient-temp-root": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_ambient_temp_root_cannot_put_worker_protocol_in_checkout"
        ],
        "family": "private-result-validation",
    },
    "worker-protocol-physical-checkout-containment": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_worker_protocol_containment_uses_directory_identity"
        ],
        "family": "private-result-validation",
    },
    "report-target-git-control-namespace": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_report_target_refuses_git_control_namespace"
        ],
        "family": "cache-path-boundary",
    },
    "inoculation-elenchus-packet-independence": {
        "owner": INOCULATION_GUARD_PATH,
        "guards": [
            "test_current_extension_is_packet_independent_and_elenchus_guarded",
            "test_guard_identity_dependency_is_explicit_for_parent_overlay",
        ],
        "family": "private-result-validation",
    },
}
# The Carryover-3 packet delegates the row-level 23-finding map to the
# machine record and the immutable audit sources whose digests its 27-path
# inventory pins.  The carried map is therefore compiled here, inside the
# verifier a caller already chose to execute, exactly as the predecessor
# packet published it; the packet's declared counts still cross-check it
# independently.
EXPECTED_CARRIED_FINDINGS = {
    "S2-R1-01": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_result_file_slot_is_bound_before_reconciliation",
            "test_non_object_result_is_a_scheduler_error_not_an_exception",
            "test_invalid_record_cannot_replay_forged_output",
            "test_replayed_text_is_bound_to_its_byte_metadata",
        ],
        "family": "private-result-validation",
    },
    "S2-R1-02": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_scheduler_error_summary_keeps_validated_worker_evidence",
            "test_structured_summary_preserves_each_shards_execution_evidence",
        ],
        "family": "structured-evidence",
    },
    "S2-R2-01": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_execution_sequences_correlate_before_result_use",
            "test_manifest_and_summary_have_explicit_byte_limits",
        ],
        "family": "structured-summary-bounds",
    },
    "S2-R2-02": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_scheduler_error_summary_keeps_validated_worker_evidence",
        ],
        "family": "structured-evidence",
    },
    "S2-R3-01": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_truncated_output_requires_the_full_bounded_head_and_tail",
            "test_bounded_text_capture_has_one_exact_utf8_truncation_shape",
            "test_invalid_record_cannot_replay_forged_output",
        ],
        "family": "bounded-output",
    },
    "S2-R3-02": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_parallel_worker_output_uses_only_coordinator_owned_pipes",
            "test_near_cap_unicode_worker_record_fits_its_private_file",
        ],
        "family": "result-cap-composition",
    },
    "S2-R3-03": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_timing_cache_read_refuses_a_linked_parent_outside_the_run_root",
            "test_timing_cache_atomic_replace_stays_on_its_bound_directory",
        ],
        "family": "cache-path-boundary",
    },
    "S2-R3-04": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_deep_json_is_a_stable_corrupt_cache_not_a_recursion_escape",
            "test_existing_json_number_refusals_remain_stable",
        ],
        "family": "malformed-json",
    },
    "S2-R4-01": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_multiple_failing_subtests_remain_test_failure_evidence",
        ],
        "family": "unittest-outcomes",
    },
    "S2-R4-02": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_pipe_read_failure_is_scheduler_evidence",
        ],
        "family": "bounded-output",
    },
    "S2-R5-01": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_worker_result_limit_is_derived_from_every_bounded_field",
        ],
        "family": "result-cap-composition",
    },
    "S2-R5-02": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_large_parseable_numbers_use_stable_scheduler_refusals",
        ],
        "family": "numeric-boundary",
    },
    "S2-R6-01": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_large_parseable_cache_number_is_a_visible_neutral_entry",
        ],
        "family": "numeric-boundary",
    },
    "S2-R6-02": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_single_worker_uses_the_private_worker_transport",
            "test_single_worker_child_fd_output_is_bounded_and_replayed",
        ],
        "family": "single-worker-parity",
    },
    "S2-R6-03": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_cross_shard_outcome_counts_refuse_before_aggregate_overflow",
            "test_uneven_outcome_counts_at_the_sequence_limit_remain_valid",
        ],
        "family": "aggregate-accounting",
    },
    "S2-R7-01": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_public_coordinator_contains_cross_shard_aggregate_refusal",
        ],
        "family": "aggregate-accounting",
    },
    "S2-R7-02": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_failure_event_summary_never_reports_negative_passes",
        ],
        "family": "unittest-outcomes",
    },
    "S2-R7-03": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_oversized_scheduler_errors_have_a_bounded_refusal_event",
        ],
        "family": "structured-summary-bounds",
    },
    "S2-R7-04": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_deep_and_cyclic_suites_have_stable_manifest_boundaries",
            "test_manifest_item_limit_stops_discovery_incrementally",
        ],
        "family": "discovery-boundary",
    },
    "S2-R8-01": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_test_output_cannot_forge_the_structured_run_summary",
        ],
        "family": "report-framing",
    },
    "S2-R8-02": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_suite_iterator_failures_are_structured_scheduler_refusals",
        ],
        "family": "discovery-boundary",
    },
    "S2-R8-03": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_test_id_failure_is_a_structured_scheduler_refusal",
        ],
        "family": "discovery-boundary",
    },
    "S2-R8-04": {
        "owner": RUNNER_PATH,
        "guards": [
            "test_sparse_suite_iteration_consumes_the_item_limit",
        ],
        "family": "discovery-boundary",
    },
}
MAX_PACKET_BYTES = 131_072
MAX_PATCH_BYTES = 1_048_576
MAX_RECORD_BYTES = 1_048_576
MAX_TARGET_BYTES = 8_388_608
MAX_GIT_DIAGNOSTIC_BYTES = 8_192
GIT_TIMEOUT_SECONDS = 15
MAX_RUNTIME_DISCOVERY_REQUEST_BYTES = 8_192
MAX_RUNTIME_DISCOVERY_BYTES = 65_536
RUNTIME_DISCOVERY_TIMEOUT_SECONDS = 20
HEX_256 = re.compile(r"^[0-9a-f]{64}$")
COMMIT_ID = re.compile(r"^[0-9a-f]{40}$")

RUNTIME_DISCOVERY_PROGRAM = r"""
import json
import os
import sys
import types
import unittest

write_fd = int(sys.argv[1])
filename = sys.argv[2]
required = json.loads(sys.argv[3])
counts = {name: 0 for name in required}
executed = {name: 0 for name in required}
result = {
    "ok": False,
    "counts": counts,
    "executed": executed,
    "error": "discovery failed",
}
try:
    source = sys.stdin.buffer.read()
    module = types.ModuleType("_issue_622_runtime_guard")
    module.__file__ = filename
    module.__package__ = ""
    sys.modules[module.__name__] = module
    exec(compile(source, filename, "exec"), module.__dict__)
    suite = unittest.defaultTestLoader.loadTestsFromModule(module)
    stack = [suite]
    selected = []
    leaves = 0
    while stack:
        item = stack.pop()
        if isinstance(item, unittest.TestSuite):
            children = list(item)
            stack.extend(reversed(children))
            continue
        leaves += 1
        if leaves > 100_000:
            raise RuntimeError("runtime guard manifest exceeds its item limit")
        if not isinstance(item, unittest.TestCase):
            raise RuntimeError("runtime guard manifest contains a non-TestCase")
        method = object.__getattribute__(item, "_testMethodName")
        if method in counts:
            counts[method] += 1
            selected.append((item, method))

    originals = []
    try:
        for item, method in selected:
            test_class = type(item)
            namespace = type.__getattribute__(test_class, "__dict__")
            present = method in namespace
            original = namespace.get(method)
            bound_original = object.__getattribute__(item, method)

            def sentinel(
                _self, _method=method, _original=bound_original
            ):
                executed[_method] += 1
                return _original()

            for attribute in (
                "__unittest_skip__",
                "__unittest_skip_why__",
                "__unittest_expecting_failure__",
            ):
                if hasattr(bound_original, attribute):
                    setattr(sentinel, attribute, getattr(bound_original, attribute))
            type.__setattr__(test_class, method, sentinel)
            originals.append((test_class, method, present, original))
        probe = unittest.TestResult()
        unittest.TestSuite(item for item, _method in selected).run(probe)
    finally:
        for test_class, method, present, original in reversed(originals):
            if present:
                type.__setattr__(test_class, method, original)
            else:
                type.__delattr__(test_class, method)

    execution_complete = (
        probe.testsRun == len(selected)
        and probe.wasSuccessful()
        and not probe.skipped
        and not probe.expectedFailures
        and all(executed[name] == counts[name] for name in required)
    )
    result = {
        "ok": execution_complete,
        "counts": counts,
        "executed": executed,
        "error": None if execution_complete else "execution-probe",
    }
except BaseException as error:
    result = {
        "ok": False,
        "counts": counts,
        "executed": executed,
        "error": type(error).__name__,
    }
payload = json.dumps(
    result, sort_keys=True, separators=(",", ":")
).encode("utf-8")
os.write(write_fd, payload)
"""


class InoculationError(RuntimeError):
    """One stable bootstrap refusal."""


def sha256_bytes(value):
    """Return the content identity used throughout the record."""
    return hashlib.sha256(value).hexdigest()


def require_keys(value, keys, label):
    """Require one closed object shape."""
    if not isinstance(value, dict) or set(value) != set(keys):
        raise InoculationError(f"{label} has an invalid field set")


def strict_object(pairs):
    """Reject duplicate JSON keys before a value can replace another."""
    value = {}
    for key, item in pairs:
        if key in value:
            raise InoculationError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def bounded_fd_bytes(file_descriptor, maximum, label):
    """Read one already-open regular file from the inode that was checked."""
    try:
        before = os.fstat(file_descriptor)
    except OSError as error:
        raise InoculationError(f"{label} read failed: {error}") from None
    if not stat.S_ISREG(before.st_mode):
        raise InoculationError(f"{label} must be a regular file")
    if before.st_size > maximum:
        raise InoculationError(f"{label} exceeds {maximum} bytes")

    first_pass = bytearray()
    try:
        while len(first_pass) <= maximum:
            chunk = os.pread(
                file_descriptor,
                min(65_536, maximum + 1 - len(first_pass)),
                len(first_pass),
            )
            if not chunk:
                break
            first_pass.extend(chunk)
    except OSError as error:
        raise InoculationError(f"{label} read failed: {error}") from None
    if len(first_pass) > maximum:
        raise InoculationError(f"{label} exceeds {maximum} bytes")

    payload = bytearray()
    try:
        while len(payload) <= maximum:
            chunk = os.read(
                file_descriptor,
                min(65_536, maximum + 1 - len(payload)),
            )
            if not chunk:
                break
            payload.extend(chunk)
        after = os.fstat(file_descriptor)
    except OSError as error:
        raise InoculationError(f"{label} read failed: {error}") from None
    if len(payload) > maximum:
        raise InoculationError(f"{label} exceeds {maximum} bytes")
    before_identity = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
    )
    after_identity = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    )
    if (
        before_identity != after_identity
        or len(payload) != after.st_size
        or payload != first_pass
    ):
        raise InoculationError(f"{label} changed while it was read")
    return bytes(payload)


def bounded_regular_bytes(path, maximum, label):
    """Open and read one bounded regular inode without following its name."""
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | os.O_NOFOLLOW
    try:
        expected = os.stat(os.fspath(path), follow_symlinks=False)
        if not stat.S_ISREG(expected.st_mode):
            raise InoculationError(f"{label} must be a regular file")
        file_descriptor = os.open(os.fspath(path), flags)
    except OSError as error:
        raise InoculationError(f"{label} is unavailable: {error}") from None
    try:
        opened = os.fstat(file_descriptor)
        if (opened.st_dev, opened.st_ino) != (
            expected.st_dev,
            expected.st_ino,
        ):
            raise InoculationError(f"{label} changed before it was opened")
        return bounded_fd_bytes(file_descriptor, maximum, label)
    finally:
        os.close(file_descriptor)


def load_record(path):
    """Read one bounded, duplicate-key-free inoculation record."""
    payload = bounded_regular_bytes(path, MAX_RECORD_BYTES, "record")
    try:
        value = json.loads(
            payload.decode("utf-8"), object_pairs_hook=strict_object
        )
    except (
        UnicodeError,
        ValueError,
        RecursionError,
        OverflowError,
        MemoryError,
    ) as error:
        raise InoculationError(
            f"record is not valid bounded UTF-8 JSON: {error}"
        ) from None
    if not isinstance(value, dict):
        raise InoculationError("record must be a JSON object")
    return value


def checked_relative_path(raw, label="path"):
    """Return one canonical repository-relative POSIX path."""
    if not isinstance(raw, str) or not raw or "\x00" in raw:
        raise InoculationError(f"{label} must be a non-empty string")
    value = PurePosixPath(raw)
    if (
        value.is_absolute()
        or str(value) != raw
        or any(part in ("", ".", "..") for part in value.parts)
        or value.parts[0] == ".git"
    ):
        raise InoculationError(f"unsafe {label}: {raw!r}")
    return raw


def target_bytes(root, relative):
    """Read one target through no-follow descriptors anchored at its root."""
    relative = checked_relative_path(relative, "target path")
    root = Path(root).resolve(strict=True)
    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_DIRECTORY", 0)
        | os.O_NOFOLLOW
    )
    file_flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | os.O_NOFOLLOW
    try:
        directory = os.open(os.fspath(root), directory_flags)
    except OSError as error:
        raise InoculationError(
            f"current target root is unavailable: {error}"
        ) from None
    parts = PurePosixPath(relative).parts
    try:
        for part in parts[:-1]:
            try:
                found = os.stat(part, dir_fd=directory, follow_symlinks=False)
            except OSError as error:
                raise InoculationError(
                    f"current target is unavailable: {relative}: {error}"
                ) from None
            if stat.S_ISLNK(found.st_mode):
                raise InoculationError(
                    f"current target crosses a symlink: {relative}"
                )
            try:
                child = os.open(part, directory_flags, dir_fd=directory)
            except OSError as error:
                raise InoculationError(
                    f"current target is unavailable: {relative}: {error}"
                ) from None
            os.close(directory)
            directory = child
        try:
            found = os.stat(
                parts[-1], dir_fd=directory, follow_symlinks=False
            )
        except OSError as error:
            raise InoculationError(
                f"current target is unavailable: {relative}: {error}"
            ) from None
        if stat.S_ISLNK(found.st_mode):
            raise InoculationError(f"current target crosses a symlink: {relative}")
        try:
            file_descriptor = os.open(
                parts[-1], file_flags, dir_fd=directory
            )
        except OSError as error:
            raise InoculationError(
                f"current target is unavailable: {relative}: {error}"
            ) from None
        try:
            return bounded_fd_bytes(
                file_descriptor,
                MAX_TARGET_BYTES,
                f"current target {relative}",
            )
        finally:
            os.close(file_descriptor)
    finally:
        os.close(directory)


def artifact_digests(packet, patch, record):
    """Bind artifacts to public values rather than record-supplied values."""
    packet_digest = sha256_bytes(packet)
    patch_digest = sha256_bytes(patch)
    if packet_digest != EXPECTED_PACKET_SHA256:
        raise InoculationError("packet SHA-256 does not match the published value")
    if patch_digest != EXPECTED_PATCH_SHA256:
        raise InoculationError("patch SHA-256 does not match the published value")
    artifacts = record.get("artifacts")
    require_keys(artifacts, ("packet", "patch"), "record artifacts")
    for name, expected in (
        ("packet", EXPECTED_PACKET_SHA256),
        ("patch", EXPECTED_PATCH_SHA256),
    ):
        item = artifacts[name]
        require_keys(item, ("sha256",), f"record artifact {name}")
        if item["sha256"] != expected:
            raise InoculationError(
                f"record artifact {name} disagrees with the published value"
            )
    return packet_digest, patch_digest


def decode_utf8(payload, label):
    try:
        return payload.decode("utf-8")
    except UnicodeError as error:
        raise InoculationError(f"{label} is not UTF-8: {error}") from None


def patch_paths(patch):
    """Extract every logical path from the bounded no-rename cumulative diff."""
    paths = []
    for line in decode_utf8(patch, "patch").splitlines():
        if not line.startswith("diff --git "):
            continue
        match = re.fullmatch(r"diff --git a/([^\t ]+) b/([^\t ]+)", line)
        if match is None:
            raise InoculationError("patch contains an unsupported path header")
        source = checked_relative_path(match.group(1), "patch source path")
        target = checked_relative_path(match.group(2), "patch target path")
        if source != target:
            raise InoculationError("patch contains an undeclared rename")
        if source in paths:
            raise InoculationError(f"patch repeats a path: {source}")
        paths.append(source)
    if not paths:
        raise InoculationError("patch contains no paths")
    return paths


def packet_section(text, heading, next_heading):
    """Return one exact packet section without accepting a later decoy."""
    start_marker = f"## {heading}\n"
    end_marker = f"\n## {next_heading}\n"
    start = text.find(start_marker)
    if start < 0:
        raise InoculationError(f"packet section is missing: {heading}")
    start += len(start_marker)
    end = text.find(end_marker, start)
    if end < 0:
        raise InoculationError(f"packet section is unterminated: {heading}")
    return text[start:end]


def packet_current_paths(packet):
    """Extract the packet's complete 27-path postimage inventory."""
    section = packet_section(
        decode_utf8(packet, "packet"),
        "Complete 27-path postimage inventory",
        "Carryover-2 continuation cause map",
    )
    paths = {}
    for path, digest in re.findall(
        r"^\| `([^`]+)` \| `([0-9a-f]{64})` \| [^|]+ \|$",
        section,
        re.MULTILINE,
    ):
        path = checked_relative_path(path, "packet current path")
        if path in paths:
            raise InoculationError("packet current inventory contains a duplicate")
        paths[path] = digest
    if len(paths) != 27:
        raise InoculationError(
            f"packet current path count is {len(paths)}, expected 27"
        )
    return paths


def logical_sources_from_current(current_paths):
    """Recover the fixed eighteen logical sources from the 27-path union."""
    current_paths = set(current_paths)
    if not ADDITIONAL_CURRENT_PATHS <= current_paths:
        missing = sorted(ADDITIONAL_CURRENT_PATHS - current_paths)
        raise InoculationError(
            f"packet current inventory omits cumulative paths: {missing}"
        )
    logical_targets = current_paths - ADDITIONAL_CURRENT_PATHS
    if len(logical_targets) != 18:
        raise InoculationError(
            f"derived logical target count is {len(logical_targets)}, expected 18"
        )
    sources = {
        ADR_SOURCE if target == PACKET_ADR_PATH else target
        for target in logical_targets
    }
    if len(sources) != 18:
        raise InoculationError("packet path manifest contains a duplicate")
    return sources


def packet_declared_counts(packet):
    """Extract the packet's independently declared cumulative counts."""
    section = packet_section(
        decode_utf8(packet, "packet"),
        "Mandatory restart rule",
        "Complete artifact identity",
    )
    declared = {}
    patterns = {
        "findings": r"^- (\d+) inherited findings from the first exhausted",
        "causes": r"^- (\d+) current cause guards, (\d+) runnable guards and "
                  r"(\d+) retained families;$",
        "paths": r"^- (\d+) current paths, including",
    }
    match = re.search(patterns["findings"], section, re.MULTILINE)
    if match is None:
        raise InoculationError("packet does not declare the inherited finding count")
    declared["findings"] = int(match.group(1))
    match = re.search(patterns["causes"], section, re.MULTILINE)
    if match is None:
        raise InoculationError("packet does not declare the cause and guard counts")
    declared["causes"] = int(match.group(1))
    declared["guards"] = int(match.group(2))
    declared["families"] = int(match.group(3))
    match = re.search(patterns["paths"], section, re.MULTILINE)
    if match is None:
        raise InoculationError("packet does not declare the current path count")
    declared["paths"] = int(match.group(1))
    return declared


def packet_findings(packet):
    """Bind the carried 23-finding map against the packet's declared count.

    The Carryover-3 packet pins the row-level finding evidence through the
    immutable audit sources in its 27-path inventory rather than an inline
    table, so the carried map itself is compiled in this trust root and the
    packet independently fixes its size.
    """
    declared = packet_declared_counts(packet)
    if declared["findings"] != len(EXPECTED_CARRIED_FINDINGS):
        raise InoculationError(
            f"packet declares {declared['findings']} inherited findings, "
            f"expected {len(EXPECTED_CARRIED_FINDINGS)}"
        )
    if declared["causes"] != len(EXPECTED_CURRENT_CAUSES):
        raise InoculationError(
            f"packet declares {declared['causes']} current cause guards, "
            f"expected {len(EXPECTED_CURRENT_CAUSES)}"
        )
    if declared["families"] != len(EXPECTED_FAMILIES):
        raise InoculationError(
            f"packet declares {declared['families']} families, "
            f"expected {len(EXPECTED_FAMILIES)}"
        )
    if declared["paths"] != 27:
        raise InoculationError(
            f"packet declares {declared['paths']} current paths, expected 27"
        )
    families = {
        item["family"] for item in EXPECTED_CARRIED_FINDINGS.values()
    }
    if families != EXPECTED_FAMILIES:
        raise InoculationError("carried finding families do not match the contract")
    return {
        finding_id: dict(item, guards=list(item["guards"]))
        for finding_id, item in EXPECTED_CARRIED_FINDINGS.items()
    }


def packet_current_causes(packet):
    """Extract the 26 Carryover-2 continuation causes the packet nominates.

    The packet's cause-map table names each cause and family exactly; its
    guard column is descriptive prose, so guard identities stay bound to the
    compiled contract and are separately proven runnable against the pinned
    guard surfaces.
    """
    section = packet_section(
        decode_utf8(packet, "packet"),
        "Carryover-2 continuation cause map",
        "Signed continuation chain",
    )
    causes = {}
    for line in section.splitlines():
        cells = [cell.strip() for cell in line.split("|")]
        if len(cells) != 6 or not re.fullmatch(r"R[1-8]", cells[1]):
            continue
        cause, family = cells[2].strip("`"), cells[4]
        if not cause or cause in causes:
            raise InoculationError(
                f"packet current cause is invalid or duplicated: {cause!r}"
            )
        expected = EXPECTED_CURRENT_CAUSES.get(cause)
        if expected is None:
            raise InoculationError(
                f"packet nominates an unknown current cause: {cause}"
            )
        if cause in EXPECTED_PACKET_CAUSES:
            raise InoculationError(
                f"packet repeats a predecessor cause: {cause}"
            )
        if expected["family"] != family:
            raise InoculationError(
                f"packet current cause family mismatch: {cause}"
            )
        causes[cause] = expected
    if len(causes) != 26:
        raise InoculationError(
            f"packet current cause count is {len(causes)}, expected 26"
        )
    if set(causes) != set(EXPECTED_CURRENT_CAUSES) - set(EXPECTED_PACKET_CAUSES):
        raise InoculationError(
            "packet current cause map does not match the contract"
        )
    return causes


def expected_targets(sources):
    """Apply the one accepted current-base path transform."""
    return {
        source: ADR_TARGET if source == ADR_SOURCE else source
        for source in sources
    }


def validate_transform_list(transforms):
    """Require exactly the recorded logical ADR move and no other transform."""
    if not isinstance(transforms, list) or len(transforms) != 1:
        raise InoculationError("record must contain exactly one path transform")
    transform = transforms[0]
    require_keys(transform, ("id", "source", "target"), "path transform")
    expected = {
        "id": TRANSFORM_ID,
        "source": ADR_SOURCE,
        "target": ADR_TARGET,
    }
    if transform != expected:
        raise InoculationError("record path transform is not the accepted ADR move")


def validate_cumulative_path_set(packet_values, patch_values):
    """Require the packet and patch to name the same complete current union."""
    packet_paths = set(packet_values)
    patch_paths = set(patch_values)
    if packet_paths != patch_paths:
        missing = sorted(packet_paths - patch_paths)
        extra = sorted(patch_paths - packet_paths)
        raise InoculationError(
            "packet and patch current path inventories disagree: "
            f"missing={missing}, extra={extra}"
        )
    return packet_paths


def validate_path_map(record_paths, logical_sources, transforms):
    """Compare the independently derived logical set with unique targets."""
    validate_transform_list(transforms)
    expected = expected_targets(logical_sources)
    if not isinstance(record_paths, list):
        raise InoculationError("record paths must be an array")
    observed = {}
    targets = []
    for item in record_paths:
        require_keys(
            item,
            ("source", "target", "archive_sha256", "current_sha256"),
            "record path",
        )
        source = checked_relative_path(item["source"], "record source path")
        target = checked_relative_path(item["target"], "record target path")
        for field in ("archive_sha256", "current_sha256"):
            if not isinstance(item[field], str) or HEX_256.fullmatch(item[field]) is None:
                raise InoculationError(f"record path has invalid {field}: {source}")
        if source in observed:
            raise InoculationError(f"record repeats a source path: {source}")
        observed[source] = item
        targets.append(target)
    if set(observed) != set(expected):
        missing = sorted(set(expected) - set(observed))
        extra = sorted(set(observed) - set(expected))
        raise InoculationError(
            f"record path set mismatch: missing={missing}, extra={extra}"
        )
    if len(targets) != len(set(targets)):
        raise InoculationError("record contains a duplicate target")
    for source, target in expected.items():
        if observed[source]["target"] != target:
            raise InoculationError(f"record target mismatch: {source}")
    return observed


def normalize_findings(values, label):
    """Return a closed finding map and reject duplicate IDs or guards."""
    if not isinstance(values, list):
        raise InoculationError(f"{label} must be an array")
    result = {}
    for item in values:
        require_keys(item, ("id", "owner", "guards", "family"), label)
        finding_id = item["id"]
        owner = checked_relative_path(item["owner"], f"{label} owner")
        guards = item["guards"]
        family = item["family"]
        if not isinstance(finding_id, str) or not finding_id:
            raise InoculationError(f"{label} has an invalid ID")
        if finding_id in result:
            raise InoculationError(f"{label} repeats ID: {finding_id}")
        if (
            not isinstance(guards, list)
            or not guards
            or any(
                not isinstance(guard, str)
                or re.fullmatch(r"test_[A-Za-z0-9_]+", guard) is None
                for guard in guards
            )
            or len(guards) != len(set(guards))
        ):
            raise InoculationError(f"{label} has an invalid guard set: {finding_id}")
        if family not in EXPECTED_FAMILIES:
            raise InoculationError(f"{label} has an unknown family: {finding_id}")
        result[finding_id] = {
            "owner": owner,
            "guards": list(guards),
            "family": family,
        }
    return result


def validate_finding_map(record, packet_values, packet_causes):
    """Require the exact carried findings and amended current-base causes."""
    observed = normalize_findings(record.get("findings"), "record findings")
    if set(observed) != set(packet_values):
        raise InoculationError("record finding IDs do not match the packet")
    for finding_id, expected in packet_values.items():
        current = observed[finding_id]
        if (
            current["owner"] != expected["owner"]
            or current["family"] != expected["family"]
            or set(current["guards"]) != set(expected["guards"])
        ):
            raise InoculationError(f"record finding mismatch: {finding_id}")
    causes = normalize_findings(
        record.get("current_cause_guards"), "current cause guards"
    )
    if causes != EXPECTED_CURRENT_CAUSES:
        raise InoculationError("current cause guard map does not match the contract")
    if any(causes.get(key) != value for key, value in packet_causes.items()):
        raise InoculationError(
            "record current cause map does not preserve the packet"
        )
    return observed, causes


def validate_record_shape(record):
    """Validate the closed durable shape before reading any named target."""
    require_keys(
        record,
        (
            "schema",
            "current_base",
            "artifacts",
            "archive",
            "transforms",
            "paths",
            "families",
            "findings",
            "current_cause_guards",
        ),
        "record",
    )
    if record["schema"] != SCHEMA:
        raise InoculationError("record schema is not supported")
    if record["current_base"] != EXPECTED_CURRENT_BASE:
        raise InoculationError("record current base does not match the replacement run")
    archive = record["archive"]
    require_keys(archive, ("ref", "commit", "tree"), "record archive")
    if archive != {
        "ref": EXPECTED_ARCHIVE_REF,
        "commit": EXPECTED_ARCHIVE_COMMIT,
        "tree": EXPECTED_ARCHIVE_TREE,
    }:
        raise InoculationError("record archive identity does not match the packet")
    families = record["families"]
    if (
        not isinstance(families, list)
        or len(families) != len(set(families))
        or set(families) != EXPECTED_FAMILIES
    ):
        raise InoculationError("record families do not match the thirteen-family contract")
    validate_transform_list(record["transforms"])


def unittest_methods(tree):
    """Count statically provable cases in top-level TestCase descendants."""

    try_statement_types = (ast.Try,)
    if hasattr(ast, "TryStar"):
        try_statement_types += (ast.TryStar,)
    local_function_names = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }

    def target_names(target):
        if isinstance(target, ast.Name):
            return {target.id}
        if isinstance(target, (ast.Tuple, ast.List)):
            return set().union(*(target_names(item) for item in target.elts))
        if isinstance(target, (ast.Attribute, ast.Subscript)):
            raise InoculationError(
                "guard AST has a dynamic module mutation"
            )
        return set()

    def expression_bindings(expression):
        if expression is None:
            return set()
        namespace_mutators = {
            "setattr",
            "delattr",
            "__setattr__",
            "__delattr__",
            "setitem",
            "delitem",
            "__setitem__",
            "__delitem__",
            "update",
            "setdefault",
            "pop",
            "popitem",
            "clear",
            "exec",
            "eval",
        }
        if any(
            isinstance(node, ast.Call)
            and (
                (
                    isinstance(node.func, ast.Name)
                    and (
                        node.func.id in namespace_mutators
                        or node.func.id in local_function_names
                    )
                )
                or (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr in namespace_mutators
                )
            )
            for node in ast.walk(expression)
        ):
            raise InoculationError(
                "guard AST has a dynamic module mutation"
            )
        return set().union(*(
            target_names(node.target)
            for node in ast.walk(expression)
            if isinstance(node, ast.NamedExpr)
        ))

    def pattern_bindings(pattern):
        if isinstance(pattern, ast.MatchAs):
            result = {pattern.name} if pattern.name else set()
            if pattern.pattern is not None:
                result.update(pattern_bindings(pattern.pattern))
            return result
        if isinstance(pattern, ast.MatchStar):
            return {pattern.name} if pattern.name else set()
        if isinstance(pattern, ast.MatchMapping):
            result = {pattern.rest} if pattern.rest else set()
            for child in pattern.patterns:
                result.update(pattern_bindings(child))
            return result
        if isinstance(pattern, (ast.MatchSequence, ast.MatchOr)):
            return set().union(*(
                pattern_bindings(child) for child in pattern.patterns
            ))
        if isinstance(pattern, ast.MatchClass):
            return set().union(*(
                pattern_bindings(child)
                for child in [*pattern.patterns, *pattern.kwd_patterns]
            ))
        return set()

    def statement_bindings(statement):
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result = {statement.name}
            expressions = [
                *statement.decorator_list,
                *statement.args.defaults,
                *(
                    value
                    for value in statement.args.kw_defaults
                    if value is not None
                ),
            ]
            for expression in expressions:
                result.update(expression_bindings(expression))
            return result
        if isinstance(statement, ast.ClassDef):
            result = {statement.name}
            expressions = [
                *statement.decorator_list,
                *statement.bases,
                *(keyword.value for keyword in statement.keywords),
            ]
            for expression in expressions:
                result.update(expression_bindings(expression))
            return result
        if isinstance(statement, (ast.Import, ast.ImportFrom)):
            return {
                item.asname or item.name.split(".")[0]
                for item in statement.names
            }
        if isinstance(statement, ast.Assign):
            result = set().union(*(
                target_names(item) for item in statement.targets
            ))
            result.update(expression_bindings(statement.value))
            return result
        if isinstance(statement, (ast.AnnAssign, ast.AugAssign)):
            result = target_names(statement.target)
            result.update(expression_bindings(statement.value))
            return result
        if isinstance(statement, (ast.For, ast.AsyncFor)):
            result = target_names(statement.target)
            result.update(expression_bindings(statement.iter))
            children = [*statement.body, *statement.orelse]
        elif isinstance(statement, (ast.If, ast.While)):
            result = expression_bindings(statement.test)
            children = [*statement.body, *statement.orelse]
        elif isinstance(statement, (ast.With, ast.AsyncWith)):
            result = set().union(*(
                target_names(item.optional_vars)
                for item in statement.items
                if item.optional_vars is not None
            )) if statement.items else set()
            for item in statement.items:
                result.update(expression_bindings(item.context_expr))
            children = statement.body
        elif isinstance(statement, try_statement_types):
            result = {
                handler.name
                for handler in statement.handlers
                if isinstance(handler.name, str)
            }
            children = [
                *statement.body,
                *statement.orelse,
                *statement.finalbody,
                *(item for handler in statement.handlers for item in handler.body),
            ]
        elif isinstance(statement, ast.Match):
            result = expression_bindings(statement.subject)
            children = []
            for case in statement.cases:
                result.update(pattern_bindings(case.pattern))
                result.update(expression_bindings(case.guard))
                children.extend(case.body)
        elif isinstance(statement, ast.Expr):
            return expression_bindings(statement.value)
        elif isinstance(statement, ast.Delete):
            return set().union(*(
                target_names(item) for item in statement.targets
            ))
        else:
            return set()
        for child in children:
            result.update(statement_bindings(child))
        return result

    module_bindings = Counter(
        name
        for statement in tree.body
        for name in statement_bindings(statement)
    )
    if (
        module_bindings["load_tests"]
        or module_bindings["__getattr__"]
        or module_bindings["__dir__"]
    ):
        raise InoculationError(
            "guard AST has a dynamic unittest discovery hook"
        )

    unittest_aliases = set()
    testcase_aliases = set()
    for statement in tree.body:
        if isinstance(statement, ast.Import):
            for item in statement.names:
                if item.name == "unittest":
                    unittest_aliases.add(item.asname or "unittest")
        elif isinstance(statement, ast.ImportFrom) and statement.module == "unittest":
            for item in statement.names:
                if item.name == "TestCase":
                    testcase_aliases.add(item.asname or item.name)

    for alias in unittest_aliases | testcase_aliases:
        if module_bindings[alias] != 1:
            raise InoculationError(
                f"guard AST shadows unittest binding: {alias}"
            )

    class_nodes = [
        node for node in tree.body if isinstance(node, ast.ClassDef)
    ]
    class_counts = Counter(node.name for node in class_nodes)
    duplicates = sorted(name for name, count in class_counts.items() if count != 1)
    if duplicates:
        raise InoculationError(
            f"guard AST repeats a top-level class binding: {duplicates}"
        )
    classes = {node.name: node for node in class_nodes}
    ancestry = {}

    def direct_testcase_base(base):
        return (
            isinstance(base, ast.Attribute)
            and isinstance(base.value, ast.Name)
            and base.value.id in unittest_aliases
            and base.attr == "TestCase"
        ) or (isinstance(base, ast.Name) and base.id in testcase_aliases)

    def descends_from_testcase(node, visiting=None):
        if node.name in ancestry:
            return ancestry[node.name]
        visiting = set() if visiting is None else visiting
        if node.name in visiting:
            raise InoculationError("guard AST has cyclic local inheritance")
        next_visiting = visiting | {node.name}
        result = any(direct_testcase_base(base) for base in node.bases)
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id in classes:
                result = result or descends_from_testcase(
                    classes[base.id], next_visiting
                )
        ancestry[node.name] = result
        return result

    descendants = {
        name: node
        for name, node in classes.items()
        if descends_from_testcase(node)
    }
    for statement in tree.body:
        if (
            isinstance(statement, ast.Assign)
            and isinstance(statement.value, ast.Name)
            and statement.value.id in descendants
            and any(target_names(target) for target in statement.targets)
        ):
            raise InoculationError(
                "guard AST aliases a discovered TestCase binding"
            )
    for name, node in descendants.items():
        if module_bindings[name] != 1:
            raise InoculationError(
                f"guard AST overwrites a TestCase binding: {name}"
            )
        if node.decorator_list or node.keywords:
            raise InoculationError(
                f"guard AST has a dynamic TestCase definition: {name}"
            )
        recognised_bases = [
            base
            for base in node.bases
            if direct_testcase_base(base)
            or (isinstance(base, ast.Name) and base.id in classes)
        ]
        if len(recognised_bases) != len(node.bases) or len(node.bases) != 1:
            raise InoculationError(
                f"guard AST has unbounded TestCase inheritance: {name}"
            )
        for member in node.body:
            if isinstance(
                member, (ast.Assign, ast.AnnAssign, ast.AugAssign)
            ):
                if "__unittest_skip__" in statement_bindings(member):
                    raise InoculationError(
                        f"guard AST has a dynamic skip binding: {name}"
                    )
                raise InoculationError(
                    "guard AST has a dynamic TestCase namespace mutation: "
                    f"{name}"
                )
            if isinstance(
                member, (ast.FunctionDef, ast.AsyncFunctionDef)
            ) and member.name == "__init_subclass__":
                raise InoculationError(
                    "guard AST has a dynamic TestCase runtime mutation: "
                    f"{name}"
                )
            if isinstance(
                member, (ast.FunctionDef, ast.AsyncFunctionDef)
            ) and member.name in {"run", "__call__"}:
                raise InoculationError(
                    "guard AST has a custom TestCase execution entrypoint: "
                    f"{name}.{member.name}"
                )
            if isinstance(
                member, (ast.FunctionDef, ast.AsyncFunctionDef)
            ) and member.name == "_callTestMethod":
                raise InoculationError(
                    "guard AST has custom TestCase method dispatch: "
                    f"{name}.{member.name}"
                )
            if isinstance(
                member, (ast.FunctionDef, ast.AsyncFunctionDef)
            ) and not member.name.startswith("test_") and any(
                not (
                    isinstance(decorator, ast.Name)
                    and decorator.id in {"classmethod", "staticmethod"}
                    and module_bindings[decorator.id] == 0
                )
                for decorator in member.decorator_list
            ):
                raise InoculationError(
                    "guard AST has a dynamic TestCase decorator mutation: "
                    f"{name}.{member.name}"
                )

    effective = {}

    def effective_methods(node, visiting=None):
        if node.name in effective:
            return effective[node.name]
        visiting = set() if visiting is None else visiting
        if node.name in visiting:
            raise InoculationError("guard AST has cyclic method inheritance")
        methods = set()
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id in classes:
                methods.update(
                    effective_methods(classes[base.id], visiting | {node.name})
                )
        local_bindings = Counter()
        local_methods = set()
        for member in node.body:
            if isinstance(member, ast.Expr) and not (
                isinstance(member.value, ast.Constant)
                and isinstance(member.value.value, str)
            ):
                raise InoculationError(
                    "guard AST has a dynamic TestCase namespace mutation: "
                    f"{node.name}"
                )
            names = statement_bindings(member)
            for name in names:
                if name.startswith("test_"):
                    local_bindings[name] += 1
            if isinstance(member, ast.FunctionDef) and member.name.startswith("test_"):
                if member.decorator_list:
                    raise InoculationError(
                        f"guard AST decorates a test method: {member.name}"
                    )
                local_methods.add(member.name)
            elif isinstance(member, ast.AsyncFunctionDef) and member.name.startswith("test_"):
                raise InoculationError(
                    f"guard AST has an async unittest method: {member.name}"
                )
            elif any(name.startswith("test_") for name in names):
                raise InoculationError(
                    f"guard AST has a dynamic test binding in: {node.name}"
                )
        repeated = sorted(name for name, count in local_bindings.items() if count != 1)
        if repeated:
            raise InoculationError(
                f"guard AST repeats a test method binding: {repeated}"
            )
        methods.update(local_methods)
        effective[node.name] = methods
        return methods

    methods = Counter()
    for node in descendants.values():
        methods.update(effective_methods(node))
    return methods


def runtime_unittest_methods(root, guard_path, source, required):
    """Discover and execution-probe required guards from exact checked bytes."""
    root = Path(root).resolve(strict=True)
    guard_path = checked_relative_path(guard_path, "guard path")
    required = sorted(set(required))
    if (
        not required
        or any(
            not isinstance(name, str)
            or re.fullmatch(r"test_[A-Za-z0-9_]+", name) is None
            for name in required
        )
    ):
        raise InoculationError("runtime unittest discovery guard set is invalid")
    required_json = json.dumps(required, separators=(",", ":"))
    if len(required_json.encode("utf-8")) > MAX_RUNTIME_DISCOVERY_REQUEST_BYTES:
        raise InoculationError(
            "runtime unittest discovery guard set exceeds its byte limit"
        )
    write_fd = None
    read_fd = None
    try:
        read_fd, write_fd = os.pipe()
        environment = os.environ.copy()
        for name in (
            "PYTHONHOME",
            "PYTHONINSPECT",
            "PYTHONPATH",
            "PYTHONSTARTUP",
        ):
            environment.pop(name, None)
        environment["LC_ALL"] = "C"
        try:
            completed = subprocess.run(
                [
                    sys.executable,
                    "-I",
                    "-c",
                    RUNTIME_DISCOVERY_PROGRAM,
                    str(write_fd),
                    str(root / guard_path),
                    required_json,
                ],
                cwd=root,
                env=environment,
                input=source,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                pass_fds=(write_fd,),
                check=False,
                timeout=RUNTIME_DISCOVERY_TIMEOUT_SECONDS,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise InoculationError(
                f"runtime unittest discovery failed: {error}"
            ) from None
        finally:
            os.close(write_fd)
            write_fd = None
        payload = bytearray()
        # The isolated interpreter has exited. Waiting for EOF here would give
        # any forked descendant that retained the writer control of our bound.
        try:
            os.set_blocking(read_fd, False)
        except OSError as error:
            raise InoculationError(
                f"runtime unittest discovery result read failed: {error}"
            ) from None
        while len(payload) <= MAX_RUNTIME_DISCOVERY_BYTES:
            try:
                chunk = os.read(
                    read_fd,
                    min(
                        65_536,
                        MAX_RUNTIME_DISCOVERY_BYTES + 1 - len(payload),
                    ),
                )
            except BlockingIOError:
                break
            except OSError as error:
                raise InoculationError(
                    "runtime unittest discovery result read failed: "
                    f"{error}"
                ) from None
            if not chunk:
                break
            payload.extend(chunk)
        if len(payload) > MAX_RUNTIME_DISCOVERY_BYTES:
            raise InoculationError(
                "runtime unittest discovery result exceeds its byte limit"
            )
        if completed.returncode != 0:
            raise InoculationError("runtime unittest discovery child failed")
        try:
            result = json.loads(
                payload.decode("utf-8"), object_pairs_hook=strict_object
            )
        except (
            UnicodeError,
            ValueError,
            RecursionError,
            OverflowError,
            MemoryError,
        ) as error:
            raise InoculationError(
                f"runtime unittest discovery result is invalid: {error}"
            ) from None
        require_keys(
            result,
            ("ok", "counts", "executed", "error"),
            "runtime discovery",
        )
        counts = result["counts"]
        executed = result["executed"]
        if (
            result["ok"] is not True
            or result["error"] is not None
            or not isinstance(counts, dict)
            or set(counts) != set(required)
            or any(type(value) is not int or value < 0 for value in counts.values())
            or not isinstance(executed, dict)
            or set(executed) != set(required)
            or any(
                type(value) is not int or value < 0
                for value in executed.values()
            )
            or executed != counts
        ):
            raise InoculationError(
                "runtime unittest discovery and execution probe was not complete"
            )
        return Counter(counts)
    finally:
        if write_fd is not None:
            os.close(write_fd)
        if read_fd is not None:
            os.close(read_fd)


def verify_guard_names(
    root, findings, causes, *, expected_guard_sha256=None
):
    """Prove every named guard is one unique runnable unittest case."""
    if expected_guard_sha256 is None:
        expected_guard_sha256 = EXPECTED_GUARD_SHA256
    required_by_path = {}
    required = set()
    for item in list(findings.values()) + list(causes.values()):
        guard_path = GUARD_PATH_BY_OWNER.get(item["owner"])
        if guard_path is None:
            raise InoculationError(
                f"no guard surface is bound to owner: {item['owner']}"
            )
        required_by_path.setdefault(guard_path, set()).update(item["guards"])
        required.update(item["guards"])

    for guard_path, path_required in required_by_path.items():
        source = target_bytes(root, guard_path)
        expected_digest = expected_guard_sha256.get(guard_path)
        if expected_digest is None:
            raise InoculationError(
                f"no fixed content identity exists for guard surface: {guard_path}"
            )
        if sha256_bytes(source) != expected_digest:
            raise InoculationError(
                f"guard surface content identity mismatch: {guard_path}"
            )
        try:
            tree = ast.parse(source, filename=guard_path)
        except (SyntaxError, ValueError, RecursionError) as error:
            raise InoculationError(f"guard AST is invalid: {error}") from None
        declared = Counter(
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        )
        missing = sorted(
            guard for guard in path_required if declared[guard] == 0
        )
        if missing:
            raise InoculationError(f"current guard is missing: {missing}")
        discovered = unittest_methods(tree)
        undiscovered = sorted(
            guard for guard in path_required if discovered[guard] != 1
        )
        if undiscovered:
            raise InoculationError(
                "current guard is not one discovered unittest case: "
                f"{undiscovered}"
            )
        runtime_discovered = runtime_unittest_methods(
            root, guard_path, source, path_required
        )
        runtime_undiscovered = sorted(
            guard
            for guard in path_required
            if runtime_discovered[guard] != 1
        )
        if runtime_undiscovered:
            raise InoculationError(
                "current guard is not one runtime unittest discovery case: "
                f"{runtime_undiscovered}"
            )
    return required


def git_environment():
    """Return a non-interactive environment for bounded Git object reads."""
    environment = os.environ.copy()
    for name in (
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_COMMON_DIR",
    ):
        environment.pop(name, None)
    environment.update({
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_PAGER": "cat",
        "GIT_TERMINAL_PROMPT": "0",
        "LC_ALL": "C",
    })
    return environment


def git_run(
    root,
    arguments,
    label,
    allowed=(0,),
    stdin_bytes=None,
    maximum_stdout=None,
):
    """Run fixed-argv Git with bounded diagnostics and a short timeout."""
    try:
        completed = subprocess.run(
            ["git", "-c", "core.pager=cat", *arguments],
            cwd=root,
            env=git_environment(),
            input=b"" if stdin_bytes is None else stdin_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise InoculationError(f"{label} failed: {error}") from None
    if (
        len(completed.stderr) > MAX_GIT_DIAGNOSTIC_BYTES
        or (
            maximum_stdout is not None
            and len(completed.stdout) > maximum_stdout
        )
        or completed.returncode not in allowed
    ):
        raise InoculationError(f"{label} was refused by Git")
    return completed


def git_text(root, arguments, label):
    """Read one short ASCII Git identity."""
    completed = git_run(root, arguments, label)
    if len(completed.stdout) > 4_096:
        raise InoculationError(f"{label} output exceeds its bound")
    try:
        return completed.stdout.decode("ascii").strip()
    except UnicodeError:
        raise InoculationError(f"{label} output is not ASCII") from None


def git_object_bytes(root, object_id, expected_type, maximum, label):
    """Read one bounded object and recompute the identity named by Git."""
    if COMMIT_ID.fullmatch(object_id) is None:
        raise InoculationError(f"{label} has an invalid object identity")
    object_type = git_text(root, ["cat-file", "-t", object_id], label)
    if object_type != expected_type:
        raise InoculationError(f"{label} has an unexpected Git object type")
    size_text = git_text(root, ["cat-file", "-s", object_id], label)
    try:
        size = int(size_text)
    except ValueError:
        raise InoculationError(f"{label} has an invalid Git object size") from None
    if size < 0 or size > maximum:
        raise InoculationError(f"{label} exceeds its Git object bound")
    completed = git_run(
        root,
        ["cat-file", "--batch"],
        label,
        stdin_bytes=f"{object_id}\n".encode("ascii"),
        maximum_stdout=size + 4_096,
    )
    header, separator, framed = completed.stdout.partition(b"\n")
    if not separator or not framed.endswith(b"\n"):
        raise InoculationError(f"{label} has an invalid Git object frame")
    try:
        returned_id, returned_type, returned_size = header.decode("ascii").split()
        framed_size = int(returned_size)
    except (UnicodeError, ValueError):
        raise InoculationError(f"{label} has an invalid Git object header") from None
    payload = framed[:-1]
    if (
        returned_id != object_id
        or returned_type != expected_type
        or framed_size != size
        or len(payload) != size
    ):
        raise InoculationError(f"{label} changed while its Git object was read")
    identity = hashlib.sha1(
        f"{expected_type} {size}\0".encode("ascii") + payload
    ).hexdigest()
    if identity != object_id:
        raise InoculationError(f"Git object identity mismatch: {label}")
    return payload


def archive_blob(root, source):
    """Read one bounded immutable blob from the verified archive commit."""
    object_name = f"{EXPECTED_ARCHIVE_COMMIT}:{source}"
    object_id = git_text(
        root, ["rev-parse", "--verify", object_name], "archive blob lookup"
    )
    if COMMIT_ID.fullmatch(object_id) is None:
        raise InoculationError(f"archive blob has an invalid identity: {source}")
    return git_object_bytes(
        root,
        object_id,
        "blob",
        MAX_TARGET_BYTES,
        f"archive blob {source}",
    )


def verify_git_identities(root):
    """Bind the current branch and local provenance archive to fixed objects."""
    current_base = git_text(
        root,
        ["rev-parse", "--verify", f"{EXPECTED_CURRENT_BASE}^{{commit}}"],
        "current base lookup",
    )
    if current_base != EXPECTED_CURRENT_BASE:
        raise InoculationError("current base object is not available")
    git_object_bytes(
        root,
        EXPECTED_CURRENT_BASE,
        "commit",
        MAX_TARGET_BYTES,
        "current base commit",
    )
    git_object_bytes(
        root,
        EXPECTED_PATCH_BASE,
        "commit",
        MAX_TARGET_BYTES,
        "cumulative patch base commit",
    )
    ancestry = git_run(
        root,
        ["merge-base", "--is-ancestor", EXPECTED_CURRENT_BASE, "HEAD"],
        "current base ancestry",
        allowed=(0, 1),
    )
    if ancestry.returncode != 0:
        raise InoculationError("HEAD does not descend from the replacement base")
    archive_commit = git_text(
        root,
        ["rev-parse", "--verify", f"refs/heads/{EXPECTED_ARCHIVE_REF}"],
        "archive ref lookup",
    )
    if archive_commit != EXPECTED_ARCHIVE_COMMIT:
        raise InoculationError("archive ref does not resolve to the published commit")
    archive_commit_bytes = git_object_bytes(
        root,
        EXPECTED_ARCHIVE_COMMIT,
        "commit",
        MAX_TARGET_BYTES,
        "archive commit",
    )
    archive_tree = git_text(
        root,
        ["rev-parse", "--verify", f"{EXPECTED_ARCHIVE_COMMIT}^{{tree}}"],
        "archive tree lookup",
    )
    if archive_tree != EXPECTED_ARCHIVE_TREE:
        raise InoculationError("archive tree does not match the published tree")
    if not archive_commit_bytes.startswith(
        f"tree {EXPECTED_ARCHIVE_TREE}\n".encode("ascii")
    ):
        raise InoculationError("archive commit does not bind the published tree")
    git_object_bytes(
        root,
        EXPECTED_ARCHIVE_TREE,
        "tree",
        MAX_TARGET_BYTES,
        "archive tree",
    )
    git_run(
        root,
        [
            "fsck",
            "--strict",
            "--no-reflogs",
            "--no-progress",
            "--no-dangling",
            EXPECTED_ARCHIVE_COMMIT,
        ],
        "archive reachable-object identity check",
        maximum_stdout=MAX_GIT_DIAGNOSTIC_BYTES,
    )
    cumulative_commit = git_object_bytes(
        root,
        EXPECTED_CUMULATIVE_COMMIT,
        "commit",
        MAX_TARGET_BYTES,
        "cumulative evidence commit",
    )
    cumulative_tree = git_text(
        root,
        [
            "rev-parse",
            "--verify",
            f"{EXPECTED_CUMULATIVE_COMMIT}^{{tree}}",
        ],
        "cumulative evidence tree lookup",
    )
    if cumulative_tree != EXPECTED_CUMULATIVE_TREE:
        raise InoculationError(
            "cumulative evidence tree does not match the published tree"
        )
    if not cumulative_commit.startswith(
        f"tree {EXPECTED_CUMULATIVE_TREE}\n".encode("ascii")
    ):
        raise InoculationError(
            "cumulative evidence commit does not bind the published tree"
        )
    git_object_bytes(
        root,
        EXPECTED_CUMULATIVE_TREE,
        "tree",
        MAX_TARGET_BYTES,
        "cumulative evidence tree",
    )


def current_target_identity_mismatches(path_map):
    """Name record identities that differ from the compiled target contract."""
    mismatches = []
    for source, item in path_map.items():
        expected = EXPECTED_CHANGED_CURRENT_SHA256.get(
            source, item["archive_sha256"]
        )
        if item["current_sha256"] != expected:
            mismatches.append(source)
    return mismatches


def verify_current_targets(root, path_map):
    """Bind every target to archive identity or one fixed reviewed divergence."""
    mismatches = current_target_identity_mismatches(path_map)
    if mismatches:
        raise InoculationError(
            f"record current content identity mismatch: {mismatches[0]}"
        )
    for source, item in path_map.items():
        expected = EXPECTED_CHANGED_CURRENT_SHA256.get(
            source, item["archive_sha256"]
        )
        current = target_bytes(root, item["target"])
        if sha256_bytes(current) != expected:
            raise InoculationError(f"current target content mismatch: {source}")


def verify_archive_targets(root, path_map):
    """Bind every source path to its immutable archived content identity."""
    for source, item in path_map.items():
        if sha256_bytes(archive_blob(root, source)) != item["archive_sha256"]:
            raise InoculationError(f"archive content mismatch: {source}")


def verify_cumulative_targets(root, current_inventory):
    """Bind the complete 27-path current union to packet or reviewed bytes."""
    rebound = set(EXPECTED_CUMULATIVE_REBIND_SHA256)
    if not rebound <= set(current_inventory):
        raise InoculationError("cumulative rebind names a path outside the packet")
    for path, packet_digest in current_inventory.items():
        current = target_bytes(
            root, ADR_TARGET if path == PACKET_ADR_PATH else path
        )
        if path == VERIFIER_PATH:
            executed = Path(__file__).resolve(strict=True)
            expected = (Path(root).resolve(strict=True) / path).resolve(strict=True)
            if executed != expected:
                raise InoculationError(
                    "executed verifier is not the cumulative target"
                )
            continue
        expected = EXPECTED_CUMULATIVE_REBIND_SHA256.get(
            path, packet_digest
        )
        if HEX_256.fullmatch(expected) is None or expected == "0" * 64:
            raise InoculationError(
                f"cumulative current identity is not rebound: {path}"
            )
        if sha256_bytes(current) != expected:
            raise InoculationError(
                f"cumulative current target content mismatch: {path}"
            )


def verify(packet_path, patch_path, record_path, root):
    """Run the complete bootstrap over the packet, the record and the tree."""
    root = Path(root).resolve(strict=True)
    packet = bounded_regular_bytes(packet_path, MAX_PACKET_BYTES, "packet")
    patch = bounded_regular_bytes(patch_path, MAX_PATCH_BYTES, "patch")
    record = load_record(record_path)
    validate_record_shape(record)
    artifact_digests(packet, patch, record)
    packet_current_values = packet_current_paths(packet)
    patch_path_values = patch_paths(patch)
    current_union = validate_cumulative_path_set(
        packet_current_values, patch_path_values
    )
    logical_sources = logical_sources_from_current(current_union)
    path_map = validate_path_map(
        record["paths"],
        logical_sources,
        record["transforms"],
    )
    packet_finding_values = packet_findings(packet)
    packet_cause_values = packet_current_causes(packet)
    findings, causes = validate_finding_map(
        record, packet_finding_values, packet_cause_values
    )
    verify_git_identities(root)
    verify_archive_targets(root, path_map)
    verify_current_targets(root, path_map)
    verify_cumulative_targets(root, packet_current_values)
    guards = verify_guard_names(root, findings, causes)
    declared = packet_declared_counts(packet)
    if declared["guards"] != len(guards):
        raise InoculationError(
            f"packet declares {declared['guards']} runnable guards, "
            f"found {len(guards)}"
        )
    return {
        "current_base": EXPECTED_CURRENT_BASE,
        "logical_paths": len(path_map),
        "current_targets": len({item["target"] for item in path_map.values()}),
        "transforms": len(record["transforms"]),
        "findings": len(findings),
        "current_causes": len(causes),
        "guards": len(guards),
        "families": len(record["families"]),
        "cumulative_paths": len(current_union),
    }


def argument_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", required=True)
    parser.add_argument("--patch", required=True)
    parser.add_argument("--record", required=True)
    parser.add_argument("--root", required=True)
    return parser


def main(argv=None):
    arguments = argument_parser().parse_args(argv)
    try:
        summary = verify(
            arguments.packet,
            arguments.patch,
            arguments.record,
            arguments.root,
        )
    except (InoculationError, OSError) as error:
        print(f"issue-622 inoculation refused: {error}", file=sys.stderr)
        return 1
    print(
        "issue-622 inoculation verified: "
        f"base {summary['current_base']}; "
        f"{summary['logical_paths']} logical paths; "
        f"{summary['current_targets']} current targets; "
        f"{summary['transforms']} transform; "
        f"{summary['findings']} inherited findings; "
        f"{summary['current_causes']} current cause guards; "
        f"{summary['guards']} unique runnable guards; "
        f"{summary['families']} families"
        f"; {summary['cumulative_paths']} cumulative paths"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
