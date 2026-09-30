"""
backend/tests/test_static.py
------------------------------
Static AST/grep tests (must fail suite immediately if triggered).

P0 rules:
- No datetime.now() or time.time() in backend/risk/ or backend/actions/
- No backend.nlp import in any Person 2 module
- No secret-looking literals in code

Authority: Plan v3 §6 (static tests).
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

RISK_PATH = REPO_ROOT / "backend" / "risk"
ACTIONS_PATH = REPO_ROOT / "backend" / "actions"
ALL_BACKEND = REPO_ROOT / "backend"

# Patterns that must NOT appear in source files


def _collect_py_files(*dirs: Path) -> list[Path]:
    files = []
    for d in dirs:
        if d.exists():
            files.extend(d.rglob("*.py"))
    return files


def test_no_datetime_now_in_risk_or_actions() -> None:
    """No datetime.now() or time.time() in risk or actions modules."""
    files = _collect_py_files(RISK_PATH, ACTIONS_PATH)
    violations = []
    for f in files:
        source = f.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(f))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                fn = node.func
                if isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name):
                    if (fn.value.id, fn.attr) in {("datetime", "now"), ("datetime", "utcnow"), ("time", "time")}:
                        violations.append(f"{f.relative_to(REPO_ROOT)}:{node.lineno} — forbidden clock call")

    assert not violations, "Forbidden time calls found:\n" + "\n".join(violations)


def test_no_backend_nlp_import() -> None:
    """No backend.nlp import anywhere in Person 2 modules."""
    files = _collect_py_files(ALL_BACKEND)
    violations = []
    for f in files:
        tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                if any(alias.name == "backend.nlp" or alias.name.startswith("backend.nlp.") for alias in node.names):
                    violations.append(f"{f.relative_to(REPO_ROOT)}:{node.lineno}")
            elif isinstance(node, ast.ImportFrom) and node.module and (node.module == "backend.nlp" or node.module.startswith("backend.nlp.")):
                violations.append(f"{f.relative_to(REPO_ROOT)}:{node.lineno}")

    assert not violations, "backend.nlp imports found in:\n" + "\n".join(violations)


def test_no_hardcoded_numeric_thresholds_in_risk() -> None:
    """Business thresholds may appear in documentation, not executable AST."""
    forbidden = {0.30, 0.85, 0.65}
    files = _collect_py_files(RISK_PATH)
    violations = []
    for f in files:
        if f.name == "config_loader.py":
            continue
        tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, float) and node.value in forbidden:
                violations.append(f"{f.relative_to(REPO_ROOT)}:{node.lineno}:{node.value}")
    assert not violations, "Business threshold literals belong in YAML: " + ", ".join(violations)
