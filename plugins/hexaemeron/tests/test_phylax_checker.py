"""The Phylax boundary lint catches its eight rules and nothing else.

Every rule carries a specimen it must flag and a neighbour it must not. The
neighbours are the point: this marketplace has a test helper named `run` and
an RPC client with a `.call`, and a lint that flags those is a lint people
learn to bypass.
"""

import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "phylax" / "scripts" / "phylax.py"

spec = importlib.util.spec_from_file_location("phylax_lint", SCRIPT)
phylax = importlib.util.module_from_spec(spec)
spec.loader.exec_module(phylax)


def codes(source, name="sample.py"):
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / name
        path.write_text(source, encoding="utf-8")
        return sorted(finding.code for finding in phylax.check(path))


def findings(source, name="sample.ts"):
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / name
        path.write_text(source, encoding="utf-8")
        return phylax.check(path)


class UnsafeDeserialization(unittest.TestCase):
    def assert_p008(self, specimens):
        for label, source in specimens.items():
            with self.subTest(label=label):
                self.assertEqual(["P008"], codes(source))

    def test_pickle_load_and_loads_import_shapes_are_p008(self):
        self.assert_p008({
            "module-load": "import pickle\npickle.load(stream)\n",
            "module-loads": "import pickle\npickle.loads(payload)\n",
            "module-alias-load": "import pickle as codec\ncodec.load(stream)\n",
            "module-alias-loads": "import pickle as codec\ncodec.loads(payload)\n",
            "direct-load": "from pickle import load\nload(stream)\n",
            "direct-loads": "from pickle import loads\nloads(payload)\n",
            "direct-alias-load": "from pickle import load as decode\ndecode(stream)\n",
            "direct-alias-loads": "from pickle import loads as decode\ndecode(payload)\n",
        })

    def test_marshal_load_import_shapes_are_p008(self):
        self.assert_p008({
            "module": "import marshal\nmarshal.load(stream)\n",
            "module-alias": "import marshal as codec\ncodec.load(stream)\n",
            "direct": "from marshal import load\nload(stream)\n",
            "direct-alias": "from marshal import load as decode\ndecode(stream)\n",
        })

    def test_yaml_load_without_safe_loader_import_shapes_is_p008(self):
        self.assert_p008({
            "module": "import yaml\nyaml.load(payload)\n",
            "module-alias": "import yaml as parser\nparser.load(payload)\n",
            "direct": "from yaml import load\nload(payload)\n",
            "direct-alias": "from yaml import load as parse\nparse(payload)\n",
        })

    def test_yaml_load_with_unsafe_loader_is_p008(self):
        self.assert_p008({
            "full-loader": (
                "import yaml\nyaml.load(payload, Loader=yaml.FullLoader)\n"
            ),
            "loader-positional": "import yaml\nyaml.load(payload, yaml.Loader)\n",
            "direct-unsafe-loader": (
                "from yaml import load, UnsafeLoader\n"
                "load(payload, Loader=UnsafeLoader)\n"
            ),
            "unknown-loader": (
                "from yaml import load\nload(payload, Loader=trusted_loader)\n"
            ),
        })

    def test_dynamic_execution_nonliteral_input_is_p008(self):
        self.assert_p008({
            "bare-eval": "eval(payload)\n",
            "bare-exec": "exec(receive())\n",
            "builtins-eval": "import builtins\nbuiltins.eval(payload)\n",
            "builtins-alias-exec": (
                "import builtins as runtime\nruntime.exec(f\"run({payload})\")\n"
            ),
            "direct-alias-eval": (
                "from builtins import eval as evaluate\nevaluate(payload)\n"
            ),
            "direct-alias-exec": (
                "from builtins import exec as execute\nexecute(payload)\n"
            ),
        })

    def test_imports_after_function_definitions_still_resolve(self):
        self.assert_p008({
            "module": (
                "def decode(payload):\n"
                "    return pickle.loads(payload)\n"
                "import pickle\n"
            ),
            "direct": (
                "def decode(payload):\n"
                "    return decode_pickle(payload)\n"
                "from pickle import loads as decode_pickle\n"
            ),
        })

    def test_import_rebinding_does_not_hide_boundary_evidence(self):
        self.assertEqual(["P008"], codes(
            "import pickle as codec\n"
            "import json as codec\n"
            "codec.loads(payload)\n"
        ))
        self.assertEqual(["P008"], codes(
            "from pickle import loads as decode\n"
            "from json import loads as decode\n"
            "decode(payload)\n"
        ))
        self.assertEqual(["P008"], codes(
            "from yaml import load, SafeLoader as Loader\n"
            "from yaml import FullLoader as Loader\n"
            "load(payload, Loader=Loader)\n"
        ))
        self.assertEqual(["P008"], codes(
            "import yaml as parser\n"
            "import custom as parser\n"
            "parser.load(payload, Loader=parser.SafeLoader)\n"
        ))
        self.assertEqual(["P008"], codes(
            "import pickle as codec\n"
            "import yaml as codec\n"
            "codec.loads(payload)\n"
        ))
        self.assertEqual(["P008"], codes(
            "from builtins import eval as decode\n"
            "from yaml import load as decode\n"
            "decode('literal')\n"
        ))

    def test_conflicting_imports_do_not_claim_one_call_family(self):
        sentinel = "conflicting-import-sentinel"
        specimens = {
            "module-boundaries": (
                "import pickle as codec\n"
                "import yaml as codec\n"
                "codec.load(payload)\n"
            ),
            "direct-boundaries": (
                "from pickle import load as decode\n"
                "from yaml import load as decode\n"
                "decode(payload)\n"
            ),
            "boundary-and-neighbour": (
                "from pickle import load as decode\n"
                "from json import load as decode\n"
                "decode(payload)\n"
            ),
            "explicit-bare-shadow": (
                "from ast import literal_eval as eval\n"
                "eval(payload)\n"
            ),
        }
        for label, source in specimens.items():
            with self.subTest(label=label):
                result = findings(
                    f'payload = "{sentinel}"\n' + source,
                    "sample.py",
                )
                self.assertEqual(["P008"], [finding.code for finding in result])
                self.assertEqual(
                    "source-local bindings leave the boundary call family unresolved",
                    result[0].message,
                )
                self.assertNotIn(sentinel, str(result[0]))
                self.assertNotIn(sentinel, json.dumps(result[0].as_dict()))

    def test_bare_dynamic_calls_survive_cross_scope_yaml_aliases(self):
        specimens = {
            "eval": (
                "def run(payload, SafeLoader):\n"
                "    return eval(payload, SafeLoader)\n"
                "def imports_elsewhere():\n"
                "    from yaml import load as eval\n"
                "    from yaml import SafeLoader\n"
            ),
            "exec": (
                "def run(payload, SafeLoader):\n"
                "    exec(payload, SafeLoader)\n"
                "def imports_elsewhere():\n"
                "    from yaml import load as exec\n"
                "    from yaml import SafeLoader\n"
            ),
        }
        for label, source in specimens.items():
            with self.subTest(label=label):
                result = findings(source, "sample.py")
                self.assertEqual(["P008"], [finding.code for finding in result])
                self.assertEqual(
                    "source-local bindings leave the boundary call family unresolved",
                    result[0].message,
                )

    def test_safe_yaml_loaders_are_allowed_in_keyword_and_positional_forms(self):
        specimens = {
            "module-safe-keyword": (
                "import yaml\nyaml.load(payload, Loader=yaml.SafeLoader)\n"
            ),
            "module-safe-positional": (
                "import yaml\nyaml.load(payload, yaml.SafeLoader)\n"
            ),
            "module-csafe-keyword": (
                "import yaml as parser\n"
                "parser.load(payload, Loader=parser.CSafeLoader)\n"
            ),
            "module-csafe-positional": (
                "import yaml as parser\nparser.load(payload, parser.CSafeLoader)\n"
            ),
            "direct-safe-keyword": (
                "from yaml import load, SafeLoader\n"
                "load(payload, Loader=SafeLoader)\n"
            ),
            "direct-safe-positional": (
                "from yaml import load as parse, SafeLoader as Safe\n"
                "parse(payload, Safe)\n"
            ),
            "direct-csafe-keyword": (
                "from yaml import load, CSafeLoader\n"
                "load(payload, Loader=CSafeLoader)\n"
            ),
            "direct-csafe-positional": (
                "from yaml import load as parse, CSafeLoader as FastSafe\n"
                "parse(payload, FastSafe)\n"
            ),
        }
        for label, source in specimens.items():
            with self.subTest(label=label):
                self.assertEqual([], codes(source))

    def test_yaml_loader_keyword_takes_precedence_over_second_position(self):
        self.assertEqual([], codes(
            "import yaml\n"
            "yaml.load(payload, yaml.FullLoader, Loader=yaml.SafeLoader)\n"
        ))
        self.assertEqual(["P008"], codes(
            "import yaml\n"
            "yaml.load(payload, yaml.SafeLoader, Loader=yaml.FullLoader)\n"
        ))

    def test_argument_shape_edges_follow_the_stated_grammar(self):
        self.assert_p008({
            "pickle-no-args": "import pickle\npickle.load()\n",
            "yaml-no-args": "import yaml\nyaml.load()\n",
        })
        self.assertEqual([], codes("eval()\nexec(source=payload)\n"))
        self.assertEqual(["P008"], codes(
            "def eval(value):\n"
            "    return value\n"
            "eval(payload)\n"
        ))

    def test_nested_boundary_calls_each_report_once(self):
        result = findings(
            "import pickle\n"
            "eval(pickle.loads(payload))\n",
            "sample.py",
        )
        self.assertEqual(
            [
                "dynamic execution receives non-literal source",
                "pickle deserialization may execute untrusted code",
            ],
            [finding.message for finding in result],
        )

    def test_named_safe_and_out_of_scope_neighbours_are_allowed(self):
        source = (
            "import json\n"
            "import marshal\n"
            "import pickle\n"
            "import yaml\n"
            "from marshal import loads as decode_marshaled\n"
            "from yaml import safe_load as parse_yaml\n"
            "yaml.safe_load(payload)\n"
            "parse_yaml(payload)\n"
            "marshal.loads(payload)\n"
            "decode_marshaled(payload)\n"
            "json.load(stream)\n"
            "json.loads(payload)\n"
            "pickle.dump(value, stream)\n"
            "pickle.dumps(value)\n"
            "reader.load(payload)\n"
            "from .pickle import load as local_load\n"
            "local_load(stream)\n"
        )
        self.assertEqual([], codes(source))

    def test_literal_string_and_bytes_dynamic_sources_are_allowed(self):
        source = (
            "import builtins as runtime\n"
            "from builtins import exec as execute\n"
            "eval('1 + 1')\n"
            "exec(b'pass')\n"
            "runtime.eval(b'1 + 1')\n"
            "execute('value = 1')\n"
        )
        self.assertEqual([], codes(source))

    def test_reason_bearing_p008_pragma_suppresses_but_a_bare_one_does_not(self):
        self.assertEqual([], codes(
            "import pickle\n"
            "pickle.loads(payload)  # phylax: allow reviewed compatibility fixture\n"
        ))
        self.assertEqual(["P008"], codes(
            "import pickle\npickle.loads(payload)  # phylax: allow\n"
        ))

    def test_p008_diagnostics_are_fixed_and_do_not_repeat_payload(self):
        sample_value = "unsafe-deserialization-sentinel"
        result = findings(
            "import pickle\n"
            f'payload = "{sample_value}"\n'
            "pickle.loads(payload)\n",
            "sample.py",
        )
        self.assertEqual(["P008"], [finding.code for finding in result])
        self.assertEqual(
            "pickle deserialization may execute untrusted code",
            result[0].message,
        )
        rendered = "\n".join(str(finding) for finding in result)
        encoded = json.dumps([finding.as_dict() for finding in result])
        self.assertNotIn(sample_value, rendered)
        self.assertNotIn(sample_value, encoded)

    def test_import_alias_rebinding_is_not_followed(self):
        self.assertEqual(["P008"], codes(
            "import pickle as codec\ncodec = local_reader\ncodec.loads(payload)\n"
        ))
        self.assertEqual([], codes(
            "from yaml import load as parse, SafeLoader as Safe\n"
            "Safe = custom_loader\nparse(payload, Loader=Safe)\n"
        ))

    def test_p000_through_p007_classifications_remain_available(self):
        specimens = {
            "P000": ("(", "sample.py"),
            "P001": (
                "import subprocess\nsubprocess.run(['tool'], shell=True)\n",
                "sample.py",
            ),
            "P002": ("import subprocess\nsubprocess.run('tool')\n", "sample.py"),
            "P003": ("package>=1\n", "requirements.txt"),
            "P004": ('SECRET = "fixture-value"\n', "sample.py"),
            "P005": (
                'import raw from "rehype-raw"\n'
                "const view = <Markdown rehypePlugins={[raw]} />\n",
                "sample.tsx",
            ),
            "P006": (
                'localStorage.setItem("authToken", authToken)\n',
                "sample.ts",
            ),
            "P007": (
                "async function load(host: string) {\n"
                "  return fetch(`https://${host}/api`)\n"
                "}\n",
                "sample.ts",
            ),
        }
        for expected, (source, name) in specimens.items():
            with self.subTest(code=expected):
                self.assertEqual([expected], codes(source, name))


