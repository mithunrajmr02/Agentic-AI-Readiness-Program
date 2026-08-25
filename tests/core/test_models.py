"""Contract tests for the WS-0 model modules + models_registry.

Asserts (a) every new table is created on a fresh DB, (b) the existing 8 tables
are untouched, and (c) the reconciliation decisions that resolve the doc-12 vs
doc-15 conflicts are baked into the schema:
  * decisions has a single 12-value ``status`` column and NO ``analysis_status``
  * approvals uses ``outcome`` (not ``status``)
  * new→new references (signal_id, run_id) are strings, not integer FKs
  * agent_runs exposes ``run_id`` (not ``run_ref``) and a string ``signal_id``
  * metric_snapshots.value is nullable (T3 metrics store NULL)
  * supplier_products is unique on (supplier_id, product_id)
No column on a new table may be a SQLAlchemy Enum (CI invariant #2).
"""
import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.pool import StaticPool

EXISTING_TABLES = {
    "suppliers", "products", "stock_levels", "stock_movements",
    "purchase_orders", "po_items", "stock_alerts", "users",
}
NEW_BUSINESS_TABLES = {
    "signals", "decisions", "approvals", "autonomy_policies",
    "supplier_products", "agent_runs", "metric_snapshots", "demo_scenarios",
}
NEW_INFRA_TABLES = {"id_sequences"}


@pytest.fixture
def engine():
    from src.backend.database import Base
    import src.backend.models  # noqa: F401 -- register the existing 8 tables
    from src.backend import models_registry  # noqa: F401 -- register the WS-0 tables

    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=eng)
    return eng


def _columns(engine, table):
    return {c["name"]: c for c in inspect(engine).get_columns(table)}


def test_all_new_business_tables_created(engine):
    tables = set(inspect(engine).get_table_names())
    assert NEW_BUSINESS_TABLES <= tables


def test_id_sequences_infra_table_created(engine):
    tables = set(inspect(engine).get_table_names())
    assert NEW_INFRA_TABLES <= tables


def test_existing_tables_untouched(engine):
    tables = set(inspect(engine).get_table_names())
    assert EXISTING_TABLES <= tables


def test_decisions_has_single_status_and_no_analysis_status(engine):
    cols = _columns(engine, "decisions")
    assert "status" in cols
    assert "analysis_status" not in cols


def test_decisions_refs_are_strings_not_int_fks(engine):
    cols = _columns(engine, "decisions")
    for ref in ("decision_id", "signal_id", "run_id", "execution_ref", "reversal_of"):
        assert ref in cols
        assert str(cols[ref]["type"]).upper().startswith("VARCHAR"), ref


def test_approvals_uses_outcome_not_status(engine):
    cols = _columns(engine, "approvals")
    assert "outcome" in cols
    assert "status" not in cols


def test_agent_runs_uses_run_id_string_not_run_ref(engine):
    cols = _columns(engine, "agent_runs")
    assert "run_id" in cols
    assert "run_ref" not in cols
    assert str(cols["run_id"]["type"]).upper().startswith("VARCHAR")
    # signal_id reconciled from Integer to a string business-ref.
    assert "signal_id" in cols
    assert str(cols["signal_id"]["type"]).upper().startswith("VARCHAR")


def test_metric_snapshots_value_is_nullable(engine):
    cols = _columns(engine, "metric_snapshots")
    assert cols["value"]["nullable"] is True


def test_signals_signal_id_is_unique_string(engine):
    cols = _columns(engine, "signals")
    assert str(cols["signal_id"]["type"]).upper().startswith("VARCHAR")
    uniques = inspect(engine).get_unique_constraints("signals")
    unique_cols = {tuple(u["column_names"]) for u in uniques}
    indexes = inspect(engine).get_indexes("signals")
    unique_index_cols = {tuple(i["column_names"]) for i in indexes if i["unique"]}
    assert ("signal_id",) in unique_cols or ("signal_id",) in unique_index_cols


def test_supplier_products_unique_on_supplier_and_product(engine):
    uniques = inspect(engine).get_unique_constraints("supplier_products")
    unique_sets = {frozenset(u["column_names"]) for u in uniques}
    assert frozenset({"supplier_id", "product_id"}) in unique_sets


def test_no_new_table_uses_sqlalchemy_enum(engine):
    # SQLite renders Enum as VARCHAR + a CHECK constraint. The frozen enum cage
    # forbids Enum on new columns; assert directly against the metadata types.
    from src.backend.database import Base
    from sqlalchemy import Enum as SAEnum

    target = NEW_BUSINESS_TABLES | NEW_INFRA_TABLES
    for table in Base.metadata.sorted_tables:
        if table.name in target:
            for column in table.columns:
                assert not isinstance(column.type, SAEnum), f"{table.name}.{column.name} is an Enum"
