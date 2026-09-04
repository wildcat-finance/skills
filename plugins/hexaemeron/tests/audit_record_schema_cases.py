"""Strict audit-record controller cases loaded by ``test_hexctl``."""


class AuditSynopsisResourceBoundaryCases:
    def test_record_framing_preserves_literal_separator_and_escape_tokens(self):
        renderer = audit_synopsis_module()
        lead = "Leads not pursued: literal <br>; escapes %, %%, and %b"
        source = (
            "\n".join(
                [
                    "## Fixture, step 1, round 1 -- 2026-08-23T02:17:46Z",
                    "",
                    "Audit schema: fiat-audit-round/v1",
                    "",
                    "Covered: fixture-risk=reviewed",
                    "",
                    "Not checked: none",
                    "",
                    "Elenchus verdict: null",
                    "",
                    "| id | severity | file | finding | status |",
                    "| --- | --- | --- | --- | --- |",
                    "| -- | -- | -- | none | -- |",
                    "",
                    lead,
                ]
            )
            + "\n"
        ).encode()
        rendered = renderer.render_source("audit/AUDIT.md", source)
        record = rendered["bytes"].decode().splitlines()[1]
        decoder = getattr(renderer, "decode_synopsis_record", None)
        physical = record.split("<br>") if decoder is None else decoder(record)

        self.assertEqual(physical[-1], lead)
        self.assertEqual(physical.count(lead), 1)
        self.assertTrue(callable(decoder))

    def test_many_short_lines_remain_inside_the_receipted_acceptance_domain(self):
        renderer = audit_synopsis_module()
        source = b"## legacy\nLeads not pursued:\n" + b"x\n" * 200_000
        rendered = renderer.render_source("audit/AUDIT.md", source)

        self.assertEqual(rendered["source_lines"], 200_002)
        self.assertEqual(rendered["h2_count"], 1)
        self.assertLess(len(rendered["bytes"]), renderer.SYNOPSIS_BYTES_MAX)

    def test_write_refuses_a_source_change_after_planning(self):
        renderer = audit_synopsis_module()
        with tempfile.TemporaryDirectory() as raw_root:
            source = Path(raw_root, "audit", "AUDIT.md")
            source.parent.mkdir()
            source.write_bytes(
                b"## legacy\nLeads not pursued: none\n" + b"x\n" * 20
            )
            destination = source.with_name("AUDIT_SYNOPSIS.md")
            real_replace = renderer.atomic_replace
            replacement_observed = False

            def mutate_then_replace(root, relative, data):
                nonlocal replacement_observed
                source.write_bytes(source.read_bytes().replace(b"none", b"nope"))
                result = real_replace(root, relative, data)
                replacement_observed = destination.is_file()
                return result

            with mock.patch.object(
                renderer, "atomic_replace", side_effect=mutate_then_replace
            ):
                with self.assertRaisesRegex(
                    renderer.SynopsisError, "source changed after planning"
                ):
                    renderer.process_repository(raw_root, write=True)
            self.assertTrue(replacement_observed)
            self.assertFalse(destination.exists())

    def test_table_cell_scanner_scales_with_the_accepted_line_length(self):
        renderer = audit_synopsis_module()

        def elapsed(size):
            line = "| " + "x" * size + " | b | c | d | e |"
            started = time.process_time()
            self.assertEqual(len(renderer._table_cells(line)), 5)
            return time.process_time() - started

        small = elapsed(64 * 1024)
        large = elapsed(512 * 1024)
        self.assertLess(
            large,
            small * 20,
            f"table scan scaled from {small:.6f}s to {large:.6f}s",
        )
def build_audit_synopsis_resource_boundary_tests(context):
    """Build synopsis boundary cases against the loaded controller harness."""
    globals().update(
        {name: value for name, value in context.items() if not name.startswith("__")}
    )
    return type(
        "AuditSynopsisResourceBoundaryTests",
        (AuditSynopsisResourceBoundaryCases, context["unittest"].TestCase),
        {},
    )