class ShellInvocation(unittest.TestCase):
    def test_it_flags_a_shell_invocation(self):
        self.assertIn("P001", codes(
            "import subprocess\nsubprocess.run(['ls'], shell=True)\n"))

    def test_it_allows_an_argument_list(self):
        self.assertEqual([], codes("import subprocess\nsubprocess.run(['ls', '-l'])\n"))


class StringCommands(unittest.TestCase):
    def test_it_flags_a_string_command(self):
        self.assertIn("P002", codes("import subprocess\nsubprocess.run('git status')\n"))

    def test_it_flags_a_command_built_by_formatting(self):
        self.assertIn("P002", codes(
            "import subprocess\nref = 'main'\nsubprocess.run(f'git checkout {ref}')\n"))

    def test_it_flags_a_direct_import(self):
        self.assertIn("P002", codes("from subprocess import run\nrun('git status')\n"))

    def test_it_allows_list_concatenation(self):
        self.assertEqual([], codes(
            "import subprocess\nbase = ['git']\nsubprocess.run(base + ['status'])\n"))

    def test_it_ignores_a_local_helper_named_run(self):
        self.assertEqual([], codes(
            "def run(name):\n    return name\n\nrun('venues')\n"))

    def test_it_ignores_an_unrelated_call_method(self):
        self.assertEqual([], codes(
            "class Client:\n    def call(self, method, params):\n        return method\n\n"
            "Client().call('eth_chainId', [])\n"))


