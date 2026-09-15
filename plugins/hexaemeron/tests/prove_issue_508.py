#!/usr/bin/env python3
"""Execute due native specimens; refuse every pending criterion."""

import argparse
import hashlib
from io import StringIO
import unittest
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/fiat/scripts"))
import worker_exec


CANDIDATES = ("whole-worker-sandbox", "optional-tool-mediation")
CRITERIA = (
    "whole-launch-dispatch", "worker-deadline", "worker-output-cap",
    "origin-drift-recovery", "single-cumulative-reconstruction",
    "executed-inoculation-guards", "carryover-lineage-recovery",
    "source-owned-report-compatibility", "gate-parser-no-execution",
    "gate-receipt-replay", "whole-path-demonstration",
)


IMPLEMENTED = frozenset({("whole-worker-sandbox", "worker-deadline"),
                         ("whole-worker-sandbox", "worker-output-cap"),
                         ("whole-worker-sandbox", "whole-launch-dispatch"),
                         ("whole-worker-sandbox", "origin-drift-recovery"),
                         ("whole-worker-sandbox", "single-cumulative-reconstruction"),
                         ("whole-worker-sandbox", "executed-inoculation-guards"),
                         ("whole-worker-sandbox", "carryover-lineage-recovery"),
                         ("whole-worker-sandbox", "source-owned-report-compatibility"),
                         ("whole-worker-sandbox", "gate-parser-no-execution"),
                         ("whole-worker-sandbox", "gate-receipt-replay"),
                         ("whole-worker-sandbox", "whole-path-demonstration")})


def dispatch_request(root, code, *, origin=None):
    """Retain the producer-relative declaration; only child argv is resolved."""
    source = ".hexaemeron/reports/result.json"
    return {"schema": "fiat-worker-request/v1", "root": str(root),
            "argv": [str(Path(sys.executable).resolve()), "-I", "-c", code, source],
            "tools": list(worker_exec.TOOLS), "deadline_seconds": 10,
            "output_cap_bytes": worker_exec.DEFAULT_CAP,
            "reports": [{"index": 4, "source": source, "output": "result.json"}],
            "origin": origin or {"root": str(root), "paths": []}}


def dispatch_cli(root, request, pass_fds=()):
    request_path = root / "request.json"
    request_path.write_text(json.dumps(request))
    command = [sys.executable, str(Path(worker_exec.__file__).with_name("hexctl.py")),
               "--dir", str(root), "worker-exec", "--request", str(request_path)]
    result = subprocess.run(command, capture_output=True, timeout=20, check=False,
                            pass_fds=pass_fds)
    require(result.returncode in (0, 1), "controller-launch-refused")
    launch = json.loads(result.stdout)
    require(launch["record"]["request"] == request, "source-declaration-rewritten")
    return launch


def admit_cli(root, launch):
    command = [sys.executable, str(Path(worker_exec.__file__).with_name("hexctl.py")),
               "--dir", str(root), "worker-admit", "--receipt", launch["receipt"],
               "--sha256", launch["sha256"]]
    return subprocess.run(command, capture_output=True, timeout=10, check=False)


