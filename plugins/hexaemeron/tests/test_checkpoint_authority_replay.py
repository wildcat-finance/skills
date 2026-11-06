"""Authenticated ordering, finite publication and current-authority boundaries.

Every refusal below is a retained counterexample: the exact history, the one
change made to it, and the code the replay must answer with.
"""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import checkpoint_authority_replay_fixture as fixture
from checkpoint_authority import signatures, wire
from checkpoint_authority.canonical import Refusal, canonical, digest
from checkpoint_authority.eligibility import Freshness, GATEWAY_CONTRACT
from checkpoint_authority.replay import EVENTS, RETAIN

REPLAYED = None
"""Set by the committed-history case; the suite runner reports it as evidence."""


class ReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture.Signer.setUpClass()
        cls.signer = fixture.Signer()

    @classmethod
    def tearDownClass(cls):
        fixture.Signer.tearDownClass()

    def history(self, **kwargs):
        return fixture.History(self.signer, **kwargs)

    def fresh(self, history, **overrides):
        values = dict(challenge="challenge-1", now=datetime(2026,9,16,0,0,10,tzinfo=timezone.utc),
            policy_count=history.policy_count, policy_tail=history.policy_tail["sha256"],
            decision_count=history.journal_count, decision_tail=history.journal_tail)
        values.update(overrides)
        return Freshness(**values)

    def refused(self, code, callable_, *args, **kwargs):
        with self.assertRaises(Refusal) as caught:
            callable_(*args, **kwargs)
        self.assertEqual(caught.exception.code, code)
        return caught.exception

    def test_complete_historical_publication_and_fresh_eligibility(self):
        h=self.history(); h.accept()
        self.assertEqual(h.reader().finish()["accepted"][0]["current_eligibility"], "unknown")
        reader=h.reader(self.fresh(h));result=reader.finish(presence=h.presence(reader))
        self.assertTrue(result["complete"])
        self.assertEqual(result["accepted"][0]["publication"], "complete")
        self.assertEqual(result["accepted"][0]["current_eligibility"], "eligible")
        self.assertEqual(result["gateway_execution"], "not-established")
        # Fresh head without a scoped presence observation is unavailable, never eligible.
        self.assertEqual(h.reader(self.fresh(h)).finish()["accepted"][0]["current_eligibility"], "unavailable")

    def test_both_complete_histories_and_exact_head_are_required(self):
        h=self.history(); h.accept()
        for source in (h.envelopes[1:], h.envelopes[:2]+h.envelopes[3:], h.envelopes[:-2],
            h.envelopes[:6]+h.envelopes[7:], h.envelopes+[h.envelopes[-1]],
            [h.envelopes[1],h.envelopes[0],*h.envelopes[2:]]):
            with self.subTest(length=len(source)), self.assertRaises(Refusal):
                h.reader(envelopes=source).finish()
        for field in ("policy_history", "decisions"):
            head=copy.deepcopy(h.records[h.last_head['sha256']]); head[field]["tail"]="f"*64
            with self.subTest(field=field), self.assertRaisesRegex(Refusal,"head-completeness"):
                h.reader(envelopes=h.envelopes[:-1]+[self.signer.envelope(head)]).finish()

    def test_omission_duplicate_and_missing_terminal_head_are_incomplete(self):
        h=self.history(); h.accept()
        # A history whose last record is not a head has no complete-head verdict.
        self.refused("history-incomplete", h.reader(envelopes=h.envelopes[:-1]).finish)
        # The exact same envelope twice is a duplicate, never a second decision.
        first_journal=next(i for i,e in enumerate(h.envelopes) if h.records[digest(e)]["type"]=="journal-entry")
        self.refused("duplicate-record", h.reader, envelopes=h.envelopes[:first_journal+1]+[h.envelopes[first_journal]])
        # An omitted trust record breaks the policy predecessor chain.
        self.refused("trust-predecessor", h.reader, envelopes=h.envelopes[:2]+h.envelopes[3:])

    def test_event_sequence_gaps_forks_payload_and_decision_substitution(self):
        for field in ("sequence", "previous_commitment", "payload_sha256", "decision_id", "stream"):
            h=self.history();h.accept()
            index=next(i for i,e in enumerate(h.envelopes) if h.records[digest(e)]["type"]=="journal-entry")
            value=copy.deepcopy(h.records[digest(h.envelopes[index])])
            if field=="sequence":value[field]=2;value["previous"]={"type":"authority-policy","sha256":h.policy["sha256"]};value["previous_commitment"]="f"*64
            elif field=="stream":value[field]="policy"
            else:value[field]="f"*64
            with self.subTest(field=field),self.assertRaises(Refusal):
                h.reader(envelopes=h.envelopes[:index]+[self.signer.envelope(value)]).finish()

    def test_foreign_scope_unknown_types_and_unjournaled_events_refuse(self):
        h=self.history(); h.accept()
        foreign=fixture.trust.Bootstrap("test","test-service",23,"fiat-"+"b"*64,h.bootstrap.roots)
        reader=fixture.Replay(foreign,h.tools,native_evidence=h.native.__getitem__)
        self.refused("foreign-scope", reader.append, h.envelopes[0])
        self.refused("replay-failed", reader.append, h.envelopes[0])
        # A record type outside the closed inventory has no trusted role, even when signed by the root.
        unknown=copy.deepcopy(h.records[h.policy["sha256"]]); unknown["type"]="future-record"
        payload=canonical({"_type":signatures.STATEMENT,"subject":signatures.subjects(unknown),"predicateType":signatures.PREDICATE,"predicate":unknown})
        forged=signatures.envelope_bytes(payload,self.signer.sign(signatures.pae(payload),"root"))
        self.refused("issuer-untrusted", h.reader, envelopes=h.envelopes+[forged])
        # A journal entry must follow exactly the event it commits.
        journal=h.body("journal-entry"); journal.update(sequence=h.journal_count+1,
            previous={"type":"journal-entry","sha256":h.journal_sha}, stream="decisions", event=h.policy,
            decision_id=None, payload_sha256="f"*64, previous_commitment=h.journal_tail)
        self.refused("journal-event-required", h.reader, envelopes=h.envelopes+[self.signer.envelope(journal)])
        # An event that is never journaled blocks every later record.
        denial=h.body("denial"); denial.update(sequence=h.journal_count+1, previous={"type":"journal-entry","sha256":h.journal_sha},
            target={"kind":"run","run_id":h.run_id}, reason="operator-revoked", descendants="none", effective_at=h.clock, policy_head=h.last_head)
        encoded=self.signer.envelope(denial); head=h.head(); h.envelopes.pop()
        self.refused("event-not-journaled", h.reader, envelopes=h.envelopes+[encoded, self.signer.envelope(h.records[head["sha256"]])])

    def test_authorization_survives_lease_and_endorsement_expiry(self):
        h=self.history();h.accept(finalize=False)
        h.clock="2026-09-16T00:06:00Z"; h.head()
        result=h.reader().finish()["accepted"][0]
        self.assertEqual((result["historical"],result["publication"]),("valid","incomplete"))
        # No temporary lease state is consulted or allowed to erase authorization.
        self.assertEqual(len(h.reader().decisions),1)

    def test_cancellation_is_exclusive_in_both_orders(self):
        h=self.history();receipt,identity=h.accept(finalize=False)
        value=h.body("cancellation");value.update(decision_id=h.records[receipt['sha256']]["identities"]["snapshot_id"],candidate_id="candidate-1")
        h.event(value,value["decision_id"]);h.head()
        self.refused("decision-exclusivity", h.reader)
        h=self.history();value=h.body("cancellation");value.update(decision_id="f"*64,candidate_id="candidate-1")
        h.event(value,value["decision_id"]);h.head();h.accept()
        self.refused("candidate-decision-conflict", h.reader)

    def test_contradictory_decisions_after_denial_and_stale_denial_heads_refuse(self):
        h=self.history();receipt,identity=h.accept(finalize=False);h.deny(receipt)
        final=h.body("publication-finalization")
        final.update(acceptance_id=identity,acceptance=receipt,authorization_head=h.last_head,
            archives=h.records[receipt['sha256']]["copies"],receipts=h.copies({"sha256":receipt["sha256"],"length":1}))
        h.event(final,identity);h.head()
        self.refused("finalization-binding", h.reader)
        h=self.history();receipt,_=h.accept();stale=h.last_head;h.accept("second")
        h.deny(receipt,mutate=lambda x:x.update(policy_head=stale))
        self.refused("denial-head", h.reader)

    def test_finite_finalization_requires_both_exact_copies(self):
        h=self.history();h.accept(final_copies=False)
        self.assertEqual(h.reader(self.fresh(h)).finish()["accepted"][0]["current_eligibility"],"unavailable")
        final=next((key,value) for key,value in h.records.items() if value["type"]=="publication-finalization")
        self.assertNotIn(final[0],json.dumps(final[1]))

    def test_exact_and_randomized_signature_retries_keep_first_envelope(self):
        h=self.history();ref,identity=h.accept();reader=h.reader()
        raw=next(e for e in h.envelopes if digest(e)==ref["sha256"])
        self.assertEqual(reader.retry(raw)["disposition"],"exact-retry")
        alternate=self.signer.envelope(h.records[ref['sha256']])
        self.assertNotEqual(digest(alternate),ref["sha256"])
        result=reader.retry(alternate)
        self.assertEqual(result["receipt_sha256"],ref["sha256"])
        self.assertFalse(result["new_decision"])
        # A retry signed by another key, or naming an unenrolled issuer, is refused
        # through the replayed policy; no caller-supplied key is consulted.
        self.refused("signature-invalid", reader.retry, self.signer.envelope(h.records[ref['sha256']], "contributor"))
        foreign=dict(h.records[ref['sha256']],issuer=h.keys["contributor"]["fingerprint"])
        self.refused("issuer-untrusted", reader.retry, self.signer.envelope(foreign, "contributor"))
        self.assertEqual(len(reader.decisions),1)

    def test_alternate_carrier_needs_full_native_equivalence_and_creates_no_child(self):
        h=self.history();ref,identity=h.accept()
        _,_,_,validation=h.validated("alternate",alternate=True);h.head();reader=h.reader()
        result=reader.equivalent(validation)
        self.assertEqual(result["receipt_sha256"],ref["sha256"])
        self.assertFalse(result["submitted_alternate_accepted"])
        self.assertFalse(result["new_child"])
        self.assertEqual(len(reader.decisions),1)
        del h.native[h.records[validation['sha256']]["output_sha256"]]
        self.refused("native-evidence-unavailable", h.reader)

    def test_root_and_immediate_parent_complete_prior_inventory(self):
        h=self.history();h.accept();h.accept("child");result=h.reader().finish()
        self.assertEqual(len(result["accepted"]),2)
        # An accepted producer prefix exists, so an emptied inventory is an omission, not a root.
        for code,change in (("parent-inventory",lambda x:x.update(parents=[],prior_receipts=[])),
            ("parent-run-base",lambda x:x.update(initial_base="f"*40)),
            ("parent-run-base",lambda x:x.update(producer_prefix_sha256="f"*64))):
            h=self.history();h.accept();h.accept("child",mutate_parent=change)
            with self.subTest(code=code):self.refused(code, h.reader)
        # A first acceptance claiming a continuation has no registered-root permission.
        h=self.history()
        h.accept(mutate_acceptance=lambda x:x.update(parent_acceptance_ids=["f"*64],transition={"kind":"continuation",
            "parent":h.records[x["endorsement"]["sha256"]]["parent"],"producer_prefix_sha256":digest(h.producer),"initial_base":h.base}))
        self.refused("root-permission", h.reader)
        h=self.history();h.accept();h.accept("child");h.accept("grandchild",mutate_parent=lambda x:x.update(parents=x["prior_receipts"][:1]))
        self.refused("parent-inventory", h.reader)
        h=self.history();h.accept();h.accept("child",mutate_parent=lambda x:x.update(prior_receipts=x["prior_receipts"]+[{"type":"acceptance","sha256":"f"*64}]))
        self.refused("missing-or-forward-reference", h.reader)

    def test_native_anchor_naming_another_run_is_a_base_run_mismatch(self):
        h=self.history(anchor_run_id="fiat-"+"c"*64);h.accept()
        self.refused("parent-run-base", h.reader)

    def test_poison_closes_descendants_and_blocks_new_children(self):
        h=self.history();ref,_=h.accept();h.accept("child");h.deny(ref)
        self.assertEqual({x["current_eligibility"] for x in h.reader(self.fresh(h)).finish()["accepted"]},{"denied"})
        h.accept("grandchild")
        self.refused("poisoned-parent", h.reader)
        h=self.history();ref,_=h.accept();h.accept("child");h.deny(ref,poison=False)
        # Without poison the child keeps its own eligibility; only the denied parent falls.
        reader=h.reader(self.fresh(h));rows={x["acceptance_id"]:x["current_eligibility"] for x in reader.finish(presence=h.presence(reader))["accepted"]}
        self.assertEqual(sorted(rows.values()),["denied","eligible"])

    def test_authorized_absence_never_restores_eligibility(self):
        h=self.history();ref,_=h.accept();denied=h.deny(ref)
        artifact=h.records[ref['sha256']]["accepted_representation"]
        absent={(artifact["sha256"],"primary"):False}
        self.assertEqual(h.reader().finish(presence=absent)["accepted"][0]["publication"],"unexplained-absence")
        removal=h.body("authorized-removal");removal.update(denial=denied,removed=[artifact])
        h.event(removal);h.head();reader=h.reader(self.fresh(h))
        presence=h.presence(reader);presence.update(absent)
        result=reader.finish(presence=presence)["accepted"][0]
        self.assertEqual((result["publication"],result["current_eligibility"]),("authorized-absence","denied"))
        # A removal naming an artifact outside the denial's scope refuses.
        h=self.history();ref,_=h.accept();other,_=h.accept("other");denied=h.deny(ref,poison=False)
        removal=h.body("authorized-removal");removal.update(denial=denied,removed=[h.records[other['sha256']]["accepted_representation"]])
        h.event(removal);h.head()
        self.refused("removal-scope", h.reader)

    def test_challenge_time_and_remembered_floor_cannot_be_self_asserted(self):
        h=self.history();h.accept()
        for code,changes in (("head-challenge",{"challenge":"other"}),
            ("head-stale",{"now":datetime(2026,9,16,0,6,tzinfo=timezone.utc)}),
            ("head-rollback",{"decision_tail":"f"*64}),("head-rollback",{"policy_tail":"f"*64}),
            ("head-rollback",{"decision_count":h.journal_count+1})):
            with self.subTest(code=code,changes=list(changes)):
                self.refused(code, lambda: h.reader(self.fresh(h,**changes)).finish())
        # A remembered floor above the presented history is a rollback, not a fresh view.
        with self.assertRaisesRegex(Refusal,"freshness-input"):h.reader(freshness=object())

    def test_permit_order_nonce_and_offline_limits(self):
        h=self.history();ref,identity=h.accept();h.permit(ref,identity);h.deny(ref)
        result=h.reader(self.fresh(h)).finish()
        self.assertEqual(result["historical_permits"],1)
        self.assertEqual(result["accepted"][0]["current_eligibility"],"denied")
        self.assertEqual(result["offline_unused_nonce"],"unknown")
        self.assertFalse(GATEWAY_CONTRACT["gateway_execution_established"])
        self.assertEqual(GATEWAY_CONTRACT["head_check_max_seconds"],2)
        self.assertEqual(GATEWAY_CONTRACT["head_check_max_bytes"],8*1024*1024)
        self.assertEqual(GATEWAY_CONTRACT["channel_stale_cancel_seconds"],5)
        self.assertFalse(GATEWAY_CONTRACT["range_enabled"] or GATEWAY_CONTRACT["delivered_bytes_recall"])
        h.permit(ref,identity,nonce="later")
        self.refused("permit-ineligible", h.reader)
        h=self.history();ref,identity=h.accept();h.permit(ref,identity);h.permit(ref,identity)
        self.refused("permit-nonce-used", h.reader)
        h=self.history();ref,identity=h.accept();h.permit(ref,identity);h.permit(ref,identity,session="session-2")
        self.assertEqual(h.reader().finish()["historical_permits"],2)

    def test_permit_binds_exact_representation_finalization_and_grant(self):
        for code,mutate in (("permit-ineligible",lambda x:x.update(outer_sha256="f"*64)),
            ("permit-ineligible",lambda x:x.update(receipt_sha256="f"*64)),
            ("grant-scope",lambda x:x.update(actor_id=2))):
            h=self.history();ref,identity=h.accept();h.permit(ref,identity,mutate=mutate)
            with self.subTest(code=code):self.refused(code, h.reader)
        h=self.history();ref,identity=h.accept(finalize=False)
        final=h.body("publication-finalization")
        # A permit before finalization has no complete publication to admit.
        record=h.body("stream-permit");record.update(actor_id=1,session_id="s",nonce="n",expires_at="2026-09-16T00:01:00Z",
            outer_sha256=h.records[ref['sha256']]["identities"]["outer_sha256"],receipt_sha256=ref["sha256"],acceptance_id=identity,
            finalization={"type":"publication-finalization","sha256":"f"*64},head=h.last_head,grant=h.grant)
        h.event(record,identity);h.head()
        self.refused("missing-or-forward-reference", h.reader)

    def test_actual_json_parse_counts_and_retained_state(self):
        h=self.history();h.accept();original=json.loads;counts={"carrier":0,"signed_body":0,"other":0}
        def observe(raw,*args,**kwargs):
            value=original(raw,*args,**kwargs)
            key="carrier" if isinstance(value,dict) and "payloadType" in value else "signed_body" if isinstance(value,dict) and "predicateType" in value else "other"
            counts[key]+=1;return value
        with mock.patch("json.loads",side_effect=observe):reader=h.reader();reader.finish()
        self.assertEqual(counts["carrier"],len(h.envelopes))
        self.assertEqual(counts["signed_body"],len(h.envelopes))
        # Native-result and producer-ledger parses are separately visible, not hidden.
        self.assertEqual(counts["other"],1+len(h.native)+len(h.producer.splitlines()))
        # Only typed projections survive: evidence keeps its RETAIN fields, a
        # journaled event or journal entry keeps its type alone, and no body bytes remain.
        for identity,node in reader.nodes.items():
            kind=node["type"]
            with self.subTest(kind=kind):
                self.assertNotIsInstance(node["value"],(bytes,bytearray))
                if kind in RETAIN: self.assertEqual(set(node["value"])-{"type"},set(RETAIN[kind]))
                elif kind in EVENTS or kind=="journal-entry": self.assertEqual(dict(node["value"]),{"type":kind})
        self.assertEqual(len(reader.decisions),1)