class SubprocessCredentialArguments(unittest.TestCase):
    def test_it_flags_module_runner_argv(self):
        self.assertEqual(["P004"], codes(
            "import subprocess\napi_key = load()\n"
            "subprocess.run(['tool', api_key])\n"))

    def test_it_flags_module_alias_runner_argv(self):
        self.assertEqual(["P004"], codes(
            "import subprocess as sp\nsecret = load()\n"
            "sp.check_call(['tool', secret])\n"))

    def test_it_flags_direct_import_runner_argv(self):
        self.assertEqual(["P004"], codes(
            "from subprocess import run\nauth_token = load()\n"
            "run(('tool', auth_token))\n"))

    def test_it_flags_direct_import_alias_runner_argv(self):
        self.assertEqual(["P004"], codes(
            "from subprocess import Popen as spawn\nprivate_key = load()\n"
            "spawn(['tool', private_key])\n"))

    def test_it_flags_keyword_args_argv(self):
        self.assertEqual(["P004"], codes(
            "import subprocess\ncredential = load()\n"
            "subprocess.run(args=['tool', credential])\n"))

    def test_it_flags_list_concatenation_without_p002(self):
        self.assertEqual(["P004"], codes(
            "import subprocess\naccess_token = load()\n"
            "subprocess.run(['tool'] + ['--auth', access_token])\n"))

    def test_it_allows_ordinary_argv_values(self):
        self.assertEqual([], codes(
            "import subprocess\nmarket = load()\n"
            "subprocess.run(['tool', market])\n"))

    def test_it_ignores_a_local_runner_name(self):
        self.assertEqual([], codes(
            "def run(argv):\n    return argv\n\nsecret = load()\n"
            "run(['tool', secret])\n"))

    def test_it_ignores_an_unrelated_call_method(self):
        self.assertEqual([], codes(
            "class Client:\n    def call(self, argv):\n        return argv\n\n"
            "api_key = load()\nClient().call(['tool', api_key])\n"))

    def test_it_allows_a_credential_only_in_env(self):
        self.assertEqual([], codes(
            "import subprocess\napi_key = load()\n"
            "subprocess.run(['tool'], env={'API_KEY': api_key})\n"))

    def test_a_stated_reason_suppresses_the_argv_finding(self):
        self.assertEqual([], codes(
            "import subprocess\nsecret = load()\n"
            "subprocess.run(['fixture', secret])  # phylax: allow hostile fixture\n"))

    def test_a_bare_pragma_does_not_suppress_the_argv_finding(self):
        self.assertEqual(["P004"], codes(
            "import subprocess\nsecret = load()\n"
            "subprocess.run(['fixture', secret])  # phylax: allow\n"))

    def test_shell_classification_stays_p001_beside_p004(self):
        self.assertEqual(["P001", "P004"], codes(
            "import subprocess\nsecret = load()\n"
            "subprocess.run(['tool', secret], shell=True)\n"))

    def test_string_command_classification_stays_p002(self):
        self.assertEqual(["P002"], codes(
            "import subprocess\nsubprocess.run('tool --version')\n"))

    def test_argv_findings_do_not_repeat_secret_material_in_text_or_json(self):
        sample_value = "test-only-credential-value"
        result = findings(
            "import subprocess\n"
            f'api_key = load("{sample_value}")\n'
            "subprocess.run(['tool', api_key])\n",
            "sample.py",
        )
        self.assertEqual(["P004"], [finding.code for finding in result])
        rendered = "\n".join(str(finding) for finding in result)
        encoded = json.dumps([finding.as_dict() for finding in result])
        self.assertNotIn(sample_value, rendered)
        self.assertNotIn(sample_value, encoded)


