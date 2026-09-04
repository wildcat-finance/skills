"""Contract checks for Fiat's host-directed workflow."""

import argparse
import hashlib
from pathlib import Path
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

try:
    from plugins.hexaemeron.tests.test_hexctl import (
        COMPLETE_STUDY,
        HexctlCase,
        PROTASIS as PROTASIS_CHECKER,
        SUITE,
        hexctl_module,
    )
except ModuleNotFoundError:
    from test_hexctl import (
        COMPLETE_STUDY,
        HexctlCase,
        PROTASIS as PROTASIS_CHECKER,
        SUITE,
        hexctl_module,
    )


ROOT = Path(__file__).resolve().parents[1]
FIAT = ROOT / "skills" / "fiat" / "SKILL.md"
PROTASIS = ROOT / "skills" / "protasis" / "SKILL.md"
FIAT_LEDGER = ROOT / "skills" / "fiat" / "EVOLUTION.md"
PROTASIS_LEDGER = ROOT / "skills" / "protasis" / "EVOLUTION.md"
ADR_006 = ROOT.parents[1] / "docs" / "decisions" / "ADR-006-skill-ledgers-are-not-semver.md"
MARKETPLACE = ROOT / "skills" / "fiat" / "references" / "wildcat-marketplace.md"
CONTRIBUTOR_CHECK = ROOT / "skills" / "fiat" / "scripts" / "check_wildcat_contributor.py"
PUSH_DISCIPLINE = ROOT / "skills" / "fiat" / "references" / "push-discipline.md"
PROSE_PASS = ROOT / "skills" / "fiat" / "references" / "prose-pass.md"
PLUGIN_CURRENCY = ROOT / "skills" / "fiat" / "references" / "plugin-currency.md"
AUDIT_LOOP = ROOT / "skills" / "fiat" / "references" / "audit-loop.md"
XRAY_REUSE = ROOT / "skills" / "fiat" / "references" / "xray-reuse.md"
KRONOS = ROOT / "skills" / "kronos" / "SKILL.md"
REPO_ROOT = ROOT.parents[1]
GUIDE = REPO_ROOT / "docs" / "how-to-help-shoggoth.md"
AGENTS = {
    name: (ROOT / "agents" / f"{name}.md").read_text(encoding="utf-8")
    for name in ("surveyor", "mason", "warden", "scribe")
}


