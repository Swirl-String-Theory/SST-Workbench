from __future__ import annotations
from pathlib import Path
import copy, tomllib
from typing import Any


def load_toml(path: str | Path) -> dict[str, Any]:
    with Path(path).open("rb") as f:
        return tomllib.load(f)


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def framework_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_instance_config(instance_root: str | Path) -> dict[str, Any]:
    root = Path(instance_root)
    local = load_toml(root / "falsifier.toml")
    profile_name = local.get("project", {}).get("profile", "minimal")
    profile_path = framework_root() / "profiles" / f"{profile_name}.toml"
    if not profile_path.exists():
        raise FileNotFoundError(f"unknown framework profile: {profile_name}")
    return deep_merge(load_toml(profile_path), local)