def execute_dispatch(criterion, root):
    """Exercise the real controller CLI and its native descendants."""
    origin = root / "origin"
    origin.mkdir()
    (origin / "user.txt").write_text("original")
    (origin / ".git").mkdir()
    (origin / ".git/config").write_text("shared")
    target = root / "target"
    target.mkdir()
    (target / ".hexaemeron").mkdir()
    (target / ".hexaemeron/live").write_text("live")
    (target / ".git").write_text("gitdir: " + str(origin / ".git"))
    declaration = {"root": str(origin), "paths": ["user.txt"]}
    observations = []
    if criterion == "origin-drift-recovery":
        code = ("import pathlib,sys\n"
                f"p=pathlib.Path({str(origin / 'user.txt')!r})\n"
                "try: p.write_text('worker')\n"
                "except PermissionError: pass\n"
                "else: raise SystemExit(9)\n"
                "pathlib.Path(sys.argv[1]).write_text('captured')")
        first = dispatch_cli(target, dispatch_request(target, code, origin=declaration))
        require((origin / "user.txt").read_text() == "original", "origin-worker-write")
        require(first["record"]["status"] == "ready", "origin-baseline-refused")
        (origin / "user.txt").write_text("independent")
        refusal = admit_cli(target, first)
        require(refusal.returncode == 2 and b"origin-drift-preserved" in refusal.stderr,
                "origin-drift-admitted")
        require((origin / "user.txt").read_text() == "independent", "origin-drift-discarded")
        fresh = dispatch_cli(target, dispatch_request(target, code, origin=declaration))
        require(fresh["record"]["attribution"] == "unknown", "invented-attribution")
        require(fresh["record"]["origin_before"] != first["record"]["origin_before"],
                "origin-not-resnapshotted")
        require(admit_cli(target, fresh).returncode == 0, "resnapshot-admission-failed")
        observations.extend([first["record"], fresh["record"]])
    else:
        python = str(Path(sys.executable).resolve())
        outside = [str(origin / "user.txt"), str(origin / ".git/config"),
                   str(target / ".hexaemeron/live"), str(target / ".git")]
        sentinel = os.open(origin / "user.txt", os.O_RDONLY)
        try:
            code = ("import os,pathlib,subprocess,sys,socket,json\n"
                    "p=pathlib.Path('inside'); p.write_text('old\\n')\n"
                    "patch='--- inside\\n+++ inside\\n@@ -1 +1 @@\\n-old\\n+new\\n'\n"
                    "r=subprocess.run(['/bin/sh','-c','/usr/bin/patch inside'],input=patch,text=True,capture_output=True)\n"
                    "assert r.returncode==0 and p.read_text()=='new\\n'\n"
                    f"targets={outside!r}\n"
                    "for name in targets:\n"
                    " for op in ('read','write','link'):\n"
                    "  try:\n"
                    "   if op=='read': pathlib.Path(name).read_bytes()\n"
                    "   elif op=='write': pathlib.Path(name).write_text('escape')\n"
                    "   else: os.link(name,'hard-alias')\n"
                    "  except PermissionError: pass\n"
                    "  else: raise SystemExit(10)\n"
                    " for tool in (['/bin/sh','-c','printf escaped >\"$1\"','sh',name],"
                    " ['/usr/bin/patch',name]):\n"
                    "  r=subprocess.run(tool,input=patch,text=True,capture_output=True)\n"
                    "  assert r.returncode!=0\n"
                    "os.symlink(targets[0],'alias')\n"
                    "try: pathlib.Path('alias').write_text('escape')\n"
                    "except PermissionError: pass\n"
                    "else: raise SystemExit(11)\n"
                    f"try: os.fstat({sentinel})\n"
                    "except OSError: pass\n"
                    "else: raise SystemExit(12)\n"
                    "for argv in (['/usr/bin/sandbox-exec','-p','(version 1)(allow default)','/bin/sh','-c','true'],['/usr/bin/curl','--version']):\n"
                    " try: subprocess.run(argv,check=True,capture_output=True)\n"
                    " except (PermissionError,subprocess.CalledProcessError): pass\n"
                    " else: raise SystemExit(13)\n"
                    "for family in (socket.AF_INET,socket.AF_UNIX):\n"
                    " try:\n"
                    "  s=socket.socket(family,socket.SOCK_STREAM)\n"
                    "  if family==socket.AF_INET: s.connect(('127.0.0.1',9))\n"
                    "  else: s.bind('ipc.sock')\n"
                    " except PermissionError: pass\n"
                    " else: raise SystemExit(14)\n"
                    "pathlib.Path(sys.argv[1]).write_text('private-result')")
            launch = dispatch_cli(target, dispatch_request(target, code, origin=declaration), (sentinel,))
        finally:
            os.close(sentinel)
        require(launch["record"]["status"] == "ready", "whole-dispatch-not-captured")
        require(admit_cli(target, launch).returncode == 0, "whole-dispatch-not-admitted")
        require((target / ".hexaemeron/reports/result.json").read_text() == "private-result",
                "admitted-bytes-mismatch")
        observations.append(launch["record"])
        detached = root / "detached"
        detached.mkdir()
        child = ("import os,time,pathlib\nos.setsid()\npathlib.Path('ready').touch()\n"
                 "time.sleep(.8)\np=pathlib.Path(os.environ['FIAT_OUTPUT_DIR'])/'result.json'\n"
                 "p.write_text('late-change')\nuntil=time.monotonic()+4\n"
                 "while time.monotonic()<until and not pathlib.Path('stop').exists(): time.sleep(.02)\n"
                 "pathlib.Path('stopped').touch()")
        code = ("import pathlib,subprocess,sys,time\npathlib.Path(sys.argv[1]).write_text('stable')\n"
                f"subprocess.Popen([{python!r},'-I','-c',{child!r}],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)\n"
                "until=time.monotonic()+2\n"
                "while not pathlib.Path('ready').exists() and time.monotonic()<until: time.sleep(.01)\n"
                "assert pathlib.Path('ready').exists()")
        launch = dispatch_cli(detached, dispatch_request(detached, code))
        scratch = Path(launch["record"]["capture"]["scratch_root"])
        try:
            require(launch["record"]["status"] == "ready", "detached-not-captured")
            time.sleep(1)
            require((scratch / "output/result.json").read_text() == "late-change", "detached-not-observed")
            require(admit_cli(detached, launch).returncode == 0, "private-snapshot-not-admitted")
            require((detached / ".hexaemeron/reports/result.json").read_text() == "stable",
                    "mutable-scratch-admitted")
        finally:
            (scratch / "stop").touch()
            until = time.monotonic()+2
            while not (scratch / "stopped").exists() and time.monotonic()<until:
                time.sleep(.02)
            require((scratch / "stopped").exists(), "detached-cleanup-ack-missing")
        observations.append(launch["record"])
    return observations


