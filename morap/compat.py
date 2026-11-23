"""Read historical Lin-MNP artifacts without rewriting their sealed contents.

New outputs always use MoRAP names. Keep legacy spelling confined to this
module so existing prediction hashes and companion bundles remain valid.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping


LEGACY_ENV_PREFIX = "LIN_MNP_"
LEGACY_METHOD_ID = "lin_mnp"
LEGACY_MODEL_NAME = "Lin-MNP"


def artifact_value(payload: Mapping[str, Any], key: str, *fallbacks: str) -> Any:
    """Read a current field first, then its historical name or explicit aliases."""
    legacy_key = key.replace("morap", LEGACY_METHOD_ID)
    for candidate in dict.fromkeys((key, legacy_key, *fallbacks)):
        if candidate in payload:
            return payload[candidate]
    raise KeyError(f"missing artifact field: {key}")


def artifact_path(path: Path) -> Path:
    """Prefer a current bundle path; fall back to a historical method directory."""
    if path.exists():
        return path
    parts = list(path.parts)
    indices = [index for index, part in enumerate(parts) if part == "morap"]
    if not indices:
        return path
    parts[indices[-1]] = LEGACY_METHOD_ID
    legacy = Path(*parts)
    return legacy if legacy.exists() else path


def canonical_method_id(value: str) -> str:
    """Normalise this method's old IDs without changing comparator identities."""
    if value.casefold() in {"morap", LEGACY_METHOD_ID, LEGACY_MODEL_NAME.casefold()}:
        return "morap"
    return value


def compatible_environment(environment: Mapping[str, str]) -> dict[str, str]:
    """Pass the same settings to current adapters and archived helper scripts."""
    result = dict(environment)
    for name, value in environment.items():
        if name.startswith(LEGACY_ENV_PREFIX):
            result.setdefault("MORAP_" + name.removeprefix(LEGACY_ENV_PREFIX), value)
    for name, value in tuple(result.items()):
        if name.startswith("MORAP_"):
            result[LEGACY_ENV_PREFIX + name.removeprefix("MORAP_")] = value
    return result
