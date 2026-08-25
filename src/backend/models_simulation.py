"""Simulation tables — WS-0 owns the schema; WS-2 writes rows.

15-SHARED-CONTRACTS.md §3 maps ``demo_scenarios`` to this module. A scenario is a
named, replayable fixture: a seed spec, a clock offset, and the signals it is
expected to raise (the verification hook from doc 13). Same WS-0 conventions:
String not Enum, explicit ``clock.now()`` timestamps.
"""
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from src.backend.database import Base


class DemoScenario(Base):
    """A replayable demo fixture with its expected signals (§ doc 12 / doc 13)."""

    __tablename__ = "demo_scenarios"

    id = Column(Integer, primary_key=True, index=True)
    scenario_key = Column(String(40), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    seed_spec = Column(Text, nullable=True)              # JSON
    clock_offset_days = Column(Integer, default=0)
    expected_signals = Column(Text, nullable=True)       # JSON
    is_loaded = Column(Boolean, default=False, nullable=False)
    loaded_at = Column(DateTime, nullable=True)          # clock.now()