def require(condition, code):
    if not condition:
        raise worker_exec.Refusal(code)


REPLACEMENT_SPECIMENS = {
    "single-cumulative-reconstruction": ["two-exhausted-passes-one-packet", "current-base-complete-reconstruction",
        "omitted-payload-refused", "partial-mapping-refused", "no-gate-before-completion"],
    "executed-inoculation-guards": ["discovery-only-refused", "skipped-guard-refused", "replaced-guard-refused",
        "executed-passes-all-families", "new-independent-audit-after-guards"],
    "carryover-lineage-recovery": ["stale-source-refused", "duplicate-sequence-refused",
        "interrupted-admission-preserved", "missing-occurrence-refused", "attachment-digest-mismatch",
        "signed-fixed-tree-ref-required"],
}


def execute_replacement(criterion):
    require(sys.platform == "darwin", "unsupported-native-host")
    import test_carryover
    sources=[Path(__file__),Path(test_carryover.__file__),
             Path(test_carryover.__file__).with_name('hexctl_harness.py')]
    sources += [Path(worker_exec.__file__).with_name(name+'.py') for name in
                ('worker_exec','hexctl','carryover','replacement','inoculation')]
    before={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in sources}
    started=time.time()
    composed=test_carryover.ReplacementAdmissionTests(
        "test_signed_archive_to_native_admission_keeps_fresh_audit_and_pending_recovery")
    negative=test_carryover.ReplacementGuardAdmissionTests(
        "test_discovery_skips_and_replaced_bodies_cannot_supply_execution_evidence")
    log=StringIO()
    result=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.TestSuite([composed,negative]))
    require(result.wasSuccessful() and result.testsRun == 2 and not result.skipped,
            "replacement-specimens-failed: "+log.getvalue())
    observations={**composed.observations,**negative.observations}
    names=REPLACEMENT_SPECIMENS[criterion]
    inventory=json.loads((Path(__file__).parent/"fixtures/issue508/criteria.json").read_text())
    expected=next(row["specimens"] for row in inventory["criteria"] if row["id"]==criterion)
    require(names==expected and all(name in observations for name in names),"specimen-inventory-drift")
    after={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in sources}
    require(before==after,'replacement-specimen-source-drift')
    return {"criterion":criterion,"specimens":names,
            "observations":{name:observations[name] for name in names},
            "execution":{"testsRun":result.testsRun,"failures":len(result.failures),
                         "errors":len(result.errors),"skipped":len(result.skipped),"log":log.getvalue()},
            "sources":before,"source_observation":{"before_unix":started,"after_unix":time.time(),"unchanged":True},
            "scope":"Actual local signed Git, checkpoint, controller admission and native guard fixtures; attachment transport controlled. Temporary fixture roots are removed after observations. Historical unknowns remain unknown; no independent audit or model evaluation is claimed."}