class HistoryFixtureTests(unittest.TestCase):
    """The committed positive history and its recorded unsigned hostile mutations."""
    @classmethod
    def setUpClass(cls):
        from test_checkpoint_authority_records import tools
        cls.tools=tools()
        cls.history=fixture.load_history()
        cls.hostile=json.loads(fixture.HOSTILE_PATH.read_bytes())

    def test_committed_history_replays_to_its_expected_head(self):
        global REPLAYED
        reader=fixture.replay_history(self.history,self.tools,with_freshness=True)
        result=reader.finish(presence={(sha,role):True for sha,_ in reader.copies for role in ("primary","recovery")})
        expected=self.history["expected"]
        self.assertTrue(result["complete"])
        for key in ("records","bytes","head_sha256","policy_history","decisions","historical_permits","cancelled"):
            self.assertEqual(result[key],expected[key],key)
        self.assertEqual([row["acceptance_id"] for row in result["accepted"]],expected["accepted"])
        self.assertEqual([row["current_eligibility"] for row in result["accepted"]],["eligible"]*len(expected["accepted"]))
        self.assertEqual(fixture.replay_history(self.history,self.tools).finish()["accepted"][0]["current_eligibility"],"unknown")
        REPLAYED={"history_sha256":hashlib.sha256(fixture.HISTORY_PATH.read_bytes()).hexdigest(),
            **{key:result[key] for key in ("records","bytes","head_sha256","policy_history","decisions","historical_permits")},
            "accepted":[row["acceptance_id"] for row in result["accepted"]],
            "hostile_refused":len(self.hostile["cases"]),
            "current_eligibility":[row["current_eligibility"] for row in result["accepted"]]}

    def test_every_recorded_hostile_mutation_refuses_with_its_recorded_code(self):
        self.assertEqual(self.hostile["schema"],fixture.HOSTILE_SCHEMA)
        self.assertEqual([row["id"] for row in self.hostile["cases"]],[row["id"] for row in fixture.HOSTILE_MUTATIONS])
        for case in self.hostile["cases"]:
            with self.subTest(case=case["id"]), self.assertRaises(Refusal) as caught:
                fixture.replay_history(self.history,self.tools,case,with_freshness=True).finish()
            self.assertEqual((caught.exception.code,caught.exception.stage),(case["code"],case["stage"]),case["id"])
        codes={row["id"]:row["code"] for row in self.hostile["cases"]}
        self.assertEqual(codes["truncated-head"],"history-incomplete")
        self.assertEqual(codes["foreign-scope"],"foreign-scope")
        self.assertEqual(codes["stale-head"],"head-stale")
        self.assertEqual(codes["rollback-below-floor"],"head-rollback")
        self.assertEqual(codes["forged-decision-tail"],"head-rollback")
        self.assertEqual(codes["foreign-root"],"bootstrap-required")
        self.assertEqual(codes["duplicate-journal-entry"],"duplicate-record")
        self.assertEqual(codes["tampered-signature"],"signature-invalid")
        self.assertEqual(codes["omitted-journal-entry"],"event-not-journaled")

    def test_history_carries_no_private_material_and_synthetic_native_only(self):
        raw=fixture.HISTORY_PATH.read_bytes()
        self.assertNotIn(b"PRIVATE KEY",raw)
        self.assertIn("no native command ran",self.history["note"])
        for row in self.history["native"].values():
            value=json.loads(fixture.unb64(row["result"]))
            self.assertEqual(value["schema"],"checkpoint-authority-native-result/v1")


