"""The four demo scenarios: definitions, idempotent load, and verification.

Doc 13 §1 is what makes this file more than fixture bookkeeping: *"if seeding
scenario D1 and running the pipeline does not produce exactly the signals named in
``expected_signals``, the build is broken."* So the tests here check two separate
things — that the four definitions are internally honest (frozen vocabulary, the
positions each narrative depends on), and that ``verify_scenario`` reports the
truth when the signals do and do not arrive.
"""
import pytest

from src.core import vocab
from src.simulation import scenarios as sc


def test_there_are_exactly_four_scenarios():
    assert len(sc.SCENARIOS) == 4
    assert sc.SCENARIO_KEYS == (
        "D1_governed_order",
        "D2_root_cause",
        "D3_config_audit",
        "D4_refusal",
    )


@pytest.mark.parametrize("spec", sc.SCENARIOS, ids=sc.SCENARIO_KEYS)
def test_every_scenario_declares_expected_signals(spec):
    """A scenario without assertions is a demo script, and doc 13 §1 is explicit
    that these rows are the integration test."""
    assert spec["expected_signals"], spec["scenario_key"]
    for entry in spec["expected_signals"]:
        assert entry.get("sku") or entry.get("supplier_code"), entry


@pytest.mark.parametrize("spec", sc.SCENARIOS, ids=sc.SCENARIO_KEYS)
def test_every_expected_signal_uses_the_frozen_vocabulary(spec):
    """After translation. Doc 13 was written with ``warning``/``info``, which are
    not in ``vocab.SEVERITIES``, and §15 wins every conflict — so the stored rows
    must contain only frozen values."""
    for entry in spec["expected_signals"]:
        assert entry["signal_type"] in vocab.SIGNAL_TYPES, entry
        assert sc.normalise_severity(entry["severity"]) in vocab.SEVERITIES, entry


def test_the_severity_translation_is_exactly_the_documented_one():
    assert sc.normalise_severity("warning") == "high"
    assert sc.normalise_severity("info") == "low"
    for severity in vocab.SEVERITIES:
        assert sc.normalise_severity(severity) == severity


def test_all_four_scenarios_run_at_offset_zero():
    """Which is why loading one needs no DEMO_MODE. The projected breaches are
    computed forward from a dense history rather than manufactured by moving the
    calendar — the demo never has to explain why "today" is not today."""
    for spec in sc.SCENARIOS:
        assert spec["clock_offset_days"] == 0, spec["scenario_key"]


# --- the demo_scenarios rows ---------------------------------------------------


def test_ensure_scenarios_writes_four_rows(db):
    from src.backend.models_simulation import DemoScenario

    result = sc.ensure_scenarios(db)
    assert result["created"] == list(sc.SCENARIO_KEYS)
    assert db.query(DemoScenario).count() == 4


def test_ensure_scenarios_is_idempotent(db):
    sc.ensure_scenarios(db)
    second = sc.ensure_scenarios(db)
    assert second == {"created": [], "updated": [], "total": 4}


def test_ensure_scenarios_overwrites_a_stale_row(db):
    """This module is the source of truth. A row edited by hand in a developer's
    database must not outvote the file."""
    from src.backend.models_simulation import DemoScenario

    sc.ensure_scenarios(db)
    row = sc.get_scenario(db, "D1_governed_order")
    row.name = "edited by hand"
    row.expected_signals = "[]"
    db.commit()

    result = sc.ensure_scenarios(db)
    assert result["updated"] == ["D1_governed_order"]
    refreshed = db.query(DemoScenario).filter(DemoScenario.scenario_key == "D1_governed_order").one()
    assert refreshed.name == sc.SCENARIOS[0]["name"]
    assert refreshed.expected_signals != "[]"


def test_ensure_scenarios_leaves_runtime_state_alone(db, demo_mode):
    """``is_loaded``/``loaded_at`` describe what is currently in the database, not
    what the scenario is — refreshing a definition must not silently unload it."""
    sc.load_scenario(db, "D2_root_cause")
    sc.ensure_scenarios(db)
    assert sc.get_scenario(db, "D2_root_cause").is_loaded is True


def test_list_scenarios_returns_demo_order_with_decoded_specs(db):
    listed = sc.list_scenarios(db)
    assert [row["key"] for row in listed] == list(sc.SCENARIO_KEYS)
    for row in listed:
        assert isinstance(row["seed_spec"], dict)
        assert isinstance(row["expected_signals"], list)
        assert row["is_loaded"] is False
        assert row["loaded_at"] is None