GATE_SPECIMENS = {
    'source-owned-report-compatibility': ['relative-source-declaration-preserved', 'absolute-execution-destination', 'report-bytes-preserved', 'report-escape-refused'],
    'gate-parser-no-execution': ['malformed-fence', 'four-draft-brevitas', 'unsupported-substitution', 'injected-command-no-side-effect'],
    'gate-receipt-replay': ['finite-per-file-command', 'command-drift', 'cli-source-drift', 'adapter-drift', 'report-source-drift'],
}


def execute_gates(criterion):
    """Run the named nonexecuting validator/real controller/producer specimens."""
    import test_gate_commands as cases
    selected = {
        'source-owned-report-compatibility': (cases.GateReportTests, 'test_source_owned_report_bytes_and_relative_declaration'),
        'gate-parser-no-execution': (cases.GateConformanceTests, 'test_inert_parser_specimens'),
        'gate-receipt-replay': (cases.GateConformanceTests, 'test_exact_replay_specimens'),
    }
    cls, method = selected[criterion]
    primary = cls(method)
    tests = [primary]
    if criterion == 'gate-receipt-replay':
        tests += [cases.GateReceiptTests(name) for name in (
            'test_current_init_and_refusal_precede_runbook_mutation',
            'test_current_init_marker_cannot_be_downgraded',
            'test_full_cli_source_drift_blocks_mutation_then_fresh_amendment',
            'test_pending_amendment_recovers_after_actual_source_replacement',
            'test_historical_fixture_remains_legacy_without_backfill')]
    root = Path(__file__).resolve().parents[3]
    sources = [Path(__file__).resolve(), Path(cases.__file__).resolve(), cases.SOURCE,
               Path(__file__).with_name('hexctl_harness.py').resolve(),
               Path(worker_exec.__file__).with_name('hexctl.py').resolve(),
               root / 'plugins/hexaemeron/skills/elenchus/scripts/elenchus.py']
    sources += [root / path for path in cases.gates.REGISTRY]
    before = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources}
    started = time.time()
    log = StringIO()
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(unittest.TestSuite(tests))
    require(result.wasSuccessful() and result.testsRun == len(tests) and not result.skipped,
            'gate-specimens-failed: ' + log.getvalue())
    names = GATE_SPECIMENS[criterion]
    inventory = json.loads((Path(__file__).parent / 'fixtures/issue508/criteria.json').read_text())
    expected = next(row['specimens'] for row in inventory['criteria'] if row['id'] == criterion)
    require(names == expected and set(primary.observations) == set(names), 'gate-specimen-inventory-drift')
    after = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources}
    require(before == after, 'gate-specimen-source-drift')
    return {'criterion': criterion, 'specimens': names, 'observations': primary.observations,
            'execution': {'testsRun': result.testsRun, 'failures': len(result.failures),
                          'errors': len(result.errors), 'skipped': len(result.skipped), 'log': log.getvalue()},
            'sources': before, 'source_observation': {'before_unix': started, 'after_unix': time.time(), 'unchanged': True},
            'scope': 'Actual inert parser and source replay specimens; real disposable controller transitions where selected. The report compatibility specimen runs one real unittest assertion through the existing producer writer and Elenchus reader. No runbook command is executed by the gate adapter; no independent audit or whole delivery success is claimed.'}



