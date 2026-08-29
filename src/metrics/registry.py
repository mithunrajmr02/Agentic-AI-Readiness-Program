"""Metrics registry and contracts (WS-17).

15-SHARED-CONTRACTS.md §14 / 10-IMPACT-METRICS.md / 12-DATA-AND-API-CHANGES.md §5.6.
Defines MetricValue dataclass, catalog of all 36 metrics (M-1 to M-36),
and unified computation interfaces (compute_all, gaps, compute_category).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Callable, Optional

from sqlalchemy.orm import Session

from src.core.vocab import DATA_DISCLOSURE, METRIC_TIERS


@dataclass(frozen=True)
class MetricValue:
    """The frozen metric value shape across all 36 metrics (doc 15 §14).

    Hard rule: every T3 metric ALWAYS returns value=None, with missing_input
    and formula populated. Any metric computation with insufficient data
    also returns value=None.
    """

    key: str                    # e.g. "M-14"
    label: str                  # e.g. "Fabricated numeric fields"
    value: Optional[float]      # None for every T3 metric. Always.
    tier: str                   # ∈ METRIC_TIERS ("T1", "T2", "T3")
    formula: str                # Human-readable exact formula
    missing_input: Optional[str]  # Required & non-null when tier == "T3"
    data_disclosure: str        # ∈ DATA_DISCLOSURE ("synthetic", "mixed", "real")
    window: str = "all_time"    # "all_time", "30d", "90d"
    scope: str = "global"       # "global", "category:grocery", "product:1"

    def __post_init__(self) -> None:
        if self.tier not in METRIC_TIERS:
            raise ValueError(f"Invalid metric tier '{self.tier}'. Must be one of {METRIC_TIERS}")
        if self.data_disclosure not in DATA_DISCLOSURE:
            raise ValueError(
                f"Invalid data_disclosure '{self.data_disclosure}'. Must be one of {DATA_DISCLOSURE}"
            )
        # CI Invariant #8 / Doc 15 §14: T3 metric must have value is None and missing_input populated
        if self.tier == "T3":
            if self.value is not None:
                raise ValueError(
                    f"Violation of CI invariant #8: T3 metric '{self.key}' must have value=None, got {self.value}"
                )
            if not self.missing_input:
                raise ValueError(
                    f"T3 metric '{self.key}' must define a non-empty missing_input"
                )

    def to_dict(self) -> dict[str, Any]:
        """Convert MetricValue to dictionary suitable for JSON serialization."""
        return asdict(self)


@dataclass(frozen=True)
class MetricDefinition:
    """Metadata and computer definition for a metric in the registry."""

    key: str
    label: str
    category: str               # "detection", "decision", "method", "position", "t3_gaps", "t2_live"
    tier: str                   # "T1", "T2", "T3"
    formula: str
    missing_input: Optional[str]
    data_disclosure: str
    computer: Optional[Callable[[Session, str, str], MetricValue]] = None


# Registry of metric definitions
_REGISTRY: dict[str, MetricDefinition] = {}


def register_metric(definition: MetricDefinition) -> MetricDefinition:
    """Register a metric definition in the global registry."""
    _REGISTRY[definition.key] = definition
    return definition


def get_metric_definition(key: str) -> Optional[MetricDefinition]:
    """Look up a metric definition by key."""
    return _REGISTRY.get(key)


def get_all_metric_definitions() -> list[MetricDefinition]:
    """Get all registered metric definitions sorted by key index."""
    def _sort_key(d: MetricDefinition) -> int:
        try:
            return int(d.key.split("-")[1])
        except (IndexError, ValueError):
            return 999

    return sorted(_REGISTRY.values(), key=_sort_key)


def compute_metric(
    db: Session,
    key: str,
    window: str = "all_time",
    scope: str = "global",
) -> MetricValue:
    """Compute a single metric by key."""
    defn = _REGISTRY.get(key)
    if defn is None:
        raise KeyError(f"Metric '{key}' is not registered.")
    if defn.computer is not None:
        return defn.computer(db, window, scope)
    # Default fallback using metadata
    return MetricValue(
        key=defn.key,
        label=defn.label,
        value=None,
        tier=defn.tier,
        formula=defn.formula,
        missing_input=defn.missing_input,
        data_disclosure=defn.data_disclosure,
        window=window,
        scope=scope,
    )


def compute_all(
    db: Session,
    window: str = "all_time",
    scope: str = "global",
) -> list[MetricValue]:
    """Compute all 36 metrics across all tiers (doc 15 §14)."""
    return [compute_metric(db, defn.key, window=window, scope=scope) for defn in get_all_metric_definitions()]


def gaps(
    db: Session,
    window: str = "all_time",
    scope: str = "global",
) -> list[MetricValue]:
    """Return all Tier 3 metrics for 'WHAT WE CANNOT MEASURE YET' (doc 15 §14)."""
    t3_defs = [d for d in get_all_metric_definitions() if d.tier == "T3"]
    return [compute_metric(db, defn.key, window=window, scope=scope) for defn in t3_defs]


def compute_category(
    db: Session,
    category: str,
    window: str = "all_time",
    scope: str = "global",
) -> list[MetricValue]:
    """Compute metrics for a specific category (detection, decision, method, position, t3_gaps, t2_live)."""
    cat_defs = [d for d in get_all_metric_definitions() if d.category == category]
    return [compute_metric(db, defn.key, window=window, scope=scope) for defn in cat_defs]
