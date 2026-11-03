"""The Hexaemeron runner keeps stated headroom under its manifest cap.

`plugins/hexaemeron/tests/run_tests.py` refuses to start once its encoded test
manifest passes `MAX_MANIFEST_BYTES`, before any test runs (#1971). This module
discovers the same manifest with the runner's own `discover_manifest` and
`manifest_bytes` in a child process, so neither suite's modules load here. It
fails while fewer than `RESERVE_BYTES` remain, so a change meets the limit in
the root suite rather than inside a step's Exit, and it refuses a test method
name longer than `MAX_METHOD_CHARS` unless the name is listed below.

`python3 tests/test_hexaemeron_manifest_headroom.py` prints the measurement.
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "plugins" / "hexaemeron" / "tests"
# About 31 median modules at the 2,121 bytes each added on 2026-11-02.
RESERVE_BYTES = 65_536
MAX_METHOD_CHARS = 60
MEASURE = (
    "import json, sys\n"
    "sys.path.insert(0, '.')\n"
    "import run_tests\n"
    "_, ids, _ = run_tests.discover_manifest()\n"
    "cap = run_tests.MAX_MANIFEST_BYTES\n"
    "# Measure past the cap too, so an overrun reports its size.\n"
    "run_tests.MAX_MANIFEST_BYTES = 1 << 40\n"
    "used = len(run_tests.manifest_bytes(ids))\n"
    "print(json.dumps({'cap': cap, 'bytes': used, 'ids': ids}))\n"
)
# Long names a record owned elsewhere fixes; renaming one moves that record.
# Remove a name here when its test is renamed under the bound.
GRANDFATHERED = frozenset({
    # Named in the Fiat checkpoint-authority manifests under
    # plugins/hexaemeron/skills/fiat/checkpoint-authority/.
    'test_a_mutable_branch_or_tag_is_never_a_compatibility_decision',
    'test_a_spawn_error_outside_the_transient_set_is_never_retried',
    'test_a_spawn_failure_that_persists_to_the_deadline_still_refuses',
    'test_a_stale_manifest_refuses_even_with_every_component_present',
    'test_a_transient_spawn_failure_is_retried_rather_than_reported_unavailable',
    'test_a_valid_history_without_fresh_evidence_invents_no_current_permission',
    'test_acceptance_domain_is_external_and_not_an_envelope_digest',
    'test_actual_dag_union_includes_both_steps_and_push_only_commits',
    'test_alternate_carrier_needs_full_native_equivalence_and_creates_no_child',
    'test_an_absent_independent_verifier_never_claims_network_denial',
    'test_an_ariadne_pass_alone_establishes_no_current_eligibility',
    'test_an_unknown_operation_or_operand_exits_two_without_echoing_it',
    'test_challenge_time_and_remembered_floor_cannot_be_self_asserted',
    'test_contradictory_decisions_after_denial_and_stale_denial_heads_refuse',
    'test_embedded_missing_extra_duplicate_ranges_never_define_denominator',
    'test_enrollment_requires_exact_challenge_actor_key_proof_and_expiry',
    'test_event_sequence_gaps_forks_payload_and_decision_substitution',
    'test_every_declared_hostile_release_case_refuses_by_its_recorded_code',
    'test_every_recorded_hostile_mutation_refuses_with_its_recorded_code',
    'test_evidence_reference_role_digest_and_copy_substitutions_refuse',
    'test_exact_and_randomized_signature_retries_keep_first_envelope',
    'test_fixture_has_independent_public_keys_and_four_real_commit_ranges',
    'test_foreign_scope_unknown_types_and_unjournaled_events_refuse',
    'test_group_permission_after_exit_is_retried_without_ignoring_denial',
    'test_historical_sigs_require_historical_approval_not_uploader',
    'test_history_carries_no_private_material_and_synthetic_native_only',
    'test_malformed_transitive_rows_refuse_before_opening_any_component',
    'test_manifest_without_ariadne_cases_or_with_foreign_cases_refuses',
    'test_missing_fields_unknown_fields_and_wrong_subject_roles_refuse',
    'test_missing_or_unchecked_declared_evidence_gates_fail_closed',
    'test_multiple_native_attempts_share_the_declared_check_budget',
    'test_native_proof_is_exact_current_subset_not_complete_history',
    'test_no_file_outside_the_named_operands_is_opened_by_the_bounded_reader',
    'test_omission_duplicate_and_missing_terminal_head_are_incomplete',
    'test_partial_duplicate_and_skipped_execution_never_passes_criterion',
    'test_permit_binds_exact_representation_finalization_and_grant',
    'test_registered_complete_results_and_explicit_authority_unknowns',
    'test_release_digests_rebuild_twice_identically_from_the_same_tree',
    'test_restore_success_must_join_nested_success_status_and_next',
    'test_schema_evidence_names_do_not_allow_self_attested_authority',
    'test_signed_noncanonical_unknown_statement_and_subject_swap_refuse',
    'test_the_committed_corpus_manifest_and_lock_example_have_no_drift',
    'test_the_demonstration_blocks_a_verifier_that_attempts_a_real_socket',
    'test_the_example_lock_leaves_the_authority_commit_for_the_consumer',
    'test_the_independent_verifier_agrees_on_every_released_case_under_network_denial',
    'test_the_manifest_never_hashes_itself_and_names_its_external_pins',
    'test_the_offline_demonstration_reconstructs_the_complete_accepted_history',
    'test_the_release_separates_authority_and_native_toolchain_pins',
    'test_the_released_verifier_runs_outside_the_repository_checkout',
    'test_the_verifier_component_lists_every_released_module_and_the_command_line',
    'test_the_verify_operation_reconstructs_the_history_from_named_files_alone',
    'test_unknown_predicate_and_fake_block_declaration_cannot_disable_core',
    # Their modules' SHA-256 is pinned by a skill DEMONSTRATION.md.
    'test_a_parked_flag_the_standing_parks_do_not_support_is_refused',
    'test_a_pass_declaring_nothing_matches_the_line_recorded_before',
    'test_a_scoreboard_path_that_is_not_there_cannot_forge_a_declaration',
    'test_a_symlink_at_the_kronos_directory_is_refused_on_pull_and_push',
    'test_a_total_that_is_not_a_whole_number_ends_show_before_it_prints',
    'test_a_truncated_final_line_is_refused_rather_than_written_past',
    'test_absolute_traversal_and_symlink_report_paths_are_rejected',
    'test_an_unrelated_function_named_sanitize_does_not_earn_trust',
    'test_argv_findings_do_not_repeat_secret_material_in_text_or_json',
    'test_blob_shape_mode_digest_object_parent_and_order_fail_closed',
    'test_cold_native_forge_fails_closed_when_it_needs_a_solc_child',
    'test_comprehension_named_expression_disqualifies_outer_assignment',
    'test_comprehension_targets_do_not_disqualify_outer_assignments',
    'test_diagnostic_poisoning_and_exit_code_do_not_change_the_report',
    'test_every_line_show_and_main_write_goes_through_one_collapse',
    'test_every_value_show_prints_is_collapsed_not_only_the_named_ones',
    'test_git_replacement_objects_do_not_change_supplied_blob_evidence',
    'test_it_allows_a_visible_transform_that_removes_the_sensitive_field',
    'test_it_flags_a_session_token_written_to_storage_on_the_exact_line',
    'test_it_flags_an_interpolated_absolute_host_on_the_exact_line',
    'test_it_flags_raw_rehype_without_a_later_sanitiser_on_the_exact_line',
    'test_joined_vacuous_result_keeps_semantic_sufficiency_unclaimed',
    'test_legacy_cli_is_nonfatal_by_default_and_fails_when_required',
    'test_legacy_runner_ancestor_substitution_cannot_execute_replacement',
    'test_legacy_runner_rejects_an_executable_changed_during_the_run',
    'test_malformed_incomplete_zero_and_contradictory_reports_fail_closed',
    'test_missing_python_dependency_is_a_named_prerequisite_refusal',
    'test_missing_report_timeout_and_executable_failure_are_inconclusive_and_clean',
    'test_missing_submodule_object_materializes_as_a_bound_empty_directory',
    'test_mixed_assertion_and_infrastructure_errors_are_inconclusive',
    'test_p004_does_not_resolve_through_excluded_expression_shapes',
    'test_p004_preserves_breadth_first_order_across_local_expansion',
    'test_p008_resolution_does_not_erase_original_boundary_evidence',
    'test_parent_guard_rejects_an_executable_changed_during_the_run',
    'test_parent_runner_ancestor_substitution_cannot_execute_replacement',
    'test_raw_blobs_modes_and_exact_report_are_returned_before_cleanup',
    'test_reason_bearing_p008_pragma_suppresses_but_a_bare_one_does_not',
    'test_reassignments_and_nonassignment_writes_refuse_resolution',
    'test_safe_yaml_loaders_are_allowed_in_keyword_and_positional_forms',
    'test_show_marks_a_declaration_that_moved_under_an_unchanged_held_job',
    'test_show_marks_an_axis_that_moved_under_an_unchanged_held_job',
    'test_show_on_the_second_tree_prints_drift_against_a_later_pass',
    'test_sink_line_suppressions_and_fixed_diagnostics_survive_resolution',
    'test_stuck_parent_git_cleanup_shares_deadline_and_reaps_process',
    'test_the_declaration_comes_from_disk_and_never_from_the_caller',
    'test_the_written_hash_is_the_digest_the_ledger_itself_records',
    'test_timeout_start_failure_and_signal_are_distinct_inconclusive_results',
    'test_unsupported_targets_definitions_imports_and_declarations_refuse',
    'test_yaml_loader_keyword_takes_precedence_over_second_position',
    # Its module's SHA-256 is pinned by the held #1378 kickoff recovery record.
    'test_absent_base_adapter_keeps_controller_pin_skew_and_a_rewritten_base_writes_nothing',
    'test_adapter_neither_reviewed_nor_the_base_keeps_gate_receipt_drift',
    'test_base_pin_disagreeing_with_the_module_keeps_controller_pin_skew',
    'test_no_refused_module_or_no_marker_or_short_base_reads_no_git',
    'test_replace_ref_on_the_base_module_blob_never_reaches_admission',
    'test_run_under_an_older_controller_verifies_and_supersedes_here',
    'test_skew_list_excludes_admitted_modules_and_marks_named_ones',
})


def measure():
    """The runner's own manifest measurement, taken in a child process."""
    result = subprocess.run(
        [sys.executable, "-c", MEASURE], cwd=SUITE, capture_output=True,
        text=True, timeout=600, check=False,
    )
    if result.returncode != 0:
        raise AssertionError("manifest discovery failed:\n" + result.stderr[-4000:])
    return json.loads(result.stdout.splitlines()[-1])


