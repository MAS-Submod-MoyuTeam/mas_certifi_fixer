"""Refresh the bundled cacert.pem from certifi and bump the submod patch version.

Run without arguments from the repository root:

    python .github/scripts/update_cacert.py

The download URL comes from CERTIFI_URL and defaults to the raw file in the
certifi/python-certifi repository on the default branch.

Exit codes:
    0 - the bundled certificate changed (version was bumped) or already matched
    1 - the download or a local file is invalid
"""

import os
import pathlib
import re
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
CERTIFI_URL = os.environ.get(
    "CERTIFI_URL",
    "https://raw.githubusercontent.com/certifi/python-certifi/master/certifi/cacert.pem",
)

# Allow overriding the paths for local dry runs; CI uses the defaults.
CERT_PATH = pathlib.Path(
    os.environ.get("CERT_PATH", ROOT / "game/Submods/CertifiFixer/certifi/cacert.pem")
)
RPY_PATH = pathlib.Path(
    os.environ.get("RPY_PATH", ROOT / "game/Submods/CertifiFixer/certifi_fixer.rpy")
)
BEGIN = b"-----BEGIN CERTIFICATE-----"
END = b"-----END CERTIFICATE-----"
# Mirrors the version extraction used by release.yml so both stay in sync.
VERSION_RE = re.compile(
    r'^([ \t]*version=")(\d+)\.(\d+)\.(\d+)(")[ \t]*,?[ \t]*$', re.MULTILINE
)


def validate(data):
    """Reject anything that is not a complete PEM bundle."""
    # Upstream certifi prefixes the bundle with blank lines and "# Issuer"/"# Subject"
    # comments, so look for the first PEM certificate after those prefix lines.
    head = data.split(BEGIN, 1)[0] if BEGIN in data else data
    for line in head.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith(b"#"):
            raise SystemExit("downloaded certificate bundle has unexpected leading content")
    if data.count(BEGIN) != data.count(END) or not data.count(BEGIN):
        raise SystemExit("downloaded certificate bundle is incomplete")


def download(url=CERTIFI_URL):
    request = urllib.request.Request(url, headers={"User-Agent": "CertifiFixer-update"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def bump_version(rpy_path):
    text = rpy_path.read_text(encoding="utf-8")
    matches = list(VERSION_RE.finditer(text))
    if len(matches) != 1:
        raise SystemExit("expected exactly one semantic version in {}".format(rpy_path.name))
    match = matches[0]
    new = str(int(match.group(4)) + 1)
    updated = text[: match.start(4)] + new + text[match.end(4) :]
    rpy_path.write_text(updated, encoding="utf-8", newline="")
    version = "{}.{}.{}".format(match.group(2), match.group(3), new)
    print("submod version bumped to {}".format(version))
    return version


def update(cert_path, rpy_path, data):
    """Write data when it differs from cert_path and return the new version.

    Returns None when the bundled certificate is already identical.
    """
    validate(data)
    if cert_path.read_bytes() == data:
        return None
    cert_path.write_bytes(data)
    return bump_version(rpy_path)


def main():
    try:
        data = download()
    except Exception as exc:
        print("unable to download {}: {}".format(CERTIFI_URL, exc))
        return 1
    try:
        version = update(CERT_PATH, RPY_PATH, data)
    except (SystemExit, OSError) as exc:
        print("update failed: {}".format(exc))
        return 1
    if version is None:
        print("cacert.pem is already up to date")
    else:
        print("cacert.pem updated, version bumped to {}".format(version))
    return 0


if __name__ == "__main__":
    sys.exit(main())
