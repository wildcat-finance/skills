"""The Ephoros signal lint catches its three rules and leaves the rest alone.

The neighbours matter as much as the specimens. This marketplace writes a
hundred f-string `print` calls, which are command-line output rather than
telemetry, and takes means of sentence lengths and layout positions, which are
not durations.
"""

import importlib.util
import io
import tempfile
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "ephoros" / "scripts" / "ephoros.py"
ALERT_FIXTURES = ROOT / "tests" / "fixtures" / "ephoros" / "alert-rules"
TELEMETRY_FIXTURES = ROOT / "tests" / "fixtures" / "ephoros" / "telemetry-keys"

spec = importlib.util.spec_from_file_location("ephoros_lint", SCRIPT)
ephoros = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ephoros)


def codes(source):
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "sample.py"
        path.write_text(source, encoding="utf-8")
        return sorted(f.code for f in ephoros.check(path))


def yaml_findings(source, name="sample.yaml"):
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / name
        path.write_text(source, encoding="utf-8")
        return ephoros.check(path)


class LogMessages(unittest.TestCase):
    def test_it_flags_an_f_string_message(self):
        self.assertIn("E001", codes(
            "import logging\nn = 3\nlogging.info(f'harvested {n} blocks')\n"))

    def test_it_flags_percent_formatting(self):
        self.assertIn("E001", codes("log = get()\nlog.warning('failed %s' % name)\n"))

    def test_it_flags_dot_format(self):
        self.assertIn("E001", codes("logger = get()\nlogger.error('at {}'.format(x))\n"))

    def test_it_allows_a_stable_name_with_fields(self):
        self.assertEqual([], codes(
            "logger = get()\nlogger.info('harvest_done', extra={'blocks': n})\n"))

    def test_it_ignores_print_which_is_not_telemetry(self):
        self.assertEqual([], codes("n = 3\nprint(f'harvested {n} blocks')\n"))

    def test_it_ignores_an_unrelated_object_with_an_info_method(self):
        self.assertEqual([], codes(
            "class Report:\n    def info(self, text):\n        return text\n\n"
            "Report().info(f'value {x}')\n"))


class MetricLabels(unittest.TestCase):
    def test_it_flags_an_address_label_as_e005_since_the_subset_moved(self):
        self.assertEqual(["E005"], codes(
            "h = Histogram('d', labels={'address': a, 'venue': v})\n"))

    def test_it_flags_a_hash_label_in_a_list(self):
        self.assertIn("E002", codes("c = Counter('c', labelnames=['tx_hash', 'chain'])\n"))

    def test_it_flags_a_request_id_tag(self):
        self.assertIn("E002", codes("m = metric('m', tags=['request_id'])\n"))

    def test_it_allows_bounded_labels(self):
        self.assertEqual([], codes(
            "h = Histogram('d', labelnames=['route', 'status_class', 'venue'])\n"))


class Durations(unittest.TestCase):
    def test_it_flags_a_mean_duration(self):
        self.assertIn("E003", codes("import statistics\nmean_latency = statistics.mean(samples)\n"))

    def test_it_flags_the_sum_over_len_idiom_on_durations(self):
        self.assertIn("E003", codes("avg = sum(durations) / len(durations)\n"))

    def test_it_allows_a_mean_of_something_that_is_not_a_duration(self):
        self.assertEqual([], codes("mean = sum(lengths) / len(lengths)\n"))

    def test_it_allows_a_mean_of_layout_positions(self):
        self.assertEqual([], codes("order = sum(positions) / len(positions)\n"))