class Requirements(unittest.TestCase):
    def test_it_flags_an_unpinned_requirement(self):
        self.assertIn("P003", codes("rlp>=4.0.0\n", name="requirements.txt"))

    def test_it_allows_an_exact_pin(self):
        self.assertEqual([], codes("rlp==4.1.0\n", name="requirements.txt"))

    def test_it_skips_comments_and_includes(self):
        self.assertEqual([], codes("# a note\n-r other.txt\n\n", name="requirements.txt"))


class Credentials(unittest.TestCase):
    def test_it_flags_a_credential_literal(self):
        self.assertIn("P004", codes('API_KEY = "sk-live-9f4b2c8e1a7d"\n'))

    def test_it_flags_a_credential_written_to_output(self):
        self.assertIn("P004", codes(
            "import logging\nprivate_key = load()\nlogging.info(private_key)\n"))

    def test_it_allows_a_credential_read_from_the_environment(self):
        self.assertEqual([], codes('import os\nAPI_KEY = os.environ["API_KEY"]\n'))

    def test_it_allows_a_placeholder(self):
        self.assertEqual([], codes('API_KEY = "<your key here>"\n'))

    def test_it_allows_an_unrelated_name(self):
        self.assertEqual([], codes('MARKET_NAME = "wildcat-usdc"\n'))


