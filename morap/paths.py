"""Portable repository paths configured through environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from morap.compat import LEGACY_ENV_PREFIX

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def environment_value(name: str, default: str | None = None) -> str | None:
    """Read a MoRAP setting, falling back to its historical environment name."""
    if name in os.environ:
        return os.environ[name]
    if name.startswith("MORAP_"):
        return os.environ.get(LEGACY_ENV_PREFIX + name.removeprefix("MORAP_"), default)
    return os.environ.get(name, default)


def environment_path(name: str, default: Path) -> Path:
    """Return an absolute path from an environment variable or local default."""
    value = environment_value(name)
    return Path(value).expanduser().resolve() if value else default.resolve()


DATA_ROOT = environment_path("MORAP_DATA_ROOT", REPOSITORY_ROOT / "data")
CACHE_ROOT = environment_path("MORAP_CACHE_ROOT", DATA_ROOT / "cache")
RESULTS_ROOT = environment_path("MORAP_RESULTS_ROOT", REPOSITORY_ROOT / "outputs")
ARCHIVE_ROOT = environment_path("MORAP_ARCHIVE_ROOT", DATA_ROOT / "archive")
MODEL_ROOT = environment_path("MORAP_MODEL_ROOT", DATA_ROOT / "models")
