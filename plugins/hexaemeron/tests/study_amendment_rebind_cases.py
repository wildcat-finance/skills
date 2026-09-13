"""Study-amendment rebind cases loaded by ``test_hexctl``.

``test_hexctl.py`` is a path the promise-machine inventory reads under its
256 KiB bound, so these cases live beside it, as the host-identity and
replacement-object cases do, and ``test_hexctl`` binds them into
``StudyAmendmentRebindTests``.
"""


class StudyAmendmentRebindCases:
    """A study amendment rebinds or displaces each effective runbook amendment."""

    def ledger(self):
        path = os.path.join(self.target, ".hexaemeron", "ledger.jsonl")
        with open(path, encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]

    def packet_amendments(self):
        """The runbook packet the next Mason or Warden brief carries."""
        controller = hexctl_module()
        state_path = os.path.join(self.target, ".hexaemeron", "state.json")
        with open(state_path, encoding="utf-8") as handle:
            state = json.load(handle)
        runbook = controller.receipted_source(self.target, state, "runbook")
        study = controller.receipted_source(self.target, state, "study")
        step = controller.current_step(state)
        return controller.source_runbook_step(
            runbook,
            step,
            current_study_sha256=study["sha256"],
            study_amendments=study["receipt"].get("amendments"),
        )["amendments"]

    def receipt_runbook_amendment(self):
        study_text, runbook_text = self.to_runbook_amendable_steps()
        suffix = self.runbook_amendment()
        candidate = self.write("runbook-candidate.md", runbook_text + suffix)
        self.run_ctl("amend", "runbook", "--artifact", candidate)
        return study_text, runbook_text, suffix

    def test_unrelated_study_amendments_keep_a_runbook_amendment_bound(self):
        study_text, _, suffix = self.receipt_runbook_amendment()
        amendment_sha256 = hashlib.sha256(suffix.encode()).hexdigest()
        digest_0 = self.state()["receipts"]["study"]["sha256"]
        before = self.next_json()["brief"]["runbook_step"]
        self.assertEqual(len(before["amendments"]), 1)
        self.assertEqual(before["amendments"][0]["markdown"], suffix)

        first_text = study_text + self.amendment()
        first = self.run_ctl(
            "amend", "study", "--artifact", self.write("study-1.md", first_text)
        )
        digest_1 = hashlib.sha256(first_text.encode()).hexdigest()
        second_text = first_text + self.amendment(
            date="2026-08-23", what="A second baseline fact changed."
        )
        second = self.run_ctl(
            "amend", "study", "--artifact", self.write("study-2.md", second_text)
        )
        digest_2 = hashlib.sha256(second_text.encode()).hexdigest()
        self.assertEqual(self.state()["receipts"]["study"]["sha256"], digest_2)

        after = self.next_json()["brief"]["runbook_step"]
        self.assertEqual(len(after["amendments"]), 1)
        self.assertEqual(after["amendments"], before["amendments"])
        self.assertEqual(after["markdown"], before["markdown"])
        self.assertEqual(after["effective_sha256"], before["effective_sha256"])
        self.assertIn("fiat-v2.0.0", after["markdown"])

        events = [entry for entry in self.ledger() if entry["event"] == "amend:study"]
        self.assertEqual(len(events), 2)
        self.assertEqual(
            [entry["data"]["runbook_rebinds"] for entry in events],
            [
                [
                    {
                        "amendment_sha256": amendment_sha256,
                        "from_study_sha256": digest_0,
                        "to_study_sha256": digest_1,
                        "decision": "retained",
                    }
                ],
                [
                    {
                        "amendment_sha256": amendment_sha256,
                        "from_study_sha256": digest_1,
                        "to_study_sha256": digest_2,
                        "decision": "retained",
                    }
                ],
            ],
        )
        history = self.state()["receipts"]["study"]["amendments"]
        self.assertEqual(
            [entry["runbook_rebinds"] for entry in history],
            [entry["data"]["runbook_rebinds"] for entry in events],
        )
        line = (
            f"runbook amendment {amendment_sha256} retained: "
            "steps [1, 2]; fields [Exit]"
        )
        for result in (first, second):
            self.assertIn("study amended:", result.stdout)
            self.assertIn(line, result.stdout)
            self.assertIn("runbook rebinds: 1 retained, 0 displaced", result.stdout)
            self.assertNotIn("fiat-v2.0.0", result.stdout)
        self.run_ctl("verify")

        # The study's one budget: `amend study` over the 500-amendment cap.
        controller = hexctl_module()
        cap = controller.AMENDMENT_HISTORY_MAX
        loaded = HexctlCase(methodName="runTest")
        loaded.setUp()
        try:
            fixture_ms = self.amend_study_twice_ms(loaded, runbook_amendments=cap)
            history = loaded.state()["receipts"]["study"]["amendments"]
            self.assertEqual(
                [
                    (len(entry["runbook_rebinds"]),
                     {record["decision"] for record in entry["runbook_rebinds"]})
                    for entry in history
                ],
                [(cap, {"retained"}), (cap, {"retained"})],
            )
            self.assertIn(
                f"runbook rebinds: {cap} retained, 0 displaced", loaded.last_stdout
            )
            loaded.run_ctl("verify")
            self.assertEqual(
                len(loaded.next_json()["brief"]["runbook_step"]["amendments"]), cap
            )
        finally:
            loaded.tearDown()
        empty = HexctlCase(methodName="runTest")
        empty.setUp()
        try:
            baseline_ms = self.amend_study_twice_ms(empty, runbook_amendments=0)
            self.assertIn("runbook rebinds: none", empty.last_stdout)
        finally:
            empty.tearDown()

        # The same loop in process: the loop alone, without start-up or verify.
        digests = [hashlib.sha256(f"study {n}".encode()).hexdigest() for n in range(3)]
        verdicts = [
            {"step": 1, "entry": "holds", "exit": "holds"},
            {"step": 2, "entry": "holds", "exit": "holds"},
        ]
        runbook_history = [
            {
                "amendment_sha256": hashlib.sha256(f"runbook {n}".encode()).hexdigest(),
                "study_sha256": digests[0],
                "steps_touched": [1, 2],
                "replacement_fields": ["Exit"],
            }
            for n in range(cap)
        ]
        started = time.perf_counter()
        first_rebinds = controller._runbook_rebinds(
            runbook_history, [], digests[0], digests[1], verdicts
        )
        study_history = [
            {
                "prior_sha256": digests[0],
                "new_sha256": digests[1],
                "step_verdicts": verdicts,
                "runbook_rebinds": first_rebinds,
            }
        ]
        second_rebinds = controller._runbook_rebinds(
            runbook_history, study_history, digests[1], digests[2], verdicts
        )
        index = controller._runbook_rebind_index(study_history)
        resolved = [
            controller.effective_study_sha256(item, None, index=index)
            for item in runbook_history
        ]
        loop_ms = (time.perf_counter() - started) * 1000
        self.assertEqual(len(first_rebinds), cap)
        self.assertEqual(len(second_rebinds), cap)
        self.assertEqual(set(resolved), {digests[1]})
        measured = (
            f"metron: amend study over {cap} effective runbook amendments; "
            f"real command {fixture_ms:.1f} ms against {baseline_ms:.1f} ms "
            f"with none; in-process rebind loop {loop_ms:.1f} ms; budget 1000 ms"
        )
        self.assertLess(loop_ms, 1000, measured)
        self.assertLess(fixture_ms - baseline_ms, 1000, measured)
        print(measured)

    def amend_study_twice_ms(self, case, *, runbook_amendments):
        """Two holding study amendments over N effective runbook amendments;
        return the faster command's wall time in ms."""
        study_text, runbook_text = case.to_runbook_amendable_steps()
        if runbook_amendments:
            controller = hexctl_module()
            state_path = os.path.join(case.target, ".hexaemeron", "state.json")
            with open(state_path, encoding="utf-8") as handle:
                state = json.load(handle)
            study_sha256 = state["receipts"]["study"]["sha256"]
            data = runbook_text.encode("utf-8")
            history = []
            for n in range(runbook_amendments):
                day = f"2026-{(n // 28) % 12 + 1:02d}-{n % 28 + 1:02d}"
                suffix = case.runbook_amendment(
                    date=day,
                    what=f"Complete replacement Exit: Run `fiat-v{n}.0.0`.",
                ).encode("utf-8")
                start = len(data)
                data += suffix
                history.append(
                    {
                        "date": day,
                        "prior_sha256": hashlib.sha256(data[:start]).hexdigest(),
                        "new_sha256": hashlib.sha256(data).hexdigest(),
                        "amendment_sha256": hashlib.sha256(suffix).hexdigest(),
                        "amendment_start": start,
                        "amendment_end": len(data),
                        "steps_touched": [1, 2],
                        "step_verdicts": [
                            {"step": 1, "entry": "holds", "exit": "holds"},
                            {"step": 2, "entry": "holds", "exit": "holds"},
                        ],
                        "replacement_fields": ["Exit"],
                        "study_sha256": study_sha256,
                    }
                )
            with open(os.path.join(case.target, "runbook.md"), "wb") as handle:
                handle.write(data)
            state["receipts"]["runbook"]["amendments"] = history
            state["receipts"]["runbook"]["sha256"] = history[-1]["new_sha256"]
            controller.commit(
                case.target, state, "fixture:effective-runbook-amendments", {}
            )
            case.run_ctl("verify")
        timings = []
        text = study_text
        for number, date in enumerate(("2026-08-22", "2026-08-23"), 1):
            text = text + case.amendment(
                date=date, what=f"Baseline fact {number} was corrected."
            )
            candidate = case.write(f"study-{number}.md", text)
            started = time.perf_counter()
            result = case.run_ctl("amend", "study", "--artifact", candidate)
            timings.append((time.perf_counter() - started) * 1000)
            case.last_stdout = result.stdout
        return min(timings)

    def test_a_related_study_amendment_displaces_and_keeps_the_step_blocked(self):
        study_text, runbook_text, suffix = self.receipt_runbook_amendment()
        amendment_sha256 = hashlib.sha256(suffix.encode()).hexdigest()
        digest_0 = self.state()["receipts"]["study"]["sha256"]
        self.assertEqual(len(self.next_json()["brief"]["runbook_step"]["amendments"]), 1)

        related_text = study_text + self.amendment(
            "Step 1: entry holds; exit broken. Step 2: entry holds; exit holds."
        )
        result = self.run_ctl(
            "amend", "study", "--artifact", self.write("study-1.md", related_text)
        )
        digest_1 = hashlib.sha256(related_text.encode()).hexdigest()
        record = {
            "amendment_sha256": amendment_sha256,
            "from_study_sha256": digest_0,
            "to_study_sha256": digest_1,
            "decision": "displaced",
        }
        self.assertEqual(self.ledger()[-1]["event"], "amend:study")
        self.assertEqual(self.ledger()[-1]["data"]["runbook_rebinds"], [record])
        self.assertEqual(
            self.state()["receipts"]["study"]["amendments"][-1]["runbook_rebinds"],
            [record],
        )
        self.assertIn(
            f"runbook amendment {amendment_sha256} displaced: steps [1, 2]; "
            "fields [Exit]",
            result.stdout,
        )
        self.assertIn("runbook rebinds: 0 retained, 1 displaced", result.stdout)

        self.assertEqual(self.packet_amendments(), [])
        blocked = self.next_json()
        self.assertEqual((blocked["do"], blocked["agent"], blocked["brief"]),
                         ("blocked", None, {}))
        self.assertIn("exit broken", blocked["reason"])
        proc = self.run_ctl(
            "done", "implement", "--branch", self.step_branch(1),
            "--commit", "abc", expect=2,
        )
        self.assertIn("study amendment blocks step 1", proc.stderr)
        self.run_ctl("verify")

        repair_suffix = self.runbook_amendment(
            date="2026-08-26", what="Complete replacement Exit: Run `fiat-v3.0.0`."
        )
        repair = self.write("repair.md", runbook_text + suffix + repair_suffix)
        self.run_ctl("amend", "runbook", "--artifact", repair)
        directive = self.next_json()
        self.assertEqual((directive["do"], directive["agent"]), ("implement", "mason"))
        carried = directive["brief"]["runbook_step"]["amendments"]
        self.assertEqual([item["markdown"] for item in carried], [repair_suffix])
        self.assertEqual(carried[0]["study_sha256"], digest_1)
        self.assertNotIn("fiat-v2.0.0", directive["brief"]["runbook_step"]["markdown"])
        self.run_ctl("verify")

    def test_a_repeated_runbook_amendment_takes_one_rebind_record(self):
        """Identical bytes receipted twice share a digest and one decision.

        Without the fix the second study amendment wrote two records under one
        digest, the post-commit verify refused them as one amendment rebound
        twice, and the run stayed pending with no recovery.
        """
        study_text, runbook_text, suffix = self.receipt_runbook_amendment()
        amendment_sha256 = hashlib.sha256(suffix.encode()).hexdigest()
        self.run_ctl(
            "amend", "runbook", "--artifact",
            self.write("runbook-repeat.md", runbook_text + suffix + suffix),
        )
        history = self.state()["receipts"]["runbook"]["amendments"]
        self.assertEqual(
            [item["amendment_sha256"] for item in history],
            [amendment_sha256, amendment_sha256],
        )
        digest_0 = self.state()["receipts"]["study"]["sha256"]

        first_text = study_text + self.amendment()
        result = self.run_ctl(
            "amend", "study", "--artifact", self.write("study-1.md", first_text)
        )
        digest_1 = hashlib.sha256(first_text.encode()).hexdigest()
        record = {
            "amendment_sha256": amendment_sha256,
            "from_study_sha256": digest_0,
            "to_study_sha256": digest_1,
            "decision": "retained",
        }
        self.assertEqual(
            self.state()["receipts"]["study"]["amendments"][-1]["runbook_rebinds"],
            [record],
        )
        self.assertEqual(self.ledger()[-1]["data"]["runbook_rebinds"], [record])
        self.assertIn("runbook rebinds: 1 retained, 0 displaced", result.stdout)
        self.run_ctl("verify")
        carried = self.next_json()["brief"]["runbook_step"]["amendments"]
        self.assertEqual([item["markdown"] for item in carried], [suffix, suffix])
        self.assertEqual({item["study_sha256"] for item in carried}, {digest_0})
        self.assertFalse(
            os.path.exists(
                os.path.join(self.target, ".hexaemeron", "study-amendment-pending.json")
            )
        )

    def test_a_touched_step_outside_the_verdicts_counts_as_holding(self):
        """A study amendment carries no verdict for a completed step, so a
        runbook amendment touching one is judged on its unbuilt steps alone."""
        controller = hexctl_module()
        digests = [hashlib.sha256(f"study {n}".encode()).hexdigest() for n in range(2)]
        history = [
            {
                "amendment_sha256": hashlib.sha256(b"runbook 0").hexdigest(),
                "study_sha256": digests[0],
                "steps_touched": [1, 2],
                "replacement_fields": ["Exit"],
            }
        ]
        for exit_verdict, decision in (("holds", "retained"), ("broken", "displaced")):
            records = controller._runbook_rebinds(
                history, [], digests[0], digests[1],
                [{"step": 2, "entry": "holds", "exit": exit_verdict}],
            )
            self.assertEqual([item["decision"] for item in records], [decision])

    def test_a_completed_touched_step_is_judged_on_its_unbuilt_steps(self):
        """End to end: a runbook amendment touching steps 1 and 2 survives step
        1's completion and is then judged on step 2's verdict alone."""
        study_text, runbook_text, suffix = self.receipt_runbook_amendment()
        amendment_sha256 = hashlib.sha256(suffix.encode()).hexdigest()
        self.run_ctl("record", "security_suite", '"waived: prose-only repo"')
        self.finish_step(1)
        self.assertEqual(self.next_json()["brief"]["runbook_step"]["number"], 2)
        digest_0 = self.state()["receipts"]["study"]["sha256"]

        holding_text = study_text + self.amendment(
            "Step 2: entry holds; exit holds.", touched="Step 2."
        )
        result = self.run_ctl(
            "amend", "study", "--artifact", self.write("study-1.md", holding_text)
        )
        digest_1 = hashlib.sha256(holding_text.encode()).hexdigest()
        self.assertEqual(
            self.state()["receipts"]["study"]["amendments"][-1]["runbook_rebinds"],
            [{
                "amendment_sha256": amendment_sha256,
                "from_study_sha256": digest_0,
                "to_study_sha256": digest_1,
                "decision": "retained",
            }],
        )
        self.assertIn(
            f"runbook amendment {amendment_sha256} retained: steps [1, 2]; "
            "fields [Exit]",
            result.stdout,
        )
        self.run_ctl("verify")
        directive = self.next_json()
        self.assertEqual((directive["do"], directive["agent"]), ("implement", "mason"))
        carried = directive["brief"]["runbook_step"]["amendments"]
        self.assertEqual([item["markdown"] for item in carried], [suffix])
        self.assertIn("fiat-v2.0.0", directive["brief"]["runbook_step"]["markdown"])

        broken_text = holding_text + self.amendment(
            "Step 2: entry holds; exit broken.",
            date="2026-08-23", what="A second baseline fact changed.", touched="Step 2.",
        )
        result = self.run_ctl(
            "amend", "study", "--artifact", self.write("study-2.md", broken_text)
        )
        digest_2 = hashlib.sha256(broken_text.encode()).hexdigest()
        self.assertEqual(
            self.state()["receipts"]["study"]["amendments"][-1]["runbook_rebinds"],
            [{
                "amendment_sha256": amendment_sha256,
                "from_study_sha256": digest_1,
                "to_study_sha256": digest_2,
                "decision": "displaced",
            }],
        )
        self.assertIn("runbook rebinds: 0 retained, 1 displaced", result.stdout)
        self.run_ctl("verify")
        self.assertEqual(self.packet_amendments(), [])
        self.assertEqual(self.next_json()["do"], "blocked")

    def test_a_legacy_study_amendment_without_rebinds_still_verifies_and_drops(self):
        study_text, _, suffix = self.receipt_runbook_amendment()
        self.run_ctl(
            "amend", "study", "--artifact",
            self.write("study-1.md", study_text + self.amendment()),
        )
        self.assertEqual(len(self.next_json()["brief"]["runbook_step"]["amendments"]), 1)

        state_path = os.path.join(self.target, ".hexaemeron", "state.json")
        with open(state_path, encoding="utf-8") as handle:
            state = json.load(handle)
        entry = state["receipts"]["study"]["amendments"][-1]
        self.assertIn("runbook_rebinds", entry)
        del entry["runbook_rebinds"]
        hexctl_module().commit(
            self.target, state, "fixture:legacy-study-amendment", {}
        )

        self.run_ctl("verify")
        self.assertEqual(self.packet_amendments(), [])
        directive = self.next_json()
        self.assertEqual((directive["do"], directive["agent"]), ("implement", "mason"))
        self.assertEqual(directive["brief"]["runbook_step"]["amendments"], [])
        self.assertNotIn("fiat-v2.0.0", directive["brief"]["runbook_step"]["markdown"])


def build_study_amendment_rebind_cases(context):
    """Bind the cases to the already-loaded controller test harness."""
    globals().update(
        {name: value for name, value in context.items() if not name.startswith("__")}
    )
    return (StudyAmendmentRebindCases,)