class WireTests(unittest.TestCase):
    def test_private_absence_fixed_headers_and_disabled_capabilities(self):
        self.assertEqual(wire.unavailable("request",authorized=False,exists=True),wire.unavailable("request",authorized=True,exists=False))
        for name in ("frontier","resolution","public-discovery"):
            status,data=wire.capability(name,"request");self.assertEqual(status,501);wire.parse("disabled",data)
        with self.assertRaisesRegex(Refusal,"capability-name"):wire.capability("lookup","request")
        self.assertEqual(wire.binary_headers("a"*64)["Cache-Control"],"private, no-store")
        self.assertEqual(wire.binary_headers("a"*64)["Content-Type"],"application/octet-stream")
        self.assertNotIn("Location",wire.binary_headers("a"*64))
        with self.assertRaises(Refusal):wire.binary_headers("https://provider.test/object")

    def test_inventory_bounds_and_control_caps(self):
        value={"protocol":"checkpoint-authority/v1","environment":"test","service":"service","scope":{"repository_id":1,"run_id":"run"},"request_id":"request",
            "inventory_sha256":"f"*64,"cursor":None,"next_cursor":None,"head":{"type":"authority-head","sha256":"f"*64},"items":[]}
        for i in range(100):
            value["items"].append({"acceptance_id":format(i,"064x"),"identities":{"snapshot_id":"a"*64,"controller_manifest_sha256":"b"*64,"outer_sha256":"c"*64},"receipt_sha256":"d"*64,"finalization_sha256":"e"*64})
        wire.parse("inventory",canonical(value,limit=wire.INVENTORY_BYTES))
        value["items"].append(dict(value["items"][-1],acceptance_id="f"*64))
        with self.assertRaisesRegex(Refusal,"schema-count"):wire.parse("inventory",canonical(value,limit=wire.INVENTORY_BYTES))
        value["items"].pop();value["items"][0],value["items"][1]=value["items"][1],value["items"][0]
        with self.assertRaisesRegex(Refusal,"inventory-order"):wire.parse("inventory",canonical(value,limit=wire.INVENTORY_BYTES))
        for kind,size in (("inventory",wire.INVENTORY_BYTES),("status",65536),("lookup",65536),("download-grant",65536)):
            with self.subTest(kind=kind),self.assertRaisesRegex(Refusal,"byte-limit"):wire.parse(kind,b" "*(size+1))
        with self.assertRaisesRegex(Refusal,"wire-type"):wire.parse("frontier",b"{}")
        with self.assertRaisesRegex(Refusal,"noncanonical-json"):wire.parse("status",b'{ "request_id":"r"}')

    def test_status_binding_and_grant_expiry_are_exact(self):
        common={"protocol":"checkpoint-authority/v1","environment":"test","service":"service","scope":{"repository_id":1,"run_id":"run"},"request_id":"request"}
        status={**common,"acceptance_id":"a"*64,"state":"eligible","head":{"type":"authority-head","sha256":"f"*64},"code":"eligible"}
        wire.parse("status",canonical(status))
        for state,code in (("eligible","denied"),("denied","publication-incomplete"),("unavailable","eligible")):
            with self.subTest(state=state,code=code),self.assertRaisesRegex(Refusal,"status-binding"):
                wire.parse("status",canonical({**status,"state":state,"code":code}))
        wire.parse("status",canonical({**status,"state":"unavailable","code":"freshness-unavailable"}))
        grant={**common,"grant_id":"g","actor_id":1,"session_id":"s","acceptance_id":"a"*64,"outer_sha256":"b"*64,"receipt_sha256":"c"*64,
            "issued_at":"2026-09-16T00:00:00Z","expires_at":"2026-09-16T00:01:00Z","head":{"type":"authority-head","sha256":"f"*64}}
        wire.parse("download-grant",canonical(grant))
        for expiry in ("2026-09-16T00:01:01Z","2026-09-16T00:00:00Z"):
            with self.subTest(expiry=expiry),self.assertRaisesRegex(Refusal,"grant-expiry"):
                wire.parse("download-grant",canonical({**grant,"expires_at":expiry}))
        self.assertEqual(set(wire.RESULTS),{"historical","publication","current_eligibility"})