def test_list_scenarios_seeds_the_rows_if_they_are_missing(db):
    """The read path is safe on a database that has never been seeded, so the
    presenter's first click cannot land on an empty list."""
    from src.backend.models_simulation import DemoScenario

    assert db.query(DemoScenario).count() == 0
    assert len(sc.list_scenarios(db)) == 4


# --- load ---------------------------------------------------------------------


def test_load_works_without_demo_mode(db, no_demo_mode):
    """Every scenario sits at offset 0, so loading one never calls
    ``clock.set_offset`` and never trips its DEMO_MODE guard. The HTTP surface
    still gates the endpoint; the function itself does not need to."""
    result = sc.load_scenario(db, "D1_governed_order")
    assert result["clock_offset_days"] == 0
    assert result["seeded"]["history"]["distinct_recorded_dates"] >= 90


def test_load_marks_exactly_one_scenario_loaded(db):
    from src.backend.models_simulation import DemoScenario

    sc.load_scenario(db, "D1_governed_order")
    sc.load_scenario(db, "D4_refusal")

    loaded = db.query(DemoScenario).filter(DemoScenario.is_loaded.is_(True)).all()
    assert [row.scenario_key for row in loaded] == ["D4_refusal"]
    assert loaded[0].loaded_at is not None
    assert sc.get_scenario(db, "D1_governed_order").loaded_at is None


def test_an_unknown_scenario_key_raises_key_error(db):
    with pytest.raises(KeyError):
        sc.load_scenario(db, "D9_does_not_exist")


def _snapshot(db):
    from sqlalchemy import func

    from src.backend.models import Product, StockLevel, StockMovement

    positions = {
        product.sku: db.query(StockLevel)
        .filter(StockLevel.product_id == product.id)
        .first()
        .quantity_on_hand
        for product in db.query(Product).all()
    }
    dates = sorted(
        {
            row[0].date().isoformat()
            for row in db.query(StockMovement.recorded_at).all()
            if row[0] is not None
        }
    )
    quantities = sorted(
        (row.reference_number, row.quantity, row.recorded_at.isoformat())
        for row in db.query(StockMovement).all()
    )
    total = int(db.query(func.coalesce(func.sum(StockMovement.quantity), 0)).scalar() or 0)
    return positions, dates, quantities, total


@pytest.mark.parametrize("key", sc.SCENARIO_KEYS)
def test_loading_a_scenario_twice_is_idempotent(db, key):
    """Doc 13 §4's "Idempotent", taken literally: not merely re-runnable, but
    producing the same numbers. Every movement — reference, quantity, and
    timestamp — is compared, so a second load cannot double the history or shift
    it by a day.
    """
    sc.load_scenario(db, key)
    first = _snapshot(db)
    sc.load_scenario(db, key)
    assert _snapshot(db) == first


def test_loading_a_different_scenario_replaces_the_previous_history(db):
    """The reset inside load is what makes this true. Without it, D4's zero-demand
    Colgate would inherit D1's ninety days and the refusal would collapse."""
    from src.simulation.backfill import sale_event_stats

    from src.backend.models import Product

    sc.load_scenario(db, "D1_governed_order")
    sc.load_scenario(db, "D4_refusal")

    headphones = db.query(Product).filter(Product.sku == "SKU-ELC-0001").first()
    # D4's demand map names only Colgate, so every other product falls back to its
    # own base rate rather than carrying D1's overrides.
    assert sale_event_stats(db, headphones.id)[0] > 0

    colgate = db.query(Product).filter(Product.sku == "SKU-PRC-0001").first()
    assert sale_event_stats(db, colgate.id) == (0, 0)


# --- the narrative preconditions each scenario depends on ---------------------


def test_d1_leaves_headphones_below_their_reorder_point(db):
    """4 against 10. If the position were anywhere else the scenario's opening
    signal would not fire and the whole demo has no first act."""
    from src.backend.models import Product, StockLevel

    sc.load_scenario(db, "D1_governed_order")
    product = db.query(Product).filter(Product.sku == "SKU-ELC-0001").first()
    stock = db.query(StockLevel).filter(StockLevel.product_id == product.id).first()
    assert stock.quantity_on_hand == 4
    assert product.reorder_point == 10


def test_d2_gives_rice_two_offers_with_different_lead_times(db):
    """The root cause is a supplier whose real lead time exceeds its quoted one,
    which needs two comparable offers to be visible at all."""
    from src.backend.models import Product
    from src.backend.models_sourcing import SupplierProduct

    sc.load_scenario(db, "D2_root_cause")
    rice = db.query(Product).filter(Product.sku == "SKU-GRO-0001").first()
    offers = db.query(SupplierProduct).filter(SupplierProduct.product_id == rice.id).all()
    assert len(offers) >= 2
    assert len({offer.lead_time_days for offer in offers}) >= 2


