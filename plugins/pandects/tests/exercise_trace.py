"""Reviewed Solidity test-function to catalogue-law exercise trace."""

VALUE = "conservation/value-conserved/v1"
BACKED = "conservation/reserves-backed-by-claims/v1"
PARTITIONED = "conservation/held-assets-partitioned/v1"
FALLS = "accrual/debt-falls-only-against-payment/v1"
AT_REST = "accrual/no-accrual-at-rest/v1"
PATH = "accrual/path-independent/v1"
SHRINKS = "claims/recorded-claim-never-shrinks/v1"
ORDERED = "claims/queue-order-preserved/v1"
COVERED = "claims/reserves-cover-payable/v1"
POOLED = "claims/pooled-claims-cover-open-batches/v1"

CORE = (VALUE, BACKED, PARTITIONED)
ONE_STATE = CORE + (ORDERED, COVERED, POOLED)
SUCCESSION = (FALLS, AT_REST, SHRINKS)

TEST_SURFACE_FILES = {
    "SoundInvariantTest": "test/SoundInvariant.t.sol",
    "CorpusTest": "test/Corpus.t.sol",
    "PairsTest": "test/Pairs.t.sol",
    "WildcatTest": "test/Wildcat.t.sol",
    "AdaptersTest": "test/Adapters.t.sol",
    "ExplainTest": "test/Explain.t.sol",
    "LawTest": "test/Law.t.sol",
    "ConservationCounterexamples": "test/counterexamples/Conservation.t.sol",
    "AccrualCounterexamples": "test/counterexamples/Accrual.t.sol",
    "ClaimsCounterexamples": "test/counterexamples/Claims.t.sol",
}

NON_JUDGING_SURFACES = {
    ("CorpusTest", "test_a_queue_law_over_a_target_with_no_queue_reverts"),
    ("CorpusTest", "test_every_law_carries_an_identifier_and_a_statement"),
    ("PairsTest", "test_every_pair_law_carries_an_identifier_and_a_statement"),
    ("WildcatTest", "test_delinquency_arrives_with_the_request"),
    ("AdaptersTest", "test_the_observer_offers_no_pair_law"),
    ("AdaptersTest", "test_a_driver_that_recorded_nothing_says_so"),
    ("LawTest", "test_a_law_holding_returns_true_with_its_detail"),
    ("LawTest", "test_a_law_violated_returns_false_rather_than_reverting"),
    ("LawTest", "test_an_unobservable_target_reverts_rather_than_passing"),
    ("LawTest", "test_a_law_carries_its_identifier_and_statement"),
}