class TelemetryKeys(unittest.TestCase):
    def test_it_flags_an_address_label_in_the_constructor_style(self):
        findings = ephoros.check(TELEMETRY_FIXTURES / "metric-label-constructor.py")
        self.assertEqual(["E005"], [finding.code for finding in findings])

    def test_it_flags_the_labels_instance_call_style(self):
        findings = ephoros.check(TELEMETRY_FIXTURES / "metric-label-instance.py")
        self.assertEqual(["E005"], [finding.code for finding in findings])

    def test_it_flags_a_forty_hex_literal_label_value(self):
        findings = ephoros.check(TELEMETRY_FIXTURES / "metric-label-hex-literal.py")
        self.assertEqual(["E005"], [finding.code for finding in findings])

    def test_it_flags_a_forty_hex_literal_in_a_constructor_label_set(self):
        self.assertEqual(["E005"], codes(
            "m = metric('m', tags=['0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef'])\n"))

    def test_it_flags_an_address_shaped_dashboard_key(self):
        findings = ephoros.check(TELEMETRY_FIXTURES / "dashboard-key.py")
        self.assertEqual(["E005"], [finding.code for finding in findings])

    def test_it_flags_an_address_shaped_log_index_key(self):
        findings = ephoros.check(TELEMETRY_FIXTURES / "log-index-key.py")
        self.assertEqual(["E005"], [finding.code for finding in findings])

    def test_it_flags_an_address_index_argument(self):
        findings = ephoros.check(TELEMETRY_FIXTURES / "log-index-argument.py")
        self.assertEqual(["E005"], [finding.code for finding in findings])

    def test_it_allows_an_address_in_an_events_fields(self):
        self.assertEqual([], ephoros.check(TELEMETRY_FIXTURES / "event-fields.py"))

    def test_it_allows_an_address_in_a_message_argument(self):
        self.assertEqual([], ephoros.check(TELEMETRY_FIXTURES / "message-argument.py"))

    def test_it_ignores_print_which_is_not_telemetry(self):
        self.assertEqual([], ephoros.check(TELEMETRY_FIXTURES / "print.py"))

    def test_an_address_key_on_an_unnamed_store_does_not_fire(self):
        self.assertEqual([], codes("cache[wallet_address] = market\n"))

    def test_a_wallet_address_label_yields_e005_and_not_e002(self):
        self.assertEqual(["E005"], codes(
            "c = Counter('c', labelnames=['wallet_address'])\n"))

    def test_a_hash_named_label_keeps_e002(self):
        self.assertEqual(["E002"], codes("c = Counter('c', labelnames=['tx_hash'])\n"))

    def test_a_reasoned_pragma_on_the_line_suppresses_e005(self):
        self.assertEqual([], codes(
            "c.labels(wallet_address=a).inc()"
            "  # ephoros: allow one aggregate treasury row\n"))

    def test_a_reasoned_pragma_on_the_line_above_suppresses_e005(self):
        self.assertEqual([], codes(
            "# ephoros: allow one aggregate treasury row\n"
            "c.labels(wallet_address=a).inc()\n"))

    def test_a_bare_pragma_does_not_suppress_e005(self):
        self.assertIn("E005", codes(
            "c.labels(wallet_address=a).inc()  # ephoros: allow\n"))

    def test_slash_pragma_text_in_a_python_string_does_not_suppress(self):
        self.assertEqual(["E005"], codes(
            's = "// ephoros: allow tracked elsewhere"\n'
            "c.labels(wallet_address=a).inc()\n"))

    def test_a_slash_pragma_mentioned_mid_comment_does_not_suppress(self):
        self.assertEqual(["E005"], codes(
            "c.labels(wallet_address=a).inc()"
            "  # see // ephoros: allow foo for the shape\n"))


def ts_codes(source, name="sample.ts"):
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / name
        path.write_text(source, encoding="utf-8")
        return sorted(f.code for f in ephoros.check(path))