def test_d2_leaves_rice_above_its_reorder_point_but_days_from_stockout(db):
    """The scenario's sharpest point: the stored threshold is not breached, and
    the projection says the shelf is empty within the week anyway."""
    from src.backend.models import Product, StockLevel

    sc.load_scenario(db, "D2_root_cause")
    rice = db.query(Product).filter(Product.sku == "SKU-GRO-0001").first()
    stock = db.query(StockLevel).filter(StockLevel.product_id == rice.id).first()
    assert stock.quantity_on_hand == 20
    assert stock.quantity_on_hand > rice.reorder_point  # 20 > 15: nothing alerts
    assert stock.quantity_on_hand / 4.0 < 7  # and it is gone inside a week


def test_d3_does_not_correct_the_stored_reorder_points(db):
    """The audit's entire finding is that the stored values are wrong. A fixture
    that fixed them would delete the scenario."""
    from src.backend.models import Product

    before = {p.sku: p.reorder_point for p in db.query(Product).all()} or None
    sc.ensure_scenarios(db)
    sc.load_scenario(db, "D3_config_audit")
    after = {p.sku: p.reorder_point for p in db.query(Product).all()}
    assert after == {
        "SKU-GRO-0001": 15,
        "SKU-ELC-0001": 10,
        "SKU-ELC-0002": 5,
        "SKU-HHD-0001": 20,
        "SKU-PRC-0001": 30,
    }
    if before:
        assert after == before


def test_d3_audits_all_five_products(db):
    """Zero of five correct is the claim; five subjects are what make it one."""
    spec = sc.SCENARIOS[2]["seed_spec"]
    assert len(spec["audit_targets"]) == 5
    assert len(spec["demand"]) == 5


def test_d4_leaves_colgate_out_of_stock_with_no_history(db):
    """Both halves of the refusal: authority to act, and no evidence to act on."""
    from src.backend.models import Product, StockLevel
    from src.simulation.backfill import sale_event_stats, sufficiency_of

    sc.load_scenario(db, "D4_refusal")
    colgate = db.query(Product).filter(Product.sku == "SKU-PRC-0001").first()
    stock = db.query(StockLevel).filter(StockLevel.product_id == colgate.id).first()
    assert stock.quantity_on_hand == 0

    events, days = sale_event_stats(db, colgate.id)
    assert (events, days) == (0, 0)
    assert sufficiency_of(events, days) == "none"


def test_d4_runs_in_autonomous_mode(db):
    """Otherwise the refusal is indistinguishable from a governance interrupt —
    the agent must have had the authority it declined to use."""
    from src.backend.models_governance import AutonomyPolicy

    sc.load_scenario(db, "D4_refusal")
    policy = db.query(AutonomyPolicy).filter(AutonomyPolicy.scope_type == "global").one()
    assert policy.mode == "autonomous"
    assert policy.max_order_value == 50000


def test_d4_draft_order_would_sit_below_the_ceiling(db):
    """₹10,800 against a ₹50,000 ceiling: doc 13's reason for choosing Colgate
    over the television, so evidence is the only variable in the refusal."""
    from src.backend.models import Product

    sc.load_scenario(db, "D4_refusal")
    colgate = db.query(Product).filter(Product.sku == "SKU-PRC-0001").first()
    assert 120 * colgate.cost_price < 50000


# --- verify -------------------------------------------------------------------


@pytest.mark.parametrize("key", sc.SCENARIO_KEYS)
def test_verify_passes_when_every_expected_signal_is_present(db, key, raise_signals):
    """Handing ``expected_signals`` straight back in. WS-3 owns detection; this
    proves the assertion contract itself is satisfiable and internally consistent
    for all four scenarios."""
    sc.load_scenario(db, key)
    expected = sc.get_scenario(db, key)
    raise_signals(sc._decode(expected.expected_signals, []))

    result = sc.verify_scenario(db, key)
    assert result["passed"] is True
    assert result["missing"] == []
    assert result["severity_mismatch"] == []
    assert len(result["matched"]) == result["expected_count"]


def test_verify_fails_on_a_missing_signal(db, raise_signals):
    sc.load_scenario(db, "D4_refusal")
    expected = sc._decode(sc.get_scenario(db, "D4_refusal").expected_signals, [])
    raise_signals(expected[:1])  # the threshold breach, not the refusal

    result = sc.verify_scenario(db, "D4_refusal")
    assert result["passed"] is False
    assert [entry["signal_type"] for entry in result["missing"]] == ["data_insufficient"]
    assert len(result["matched"]) == 1


