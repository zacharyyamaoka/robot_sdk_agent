"""The ruler is frozen: its files hash to the sha256 written in OBJECTIVES.md. A solution that edits the scorer (or its
tests and fixtures) turns this red. A real ruler change is a new version: a new OBJECTIVES.md section and a new hash."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RULER_FILES = ("scorer/*.py", "tests/ruler_fixtures.py", "tests/test_scorer_*.py")


def ruler_files() -> list[Path]:
    return sorted({p for pattern in RULER_FILES for p in REPO.glob(pattern)})


def ruler_sha256() -> str:
    digest = hashlib.sha256()
    for path in ruler_files():
        digest.update(path.relative_to(REPO).as_posix().encode() + b"\0")
        digest.update(path.read_bytes().replace(b"\r\n", b"\n") + b"\0")
    return digest.hexdigest()


def test_ruler_matches_the_hash_in_objectives():
    stated = re.search(r"ruler sha256: `([0-9a-f]{64})`", (REPO / "OBJECTIVES.md").read_text(encoding="utf-8"))
    assert stated, "OBJECTIVES.md must state `ruler sha256: `<hex>``"
    assert ruler_sha256() == stated.group(1), "the scorer changed: that is ruler v2 (OBJECTIVES.md), never a solution"


def test_the_hash_covers_the_scorer():
    names = {p.relative_to(REPO).as_posix() for p in ruler_files()}
    assert {"scorer/score.py", "scorer/collect.py", "scorer/__init__.py"} <= names


def test_no_solution_ships_its_own_scorer():
    assert not [p for p in (REPO / "solutions").rglob("*") if "scorer" in p.parts]


if __name__ == "__main__":
    print(ruler_sha256())
