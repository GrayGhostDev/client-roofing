"""
iSwitch Roofs CRM - Business Logic Services
Version: 1.0.0

Service layer for business logic, algorithms, and integrations.

This package exposes select service singletons and classes at the package level
via lazy loading to avoid circular imports and heavy import costs.

Usage examples:
    from app.services import lead_scoring_engine
    from app.services import LeadScoringEngine

The actual implementations live in their respective modules under this package.
"""

from __future__ import annotations

import importlib
from typing import Any, Dict, Tuple

# Map exported names to (module_path, attribute_name)
_services_map: Dict[str, Tuple[str, str]] = {
    # Lead scoring exports
    "LeadScoringEngine": ("app.services.lead_scoring", "LeadScoringEngine"),
    "lead_scoring_engine": ("app.services.lead_scoring", "lead_scoring_engine"),

    # Common real-time/partnership exports (optional convenience)
    "realtime_service": ("app.services.realtime_service", "realtime_service"),
    "partnerships_service": ("app.services.partnerships_service", "partnerships_service"),
}

__all__ = list(_services_map.keys())


def __getattr__(name: str) -> Any:  # PEP 562 lazy attribute access
    """Lazily import and return the requested service attribute.

    This prevents import-time cycles and reduces import overhead.
    """
    if name in _services_map:
        module_path, attr_name = _services_map[name]
        module = importlib.import_module(module_path)
        try:
            return getattr(module, attr_name)
        except AttributeError as exc:
            raise AttributeError(f"Module '{module_path}' has no attribute '{attr_name}'") from exc
    raise AttributeError(f"module 'app.services' has no attribute '{name}'")


def __dir__() -> list[str]:
    """Advertise exported names for tooling/IDE support."""
    return sorted(list(globals().keys()) + __all__)