def test_verify_reports_a_wrong_severity_separately_from_a_missing_signal(db, raise_signals):
    """"We found it but called it low" is a different defect from "we did not find
    it", and a report that merged the two would send the reader to the wrong
    place."""
    sc.load_scenario(db, "D4_refusal")
    raise_signals(
        [
            {"signal_type": "threshold_breach", "sku": "SKU-PRC-0001", "severity": "low"},
            {"signal_type": "data_insufficient", "sku": "SKU-PRC-0001", "severity": "low"},
        ]
    )

    result = sc.verify_scenario(db, "D4_refusal")
    assert result["passed"] is False
    assert result["missing"] == []
    assert len(result["severity_mismatch"]) == 1
    mismatch = result["severity_mismatch"][0]
    assert mismatch["signal_type"] == "threshold_breach"
    assert mismatch["severity"] == "critical"
    assert mismatch["actual_severity"] == ["low"]


def test_verify_reports_extra_signals_without_failing(db, raise_signals):
    """A dense ninety-day history legitimately raises findings beyond the two a
    scenario is built to show. Concealing them would be worse than reporting
    them, and failing on them would make every scenario permanently red."""
    sc.load_scenario(db, "D4_refusal")
    expected = sc._decode(sc.get_scenario(db, "D4_refusal").expected_signals, [])
    raise_signals(
        expected + [{"signal_type": "po_overdue", "sku": "SKU-GRO-0001", "severity": "medium"}]
    )

    result = sc.verify_scenario(db, "D4_refusal")
    assert result["passed"] is True
    assert [entry["signal_type"] for entry in result["unexpected"]] == ["po_overdue"]


def test_verify_ignores_signals_that_are_no_longer_open(db, raise_signals):
    """A resolved or superseded signal is history, not a current finding."""
    sc.load_scenario(db, "D4_refusal")
    expected = sc._decode(sc.get_scenario(db, "D4_refusal").expected_signals, [])
    raise_signals(expected, status="resolved")

    result = sc.verify_scenario(db, "D4_refusal")
    assert result["passed"] is False
    assert result["signals_examined"] == 0
    assert len(result["missing"]) == len(expected)


def test_verify_matches_a_supplier_signal_by_code(db, raise_signals):
    """D2's ``supplier_drift`` names a supplier, not a product. The signals table
    stores an integer FK, so the code has to survive the round trip."""
    sc.load_scenario(db, "D2_root_cause")
    raise_signals(
        [{"signal_type": "supplier_drift", "supplier_code": "SUP-0005", "severity": "high"}]
    )

    result = sc.verify_scenario(db, "D2_root_cause")
    matched = [entry for entry in result["matched"] if entry["signal_type"] == "supplier_drift"]
    assert len(matched) == 1
    assert matched[0]["supplier_code"] == "SUP-0005"


def test_verify_on_an_empty_database_reports_everything_missing(db):
    """Not an error, and not a pass. Before WS-3 lands this is the honest answer,
    and it is the state CI starts from."""
    result = sc.verify_scenario(db, "D1_governed_order")
    assert result["passed"] is False
    assert result["signals_examined"] == 0
    assert len(result["missing"]) == result["expected_count"] == 3


def test_verify_is_idempotent_and_writes_nothing(db, raise_signals):
    """Doc 14's WS-2 test row: *"load twice, verify twice"*. Verification is a
    read: calling it twice must return the same report, and must not itself raise,
    resolve, or renumber a signal — a verifier that mutated the state it inspects
    could turn a failing build green on the second look.
    """
    from src.backend.models_analytics import Signal

    sc.load_scenario(db, "D4_refusal")
    expected = sc._decode(sc.get_scenario(db, "D4_refusal").expected_signals, [])
    raise_signals(expected[:1])

    signals_before = sorted(
        (row.signal_id, row.signal_type, row.severity, row.status)
        for row in db.query(Signal).all()
    )
    first = sc.verify_scenario(db, "D4_refusal")
    second = sc.verify_scenario(db, "D4_refusal")

    assert first == second
    assert first["passed"] is False
    assert (
        sorted(
            (row.signal_id, row.signal_type, row.severity, row.status)
            for row in db.query(Signal).all()
        )
        == signals_before
    )


def test_verify_on_an_unknown_key_raises_key_error(db):
    with pytest.raises(KeyError):
        sc.verify_scenario(db, "D9_does_not_exist")
