from __future__ import annotations
from pathlib import Path
from typing import Any
import json

REQUIRED_TOP = (
    "schema", "research_question", "objective", "null_hypothesis", "alternative_hypothesis",
    "assumptions", "symbols", "equations", "observables", "steps", "falsification_criteria"
)
PLACEHOLDERS = ("<<FILL", "TODO_SCIENCE", "REPLACE_BEFORE_FREEZE")

class ScienceContractError(RuntimeError):
    pass


def load_science_contract(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_science_contract(contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for k in REQUIRED_TOP:
        if k not in contract:
            errors.append(f"missing top-level field: {k}")
    text = json.dumps(contract, ensure_ascii=False)
    for token in PLACEHOLDERS:
        if token in text:
            errors.append(f"placeholder remains: {token}")
    eq_ids = set()
    for i, eq in enumerate(contract.get("equations", [])):
        for field in ("id", "purpose", "latex", "inputs", "outputs", "dimensional_check"):
            if field not in eq or eq[field] in (None, "", []):
                errors.append(f"equations[{i}] missing/empty {field}")
        if eq.get("id") in eq_ids:
            errors.append(f"duplicate equation id: {eq.get('id')}")
        eq_ids.add(eq.get("id"))
    step_ids=set()
    for i, step in enumerate(contract.get("steps", [])):
        for field in ("id", "operation", "formula_refs", "gate"):
            if field not in step or step[field] in (None, "", []):
                errors.append(f"steps[{i}] missing/empty {field}")
        for ref in step.get("formula_refs", []):
            if ref not in eq_ids:
                errors.append(f"steps[{i}] references unknown equation: {ref}")
        if step.get("id") in step_ids:
            errors.append(f"duplicate step id: {step.get('id')}")
        step_ids.add(step.get("id"))
    if not contract.get("falsification_criteria"):
        errors.append("at least one falsification criterion is required")
    return errors


def assert_science_contract(path: str | Path) -> dict[str, Any]:
    c = load_science_contract(path)
    errors = validate_science_contract(c)
    if errors:
        raise ScienceContractError("science contract incomplete:\n- " + "\n- ".join(errors))
    return c
