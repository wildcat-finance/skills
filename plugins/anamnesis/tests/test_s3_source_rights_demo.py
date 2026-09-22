"""Exercise the rebuilt corpora and preserve the source-rights scope boundary."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
PLUGIN = ROOT / 'plugins/anamnesis'
SKILL = PLUGIN / 'skills/anamnesis'
DOCS = PLUGIN / 'docs/source-rights'
SCRIPT = SKILL / 'scripts/anamnesis.py'
CASES = {
    'pilot': ('4fb98a0684cd4704ce038787f62e860e33a0fc1c3562670c2d9146a39f0aea9f', 41, 19, 31, 12, 2, 144),
    'estate': ('b321c3541cc665b9adc8734fe83c342ee9260612a3e93ff519f97922d28279b2', 17, 0, 4, 0, 4, 59),
    'synopsis': ('8e827216e88a2735e0e88619c72c93e1a67b0891b7e9c6beac7625a1878cdb3d', 41, 19, 31, 12, 2, 144),
}
FIELDS = ('id', 'sha256', 'bytes', 'disclosure', 'basis', 'rights_sha256')


def canonical(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def load_script():
    spec = importlib.util.spec_from_file_location('source_rights_demo', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SourceRightsWholePath(unittest.TestCase):
    def test_actual_demo_commands_cover_all_three_corpora(self):
        for name, (identity, findings, _, rounds, empty, high, unknown) in CASES.items():
            with self.subTest(specimen=name):
                run = subprocess.run(
                    [sys.executable, str(SCRIPT), 'demo', '--specimen',
                     str(PLUGIN / 'specimens' / name)],
                    cwd=ROOT, capture_output=True, text=True, timeout=60)
                self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                expected = [
                    f'1. two fresh builds agree on {identity} across 7 components',
                    f'2. the committed release verifies: {findings} finding(s), {rounds} round(s), {empty} with no findings',
                    f'3. Elenchus analogues for severity high: {high}; verdict None',
                    f'4. Synkrisis cohort cohort:{identity[:16]}: {findings} included against {findings} findings; 0 exclusion(s), {unknown} unknown(s)',
                ]
                self.assertEqual(run.stdout.splitlines()[:4], expected)
                self.assertIn('No budget is declared for either, so neither gates.', run.stdout)

    def test_all_source_rows_and_release_preimages_match_independent_construction(self):
        for name, (identity, *_) in CASES.items():
            with self.subTest(specimen=name):
                specimen = PLUGIN / 'specimens' / name
                admission = json.loads((specimen / 'policy.json').read_bytes())
                manifest = json.loads((specimen / 'release/manifest.json').read_bytes())
                expected = []
                for source in admission['sources']:
                    row = {key: source[key] for key in ('id', 'sha256', 'bytes')}
                    row.update(basis=source['rights']['basis'], disclosure=source['rights']['disclosure'],
                               rights_sha256=hashlib.sha256(canonical(source['rights'])).hexdigest())
                    expected.append(row)
                expected.sort(key=lambda row: row['id'])
                self.assertEqual(manifest['sources'], expected)
                digest = hashlib.sha256(canonical(json.loads((specimen / 'curation-policy.json').read_bytes())))
                for row in expected:
                    self.assertEqual(set(row), set(FIELDS))
                    digest.update(':'.join(str(row[key]) for key in FIELDS).encode())
                for key in ('engagements', 'assertions', 'relations', 'quarantine', 'unknowns'):
                    digest.update(canonical(json.loads((specimen / 'release' / (key + '.json')).read_bytes())))
                self.assertEqual(manifest['release_id'], digest.hexdigest())
                self.assertEqual(manifest['release_id'], identity)

    def test_consumer_views_keep_counts_denominators_and_privacy(self):
        module = load_script()
        for name, (identity, findings, remediations, rounds, empty, high, unknown) in CASES.items():
            with self.subTest(specimen=name):
                specimen = PLUGIN / 'specimens' / name
                release = specimen / 'release'
                manifest, _ = module.verify_release(str(release))
                analogue = module.analogues(str(release), 'severity', 'high')
                cohort = module.observations(str(release), 'every public finding in the release')
                self.assertEqual(manifest['counts']['remediations'], remediations)
                self.assertEqual(cohort['denominators'], manifest['counts'] | {'findings_withheld_by_disclosure': 0})
                self.assertEqual(cohort['cohort']['included'], findings)
                self.assertEqual(cohort['release_id'], identity)
                self.assertEqual(analogue['release_id'], identity)
                self.assertEqual(len(analogue['analogues']), high)
                self.assertIsNone(analogue['verdict'])
                self.assertEqual(cohort['unknowns'], manifest['unknowns'])
                self.assertEqual(sum(cohort['unknowns'].values()), unknown)
                self.assertEqual(cohort['denominators']['rounds'], rounds)
                self.assertEqual(cohort['denominators']['rounds_with_no_findings'], empty)
                self.assertEqual(analogue, json.loads((specimen / 'projections/elenchus-severity-high.json').read_bytes()))
                self.assertEqual(cohort, json.loads((specimen / 'projections/synkrisis-cohort.json').read_bytes()))
                for row in manifest['sources']:
                    self.assertNotIn('holder', row)
                    self.assertNotIn('statement', row)

    def test_private_rights_prose_does_not_reach_releases_or_projections(self):
        module = load_script()
        for name in CASES:
            with self.subTest(specimen=name), tempfile.TemporaryDirectory() as directory:
                specimen = Path(directory) / name
                shutil.copytree(PLUGIN / 'specimens' / name, specimen)
                policy = specimen / 'policy.json'
                data = json.loads(policy.read_bytes())
                for source in data['sources']:
                    source['rights'].update(holder='Private holder sentinel 1364',
                                            statement='Private decision sentinel 1364')
                policy.write_bytes(canonical(data))
                release = Path(directory) / 'fresh-release'
                module._rebuild_once(str(specimen), str(release))
                analogue = module.analogues(str(release), 'severity', 'high')
                cohort = module.observations(str(release), 'every public finding in the release')
                released = b''.join(path.read_bytes() for path in release.iterdir()) + canonical(analogue) + canonical(cohort)
                self.assertNotIn(b'Private holder sentinel 1364', released)
                self.assertNotIn(b'Private decision sentinel 1364', released)

    def test_sources_policies_graphs_and_historical_records_remain_exact(self):
        preserved = json.loads((DOCS / 'preserved-inputs.json').read_bytes())
        self.assertEqual(preserved['base'], '7952eafa337f5ba1c4f45417ceb154673f629c1c')
        self.assertGreaterEqual(len(preserved['files']), 33)
        self.assertIn('docs/kickoff/1359/evidence/consumer-inputs.json', preserved['files'])
        for path, digest in preserved['files'].items():
            with self.subTest(path=path):
                self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), digest)
        for name, entry in preserved['ledger_prefixes'].items():
            history = (SKILL / name).read_bytes().split(b'## History\n', 1)[1]
            self.assertEqual(hashlib.sha256(history[:entry['bytes']]).hexdigest(), entry['sha256'])

    def test_generation_retains_the_held_frontier_and_input(self):
        text = (SKILL / 'EVOLUTION.md').read_text()
        fields = dict(re.findall(r'^- ([^:]+): (.*)$', text, re.M))
        self.assertEqual(fields['Current version'], '`anamnesis-v5.2.0`')
        frontier = '|'.join(fields[key].strip('`') for key in (
            'Frontier status', 'Frontier revision', 'Current frontier', 'Next Fiat job')) + '\n'
        self.assertEqual(hashlib.sha256(frontier.encode()).hexdigest(),
                         'df27b276252cc4045a18c202b8b00782fe4dc40835b3eafca3935f48900e13f9')
        declared = text.split('```declared-inputs\n', 1)[1].split('```', 1)[0]
        self.assertEqual(declared, 'second-producer-findings | corpus | absent | Audit findings a party outside this repository produced, together with a rights basis that permits redistributing them.\n')
        self.assertIn('| `anamnesis-v5.2.0` | generation |', text)
        self.assertIn('version: "5.2.0"', (SKILL / 'SKILL.md').read_text())

    def test_demonstration_generation_preserves_frontier_and_nonclaim(self):
        text = (SKILL / 'DEMONSTRATION.md').read_text()
        record = json.loads(re.search(r'```shoggoth-demonstration\n(.*?)\n```', text, re.S).group(1))
        self.assertEqual(record['frontier']['version'], 'anamnesis-demo-v0.7.0')
        self.assertEqual(record['frontier']['sha256'], '04859403f738c0e6c358e794307f9db5abecd53f5ec8ec2dd7a2863886086374')
        self.assertEqual(record['frontier']['next'], 'Admit a second independent audit corpus so the path is shown over more than one producer.')
        self.assertEqual(record['non_claim'], 'It does not establish that the corpus is complete, that any finding is real, or that any remediation is correct.')
        for source in record['sources']:
            self.assertEqual(hashlib.sha256((ROOT / source['path']).read_bytes()).hexdigest(), source['sha256'])


if __name__ == '__main__':
    unittest.main()