def load_contributor_check():
    spec = importlib.util.spec_from_file_location("check_wildcat_contributor", CONTRIBUTOR_CHECK)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FiatSkillContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fiat = FIAT.read_text(encoding="utf-8")
        cls.protasis = PROTASIS.read_text(encoding="utf-8")
        cls.marketplace = MARKETPLACE.read_text(encoding="utf-8")
        cls.push_discipline = PUSH_DISCIPLINE.read_text(encoding="utf-8")
        cls.prose_pass = PROSE_PASS.read_text(encoding="utf-8")
        cls.audit_loop = AUDIT_LOOP.read_text(encoding="utf-8")
        cls.xray_reuse = XRAY_REUSE.read_text(encoding="utf-8")

    def test_marketplace_reference_is_linked(self):
        self.assertIn("[wildcat-marketplace.md](references/wildcat-marketplace.md)", self.fiat)
        self.assertTrue(MARKETPLACE.is_file())

    def test_xray_reuse_reference_is_bound_to_audit_and_warden_instructions(self):
        audit = " ".join(self.audit_loop.split())
        warden = " ".join(AGENTS["warden"].split())
        self.assertTrue(XRAY_REUSE.is_file())
        self.assertIn("[X-Ray source-reuse protocol](xray-reuse.md)", self.audit_loop)
        self.assertIn(
            "`<plugin-root>/skills/fiat/references/xray-reuse.md`", warden
        )
        for text in (audit, warden):
            self.assertIn("preparation layer only", text)
            self.assertIn("full logical scope", text)
            self.assertIn("fresh global synthesis", text)
            self.assertIn("all four final outputs", text)
            self.assertIn("Any cache uncertainty", text)
        self.assertIn("Do not add them to `hexctl` state", self.xray_reuse)

    def test_failed_identity_check_is_silent_and_non_persistent(self):
        self.assertIn("do not record a receipt", self.marketplace)
        self.assertRegex(self.marketplace, r"say nothing about the\s+check")
        self.assertIn("do not ask a follow-up question", self.marketplace)

    def test_supported_contributor_signals_and_acknowledgement_are_explicit(self):
        self.assertIn("`@wildcat.finance`", self.marketplace)
        self.assertIn("active membership in the `wildcat-finance`", self.marketplace)
        self.assertIn("exact normalised display name or login", self.marketplace)
        self.assertIn("Acknowledge that this is a Wildcat Labs run", self.marketplace)
        self.assertIn("List every other available plugin separately", self.marketplace)

    def test_authenticated_github_does_not_require_a_connector(self):
        self.assertIn("Do not require a connector", self.marketplace)
        self.assertIn("already-authenticated local GitHub account", self.marketplace)
        self.assertIn("under-permissioned\nconnector is not itself a failed check", self.marketplace)
        self.assertIn("a GitHub connector is optional", self.fiat)
        self.assertTrue(CONTRIBUTOR_CHECK.is_file())

    def test_private_discovery_does_not_fetch_or_disclose_references(self):
        self.assertIn("discover\n   private plugin descriptors", self.marketplace)
        self.assertIn("must not fetch its image\n   references", self.marketplace)
        self.assertIn("Do not name a\n   source repository", self.marketplace)
        self.assertIn("`.wildcat-labs/private-plugin.json`", self.marketplace)
        self.assertIn("`fiat-contributor-check`", self.marketplace)
        self.assertIn("fetch its declared plugin subtree", self.marketplace)
        self.assertIn("Delete staging afterwards", self.marketplace)
        self.assertIn("Never\n   clone or copy its source repository root", self.marketplace)

    def test_installation_waits_for_completed_study(self):
        completed = self.marketplace.index("The spec is complete only after `hexctl done study ...` succeeds")
        install = self.marketplace.index("Install each relevant missing plugin now")
        refresh = self.marketplace.index("Finish every selected install before any skill or plugin refresh")
        self.assertLess(completed, install)
        self.assertLess(install, refresh)
        self.assertIn("Never install a wider-marketplace plugin before the study receipt exists", self.fiat)

    def test_success_receipts_omit_identity_data(self):
        self.assertIn("Never record the account email, name, login, or matching evidence", self.marketplace)
        self.assertIn("hexctl record labs_marketplace", self.marketplace)

    def test_ai_origin_markers_are_required_for_delivery_artifacts(self):
        self.assertIn("`origin:ai`", self.push_discipline)
        self.assertIn("<!-- wildcat-origin: shoggoth -->", self.push_discipline)
        self.assertIn(
            "Co-authored-by: Shoggoth <shoggoth@wildcat.finance>",
            self.push_discipline,
        )
        self.assertIn("Wildcat-Origin: shoggoth", self.push_discipline)

    def test_runtime_hosts_are_not_governed_authors(self):
        flat = " ".join(self.push_discipline.split())
        self.assertIn("Authorship follows the contributing actor", flat)
        self.assertIn("Attribute Shoggoth's own agent-produced run work to `Shoggoth", flat)
        self.assertIn("Preserve a human contributor as Git author and signer", flat)
        self.assertIn("publish through their own GitHub account", flat)
        self.assertIn("Never ask for, copy, upload, configure or use the Shoggoth private signing key", flat)
        self.assertIn("Publication is a separate role", flat)
        self.assertIn("explicitly authorises a human publisher", flat)
        self.assertIn("Record both roles", flat)
        self.assertIn("is neither author, committer nor co-author", flat)
        self.assertIn("Without explicit authority", flat)
        self.assertIn("known host account as pull-request author", flat)

    def test_agent_contracts_own_the_exact_delegation_brief_fields(self):
        clauses = {
            "surveyor": "`topic`, `target_dir`, `base_ref`, `output_path`, and `design_output_path`",
            "mason": "`runbook_step`, `design_evidence`, `branch`, and `branch_from`",
            "warden": (
                "`step_branch`, `stacked_branch`, `security_suite`, `plugin_root`, "
                "`audit_log_path`, `round`, `audit_filter`, `risk_register`, "
                "`runbook_step`, and `design_evidence`"
            ),
            "scribe": "`files`, `pr_base`, `pr_draft_path`, and `plugin_root`",
        }
        for role, clause in clauses.items():
            with self.subTest(role=role):
                contract = " ".join(AGENTS[role].split())
                self.assertIn(f"one `brief` object with exactly {clause}", contract)

    def test_audit_fix_receipts_bind_the_closed_elenchus_verdict(self):
        fiat = " ".join(self.fiat.split())
        audit = " ".join(self.audit_loop.split())
        for text in (fiat, audit):
            self.assertIn("--elenchus-verdict", text)
            self.assertIn("--fixes-commit", text)
            for verdict in ("guarded", "unguarded", "passed", "inconclusive"):
                self.assertIn(verdict, text)
        self.assertIn("checked-and-recorded", audit)
        self.assertIn("does not attest the Elenchus report bytes", audit)
        self.assertIn("issue 453", audit)

    def test_future_audit_records_use_v2_while_v1_remains_readable(self):
        audit = " ".join(self.audit_loop.split())
        fiat = " ".join(self.fiat.split())
        warden = " ".join(AGENTS["warden"].split())
        for text in (audit, warden):
            self.assertIn("fiat-audit-round/v2", text)
            self.assertIn("fiat-audit-round/v1", text)
            self.assertIn("Covered", text)
            self.assertIn("Not checked", text)
            self.assertIn("Leads not pursued", text)
        self.assertIn("[audit-loop.md]", fiat)
        self.assertIn("do not write a new one", warden)
        self.assertIn("YYYY-MM-DDTHH:MM:SSZ", audit)
        self.assertIn("one raw record in the grammar above at EOF", audit)
        self.assertIn("Only the appended delta is decoded", audit)
        self.assertIn("canonical log path", audit)
        self.assertIn("entry SHA-256", audit)
        self.assertIn("packet's risk register", warden)

    def test_warden_uses_the_source_bound_step_and_returns_the_exact_verdict(self):
        contract = " ".join(AGENTS["warden"].split())
        self.assertIn("exact source-bound `runbook_step`", contract)
        self.assertIn("test command, report format, and report file", contract)
        self.assertIn("return its exact Elenchus verdict", contract)

    def test_audit_rounds_require_the_exact_sapheneia_declaration(self):
        fiat = " ".join(self.fiat.split())
        audit = " ".join(self.audit_loop.split())
        warden = " ".join(AGENTS["warden"].split())
        for text in (fiat, audit, warden):
            self.assertIn("--audit-filter sapheneia:sapheneia", text)
        self.assertIn("compact", audit.lower())
        self.assertIn("before appending", audit.lower())
        self.assertIn("checked operator declaration", audit)
        self.assertIn("not semantic proof", audit)

    def test_task_issue_comment_uses_the_ordered_publication_rule(self):
        prose = " ".join(self.prose_pass.split())
        push = " ".join(self.push_discipline.split())
        sequence = "Sapheneia -> Imprimatur -> Vulgate -> Imprimatur"
        for text in (prose, push):
            self.assertIn(sequence, text)
            for protected in (
                "issue URL",
                "pull request URL",
                "identifiers",
                "status",
                "unresolved work",
            ):
                self.assertIn(protected, text)
        self.assertIn("post those exact checked bytes verbatim", push)
        self.assertIn("read the remote comment back", push)
        self.assertIn("does not make the comment controller-attested", push)

    def test_step_checkpoint_is_unconditional_local_agent_work(self):
        section = self.push_discipline.split("## Step checkpoint", 1)[1].split(
            "\n## ", 1
        )[0]
        flat = " ".join(section.split())
        required = (
            "Every successful `done push` boundary",
            "mandatory controller work",
            "cannot be waived",
            "must not ask the user",
            "<origin>/.hexaemeron/checkpoints/<run-worktree-name>/",
            "A save failure blocks the next directive",
            "Do not upload the checkpoint",
            "direct agent-to-agent hand-off",
            "absolute archive path",
            "outer SHA-256",
            "controller-manifest SHA-256",
        )
        missing = [item for item in required if item not in flat]
        self.assertEqual([], missing)
        self.assertNotIn("HexaemeronCheckpoints Drive", section)
        self.assertNotIn("Anyone directing a run may waive", section)
        self.assertNotIn("Post a note on the run's task issue", section)

        fiat = " ".join(self.fiat.split())
        self.assertIn("fixed local checkpoint store", fiat)
        self.assertIn("mandatory controller work", fiat)
        self.assertIn("do not ask the user whether to save it", fiat)

    def test_provenance_is_verified_without_reclassifying_human_work(self):
        # Flattened: these assert what the instruction says, and a reflow of the
        # same sentence is not a change to it. Pinning the line breaks made an
        # edit that only rewrapped the paragraph look like a removed rule.
        flat = " ".join(self.push_discipline.split())
        self.assertIn("Read the pull request back from GitHub", flat)
        self.assertIn("same `gh pr create` command", flat)
        self.assertIn("pre-existing human commit", flat)
        self.assertIn("pre-existing human pull request", flat)

    def test_publish_phase_merges_and_closes_its_own_work(self):
        flat = " ".join(self.push_discipline.split())
        self.assertIn("permitted merge method", flat)
        self.assertIn("close that exact issue", flat)
        self.assertIn("Closes owner/repository#number", flat)
        self.assertIn("recognised closing reference to the exact issue", flat)
        self.assertIn(
            "hexctl done integrate --pr-url <url> --merge-commit <sha>",
            self.push_discipline,
        )
        self.assertNotIn("Never merge it", self.push_discipline)
        self.assertIn(
            "routine publish or closure action is not a handoff",
            " ".join(self.fiat.split()),
        )

    def test_known_task_issue_is_bound_during_init_and_names_the_run(self):
        flat = " ".join(self.fiat.split())
        push = " ".join(self.push_discipline.split())
        self.assertIn("init --task-issue <url>", flat)
        self.assertIn("before branch creation", flat)
        self.assertIn("fiat/<issue>-", flat)
        self.assertIn("fiat/<issue>-", push)
        self.assertNotIn("record its URL after init", flat)

    def test_steps_stack_and_only_the_run_branch_merges_into_the_base(self):
        flat = " ".join(self.push_discipline.split())
        fiat = " ".join(self.fiat.split())
        # A step's pull request targets the step below it, never the base.
        self.assertIn("gh pr create --base <pr_base> --head <branch>", self.push_discipline)
        self.assertIn("hexctl done push --pr-url <url> --head-commit <full-sha> --pr-base <ref>",
                      self.push_discipline)
        self.assertIn("never point one at the recorded base", flat)
        self.assertIn("only merge into the base in the whole run", flat)
        # The stack comes down in order, in its own phase.
        self.assertIn("hexctl done merge-step --step <n> --merge-commit <sha>",
                      self.push_discipline)
        self.assertIn("Merges belong to `integrate`", self.push_discipline)
        # And the loop itself says so.
        self.assertIn("Never target the base or the repository default branch with a step pull",
                      self.fiat)
        self.assertIn("Never merge into the base more than once in a run", self.fiat)
        self.assertIn("nothing merges while the steps run", fiat.lower())

    def test_receipted_study_amendment_command_and_phase_boundary_are_explicit(self):
        flat = " ".join(self.fiat.split())
        self.assertIn("hexctl amend study --artifact <candidate>", self.fiat)
        self.assertIn("only while build steps are active", flat)
        self.assertIn("currently receipted study bytes as its exact prefix", flat)

    def test_amendment_receipt_names_digests_verdicts_and_evidence_boundary(self):
        flat = " ".join(self.fiat.split())
        self.assertIn("prior, new, and amendment digests", flat)
        self.assertIn("bounded step verdicts in state and the ledger", flat)
        self.assertIn("does not establish that the amendment is true", flat)

    def test_broken_current_step_has_a_durable_block_and_recovery(self):
        flat = " ".join(self.fiat.split())
        self.assertIn("`next` returns a durable blocked directive", flat)
        self.assertIn("step receipts refuse to advance", flat)
        self.assertIn("separately specified runbook-repair transition", flat)

    def test_blocked_is_a_terminal_loop_outcome_with_no_implied_receipt(self):
        loop = self.fiat.split("## The loop", 1)[1].split("## Phase notes", 1)[0]
        self.assertIn("`blocked`", loop)
        self.assertRegex(loop, r"\| `blocked` \|.*\| -- \|")

    def test_amendment_mutation_has_its_own_promise_authorisation(self):
        promise = self.fiat.split("### fiat-study-amendment", 1)[1]
        promise = promise.split("### ", 1)[0]
        self.assertIn("- Consequence: 2", promise)
        self.assertIn("- Authorises:", promise)
        self.assertIn("re-pinning", promise)
        self.assertIn("durable blocked directive", promise)

    def test_receipted_runbook_amendment_and_effective_source_are_explicit(self):
        flat = " ".join(self.fiat.split())
        self.assertIn("hexctl amend runbook --artifact <candidate>", self.fiat)
        self.assertIn("Complete replacement Exit: <full value>", self.fiat)
        self.assertIn("one numbered and titled baseline block", flat)
        self.assertIn("exact bytes and digests", flat)
        self.assertIn("current study digest", flat)
        self.assertIn("If both markers exist, recovery refuses", flat)

    def test_runbook_amendment_has_a_narrow_consequence_two_promise(self):
        promise = self.fiat.split("### fiat-runbook-amendment", 1)[1]
        promise = promise.split("### ", 1)[0]
        self.assertIn("- Consequence: 2", promise)
        self.assertIn("- Authorises:", promise)
        self.assertIn("amend:runbook", promise)
        self.assertIn("does not establish that the free-form replacement", promise)
        self.assertIn("pending-subject collision", promise)

    def test_protasis_owns_the_complete_replacement_syntax_and_p005_boundary(self):
        flat = " ".join(self.protasis.split())
        self.assertIn("Complete replacement Exit:", self.protasis)
        self.assertIn("P005", self.protasis)
        self.assertIn("ends the last baseline step before a real amendment heading", flat)
        self.assertIn("not that the new criterion is correct", flat)

    def test_protasis_verified_audit_read_view_preserves_source_evidence(self):
        passages = {
            "study item 2": self.protasis.split("2. **Prior art.**", 1)[1].split(
                "3. **Constraints and non-goals.**", 1
            )[0],
            "pre-receipt checklist": self.protasis.split(
                "## Before the runbook is receipted", 1
            )[1].split("## Hand back", 1)[0],
        }
        required = {
            "source authority": "Every discovered audit source remains authoritative.",
            "legacy mapping": (
                "`**/audit/AUDIT.md` maps to its sibling `AUDIT_SYNOPSIS.md`."
            ),
            "per-run mapping": (
                "A direct child `audit/rounds/<run>.md` maps to "
                "`audit/rounds/<run>.synopsis.md`."
            ),
            "currency command": (
                "`python3 plugins/hexaemeron/skills/fiat/scripts/"
                "audit_synopsis.py --check <target-root>`"
            ),
            "whole-set gate": "whole-set currency check exits zero",
            "unavailable view": "Missing, stale, unsupported, or unavailable view",
            "source fallback": "read the authoritative source directly",
            "fallback evidence": "record its source path and the reason",
            "finding identity": "every finding id and status",
            "covered evidence": "`Covered`",
            "unchecked evidence": "`Not checked`",
            "elenchus evidence": "`Elenchus verdict`",
            "unfollowed leads": "`Leads not pursued`",
            "legacy unknown": "`[missing legacy field: ...]` remains unknown",
            "source inventory": "name every in-scope source",
            "actual read mode": "which synopsis or source was actually read",
            "read-mode evidence": "evidence for that choice",
            "truthful source claim": (
                "Do not claim the source was read when only its synopsis was read."
            ),
        }
        for passage_name, passage in passages.items():
            flat = " ".join(passage.split())
            for rule, clause in required.items():
                with self.subTest(passage=passage_name, rule=rule):
                    self.assertIn(clause, flat)

    def test_protasis_owns_the_closed_version_relation_and_p006_boundary(self):
        flat = " ".join(self.protasis.split())
        self.assertIn("```version-relations", self.protasis)
        self.assertIn("next-generation-after-integration-base", self.protasis)
        self.assertIn("P006", self.protasis)
        self.assertIn("Prose, examples, commands and amendments all count", flat)
        self.assertIn("It does not open the ledger", flat)
        self.assertIn("allocate a version", flat)

    def test_fiat_owns_the_exact_anchor_without_calling_it_a_reservation(self):
        flat = " ".join(self.fiat.split())
        self.assertIn("`fiat-version-relations/v1` anchor", flat)
        self.assertIn("bounded regular Git blob", flat)
        self.assertIn("The generation-plus-one value", flat)
        self.assertIn("It is not a reservation", flat)
        self.assertIn("an explicit null resolution", flat)
        self.assertIn("worker directive shapes stay unchanged", flat)
        self.assertIn("no Git version evidence is read", flat)

    def test_version_resolution_has_a_narrow_consequence_two_promise(self):
        promise = self.fiat.split("### fiat-version-resolution", 1)[1]
        promise = promise.split("### ", 1)[0]
        self.assertIn("- Consequence: 2", promise)
        self.assertIn("- Authorises:", promise)
        self.assertIn("newest still-current receipt", promise)
        self.assertIn("does not reserve a label", promise)
        self.assertIn("subject-labelled pending record", promise)
        self.assertIn("ninth resolution", promise)

    def test_resolution_transition_and_final_replay_are_explicit(self):
        flat = " ".join(self.fiat.split())
        push = " ".join(self.push_discipline.split())
        self.assertIn("`resolve-versions`", self.fiat)
        self.assertIn("`done resolve-versions`", self.fiat)
        for text in (flat, push):
            self.assertIn("subject-labelled pending", text)
            self.assertIn("eight", text)
        self.assertIn("[base, candidate]", flat)
        self.assertIn("[checked base, checked candidate]", push)
        self.assertIn("All targets pass or none are recorded", push)
        self.assertIn("performs none of these version reads", push)

    def test_decision_assignment_contract_is_read_only_and_source_bound(self):
        fiat = " ".join(self.fiat.split())
        push = " ".join(self.push_discipline.split())
        for text in (fiat, push):
            self.assertIn("fiat-decision-assignments/v1", text)
            self.assertIn("fiat-decision-assignment-composition/v1", text)
            self.assertIn("verify-decision-assignments", text)
            self.assertIn("read-only", text)
            self.assertIn("ADR-Assignment-Base: <base>", text)
            self.assertIn("ADR-Assignment: adr/<slug>=ADR-NNN", text)
            self.assertIn("sibling", text)
        self.assertIn("--decision-assignments", push)
        self.assertIn("fiat_decision_assignments_v1", push)
        self.assertIn("must not remain in active ancestry", push)

    def test_decision_assignment_promise_keeps_hypomnema_authority(self):
        promise = self.fiat.split(
            "### fiat-decision-assignment-composition", 1
        )[1].split("### ", 1)[0]
        self.assertIn("- Consequence: 2", promise)
        self.assertIn("- Authorises:", promise)
        self.assertIn("Hypomnema alone owns allocation policy", promise)
        self.assertIn("does not reserve a number", promise)
        self.assertIn("does not", promise)
        self.assertIn("mutate a draft", promise)
        self.assertIn("superseded assignment retained in active ancestry", promise)

    def test_issue_556_generation_records_retain_the_declared_relation(self):
        ledgers = {
            "fiat-v5.37.1": FIAT_LEDGER.read_text(encoding="utf-8"),
            "protasis-v4.9.0": PROTASIS_LEDGER.read_text(encoding="utf-8"),
        }
        for version, ledger in ledgers.items():
            with self.subTest(version=version):
                latest = next(
                    line for line in ledger.splitlines()
                    if line.startswith(f"| `{version}` |")
                )
                self.assertIn(f"| `{version}` | generation |", latest)
                self.assertIn("skills#556", latest)
                self.assertIn("ADR-006", latest)
                self.assertIn("next-generation-after-integration-base", latest)

    def test_issue_556_addendum_separates_relation_from_resolution(self):
        record = ADR_006.read_text(encoding="utf-8")
        addendum = record.split("## Issue 556 addendum", 1)[1]
        self.assertIn("Accepted, 2026-08-28", addendum)
        self.assertIn("skills#556", addendum)
        self.assertIn("next-generation-after-integration-base", addendum)
        self.assertIn("does not reserve a label", addendum)
        self.assertIn("exact integration base", addendum)
        self.assertIn("signed two-parent", addendum)
        self.assertIn("fiat-integration-revalidation/v1", addendum)
        self.assertIn("self-hosted", addendum)

    def test_observation_binding_is_optional_and_non_authorising(self):
        flat = " ".join(self.fiat.split())
        self.assertIn("Observation is never a phase gate", self.fiat)
        self.assertIn("hexctl verify --observations", self.fiat)
        self.assertIn("appended bytes remain unbound", flat)
        promise = self.fiat.split("### fiat-run-observation-binding", 1)[1]
        promise = promise.split("### ", 1)[0]
        self.assertIn("- Consequence: 2", promise)
        self.assertIn("does not establish that events are true or complete", promise)


