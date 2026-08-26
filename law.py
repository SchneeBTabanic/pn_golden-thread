"""
law.py — the sovereign's clauses, READ and never interpreted.

This module does not rank, score, select, embed, or inject clauses.
It loads the inoculated GoldenThread file by identity, and stops.

GT_LAW overrides the path. Else the in-tree copy at law/ (what a GitHub
clone ships). Else ../ref/canonical-docs/ (this working copy). Missing
file: hard-fail. Two copies of one law drift (Charter §3.13) — do not
edit one and leave the other.

declared.txt is displayed and never acted on. A declaration that quietly
acquired a trigger would be the failure this runtime exists to prevent.
"""
import json
import os
from dataclasses import dataclass, field
from typing import Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
_LAW_NAME = "GoldenThread-v1.6.2-Triune-Cathedral.json"
IN_TREE_LAW = os.path.join(HERE, "law", _LAW_NAME)
REF_LAW = os.path.normpath(os.path.join(
    HERE, "..", "ref", "canonical-docs", _LAW_NAME))
DECLARED_FILE = os.path.join(HERE, "law", "declared.txt")

INTEGRITY = {
    "conserves": "the clause text exactly as written — loaded, never "
                 "summarised, never embedded. Default: not placed. "
                 "/withlaw or GT_PLACE_LAW=1 places the WHOLE file, "
                 "verbatim, file order, no ranking",
    "discards": "nothing, and adds nothing — in particular no applies_when",
    "proves_it_by": "tests/test_law.py",
    "surfaced_as": "the clause ledger, every turn",
}


@dataclass
class Clause:
    id: str
    title: str
    text: str


@dataclass
class Law:
    clauses: List[Clause] = field(default_factory=list)
    by_id: Dict[str, Clause] = field(default_factory=dict)
    source_path: str = ""
    declared_conditions: List[str] = field(default_factory=list)
    declared_path: str = ""

    def get(self, clause_id) -> Clause:
        key = str(clause_id)
        if key not in self.by_id:
            raise KeyError(
                f"No clause {key} in {self.source_path}. Refusing a near "
                f"match: substituting a similar clause is the error this "
                f"runtime exists to remove.")
        return self.by_id[key]

    def __len__(self):
        return len(self.clauses)


def _clause_path() -> str:
    override = os.environ.get("GT_LAW", "").strip()
    if override:
        return override
    if os.path.isfile(IN_TREE_LAW):
        return IN_TREE_LAW
    return REF_LAW


def load() -> Law:
    path = _clause_path()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except OSError as e:
        raise SystemExit(
            f"The clause file is missing at {path} ({e}). Refusing to run. "
            f"Set GT_LAW, or place {_LAW_NAME} at law/ "
            f"(the clone ships it there), or keep ref/canonical-docs/ "
            f"next to this project.")
    except json.JSONDecodeError as e:
        raise SystemExit(f"The clause file at {path} is not valid JSON ({e}).")

    law = Law(source_path=path, declared_path=DECLARED_FILE)
    for c in data.get("clauses", []):
        desc = c.get("description", [])
        text = "\n".join(desc) if isinstance(desc, list) else str(desc)
        cl = Clause(id=str(c.get("id")), title=c.get("title", ""), text=text)
        law.clauses.append(cl)
        law.by_id[cl.id] = cl
    law.declared_conditions = _load_declared()
    return law


def _load_declared() -> List[str]:
    if not os.path.exists(DECLARED_FILE):
        return []
    out = []
    with open(DECLARED_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                out.append(line)
    return out


def law_text(law=None):
    """All clauses, verbatim, file order. Nothing ranked. Nothing omitted."""
    if law is None:
        law = load()
    parts = []
    for c in law.clauses:
        head = f"{c.id}. {c.title}".strip()
        if c.text:
            parts.append(head + "\n" + c.text)
        else:
            parts.append(head)
    return "\n\n".join(parts)


# There is NO search(), NO rank(), NO select(), NO relevance(), NO embed()
# in this module. tests/test_law.py fails if any appears.
