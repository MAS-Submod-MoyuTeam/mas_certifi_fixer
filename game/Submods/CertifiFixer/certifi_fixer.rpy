init -1512 python:
    import ast
    import os
    import shutil
    import sys

    _certifi_fixer_files = ("__init__.py", "core.py", "cacert.pem")
    _certifi_fixer_source = os.path.join(
        renpy.config.gamedir, "Submods", "CertifiFixer", "certifi"
    )
    _certifi_fixer_target = os.path.join(
        renpy.config.gamedir, "python-packages", "certifi"
    )

    def _certifi_fixer_valid_package():
        try:
            for filename in _certifi_fixer_files:
                path = os.path.join(_certifi_fixer_target, filename)
                if not os.path.isfile(path) or os.path.getsize(path) == 0:
                    return False

            with open(os.path.join(_certifi_fixer_target, "core.py"), "rb") as code_file:
                core = ast.parse(code_file.read())
            functions = set(
                node.name for node in core.body if isinstance(node, ast.FunctionDef)
            )
            if not set(("where", "has_cert", "set_parent_dir", "check_update")).issubset(functions):
                return False

            with open(os.path.join(_certifi_fixer_target, "__init__.py"), "rb") as code_file:
                package = ast.parse(code_file.read())
            exports = set(
                alias.name
                for node in package.body if isinstance(node, ast.ImportFrom) and node.module == "core"
                for alias in node.names
            )
            if not set(("where", "has_cert", "set_parent_dir", "check_update")).issubset(exports):
                return False

            with open(os.path.join(_certifi_fixer_target, "cacert.pem"), "rb") as cert_file:
                cert = cert_file.read()
            return b"-----BEGIN CERTIFICATE-----" in cert and b"-----END CERTIFICATE-----" in cert
        except (IOError, OSError, SyntaxError, ValueError):
            return False

    def _certifi_fixer_replace_certifi():
        if not all(os.path.isfile(os.path.join(_certifi_fixer_source, name)) for name in _certifi_fixer_files):
            renpy.log("CertifiFixer: bundled certifi files are missing")
            return False

        try:
            if not os.path.isdir(_certifi_fixer_target):
                os.makedirs(_certifi_fixer_target)
            for filename in _certifi_fixer_files:
                shutil.copy2(
                    os.path.join(_certifi_fixer_source, filename),
                    os.path.join(_certifi_fixer_target, filename)
                )
        except (IOError, OSError) as exc:
            renpy.log("CertifiFixer: unable to replace certifi: {}".format(exc))
            return False

        renpy.log("CertifiFixer: replaced game/python-packages/certifi")
        return True

    if not _certifi_fixer_valid_package():
        _certifi_fixer_replace_certifi()


init -1499 python:
    if not store.mas_can_import.certifi() and _certifi_fixer_replace_certifi():
        sys.modules.pop("certifi.core", None)
        sys.modules.pop("certifi", None)
        store.mas_can_import.certifi.load()


init -990 python:
    certifi_fixer_submod = store.mas_submod_utils.Submod(
        author="P",
        name="CertifiFixer",
        version="1.0.2",
        description="Restores the bundled certifi package when MAS cannot import it."
    )
