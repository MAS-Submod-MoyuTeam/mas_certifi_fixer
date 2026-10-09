import pathlib
import tempfile
import types
import unittest


SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "game/Submods/CertifiFixer/certifi_fixer.rpy"
FILES = ("__init__.py", "core.py", "cacert.pem")


def run_init(priority, namespace):
    lines = SCRIPT.read_text(encoding="utf-8").splitlines()
    marker = "init {} python:".format(priority)
    start = lines.index(marker) + 1
    end = next((i for i in range(start, len(lines)) if lines[i].startswith("init ")), len(lines))
    code = "\n".join(line[4:] if line.startswith("    ") else line for line in lines[start:end])
    exec(compile(code, str(SCRIPT), "exec"), namespace)


class StartupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.game = pathlib.Path(self.temp.name)
        self.source = self.game / "Submods/CertifiFixer/certifi"
        self.target = self.game / "python-packages/certifi"
        self.source.mkdir(parents=True)
        self.target.mkdir(parents=True)
        contents = {
            "__init__.py": "from .core import where, has_cert, set_parent_dir, check_update\n",
            "core.py": "\n".join("def {}(): pass".format(name) for name in
                                  ("where", "has_cert", "set_parent_dir", "check_update")) + "\n",
            "cacert.pem": "-----BEGIN CERTIFICATE-----\nvalid\n-----END CERTIFICATE-----\n",
        }
        for name in FILES:
            (self.source / name).write_text(contents[name], encoding="utf-8")

        self.messages = []
        self.enabled = True
        self.loads = 0

        class ImportState:
            def __call__(inner):
                return self.enabled

            def load(inner):
                self.loads += 1
                self.enabled = True

        self.import_state = ImportState()
        self.namespace = {
            "renpy": types.SimpleNamespace(config=types.SimpleNamespace(gamedir=str(self.game)), log=self.messages.append),
            "store": types.SimpleNamespace(mas_can_import=types.SimpleNamespace(certifi=self.import_state)),
        }

    def test_static_check_repairs_missing_file_before_mas_probe(self):
        for name in FILES:
            if name != "cacert.pem":
                (self.target / name).write_bytes((self.source / name).read_bytes())
        run_init(-1512, self.namespace)
        self.assertEqual((self.target / "cacert.pem").read_bytes(), (self.source / "cacert.pem").read_bytes())

    def test_static_check_preserves_valid_different_certificate(self):
        for name in FILES:
            (self.target / name).write_bytes((self.source / name).read_bytes())
        updated = b"-----BEGIN CERTIFICATE-----\nupdated\n-----END CERTIFICATE-----\n"
        (self.target / "cacert.pem").write_bytes(updated)
        run_init(-1512, self.namespace)
        self.assertEqual((self.target / "cacert.pem").read_bytes(), updated)

    def test_failed_mas_probe_repairs_and_rechecks_same_startup(self):
        for name in FILES:
            (self.target / name).write_bytes((self.source / name).read_bytes())
        (self.target / "core.py").write_text(
            "def where(): pass\ndef has_cert(): pass\n"
            "def set_parent_dir(): pass\ndef check_update(): pass\n",
            encoding="utf-8",
        )
        self.enabled = False
        run_init(-1512, self.namespace)
        run_init(-1499, self.namespace)
        self.assertEqual((self.target / "core.py").read_bytes(), (self.source / "core.py").read_bytes())
        self.assertEqual(self.loads, 1)

    def test_static_check_repairs_missing_required_function(self):
        for name in FILES:
            (self.target / name).write_bytes((self.source / name).read_bytes())
        (self.target / "core.py").write_text("def where(): pass\n", encoding="utf-8")
        run_init(-1512, self.namespace)
        self.assertEqual((self.target / "core.py").read_bytes(), (self.source / "core.py").read_bytes())

    def test_static_check_repairs_missing_export(self):
        for name in FILES:
            (self.target / name).write_bytes((self.source / name).read_bytes())
        (self.target / "__init__.py").write_text("from .core import where\n", encoding="utf-8")
        run_init(-1512, self.namespace)
        self.assertEqual((self.target / "__init__.py").read_bytes(), (self.source / "__init__.py").read_bytes())

    def test_healthy_mas_probe_does_not_reload(self):
        for name in FILES:
            (self.target / name).write_bytes((self.source / name).read_bytes())
        run_init(-1512, self.namespace)
        run_init(-1499, self.namespace)
        self.assertEqual(self.loads, 0)

    def test_bundled_package_passes_static_check(self):
        bundled = SCRIPT.parent / "certifi"
        for name in FILES:
            (self.target / name).write_bytes((bundled / name).read_bytes())
        run_init(-1512, self.namespace)
        self.assertTrue(self.namespace["_certifi_fixer_valid_package"]())
        self.assertFalse(self.messages)


if __name__ == "__main__":
    unittest.main()