def execute_lifecycle():
    """Execute the joined native fixture; delivery transport remains controlled."""
    require(sys.platform == 'darwin', 'unsupported-native-host')
    import test_confined_replacement_lifecycle as cases
    root = Path(__file__).resolve().parents[3]
    sources = [Path(__file__).resolve(), Path(cases.__file__).resolve(),
               Path(__file__).with_name('test_carryover.py').resolve(),
               Path(__file__).parent / 'fixtures/issue508/criteria.json',
               Path(__file__).with_name('hexctl_harness.py').resolve(), root / cases.CLI,
               root / 'plugins/hexaemeron/skills/protasis/scripts/gate_commands.py',
               root / 'plugins/hexaemeron/skills/protasis/scripts/protasis.py']
    sources += sorted(Path(worker_exec.__file__).parent.glob('*.py'))
    before = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources}
    started = time.time()
    case = cases.ConfinedReplacementLifecycleTests(
        'test_exhausted_source_to_current_gate_audit_and_integration')
    log = StringIO()
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(unittest.TestSuite([case]))
    require(result.wasSuccessful() and result.testsRun == 1 and not result.skipped,
            'lifecycle-specimen-failed: ' + log.getvalue())
    names = ['exhaust-export-retire', 'complete-reconstruction', 'executed-inoculation',
             'independent-audit', 'matching-launch-and-gate-evidence', 'integration-refuses-mismatch']
    inventory = json.loads((Path(__file__).parent / 'fixtures/issue508/criteria.json').read_text())
    expected = next(row['specimens'] for row in inventory['criteria'] if row['id'] == 'whole-path-demonstration')
    require(names == expected and set(case.observations) == set(names), 'lifecycle-specimen-inventory-drift')
    after = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources}
    require(before == after, 'lifecycle-specimen-source-drift')
    return {'criterion': 'whole-path-demonstration', 'specimens': names,
            'observations': case.observations,
            'execution': {'testsRun': result.testsRun, 'failures': len(result.failures),
                          'errors': len(result.errors), 'skipped': len(result.skipped), 'log': log.getvalue()},
            'sources': before, 'source_observation': {'before_unix': started, 'after_unix': time.time(), 'unchanged': True},
            'scope': 'Actual local signed Git, archived exhaustion/export/retirement, complete current-base reconstruction, native mapped guards, current gate receipts and controller integration transitions. Attachment and host Git/GitHub delivery transport are controlled fixtures. The new audit round proves transition handling only; independent product Warden remains separate. No model backend, VM deployment, external publication or protection of conversation tools is claimed.'}

