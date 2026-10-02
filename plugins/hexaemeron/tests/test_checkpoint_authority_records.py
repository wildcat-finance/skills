"""Closed protocol records, mandatory schema parity and authenticated byte guards."""
from __future__ import annotations

import copy
import contextlib
import fcntl
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / 'plugins/hexaemeron/skills/fiat/scripts'
sys.path.insert(0, str(SCRIPTS))
from checkpoint_authority import canonical as encoding
from checkpoint_authority import records, schema, signatures, trust
from checkpoint_authority.canonical import Refusal, canonical, decode, digest

FIXTURES = ROOT / 'plugins/hexaemeron/skills/fiat/checkpoint-authority/fixtures'


class RecordTests(unittest.TestCase):
    def test_container_record_tags_are_typed_refusals(self):
        for value in ([], {}, True, 1, None):
            with self.subTest(value=value), self.assertRaises(Refusal) as result:
                records.parse_record(canonical({'type': value}))
            self.assertEqual(result.exception.code, 'unsupported-record-type')


def specimen(kind):
    return decode((FIXTURES / (kind + '.json')).read_bytes())


def tool(name):
    path = os.environ.get('CHECKPOINT_' + name.upper().replace('-', '_')) or shutil.which(name)
    if not path:
        raise AssertionError('mandatory public verification tool absent: ' + name)
    path = str(Path(path).resolve())
    return signatures.ToolPin(name, path, digest(Path(path).read_bytes()))


def tools():
    return {name: tool(name) for name in ('openssl', 'ssh-keygen', 'gpg')}


# The profile accepts only the named-curve P-256 key. OpenSSL 3 writes that
# form by default, but LibreSSL, macOS's /usr/bin/openssl, writes explicit
# curve parameters unless the encoding is named (#1927).
P256_KEYGEN = ('genpkey', '-algorithm', 'EC', '-pkeyopt', 'ec_paramgen_curve:prime256v1',
               '-pkeyopt', 'ec_param_enc:named_curve')


def bootstrap():
    return trust.Bootstrap('test', 'test-service', 23, 'run-1',
                           ((FIXTURES / 'bootstrap.json').read_bytes(),))


def chain(name='trust-prefix'):
    return [canonical(value, limit=128*1024) for value in json.loads((FIXTURES / (name + '.json')).read_bytes())]


DESCENDANT_PROBE = '''import fcntl, os, time
ready_read, ready_write = os.pipe()
child = os.fork()
if child:
    os.close(ready_write)
    assert os.read(ready_read, 1) == b"1"
    with open("descendant.pid", "w") as output:
        output.write(str(child))
    print("{}", flush=True)
    os._exit(0)
os.close(ready_read)
with open("descendant.lock", "w") as held:
    fcntl.flock(held, fcntl.LOCK_EX)
    os.write(ready_write, b"1")
    time.sleep(60)
'''


def assert_descendant_stopped(case, directory):
    """A released lock observes process exit even when an orphan remains a zombie."""
    case.assertTrue((directory / 'descendant.pid').is_file())
    deadline = time.monotonic() + 2
    with (directory / 'descendant.lock').open('rb') as held:
        while True:
            try:
                fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    case.fail('verifier descendant survived cleanup after its parent exited')
                time.sleep(0.01)


def cleanup_descendant(directory):
    path = directory / 'descendant.pid'
    if path.is_file():
        try:
            os.kill(int(path.read_text()), signal.SIGKILL)
        except ProcessLookupError:
            pass


class CanonicalTests(unittest.TestCase):
    def test_exact_encoding(self):
        self.assertEqual(canonical({'z': 'é', 'a': [True, None, 2]}),
                         b'{"a":[true,null,2],"z":"\\u00e9"}')
        self.assertEqual(decode(b'{"z":"\\u00e9"}', require_canonical=True), {'z': 'é'})

    def test_duplicate_trailing_unicode_and_numbers(self):
        rows = [(b'{"a":1,"a":2}', 'duplicate-key'), (b'{}{}', 'invalid-json'),
                (b'\xff', 'invalid-json'), (b'1.0', 'noninteger-number'),
                (b'1e0', 'noninteger-number'), (b'NaN', 'noninteger-number'),
                (b'Infinity', 'noninteger-number'), (b'"\\ud800"', 'invalid-unicode'),
                (b'9223372036854775808', 'integer-limit')]
        for raw, code in rows:
            with self.subTest(code=code), self.assertRaises(Refusal) as result:
                decode(raw)
            self.assertEqual(result.exception.code, code)

    def test_canonical_and_depth_byte_boundaries(self):
        self.assertEqual(decode(b'['*31+b'0'+b']'*31), self.nested(31))
        self.assertEqual(decode(b'['*32+b'0'+b']'*32), self.nested(32))
        for raw in (b'['*33+b'0'+b']'*33, b' '*65537):
            with self.assertRaises(Refusal): decode(raw)
        with self.assertRaisesRegex(Refusal, 'noncanonical-json'):
            decode(b'{ "a":1}', require_canonical=True)
        self.assertEqual(len(canonical('x'*65534)), 65536)
        with self.assertRaisesRegex(Refusal, 'byte-limit'): canonical('x'*65535)
        self.assertEqual(decode(str(2**63-1).encode()), 2**63-1)
        with self.assertRaises(Refusal): canonical(2**63)
        cycle=[];cycle.append(cycle)
        with self.assertRaisesRegex(Refusal, 'cyclic-json'): canonical(cycle)

    @staticmethod
    def nested(depth):
        result=0
        for _ in range(depth): result=[result]
        return result


class SchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import jsonschema
        except ModuleNotFoundError as error:
            # A closed fixed-tree run hides the user site, so name the lock
            # rather than leave a bare import error (#1927).
            raise AssertionError('mandatory schema tool absent: ' + str(error.name)
                                 + '; install plugins/hexaemeron/tests/requirements.lock into '
                                 + sys.executable) from None
        cls.jsonschema = jsonschema
        cls.validators = {kind: jsonschema.Draft202012Validator(schema.document(kind)) for kind in schema.SCHEMAS}

    def test_mandatory_schema_tool_versions(self):
        profile=json.loads((FIXTURES.parent/'tool-profile.json').read_bytes())
        for name, version in profile['schema_tools'].items():
            self.assertEqual(importlib.metadata.version(name), version)

    def test_every_schema_is_closed_and_matches_its_published_bytes(self):
        self.assertEqual(set(schema.SCHEMAS), set(schema.RECORD_TYPES))
        for kind, shape in schema.SCHEMAS.items():
            with self.subTest(kind=kind):
                self.jsonschema.Draft202012Validator.check_schema(schema.document(kind))
                self.assertEqual(decode((FIXTURES.parent/'schemas'/(kind+'.schema.json')).read_bytes()), schema.document(kind))
                value=specimen(kind)
                self.validators[kind].validate(value)
                self.assertEqual(records.parse_record(canonical(value)), value)

    def test_every_required_field_missing_unknown_and_wrong_type(self):
        count=0
        def objects(value, shape, path=()):
            if 'oneOf' in shape:
                branches=[branch for branch in shape['oneOf'] if self.jsonschema.Draft202012Validator(branch).is_valid(value)]
                if len(branches)==1:yield from objects(value,branches[0],path)
            elif 'anyOf' in shape:
                for branch in shape['anyOf']:
                    if self.jsonschema.Draft202012Validator(branch).is_valid(value):yield from objects(value,branch,path)
            elif shape.get('type')=='object':
                yield path,value,shape
                for key,child in value.items():yield from objects(child,shape['properties'][key],path+(key,))
            elif shape.get('type')=='array':
                for index,child in enumerate(value):yield from objects(child,shape['items'],path+(index,))
        for kind,shape in schema.SCHEMAS.items():
            original=specimen(kind)
            for path,obj_value,obj_shape in objects(original,shape):
                for field in (*obj_value,'__unknown__'):
                    value=copy.deepcopy(original);target=value
                    for segment in path:target=target[segment]
                    if field=='__unknown__':target[field]=1
                    else:del target[field]
                    with self.subTest(kind=kind,path=path,field=field):
                        self.assertFalse(self.validators[kind].is_valid(value))
                        with self.assertRaises(Refusal):records.parse_record(canonical(value))
                    count+=1
                    if field != '__unknown__':
                        value=copy.deepcopy(original);target=value
                        for segment in path:target=target[segment]
                        field_validator=self.jsonschema.Draft202012Validator(obj_shape['properties'][field])
                        target[field]=next(candidate for candidate in (None,True,[],{},0,'') if not field_validator.is_valid(candidate))
                        with self.subTest(kind=kind,path=path,wrong_type=field):
                            self.assertFalse(self.validators[kind].is_valid(value))
                            with self.assertRaises(Refusal):records.parse_record(canonical(value))
                        count+=1
        self.assertGreater(count, 500)

    def test_scalar_and_boundary_types_agree(self):
        for definition in (schema.POSITIVE,schema.UINT,schema.HASH,schema.COMMIT,schema.TIME,schema.ID,schema.KEY,schema.BOOL):
            validator=self.jsonschema.Draft202012Validator(definition)
            for value in (True,False,None,[],{},0,1,-1,'x','x\n','a'*40+'\n','x'*129,2**63):
                try:schema.validate(value,definition);accepted=True
                except Refusal:accepted=False
                self.assertEqual(accepted,validator.is_valid(value),(definition,value))
        for value in (True,0,2**63,-1):
            record=specimen('acceptance');record['actor_id']=value
            with self.assertRaises(Refusal):records.parse_record(canonical(record))
        for value in ('x'*128, 'A-1._'):
            schema.validate(value,schema.ID)
        for value in ('x'*129,'../x','x\n','é'):
            with self.assertRaises(Refusal):schema.validate(value,schema.ID)
        refs=[{'type':'acceptance','sha256':hashlib.sha256(str(i).encode()).hexdigest()} for i in range(64)]
        schema.validate(refs,schema.array(schema.ref('acceptance')))
        with self.assertRaises(Refusal):schema.validate(refs+[{'type':'acceptance','sha256':'f'*64}],schema.array(schema.ref('acceptance')))

    def test_all_tagged_variants(self):
        for format in ('root','ssh-ed25519','ssh-p256','openpgp-v4'):
            key=decode((FIXTURES/(format+'-public.json')).read_bytes())
            schema.validate(key,schema.KEY)
            self.jsonschema.Draft202012Validator(schema.KEY).validate(key)
            signatures.public_key(key)
            self.assert_closed_variant(key,schema.KEY)
        for kind,field,value in (('snapshot','snapshot_id','a'*64),('representation','outer_sha256','b'*64),('run','run_id','run-1'),('key','enrollment',{'type':'key-enrollment','sha256':'c'*64})):
            target={'kind':kind,field:value};schema.validate(target,schema.TARGET)
            self.jsonschema.Draft202012Validator(schema.TARGET).validate(target)
            self.assert_closed_variant(target,schema.TARGET)
        for transition in ({'kind':'registered-root','registration':{'type':'run-registration','sha256':'a'*64}}, {'kind':'continuation','parent':{'type':'parent-link','sha256':'b'*64},'producer_prefix_sha256':'c'*64,'initial_base':'d'*40}):
            schema.validate(transition,schema.TRANSITION)
            self.jsonschema.Draft202012Validator(schema.TRANSITION).validate(transition)
            self.assert_closed_variant(transition,schema.TRANSITION)

    def assert_closed_variant(self,value,definition):
        validator=self.jsonschema.Draft202012Validator(definition)
        for field in (*value,'__unknown__'):
            changed=copy.deepcopy(value)
            if field=='__unknown__':changed[field]=None
            else:del changed[field]
            with self.subTest(variant=value.get('format',value.get('kind')),field=field):
                self.assertFalse(validator.is_valid(changed))
                with self.assertRaises(Refusal):schema.validate(changed,definition)