def build_audit_record_schema_tests(context):
    """Build the cases against the already-loaded controller test harness."""
    globals().update(
        {name: value for name, value in context.items() if not name.startswith("__")}
    )
    class AuditRecordSchemaTests(HexctlCase):
        """The receipt checks Warden's final append before durable mutation."""

        def setUp(self):
            super().setUp()
            self.auto_audit_records = False
            self.to_audit()
            self.run_ctl("record", "security_suite", SUITE)

        def run_ctl(self, *args, expect=0):
            if args[:1] == ("audit-round",) and expect == 0:
                synopsis = subprocess.run(
                    [sys.executable, AUDIT_SYNOPSIS, "--write", self.target],
                    cwd=self.target,
                    capture_output=True,
                    text=True,
                )
                if synopsis.returncode:
                    raise AssertionError(
                        f"audit synopsis fixture failed\nstdout: {synopsis.stdout}"
                        f"stderr: {synopsis.stderr}"
                    )
            return super().run_ctl(*args, expect=expect)

        def state_ledger_digests(self):
            return tuple(
                hashlib.sha256(Path(path).read_bytes()).hexdigest()
                for path in (
                    os.path.join(self.target, ".hexaemeron", "state.json"),
                    os.path.join(self.target, ".hexaemeron", "ledger.jsonl"),
                )
            )

        def log_path(self):
            relative = self.state()["config"]["audit"]["log_path"]
            return os.path.join(self.target, *relative.split("/"))

        def record_lines(
            self,
            findings=0,
            verdict="null",
            *,
            schema="fiat-audit-round/v2",
            heading=None,
            timestamp="2026-08-23T02:17:46Z",
            covered="packet-state-drift=reviewed",
            omit=(),
            table_rows=None,
            extra=(),
        ):
            state = self.state()
            round_number = len(state["steps"][0]["audit"]["rounds"]) + 1
            rows = table_rows
            if rows is None:
                rows = (
                    ["| -- | -- | -- | none | -- |"]
                    if findings == 0
                    else [
                        f"| F-{index:02d} | low | fixture.py | finding {index} | open |"
                        for index in range(1, findings + 1)
                    ]
                )
            if heading is None:
                if schema == "fiat-audit-round/v1":
                    heading = (
                        f"## {state['topic']}, step 1, round {round_number} -- "
                        f"{timestamp}"
                    )
                else:
                    heading = f"## Step 1, round {round_number} -- {timestamp}"
            blocks = {
                "heading": [heading],
                "schema": [f"Audit schema: {schema}"],
                "covered": [f"Covered: {covered}"],
                "not_checked": ["Not checked: none"],
                "verdict": [f"Elenchus verdict: {verdict}"],
                "table": [
                    "| id | severity | file | finding | status |",
                    "| --- | --- | --- | --- | --- |",
                    *rows,
                ],
                "leads": ["Leads not pursued: none"],
            }
            lines = []
            for name in (
                "heading", "schema", "covered", "not_checked", "verdict", "table", "leads"
            ):
                if name not in omit:
                    lines.extend(blocks[name])
                    lines.append("")
            lines.extend(extra)
            return lines

        def write_record(self, *args, append=False, **kwargs):
            path = self.log_path()
            os.makedirs(os.path.dirname(path), exist_ok=True)
            record = "\n".join(self.record_lines(*args, **kwargs)).encode()
            prefix = Path(path).read_bytes() if append and os.path.exists(path) else b""
            separator = b""
            if prefix:
                separator = b"\n" if prefix.endswith(b"\n") else b"\n\n"
            Path(path).write_bytes(prefix + separator + record)
            return path

        def set_fake_baseline(self, data):
            self.env["FAKE_GIT_BASELINE_HEX"] = data.hex()

        def rewrite_latest_round(self, **changes):
            state_path = Path(self.target, ".hexaemeron", "state.json")
            ledger_path = Path(self.target, ".hexaemeron", "ledger.jsonl")
            state = json.loads(state_path.read_text(encoding="utf-8"))
            latest = state["steps"][0]["audit"]["rounds"][-1]
            for key, value in changes.items():
                if value is ...:
                    latest.pop(key, None)
                else:
                    latest[key] = value
            state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

            entries = [
                json.loads(line)
                for line in ledger_path.read_text(encoding="utf-8").splitlines()
                if line
            ]
            self.assertEqual(entries[-1]["event"], "audit-round")
            for key, value in changes.items():
                if value is ...:
                    entries[-1]["data"].pop(key, None)
                else:
                    entries[-1]["data"][key] = value
            entries[-1]["state"] = hashlib.sha256(
                json.dumps(state, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
            unsigned = {key: value for key, value in entries[-1].items() if key != "hash"}
            entries[-1]["hash"] = hashlib.sha256(
                json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
            ledger_path.write_text(
                "".join(json.dumps(entry, sort_keys=True) + "\n" for entry in entries),
                encoding="utf-8",
            )

        def refuse(self, fragment, *args):
            before = self.state_ledger_digests()
            result = self.run_ctl("audit-round", *args, expect=2)
            self.assertIn(fragment, result.stderr)
            self.assertEqual(self.state_ledger_digests(), before)

        def write_synopsis(self):
            result = subprocess.run(
                [sys.executable, AUDIT_SYNOPSIS, "--write", self.target],
                cwd=self.target,
                capture_output=True,
                text=True,
            )
            if result.returncode:
                raise AssertionError(
                    f"audit synopsis fixture failed\nstdout: {result.stdout}"
                    f"stderr: {result.stderr}"
                )
            source = Path(self.log_path())
            return source.with_name(source.stem + ".synopsis.md")

        def call_with_renderer(self, controller, renderer, stderr):
            class Loader:
                @staticmethod
                def exec_module(_module):
                    pass

            specification = argparse.Namespace(loader=Loader())
            with (
                mock.patch.object(
                    controller, "read_configured_audit_log",
                    return_value=("audit/AUDIT.md", b"record"),
                ),
                mock.patch.object(controller, "audit_delta_start", return_value=0),
                mock.patch.object(controller, "audit_record_bytes", return_value=b"record"),
                mock.patch.object(
                    controller,
                    "parse_audit_record",
                    return_value=("fiat-audit-round/v1", "2026-08-23T02:17:46Z"),
                ),
                mock.patch.object(
                    controller.importlib.util,
                    "spec_from_file_location",
                    return_value=specification,
                ),
                mock.patch.object(
                    controller.importlib.util, "module_from_spec", return_value=renderer
                ),
                redirect_stderr(stderr),
            ):
                return controller.validated_audit_record(
                    self.target,
                    {"config": {"audit": {"log_path": "audit/AUDIT.md"}}},
                    {"audit": {"rounds": []}},
                    argparse.Namespace(log=None),
                )

        def assert_renderer_refusal(self, call):
            try:
                call()
            except BaseException as error:
                caught = error
            else:
                self.fail("renderer validation did not refuse")
            self.assertIsInstance(caught, SystemExit)
            self.assertEqual(caught.code, 2)

        def test_missing_stale_and_lossy_synopsis_refuse_without_drift(self):
            self.write_record()
            self.refuse("synopsis is missing", "--findings", "0")

            synopsis = self.write_synopsis()
            synopsis.write_bytes(synopsis.read_bytes() + b"stale\n")
            self.refuse("synopsis is stale", "--findings", "0")

            self.write_synopsis()
            text = synopsis.read_text(encoding="utf-8")
            synopsis.write_text(
                text.replace("Leads not pursued: none", "[lead dropped]", 1),
                encoding="utf-8",
            )
            self.refuse("synopsis is stale", "--findings", "0")

        def test_corrupt_renderer_import_is_a_bounded_refusal(self):
            controller = hexctl_module()

            class BrokenLoader:
                @staticmethod
                def exec_module(_module):
                    raise RuntimeError("corrupt renderer fixture")

            specification = argparse.Namespace(loader=BrokenLoader())
            stderr = StringIO()
            with (
                mock.patch.object(
                    controller, "read_configured_audit_log",
                    return_value=("audit/AUDIT.md", b"record"),
                ),
                mock.patch.object(controller, "audit_delta_start", return_value=0),
                mock.patch.object(controller, "audit_record_bytes", return_value=b"record"),
                mock.patch.object(
                    controller,
                    "parse_audit_record",
                    return_value=("fiat-audit-round/v1", "2026-08-23T02:17:46Z"),
                ),
                mock.patch.object(
                    controller.importlib.util,
                    "spec_from_file_location",
                    return_value=specification,
                ),
                mock.patch.object(
                    controller.importlib.util, "module_from_spec", return_value=object()
                ),
                redirect_stderr(stderr),
                self.assertRaises(BaseException) as raised,
            ):
                controller.validated_audit_record(
                    self.target,
                    {"config": {"audit": {"log_path": "audit/AUDIT.md"}}},
                    {"audit": {"rounds": []}},
                    argparse.Namespace(log=None),
                )
            self.assertIsInstance(raised.exception, SystemExit)
            self.assertEqual(raised.exception.code, 2)
            self.assertIn("audit synopsis renderer cannot be loaded", stderr.getvalue())

        def test_renderer_cannot_terminate_successfully_at_checked_boundaries(self):
            controller = hexctl_module()

            class RendererError(Exception):
                def __str__(self):
                    if renderer.stop_during_error_format:
                        raise SystemExit(0)
                    return super().__str__()

            class StoppingRenderer:
                SynopsisError = RendererError
                stop_during_interface = False
                stop_during_validation = False
                stop_during_error_format = False

                def __getattribute__(self, name):
                    if (
                        name == "validate_committed_synopsis"
                        and object.__getattribute__(self, "stop_during_interface")
                    ):
                        raise SystemExit(0)
                    return object.__getattribute__(self, name)

                @staticmethod
                def validate_committed_synopsis(*_args):
                    if renderer.stop_during_error_format:
                        raise RendererError("renderer refusal")
                    if renderer.stop_during_validation:
                        raise SystemExit(0)
                    return "a" * 64

            renderer = StoppingRenderer()

            class StoppingLoader:
                stop_during_load = True

                def exec_module(self, _module):
                    if self.stop_during_load:
                        raise SystemExit(0)

            loader = StoppingLoader()
            specification = argparse.Namespace(loader=loader)
            for stop_at in (
                "module",
                "load",
                "interface",
                "type-check",
                "validation",
                "error-format",
                "digest-check",
            ):
                with self.subTest(stop_at=stop_at):
                    loader.stop_during_load = stop_at == "load"
                    renderer.stop_during_interface = stop_at == "interface"
                    renderer.stop_during_validation = stop_at == "validation"
                    renderer.stop_during_error_format = stop_at == "error-format"
                    stderr = StringIO()

                    def create_module(_specification):
                        if stop_at == "module":
                            raise SystemExit(0)
                        return renderer

                    with ExitStack() as stack:
                        stack.enter_context(mock.patch.object(
                            controller, "read_configured_audit_log",
                            return_value=("audit/AUDIT.md", b"record"),
                        ))
                        stack.enter_context(mock.patch.object(
                            controller, "audit_delta_start", return_value=0
                        ))
                        stack.enter_context(mock.patch.object(
                            controller, "audit_record_bytes", return_value=b"record"
                        ))
                        stack.enter_context(mock.patch.object(
                            controller,
                            "parse_audit_record",
                            return_value=(
                                "fiat-audit-round/v1", "2026-08-23T02:17:46Z"
                            ),
                        ))
                        stack.enter_context(mock.patch.object(
                            controller.importlib.util,
                            "spec_from_file_location",
                            return_value=specification,
                        ))
                        stack.enter_context(mock.patch.object(
                            controller.importlib.util,
                            "module_from_spec",
                            side_effect=create_module,
                        ))
                        if stop_at == "type-check":
                            stack.enter_context(mock.patch.object(
                                controller,
                                "issubclass",
                                side_effect=SystemExit(0),
                                create=True,
                            ))
                        if stop_at == "digest-check":
                            stack.enter_context(mock.patch.object(
                                controller.re, "fullmatch", side_effect=SystemExit(0)
                            ))
                        stack.enter_context(redirect_stderr(stderr))
                        raised = stack.enter_context(self.assertRaises(SystemExit))
                        controller.validated_audit_record(
                            self.target,
                            {"config": {"audit": {"log_path": "audit/AUDIT.md"}}},
                            {"audit": {"rounds": []}},
                            argparse.Namespace(log=None),
                        )
                    self.assertEqual(raised.exception.code, 2)
                    self.assertIn("audit synopsis renderer", stderr.getvalue())

        def test_declared_renderer_diagnostics_cannot_break_the_refusal(self):
            controller = hexctl_module()

            class RendererError(Exception):
                pass

            class Renderer:
                SynopsisError = RendererError
                message = "unsafe\nsurrogate: \ud800"

                @classmethod
                def validate_committed_synopsis(cls, *_args):
                    raise RendererError(cls.message)

            before = self.state_ledger_digests()
            for message, expected, exact_size in (
                (
                    "unsafe\x00\x1b\nsurrogate: \ud800\\",
                    b"unsafe\\x00\\x1b\\nsurrogate: \\ud800\\\\",
                    None,
                ),
                ("x" * 4_080, b"x" * 4_080, 4_096),
                ("x" * 4_081, b"audit synopsis renderer validation failed", None),
                ("x" * 4_096, b"audit synopsis renderer validation failed", None),
                ("\\" * 2_040, b"\\\\" * 2_040, 4_096),
                ("\\" * 2_041, b"audit synopsis renderer validation failed", None),
                ("x" * 5_000, b"audit synopsis renderer validation failed", None),
            ):
                with self.subTest(message_chars=len(message)):
                    Renderer.message = message
                    output = BytesIO()
                    stderr = TextIOWrapper(output, encoding="ascii", errors="strict")
                    try:
                        self.assert_renderer_refusal(lambda:
                            self.call_with_renderer(controller, Renderer(), stderr)
                        )
                        stderr.flush()
                        self.assertIn(expected, output.getvalue())
                        self.assertLessEqual(
                            len(output.getvalue()),
                            controller.AUDIT_RENDERER_DIAGNOSTIC_BYTES_MAX,
                        )
                        if exact_size is not None:
                            self.assertEqual(len(output.getvalue()), exact_size)
                        self.assertEqual(output.getvalue()[-1:], b"\n")
                        self.assertTrue(
                            all(32 <= byte <= 126 for byte in output.getvalue()[:-1])
                        )
                    finally:
                        stderr.detach()
            self.assertEqual(self.state_ledger_digests(), before)

        def test_renderer_diagnostic_byte_cap_is_encoding_independent(self):
            controller = hexctl_module()
            for encoding in ("utf-8", "utf-16"):
                with self.subTest(encoding=encoding):
                    output = BytesIO()
                    stderr = TextIOWrapper(output, encoding=encoding, errors="strict")
                    try:
                        with redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
                            controller.refuse_audit_renderer("x" * 4_080)
                        stderr.flush()
                        self.assertEqual(raised.exception.code, 2)
                        self.assertEqual(
                            len(output.getvalue()),
                            controller.AUDIT_RENDERER_DIAGNOSTIC_BYTES_MAX,
                        )
                    finally:
                        stderr.detach()

        def test_renderer_diagnostic_completes_binary_short_writes(self):
            controller = hexctl_module()
            expected = b"hexctl: error: renderer refusal\n"

            class ShortBuffer:
                def __init__(self, limit):
                    self.limit = limit
                    self.output = bytearray()
                    self.flushed = False

                def write(self, value):
                    size = min(self.limit, len(value))
                    self.output.extend(value[:size])
                    return size

                def flush(self):
                    self.flushed = True

            for limit in (1, 3, len(expected) - 1):
                with self.subTest(limit=limit):
                    stderr = argparse.Namespace(buffer=ShortBuffer(limit))
                    with mock.patch.object(controller.sys, "stderr", stderr):
                        with self.assertRaises(SystemExit) as raised:
                            controller.refuse_audit_renderer("renderer refusal")
                    self.assertEqual(raised.exception.code, 2)
                    self.assertEqual(bytes(stderr.buffer.output), expected)
                    self.assertTrue(stderr.buffer.flushed)

        def test_renderer_diagnostic_binary_write_boundaries_preserve_exit(self):
            controller = hexctl_module()
            full_write = object()

            class BoundaryBuffer:
                def __init__(
                    self, *, result=full_write, write_error=None, flush_error=None
                ):
                    self.result = result
                    self.write_error = write_error
                    self.flush_error = flush_error

                def write(self, value):
                    if self.write_error is not None:
                        raise self.write_error
                    return len(value) if self.result is full_write else self.result

                def flush(self):
                    if self.flush_error is not None:
                        raise self.flush_error

            for result in (None, 0, -1, True, 10_000):
                with self.subTest(result=result):
                    stderr = argparse.Namespace(buffer=BoundaryBuffer(result=result))
                    with mock.patch.object(controller.sys, "stderr", stderr):
                        with self.assertRaises(SystemExit) as raised:
                            controller.refuse_audit_renderer("renderer refusal")
                    self.assertEqual(raised.exception.code, 2)

            for stage in ("write", "flush"):
                for failure in (OSError("diagnostic failure"), SystemExit(0)):
                    with self.subTest(stage=stage, failure=type(failure).__name__):
                        stderr = argparse.Namespace(buffer=BoundaryBuffer(**{
                            f"{stage}_error": failure,
                        }))
                        with mock.patch.object(controller.sys, "stderr", stderr):
                            with self.assertRaises(SystemExit) as raised:
                                controller.refuse_audit_renderer("renderer refusal")
                        self.assertEqual(raised.exception.code, 2)

            for stage in ("write", "flush"):
                for failure in (KeyboardInterrupt(), GeneratorExit()):
                    with self.subTest(stage=stage, failure=type(failure).__name__):
                        stderr = argparse.Namespace(buffer=BoundaryBuffer(**{
                            f"{stage}_error": failure,
                        }))
                        with mock.patch.object(controller.sys, "stderr", stderr):
                            try:
                                controller.refuse_audit_renderer("renderer refusal")
                            except BaseException as error:
                                caught = error
                            else:
                                self.fail("renderer diagnostic did not terminate")
                        self.assertIs(caught, failure)

            stderr = StringIO()
            with redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
                controller.refuse_audit_renderer("renderer refusal")
            self.assertEqual(raised.exception.code, 2)
            self.assertEqual(stderr.getvalue(), "hexctl: error: renderer refusal\n")

        def test_renderer_diagnostic_emission_cannot_report_false_success(self):
            controller = hexctl_module()

            class RendererError(Exception):
                pass

            renderer = argparse.Namespace(
                SynopsisError=RendererError,
                validate_committed_synopsis=lambda *_args: (_ for _ in ()).throw(
                    RendererError("renderer refusal")
                ),
            )

            class BrokenDiagnostic(StringIO):
                def __init__(self, failure):
                    super().__init__()
                    self.failure = failure

                def write(self, _value):
                    raise self.failure

            before = self.state_ledger_digests()
            for failure in (SystemExit(0), OSError("closed diagnostic stream")):
                with self.subTest(failure=type(failure).__name__):
                    self.assert_renderer_refusal(lambda:
                        self.call_with_renderer(
                            controller, renderer, BrokenDiagnostic(failure)
                        )
                    )
                    self.assertEqual(self.state_ledger_digests(), before)

        def test_foreign_renderer_exceptions_and_process_interrupts_stay_distinct(self):
            controller = hexctl_module()

            class RendererError(Exception):
                pass

            for failure in (
                RuntimeError("foreign renderer failure"),
                KeyboardInterrupt(),
                GeneratorExit(),
            ):
                with self.subTest(failure=type(failure).__name__):
                    renderer = argparse.Namespace(
                        SynopsisError=RendererError,
                        validate_committed_synopsis=lambda *_args, failure=failure: (
                            _ for _ in ()
                        ).throw(failure),
                    )
                    with self.assertRaises(type(failure)) as raised:
                        self.call_with_renderer(controller, renderer, StringIO())
                    self.assertIs(raised.exception, failure)

        def test_corrupt_renderer_interface_is_a_bounded_refusal(self):
            controller = hexctl_module()

            class Loader:
                @staticmethod
                def exec_module(_module):
                    pass

            specification = argparse.Namespace(loader=Loader())
            stderr = StringIO()
            with (
                mock.patch.object(
                    controller, "read_configured_audit_log",
                    return_value=("audit/AUDIT.md", b"record"),
                ),
                mock.patch.object(controller, "audit_delta_start", return_value=0),
                mock.patch.object(controller, "audit_record_bytes", return_value=b"record"),
                mock.patch.object(
                    controller,
                    "parse_audit_record",
                    return_value=("fiat-audit-round/v1", "2026-08-23T02:17:46Z"),
                ),
                mock.patch.object(
                    controller.importlib.util,
                    "spec_from_file_location",
                    return_value=specification,
                ),
                mock.patch.object(
                    controller.importlib.util, "module_from_spec", return_value=object()
                ),
                redirect_stderr(stderr),
                self.assertRaises(BaseException) as raised,
            ):
                controller.validated_audit_record(
                    self.target,
                    {"config": {"audit": {"log_path": "audit/AUDIT.md"}}},
                    {"audit": {"rounds": []}},
                    argparse.Namespace(log=None),
                )
            self.assertIsInstance(raised.exception, SystemExit)
            self.assertEqual(raised.exception.code, 2)
            self.assertIn("audit synopsis renderer cannot be loaded", stderr.getvalue())

        def test_renderer_must_return_one_sha256_digest(self):
            controller = hexctl_module()

            class RendererError(Exception):
                pass

            renderer = argparse.Namespace(
                SynopsisError=RendererError,
                validate_committed_synopsis=lambda *_args: "not-a-sha256",
            )

            class Loader:
                @staticmethod
                def exec_module(_module):
                    pass

            specification = argparse.Namespace(loader=Loader())
            stderr = StringIO()
            with (
                mock.patch.object(
                    controller, "read_configured_audit_log",
                    return_value=("audit/AUDIT.md", b"record"),
                ),
                mock.patch.object(controller, "audit_delta_start", return_value=0),
                mock.patch.object(controller, "audit_record_bytes", return_value=b"record"),
                mock.patch.object(
                    controller,
                    "parse_audit_record",
                    return_value=("fiat-audit-round/v1", "2026-08-23T02:17:46Z"),
                ),
                mock.patch.object(
                    controller.importlib.util,
                    "spec_from_file_location",
                    return_value=specification,
                ),
                mock.patch.object(
                    controller.importlib.util, "module_from_spec", return_value=renderer
                ),
                redirect_stderr(stderr),
                self.assertRaises(SystemExit) as raised,
            ):
                controller.validated_audit_record(
                    self.target,
                    {"config": {"audit": {"log_path": "audit/AUDIT.md"}}},
                    {"audit": {"rounds": []}},
                    argparse.Namespace(log=None),
                )
            self.assertEqual(raised.exception.code, 2)
            self.assertIn("renderer returned an invalid digest", stderr.getvalue())

        def test_date_only_heading_is_refused_before_mutation(self):
            self.write_record(timestamp="2026-08-23")
            self.refuse("record timestamp", "--findings", "0")

        def test_controller_accepts_strict_v1_and_v2_records(self):
            self.write_record(schema="fiat-audit-round/v1")
            self.run_ctl("audit-round", "--findings", "0")
            self.write_record(schema="fiat-audit-round/v2", append=True)
            self.run_ctl("audit-round", "--findings", "0")
            self.assertEqual(
                [
                    entry["schema"]
                    for entry in self.state()["steps"][0]["audit"]["rounds"]
                ],
                ["fiat-audit-round/v1", "fiat-audit-round/v2"],
            )

        def test_schema_versions_cannot_cross_interpret_headings(self):
            v2_heading = "## Step 1, round 1 -- 2026-08-23T02:17:46Z"
            self.write_record(schema="fiat-audit-round/v1", heading=v2_heading)
            self.refuse("heading does not match its schema", "--findings", "0")
            v1_heading = (
                "## test topic, step 1, round 1 -- 2026-08-23T02:17:46Z"
            )
            self.write_record(schema="fiat-audit-round/v2", heading=v1_heading)
            self.refuse("heading does not match its schema", "--findings", "0")

        def test_heading_identity_and_calendar_date_are_exact(self):
            self.write_record(timestamp="2026-02-30T02:17:46Z")
            self.refuse("calendar-valid", "--findings", "0")
            lines = self.record_lines()
            lines[0] = "## another topic, step 1, round 1 -- 2026-08-23T02:17:46Z"
            Path(self.log_path()).write_text("\n".join(lines), encoding="utf-8")
            self.refuse("schema, step, and round", "--findings", "0")

        def test_prior_offset_makes_legacy_markdown_irrelevant(self):
            self.write_record(findings=1)
            self.run_ctl("audit-round", "--findings", "1")
            path = Path(self.log_path())
            prefix = bytearray(path.read_bytes())
            finding = prefix.index(b"finding 1")
            prefix[finding: finding + len(b"finding 1")] = b"<script>x"
            path.write_bytes(prefix)
            self.write_record(append=True)
            self.env["FAKE_GIT_MODE"] = "baseline-unavailable"
            self.run_ctl("audit-round", "--findings", "0")

        def test_clean_log_only_predecessor_also_supplies_the_next_offset(self):
            self.write_record()
            self.run_ctl("audit-round", "--findings", "0")
            self.write_record(append=True)
            self.env["FAKE_GIT_MODE"] = "baseline-unavailable"
            self.run_ctl("audit-round", "--findings", "0")

        def test_first_strict_round_accepts_a_git_absent_log(self):
            self.write_record()
            self.run_ctl("audit-round", "--findings", "0")
            latest = self.state()["steps"][0]["audit"]["rounds"][-1]
            self.assertEqual(latest["log_end_offset"], os.path.getsize(self.log_path()))

        def test_first_strict_round_preserves_a_git_baseline_ending_in_lf(self):
            baseline = b"legacy evidence\n"
            self.set_fake_baseline(baseline)
            Path(self.log_path()).parent.mkdir(parents=True, exist_ok=True)
            Path(self.log_path()).write_bytes(baseline)
            self.write_record(append=True)
            self.run_ctl("audit-round", "--findings", "0")

        def test_first_strict_round_preserves_a_git_baseline_without_lf(self):
            baseline = b"legacy evidence"
            self.set_fake_baseline(baseline)
            Path(self.log_path()).parent.mkdir(parents=True, exist_ok=True)
            Path(self.log_path()).write_bytes(baseline)
            self.write_record(append=True)
            self.run_ctl("audit-round", "--findings", "0")

        def test_first_round_uses_implementation_baseline_after_prior_follow_ons(self):
            controller = hexctl_module()
            log_path = "audit/rounds/run.md"
            closed = b"prior step through its closing receipt\n"
            follow_ons = b"independent rounds after close\n"
            baseline = closed + follow_ons
            current = {
                "n": 2,
                "audit": {"rounds": []},
                "receipts": {
                    "implement": {
                        "commit": "2" * 40,
                        "verified_commits": ["2" * 40],
                    }
                },
            }
            state = {
                "steps": [
                    {
                        "n": 1,
                        "audit": {
                            "rounds": [
                                {"log": log_path, "log_end_offset": len(closed)}
                            ]
                        },
                    },
                    current,
                ]
            }
            data = baseline + b"\n## Step 2, round 1 -- 2026-09-04T00:00:00Z\n"

            with mock.patch.object(
                controller, "audit_baseline_blob", return_value=baseline
            ) as baseline_reader:
                start = controller.audit_delta_start(
                    self.target, state, current, log_path, data
                )

            baseline_reader.assert_called_once_with(self.target, current, log_path)
            self.assertEqual(start, len(baseline))

        def test_first_round_refuses_drift_before_implementation_baseline(self):
            controller = hexctl_module()
            log_path = "audit/rounds/run.md"
            closed = b"prior step through its closing receipt\n"
            baseline = closed + b"committed independent follow-ons\n"
            current = {
                "n": 2,
                "audit": {"rounds": []},
                "receipts": {"implement": {"commit": "2" * 40}},
            }
            state = {
                "steps": [
                    {
                        "n": 1,
                        "audit": {
                            "rounds": [
                                {"log": log_path, "log_end_offset": len(closed)}
                            ]
                        },
                    },
                    current,
                ]
            }
            data = closed + b"changed independent follow-ons\nnew round\n"
            stderr = StringIO()

            with (
                mock.patch.object(
                    controller, "audit_baseline_blob", return_value=baseline
                ) as baseline_reader,
                redirect_stderr(stderr),
                self.assertRaises(SystemExit) as raised,
            ):
                controller.audit_delta_start(
                    self.target, state, current, log_path, data
                )

            self.assertEqual(raised.exception.code, 2)
            self.assertIn("changed before its Git baseline boundary", stderr.getvalue())
            baseline_reader.assert_called_once_with(self.target, current, log_path)

        def test_later_round_uses_only_latest_same_step_offset(self):
            controller = hexctl_module()
            log_path = "audit/rounds/run.md"
            current_offset = 256

            class PriorStep(dict):
                def get(self, key, default=None):
                    if key == "audit":
                        raise AssertionError("a prior step's offset was inspected")
                    return super().get(key, default)

            current = {
                "n": 2,
                "audit": {
                    "rounds": [
                        {"log": log_path, "log_end_offset": current_offset}
                    ]
                },
            }
            state = {
                "steps": [
                    PriorStep(
                        n=1,
                        audit={
                            "rounds": [
                                {
                                    "log": "audit/rounds/previous-run.md",
                                    "log_end_offset": 64,
                                }
                            ]
                        },
                    ),
                    current,
                ]
            }

            with mock.patch.object(
                controller,
                "audit_baseline_blob",
                side_effect=AssertionError("later rounds must not reread the baseline"),
            ):
                start = controller.audit_delta_start(
                    self.target, state, current, log_path, b"x" * 512
                )

            self.assertEqual(start, current_offset)

        def test_legacy_missing_leaves_use_the_verified_git_blob(self):
            self.write_record(findings=1, verdict="guarded")
            self.run_ctl(
                "audit-round", "--findings", "1",
                "--fixes-commit", "legacy-fix",
                "--elenchus-verdict", "guarded",
            )
            baseline = Path(self.log_path()).read_bytes()
            self.rewrite_latest_round(
                schema=...,
                record_timestamp=...,
                entry_sha256=...,
                log_end_offset=...,
                elenchus_verdict=...,
            )
            self.run_ctl("status")
            self.run_ctl("verify")
            self.set_fake_baseline(baseline)
            self.write_record(append=True)
            self.run_ctl("audit-round", "--findings", "0")
            rounds = self.state()["steps"][0]["audit"]["rounds"]
            self.assertNotIn("log_end_offset", rounds[0])
            self.assertEqual(rounds[1]["log_end_offset"], os.path.getsize(self.log_path()))

        def test_git_baseline_failures_refuse_without_state_or_ledger_drift(self):
            baseline = b"legacy evidence\n"
            self.set_fake_baseline(baseline)
            Path(self.log_path()).parent.mkdir(parents=True, exist_ok=True)
            Path(self.log_path()).write_bytes(baseline)
            self.write_record(append=True)
            self.write_synopsis()
            for mode, fragment in (
                ("missing-commit", "baseline commit"),
                ("baseline-unavailable", "baseline path"),
                ("baseline-ambiguous", "ambiguous Git"),
                ("baseline-unsafe", "regular Git blob"),
                ("baseline-oversized", "byte cap"),
                ("baseline-malformed-size", "size is malformed"),
                ("baseline-short-read", "length does not match"),
            ):
                with self.subTest(mode=mode):
                    self.env["FAKE_GIT_MODE"] = mode
                    self.refuse(fragment, "--findings", "0")
            self.env.pop("FAKE_GIT_MODE", None)

        def test_changed_git_baseline_refuses_without_drift(self):
            self.set_fake_baseline(b"expected legacy\n")
            Path(self.log_path()).parent.mkdir(parents=True, exist_ok=True)
            Path(self.log_path()).write_bytes(b"changed! legacy\n")
            self.write_record(append=True)
            self.refuse("changed before", "--findings", "0")

        def test_boundary_separator_is_exact_for_all_baseline_endings(self):
            record = "\n".join(self.record_lines()).encode()
            cases = (
                (b"", b"\n" + record),
                (b"legacy\n", b"legacy\n" + record),
                (b"legacy\n", b"legacy\n\n\n" + record),
                (b"legacy", b"legacy\n" + record),
                (b"legacy", b"legacy\n\n\n" + record),
            )
            for baseline, live in cases:
                with self.subTest(baseline=baseline, delta=live[len(baseline):]):
                    self.set_fake_baseline(baseline)
                    Path(self.log_path()).parent.mkdir(parents=True, exist_ok=True)
                    Path(self.log_path()).write_bytes(live)
                    self.refuse("audit record", "--findings", "0")

        def test_malformed_mismatched_and_past_eof_offsets_never_fall_back(self):
            self.write_record(findings=1)
            self.run_ctl("audit-round", "--findings", "1")
            log = Path(self.log_path())
            initial_log = log.read_bytes()
            state_path = Path(self.target, ".hexaemeron", "state.json")
            ledger_path = Path(self.target, ".hexaemeron", "ledger.jsonl")
            initial_state = state_path.read_bytes()
            initial_ledger = ledger_path.read_bytes()
            cases = (
                ({"log_end_offset": True}, "non-boolean integer", True),
                ({"log_end_offset": "1"}, "non-boolean integer", True),
                ({"log_end_offset": -1}, "outside the current log", True),
                ({"log_end_offset": len(initial_log)}, "outside the current log", False),
                ({"log_end_offset": 2 * 1024 * 1024 + 1}, "outside", True),
                ({"log": "other/AUDIT.md"}, "does not match", True),
            )
            self.set_fake_baseline(initial_log)
            for changes, fragment, append in cases:
                with self.subTest(changes=changes):
                    state_path.write_bytes(initial_state)
                    ledger_path.write_bytes(initial_ledger)
                    log.write_bytes(initial_log)
                    self.rewrite_latest_round(**changes)
                    if append:
                        self.write_record(append=True)
                    self.refuse(fragment, "--findings", "0")

        def test_prefix_utf8_stays_outside_delta_parsing_but_fails_synopsis_input(self):
            self.write_record(findings=1)
            self.run_ctl("audit-round", "--findings", "1")
            path = Path(self.log_path())
            prefix = bytearray(path.read_bytes())
            prefix[0] = 0xff
            path.write_bytes(prefix)
            self.write_record(append=True)
            self.refuse("source is not UTF-8", "--findings", "0")

        def test_invalid_utf8_in_the_delta_refuses_without_drift(self):
            self.write_record(findings=1)
            self.run_ctl("audit-round", "--findings", "1")
            path = Path(self.log_path())
            path.write_bytes(path.read_bytes() + b"\n\xff\n")
            self.refuse("delta is not UTF-8", "--findings", "0")

        def test_raw_suffix_refuses_prelude_extra_fields_rows_headings_and_trailers(self):
            canonical = self.record_lines()
            placeholder = canonical.index("| -- | -- | -- | none | -- |")
            leads = canonical.index("Leads not pursued: none")
            cases = {
                "prelude": ["prelude", *canonical],
                "field": canonical[:leads] + ["Extra: value", ""] + canonical[leads:],
                "row": canonical[:placeholder + 1]
                + ["| F-02 | low | fixture.py | extra | open |"]
                + canonical[placeholder + 1:],
                "heading": canonical[:-1] + ["## later", ""],
                "trailer": canonical[:-1] + ["trailer", ""],
            }
            for name, lines in cases.items():
                with self.subTest(name=name):
                    Path(self.log_path()).parent.mkdir(parents=True, exist_ok=True)
                    Path(self.log_path()).write_bytes("\n".join(lines).encode())
                    self.refuse("audit record", "--findings", "0")

        def test_each_field_and_blank_separator_is_required(self):
            for omitted in (
                "schema", "covered", "not_checked", "verdict", "table", "leads"
            ):
                with self.subTest(omitted=omitted):
                    self.write_record(omit=(omitted,))
                    self.refuse("audit record", "--findings", "0")
            lines = self.record_lines()
            for index, line in enumerate(lines):
                if line != "":
                    continue
                with self.subTest(blank_index=index):
                    altered = lines[:index] + lines[index + 1:]
                    Path(self.log_path()).write_bytes("\n".join(altered).encode())
                    self.refuse("audit record", "--findings", "0")

        def test_active_round_ten_offset_is_a_stable_raw_boundary(self):
            controller = hexctl_module()
            repository = Path(HERE).parents[2]
            product_log = (
                repository
                / "audit"
                / "rounds"
                / "fiat-429-audit-record-schema-timestamp-synopsis.md"
            )
            prefix = product_log.read_bytes()[:20894]
            self.assertEqual(len(prefix), 20894)
            self.assertEqual(
                hashlib.sha256(prefix).hexdigest(),
                "c12b08243b2423a6980bb02ae1d9cd3539085e35912b7855dddc668669709f73",
            )
            relative = "audit/rounds/fiat-429-audit-record-schema-timestamp-synopsis.md"
            step = {
                "n": 1,
                "audit": {
                    "rounds": [
                        {"log": relative, "log_end_offset": 20894}
                    ]
                }
            }
            boundary = getattr(controller, "audit_delta_start", None)
            self.assertTrue(callable(boundary))
            self.assertEqual(
                boundary(
                    str(repository), {"steps": [step]}, step,
                    relative, prefix + b"\nnext"
                ),
                20894,
            )

        def test_covered_refuses_missing_duplicate_unknown_and_invalid_values(self):
            for covered in (
                "",
                "packet-state-drift=reviewed; packet-state-drift=reviewed",
                "packet-state-drift=reviewed; unknown-risk=reviewed",
                "packet-state-drift=accepted",
            ):
                with self.subTest(covered=covered):
                    self.write_record(covered=covered)
                    self.refuse("Covered", "--findings", "0")

        def test_findings_count_zero_row_and_verdict_must_match(self):
            self.write_record(findings=1, table_rows=[])
            self.refuse("findings table", "--findings", "1")
            self.write_record(
                findings=0,
                table_rows=["| F-01 | low | fixture.py | unexpected | open |"],
            )
            self.refuse("zero-finding row", "--findings", "0")
            self.write_record(findings=1, verdict="guarded")
            self.refuse(
                "Elenchus verdict",
                "--findings", "1", "--fixes-commit", "fix-1",
                "--elenchus-verdict", "passed",
            )

        def test_findings_table_accepts_a_raw_escaped_pipe_in_a_cell(self):
            self.write_record(
                findings=1,
                table_rows=[
                    r"| F-01 | low | fixture.py | comparison `a \| b` | open |"
                ],
            )
            self.run_ctl("audit-round", "--findings", "1")

        def test_controller_table_cell_scanner_scales_with_the_line_cap(self):
            controller = hexctl_module()

            def elapsed(size):
                line = "| " + "x" * size + " | b | c | d | e |"
                started = time.process_time()
                self.assertEqual(len(controller.audit_table_cells(line)), 5)
                return time.process_time() - started

            small = elapsed(64 * 1024)
            large = elapsed(512 * 1024)
            self.assertLess(
                large,
                small * 20,
                f"controller table scan scaled from {small:.6f}s to {large:.6f}s",
            )

        def test_findings_table_refuses_an_escaped_closing_pipe(self):
            self.write_record(
                findings=1,
                table_rows=[r"| F-01 | low | fixture.py | finding | open \|"],
            )
            self.refuse("malformed data row", "--findings", "1")

        def test_supplied_log_must_be_the_configured_path(self):
            self.write_record()
            self.refuse(
                "this round writes",
                "--findings", "0", "--log", "other/AUDIT.md",
            )
            relative = self.state()["config"]["audit"]["log_path"]
            alias_relative = relative.rsplit("/", 1)[0] + "/alias.md"
            alias = os.path.join(self.target, *alias_relative.split("/"))
            os.symlink(os.path.basename(relative), alias)
            self.refuse(
                "this round writes",
                "--findings", "0", "--log", alias_relative,
            )

        def test_log_must_be_regular_contained_utf8_and_bounded(self):
            path = self.log_path()
            os.makedirs(os.path.dirname(path), exist_ok=True)
            self.refuse("regular file", "--findings", "0")

            self.write_record()
            os.remove(path)
            os.mkdir(path)
            self.refuse("regular file", "--findings", "0")
            os.rmdir(path)

            real = os.path.join(os.path.dirname(path), "real.md")
            Path(real).write_text("\n".join(self.record_lines()), encoding="utf-8")
            os.symlink("real.md", path)
            self.refuse("symlink", "--findings", "0")
            os.remove(path)

            Path(path).write_bytes(b"\xff\n")
            self.refuse("UTF-8", "--findings", "0")
            Path(path).write_bytes(b"x" * (2 * 1024 * 1024 + 1))
            self.refuse("byte cap", "--findings", "0")

        def test_log_refuses_delta_line_and_total_byte_caps(self):
            path = self.write_record()
            record = Path(path).read_bytes()
            Path(path).write_bytes(b"x" * (1024 * 1024 + 1) + b"\n" + record)
            self.refuse("physical line", "--findings", "0")

            Path(path).write_bytes(b"x" * (2 * 1024 * 1024 + 1))
            self.refuse("byte cap", "--findings", "0")

        def test_high_cardinality_risk_coverage_stays_within_the_input_bound(self):
            controller = hexctl_module()
            count = 30_000
            register = (
                "```risk-register\n"
                + "\n".join(
                    f"risk-{index} | boundary | check" for index in range(count)
                )
                + "\n```\n"
            )
            started = time.monotonic()
            with (
                mock.patch.object(controller, "receipted_source", return_value={}),
                mock.patch.object(
                    controller,
                    "source_risk_register",
                    return_value={"markdown": register},
                ),
            ):
                risk_ids = controller.audit_risk_ids(".", {})
            controller.audit_covered(
                "; ".join(f"{risk_id}=reviewed" for risk_id in risk_ids),
                risk_ids,
            )
            elapsed = time.monotonic() - started
            self.assertEqual(len(risk_ids), count)
            self.assertLess(elapsed, 1.0)

        def test_invalid_configured_path_refuses_without_a_traceback(self):
            for invalid in (
                "audit/rounds/\0fiat-test-topic.md",
                "audit/rounds/\ud800fiat-test-topic.md",
            ):
                with self.subTest(invalid=ascii(invalid)):
                    before = self.state_ledger_digests()
                    result = self.run_ctl(
                        "config", "set", "audit.log_path", json.dumps(invalid),
                        expect=2,
                    )
                    self.assertIn("config audit.log_path", result.stderr)
                    self.assertNotIn("Traceback", result.stderr)
                    self.assertEqual(self.state_ledger_digests(), before)

        def test_parent_symlink_swap_cannot_escape_the_descriptor_walk(self):
            controller = hexctl_module()
            with (
                tempfile.TemporaryDirectory() as raw_root,
                tempfile.TemporaryDirectory() as raw_outside,
            ):
                root = os.path.realpath(raw_root)
                outside = os.path.realpath(raw_outside)
                audit_dir = Path(root) / "audit"
                audit_dir.mkdir()
                (audit_dir / "AUDIT.md").write_bytes(b"inside")
                (Path(outside) / "AUDIT.md").write_bytes(b"outside")
                lexical = str(audit_dir / "AUDIT.md")
                real_open = os.open
                swapped = False

                def racing_open(target, flags, *args, **kwargs):
                    nonlocal swapped
                    opens_old_path = target == lexical
                    opens_new_component = target == "audit" and "dir_fd" in kwargs
                    if not swapped and (opens_old_path or opens_new_component):
                        swapped = True
                        audit_dir.rename(Path(root) / "audit-before-swap")
                        os.symlink(outside, audit_dir)
                    return real_open(target, flags, *args, **kwargs)

                stderr = StringIO()
                with mock.patch.object(controller.os, "open", side_effect=racing_open):
                    with redirect_stderr(stderr), self.assertRaises(SystemExit):
                        controller.read_configured_audit_log(
                            root, "audit/AUDIT.md", None
                        )
                self.assertIn("audit log path cannot be read", stderr.getvalue())

        def test_descriptor_walk_closes_a_child_when_its_stat_fails(self):
            controller = hexctl_module()
            with tempfile.TemporaryDirectory() as raw_root:
                root = os.path.realpath(raw_root)
                audit_dir = Path(root) / "audit"
                audit_dir.mkdir()
                (audit_dir / "AUDIT.md").write_bytes(b"inside")
                real_fstat = os.fstat
                opened = []

                def failing_child_stat(descriptor):
                    opened.append(descriptor)
                    if len(opened) == 2:
                        raise OSError("synthetic child fstat failure")
                    return real_fstat(descriptor)

                stderr = StringIO()
                with mock.patch.object(
                    controller.os, "fstat", side_effect=failing_child_stat
                ):
                    with redirect_stderr(stderr), self.assertRaises(SystemExit):
                        controller.read_configured_audit_log(
                            root, "audit/AUDIT.md", None
                        )
                self.assertIn("audit log path cannot be read", stderr.getvalue())

                still_open = []
                for descriptor in opened:
                    try:
                        real_fstat(descriptor)
                    except OSError:
                        continue
                    still_open.append(descriptor)
                    os.close(descriptor)
                self.assertEqual(still_open, [])

        def test_canonical_reopen_closes_a_child_when_parent_close_fails(self):
            controller = hexctl_module()
            with tempfile.TemporaryDirectory() as raw_root:
                root = os.path.realpath(raw_root)
                audit_dir = Path(root) / "audit"
                audit_dir.mkdir()
                (audit_dir / "AUDIT.md").write_bytes(b"inside")
                real_open = os.open
                real_close = os.close
                real_fstat = os.fstat
                opened = []
                close_failed = False

                def tracking_open(*args, **kwargs):
                    descriptor = real_open(*args, **kwargs)
                    opened.append(descriptor)
                    return descriptor

                def fail_current_parent_close(descriptor):
                    nonlocal close_failed
                    if len(opened) >= 5 and descriptor == opened[3] and not close_failed:
                        close_failed = True
                        raise OSError("synthetic parent close failure")
                    return real_close(descriptor)

                stderr = StringIO()
                with (
                    mock.patch.object(controller.os, "open", side_effect=tracking_open),
                    mock.patch.object(
                        controller.os, "close", side_effect=fail_current_parent_close
                    ),
                    redirect_stderr(stderr),
                    self.assertRaises(SystemExit),
                ):
                    controller.read_configured_audit_log(
                        root, "audit/AUDIT.md", None
                    )
                self.assertTrue(close_failed)
                self.assertIn("changed during read", stderr.getvalue())

                still_open = []
                for descriptor in opened:
                    try:
                        real_fstat(descriptor)
                    except OSError:
                        continue
                    still_open.append(descriptor)
                    real_close(descriptor)
                self.assertEqual(still_open, [])

        def test_descriptor_walk_refuses_a_platform_without_safe_primitives(self):
            controller = hexctl_module()
            with tempfile.TemporaryDirectory() as root:
                audit_dir = Path(root) / "audit"
                audit_dir.mkdir()
                (audit_dir / "AUDIT.md").write_bytes(b"inside")
                stderr = StringIO()
                with mock.patch.object(controller.os, "O_NOFOLLOW", 0):
                    with redirect_stderr(stderr), self.assertRaises(SystemExit):
                        controller.read_configured_audit_log(
                            root, "audit/AUDIT.md", None
                        )
                self.assertIn("platform cannot safely read", stderr.getvalue())

        def test_configured_log_read_refuses_an_observed_in_place_rewrite(self):
            controller = hexctl_module()
            with tempfile.TemporaryDirectory() as raw_root:
                root = os.path.realpath(raw_root)
                audit_dir = Path(root) / "audit"
                audit_dir.mkdir()
                log = audit_dir / "AUDIT.md"
                log.write_bytes(b"inside")
                real_fdopen = controller.os.fdopen

                class RacingHandle:
                    def __init__(self, descriptor, mode):
                        self.handle = real_fdopen(descriptor, mode)

                    def __enter__(self):
                        return self

                    def __exit__(self, *args):
                        self.handle.close()

                    def fileno(self):
                        return self.handle.fileno()

                    def read(self, size):
                        data = self.handle.read(size)
                        log.write_bytes(b"outside")
                        return data

                stderr = StringIO()
                with mock.patch.object(
                    controller.os, "fdopen", side_effect=RacingHandle
                ):
                    with redirect_stderr(stderr), self.assertRaises(SystemExit):
                        controller.read_configured_audit_log(
                            root, "audit/AUDIT.md", None
                        )
                self.assertIn("changed during read", stderr.getvalue())

        def test_configured_log_read_refuses_an_observed_parent_rebind(self):
            controller = hexctl_module()
            with tempfile.TemporaryDirectory() as raw_root:
                root = os.path.realpath(raw_root)
                audit_dir = Path(root) / "audit"
                audit_dir.mkdir()
                log = audit_dir / "AUDIT.md"
                log.write_bytes(b"inside")
                moved_dir = Path(root) / "moved-audit"
                real_fdopen = controller.os.fdopen

                class RacingHandle:
                    def __init__(self, descriptor, mode):
                        self.handle = real_fdopen(descriptor, mode)

                    def __enter__(self):
                        return self

                    def __exit__(self, *args):
                        self.handle.close()

                    def fileno(self):
                        return self.handle.fileno()

                    def read(self, size):
                        data = self.handle.read(size)
                        audit_dir.rename(moved_dir)
                        audit_dir.mkdir()
                        (audit_dir / "AUDIT.md").write_bytes(b"outside")
                        return data

                stderr = StringIO()
                with mock.patch.object(
                    controller.os, "fdopen", side_effect=RacingHandle
                ):
                    with redirect_stderr(stderr), self.assertRaises(SystemExit):
                        controller.read_configured_audit_log(
                            root, "audit/AUDIT.md", None
                        )
                self.assertIn("changed during read", stderr.getvalue())

        def test_fifo_swap_cannot_block_the_final_open(self):
            controller = hexctl_module()
            with tempfile.TemporaryDirectory() as raw_root:
                root = os.path.realpath(raw_root)
                audit_dir = Path(root) / "audit"
                audit_dir.mkdir()
                log = audit_dir / "AUDIT.md"
                log.write_bytes(b"inside")
                real_open = os.open
                swapped = False

                def racing_open(target, flags, *args, **kwargs):
                    nonlocal swapped
                    if not swapped and target == "AUDIT.md" and "dir_fd" in kwargs:
                        self.assertTrue(flags & os.O_NONBLOCK)
                        swapped = True
                        log.unlink()
                        os.mkfifo(log)
                    return real_open(target, flags, *args, **kwargs)

                stderr = StringIO()
                with mock.patch.object(controller.os, "open", side_effect=racing_open):
                    with redirect_stderr(stderr), self.assertRaises(SystemExit):
                        controller.read_configured_audit_log(
                            root, "audit/AUDIT.md", None
                        )
                self.assertIn("not a regular file", stderr.getvalue())

        def test_escaping_configured_log_is_refused(self):
            before = self.state_ledger_digests()
            result = self.run_ctl(
                "config", "set", "audit.log_path", '"../fiat-test-topic.md"',
                expect=2,
            )
            self.assertIn("no '..' component", result.stderr)
            self.assertEqual(self.state_ledger_digests(), before)

        def test_valid_rounds_store_schema_timestamp_digest_offset_and_exact_verdicts(self):
            expected_verdicts = ["guarded", "unguarded", "passed", "inconclusive", None]
            relative = self.state()["config"]["audit"]["log_path"]
            for index, verdict in enumerate(expected_verdicts, 1):
                findings = 0 if verdict is None else 1
                self.write_record(
                    findings=findings,
                    verdict=verdict or "null",
                    append=index > 1,
                )
                args = ["--findings", str(findings), "--log", relative]
                if verdict is not None:
                    args += [
                        "--fixes-commit", f"fix-{index}",
                        "--elenchus-verdict", verdict,
                    ]
                self.run_ctl("audit-round", *args)
                round_entry = self.state()["steps"][0]["audit"]["rounds"][-1]
                self.assertEqual(round_entry.get("schema"), "fiat-audit-round/v2")
                self.assertEqual(round_entry["log"], relative)
                self.assertEqual(
                    round_entry.get("record_timestamp"), "2026-08-23T02:17:46Z"
                )
                self.assertRegex(
                    round_entry.get("entry_sha256", ""), r"^[0-9a-f]{64}$"
                )
                self.assertRegex(
                    round_entry.get("synopsis_sha256", ""), r"^[0-9a-f]{64}$"
                )
                self.assertEqual(
                    round_entry.get("log_end_offset"), os.path.getsize(self.log_path())
                )
                self.assertEqual(round_entry["elenchus_verdict"], verdict)

            events = [
                json.loads(line)["data"]
                for line in Path(
                    os.path.join(self.target, ".hexaemeron", "ledger.jsonl")
                ).read_text(encoding="utf-8").splitlines()
                if json.loads(line)["event"] == "audit-round"
            ]
            self.assertEqual(
                [event.get("elenchus_verdict") for event in events], expected_verdicts
            )

        def test_audit_closure_cannot_replace_the_checked_log_path(self):
            self.write_record()
            self.run_ctl("audit-round", "--findings", "0")
            relative = self.state()["config"]["audit"]["log_path"]
            before = self.state_ledger_digests()
            result = self.run_ctl(
                "done", "audit", "--log", "other/AUDIT.md", expect=2
            )
            self.assertIn("final round", result.stderr)
            self.assertEqual(self.state_ledger_digests(), before)

            self.run_ctl("done", "audit", "--log", relative)
            self.assertEqual(
                self.state()["steps"][0]["receipts"]["audit"]["log"],
                relative,
            )


    return AuditRecordSchemaTests
