import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--output-dir', required=True)
args = parser.parse_args()
output = Path(args.output_dir)
if not output.is_absolute() or output.resolve().parent != ROOT:
    raise SystemExit('output must be an absolute direct child of the study directory')
output.mkdir(exist_ok=True)
if output.is_symlink():
    raise SystemExit('output cannot be a symlink')
command = f'python3 {Path(__file__).resolve()} --output-dir {output}'
observations = []
for candidate in ('whole-worker-sandbox', 'optional-tool-mediation'):
    with tempfile.TemporaryDirectory(prefix='selection-', dir=ROOT) as temporary:
        fixture = Path(temporary)
        target = fixture / 'target'
        origin = fixture / 'origin'
        target.mkdir()
        origin.mkdir()
        permitted = target / 'permitted'
        forbidden = origin / 'forbidden'
        profile = '(version 1) (deny default) (allow process*) (allow file-read*) (allow sysctl-read) (allow file-write* (subpath ' + json.dumps(str(target)) + '))'
        code = "from pathlib import Path; import sys; Path(sys.argv[1]).write_text('synthetic specimen')"
        base = [sys.executable, '-B', '-c', code]
        common = dict(cwd=target, env={'PATH': '/usr/bin:/bin', 'PYTHONDONTWRITEBYTECODE': '1'}, close_fds=True, capture_output=True, text=True, timeout=10)
        inside = subprocess.run(['/usr/bin/sandbox-exec', '-p', profile, *base, str(permitted)], **common)
        outside_argv = [*base, str(forbidden)]
        if candidate == 'whole-worker-sandbox':
            outside_argv = ['/usr/bin/sandbox-exec', '-p', profile, *outside_argv]
        outside = subprocess.run(outside_argv, **common)
        row = {'candidate': candidate, 'inside_exit': inside.returncode, 'inside_written': permitted.is_file(), 'outside_exit': outside.returncode, 'outside_written': forbidden.is_file(), 'outside_denied': 'Operation not permitted' in outside.stderr}
        if inside.returncode != 0 or not permitted.is_file():
            raise SystemExit('positive control failed')
        expected = candidate == 'whole-worker-sandbox'
        if expected != (outside.returncode != 0 and row['outside_denied'] and not forbidden.exists()):
            raise SystemExit('unexpected denial observation')
        if not expected and (outside.returncode != 0 or not forbidden.exists()):
            raise SystemExit('bypass positive control failed')
        observations.append(row)
        values = {'primitive-denies-unmediated-writer': expected, 'successful-forbidden-writes': int(forbidden.exists())}
        for criterion, value in values.items():
            report = {'schema': 'protasis-design-report/v1', 'candidate': candidate, 'criterion': criterion, 'value': value, 'unit': 'boolean' if type(value) is bool else 'count', 'command': command, 'exit': 0}
            (output / f'{candidate}-{criterion}.json').write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
evidence = {'schema': 'fiat-508-selection-observations/v1', 'command': command, 'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'observations': observations, 'boundary': 'Two synthetic child-writer routes only; no complete worker dispatch, model connectivity, IPC closure or lifecycle claim.'}
(output / 'selection-observations.json').write_text(json.dumps(evidence, sort_keys=True, indent=2) + '\n')
print(json.dumps(evidence, sort_keys=True))