class BindingTests(unittest.TestCase):
    def mutate(self, kind, path, value, code):
        record=specimen(kind);target=record
        for segment in path[:-1]:target=target[segment]
        target[path[-1]]=value
        with self.assertRaises(Refusal) as result:records.parse_record(canonical(record))
        self.assertEqual(result.exception.code,code)

    def test_protocol_type_scope_and_real_calendar(self):
        self.mutate('acceptance',('protocol',),'checkpoint-authority/v2','unsupported-protocol')
        self.mutate('acceptance',('issued_at',),'2026-02-30T00:00:00Z','invalid-time')
        for value in ([],{},None,'unknown'):
            self.mutate('acceptance',('type',),value,'unsupported-record-type')
        with self.assertRaisesRegex(Refusal,'foreign-scope'):
            records.parse_record(canonical(specimen('acceptance')),scope=('production','test-service',{'repository_id':23,'run_id':'run-1'}))

    def test_digest_roles_copy_evidence_and_native_order(self):
        self.mutate('acceptance',('accepted_representation','sha256'),'f'*64,'representation-binding')
        self.mutate('acceptance',('copies',0,'object_key'),'sha256/'+'f'*64,'object-key')
        self.mutate('storage-copy',('get_length',),124,'copy-readback')
        self.mutate('validation',('input_sha256',),'f'*64,'input-binding')
        self.mutate('validation',('native_results',0,'stage'),'restore','native-stage-order')
        self.mutate('validation',('coverage','verified'),[],'coverage-shape')
        self.mutate('authority-head',('policy_history','count'),1,'head-shape')
        self.mutate('authority-policy',('locations',1,'account_id'),'primary-account','storage-independence')
        self.mutate('enrollment-challenge',('expires_at',),'2026-09-16T00:05:01Z','expiry-interval')
        self.mutate('stream-permit',('expires_at',),'2026-09-16T00:01:01Z','expiry-interval')

    def test_reference_self_cycle_missing_and_wrong_type(self):
        data=canonical(specimen('authority-policy'));identity='a'*64
        self.assertEqual(records.check_reference_order([(identity,data)])['count'],1)
        record=specimen('authority-policy');record.update(sequence=2,previous={'type':'authority-policy','sha256':identity})
        for row in ([(identity,canonical(record))], [('b'*64,canonical(record))]):
            with self.assertRaises(Refusal):records.check_reference_order(row)
        with self.assertRaisesRegex(Refusal,'missing-or-forward-reference'):
            records.check_reference_order([('b'*64,canonical(record))],external=((identity,'acceptance'),))
        # A cycle necessarily carries an unresolved forward edge in ordered admission.
        second=copy.deepcopy(record);second['previous']['sha256']='b'*64
        with self.assertRaises(Refusal):records.check_reference_order([(identity,canonical(second)),('b'*64,canonical(record))])
        with self.assertRaisesRegex(Refusal,'duplicate-record'):
            records.check_reference_order([(identity,data),(identity,data)])

    def test_aggregate_budgets_have_named_refusals(self):
        data=canonical(specimen('authority-policy'))
        with self.assertRaisesRegex(Refusal,'aggregate-limit'):
            records.check_reference_order([('f'*64,data)],external=
                ((format(i,'064x'),'authority-policy') for i in range(encoding.MAX_ENTRIES)))
        with self.assertRaisesRegex(Refusal,'count-limit'):
            records.check_reference_order([],external=
                ((format(i,'064x'),'authority-policy') for i in range(encoding.MAX_ENTRIES+1)))
        with mock.patch.object(records,'MAX_ENTRIES',2):
            with self.assertRaisesRegex(Refusal,'aggregate-limit'):
                records.check_reference_order([(str(i)*64,data) for i in range(3)])
        with mock.patch.object(records,'MAX_TOTAL_BYTES',len(data)-1):
            with self.assertRaisesRegex(Refusal,'aggregate-limit'):records.check_reference_order([('a'*64,data)])
        self.assertEqual((encoding.MAX_ENTRIES,encoding.MAX_TOTAL_BYTES),(65536,268435456))

    def test_acceptance_domain_is_external_and_not_an_envelope_digest(self):
        record=canonical(specimen('acceptance'));identity=records.acceptance_id(record)
        self.assertNotEqual(identity,digest(record))
        self.assertNotIn(identity,record.decode())
        first=(FIXTURES/'valid-envelope.json').read_bytes();second=(FIXTURES/'alternate-envelope.json').read_bytes()
        self.assertNotEqual(digest(first),digest(second))
        self.assertEqual(decode(first)['payload'],decode(second)['payload'])
        self.assertNotIn(identity,list(specimen('acceptance')['identities'].values()))
        with self.assertRaises(Refusal):records.acceptance_id(canonical(specimen('denial')))


class SignatureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tools=tools();cls.key=decode((FIXTURES/'root-public.json').read_bytes())
        cls.valid=(FIXTURES/'valid-envelope.json').read_bytes()

    def verify(self, data=None,key=None):
        return signatures.verify_envelope(data or self.valid,key or self.key,self.tools)

    def test_real_p256_exact_payload_and_randomized_equivalence(self):
        result=self.verify()
        self.assertEqual(result.payload,signatures.b64decode(decode(self.valid)['payload']))
        self.assertEqual(result.envelope_sha256,digest(self.valid))
        snapshot=result.record_bytes
        copy_value=result.record;copy_value['actor_id']=99
        self.assertEqual(result.record_bytes,snapshot)
        alternate=self.verify((FIXTURES/'alternate-envelope.json').read_bytes())
        self.assertEqual(result.record_bytes,alternate.record_bytes)
        self.assertNotEqual(result.envelope_sha256,alternate.envelope_sha256)
        with self.assertRaises(AttributeError):result.payload=b'changed'

    def test_pae_literal_vector(self):
        self.assertEqual(signatures.pae(b'hello','example'),b'DSSEv1 7 example 5 hello')
        self.assertEqual(signatures.pae('é'.encode(),'text'),b'DSSEv1 4 text 2 \xc3\xa9')

    def test_hostile_signature_byte_changes(self):
        outer=decode(self.valid)
        changes=[('payloadType','application/wrong'),('payload',signatures.b64(b'{}'))]
        for field,value in changes:
            bad=copy.deepcopy(outer);bad[field]=value
            with self.assertRaises(Refusal):self.verify(canonical(bad,limit=128*1024))
        for name in ('double-hashed-envelope',):
            with self.assertRaisesRegex(Refusal,'signature-invalid'):self.verify((FIXTURES/(name+'.json')).read_bytes())
        with self.assertRaisesRegex(Refusal,'signature-invalid'):self.verify(key=decode((FIXTURES/'wrong-public.json').read_bytes()))
        with self.assertRaisesRegex(Refusal,'wrong-key-curve'):self.verify(key=decode((FIXTURES/'wrongcurve-public.json').read_bytes()))

    def test_der_scalar_minimality_bounds_and_trailing_bytes(self):
        valid=signatures.b64decode(decode(self.valid)['signatures'][0]['sig'])
        signatures.check_der(valid)
        for data in (b'',valid+b'\x00',b'\x30\x06\x02\x01\x00\x02\x01\x01',b'\x30\x07\x02\x02\x00\x01\x02\x01\x01',b'\x30\x06\x02\x01\x80\x02\x01\x01'):
            with self.assertRaisesRegex(Refusal,'invalid-der'):signatures.check_der(data)

    def test_base64_alphabets_padding_and_pad_bits(self):
        for value in ('+/8=','+/8','-_8=','-_8'):
            self.assertEqual(signatures.b64decode(value),b'\xfb\xff')
        for value in ('+_8=','-_8==','A','YQ=','YQ===','YR==','YQ==\n',' YQ==','é',True,[],{}):
            with self.subTest(value=value),self.assertRaises(Refusal):signatures.b64decode(value)
        outer=decode(self.valid)
        for name in ('payload',):outer[name]=outer[name].rstrip('=').replace('+','-').replace('/','_')
        outer['signatures'][0]['sig']=outer['signatures'][0]['sig'].rstrip('=').replace('+','-').replace('/','_')
        self.verify(canonical(outer,limit=128*1024))

    def test_envelope_field_signature_count_and_hint_closure(self):
        outer=decode(self.valid)
        for extra in ({'extra':True},{'signatures':[]},{'signatures':outer['signatures']*2},{'signatures':[{'keyid':'carried-key','sig':outer['signatures'][0]['sig']}]}):
            with self.assertRaises(Refusal):self.verify(canonical(outer|extra,limit=128*1024))
        bad=copy.deepcopy(self.key);bad['fingerprint']='f'*64
        with self.assertRaisesRegex(Refusal,'key-fingerprint'):self.verify(key=bad)

    def test_tool_missing_changed_and_symlink_are_refused(self):
        with self.assertRaisesRegex(Refusal,'tool-required'):signatures.verify_envelope(self.valid,self.key,{})
        pin=self.tools['openssl']
        with self.assertRaisesRegex(Refusal,'tool-pin'):
            signatures.ToolPin(pin.name,pin.path,'0'*64).check()
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'openssl';path.symlink_to(pin.path)
            with self.assertRaises(Refusal):signatures.ToolPin(pin.name,str(path),pin.sha256).check()

    def test_native_proof_and_upload_formats(self):
        for format in ('ssh-ed25519','ssh-p256','openpgp-v4'):
            with self.subTest(format=format):
                prefix=trust.verify_trust_prefix(chain(format+'-trust-prefix'),bootstrap(),self.tools)
                envelope=(FIXTURES/(format+'-endorsement.json')).read_bytes()
                result=prefix.authenticate(envelope)
                self.assertEqual(result.record['type'],'upload-endorsement')
                self.assertEqual(result.payload,signatures.b64decode(decode(envelope)['payload']))
                bad=decode(envelope);bad['payload']=signatures.b64(b'{}')
                with self.assertRaises(Refusal):prefix.authenticate(canonical(bad))
        # Public verification must not require an agent socket in a short home.
        with tempfile.TemporaryDirectory(prefix='checkpoint-gpg-'+('x'*90)) as parent:
            with mock.patch.object(tempfile,'tempdir',parent):
                prefix=trust.verify_trust_prefix(chain('openpgp-v4-trust-prefix'),bootstrap(),self.tools)
                envelope=(FIXTURES/'openpgp-v4-endorsement.json').read_bytes()
                self.assertEqual(prefix.authenticate(envelope).record['type'],'upload-endorsement')
                bad=decode(envelope);bad['payload']=signatures.b64(b'{}')
                with self.assertRaises(Refusal):prefix.authenticate(canonical(bad))

    def test_real_cosign_pinned_interoperability(self):
        import platform
        profile=json.loads((FIXTURES.parent/'tool-profile.json').read_bytes())
        architecture={'aarch64':'arm64','arm64':'arm64','x86_64':'amd64'}[platform.machine()]
        expected=profile['cosign']['assets'][platform.system().lower()+'-'+architecture]
        pin=tool('cosign')
        self.assertEqual(pin.sha256,expected['sha256'],pin.path+' is not the pinned cosign '+profile['cosign']['version']+' asset; set CHECKPOINT_COSIGN to it')
        pin.check()
        self.assertEqual(Path(pin.path).stat().st_size,expected['bytes'])
        envelope=decode((FIXTURES/'cosign-envelope.json').read_bytes())
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary)
            (directory/'blob').write_bytes((FIXTURES/'semantic-specimen').read_bytes())
            (directory/'trusted.pem').write_bytes((FIXTURES/'root-public.pem').read_bytes())
            (directory/'wrong.pem').write_bytes((FIXTURES/'wrong-public.pem').read_bytes())
            cases=[('valid',envelope,'trusted.pem',0)]
            bad=copy.deepcopy(envelope);bad['payload']=signatures.b64(signatures.b64decode(bad['payload']).replace(b'test-service',b'evil-service'))
            cases.append(('payload',bad,'trusted.pem',1))
            cases.append(('wrong-key',envelope,'wrong.pem',1))
            bad=copy.deepcopy(envelope);bad['payloadType']='application/wrong';cases.append(('type',bad,'trusted.pem',1))
            # Identical payload and subject isolate the second digest as the cause.
            double=decode((FIXTURES/'cosign-double-hashed-envelope.json').read_bytes())
            self.assertEqual(double['payload'],envelope['payload'])
            cases.append(('double-hash',double,'trusted.pem',1))
            for name,value,key,expected_exit in cases:
                bundle={'mediaType':'application/vnd.dev.sigstore.bundle.v0.3+json','verificationMaterial':{'publicKey':{'hint':''}},'dsseEnvelope':value}
                (directory/'bundle.json').write_bytes(canonical(bundle,limit=128*1024))
                result=signatures._run(pin,['verify-blob-attestation','--offline','--insecure-ignore-tlog','--key',key,'--bundle','bundle.json','--type',schema.PREDICATE,'blob'],directory,timeout=30)
                self.assertEqual(result[0],expected_exit,(name,result[2][:150]))


class TrustTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.tools=tools()

    def test_every_trust_transition_and_original_keys_are_retained(self):
        prefix=trust.verify_trust_prefix(chain(),bootstrap(),self.tools)
        self.assertEqual(prefix.count,10)
        self.assertEqual(len(prefix.enrollments),2)
        self.assertEqual(len(prefix.revoked),2)
        self.assertEqual(len(prefix.consumed_challenges),2)
        self.assertEqual(prefix.policy.record['sequence'],10)
        for identity in prefix.consumed_challenges:
            self.assertEqual(prefix.records[identity].record,{'type':'enrollment-challenge'})
        self.assertTrue(all(not hasattr(value,'payload') for value in prefix.records.values()))

    def test_no_carried_key_bootstrap_or_test_root_in_production(self):
        with self.assertRaisesRegex(Refusal,'test-production-separation'):
            trust.verify_trust_prefix(chain(),trust.Bootstrap('production','test-service',23,'run-1',bootstrap().roots),self.tools)
        wrong=canonical({'environment':'test','key':decode((FIXTURES/'wrong-public.json').read_bytes())})
        with self.assertRaisesRegex(Refusal,'bootstrap-required'):
            trust.verify_trust_prefix(chain(),trust.Bootstrap('test','test-service',23,'run-1',(wrong,)),self.tools)
        with self.assertRaisesRegex(Refusal,'bootstrap-required'):
            trust.verify_trust_prefix(chain()[1:],bootstrap(),self.tools)

    def test_omission_order_duplicates_and_foreign_scope(self):
        original=chain()
        for modified in (original[:1]+original[2:],original[:1]+original[2:3]+original[1:2],original[:2]+original[1:2]):
            with self.assertRaises(Refusal):trust.verify_trust_prefix(modified,bootstrap(),self.tools)
        with self.assertRaisesRegex(Refusal,'foreign-scope'):
            trust.verify_trust_prefix(original,trust.Bootstrap('test','other-service',23,'run-1',bootstrap().roots),self.tools)

    def test_refusal_does_not_advance_prefix(self):
        prefix=trust.verify_trust_prefix(chain()[:2],bootstrap(),self.tools)
        before=(prefix.count,prefix.tail,prefix.total_bytes,len(prefix.records))
        with self.assertRaises(Refusal):prefix.append(chain()[3])
        self.assertEqual((prefix.count,prefix.tail,prefix.total_bytes,len(prefix.records)),before)


class AuthenticatedHostileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tools=tools();cls.temporary=tempfile.TemporaryDirectory(prefix='ca-test-')
        cls.directory=Path(cls.temporary.name);cls.keys={}
        for name in ('root','contributor'):
            path=cls.directory/(name+'.pem')
            subprocess.run([cls.tools['openssl'].path,*P256_KEYGEN,'-out',str(path)],check=True,capture_output=True,timeout=10)
            data=subprocess.check_output([cls.tools['openssl'].path,'pkey','-in',str(path),'-pubout','-outform','DER'],timeout=10)
            cls.keys[name]={'format':'spki-p256','algorithm':'ecdsa-p256-sha256','public':signatures.b64(data),'fingerprint':digest(data)}
        cls.bootstrap=trust.Bootstrap('test','test-service',23,'run-1',(canonical({'environment':'test','key':cls.keys['root']}),))

    @classmethod
    def tearDownClass(cls):cls.temporary.cleanup()

    def sign(self, message, name='root'):
        return subprocess.run([self.tools['openssl'].path,'dgst','-sha256','-sign',str(self.directory/(name+'.pem'))],input=message,capture_output=True,check=True,timeout=10).stdout

    def envelope(self, record, name='root'):
        payload=signatures.statement_bytes(canonical(record))
        return signatures.envelope_bytes(payload,self.sign(signatures.pae(payload),name))

    def base(self, *, policy_roles=None):
        prefix=trust.TrustPrefix(self.bootstrap,self.tools)
        record=specimen('authority-policy');record['issuer']=self.keys['root']['fingerprint'];record['authorities'][0]['key']=self.keys['root']
        if policy_roles is not None:record['authorities'][0]['roles']=policy_roles
        prefix.append(self.envelope(record));return prefix

    def next_record(self, prefix, kind):
        record=specimen(kind);record['issuer']=self.keys['root']['fingerprint']
        record['sequence']=prefix.count+1;record['previous']={'type':prefix.records[prefix.tail].record['type'],'sha256':prefix.tail}
        if kind!='authority-policy':record['policy']={'type':'authority-policy','sha256':prefix.policy.envelope_sha256}
        return record

    def challenge(self,prefix):
        record=self.next_record(prefix,'enrollment-challenge');record['key']=self.keys['contributor']
        return prefix.append(self.envelope(record))

    def enrollment(self,prefix,challenge):
        record=self.next_record(prefix,'key-enrollment');record['key']=self.keys['contributor']
        record['proof']={'challenge':{'type':'enrollment-challenge','sha256':challenge.envelope_sha256},'signature':signatures.b64(self.sign(trust.proof_message(challenge.record),'contributor'))}
        return record

    def test_enrollment_requires_exact_challenge_actor_key_proof_and_expiry(self):
        for mutation,code in (('actor','challenge-scope'),('key','challenge-scope'),('proof','signature-invalid'),('expired','challenge-expired')):
            prefix=self.base();challenge=self.challenge(prefix);record=self.enrollment(prefix,challenge)
            if mutation=='actor':record['actor_id']=2
            elif mutation=='key':record['key']=self.keys['root']
            elif mutation=='proof':record['proof']['signature']=signatures.b64(self.sign(b'other message','contributor'))
            else:record['issued_at']='2026-09-16T00:01:00Z'
            with self.subTest(mutation=mutation),self.assertRaisesRegex(Refusal,code):prefix.append(self.envelope(record))
            self.assertEqual(prefix.count,2)

    def test_challenge_is_one_use_and_requires_operator_role(self):
        prefix=self.base();challenge=self.challenge(prefix)
        prefix.append(self.envelope(self.enrollment(prefix,challenge)))
        with self.assertRaisesRegex(Refusal,'challenge-used'):prefix.append(self.envelope(self.enrollment(prefix,challenge)))
        prefix=self.base(policy_roles=['policy'])
        with self.assertRaisesRegex(Refusal,'issuer-untrusted'):self.challenge(prefix)

    def test_all_predecessors_are_checked_after_authentication(self):
        prefix=self.base();record=self.next_record(prefix,'enrollment-challenge');record['key']=self.keys['contributor']
        for mutate,code in ((lambda r:r.update(policy={'type':'authority-policy','sha256':'f'*64}),'policy-predecessor'),(lambda r:r.update(previous={'type':'authority-policy','sha256':'f'*64}),'trust-predecessor'),(lambda r:r.update(sequence=3),'trust-predecessor')):
            altered=copy.deepcopy(record);mutate(altered)
            with self.assertRaisesRegex(Refusal,code):prefix.append(self.envelope(altered))
        self.assertEqual(prefix.count,1)

    def test_revocation_grant_scope_and_validity_block_endorsements(self):
        for mutation,code in (('grant','grant-scope'),('expired','grant-expired'),('revoked','enrollment-inactive')):
            prefix=self.base();challenge=self.challenge(prefix)
            enrollment=prefix.append(self.envelope(self.enrollment(prefix,challenge)))
            reference={'type':'key-enrollment','sha256':enrollment.envelope_sha256}
            grant=self.next_record(prefix,'run-grant');grant['enrollment']=reference;grant['permissions']=['download'] if mutation=='grant' else ['upload']
            if mutation=='expired':grant['not_after']='2026-09-16T00:00:30Z'
            granted=prefix.append(self.envelope(grant))
            if mutation=='revoked':
                revoked=self.next_record(prefix,'key-revocation');revoked['enrollment']=reference
                prefix.append(self.envelope(revoked))
            endorsement=self.next_record(prefix,'upload-endorsement');endorsement.update(enrollment=reference,grant={'type':'run-grant','sha256':granted.envelope_sha256},issuer=self.keys['contributor']['fingerprint'])
            if mutation=='expired':endorsement.update(issued_at='2026-09-16T00:00:30Z',expires_at='2026-09-16T00:01:30Z')
            with self.subTest(mutation=mutation),self.assertRaisesRegex(Refusal,code):prefix.authenticate(self.envelope(endorsement,'contributor'))

    def test_signed_noncanonical_unknown_statement_and_subject_swap_refuse(self):
        record=specimen('acceptance');record['issuer']=self.keys['root']['fingerprint']
        statement=decode(signatures.statement_bytes(canonical(record)))
        for mutation,code in (('whitespace','noncanonical-json'),('subject','subject-roles'),('statement','statement-fields'),('predicate','schema-fields')):
            value=copy.deepcopy(statement)
            if mutation=='subject':value['subject'][0]['name']='outer_sha256'
            elif mutation=='statement':value['extra']='field'
            elif mutation=='predicate':value['predicate']['self_hash']='f'*64
            payload=json.dumps(value,indent=2).encode() if mutation=='whitespace' else canonical(value)
            envelope=signatures.envelope_bytes(payload,self.sign(signatures.pae(payload)))
            with self.subTest(mutation=mutation),self.assertRaisesRegex(Refusal,code):signatures.verify_envelope(envelope,self.keys['root'],self.tools)