def summary(measurement):
    used, cap = measurement["bytes"], measurement["cap"]
    return (f"{len(measurement['ids'])} test ids, {used:,} of {cap:,} manifest bytes, "
            f"{cap - used:,} remaining, reserve {RESERVE_BYTES:,}")


def findings(measurement):
    """Every reason the measured manifest fails its headroom or name bound."""
    problems = []
    if measurement["cap"] - measurement["bytes"] < RESERVE_BYTES:
        problems.append("headroom below reserve: " + summary(measurement))
    for identifier in measurement["ids"]:
        method = identifier.rsplit(".", 1)[-1]
        if len(method) > MAX_METHOD_CHARS and method not in GRANDFATHERED:
            problems.append(f"method name over {MAX_METHOD_CHARS} characters: {identifier}")
    return problems


class ManifestHeadroomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.measurement = measure()

    def test_manifest_keeps_its_reserve_under_the_cap(self):
        self.assertEqual([], [p for p in findings(self.measurement) if p.startswith("headroom")])

    def test_method_names_stay_within_the_bound(self):
        self.assertEqual([], [p for p in findings(self.measurement) if p.startswith("method")])

    def test_every_grandfathered_name_is_still_a_long_test(self):
        methods = {i.rsplit(".", 1)[-1] for i in self.measurement["ids"]}
        self.assertEqual(set(), GRANDFATHERED - methods)
        self.assertTrue(all(len(name) > MAX_METHOD_CHARS for name in GRANDFATHERED))


class FindingTests(unittest.TestCase):
    def test_fails_while_the_reserve_is_short_before_the_cap(self):
        cap = 1_048_576
        for used, failing in ((cap - RESERVE_BYTES, False), (cap - RESERVE_BYTES + 1, True),
                              (cap + 1, True)):
            with self.subTest(used=used):
                problems = findings({"cap": cap, "bytes": used, "ids": ["m.C.test_x"]})
                self.assertEqual(bool(problems), failing)
                if failing:
                    self.assertIn(f"{cap - used:,} remaining", problems[0])

    def test_refuses_a_long_name_unless_grandfathered(self):
        long_name = "test_" + "x" * (MAX_METHOD_CHARS - 4)
        listed = next(iter(GRANDFATHERED))
        problems = findings({"cap": 1 << 20, "bytes": 0,
                             "ids": [f"m.C.{long_name}", f"m.C.{listed}", "m.C.test_" + "y" * 55]})
        self.assertEqual([f"method name over {MAX_METHOD_CHARS} characters: m.C.{long_name}"],
                         problems)


if __name__ == "__main__":
    print(summary(measure()))
