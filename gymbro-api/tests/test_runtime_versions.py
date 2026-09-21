"""Guards against CI and Vercel running different Python and Node versions.

Vercel builds on the versions in `.python-version` and `engines.node`; CI reads
its own copies from the workflow. Before they were pinned, Vercel ran Python 3.12
and Node 24 while CI tested 3.11 and 20, so a green build proved little about
what was deployed.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


def _ci_env(name: str) -> str:
    match = re.search(rf"^\s*{name}:\s*'?([\d.]+)'?\s*$", CI_WORKFLOW.read_text(), re.M)
    assert match, f"{name} not found in {CI_WORKFLOW.name}"
    return match.group(1)


def test_python_version_matches_ci():
    pinned = (ROOT / ".python-version").read_text().strip()
    assert pinned == _ci_env("PYTHON_VERSION")


def test_node_version_matches_ci_and_engines():
    nvmrc = (ROOT / ".nvmrc").read_text().strip()
    engines = json.loads((ROOT / "gymbro-web" / "package.json").read_text())["engines"]["node"]
    assert nvmrc == _ci_env("NODE_VERSION")
    assert engines == f"{nvmrc}.x"