class Suppression(unittest.TestCase):
    def test_a_stated_reason_suppresses_the_finding(self):
        self.assertEqual([], codes(
            'SECRET = "9f4b2c8e"  # phylax: allow scrubbing fixture, not live\n'))

    def test_a_reason_on_the_line_above_also_suppresses(self):
        self.assertEqual([], codes(
            '# phylax: allow fixture material\nSECRET = "9f4b2c8e"\n'))

    def test_a_bare_pragma_without_a_reason_does_not_suppress(self):
        self.assertIn("P004", codes('SECRET = "9f4b2c8e"  # phylax: allow\n'))


class RawHTML(unittest.TestCase):
    def test_it_flags_raw_rehype_without_a_later_sanitiser_on_the_exact_line(self):
        source = (
            'import raw from "rehype-raw"\n'
            'import clean from "rehype-sanitize"\n'
            'const view = <Markdown rehypePlugins={[\n'
            '  raw,\n'
            ']} />\n'
        )
        result = findings(source, "sample.tsx")
        self.assertEqual(["P005"], [finding.code for finding in result])
        self.assertEqual(4, result[0].line)

    def test_it_allows_import_aliases_in_safe_order(self):
        source = (
            'import unsafeTransform from "rehype-raw"\n'
            'import scrub from "rehype-sanitize"\n'
            'const view = <Markdown rehypePlugins={[unsafeTransform, scrub]} />\n'
        )
        self.assertEqual([], codes(source, "sample.tsx"))

    def test_it_allows_emotion_style_injection(self):
        source = '<style dangerouslySetInnerHTML={{ __html: styles }} />\n'
        self.assertEqual([], codes(source, "sample.tsx"))

    def test_it_flags_raw_named_html_without_a_trusted_call(self):
        source = 'const view = <div dangerouslySetInnerHTML={{ __html: rawHtml }} />\n'
        self.assertEqual(["P005"], codes(source, "sample.tsx"))

    def test_a_side_effect_import_does_not_hide_the_raw_binding(self):
        source = (
            'import "./setup"\n'
            'import raw from "rehype-raw"\n'
            'const view = <Markdown rehypePlugins={[raw]} />\n'
        )
        self.assertEqual(["P005"], codes(source, "sample.tsx"))

    def test_it_allows_raw_html_passed_to_an_imported_sanitiser(self):
        source = (
            'import clean from "sanitize-html"\n'
            'const view = <div dangerouslySetInnerHTML={{ __html: clean(rawHtml) }} />\n'
        )
        self.assertEqual([], codes(source, "sample.tsx"))

    def test_an_unrelated_function_named_sanitize_does_not_earn_trust(self):
        source = (
            'const sanitize = (value: string) => value\n'
            'const view = <div dangerouslySetInnerHTML={{ __html: sanitize(rawHtml) }} />\n'
        )
        self.assertEqual(["P005"], codes(source, "sample.tsx"))