class StackBringDownTests(unittest.TestCase):
    """The order the stack comes down in, and why deleting early is fatal.

    A run merged step 1 with --delete-branch. GitHub did not retarget the pull
    request stacked on it; it closed it, and a closed pull request whose base ref
    is gone can be neither reopened nor retargeted. The instructions' own
    recovery path was unreachable from the state the instructions produced.
    """

    @classmethod
    def setUpClass(cls):
        cls.push_discipline = PUSH_DISCIPLINE.read_text(encoding="utf-8")
        cls.flat = " ".join(cls.push_discipline.split())

    def test_the_next_pull_request_is_retargeted_before_the_merge(self):
        self.assertIn("gh pr edit <next pr> --base <run branch>", self.push_discipline)
        self.assertIn("before this", self.flat)
        # Retargeting must come first in the numbered procedure.
        bring_down = self.push_discipline.split("## Bringing the stack down")[1]
        retarget = bring_down.index("gh pr edit <next pr>")
        merge = bring_down.index("Merge that step's pull request")
        self.assertLess(retarget, merge)

    def test_step_merges_do_not_delete_branches(self):
        self.assertIn("Do not pass", self.flat)
        self.assertIn("--delete-branch", self.push_discipline)
        self.assertIn("do not delete the branch here", self.flat)

    def test_the_closed_pull_request_failure_mode_is_written_down(self):
        self.assertIn("GitHub closes", self.flat)
        self.assertIn("neither reopened nor retargeted", self.flat)

    def test_cleanup_belongs_to_integrate(self):
        integration = self.push_discipline.split("## The integration pull request")[1]
        self.assertIn("delete the run branch and every step branch", " ".join(integration.split()))
        self.assertIn("one place branch cleanup happens", " ".join(integration.split()))

    def test_base_drift_preserves_product_evidence(self):
        integration = self.push_discipline.split("## The integration pull request")[1]
        flat = " ".join(integration.split())
        self.assertIn("fiat-integration-revalidation/v1", integration)
        self.assertIn("--revalidation .hexaemeron/integration-revalidation.json", flat)
        self.assertIn("implementation and audit remain evidence", flat)
        self.assertIn("Base advancement alone never authorises a carryover", flat)
        self.assertIn("config.git.base", integration)
        self.assertIn("starting commit", flat)