class BoundaryTests(unittest.TestCase):
    def test_timeout_reaps_descendants_after_verifier_parent_exits(self):
        executable = str(Path(sys.executable).resolve())
        pin = signatures.ToolPin('openssl', executable, digest(Path(executable).read_bytes()))
        for exited in (True, False):
            with self.subTest(exited=exited), tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary)
                program = DESCENDANT_PROBE if exited else DESCENDANT_PROBE.replace('os._exit(0)', 'time.sleep(60)')
                try:
                    if exited:
                        result = signatures._run(pin, ['-c', program], directory, timeout=2)
                        self.assertEqual(result, (0, b'{}\n', b''))
                    else:
                        with self.assertRaisesRegex(Refusal, 'tool-timeout'):
                            signatures._run(pin, ['-c', program], directory, timeout=2)
                    assert_descendant_stopped(self, directory)
                finally:
                    cleanup_descendant(directory)

    def test_published_hostile_vectors(self):
        corpus=json.loads((FIXTURES/'hostile-records.json').read_bytes())
        self.assertEqual(corpus['schema'],'checkpoint-authority-hostile-records/v1')
        for row in corpus['cases']:
            with self.subTest(case=row['id']),self.assertRaises(Refusal) as error:
                records.parse_record(bytes.fromhex(row['hex']))
            self.assertEqual(error.exception.code,row['code'])

    def test_reference_pair_types_and_external_inventory(self):
        data=canonical(specimen('authority-policy'))
        for items in ([([],data)], [({},data)], [('a'*64,None)], [None], [('a'*64,data,1)]):
            with self.subTest(items=repr(items)[:40]),self.assertRaises(Refusal):
                records.check_reference_order(items)
        for external in ([([], 'authority-policy')], [('a'*64,[])], [('a'*64,'unknown')], [('a'*64,'authority-policy')]*2):
            with self.assertRaises(Refusal):records.check_reference_order([],external=external)
        with mock.patch.object(records,'MAX_ENTRIES',1):
            with self.assertRaisesRegex(Refusal,'aggregate-limit'):
                records.check_reference_order([('b'*64,data)],external=[('a'*64,'authority-policy')])

    def test_group_permission_after_exit_is_retried_without_ignoring_denial(self):
        executable = str(Path(sys.executable).resolve())
        pin = signatures.ToolPin('openssl', executable, digest(Path(executable).read_bytes()))
        popen = subprocess.Popen
        for second_error, expected in (
            (ProcessLookupError(3, 'group gone'), 'tool-output-limit'),
            (PermissionError(1, 'signal denied'), 'tool-unavailable'),
        ):
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as temporary:
                with contextlib.ExitStack() as children:
                    def start(*args, **kwargs):
                        return children.enter_context(popen(*args, **kwargs))
                    with mock.patch.object(signatures.subprocess, 'Popen', side_effect=start), \
                            mock.patch.object(signatures.os, 'killpg', side_effect=[
                                PermissionError(1, 'unreaped leader'), second_error,
                            ]) as signalling:
                        with self.assertRaisesRegex(Refusal, expected):
                            signatures._run(pin, ['-c', 'import os; os.write(1, b"x" * 70000)'],
                                            Path(temporary), timeout=10)
                        if expected == 'tool-output-limit':
                            self.assertEqual(signalling.call_count, 2)

    def test_public_verification_subprocess_output_and_time_caps(self):
        key=specimen('root-public')
        for message,signature in ((None,b'x'),(b'x',None),(b'x'*131073,b'x'),
                                  (b'x',b'x'*16385),(b'x',b'')):
            with self.subTest(message_type=type(message).__name__,signature_type=type(signature).__name__):
                with mock.patch.object(signatures.tempfile,'TemporaryDirectory',side_effect=AssertionError('scratch reached')):
                    with self.assertRaisesRegex(Refusal,'signature-input-limit'):
                        signatures.verify_signature(message,signature,key,{})
        pin=signatures.ToolPin('openssl',str(Path(sys.executable).resolve()),digest(Path(sys.executable).read_bytes()))
        with tempfile.TemporaryDirectory() as temporary:
            for args,code,deadline in ((['-c','import os; os.write(1, b"x" * 70000)'],'tool-output-limit',10),
                                       (['-c','import time; time.sleep(2)'],'tool-timeout',0.2)):
                with self.assertRaisesRegex(Refusal,code):
                    signatures._run(pin,args,Path(temporary),timeout=deadline)

    def test_noncanonical_native_public_keys_and_wrong_fingerprints(self):
        for name in ('ssh-ed25519','ssh-p256','openpgp-v4'):
            key=specimen(name+'-public')
            envelope=(FIXTURES/(name+'-endorsement.json')).read_bytes()
            bad=copy.deepcopy(key);bad['public']+='\n'
            with self.assertRaises(Refusal):signatures.verify_envelope(envelope,bad,tools())
            bad=copy.deepcopy(key)
            bad['fingerprint']='0'*40 if name=='openpgp-v4' else 'SHA256:'+'A'*43
            with self.assertRaisesRegex(Refusal,'key-fingerprint'):
                signatures.verify_envelope(envelope,bad,tools())


if __name__ == '__main__':
    unittest.main()