class PersistedSessions(unittest.TestCase):
    def test_it_flags_a_session_token_written_to_storage_on_the_exact_line(self):
        source = (
            'const accessToken = getToken()\n'
            'localStorage.setItem("accessToken", accessToken)\n'
        )
        result = findings(source)
        self.assertEqual(["P006"], [finding.code for finding in result])
        self.assertEqual(2, result[0].line)

    def test_it_allows_ordinary_ui_storage(self):
        self.assertEqual([], codes(
            'localStorage.setItem("lastSeen", String(Date.now()))\n', "sample.ts"))

    def test_it_allows_api_token_domain_and_pending_signature_names(self):
        source = (
            'type ApiTokensState = { apiTokens: Record<string, string> }\n'
            'type Pending = { signature?: string }\n'
            'localStorage.setItem("apiTokens", JSON.stringify(apiTokens))\n'
        )
        self.assertEqual([], codes(source, "sample.ts"))

    def test_it_flags_a_session_field_in_a_persisted_reducer(self):
        source = (
            'import { persistReducer } from "redux-persist"\n'
            'type AuthState = { sessionToken: string }\n'
            'const persistConfig = { key: "auth", storage }\n'
            'export default persistReducer(persistConfig, reducer)\n'
        )
        result = findings(source)
        self.assertEqual(["P006"], [finding.code for finding in result])
        self.assertEqual(4, result[0].line)

    def test_it_allows_a_sensitive_field_on_the_blacklist(self):
        source = (
            'import { persistReducer } from "redux-persist"\n'
            'type AuthState = { authToken: string; theme: string }\n'
            'const persistConfig = { key: "auth", storage, blacklist: ["authToken"] }\n'
            'export default persistReducer(persistConfig, reducer)\n'
        )
        self.assertEqual([], codes(source, "sample.ts"))

    def test_it_allows_a_whitelist_that_omits_the_sensitive_field(self):
        source = (
            'import { persistReducer } from "redux-persist"\n'
            'type AuthState = { jwt: string; theme: string }\n'
            'const persistConfig = { key: "auth", storage, whitelist: ["theme"] }\n'
            'export default persistReducer(persistConfig, reducer)\n'
        )
        self.assertEqual([], codes(source, "sample.ts"))

    def test_it_allows_a_visible_transform_that_removes_the_sensitive_field(self):
        source = (
            'import { createTransform, persistReducer } from "redux-persist"\n'
            'type AuthState = { authToken: string; theme: string }\n'
            'const stripAuth = createTransform((state: AuthState) => {\n'
            '  const { authToken, ...safe } = state\n'
            '  return safe\n'
            '})\n'
            'const config = { key: "auth", storage, transforms: [stripAuth] }\n'
            'export default persistReducer(config, reducer)\n'
        )
        self.assertEqual([], codes(source, "sample.ts"))