class OriginLabelTests(unittest.TestCase):
    """The provenance label, and not trusting a query that failed.

    A run reported the label missing and created one that already existed: the
    check ran moments after a rate-limit error, so an empty result read as an
    empty repository. A gh query shaped `list | grep -q` cannot tell absence from
    failure.
    """

    @classmethod
    def setUpClass(cls):
        cls.flat = " ".join(PUSH_DISCIPLINE.read_text(encoding="utf-8").split())

    def test_the_label_is_created_when_absent(self):
        self.assertIn("gh label create origin:ai", self.flat)

    def test_the_label_is_read_back_rather_than_assumed(self):
        self.assertIn("Read it back", self.flat)
        self.assertIn("rather than trusting that `gh pr create` applied it", self.flat)

    def test_a_failed_query_is_not_an_answer(self):
        self.assertIn("A failed query is not an answer", self.flat)
        self.assertIn("Check the exit status separately from the match", self.flat)


class BodyReadBackTests(unittest.TestCase):
    """A host can rewrite the pull-request body after `gh pr create` returns.

    Pull request #615 was drafted without a byline and came back from GitHub
    carrying the host's session-link footer; a body edit removed it and the
    removal held. Nothing in the loop said to read the body back, and a Fiat
    receipt over that body would have refused it with no word about where the
    line came from (skills#617). Flattened, like the label pins above, so a
    reflow of the same sentence is not a removed rule.
    """

    @classmethod
    def setUpClass(cls):
        cls.flat = " ".join(PUSH_DISCIPLINE.read_text(encoding="utf-8").split())
        cls.fiat = " ".join(FIAT.read_text(encoding="utf-8").split())

    def test_the_body_is_read_back_over_rest_after_creation(self):
        self.assertIn("## Read the body back", self.flat)
        self.assertIn("The body is the second thing to read back, after the label.", self.flat)
        self.assertIn("after `gh pr create` returns", self.flat)
        self.assertIn("gh api repos/<owner>/<repo>/pulls/<n> --jq .body", self.flat)
        self.assertIn("rather than `gh pr view --json body`", self.flat)

    def test_the_section_sits_between_the_label_read_back_and_the_url_check(self):
        self.assertLess(
            self.flat.index("A failed query is not an answer"),
            self.flat.index("## Read the body back"),
        )
        self.assertLess(
            self.flat.index("## Read the body back"),
            self.flat.index("Verify the pull request URL after creation"),
        )

    def test_a_failed_read_is_not_a_clean_body(self):
        self.assertIn("A failed read is not a clean body", self.flat)

    def test_the_recovery_edits_the_stashed_body_and_reads_it_again(self):
        self.assertIn("gh pr edit <url> --body-file .hexaemeron/steps/<n>/pr.md", self.flat)
        self.assertIn("read it back again", self.flat)
        self.assertIn("`done push`, `done merge-step` and `done integrate`", self.flat)

    def test_the_repository_rule_wins_over_the_host_trailer_instruction(self):
        self.assertIn("cannot both be satisfied, and the repository rule wins", self.flat)

    def test_the_settings_file_is_named_and_is_not_evidence(self):
        self.assertIn("`.claude/settings.json`", self.flat)
        self.assertIn("a setting is not evidence", self.flat)

    def test_the_listed_footer_is_named_by_where_it_was_seen(self):
        # The study records the #615 footer as having the documented session
        # link's shape and declines to claim it is that link (skills#617 audit
        # S2-R1-02); the list says the same rather than more.
        self.assertIn("the footer that reached pull request #615", self.flat)
        self.assertIn("it has the shape of the session link", self.flat)

    def test_the_skill_push_note_points_at_the_section(self):
        self.assertIn(
            "`Read the body back` section of [push-discipline.md](references/push-discipline.md)",
            self.fiat,
        )


class HostGuidanceTests(unittest.TestCase):
    """The contributor guide promises no refusal the byline expression does not make.

    The guide's attribution paragraph once said a `Generated with` or
    `Generated by` line "naming Claude Code, Codex or another host" is refused,
    in the paragraph that sends Cursor, Windsurf and GitHub Copilot contributors
    to remove such lines by hand; `HOST_BYLINE_RE` names six hosts and passes a
    line naming any other (skills#617 audit S2-R1-01). The guard reads the hosts
    the sentence names and drives each through the expression the controller
    applies, so the list can widen only together with the expression.
    """

    HOST_LIST_RE = re.compile(r"line naming (.+?), refused as a runtime-host byline")

    @classmethod
    def setUpClass(cls):
        cls.flat = " ".join(GUIDE.read_text(encoding="utf-8").split())
        cls.byline = hexctl_module().HOST_BYLINE_RE

    def test_every_host_the_guide_names_is_one_the_expression_reads(self):
        match = self.HOST_LIST_RE.search(self.flat)
        self.assertIsNotNone(match, "the guide no longer lists the hosts the byline gate reads")
        hosts = re.split(r", | or ", match.group(1))
        self.assertGreaterEqual(len(hosts), 2)
        for host in hosts:
            for verb in ("Generated with", "Generated by"):
                with self.subTest(host=host, verb=verb):
                    self.assertIsNotNone(self.byline.search(f"{verb} {host}"))

    def test_the_guide_promises_no_refusal_for_an_unnamed_host(self):
        self.assertNotIn("or another host, refused", self.flat)
        self.assertIn(
            "a line naming any other host passes the gate and still has to go",
            self.flat,
        )


class BaseSyncTests(unittest.TestCase):
    """A run inherits every mistake in the ref it was cut from.

    A session began with the local base a hundred and forty-six commits behind
    the remote. Nothing in the loop said to sync it, so the study would have
    cited a starting ref that was already history.
    """

    @classmethod
    def setUpClass(cls):
        cls.fiat = FIAT.read_text(encoding="utf-8")
        cls.flat = " ".join(cls.fiat.split())

    def test_the_base_is_synced_before_any_branch_is_cut(self):
        self.assertIn("Sync the base first", self.fiat)
        self.assertIn("git merge --ff-only origin/<base>", self.fiat)
        self.assertIn("bring the base up to date before anything is cut from it", self.flat)

    def test_the_sync_is_fast_forward_only_and_refuses_a_dirty_tree(self):
        self.assertIn("Fast-forward only", self.fiat)
        self.assertIn("If the tree is dirty, stop", self.flat)

    def test_the_starting_sha_reaches_the_study(self):
        self.assertIn("state the starting SHA in the study's constraints", self.flat)


class PluginCurrencyTests(unittest.TestCase):
    """Directing the update, rather than noting the version and carrying on.

    A run drove a controller a whole evolution behind the repository it was
    editing and recorded its lint results as prose, because the installed
    audit-round did not accept flags its own ledger documented.
    """

    @classmethod
    def setUpClass(cls):
        cls.doc = PLUGIN_CURRENCY.read_text(encoding="utf-8")
        cls.flat = " ".join(cls.doc.split())
        cls.fiat = " ".join(FIAT.read_text(encoding="utf-8").split())
        cls.market = " ".join(
            MARKETPLACE.read_text(encoding="utf-8").split()
        )

    def test_preflight_directs_the_update_rather_than_noting_it(self):
        self.assertIn("plugin-currency.md", self.fiat)
        self.assertIn("Do not run the loop under a controller you have noticed is behind",
                      self.fiat)

    def test_the_host_mechanism_lives_here_only(self):
        # Both callers need it; two copies of a host list drift.
        self.assertIn("/reload-plugins", self.doc)
        self.assertIn("plugin-currency.md", self.market)
        self.assertNotIn("/reload-plugins", self.market)

    def test_the_install_route_is_established_not_assumed(self):
        self.assertIn("Do not assume", self.flat)
        self.assertIn("git-backed marketplace", self.flat)
        self.assertIn("managed marketplace", self.flat)
        self.assertIn("the agent cannot do it", self.flat)

    def test_the_two_repositories_and_the_mirror_delay_are_stated(self):
        self.assertIn("wildcat-finance/skills-marketplace", self.doc)
        # Measured, not declared. The cron requests five minutes; the
        # scheduler delivers closer to twenty, so the doc must send a
        # reader to the two heads and the manual trigger instead.
        self.assertIn("read the two heads rather than trusting an interval", self.flat)
        self.assertIn("gh workflow run sync-skills-marketplace.yml", self.doc)
        self.assertIn("chain rather than a step", self.flat)

    def test_an_unfixable_gap_becomes_a_receipt(self):
        self.assertIn("hexctl record controller_version", self.doc)
        self.assertIn("say so out loud", self.flat)

    def test_hand_editing_a_plugin_cache_is_refused(self):
        self.assertIn("Do not hand-edit a plugin cache", self.flat)

    def test_the_self_hosting_case_is_excluded(self):
        self.assertIn("is not a problem", self.flat)
        self.assertIn("skips that by identity", self.flat)

    def test_a_run_cannot_enforce_what_it_just_shipped(self):
        self.assertIn("cannot take effect for the very run that made it", self.flat)


