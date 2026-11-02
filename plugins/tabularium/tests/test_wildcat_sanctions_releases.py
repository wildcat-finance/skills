"""Version replay and hostile digest rebinding over constructed raw releases."""

from copy import deepcopy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wildcat_sanctions_fixtures import raw_release
from wildcat_v3_public_fixtures import rebuild_example as rebuild_native
from wildcat_batch_public_fixtures import rebuild_example as rebuild_batches
from tabularium_lib.core import TabulariumError, canonical_json, sha256_bytes
from tabularium_lib.wildcat_release import build_wildcat_canonical, verify_wildcat_canonical
from tabularium_lib import release_v2


def write(root,name,value):
    (root/name).write_bytes(canonical_json(value)+b'\n')


def read(root,name):
    return json.loads((root/name).read_bytes())


def rebind(root,name):
    data=(root/name).read_bytes()
    if name=='source.json':
        capture=read(root,'capture.json');capture['source']={'sha256':sha256_bytes(data),'bytes':len(data)}
        write(root,'capture.json',capture)
    manifest=read(root,'coverage.json')
    key={'source.json':'source','capture.json':'capture_manifest','events.jsonl':'canonical'}[name]
    manifest[key].update(sha256=sha256_bytes(data),bytes=len(data))
    if name=='source.json':
        capture=(root/'capture.json').read_bytes()
        manifest['capture_manifest'].update(sha256=sha256_bytes(capture),bytes=len(capture))
    write(root,'coverage.json',manifest)


