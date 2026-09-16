"""Guards against production and CI installing different dependency sets.

This is the defect class that made the photo endpoint fail in production while
CI stayed green: `pillow` was in gymbro-api/requirements.txt (used by CI and
local dev) but not in api/requirements.txt (what Vercel installs for the
serverless function), so `from PIL import Image` raised ImportError only in
production.
"""

from pathlib import Path
from typing import Dict

import pytest

ROOT = Path(__file__).resolve().parents[2]
PROD_REQUIREMENTS = ROOT / "api" / "requirements.txt"
DEV_REQUIREMENTS = ROOT / "gymbro-api" / "requirements.txt"

# Test-only packages that are expected in the dev file and absent from production.
TEST_ONLY_PACKAGES = {"pytest", "pytest-asyncio", "pytest-cov", "respx", "ruff"}

# Packages the app imports at runtime. If one of these is missing from the
# production file, the deployed function breaks on import or first use.
RUNTIME_CRITICAL_PACKAGES = {
    "fastapi",
    "sqlmodel",
    "sqlalchemy",
    "pydantic",
    "pydantic-settings",
    "psycopg2-binary",
    "httpx",
    "pillow",
    "pyjwt",
    "python-multipart",
    "mangum",
    "alembic",
}


def _parse(path: Path) -> Dict[str, str]:
    """Parse a requirements file into {normalised_name: version}."""
    pins: Dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "==" not in line:
            pytest.fail(f"{path.name}: expected a pinned requirement, got {line!r}")
        name, version = line.split("==", 1)
        # Normalise "PyJWT[crypto]" -> "pyjwt" so extras and case don't matter.
        name = name.split("[", 1)[0].strip().lower().replace("_", "-")
        pins[name] = version.strip()
    return pins


@pytest.fixture(scope="module")
def prod_pins() -> Dict[str, str]:
    return _parse(PROD_REQUIREMENTS)


@pytest.fixture(scope="module")
def dev_pins() -> Dict[str, str]:
    return _parse(DEV_REQUIREMENTS)


def test_shared_packages_are_pinned_identically(prod_pins, dev_pins):
    """A package in both files must be pinned to the same version."""
    mismatched = {
        name: (prod_pins[name], dev_pins[name])
        for name in prod_pins.keys() & dev_pins.keys()
        if prod_pins[name] != dev_pins[name]
    }
    assert not mismatched, (
        "Version mismatch between api/requirements.txt (production) and "
        f"gymbro-api/requirements.txt (CI): {mismatched}"
    )


def test_production_has_every_runtime_critical_package(prod_pins):
    """The deployed function must install everything the app imports."""
    missing = RUNTIME_CRITICAL_PACKAGES - prod_pins.keys()
    assert not missing, (
        f"api/requirements.txt is missing runtime dependencies: {sorted(missing)}. "
        "CI would still pass, but the deployed function would fail."
    )


def test_dev_only_adds_test_packages(prod_pins, dev_pins):
    """The dev file should be the production set plus test tooling, nothing else.

    Anything else that drifts in is a dependency production will not have.
    """
    extra = dev_pins.keys() - prod_pins.keys() - TEST_ONLY_PACKAGES
    assert not extra, (
        f"gymbro-api/requirements.txt has packages production will not install: "
        f"{sorted(extra)}. Add them to api/requirements.txt or to TEST_ONLY_PACKAGES."
    )


def test_production_does_not_ship_test_tooling(prod_pins):
    """Test packages should not be deployed."""
    shipped = TEST_ONLY_PACKAGES & prod_pins.keys()
    assert not shipped, f"api/requirements.txt ships test-only packages: {sorted(shipped)}"


def test_requirements_files_are_utf8(request):
    """Both files must be UTF-8.

    They were previously written as UTF-16LE by PowerShell, which tooling reads
    inconsistently.
    """
    for path in (PROD_REQUIREMENTS, DEV_REQUIREMENTS):
        raw = path.read_bytes()
        assert not raw.startswith(b"\xff\xfe"), f"{path.name} is UTF-16LE, expected UTF-8"
        assert not raw.startswith(b"\xef\xbb\xbf"), f"{path.name} has a UTF-8 BOM"
        path.read_text(encoding="utf-8")  # raises if not valid UTF-8