class FrontierGateContractTests(unittest.TestCase):
    """The ledger update is owed mechanically, and both callers say so.

    The maturity gate stated it in prose, and this repository has already had to
    reconstruct two broken evolutions. Kronos ranks by held job, so an unchanged
    ledger read as a closed one would make it rank the same job forever.
    """

    @classmethod
    def setUpClass(cls):
        cls.fiat = " ".join(FIAT.read_text(encoding="utf-8").split())
        cls.fiat_raw = FIAT.read_text(encoding="utf-8")
        cls.kronos = " ".join(KRONOS.read_text(encoding="utf-8").split())

    def test_the_maturity_gate_names_the_flag(self):
        self.assertIn("--frontier plugins/<plugin>/skills/<skill>/EVOLUTION.md",
                      self.fiat_raw)
        self.assertIn("Make step 4 mechanical", self.fiat_raw)

    def test_what_the_gate_checks_is_written_down(self):
        self.assertIn("exactly one new row valid under the versioning contract",
                      self.fiat)
        self.assertIn("Each refusal names which of those failed", self.fiat)

    def test_ordinary_delivery_does_not_owe_a_row(self):
        self.assertIn("Leave it off for ordinary delivery", self.fiat)

    def test_a_recorded_stop_is_not_a_silent_finish(self):
        self.assertIn("refuses a silent finish, not a recorded stop", self.fiat)

    def test_kronos_requires_it_mechanically(self):
        self.assertIn("hexctl init --frontier", self.kronos)
        self.assertIn("cannot afford to take an unchanged ledger for a closed one",
                      self.kronos)


class ContributorCheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_contributor_check()

    @staticmethod
    def completed(returncode=0, payload=None):
        stdout = "" if payload is None else json.dumps(payload)
        return subprocess.CompletedProcess(["gh"], returncode, stdout=stdout, stderr="")

    def test_active_org_membership_passes(self):
        responses = [
            self.completed(),
            self.completed(payload={"login": "member", "email": None}),
            self.completed(payload={"state": "active"}),
        ]
        with mock.patch.object(self.module, "_gh", side_effect=responses):
            self.assertTrue(self.module.authenticated_github_user_is_contributor())

    def test_verified_wildcat_email_passes_when_membership_is_unavailable(self):
        responses = [
            self.completed(),
            self.completed(payload={"login": "member", "email": None}),
            self.completed(returncode=1),
            self.completed(payload=[{"email": "member@wildcat.finance", "verified": True}]),
        ]
        with mock.patch.object(self.module, "_gh", side_effect=responses):
            self.assertTrue(self.module.authenticated_github_user_is_contributor())

    def test_missing_auth_fails_without_output(self):
        with mock.patch.object(self.module, "_gh", return_value=self.completed(returncode=1)):
            with mock.patch("sys.stdout") as stdout, mock.patch("sys.stderr") as stderr:
                self.assertEqual(self.module.main(), 1)
                stdout.write.assert_not_called()
                stderr.write.assert_not_called()


if __name__ == "__main__":
    unittest.main()


class PhaseSkillInventoryTests(unittest.TestCase):
    """The README counts how many phase skills ship an executable check.

    It said four while five did. A prose count goes stale the next time one is added, and
    this run added one, so the count is derived here rather than trusted.
    """

    PHASES = ("protasis", "elenchus", "phylax", "ephoros", "metron", "hypomnema")
    WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six"}

    def test_the_readme_counts_the_checks_that_exist(self):
        root = Path(__file__).resolve().parents[1]
        with_script = [
            name for name in self.PHASES
            if (root / "skills" / name / "scripts" / f"{name}.py").is_file()
        ]
        readme = (root / "README.md").read_text(encoding="utf-8")
        expected = (
            f"six phase disciplines; all "
            f"{self.WORDS[len(with_script)]} ship an executable check:"
        )
        self.assertIn(expected, readme,
                      f"{len(with_script)} phase skills ship a check: {with_script}")

    def test_every_named_phase_skill_exists(self):
        root = Path(__file__).resolve().parents[1]
        for name in self.PHASES:
            with self.subTest(skill=name):
                self.assertTrue((root / "skills" / name / "SKILL.md").is_file())


HEXCTL = ROOT / "skills" / "fiat" / "scripts" / "hexctl.py"


class RunWorktreeContractTests(unittest.TestCase):
    """The written contract has to match what `init` now builds.

    The advice this replaces was contract text too, and it was wrong in the
    ordinary case for two years of runs. A contract nothing checks is how that
    happens.
    """

    @classmethod
    def setUpClass(cls):
        cls.fiat = FIAT.read_text(encoding="utf-8")
        cls.push_discipline = PUSH_DISCIPLINE.read_text(encoding="utf-8")
        cls.hexctl = HEXCTL.read_text(encoding="utf-8")

    def test_the_contract_says_the_run_works_in_its_own_worktree(self):
        self.assertIn("## The run's worktree", self.fiat)
        self.assertIn("`init` creates a dedicated git worktree", self.fiat)

    def test_the_contract_says_where_the_worktree_lives(self):
        self.assertIn("tmp/fiat/", self.fiat)

    def test_the_contract_says_dir_points_at_the_worktree(self):
        collapsed = " ".join(self.fiat.split())
        self.assertIn("Point `--dir` at the target repository once, at `init`, and at "
                      "the worktree it prints for everything after that.", collapsed)

    def test_the_contract_states_the_cleanup_rule(self):
        collapsed = " ".join(self.fiat.split())
        self.assertIn("Nothing is ever forced.", collapsed)
        self.assertIn("removes the tree when git can remove it without force", collapsed)
        self.assertIn("A tree holding work is kept and named instead", collapsed)

    def test_terminal_cleanup_follows_status_and_verification(self):
        final_report = self.fiat.split("## Final report", 1)[1].split(
            "## Promise Machine contract", 1
        )[0]
        status_at = final_report.index("`hexctl status`")
        verify_at = final_report.index("`hexctl verify`")
        reset_at = final_report.index("`hexctl reset`")
        self.assertLess(status_at, verify_at)
        self.assertLess(verify_at, reset_at)
        self.assertIn("local archive path", final_report)
        self.assertIn("no `.hexaemeron/` byte", final_report)
        self.assertIn("### fiat-local-retirement", self.fiat)

    def test_the_contract_states_the_fail_closed_fallback(self):
        self.assertIn("There is no in-place fallback.", self.fiat)

    def test_the_unusable_advice_is_gone_everywhere(self):
        """`git worktree add ../<name> main` fails whenever the base is
        already checked out, which is the ordinary case."""
        for name, text in (("SKILL.md", self.fiat), ("hexctl.py", self.hexctl)):
            with self.subTest(file=name):
                self.assertNotIn("git worktree add ../", text)

    def test_the_lock_refusal_names_something_that_works(self):
        self.assertIn("hexctl --dir <checkout> init --topic ", self.hexctl)

    def test_the_run_branch_is_no_longer_cut_by_hand(self):
        self.assertNotIn("git checkout -b <run branch> <base>", self.fiat)
        self.assertNotIn("git checkout -b <run branch> <base>", self.push_discipline)
        self.assertIn("`init` cuts it", self.fiat)
        self.assertIn("`init` cuts it", self.push_discipline)


