"""The isolated checkpoint predicate binds evidence and leaves authority external."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

PLUGIN = Path(__file__).resolve().parents[1]
ROOT = PLUGIN.parents[1]
sys.path.insert(0, str(PLUGIN / "scripts"))
from ariadne_lib import envelope, registry, verify
from ariadne_lib.predicates import checkpoint_authority as predicate

FIXTURE = PLUGIN / "tests/fixtures/checkpoint-authority-acceptance.json"


def statement(value=None):
    if value is None:
        value = json.loads(FIXTURE.read_bytes())
    return {"_type":"https://in-toto.io/Statement/v1", "predicateType":predicate.TYPE,
        "subject":[{"name":key,"digest":{"sha256":value["identities"][key]}}
            for key in ("snapshot_id","controller_manifest_sha256","outer_sha256")], "predicate":value}


def report(value):
    return verify.report(envelope.read(json.dumps(value).encode()))


class CheckpointPredicateTests(unittest.TestCase):
    def test_registered_complete_results_and_explicit_authority_unknowns(self):
        self.assertIs(registry.DEFAULT.get(predicate.TYPE),predicate)
        result=report(statement())
        self.assertTrue(result.ok,result.to_dict())
        self.assertTrue(result.predicate_gates_checked)
        self.assertEqual(tuple((x.number,x.name) for x in result.gates if (x.number,x.name) in predicate.EXPECTED_RESULTS),predicate.EXPECTED_RESULTS)
        self.assertEqual(result.unchecked,list(predicate.UNCHECKED))
        self.assertNotIn("verified",result.document.signature_state)

    def test_missing_fields_unknown_fields_and_wrong_subject_roles_refuse(self):
        original=statement()
        for key in original["predicate"]:
            value=copy.deepcopy(original);del value["predicate"][key]
            with self.subTest(key=key):self.assertFalse(report(value).ok)
        value=copy.deepcopy(original);value["predicate"]["claims"]=[]
        self.assertFalse(report(value).ok)
        for index in range(3):
            value=copy.deepcopy(original);value["subject"][index]["name"]="other-role"
            self.assertFalse(report(value).ok)
            value=copy.deepcopy(original);value["subject"][index]["digest"]["sha256"]="f"*64
            self.assertFalse(report(value).ok)

    def test_evidence_reference_role_digest_and_copy_substitutions_refuse(self):
        for mutate in (
            lambda x:x["validation"].update(type="acceptance"),
            lambda x:x["grant"].update(sha256="not-a-digest"),
            lambda x:x.update(signing_history=[]),
            lambda x:x["copies"][0]["object"].update(sha256="f"*64),
            lambda x:x["copies"][1].update(role="primary"),
            lambda x:x.update(carrier_length=True)):
            value=statement();mutate(value["predicate"])
            self.assertFalse(report(value).ok)

    def test_unknown_predicate_and_fake_block_declaration_cannot_disable_core(self):
        value=statement();value["predicateType"]="https://example.test/unknown/v1"
        result=report(value)
        self.assertFalse(result.ok)
        self.assertFalse(result.predicate_gates_checked)
        class Fake:
            TYPE=value["predicateType"]
            SUMMARY="test declaration"
            CORE_BLOCKS=predicate.CORE_BLOCKS
        own=registry.Registry();own.register(Fake)
        result=verify.report(envelope.read(json.dumps(value).encode()),registry=own)
        self.assertFalse(result.ok)
        self.assertFalse(result.predicate_gates_checked)

    def test_schema_evidence_names_do_not_allow_self_attested_authority(self):
        value=statement()
        self.assertTrue(report(value).ok)
        for path,key in (((),"verified"), (("native",),"verified"),
                         (("release",),"verifier_sha256_extra")):
            changed=copy.deepcopy(value)
            node=changed["predicate"]
            for part in path:node=node[part]
            node[key]=True
            self.assertFalse(report(changed).ok)
        changed=copy.deepcopy(value)
        changed["predicate"]["release"]["verifier_sha256"]=True
        self.assertFalse(report(changed).ok)
        for kind,shape in predicate.RECORDS.items():
            owner=ROOT/"plugins/hexaemeron/skills/fiat/checkpoint-authority/fixtures"/(kind+".json")
            if not owner.is_file():continue
            record=json.loads(owner.read_bytes())
            data={"_type":"https://in-toto.io/Statement/v1","predicateType":predicate.TYPE,
                  "predicate":record,"subject":[]}
            if "identities" in record:
                data["subject"]=statement(record)["subject"]
            else:
                import hashlib
                data["subject"]=[{"name":"record","digest":{"sha256":hashlib.sha256(predicate.canonical(record)).hexdigest()}}]
            with self.subTest(kind=kind):self.assertTrue(report(data).ok,report(data).to_dict())

    def test_missing_or_unchecked_declared_evidence_gates_fail_closed(self):
        from unittest.mock import patch
        original=predicate.check
        for missing in range(len(predicate.EXPECTED_RESULTS)):
            with patch.object(predicate,"check",side_effect=lambda value,index=missing:[x for i,x in enumerate(original(value)) if i!=index]):
                self.assertFalse(report(statement()).ok)

    def test_owner_schema_and_result_vocabulary_are_exact(self):
        owner=ROOT/"plugins/hexaemeron/skills/fiat/scripts"
        if not owner.is_dir():
            self.skipTest("checkout-only owner parity; isolated import is tested separately")
        sys.path.insert(0,str(owner))
        from checkpoint_authority import schema,wire
        self.assertEqual(predicate.SCHEMA,schema.family_document())
        self.assertEqual(predicate.PREDICATE_FIELDS,tuple(sorted({key for row in schema.SCHEMAS.values() for key in row["properties"]})))
        self.assertEqual(predicate.RESULTS,wire.RESULTS)
        self.assertEqual(predicate.TYPE,schema.PREDICATE)

    def test_isolated_install_import_and_verification(self):
        with tempfile.TemporaryDirectory(prefix="ariadne-checkpoint-isolated-") as temp:
            target=Path(temp)/"ariadne"
            shutil.copytree(PLUGIN/"scripts",target/"scripts",ignore=shutil.ignore_patterns("__pycache__"))
            shutil.copytree(PLUGIN/"schemas",target/"schemas")
            data=statement()
            path=Path(temp)/"statement.json";path.write_text(json.dumps(data))
            result=subprocess.run([sys.executable,"-I",str(target/"scripts/ariadne.py"),"verify",str(path),"--json"],
                capture_output=True,timeout=20,cwd=temp)
            self.assertEqual(result.returncode,0,result.stderr.decode())
            value=json.loads(result.stdout)
            self.assertTrue(value["predicateGatesChecked"])
            self.assertEqual(value["unchecked"],list(predicate.UNCHECKED))
