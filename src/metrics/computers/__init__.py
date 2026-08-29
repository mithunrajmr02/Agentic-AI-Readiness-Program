"""Metric computers registration package (WS-17).

Registers all 36 metrics (M-1 to M-36) into the central registry.
"""
from src.metrics.computers.detection import register_detection_metrics
from src.metrics.computers.governance import register_governance_metrics
from src.metrics.computers.method import register_method_metrics
from src.metrics.computers.position import register_position_metrics
from src.metrics.computers.t2_live import register_t2_metrics
from src.metrics.computers.t3_gaps import register_t3_metrics


def initialize_all_metrics() -> None:
    """Register all 36 metrics into the global registry."""
    register_detection_metrics()
    register_governance_metrics()
    register_method_metrics()
    register_position_metrics()
    register_t3_metrics()
    register_t2_metrics()


# Run initialization on import
initialize_all_metrics()