class TypeScriptTelemetryKeys(unittest.TestCase):
    def test_it_flags_an_address_key_on_a_metric_label_set(self):
        findings = ephoros.check(TELEMETRY_FIXTURES / "metric-label-set.ts")
        self.assertEqual(["E005"], [finding.code for finding in findings])

    def test_it_flags_an_address_key_on_a_dashboard_structure(self):
        findings = ephoros.check(TELEMETRY_FIXTURES / "dashboard-key.ts")
        self.assertEqual(["E005"], [finding.code for finding in findings])

    def test_it_flags_an_address_key_on_a_log_index_position(self):
        findings = ephoros.check(TELEMETRY_FIXTURES / "log-index.ts")
        self.assertEqual(["E005"], [finding.code for finding in findings])

    def test_it_flags_a_camel_case_label_key_on_an_analytics_sink(self):
        self.assertEqual(["E005"], ts_codes(
            'analytics.track("deposit", { labels: { walletAddress: depositor } })\n'))

    def test_it_flags_a_forty_hex_literal_in_a_label_array(self):
        self.assertEqual(["E005"], ts_codes(
            'metrics.increment("m", '
            '{ tags: ["0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef"] })\n'))

    def test_it_flags_the_labels_instance_call_style(self):
        self.assertEqual(["E005"], ts_codes(
            "deposits.labels({ walletAddress: depositor }).inc()\n"))

    def test_it_flags_a_log_store_partitioned_by_address(self):
        self.assertEqual(["E005"], ts_codes("eventLog[walletAddress] = event\n"))

    def test_it_flags_a_string_literal_wallet_index(self):
        self.assertEqual(["E005"], ts_codes(
            "auditLog.write(event, { index: 'wallet_address' })\n"))

    def test_it_flags_a_forty_hex_literal_index(self):
        self.assertEqual(["E005"], ts_codes(
            "auditLog.write(event, "
            "{ index: '0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef' })\n"))

    def test_it_flags_the_camel_case_label_names_property(self):
        self.assertEqual(["E005"], ts_codes(
            'const c = new client.Counter({ name: "c", '
            'labelNames: ["wallet_address"] })\n'))

    def test_it_flags_an_optional_chained_metric_sink(self):
        self.assertEqual(["E005"], ts_codes(
            "metrics?.gauge('m', { tags: { walletAddress: w } })\n"))

    def test_it_flags_an_optional_chain_inside_a_sink_chain(self):
        self.assertEqual(["E005"], ts_codes(
            "sink?.metrics.gauge('m', { tags: { walletAddress: w } })\n"))

    def test_an_optional_chained_cache_key_does_not_fire(self):
        self.assertEqual([], ts_codes(
            "cache?.store[walletAddress] = market\n"))

    def test_it_flags_an_optional_chain_bracket_log_store(self):
        self.assertEqual(["E005"], ts_codes(
            "eventLog?.[walletAddress] = event\n"))

    def test_it_flags_an_optional_chain_bracket_dashboard_key(self):
        self.assertEqual(["E005"], ts_codes(
            "dashboards?.[walletAddress] = panel\n"))

    def test_it_flags_an_optional_chain_bracket_string_log_index(self):
        self.assertEqual(["E005"], ts_codes(
            "auditLog?.['walletAddress'].push(e)\n"))

    def test_an_optional_chain_bracket_on_an_unnamed_store_does_not_fire(self):
        self.assertEqual([], ts_codes("cache?.[walletAddress]\n"))

    def test_an_optional_chain_bracket_after_a_subscript_does_not_fire(self):
        self.assertEqual([], ts_codes(
            "ADS_REGISTRY[chainId]?.[marketAddress.toLowerCase()]\n"))

    def test_it_flags_a_template_literal_wallet_index(self):
        self.assertEqual(["E005"], ts_codes(
            "auditLog.write(e, { index: `wallet_address` })\n"))

    def test_an_interpolated_template_index_does_not_fire(self):
        self.assertEqual([], ts_codes(
            "auditLog.write(e, { index: `${walletAddress}` })\n"))

    def test_it_allows_a_query_key_array_carrying_an_address(self):
        self.assertEqual([], ephoros.check(TELEMETRY_FIXTURES / "query-key.ts"))

    def test_it_allows_a_storage_key_built_from_an_address(self):
        self.assertEqual([], ephoros.check(TELEMETRY_FIXTURES / "storage-key.ts"))

    def test_it_allows_a_logger_message_interpolating_an_address(self):
        self.assertEqual([], ephoros.check(TELEMETRY_FIXTURES / "logger-message.ts"))

    def test_it_ignores_console_output_which_is_not_telemetry(self):
        self.assertEqual([], ephoros.check(TELEMETRY_FIXTURES / "console-output.ts"))

    def test_an_address_key_on_an_unnamed_store_does_not_fire(self):
        self.assertEqual([], ts_codes("cache[walletAddress] = market\n"))

    def test_a_label_shaped_object_outside_a_telemetry_sink_does_not_fire(self):
        self.assertEqual([], ts_codes(
            "chip.render({ tags: { walletAddress: lender } })\n"))

    def test_a_reasoned_slash_pragma_on_the_line_suppresses_e005(self):
        self.assertEqual([], ts_codes(
            "eventLog[walletAddress] = event"
            "  // ephoros: allow one aggregate treasury row\n"))

    def test_a_reasoned_slash_pragma_on_the_line_above_suppresses_e005(self):
        self.assertEqual([], ts_codes(
            "// ephoros: allow one aggregate treasury row\n"
            "eventLog[walletAddress] = event\n"))

    def test_a_bare_slash_pragma_does_not_suppress_e005(self):
        self.assertEqual(["E005"], ts_codes(
            "eventLog[walletAddress] = event  // ephoros: allow\n"))

    def test_pragma_text_in_a_string_does_not_suppress(self):
        self.assertEqual(["E005"], ts_codes(
            'eventLog[walletAddress] = "// ephoros: allow tracked elsewhere"\n'))

    def test_pragma_text_in_a_template_does_not_suppress(self):
        self.assertEqual(["E005"], ts_codes(
            "const note = `// ephoros: allow tracked elsewhere`\n"
            "eventLog[walletAddress] = event\n"))

    def test_a_hash_pragma_does_not_suppress_in_typescript(self):
        self.assertEqual(["E005"], ts_codes(
            "// # ephoros: allow tracked elsewhere\n"
            "eventLog[walletAddress] = event\n"))

    def test_a_block_comment_pragma_does_not_suppress(self):
        self.assertEqual(["E005"], ts_codes(
            "/* // ephoros: allow smuggled reason */ "
            "eventLog[walletAddress] = event\n"))

    def test_a_block_comment_pragma_on_the_line_above_does_not_suppress(self):
        self.assertEqual(["E005"], ts_codes(
            "/* // ephoros: allow smuggled reason */\n"
            "eventLog[walletAddress] = event\n"))