def reviewed_surface_laws():
    """Return {(contract, function): {law_id: kind}} from the reviewed call trace."""
    found = {}

    def add(contract, functions, laws, kind):
        for function in functions:
            by_law = found.setdefault((contract, function), {})
            for identifier in laws:
                by_law[identifier] = kind

    invariant_surfaces = {
        "invariant_value_is_conserved": VALUE,
        "invariant_reserves_are_backed_by_claims": BACKED,
        "invariant_held_assets_stay_partitioned": PARTITIONED,
        "invariant_the_queue_stays_in_order": ORDERED,
        "invariant_reserves_cover_what_is_payable": COVERED,
        "invariant_pooled_claims_cover_open_batches": POOLED,
    }
    for function, identifier in invariant_surfaces.items():
        add("SoundInvariantTest", (function,), (identifier,), "invariant-fuzz")

    add(
        "CorpusTest",
        (
            "test_the_sound_reference_holds_every_law",
            "test_a_sound_system_at_rest_holds_every_law",
            "test_minted_claims_breaks_conservation_alone",
            "test_over_reserved_breaks_reserve_backing_alone",
            "test_over_promised_breaks_the_partition_alone",
            "test_queue_jumped_breaks_the_ordering_alone",
            "test_payable_beyond_reserves_breaks_the_cover_alone",
            "test_fee_from_queued_breaks_the_pooled_cover_alone",
            "test_debt_forgiven_holds_every_one_state_law",
            "test_accrues_at_rest_holds_every_one_state_law",
            "test_compounds_per_step_holds_every_one_state_law",
            "test_claim_haircut_holds_every_one_state_law",
            "test_every_law_returns_a_detail_whichever_way_it_decides",
        ),
        ONE_STATE,
        "deterministic",
    )
    add(
        "CorpusTest",
        (
            "test_no_law_reverts_at_the_arithmetic_limit",
            "test_a_sum_that_overflows_is_reported_as_a_violation",
        ),
        CORE,
        "deterministic",
    )
    add(
        "CorpusTest",
        ("test_a_queue_law_reports_its_own_overflow",),
        (POOLED,),
        "deterministic",
    )

    add(
        "PairsTest",
        (
            "test_no_transition_of_the_sound_reference_breaks_a_pair_law",
            "test_debt_forgiven_breaks_the_payment_law_alone",
            "test_accrues_at_rest_breaks_the_rest_law_alone",
            "test_claim_haircut_breaks_the_claim_law_alone",
            "test_the_one_state_specimens_break_no_pair_law",
            "test_the_other_pair_specimens_break_no_pair_law_in_passing",
        ),
        SUCCESSION,
        "deterministic-transition",
    )
    add(
        "PairsTest",
        (
            "test_the_sound_reference_is_path_independent",
            "test_compounding_per_step_breaks_path_independence_alone",
            "test_no_other_specimen_breaks_path_independence",
            "test_the_bound_holds_at_its_edge_and_not_beyond",
            "test_a_bound_built_for_the_wrong_run_is_wrong_in_both_directions",
            "test_a_pair_at_different_times_is_refused",
        ),
        (PATH,),
        "probe",
    )
    add(
        "PairsTest",
        ("test_a_pair_at_different_times_is_refused",),
        (AT_REST,),
        "deterministic-transition",
    )
    add(
        "PairsTest",
        ("test_an_unobserved_queue_is_refused",),
        (SHRINKS,),
        "deterministic-transition",
    )
    add(
        "PairsTest",
        ("test_the_laws_that_need_no_queue_judge_a_pair_without_one",),
        (FALLS, AT_REST),
        "deterministic-transition",
    )

    add(
        "WildcatTest",
        ("test_the_model_holds_every_one_state_law_it_claims",),
        ONE_STATE,
        "deterministic",
    )
    add(
        "WildcatTest",
        ("test_no_transition_of_the_model_breaks_a_succession_law",),
        SUCCESSION,
        "deterministic-transition",
    )
    add(
        "WildcatTest",
        (
            "test_a_batch_paid_pro_rata_does_not_break_the_ordering",
            "test_an_older_batch_is_settled_first",
        ),
        (ORDERED,),
        "deterministic",
    )
    add(
        "WildcatTest",
        (
            "test_an_open_batch_grows_and_the_claim_law_refuses_it",
            "test_a_closed_batch_satisfies_the_claim_law",
        ),
        (SHRINKS,),
        "deterministic-transition",
    )
    add(
        "WildcatTest",
        (
            "test_a_solvent_market_is_path_independent",
            "test_a_penalised_market_is_not_path_independent",
        ),
        (PATH,),
        "probe",
    )
    add(
        "WildcatTest",
        ("test_the_model_runs_through_the_shipped_adapter",),
        (VALUE, BACKED, PARTITIONED, ORDERED, COVERED) + SUCCESSION,
        "driver-adapter",
    )
    add(
        "WildcatTest",
        ("test_the_borrower_cannot_take_the_required_reserve",),
        (PARTITIONED,),
        "deterministic",
    )
    add(
        "WildcatTest",
        ("test_a_delinquent_market_can_take_no_fee_from_a_queued_batch",),
        (VALUE, BACKED, POOLED),
        "deterministic",
    )

    add(
        "AdaptersTest",
        (
            "test_the_observer_judges_a_target_it_does_not_front",
            "test_the_observer_carries_a_reason_for_every_verdict",
        ),
        ONE_STATE,
        "deterministic",
    )
    add(
        "AdaptersTest",
        ("test_a_queueless_target_still_gets_the_core_reasons",),
        CORE,
        "deterministic",
    )
    add(
        "AdaptersTest",
        ("test_the_driver_catches_a_claim_written_down",),
        SUCCESSION,
        "driver-adapter",
    )
    add(
        "AdaptersTest",
        ("test_both_prefixes_answer_for_the_new_law",),
        (VALUE, BACKED, POOLED),
        "deterministic",
    )
    add(
        "AdaptersTest",
        ("test_the_echidna_entry_points_answer",),
        (VALUE, ORDERED),
        "deterministic",
    )
    add(
        "AdaptersTest",
        (
            "test_the_probe_catches_compounding_and_clears_the_reference",
            "test_a_probe_built_for_the_wrong_run_passes_a_broken_system",
        ),
        (PATH,),
        "probe",
    )

    for function in (
        "test_explain_names_the_quantities_that_disagreed",
        "test_explain_carries_the_reason_a_pair_law_gave",
        "test_explain_carries_the_reason_the_new_law_gave",
    ):
        add("ExplainTest", (function,), ONE_STATE, "deterministic")
        add("ExplainTest", (function,), SUCCESSION, "deterministic-transition")
    add(
        "ExplainTest",
        ("test_explain_is_empty_for_the_pair_laws_before_the_first_call",),
        ONE_STATE,
        "deterministic",
    )

    counterexamples = (
        ("ConservationCounterexamples", "test_value_conserved_counterexample", VALUE, "deterministic"),
        (
            "ConservationCounterexamples",
            "test_reserves_backed_by_claims_counterexample",
            BACKED,
            "deterministic",
        ),
        (
            "ConservationCounterexamples",
            "test_held_assets_partitioned_counterexample",
            PARTITIONED,
            "deterministic",
        ),
        (
            "AccrualCounterexamples",
            "test_debt_falls_only_against_payment_counterexample",
            FALLS,
            "deterministic-transition",
        ),
        (
            "AccrualCounterexamples",
            "test_no_accrual_at_rest_counterexample",
            AT_REST,
            "deterministic-transition",
        ),
        (
            "AccrualCounterexamples",
            "test_accrual_path_independent_counterexample",
            PATH,
            "probe",
        ),
        (
            "ClaimsCounterexamples",
            "test_recorded_claim_never_shrinks_counterexample",
            SHRINKS,
            "deterministic-transition",
        ),
        (
            "ClaimsCounterexamples",
            "test_queue_order_preserved_counterexample",
            ORDERED,
            "deterministic",
        ),
        (
            "ClaimsCounterexamples",
            "test_reserves_cover_payable_counterexample",
            COVERED,
            "deterministic",
        ),
        (
            "ClaimsCounterexamples",
            "test_pooled_claims_cover_open_batches_counterexample",
            POOLED,
            "deterministic",
        ),
    )
    for contract, function, identifier, kind in counterexamples:
        add(contract, (function,), (identifier,), kind)

    return found
