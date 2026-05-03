"""Typed configuration model for the download-engine seam.

This config is intentionally small and serializable. Persistence and UI
binding are out of scope for this patch — the model only declares shape and
validation rules so later patches can persist it safely.

Security boundaries:
- Engine-specific settings live in a namespaced `engine_settings` mapping so
  that one engine cannot read another's settings by accident.
- `engine_settings` is `field(repr=False)` so default `repr()`/`str()` will
  not leak any token/cookie/secret values that future engines might store
  there (for example an aria2c RPC secret). Callers who need to inspect the
  settings must do so explicitly via `engine_settings_for()`.
- The model never reads files and never executes anything.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, fields, replace
from types import MappingProxyType
from typing import Any, TypeVar

from .models import EngineInputType, validate_engine_id

SCHEMA_VERSION = 1


_K = TypeVar("_K")
_V = TypeVar("_V")


def _freeze_mapping(value: Mapping[_K, _V]) -> Mapping[_K, _V]:
    return MappingProxyType(dict(value))


@dataclass(frozen=True)
class EngineConfig:
    """User-facing engine selection/preference state.

    Fields:
    - `default_engine_id`: preferred engine id when no per-scheme/per-input
      preference matches. Validated against the registry by the factory.
    - `auto_select_enabled`: when True, the registry/factory may fall back to
      any healthy engine if the preferred one is unavailable. When False,
      callers must honor preferences strictly.
    - `disabled_engine_ids`: engines the user has opted out of. Disabled
      engines are not registered by `create_default_registry`.
    - `per_scheme_preference`: scheme (lowercase, no colon) -> engine id.
    - `per_input_type_preference`: `EngineInputType` -> engine id.
    - `engine_settings`: namespaced per-engine free-form settings. Excluded
      from `repr()` to avoid leaking secret values.
    - `schema_version`: bumped only when the on-disk shape changes.
    """

    default_engine_id: str | None = None
    auto_select_enabled: bool = True
    disabled_engine_ids: tuple[str, ...] = ()
    per_scheme_preference: Mapping[str, str] = field(default_factory=dict)
    per_input_type_preference: Mapping[EngineInputType, str] = field(default_factory=dict)
    engine_settings: Mapping[str, Mapping[str, Any]] = field(default_factory=dict, repr=False)
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.default_engine_id is not None:
            validate_engine_id(self.default_engine_id)

        seen_disabled: set[str] = set()
        for engine_id in self.disabled_engine_ids:
            validate_engine_id(engine_id)
            if engine_id in seen_disabled:
                raise ValueError(
                    f"Duplicate engine id in disabled_engine_ids: {engine_id!r}"
                )
            seen_disabled.add(engine_id)

        if self.default_engine_id is not None and self.default_engine_id in seen_disabled:
            raise ValueError(
                f"default_engine_id {self.default_engine_id!r} is also in "
                f"disabled_engine_ids"
            )

        normalized_scheme: dict[str, str] = {}
        for scheme, engine_id in self.per_scheme_preference.items():
            if not scheme:
                raise ValueError("per_scheme_preference scheme must be non-empty")
            validate_engine_id(engine_id)
            key = scheme.lower().rstrip(":")
            if key in normalized_scheme:
                raise ValueError(
                    f"Duplicate scheme entry in per_scheme_preference: {key!r}"
                )
            normalized_scheme[key] = engine_id
        object.__setattr__(self, "per_scheme_preference", _freeze_mapping(normalized_scheme))

        normalized_input: dict[EngineInputType, str] = {}
        for input_type, engine_id in self.per_input_type_preference.items():
            if not isinstance(input_type, EngineInputType):
                raise ValueError(
                    "per_input_type_preference keys must be EngineInputType"
                )
            validate_engine_id(engine_id)
            if input_type in normalized_input:
                raise ValueError(
                    f"Duplicate input type in per_input_type_preference: "
                    f"{input_type.value!r}"
                )
            normalized_input[input_type] = engine_id
        object.__setattr__(
            self, "per_input_type_preference", _freeze_mapping(normalized_input)
        )

        normalized_settings: dict[str, Mapping[str, Any]] = {}
        for engine_id, settings in self.engine_settings.items():
            validate_engine_id(engine_id)
            if not isinstance(settings, Mapping):
                raise ValueError(
                    f"engine_settings[{engine_id!r}] must be a mapping"
                )
            if engine_id in normalized_settings:
                raise ValueError(
                    f"Duplicate engine id in engine_settings: {engine_id!r}"
                )
            normalized_settings[engine_id] = _freeze_mapping(settings)
        object.__setattr__(
            self, "engine_settings", _freeze_mapping(normalized_settings)
        )

        object.__setattr__(
            self, "disabled_engine_ids", tuple(self.disabled_engine_ids)
        )

        if not isinstance(self.schema_version, int) or self.schema_version < 1:
            raise ValueError("schema_version must be a positive int")

    def is_disabled(self, engine_id: str) -> bool:
        return engine_id in self.disabled_engine_ids

    def preferred_for_scheme(self, scheme: str) -> str | None:
        return self.per_scheme_preference.get(scheme.lower().rstrip(":"))

    def preferred_for_input_type(self, input_type: EngineInputType) -> str | None:
        return self.per_input_type_preference.get(input_type)

    def engine_settings_for(self, engine_id: str) -> Mapping[str, Any]:
        validate_engine_id(engine_id)
        return self.engine_settings.get(engine_id, MappingProxyType({}))

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable dict suitable for later JSON persistence.

        Mappings are converted to plain dicts and `EngineInputType` keys are
        serialized to their `.value`. Engine settings are included as-is —
        callers that persist this dict must redact secret keys themselves.
        """
        return {
            "schema_version": self.schema_version,
            "default_engine_id": self.default_engine_id,
            "auto_select_enabled": self.auto_select_enabled,
            "disabled_engine_ids": list(self.disabled_engine_ids),
            "per_scheme_preference": dict(self.per_scheme_preference),
            "per_input_type_preference": {
                input_type.value: engine_id
                for input_type, engine_id in self.per_input_type_preference.items()
            },
            "engine_settings": {
                engine_id: dict(settings)
                for engine_id, settings in self.engine_settings.items()
            },
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> EngineConfig:
        """Reverse of `to_dict`. Unknown keys are ignored for forward compat."""
        if not isinstance(payload, Mapping):
            raise ValueError("EngineConfig.from_dict requires a mapping payload")

        schema_version = int(payload.get("schema_version", SCHEMA_VERSION))
        if schema_version > SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported EngineConfig schema_version {schema_version}; "
                f"maximum supported is {SCHEMA_VERSION}"
            )

        per_input_raw = payload.get("per_input_type_preference") or {}
        per_input: dict[EngineInputType, str] = {}
        for raw_key, engine_id in per_input_raw.items():
            try:
                key = EngineInputType(raw_key)
            except ValueError as exc:
                raise ValueError(
                    f"Unknown input type in per_input_type_preference: "
                    f"{raw_key!r}"
                ) from exc
            per_input[key] = engine_id

        return cls(
            default_engine_id=payload.get("default_engine_id"),
            auto_select_enabled=bool(payload.get("auto_select_enabled", True)),
            disabled_engine_ids=tuple(payload.get("disabled_engine_ids", ())),
            per_scheme_preference=dict(payload.get("per_scheme_preference", {})),
            per_input_type_preference=per_input,
            engine_settings=dict(payload.get("engine_settings", {})),
            schema_version=schema_version,
        )

    def with_overrides(self, **overrides: Any) -> EngineConfig:
        """Helper for tests / callers that want a tweaked copy.

        Validates that override keys correspond to declared fields so typos
        do not silently pass through.
        """
        valid_names = {item.name for item in fields(self)}
        unknown = set(overrides) - valid_names
        if unknown:
            raise ValueError(f"Unknown EngineConfig fields: {sorted(unknown)}")
        return replace(self, **overrides)