class TypeScriptBoundaries(unittest.TestCase):
    def test_an_oversized_typescript_file_fails_visibly(self):
        source = "//" + "x" * ephoros.TYPESCRIPT_MAX_BYTES
        self.assertEqual(["E000"], ts_codes(source))

    def test_typescript_read_requests_only_the_cap_plus_one_byte(self):
        class RecordingReader(io.BytesIO):
            requested = None

            def read(self, size=-1):
                self.requested = size
                return super().read(size)

        reader = RecordingReader(b"/" * (ephoros.TYPESCRIPT_MAX_BYTES + 1))
        with mock.patch.object(Path, "open", return_value=reader), \
                mock.patch.object(Path, "read_bytes", side_effect=AssertionError):
            findings = ephoros.check(Path("bounded.ts"))
        self.assertEqual(["E000"], [finding.code for finding in findings])
        self.assertEqual(ephoros.TYPESCRIPT_MAX_BYTES + 1, reader.requested)

    def test_a_lexer_failure_reports_e000(self):
        self.assertEqual(["E000"], ts_codes("const s = `never terminated\n"))

    def test_a_pragma_cannot_suppress_a_lexer_failure(self):
        self.assertEqual(["E000"], ts_codes(
            "// ephoros: allow crafted reason\n"
            "const s = `never terminated\n"))

    def test_a_lexer_recursion_failure_fails_closed_per_file(self):
        with tempfile.TemporaryDirectory() as base:
            nested = Path(base) / "nested.ts"
            nested.write_text(
                "const s = " + "`${" * 600 + "0" + "}`" * 600 + "\n",
                encoding="utf-8")
            sibling = Path(base) / "sibling.ts"
            sibling.write_text("eventLog[walletAddress] = event\n",
                               encoding="utf-8")
            findings = [finding for path in ephoros.walk([base])
                        for finding in ephoros.check(path)]
            by_file = {Path(finding.path).name: finding for finding in findings}
            self.assertEqual("E000", by_file["nested.ts"].code)
            self.assertIn("recursion", by_file["nested.ts"].message)
            self.assertEqual("E005", by_file["sibling.ts"].code)

    def test_an_adversarial_dotted_chain_completes_with_zero_findings(self):
        # A whitespace-separated dotted chain that never reaches a bracket
        # once cost quadratic rescans (about a minute at this size); the
        # bracket-anchored scan reads it once and finds nothing.
        with tempfile.TemporaryDirectory() as base:
            specimen = Path(base) / "adversarial.ts"
            specimen.write_text("a . " * 25_000, encoding="utf-8")
            self.assertEqual([], ephoros.check(specimen))

    def test_a_deeply_nested_bracket_chain_completes_with_zero_findings(self):
        # Every bracket in a[a[a[...]]] carries a chain, and the old
        # per-bracket forward scan to its closer re-read the fully
        # overlapping nested spans quadratically: 28s at N=16000, hours at
        # the 1 MiB cap. One linear stack pass now matches every bracket up
        # front, and the unnamed chain yields nothing even at cap scale.
        depth = 250_000
        with tempfile.TemporaryDirectory() as base:
            specimen = Path(base) / "nested.ts"
            specimen.write_text("a[" * depth + "x" + "]" * depth,
                                encoding="utf-8")
            self.assertEqual([], ephoros.check(specimen))

    def test_a_sink_named_labels_nest_keeps_its_single_exact_finding(self):
        # Once every nested chain names `.labels`, the cheap unnamed-chain
        # gate stops short-circuiting and each fully overlapping span paid
        # a full-width comma split and key read: 28 seconds at this depth,
        # about 77 minutes at the 1 MiB cap. The per-file position tables
        # keep the walk near-linear, and only the innermost span carries
        # the address-shaped key.
        depth = 8192
        source = ("// nested labels specimen\n"
                  + "m.labels(" * depth + "{walletAddress: 1}" + ")" * depth)
        with tempfile.TemporaryDirectory() as base:
            specimen = Path(base) / "labels.ts"
            specimen.write_text(source, encoding="utf-8")
            findings = ephoros.check(specimen)
        self.assertEqual(["E005"], [finding.code for finding in findings])
        self.assertEqual([2], [finding.line for finding in findings])
        self.assertIn("metric label `walletAddress`", findings[0].message)

    def test_a_sink_named_logger_nest_repeats_the_index_finding_per_span(self):
        # Each of the nested `logger.info` spans contains the one `index:`
        # property, so each span reports it, exactly as the old per-span
        # scans did -- the findings repeat while the work does not (the
        # same shape cost 7.3 seconds at this depth and quadratically more
        # beyond it).
        depth = 8192
        source = ("// nested logger specimen\n"
                  + "logger.info(" * depth
                  + "{index: walletAddress}" + ")" * depth)
        with tempfile.TemporaryDirectory() as base:
            specimen = Path(base) / "logger.ts"
            specimen.write_text(source, encoding="utf-8")
            findings = ephoros.check(specimen)
        self.assertEqual(["E005"] * depth,
                         [finding.code for finding in findings])
        self.assertEqual({2}, {finding.line for finding in findings})
        self.assertIn("log index `walletAddress`", findings[0].message)

    def test_a_sink_named_counter_nest_repeats_the_label_finding_per_span(self):
        # The metric-sink reading of the same overlap: every nested
        # `counter` span contains the one `labels:` container, so every
        # span repeats its finding from the container analysed once.
        depth = 8192
        source = ("// nested counter specimen\n"
                  + "counter(" * depth
                  + "{labels: {walletAddress: 1}}" + ")" * depth)
        with tempfile.TemporaryDirectory() as base:
            specimen = Path(base) / "counter.ts"
            specimen.write_text(source, encoding="utf-8")
            findings = ephoros.check(specimen)
        self.assertEqual(["E005"] * depth,
                         [finding.code for finding in findings])
        self.assertEqual({2}, {finding.line for finding in findings})
        self.assertIn("metric label `walletAddress`", findings[0].message)

    def test_a_log_named_bracket_nest_keeps_its_single_exact_finding(self):
        # The subscript form of the same overlap: every `log[` span read
        # its full width for a key expression (12.2 seconds at the 1 MiB
        # cap); the bounded forward parse stops at the first character
        # outside the chain grammar, and only the innermost span holds one.
        depth = 150_000
        source = ("// nested log store specimen\n"
                  + "log[" * depth + "walletAddress" + "]" * depth)
        with tempfile.TemporaryDirectory() as base:
            specimen = Path(base) / "logstore.ts"
            specimen.write_text(source, encoding="utf-8")
            findings = ephoros.check(specimen)
        self.assertEqual(["E005"], [finding.code for finding in findings])
        self.assertEqual([2], [finding.line for finding in findings])
        self.assertIn("log index `walletAddress`", findings[0].message)

    def test_a_findings_saturated_file_keeps_every_line_number(self):
        # Counting newlines from the top of the file for every finding cost
        # quadratic time on findings-saturated files (10s at this size); a
        # bisected newline table built once per file keeps it linear. The
        # first, middle, and last findings pin the exact line numbers the
        # counting implementation reported.
        lines = 50_000
        with tempfile.TemporaryDirectory() as base:
            specimen = Path(base) / "saturated.ts"
            specimen.write_text("log[walletAddress]\n" * lines,
                                encoding="utf-8")
            findings = ephoros.check(specimen)
        self.assertEqual(["E005"] * lines,
                         [finding.code for finding in findings])
        self.assertEqual(1, findings[0].line)
        self.assertEqual(25_001, findings[lines // 2].line)
        self.assertEqual(50_000, findings[-1].line)

    def test_the_walk_skips_node_modules(self):
        with tempfile.TemporaryDirectory() as base:
            vendored = Path(base) / "node_modules" / "left-pad"
            vendored.mkdir(parents=True)
            (vendored / "index.ts").write_text(
                "eventLog[walletAddress] = event\n", encoding="utf-8")
            first_party = Path(base) / "src"
            first_party.mkdir()
            kept = first_party / "page.tsx"
            kept.write_text("export default null\n", encoding="utf-8")
            self.assertEqual([kept], ephoros.walk([base]))


class AlertLabelKeys(unittest.TestCase):
    def test_an_address_named_key_under_alert_labels_reports_e005(self):
        findings = ephoros.check(TELEMETRY_FIXTURES / "alert-labels.yaml")
        self.assertEqual(["E005"], [finding.code for finding in findings])

    def test_a_bounded_label_key_is_clean(self):
        source = ("- alert: Bounded\n"
                  "  labels:\n"
                  "    severity: page\n"
                  "  annotations:\n"
                  "    runbook: runbooks/bounded.md\n")
        self.assertEqual([], yaml_findings(source))

    def test_a_labels_mapping_outside_an_alert_entry_is_ignored(self):
        source = "service:\n  labels:\n    wallet_address: primary\n"
        self.assertEqual([], yaml_findings(source))

    def test_a_reasoned_pragma_suppresses_an_alert_label_key(self):
        source = ("- alert: Suppressed\n"
                  "  labels:\n"
                  "    # ephoros: allow one aggregate treasury row\n"
                  "    wallet_address: treasury\n"
                  "  annotations:\n"
                  "    runbook: runbooks/suppressed.md\n")
        self.assertEqual([], yaml_findings(source))

    def test_a_bare_pragma_does_not_suppress_an_alert_label_key(self):
        source = ("- alert: StillKeyed\n"
                  "  labels:\n"
                  "    wallet_address: treasury  # ephoros: allow\n"
                  "  annotations:\n"
                  "    runbook: runbooks/still-keyed.md\n")
        self.assertEqual(["E005"], [finding.code for finding in yaml_findings(source)])


class Suppression(unittest.TestCase):
    def test_a_stated_reason_suppresses(self):
        self.assertEqual([], codes(
            "log = get()\nlog.info(f'x {y}')  # ephoros: allow one-off migration script\n"))

    def test_a_bare_pragma_does_not_suppress(self):
        self.assertIn("E001", codes("log = get()\nlog.info(f'x {y}')  # ephoros: allow\n"))


class AlertRules(unittest.TestCase):
    def test_a_missing_annotation_reports_e004(self):
        findings = ephoros.check(ALERT_FIXTURES / "missing.yaml")
        self.assertEqual(["E004"], [finding.code for finding in findings])

    def test_a_complete_alert_is_clean(self):
        self.assertEqual([], ephoros.check(ALERT_FIXTURES / "complete.yaml"))

    def test_e004_does_not_resolve_the_runbook_target(self):
        self.assertEqual([], ephoros.check(ALERT_FIXTURES / "dangling.yaml"))

    def test_an_annotated_neighbour_cannot_satisfy_the_missing_alert(self):
        findings = ephoros.check(ALERT_FIXTURES / "multi-alert.yaml")
        self.assertEqual(["E004"], [finding.code for finding in findings])
        self.assertEqual(7, findings[0].line)

    def test_a_top_level_pointer_does_not_satisfy_an_alert(self):
        source = "runbook: runbooks/top.md\n- alert: NeedsOwnPointer\n"
        self.assertEqual(["E004"], [f.code for f in yaml_findings(source)])

    def test_a_deeper_runbook_key_does_not_satisfy_annotations(self):
        source = ("- alert: NeedsDirectAnnotation\n"
                  "  annotations:\n"
                  "    links:\n"
                  "      runbook: runbooks/deep.md\n")
        self.assertEqual(["E004"], [f.code for f in yaml_findings(source)])

    def test_comments_do_not_create_or_satisfy_alerts(self):
        source = ("# - alert: CommentOnly\n"
                  "- alert: RealAlert\n"
                  "  annotations:\n"
                  "    # runbook: runbooks/comment.md\n")
        self.assertEqual(["E004"], [f.code for f in yaml_findings(source)])

    def test_block_scalars_do_not_create_or_satisfy_alerts(self):
        source = ("- alert: ScalarExample\n"
                  "  description: |\n"
                  "    annotations:\n"
                  "      runbook: runbooks/example.md\n"
                  "    - alert: NotARealNeighbour\n")
        self.assertEqual(["E004"], [f.code for f in yaml_findings(source)])

    def test_unsupported_mapping_and_flow_shapes_are_ignored(self):
        self.assertEqual([], ephoros.check(ALERT_FIXTURES / "false-positives.yaml"))

    def test_a_reasoned_suppression_covers_e004(self):
        self.assertEqual([], ephoros.check(ALERT_FIXTURES / "suppressed.yaml"))

    def test_pragma_shaped_scalar_text_does_not_suppress_e004(self):
        specimens = (
            'note: "# ephoros: allow quoted example"\n- alert: StillMissing\n',
            "note: |\n  # ephoros: allow block example\n- alert: StillMissing\n",
        )
        for source in specimens:
            with self.subTest(source=source):
                self.assertEqual(["E004"], [f.code for f in yaml_findings(source)])

    def test_an_unseparated_plain_scalar_hash_is_not_a_suppression_comment(self):
        source = ("- note: literal# ephoros: allow not a comment\n"
                  "- alert: StillMissing\n")
        self.assertEqual(["E004"], [finding.code for finding in yaml_findings(source)])

    def test_a_dedented_comment_after_a_block_scalar_can_suppress_e004(self):
        source = ("note: |\n"
                  "  scalar body\n"
                  "# ephoros: allow generated annotation arrives downstream\n"
                  "- alert: SuppressedMissingAnnotation\n")
        self.assertEqual([], yaml_findings(source))

    def test_a_bare_suppression_does_not_cover_e004(self):
        source = "# ephoros: allow\n- alert: StillMissing\n"
        self.assertEqual(["E004"], [f.code for f in yaml_findings(source)])

    def test_an_oversized_yaml_file_fails_visibly(self):
        source = "#" * (ephoros.MAX_YAML_BYTES + 1)
        self.assertEqual(["E000"], [f.code for f in yaml_findings(source)])

    def test_yaml_read_requests_only_the_cap_plus_one_byte(self):
        class RecordingReader(io.BytesIO):
            requested = None

            def read(self, size=-1):
                self.requested = size
                return super().read(size)

        reader = RecordingReader(b"#" * (ephoros.MAX_YAML_BYTES + 1))
        with mock.patch.object(Path, "open", return_value=reader), \
                mock.patch.object(Path, "read_bytes", side_effect=AssertionError):
            findings = ephoros.check(Path("bounded.yaml"))
        self.assertEqual(["E000"], [finding.code for finding in findings])
        self.assertEqual(ephoros.MAX_YAML_BYTES + 1, reader.requested)

    def test_bare_sequence_block_scalars_do_not_create_alerts(self):
        for marker in ("|", ">"):
            with self.subTest(marker=marker):
                source = f"examples:\n  - {marker}\n    - alert: ExampleOnly\n"
                self.assertEqual([], yaml_findings(source))

    def test_yaml_keys_are_case_sensitive(self):
        self.assertEqual([], yaml_findings("- Alert: UnsupportedCase\n"))
        source = ("- alert: MissingLowercaseKeys\n"
                  "  Annotations:\n"
                  "    Runbook: runbooks/wrong-case.md\n")
        self.assertEqual(["E004"], [finding.code for finding in yaml_findings(source)])

    def test_an_unseparated_hash_in_a_runbook_path_satisfies_presence(self):
        source = ("- alert: HashInPlainScalar\n"
                  "  annotations:\n"
                  "    runbook: runbooks/missing#book.md\n")
        self.assertEqual([], yaml_findings(source))

    def test_multiline_quoted_alert_text_does_not_fire_e004(self):
        for quote in ("'", '"'):
            with self.subTest(quote=quote):
                source = f"notes: {quote}\n  - alert: QuotedExample\n  {quote}\n"
                self.assertEqual([], yaml_findings(source))

    def test_multiline_quoted_runbook_text_does_not_satisfy_e004(self):
        for quote in ("'", '"'):
            with self.subTest(quote=quote):
                source = ("- alert: NeedsRealRunbook\n"
                          "  annotations:\n"
                          f"    note: {quote}\n"
                          "      runbook: runbooks/quoted.md\n"
                          f"      {quote}\n")
                self.assertEqual(["E004"], [finding.code for finding in yaml_findings(source)])

    def test_multiline_quoted_pragma_text_does_not_suppress_e004(self):
        for quote in ("'", '"'):
            with self.subTest(quote=quote):
                source = (f"note: {quote}\n"
                          f"  # ephoros: allow quoted example {quote}\n"
                          "- alert: StillMissing\n")
                self.assertEqual(["E004"], [finding.code for finding in yaml_findings(source)])

    def test_quotes_inside_plain_scalars_do_not_hide_alerts(self):
        for quote, value in (("'", "O'Brien"), ('"', 'six" pipe')):
            with self.subTest(quote=quote):
                source = f"note: {value}\n- alert: StillMissing\n"
                self.assertEqual(
                    ["E004"], [finding.code for finding in yaml_findings(source)])

    def test_unseparated_quote_starts_do_not_hide_alerts(self):
        for shape in ("- note: plain:{quote}text", "  -{quote}text"):
            for quote in ("'", '"'):
                with self.subTest(shape=shape, quote=quote):
                    source = f"{shape.format(quote=quote)}\n- alert: StillMissing\n"
                    self.assertEqual(
                        ["E004"], [finding.code for finding in yaml_findings(source)])

    def test_plain_scalar_continuation_quotes_do_not_hide_alerts(self):
        for quote in ("'", '"'):
            with self.subTest(quote=quote):
                source = ("- note: first\n"
                          f"    {quote}continued\n"
                          "- alert: StillMissing\n")
                self.assertEqual(
                    ["E004"], [finding.code for finding in yaml_findings(source)])

    def test_a_folded_plain_runbook_cannot_use_a_first_line_decoy(self):
        source = ("- alert: FoldedPointer\n"
                  "  annotations:\n"
                  "    runbook: runbooks/present.md\n"
                  "      extra\n")
        self.assertEqual(["E004"], [finding.code for finding in yaml_findings(source)])

    def test_single_line_and_valid_folded_plain_runbooks_satisfy_e004(self):
        single = ("- alert: SingleLine\n"
                  "  annotations:\n"
                  "    runbook: runbooks/present.md\n")
        folded = ("- alert: FoldedPath\n"
                  "  annotations:\n"
                  "    runbook: runbooks/present\n"
                  "      target.md\n")
        self.assertEqual([], yaml_findings(single))
        self.assertEqual([], yaml_findings(folded))

    def test_a_blank_plain_fold_cannot_collapse_to_a_valid_pointer(self):
        source = ("- alert: BlankFold\n"
                  "  annotations:\n"
                  "    runbook: runbooks/present\n"
                  "\n"
                  "      target.md\n")
        self.assertEqual(["E004"], [finding.code for finding in yaml_findings(source)])


class OverTheMarketplace(unittest.TestCase):
    def test_suffix_matching_directories_are_not_walked_as_files(self):
        with tempfile.TemporaryDirectory() as base:
            for name in ("generated.py", "generated.yaml", "generated.yml"):
                (Path(base) / name).mkdir()
            self.assertEqual([], ephoros.walk([base]))


if __name__ == "__main__":
    unittest.main()
