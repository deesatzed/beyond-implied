"""Project paths and config loading."""

from __future__ import annotations

import os
import tomllib
from pathlib import Path


def project_root() -> Path:
    """Repo root: $BI_ROOT if set, else the nearest parent of cwd containing pyproject.toml."""
    env = os.environ.get("BI_ROOT")
    if env:
        return Path(env).resolve()
    here = Path.cwd().resolve()
    for p in (here, *here.parents):
        if (p / "pyproject.toml").exists() and (p / "src" / "beyond_implied").exists():
            return p
    return here


def data_dir() -> Path:
    return project_root() / "data"


def raw_dir(source: str) -> Path:
    d = data_dir() / "raw" / source
    d.mkdir(parents=True, exist_ok=True)
    return d


def ledger_path() -> Path:
    return project_root() / "ledger" / "predictions.jsonl"


def load_toml(path: str | Path) -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)


def universe_config() -> dict:
    return load_toml(project_root() / "config" / "universe.toml")
