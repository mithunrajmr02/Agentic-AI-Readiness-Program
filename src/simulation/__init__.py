"""WS-2 — the simulation and data harness.

This package builds the dataset every other workstream reasons over. It exists
alongside ``src/backend/seed_demo_data.py`` and never modifies it: that script
produces the *baseline* (4 suppliers, 5 products, 4 purchase orders, an opening
movement ledger), and this package layers ninety days of history, the operational
edge cases, and the four named demo scenarios on top of it.

The defect this package fixes
-----------------------------
``stock_movements.recorded_at`` carries ``server_default=func.now()``, which
SQLite evaluates at insert time. Any writer that omits ``recorded_at`` therefore
stamps *wall-clock now*, no matter what ``clock.now()`` says — which is how the
original thirteen movements ended up inside a single seven-hour window and made
every demand calculation in the system undefined. **Every movement written from
this package passes ``recorded_at`` explicitly**, derived from ``clock.now()``:

    recorded_at = clock.now() - timedelta(days=n)   # never the column default

Module map
----------
``backfill``   the ninety-day movement history: demand curves, the backward
               receipt schedule, and the sufficiency arithmetic that proves the
               history is dense enough to compute from.
``seeder``     everything the ninety days sit inside: users, supplier catalogue
               terms, the autonomy policy, and the two operational purchase
               orders (one overdue, one partially received).
``scenarios``  the four ``demo_scenarios`` rows from doc 13 — their seed specs,
               their clock offsets, and their ``expected_signals`` assertions —
               plus load and verify.
``reset``      returns the database to the baseline so a scenario load is
               genuinely idempotent rather than merely re-runnable.

Everything in this package takes an explicit ``db`` session. Nothing here opens
its own, because ``database.py`` rewrites relative SQLite URLs back to the real
``inventory.db`` and a harness that quietly wrote to the production database
during a test would be worse than no harness.

The names re-exported below never shadow a submodule name — hence
``backfill_history`` rather than ``backfill``, which would replace the module of
that name in this package's namespace and break ``from src.simulation import
backfill``.
"""
from src.simulation.backfill import (
    BACKFILL_DAYS,
    BASE_DEMAND,
    SIM_ACTOR,
    SIM_PREFIX,
    backfill_history,
    backfill_product,
    sale_event_stats,
    sufficiency_of,
)
from src.simulation.reset import reset_simulation
from src.simulation.scenarios import (
    SCENARIOS,
    ensure_scenarios,
    list_scenarios,
    load_scenario,
    verify_scenario,
)
from src.simulation.seeder import seed_dataset

__all__ = [
    "BACKFILL_DAYS",
    "BASE_DEMAND",
    "SCENARIOS",
    "SIM_ACTOR",
    "SIM_PREFIX",
    "backfill_history",
    "backfill_product",
    "ensure_scenarios",
    "list_scenarios",
    "load_scenario",
    "reset_simulation",
    "sale_event_stats",
    "seed_dataset",
    "sufficiency_of",
    "verify_scenario",
]