class SanctionsReleaseTests(unittest.TestCase):
    def build(self,base,venue='wildcat-v2',version='1.3.0'):
        raw=raw_release(base,venue);root=base/'canonical'
        build_wildcat_canonical(raw,root,venue+'-constructed-sanctions-control',adapter_version=version)
        verify_wildcat_canonical(root/'coverage.json')
        return root

    def test_current_constructed_releases_rebuild_move_and_verify(self):
        for venue in ('wildcat-v1','wildcat-v2'):
            with self.subTest(venue=venue),tempfile.TemporaryDirectory() as temporary:
                base=Path(temporary).resolve();root=self.build(base,venue)
                source=read(root,'source.json');manifest=read(root,'coverage.json')
                self.assertEqual(manifest['versions']['adapter']['version'],'1.3.0')
                self.assertTrue(any(m['routing_joins'] for m in source['mapping_records']))
                self.assertTrue(all('routing_joins' in m for m in source['mapping_records']))
                second=base/'rebuilt'
                build_wildcat_canonical(root/'source/raw-release',second,manifest['release'])
                for path in root.rglob('*'):
                    if path.is_file():self.assertEqual(path.read_bytes(),(second/path.relative_to(root)).read_bytes())
                moved=base/'moved';shutil.move(second,moved)
                shutil.rmtree(root);verify_wildcat_canonical(moved/'coverage.json')

    def test_legacy_release_replays_unsupported_companions_without_new_fields(self):
        for venue in ('wildcat-v1','wildcat-v2'):
            with self.subTest(venue=venue),tempfile.TemporaryDirectory() as temporary:
                root=self.build(Path(temporary).resolve(),venue,'1.0.0')
                source=read(root,'source.json')
                self.assertTrue(all('routing_joins' not in m for m in source['mapping_records']))
                companions=[m for m in source['mapping_records'] if 'SanctionedAccountAssets' in (m['signature'] or '')]
                self.assertTrue(companions)
                self.assertTrue(all(m['disposition']=='unsupported-canonical-meaning' for m in companions))

    def test_all_preexisting_public_native_and_batch_examples_reproduce(self):
        for venue in ('wildcat-v1','wildcat-v2'):
            self.assertEqual(rebuild_native(venue),0)
            self.assertEqual(rebuild_batches(venue),0)

    def test_rehashed_source_cannot_erase_or_rewrite_closed_routing_evidence(self):
        for mutation in ('erase','rule','conditions','class','selector','disposition','extra-key'):
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as temporary:
                root=self.build(Path(temporary).resolve());source=read(root,'source.json')
                mapping=next(m for m in source['mapping_records'] if m['routing_joins'])
                relation=mapping['routing_joins'][0]
                if mutation=='erase':mapping['routing_joins']=[]
                elif mutation=='rule':relation['rule']='first-match'
                elif mutation=='conditions':relation['conditions']['amount']='41'
                elif mutation=='class':relation['evidence_class']='proved'
                elif mutation=='selector':relation['companion_selector']='wildcat-journal:'+'0'*64
                elif mutation=='disposition':mapping['disposition']='supporting-routing'
                else:relation['identity']='invented'
                write(root,'source.json',source);rebind(root,'source.json')
                with self.assertRaisesRegex(TabulariumError,'source.json differs'):
                    verify_wildcat_canonical(root/'coverage.json')

    def test_rehashed_canonical_cannot_rewrite_units_parties_or_provenance(self):
        for mutation in ('party','amount','units','support','duplicate'):
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as temporary:
                root=self.build(Path(temporary).resolve())
                events=[json.loads(line) for line in (root/'events.jsonl').read_text().splitlines()]
                event=events[0]
                if mutation=='party':event['parties'][0]['address']='0x'+'99'*20
                elif mutation=='amount':event['amounts'][0]['base_units']='41'
                elif mutation=='units':event['amounts'][0]['kind']='assets'
                elif mutation=='support':event['provenance']['supporting_selectors']=[]
                else:events.append(deepcopy(event))
                (root/'events.jsonl').write_bytes(b''.join(canonical_json(e)+b'\n' for e in events));rebind(root,'events.jsonl')
                with self.assertRaises(TabulariumError):verify_wildcat_canonical(root/'coverage.json')

    def test_legacy_forged_new_relations_and_current_erased_dispositions_refuse(self):
        for version in ('1.0.0','1.3.0'):
            with self.subTest(version=version),tempfile.TemporaryDirectory() as temporary:
                root=self.build(Path(temporary).resolve(),version=version);source=read(root,'source.json')
                companion=next(m for m in source['mapping_records'] if 'SanctionedAccountAssets' in (m['signature'] or ''))
                if version=='1.0.0':companion['routing_joins']=[]
                else:companion['disposition']='unsupported-canonical-meaning'
                write(root,'source.json',source);rebind(root,'source.json')
                with self.assertRaisesRegex(TabulariumError,'source.json differs'):
                    verify_wildcat_canonical(root/'coverage.json')

    def test_unknown_and_mixed_adapter_versions_refuse(self):
        for version in ('1.1.0','1.2.0','9.0.0','1.0.0'):
            with self.subTest(version=version),tempfile.TemporaryDirectory() as temporary:
                root=self.build(Path(temporary).resolve());manifest=read(root,'coverage.json')
                manifest['versions']['adapter']['version']=version;write(root,'coverage.json',manifest)
                with self.assertRaises(TabulariumError):verify_wildcat_canonical(root/'coverage.json')
        with tempfile.TemporaryDirectory() as temporary:
            base=Path(temporary).resolve();raw=raw_release(base)
            with self.assertRaises(TabulariumError):build_wildcat_canonical(raw,base/'bad','constructed',adapter_version='1.2.0')
            self.assertFalse((base/'bad').exists())

    def test_schema_and_python_agree_on_supported_versions(self):
        from test_wildcat_v3_schema_parity import locked_oracle
        schema=json.loads((Path(__file__).parents[1]/'schemas/canonical-event-v3.json').read_bytes())
        oracle=locked_oracle().Draft202012Validator(schema)
        with tempfile.TemporaryDirectory() as temporary:
            root=self.build(Path(temporary).resolve());events=[json.loads(line) for line in (root/'events.jsonl').read_text().splitlines()]
            for event in events:
                for version in ('1.0.0','1.3.0','1.2.0','9.0.0'):
                    row=deepcopy(event);row['provenance']['adapter_version']=version
                    accepted=version in ('1.0.0','1.3.0')
                    self.assertEqual(oracle.is_valid(row),accepted)
                    if accepted:release_v2.validate_event_row(row,release_v2.adapter_module(row['venue']),3)
                    else:
                        with self.assertRaises(TabulariumError):release_v2.validate_event_row(row,release_v2.adapter_module(row['venue']),3)

    def test_coverage_schema_and_python_agree_on_supported_versions(self):
        from test_wildcat_v3_schema_parity import locked_oracle
        schema=json.loads((Path(__file__).parents[1]/'schemas/coverage-manifest-v3.json').read_bytes())
        oracle=locked_oracle().Draft202012Validator(schema)
        for venue in ('wildcat-v1','wildcat-v2'):
            with tempfile.TemporaryDirectory() as temporary:
                root=self.build(Path(temporary).resolve(),venue);manifest=read(root,'coverage.json')
                for version in ('1.0.0','1.3.0','1.2.0','9.0.0'):
                    mutated=deepcopy(manifest);mutated['versions']['adapter']['version']=version
                    accepted=version in ('1.0.0','1.3.0')
                    self.assertEqual(oracle.is_valid(mutated),accepted)
                    if accepted:release_v2.validate_manifest(mutated,3)
                    else:
                        with self.assertRaises(TabulariumError):release_v2.validate_manifest(mutated,3)