class TestRunbookAmendments(HexctlCase):
    def test_complete_replacement_exit_reaches_mason_and_warden_exactly(self):
        _, original = self.to_runbook_amendable_steps()
        suffix = self.runbook_amendment()
        candidate = self.write("candidate.md", original + suffix)

        result = self.run_ctl("amend", "runbook", "--artifact", candidate)
        self.assertIn("runbook amended", result.stdout)
        state = self.state()
        receipt = state["receipts"]["runbook"]
        amendment = receipt["amendments"][0]
        self.assertEqual(amendment["study_sha256"], state["receipts"]["study"]["sha256"])
        self.assertEqual(amendment["replacement_fields"], ["Exit"])
        self.assertEqual(amendment["steps_touched"], [1, 2])
        self.assertEqual(amendment["amendment_sha256"], hashlib.sha256(suffix.encode()).hexdigest())
        with open(
            os.path.join(self.target, ".hexaemeron", "ledger.jsonl"),
            encoding="utf-8",
        ) as handle:
            events = [json.loads(line)["event"] for line in handle if line.strip()]
        self.assertEqual(events[-1], "amend:runbook")

        mason = self.next_json()
        source = mason["brief"]["runbook_step"]
        self.assertIn("fiat-v1.0.0", source["baseline_markdown"])
        self.assertEqual(source["amendments"][0]["markdown"], suffix)
        self.assertIn("fiat-v2.0.0", source["markdown"])
        self.run_ctl(
            "done", "implement", "--branch", self.step_branch(1), "--commit", "abc"
        )
        self.run_ctl("record", "security_suite", SUITE)
        warden = self.next_json()
        self.assertEqual(
            warden["brief"]["runbook_step"], mason["brief"]["runbook_step"]
        )

    def test_exact_unicode_and_whitespace_bytes_are_not_normalised_in_packets(self):
        _, original = self.to_runbook_amendable_steps()
        suffix = self.runbook_amendment(
            what=(
                "Complete replacement Exit: Run `fiat-v2.0.0` for café.\n"
                "  Preserve  these  spaces."
            )
        )
        candidate = self.write("candidate.md", original + suffix)
        self.run_ctl("amend", "runbook", "--artifact", candidate)
        carried = self.next_json()["brief"]["runbook_step"]["amendments"][0]
        self.assertEqual(carried["markdown"].encode("utf-8"), suffix.encode("utf-8"))
        self.assertEqual(carried["sha256"], hashlib.sha256(suffix.encode()).hexdigest())

    def test_current_study_bound_complete_replacement_repairs_broken_study(self):
        study_text, runbook_text = self.to_runbook_amendable_steps()
        broken_study = self.write(
            "broken-study.md",
            study_text
            + self.amendment(
                "Step 1: entry broken; exit holds. "
                "Step 2: entry holds; exit holds."
            ),
        )
        self.run_ctl("amend", "study", "--artifact", broken_study)
        self.assertEqual(self.next_json()["do"], "blocked")

        repair = self.write(
            "repair-runbook.md", runbook_text + self.runbook_amendment()
        )
        self.run_ctl("amend", "runbook", "--artifact", repair)
        self.assertEqual(self.next_json()["do"], "implement")

        amended_study = self.state()["receipts"]["study"]["artifact"]
        if not os.path.isabs(amended_study):
            amended_study = os.path.join(self.target, amended_study)
        with open(amended_study, encoding="utf-8") as handle:
            current_study = handle.read()
        later = self.write(
            "later-study.md",
            current_study
            + self.amendment(
                "Step 1: entry holds; exit broken. "
                "Step 2: entry holds; exit holds.",
                date="2026-08-25",
                what="A later study belief changed.",
            ),
        )
        self.run_ctl("amend", "study", "--artifact", later)
        blocked = self.next_json()
        self.assertEqual((blocked["do"], blocked["reason"].split()[0]), ("blocked", "study"))

    def test_broken_runbook_verdict_is_receipted_and_blocks(self):
        _, original = self.to_runbook_amendable_steps()
        suffix = self.runbook_amendment(
            "Step 1: entry holds; exit broken. "
            "Step 2: entry holds; exit holds."
        )
        candidate = self.write("candidate.md", original + suffix)
        result = self.run_ctl("amend", "runbook", "--artifact", candidate)
        self.assertIn("dependent work is blocked", result.stdout)
        blocked = self.next_json()
        self.assertIn("runbook amendment marks step 1", blocked["reason"])
        proc = self.run_ctl(
            "done", "implement", "--branch", self.step_branch(1),
            "--commit", "abc", expect=2,
        )
        self.assertIn("runbook amendment blocks step 1", proc.stderr)

    def test_prefix_forgery_and_appended_step_topology_refuse_without_mutation(self):
        for label, candidate_text, message in (
            (
                "prefix",
                lambda original: "forged\n" + original + self.runbook_amendment(),
                "exact prefix",
            ),
            (
                "topology",
                lambda original: original + self.runbook_amendment()
                + "\n## Step 3: Smuggled\n\nNo.\n",
                "final section",
            ),
        ):
            with self.subTest(label=label):
                other = TestRunbookAmendments(methodName="runTest")
                other.setUp()
                try:
                    _, original = other.to_runbook_amendable_steps()
                    before = other.state()["receipts"]["runbook"]["sha256"]
                    candidate = other.write("candidate.md", candidate_text(original))
                    proc = other.run_ctl(
                        "amend", "runbook", "--artifact", candidate, expect=2
                    )
                    self.assertIn(message, proc.stderr)
                    self.assertEqual(
                        other.state()["receipts"]["runbook"]["sha256"], before
                    )
                finally:
                    other.tearDown()

    def test_fenced_decoy_is_ignored_and_two_real_final_blocks_refuse(self):
        self.init()
        with open(COMPLETE_STUDY, encoding="utf-8") as handle:
            study = self.write("study.md", handle.read())
        self.run_ctl("done", "study", "--artifact", study)
        original = (
            "# Runbook\n\n```markdown\n### Amendment -- 2026-01-01\n```\n\n"
            "## Step 1: Core\n\n**Goal.** Core.\n**Entry.** Ready.\n"
            "**Exit.** Run `fiat-v1.0.0`.\n**Files.** `a`.\n"
            "**Tests.** Run `python3 -m unittest`.\n"
            "**Disciplines.** none, fixture.\n"
            "\n## Step 2: Finish\n\n**Goal.** Finish.\n**Entry.** Ready.\n"
            "**Exit.** Run `fiat-v1.0.0`.\n**Files.** `b`.\n"
            "**Tests.** Run `python3 -m unittest`.\n"
            "**Disciplines.** none, fixture.\n"
        )
        runbook = self.write("runbook.md", original)
        steps = self.write("steps.json", '["Core", "Finish"]')
        self.run_ctl("done", "runbook", "--artifact", runbook, "--steps-file", steps)
        original = Path(os.path.join(self.target, runbook)).read_text(encoding="utf-8")
        valid = self.write("candidate.md", original + self.runbook_amendment())
        self.run_ctl("amend", "runbook", "--artifact", valid)

        other = TestRunbookAmendments(methodName="runTest")
        other.setUp()
        try:
            _, baseline = other.to_runbook_amendable_steps()
            duplicate = other.write(
                "candidate.md",
                baseline + other.runbook_amendment() + other.runbook_amendment(date="2026-08-25"),
            )
            proc = other.run_ctl("amend", "runbook", "--artifact", duplicate, expect=2)
            self.assertIn("more than one final amendment", proc.stderr)
        finally:
            other.tearDown()

    def test_replacement_clause_unknown_duplicate_partial_and_field_shape_refuse(self):
        cases = {
            "unknown": (
                self.runbook_amendment(what="Complete replacement Unknown: no."),
                "complete field",
            ),
            "duplicate": (
                self.runbook_amendment(
                    what=(
                        "Complete replacement Exit: first. "
                        "Complete replacement Exit: second."
                    )
                ),
                "repeats complete replacement",
            ),
            "partial": (
                self.runbook_amendment(what="The Exit should use v2."),
                "complete field",
            ),
            "missing why": (
                self.runbook_amendment().replace(
                    "**Why.** The target version changed.\n", ""
                ),
                "field 'Why' must occur exactly once",
            ),
            "reordered": (
                self.runbook_amendment().replace(
                    "**What changed.** Complete replacement Exit: Run `fiat-v2.0.0`.\n"
                    "**Why.** The target version changed.\n",
                    "**Why.** The target version changed.\n"
                    "**What changed.** Complete replacement Exit: Run `fiat-v2.0.0`.\n",
                ),
                "accepted four-field order",
            ),
        }
        for label, (suffix, message) in cases.items():
            with self.subTest(label=label):
                other = TestRunbookAmendments(methodName="runTest")
                other.setUp()
                try:
                    _, original = other.to_runbook_amendable_steps()
                    candidate = other.write("candidate.md", original + suffix)
                    proc = other.run_ctl(
                        "amend", "runbook", "--artifact", candidate, expect=2
                    )
                    self.assertIn(message, proc.stderr)
                finally:
                    other.tearDown()

    def test_replacement_exit_without_command_refuses_without_mutation_or_carriage(self):
        _, original = self.to_runbook_amendable_steps()
        before = self.state()["receipts"]["runbook"]["sha256"]
        suffix = self.runbook_amendment(
            what="Complete replacement Exit: Reviewed and working."
        )
        candidate = self.write("candidate.md", original + suffix)
        proc = self.run_ctl("amend", "runbook", "--artifact", candidate, expect=2)
        self.assertIn("Protasis rejected", proc.stderr)
        self.assertEqual(self.state()["receipts"]["runbook"]["sha256"], before)
        packet = self.next_json()["brief"]["runbook_step"]
        self.assertNotIn("Reviewed and working.", packet["markdown"])

    def test_indented_code_line_cannot_hide_a_step_heading_from_topology(self):
        _, original = self.to_runbook_amendable_steps()
        before = self.state()["receipts"]["runbook"]["sha256"]
        suffix = self.runbook_amendment().replace(
            "**What changed.** Complete replacement Exit: Run `fiat-v2.0.0`.\n",
            "**What changed.** Complete replacement Exit: Run `fiat-v2.0.0`.\n"
            "    ```\n"
            "## Step 3: Smuggled visible heading\n\n"
            "Outside the accepted topology.\n"
            "    ```\n",
        )
        candidate = self.write("candidate.md", original + suffix)
        proc = self.run_ctl("amend", "runbook", "--artifact", candidate, expect=2)
        self.assertIn("final section", proc.stderr)
        self.assertEqual(self.state()["receipts"]["runbook"]["sha256"], before)
        packet = self.next_json()["brief"]["runbook_step"]
        self.assertNotIn("Smuggled visible heading", packet["markdown"])

    def test_verdict_coverage_unknown_touch_and_completed_touch_refuse(self):
        cases = (
            (
                "missing verdict",
                self.runbook_amendment("Step 1: entry holds; exit holds."),
                "missing verdict",
                False,
            ),
            (
                "duplicate verdict",
                self.runbook_amendment(
                    "Step 1: entry holds; exit holds. "
                    "Step 1: entry holds; exit holds. "
                    "Step 2: entry holds; exit holds."
                ),
                "duplicate step verdict",
                False,
            ),
            (
                "unknown touched",
                self.runbook_amendment(touched="Step 9."),
                "unknown touched step",
                False,
            ),
            (
                "completed touched",
                self.runbook_amendment(
                    "Step 2: entry holds; exit holds.", touched="Step 1."
                ),
                "cannot rewrite completed step",
                True,
            ),
        )
        for label, suffix, message, complete_first in cases:
            with self.subTest(label=label):
                other = TestRunbookAmendments(methodName="runTest")
                other.setUp()
                try:
                    _, original = other.to_runbook_amendable_steps()
                    if complete_first:
                        path = os.path.join(other.target, ".hexaemeron", "state.json")
                        with open(path, encoding="utf-8") as handle:
                            state = json.load(handle)
                        state["steps"][0].update(status="done", phase="done")
                        state["steps"][1].update(status="open", phase="implement")
                        state["current_step"] = 2
                        with open(path, "w", encoding="utf-8") as handle:
                            json.dump(state, handle)
                    candidate = other.write("candidate.md", original + suffix)
                    proc = other.run_ctl(
                        "amend", "runbook", "--artifact", candidate, expect=2
                    )
                    self.assertIn(message, proc.stderr)
                finally:
                    other.tearDown()

    def test_wrong_phase_unbound_receipt_checker_path_and_size_refuse(self):
        self.init()
        candidate = self.write("candidate.md", self.runbook_amendment())
        proc = self.run_ctl("amend", "runbook", "--artifact", candidate, expect=2)
        self.assertIn("only while build steps are active", proc.stderr)

        for label in ("checker", "unbound"):
            other = TestRunbookAmendments(methodName="runTest")
            other.setUp()
            try:
                if label == "checker":
                    other.to_amendable_steps()
                    with open(os.path.join(other.target, "runbook.md"), encoding="utf-8") as handle:
                        original = handle.read()
                else:
                    _, original = other.to_runbook_amendable_steps()
                    path = os.path.join(other.target, ".hexaemeron", "state.json")
                    with open(path, encoding="utf-8") as handle:
                        state = json.load(handle)
                    state["receipts"]["runbook"].pop("sha256")
                    with open(path, "w", encoding="utf-8") as handle:
                        json.dump(state, handle)
                candidate = other.write("candidate.md", original + other.runbook_amendment())
                proc = other.run_ctl("amend", "runbook", "--artifact", candidate, expect=2)
                self.assertIn(
                    "Protasis rejected" if label == "checker" else "source-bound runbook receipt",
                    proc.stderr,
                )
            finally:
                other.tearDown()

        bounded = TestRunbookAmendments(methodName="runTest")
        bounded.setUp()
        try:
            _, original = bounded.to_runbook_amendable_steps()
            outside = tempfile.NamedTemporaryFile("w", delete=False)
            try:
                outside.write(original + bounded.runbook_amendment())
                outside.close()
                proc = bounded.run_ctl(
                    "amend", "runbook", "--artifact", outside.name, expect=2
                )
                self.assertIn("escapes target directory", proc.stderr)
            finally:
                os.unlink(outside.name)
            large = bounded.write(
                "large.md", original + bounded.runbook_amendment() + "x" * (2 * 1024 * 1024)
            )
            proc = bounded.run_ctl("amend", "runbook", "--artifact", large, expect=2)
            self.assertIn("exceeds 2097152-byte cap", proc.stderr)
        finally:
            bounded.tearDown()

    def test_interrupted_runbook_replacement_recovers_once(self):
        _, original = self.to_runbook_amendable_steps()
        suffix = self.runbook_amendment()
        candidate_text = original + suffix
        candidate = self.write("candidate.md", candidate_text)
        module = hexctl_module()
        with mock.patch.object(
            module,
            "commit",
            side_effect=KeyboardInterrupt("interrupted after runbook replacement"),
        ):
            with self.assertRaises(KeyboardInterrupt):
                module.cmd_amend_runbook(
                    argparse.Namespace(
                        dir=self.target,
                        artifact=os.path.join(self.target, candidate),
                    )
                )
        pending = os.path.join(
            self.target, ".hexaemeron", "runbook-amendment-pending.json"
        )
        self.assertTrue(os.path.isfile(pending))
        proc = self.run_ctl("status", expect=2)
        self.assertIn("runbook amendment transaction is pending", proc.stderr)
        recovered = self.run_ctl(
            "amend", "runbook", "--artifact", os.path.join(self.target, "runbook.md")
        )
        self.assertIn("recovered", recovered.stdout)
        self.assertFalse(os.path.exists(pending))
        self.run_ctl("verify")
        with open(
            os.path.join(self.target, ".hexaemeron", "ledger.jsonl"), encoding="utf-8"
        ) as handle:
            events = [json.loads(line)["event"] for line in handle if line.strip()]
        self.assertEqual(events.count("amend:runbook"), 1)

    def test_written_runbook_ledger_event_recovers_without_duplication(self):
        _, original = self.to_runbook_amendable_steps()
        candidate_text = original + self.runbook_amendment()
        candidate = self.write("candidate.md", candidate_text)
        module = hexctl_module()
        with mock.patch.object(
            module,
            "save_state",
            side_effect=OSError("interrupted before runbook state replacement"),
        ):
            with self.assertRaises(OSError):
                module.cmd_amend_runbook(
                    argparse.Namespace(
                        dir=self.target,
                        artifact=os.path.join(self.target, candidate),
                    )
                )
        recovered = self.run_ctl(
            "amend", "runbook", "--artifact", os.path.join(self.target, "runbook.md")
        )
        self.assertIn("recovered", recovered.stdout)
        with open(
            os.path.join(self.target, ".hexaemeron", "ledger.jsonl"), encoding="utf-8"
        ) as handle:
            events = [json.loads(line)["event"] for line in handle if line.strip()]
        self.assertEqual(events.count("amend:runbook"), 1)

    def test_runbook_pending_marker_rolls_back_when_canonical_bytes_are_prior(self):
        _, original = self.to_runbook_amendable_steps()
        module = hexctl_module()
        state = self.state()
        candidate = (original + self.runbook_amendment()).encode()
        amendment = module._runbook_amendment_record(
            state, state["receipts"]["runbook"]["sha256"], candidate
        )
        module.write_amendment_pending(
            self.target,
            "runbook",
            {
                "version": 1,
                "artifact": state["receipts"]["runbook"]["artifact"],
                "state_before_sha256": module.state_fingerprint(state),
                "amendment": amendment,
            },
        )
        recovered = self.run_ctl(
            "amend", "runbook", "--artifact", os.path.join(self.target, "runbook.md")
        )
        self.assertIn("rolled back", recovered.stdout)
        self.assertNotIn("amendments", self.state()["receipts"]["runbook"])

    def test_committed_runbook_receipt_clears_a_marker_left_before_cleanup(self):
        _, original = self.to_runbook_amendable_steps()
        candidate = self.write(
            "candidate.md", original + self.runbook_amendment()
        )
        module = hexctl_module()
        with mock.patch.object(
            module,
            "verify_run",
            side_effect=KeyboardInterrupt("interrupted before pending cleanup"),
        ):
            with self.assertRaises(KeyboardInterrupt):
                module.cmd_amend_runbook(
                    argparse.Namespace(
                        dir=self.target,
                        artifact=os.path.join(self.target, candidate),
                    )
                )
        pending = module.amendment_pending_path(self.target, "runbook")
        self.assertTrue(os.path.isfile(pending))
        recovered = self.run_ctl(
            "amend", "runbook", "--artifact", os.path.join(self.target, "runbook.md")
        )
        self.assertIn("committed", recovered.stdout)
        self.assertFalse(os.path.exists(pending))
        with open(
            os.path.join(self.target, ".hexaemeron", "ledger.jsonl"), encoding="utf-8"
        ) as handle:
            events = [json.loads(line)["event"] for line in handle if line.strip()]
        self.assertEqual(events.count("amend:runbook"), 1)

    def test_legacy_study_pending_marker_recovers_without_subject(self):
        original = self.to_amendable_steps()
        candidate_text = original + self.amendment()
        module = hexctl_module()
        state = self.state()
        amendment = module._study_amendment_record(
            state,
            state["receipts"]["study"]["sha256"],
            candidate_text.encode(),
        )
        marker = {
            "version": 1,
            "artifact": state["receipts"]["study"]["artifact"],
            "state_before_sha256": module.state_fingerprint(state),
            "amendment": amendment,
        }
        pending = os.path.join(
            self.target, ".hexaemeron", "study-amendment-pending.json"
        )
        with open(pending, "w", encoding="utf-8") as handle:
            json.dump(marker, handle)
        recovered = self.run_ctl(
            "amend", "study", "--artifact", os.path.join(self.target, "study.md")
        )
        self.assertIn("rolled back", recovered.stdout)
        self.assertFalse(os.path.exists(pending))

    def test_two_pending_subjects_refuse_without_deleting_either(self):
        self.to_runbook_amendable_steps()
        module = hexctl_module()
        state = self.state()
        for subject in ("study", "runbook"):
            receipt = state["receipts"][subject]
            module.write_amendment_pending(
                self.target,
                subject,
                {
                    "version": 1,
                    "artifact": receipt["artifact"],
                    "state_before_sha256": module.state_fingerprint(state),
                    "amendment": {},
                },
            )
        proc = self.run_ctl("verify", expect=1)
        self.assertIn("multiple amendment transactions", proc.stderr)
        for subject in ("study", "runbook"):
            self.assertTrue(os.path.isfile(module.amendment_pending_path(self.target, subject)))

    def test_unrelated_and_stale_amendments_are_not_selected_for_a_packet(self):
        study_text, original = self.to_runbook_amendable_steps()
        suffix = self.runbook_amendment(touched="Step 2.")
        candidate = self.write("candidate.md", original + suffix)
        self.run_ctl("amend", "runbook", "--artifact", candidate)
        first = self.next_json()["brief"]["runbook_step"]
        self.assertEqual(first["amendments"], [])
        self.assertNotIn("fiat-v2.0.0", first["markdown"])

        holding = self.write(
            "holding-study.md",
            study_text
            + self.amendment(
                "Step 1: entry holds; exit holds. "
                "Step 2: entry holds; exit holds."
            ),
        )
        self.run_ctl("amend", "study", "--artifact", holding)
        stale = self.next_json()["brief"]["runbook_step"]
        self.assertEqual(stale["amendments"], [])

    def test_multiple_current_amendments_are_carried_in_receipt_order(self):
        _, original = self.to_runbook_amendable_steps()
        first_suffix = self.runbook_amendment(
            what="Complete replacement Exit: Run `fiat-v2.0.0`."
        )
        first = original + first_suffix
        self.run_ctl(
            "amend", "runbook", "--artifact", self.write("first.md", first)
        )
        second_suffix = self.runbook_amendment(
            date="2026-08-25",
            what="Complete replacement Tests: Run `python3 -m unittest -v`.",
        )
        self.run_ctl(
            "amend", "runbook", "--artifact", self.write("second.md", first + second_suffix)
        )
        carried = self.next_json()["brief"]["runbook_step"]["amendments"]
        self.assertEqual(
            [item["markdown"] for item in carried], [first_suffix, second_suffix]
        )

    def test_checker_receives_exact_captured_bytes_by_fixed_argv(self):
        _, original = self.to_runbook_amendable_steps()
        candidate_text = original + self.runbook_amendment()
        candidate = self.write("candidate.md", candidate_text)
        module = hexctl_module()
        calls = []

        def checker(base_dir, program, argv, refusal=None):
            calls.append((base_dir, program, list(argv), refusal))
            with open(argv[1], "rb") as handle:
                self.assertEqual(handle.read(), candidate_text.encode())
            return b""

        with mock.patch.object(module, "bounded_tool", side_effect=checker):
            module.cmd_amend_runbook(
                argparse.Namespace(
                    dir=self.target, artifact=os.path.join(self.target, candidate)
                )
            )
        self.assertEqual(len(calls), 1)
        _, program, argv, refusal = calls[0]
        self.assertEqual(program, sys.executable)
        self.assertEqual(argv[0], os.path.realpath(PROTASIS_CHECKER))
        self.assertEqual(len(argv), 2)
        self.assertIn("Protasis rejected", refusal)

    def test_post_amendment_drift_and_receipt_history_mismatch_refuse(self):
        _, original = self.to_runbook_amendable_steps()
        suffix = self.runbook_amendment()
        candidate = self.write("candidate.md", original + suffix)
        self.run_ctl("amend", "runbook", "--artifact", candidate)
        self.write("runbook.md", original + suffix + "unreceipted\n")
        for command in (("next",), ("status",), ("verify",)):
            with self.subTest(command=command[0]):
                proc = self.run_ctl(*command, expect=2)
                self.assertIn("runbook artefact digest changed", proc.stderr)

        other = TestRunbookAmendments(methodName="runTest")
        other.setUp()
        try:
            _, baseline = other.to_runbook_amendable_steps()
            candidate = other.write("candidate.md", baseline + other.runbook_amendment())
            other.run_ctl("amend", "runbook", "--artifact", candidate)
            path = os.path.join(other.target, ".hexaemeron", "state.json")
            with open(path, encoding="utf-8") as handle:
                state = json.load(handle)
            state["receipts"]["runbook"]["amendments"][0]["amendment_start"] += 1
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(state, handle)
            proc = other.run_ctl("next", expect=1)
            self.assertIn("digest evidence does not match source", proc.stderr)
        finally:
            other.tearDown()




