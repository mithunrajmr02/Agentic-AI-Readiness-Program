"""Table registry — imports every WS-0 model so create_all() sees them all.

15-SHARED-CONTRACTS.md §3 assigns each new table to a module. SQLAlchemy only
knows about a table once its module is imported, so this file imports them all;
importing ``models_registry`` once registers the entire Steward schema on
``Base.metadata``.

``src/backend/main.py`` imports this module (WS-0's one sanctioned edit to a
shared file) before the lifespan handler calls ``Base.metadata.create_all``, so
the new tables are created at startup. Tests import it for the same effect.
"""
from src.core import ids  # noqa: F401 -- id_sequences (IdSequence)
from src.backend import models_analytics  # noqa: F401 -- signals, agent_runs, metric_snapshots
from src.backend import models_governance  # noqa: F401 -- decisions, approvals, autonomy_policies
from src.backend import models_sourcing  # noqa: F401 -- supplier_products
from src.backend import models_simulation  # noqa: F401 -- demo_scenarios