class FetchHosts(unittest.TestCase):
    def test_it_flags_an_interpolated_absolute_host_on_the_exact_line(self):
        source = (
            'async function load(host: string) {\n'
            '  return fetch(`https://${host}/api`)\n'
            '}\n'
        )
        result = findings(source)
        self.assertEqual(["P007"], [finding.code for finding in result])
        self.assertEqual(2, result[0].line)

    def test_it_flags_new_url_with_a_runtime_base(self):
        source = (
            'async function load(host: string) {\n'
            '  const url = new URL("/api", host)\n'
            '  return fetch(url.toString())\n'
            '}\n'
        )
        self.assertEqual(["P007"], codes(source, "sample.ts"))

    def test_it_allows_a_prior_named_allowlist_guard(self):
        source = (
            'const ALLOWED_HOSTS = new Set(["api.example"])\n'
            'async function load(host: string) {\n'
            '  if (!ALLOWED_HOSTS.has(host)) throw new Error("not allowed")\n'
            '  return fetch(`https://${host}/api`)\n'
            '}\n'
        )
        self.assertEqual([], codes(source, "sample.ts"))

    def test_a_non_dominating_membership_check_does_not_earn_trust(self):
        source = (
            'const ALLOWED_HOSTS = new Set(["api.example"])\n'
            'async function load(host: string) {\n'
            '  if (ALLOWED_HOSTS.has(host)) recordAllowed(host)\n'
            '  return fetch(`https://${host}/api`)\n'
            '}\n'
        )
        self.assertEqual(["P007"], codes(source, "sample.ts"))

    def test_it_allows_relative_same_origin_and_fixed_urls(self):
        source = (
            'fetch("/api/items")\n'
            'fetch(new URL("/api/items", window.location.origin))\n'
            'fetch("https://api.example/items")\n'
        )
        self.assertEqual([], codes(source, "sample.ts"))

    def test_a_bare_fetch_binding_has_no_invented_host(self):
        self.assertEqual([], codes(
            'async function query(url: string) { return fetch(url) }\n', "sample.ts"))


class TypeScriptContract(unittest.TestCase):
    def test_reason_bearing_line_and_previous_line_suppressions_work(self):
        self.assertEqual([], codes(
            '// phylax: allow hostile fixture\n'
            'localStorage.setItem("authToken", authToken)\n', "sample.ts"))
        self.assertEqual([], codes(
            'localStorage.setItem("authToken", authToken) // phylax: allow test-only token\n',
            "sample.ts",
        ))

    def test_a_bare_typescript_pragma_does_not_suppress(self):
        self.assertEqual(["P006"], codes(
            'localStorage.setItem("authToken", authToken) // phylax: allow\n',
            "sample.ts",
        ))

    def test_unterminated_typescript_is_p000(self):
        result = findings('const value = `unterminated ${name}\n')
        self.assertEqual(["P000"], [finding.code for finding in result])
        self.assertEqual(1, result[0].line)

    def test_oversized_typescript_stops_at_the_analysis_cap(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "oversized.ts"
            path.write_bytes(b"a" * (phylax.TYPESCRIPT_MAX_BYTES + 1))
            result = phylax.check(path)
        self.assertEqual(["P000"], [finding.code for finding in result])
        self.assertIn("1048576-byte analysis cap", result[0].message)

    def test_findings_do_not_repeat_secret_material_in_text_or_json(self):
        sample_value = "top-secret-session-value"
        result = findings(
            f'const accessToken = "{sample_value}"\n'
            'localStorage.setItem("accessToken", accessToken)\n'
        )
        rendered = "\n".join(str(finding) for finding in result)
        encoded = json.dumps([finding.as_dict() for finding in result])
        self.assertNotIn(sample_value, rendered)
        self.assertNotIn(sample_value, encoded)

    def test_main_accepts_mixed_python_and_typescript_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            python_path = Path(directory) / "unsafe.py"
            typescript_path = Path(directory) / "unsafe.ts"
            python_path.write_text('SECRET = "live-value"\n', encoding="utf-8")
            typescript_path.write_text(
                'localStorage.setItem("authToken", authToken)\n', encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                status = phylax.main([str(python_path), str(typescript_path)])
        self.assertEqual(1, status)
        self.assertIn("P004", output.getvalue())
        self.assertIn("P006", output.getvalue())


if __name__ == "__main__":
    unittest.main()