class RunWorktreeDemoTests(unittest.TestCase):
    """The study's demo path, run rather than described."""

    def setUp(self):
        import tempfile, shutil, os
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.repo = os.path.join(self.tmp, "repo")
        os.makedirs(self.repo)
        for argv in (["init", "-q", "-b", "main"],
                     ["config", "user.email", "demo@example.invalid"],
                     ["config", "user.name", "Demo"],
                     ["config", "commit.gpgsign", "false"],
                     ["commit", "-q", "--allow-empty", "-m", "base"]):
            subprocess.run(["git", *argv], cwd=self.repo, check=True, capture_output=True)

    def git(self, *args, cwd=None):
        return subprocess.run(["git", *args], cwd=cwd or self.repo,
                              capture_output=True, text=True, check=True).stdout.strip()

    def hexctl(self, *args):
        import sys
        return subprocess.run([sys.executable, str(HEXCTL), *args],
                              capture_output=True, text=True)

    def test_the_demo_path_leaves_a_dirty_checkout_exactly_as_it_found_it(self):
        import os
        with open(os.path.join(self.repo, "dirty-file.txt"), "w", encoding="utf-8") as fh:
            fh.write("the operator's uncommitted work\n")
        before_branch = self.git("rev-parse", "--abbrev-ref", "HEAD")
        before_head = self.git("rev-parse", "HEAD")
        before_status = self.git("status", "--short")

        done = self.hexctl("--dir", self.repo, "init", "--topic", "worktree demo",
                           "--base", "main")
        self.assertEqual(done.returncode, 0, done.stderr)

        self.assertEqual(self.git("rev-parse", "--abbrev-ref", "HEAD"), before_branch)
        self.assertEqual(self.git("rev-parse", "HEAD"), before_head)
        self.assertEqual(self.git("status", "--short"), before_status)

        worktree = os.path.join(self.repo, "tmp", "fiat", "fiat-worktree-demo")
        self.assertIn(worktree, self.git("worktree", "list", "--porcelain"))
        self.assertEqual(self.git("rev-parse", "--abbrev-ref", "HEAD", cwd=worktree),
                         "fiat/worktree-demo")

        status = self.hexctl("--dir", worktree, "status", "--json")
        self.assertEqual(status.returncode, 0, status.stderr)
        self.assertEqual(json.loads(status.stdout)["topic"], "worktree demo")

    def test_a_directory_that_is_not_a_repository_refuses_and_creates_no_state(self):
        import os
        plain = os.path.join(self.tmp, "not-a-repo")
        os.makedirs(plain)
        done = self.hexctl("--dir", plain, "init", "--topic", "worktree demo")
        self.assertEqual(done.returncode, 2)
        self.assertIn("not a git repository", done.stderr)
        for name in ("state.json", "ledger.jsonl", "worktree"):
            self.assertFalse(os.path.exists(os.path.join(plain, ".hexaemeron", name)), name)
