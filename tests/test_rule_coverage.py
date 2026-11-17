"""Fails if a rule ID used in the code has no test that mentions it."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ID = re.compile(r"BR-\d\d")


def ids_in(files):
    found = set()
    for f in files:
        found |= set(ID.findall(f.read_text(encoding="utf-8")))
    return found


def test_every_rule_id_in_code_is_tested():
    in_code = ids_in((ROOT / "ride").glob("*.py"))
    in_tests = ids_in(p for p in (ROOT / "tests").glob("test_*.py") if p.name != "test_rule_coverage.py")
    missing = sorted(in_code - in_tests)
    assert not missing, f"rule IDs without a test: {missing}"