def execute(criterion, root):
    if criterion == "whole-path-demonstration":
        return execute_lifecycle()
    if criterion in GATE_SPECIMENS:
        return execute_gates(criterion)
    if criterion in REPLACEMENT_SPECIMENS:
        return execute_replacement(criterion)
    """Observe real native processes; no assertion supplied by the caller passes."""
    python = str(Path(sys.executable).resolve())
    observations = []

    def run(code, **kwargs):
        capture = worker_exec.run_worker(root, [python, "-I", "-c", code], **kwargs)
        observations.append(capture.record)
        return capture

    if criterion in ("whole-launch-dispatch", "origin-drift-recovery"):
        observations = execute_dispatch(criterion, root)
    elif criterion == "worker-deadline":
        child = ("import os,time,pathlib\nos.setsid()\nprint('ready',flush=True)\n"
                 "until=time.monotonic()+6\n"
                 "while time.monotonic()<until and not pathlib.Path('stop').exists(): time.sleep(.02)\n"
                 "pathlib.Path('stopped').write_text('ack')\n")
        code = ("import subprocess,time; "
                f"subprocess.Popen([{python!r},'-I','-c',{child!r}]); time.sleep(30)")
        capture = run(code, deadline_seconds=2)
        try:
            require(capture.record["code"] == "deadline", "deadline-specimen-did-not-time-out")
            require(capture.record["deadline_seconds"] == 2 and capture.record["elapsed_seconds"] < 10,
                    "deadline-return-bound")
            require(capture.record["snapshot"] is None and not capture.record["artifacts"],
                    "timeout-admitted-output")
            require(not capture.record["scratch_reusable"] and
                    capture.record["cleanup"].endswith("-retired"), "uncertain-cleanup-reused")
            require(capture.stdout == b"ready\n", "detached-specimen-not-started")
        finally:
            scratch = Path(capture.record["scratch_root"])
            (scratch / "stop").write_text("stop")
            until = time.monotonic() + 2
            while time.monotonic() < until and not (scratch / "stopped").exists():
                time.sleep(.02)
            require((scratch / "stopped").exists(), "detached-specimen-ack-missing")
    elif criterion == "worker-output-cap":
        cap = worker_exec.DEFAULT_CAP
        for artifact in (False, True):
            for excess in (0, 1):
                if artifact:
                    code = ("import os; open(os.environ['FIAT_OUTPUT_DIR']+'/x','wb').write("
                            f"b'x'*{cap + excess})")
                else:
                    code = f"import os; os.write(1,b'x'*{cap + excess})"
                capture = run(code, outputs=["x"] if artifact else [],
                              deadline_seconds=5, output_cap_bytes=cap)
                record = capture.record
                require(record["stream_bytes"] + record["artifact_bytes"] <= cap and
                        len(capture.stdout) + len(capture.stderr) <= cap, "retained-buffer-excess")
                if excess:
                    require(record["status"] == "refused" and record["code"] == "output-cap"
                            and record["snapshot"] is None, "first-excess-admitted")
                else:
                    require(record["status"] == "captured" and
                            record["stream_bytes"] + record["artifact_bytes"] == cap,
                            "exact-cap-not-captured")
    else:
        raise worker_exec.Refusal("executor-unimplemented")
    inventory = json.loads((Path(__file__).parent / "fixtures/issue508/criteria.json").read_text())
    names = next(item["specimens"] for item in inventory["criteria"] if item["id"] == criterion)
    expected = {
        "whole-launch-dispatch": ["inside-shell-python-patch", "outside-shell-python-patch",
                                  "symlink-escape", "live-git-and-controller-metadata",
                                  "external-deputy-unavailable", "inherited-descriptor-closed",
                                  "host-ipc-denied", "nested-policy-loosening-denied",
                                  "detached-writer-private-snapshot"],
        "origin-drift-recovery": ["denied-origin-write-unchanged", "independent-drift-preserved",
                                  "no-invented-attribution", "resnapshot"],
        "worker-deadline": ["two-second-deadline", "ten-second-return-bound",
                            "timeout-admission-refused", "uncertain-cleanup-no-reuse"],
        "worker-output-cap": ["one-mib-stream", "first-stream-excess", "one-mib-artifact",
                              "first-artifact-excess", "bounded-retained-buffer"],
    }
    require(names == expected[criterion], "specimen-inventory-drift")
    return {"criterion": criterion, "specimens": names, "captures": observations}


def main(argv=None):
    """Publish a boolean only after the complete due native specimen set."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, choices=CANDIDATES)
    parser.add_argument("--criterion", required=True, choices=CRITERIA)
    parser.add_argument("--report", required=True)
    args = parser.parse_args(argv)
    if (args.candidate, args.criterion) in IMPLEMENTED:
        try:
            with tempfile.TemporaryDirectory(prefix="fiat-native-conformance-") as temp:
                evidence = execute(args.criterion, Path(temp).resolve())
            report = Path(args.report)
            command = shlex.join(["python3", "plugins/hexaemeron/tests/prove_issue_508.py",
                                  "--candidate", args.candidate, "--criterion", args.criterion,
                                  "--report", args.report])
            payload = {"schema": "protasis-design-report/v1", "candidate": args.candidate,
                       "criterion": args.criterion, "value": True, "unit": "boolean",
                       "command": command, "exit": 0}
            report.parent.mkdir(parents=True, exist_ok=True)
            report.with_suffix(".observations.json").write_text(json.dumps(evidence, indent=2) + "\n")
            report.write_text(json.dumps(payload, indent=2) + "\n")
            return 0
        except (worker_exec.Refusal, OSError, ValueError) as exc:
            print(json.dumps({"schema": "issue508-conformance-refusal/v1",
                              "code": str(exc), "criterion": args.criterion}))
            return 1
    print(json.dumps({
        "schema": "issue508-conformance-refusal/v1",
        "event": "issue508_conformance_refused",
        "code": "executor-unimplemented",
        "promise": "protasis-runbook-readiness",
        "candidate": args.candidate,
        "criterion": args.criterion,
        "consequence": 2,
        "blocked_transition": "criterion-acceptance",
        "recovery": "Implement and execute the complete declared specimen set, then rerun.",
    }, sort_keys=True))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
