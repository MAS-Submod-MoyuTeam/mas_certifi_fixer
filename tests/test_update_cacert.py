import importlib.util
import pathlib
import tempfile
import unittest


SCRIPT = pathlib.Path(__file__).resolve().parents[1] / ".github/scripts/update_cacert.py"

OLD_CERT = (
    "\n# Issuer: CN=Old Root CA\n# Subject: CN=Old Root CA\n"
    "-----BEGIN CERTIFICATE-----\nOLD\n-----END CERTIFICATE-----\n"
)
NEW_CERT = (
    "\n# Issuer: CN=New Root CA\n# Subject: CN=New Root CA\n"
    "-----BEGIN CERTIFICATE-----\nNEW\n-----END CERTIFICATE-----\n"
)
RPY = '''init -1512 python:
    pass

init -990 python:
    certifi_fixer_submod = store.mas_submod_utils.Submod(
        author="P",
        name="CertifiFixer",
        version="1.0.2",
        description="Restores the bundled certifi package when MAS cannot import it."
    )
'''


def load_module():
    spec = importlib.util.spec_from_file_location("update_cacert", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class UpdateCacertTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.pem = self.root / "certifi" / "cacert.pem"
        self.pem.parent.mkdir(parents=True)
        self.pem.write_text(OLD_CERT, encoding="utf-8")
        self.rpy = self.root / "certifi_fixer.rpy"
        self.rpy.write_text(RPY, encoding="utf-8")
        self.module = load_module()

    def test_validate_accepts_pem_with_basic_instruction(self):
        self.module.validate(NEW_CERT.encode("ascii"))

    def test_validate_rejects_truncated_certificate(self):
        with self.assertRaises(SystemExit):
            self.module.validate(b"-----BEGIN CERTIFICATE-----\nNEW\n")

    def test_update_writes_certificate_and_bumps_patch_version(self):
        version = self.module.update(self.pem, self.rpy, NEW_CERT.encode("ascii"))
        self.assertEqual(version, "1.0.3")
        self.assertEqual(self.pem.read_bytes(), NEW_CERT.encode("ascii"))
        self.assertIn('version="1.0.3"', self.rpy.read_text(encoding="utf-8"))

    def test_update_keeps_version_when_certificate_is_unchanged(self):
        version = self.module.update(self.pem, self.rpy, NEW_CERT.encode("ascii"))
        self.assertEqual(version, "1.0.3")
        unchanged = self.module.update(self.pem, self.rpy, NEW_CERT.encode("ascii"))
        self.assertIsNone(unchanged)
        self.assertIn('version="1.0.3"', self.rpy.read_text(encoding="utf-8"))

    def test_update_requires_single_version_line(self):
        self.rpy.write_text(RPY + 'version="9.9.9"\n', encoding="utf-8")
        with self.assertRaises(SystemExit):
            self.module.update(self.pem, self.rpy, NEW_CERT.encode("ascii"))


if __name__ == "__main__":
    unittest.main()
