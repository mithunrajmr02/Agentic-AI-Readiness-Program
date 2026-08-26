"""The four named demo scenarios — their seed specs, clock offsets, and assertions.

Doc 13. A scenario is a row in ``demo_scenarios``, not a script: a ``seed_spec``
saying what to build, a ``clock_offset_days`` saying where the calendar sits, and
an ``expected_signals`` list saying what the pipeline must then raise. That last
field is what turns a demo into an integration test — doc 13 §1: *"if seeding
scenario D1 and running the pipeline does not produce exactly the signals named in
``expected_signals``, the build is broken."* The presenter is never the person who
discovers this.

The severity translation
------------------------
Doc 13's scenario tables were written with ``warning`` and ``info`` severities.
Neither is in the frozen vocabulary — ``vocab.SEVERITIES`` is
``("critical", "high", "medium", "low")`` — and 15-SHARED-CONTRACTS.md wins every
conflict, so the doc's labels are translated on the way in:

    critical → critical      warning → high      info → low

The mapping is applied here, once, and the stored rows contain only frozen values.
The exact ``(signal_type, sku, severity)`` triples WS-3's detectors must produce
are filed in ``integration-requests/WS-2.md`` so they are agreed rather than
discovered during integration.

Two schema notes
----------------
Doc 13 §4 sketches an ``is_active`` column, "exactly one active at a time". The
WS-0 model that actually exists carries ``is_loaded`` and ``loaded_at``; WS-0 owns
the schema and streams write rows, never columns, so ``is_loaded`` is what this
module sets — and ``load_scenario`` clears the others, preserving the intended
one-at-a-time semantics.

``signals`` references products by integer FK, not by SKU. Expected signals are
written with SKUs (stable, human-readable, and what the doc uses) and resolved to
ids at verify time, so the assertions survive a database rebuild that renumbers
rows.
"""
import json

import structlog

from src.backend.models import Product, Supplier
from src.backend.models_analytics import Signal
from src.backend.models_simulation import DemoScenario
from src.core import clock
from src.simulation.reset import reset_simulation
from src.simulation.seeder import seed_dataset

logger = structlog.get_logger()

#: Doc 13's severity labels → the frozen ``vocab.SEVERITIES`` values.
SEVERITY_TRANSLATION = {"warning": "high", "info": "low"}

#: Doc 13 §13: all four scenarios run at offset 0. The projected breaches are
#: computed forward from a dense ninety-day history rather than manufactured by
#: moving the calendar, so the demo never has to explain why "today" is not today.
#: ``POST /api/simulation/clock`` remains available for exploring the projection.
DEFAULT_OFFSET = 0

_D1 = {
    "scenario_key": "D1_governed_order",
    "name": "D1 — The Governed High-Value Order",
    "description": (
        "Headphones sit at 4 units against a reorder point of 10. The agent sizes a "
        "correct replenishment, finds it exceeds the assisted-mode value ceiling, and "
        "routes it to a human instead of acting. Proves the interrupt is durable and "
        "that governance is real rather than decorative."
    ),
    "clock_offset_days": DEFAULT_OFFSET,
    "seed_spec": {
        "backfill_days": 90,
        "demand": {
            "SKU-ELC-0001": 1.5,
            "SKU-GRO-0001": 4.0,
            "SKU-HHD-0001": 6.0,
            "SKU-ELC-0002": 0.2,
            "SKU-PRC-0001": 0.0,
        },
        "stock": {"SKU-ELC-0001": 4},
        "preserve_pos": ["PO-2026-0001", "PO-2026-0002"],
        "autonomy": {"mode": "assisted", "max_order_value": 50000},
    },
    "expected_signals": [
        # Headphones below their reorder point: the signal the demo opens on.
        {"signal_type": "threshold_breach", "sku": "SKU-ELC-0001", "severity": "warning"},
        # Rice's stored reorder point of 15 against a derived 44 (doc 13 §7.1).
        {"signal_type": "config_drift", "sku": "SKU-GRO-0001", "severity": "critical"},
        # Colgate has no history, and the system says so rather than guessing.
        {"signal_type": "data_insufficient", "sku": "SKU-PRC-0001", "severity": "info"},
    ],
}

_D2 = {
    "scenario_key": "D2_root_cause",
    "name": "D2 — The Root Cause",
    "description": (
        "Rice stocks out every cycle. The proximate reading is 'order more rice'; the "
        "actual causes are a reorder point derived from nothing and an incumbent "
        "supplier whose real lead time runs longer than its quoted one. Proves the "
        "system reasons past the symptom."
    ),
    "clock_offset_days": DEFAULT_OFFSET,
    "seed_spec": {
        "backfill_days": 90,
        "demand": {"SKU-GRO-0001": 4.0},
        "stock": {"SKU-GRO-0001": 20},
        "preserve_pos": ["PO-2026-0001"],
        # Doc 13 §6 names supplier ids 4 and 1. Supplier codes are the natural key
        # and survive a renumbering, and the seeder resolves either form.
        "supplier_products": [
            {
                "sku": "SKU-GRO-0001",
                "supplier_code": "SUP-0005",
                "unit_price": 600,
                "lead_time_days": 5,
                "is_preferred": True,
            },
            {
                "sku": "SKU-GRO-0001",
                "supplier_code": "SUP-0001",
                "unit_price": 625,
                "lead_time_days": 7,
            },
        ],
    },
    "expected_signals": [
        # 20 bags against ~4/day: above the (wrong) reorder point, out within days.
        {"signal_type": "projected_breach", "sku": "SKU-GRO-0001", "severity": "critical"},
        # Quoted 5 days, delivering closer to 9 — the second root cause.
        {"signal_type": "supplier_drift", "supplier_code": "SUP-0005", "severity": "warning"},
        # The first root cause, and the reason the alert never fired.
        {"signal_type": "config_drift", "sku": "SKU-GRO-0001", "severity": "critical"},
    ],
}

_D3 = {
    "scenario_key": "D3_config_audit",
    "name": "D3 — The Audit Nobody Ran",
    "description": (
        "Re-derives all five stored reorder points from the manual's formula. Zero of "
        "five are correct: two are dangerously low, two trap capital, and one cannot be "
        "assessed at all. Proves the system finds a class of problem that is invisible "
        "by construction — the alerting mechanism is calibrated by the thing being "
        "audited."
    ),
    "clock_offset_days": DEFAULT_OFFSET,
    "seed_spec": {
        "backfill_days": 90,
        "demand": {
            "SKU-GRO-0001": 4.0,
            "SKU-ELC-0001": 1.5,
            "SKU-ELC-0002": 0.2,
            "SKU-HHD-0001": 6.0,
            "SKU-PRC-0001": 0.0,
        },
        "preserve_pos": ["PO-2026-0001", "PO-2026-0002", "PO-2026-0003", "PO-2026-0004"],
        "autonomy": {"mode": "assisted", "max_order_value": 50000},
        # The audit's whole point is that the *stored* values are wrong. Nothing
        # here overrides products.reorder_point: the drift is the finding, and a
        # fixture that corrected it would delete the scenario.
        "audit_targets": [
            "SKU-GRO-0001",
            "SKU-HHD-0001",
            "SKU-ELC-0001",
            "SKU-ELC-0002",
            "SKU-PRC-0001",
        ],
    },
    "expected_signals": [
        # Doc 13 §7.1, in the doc's own order of severity.
        # Dangerously low — stocks out every cycle, and is not alerting.
        {"signal_type": "config_drift", "sku": "SKU-GRO-0001", "severity": "critical"},
        # Dangerously low — the worst absolute gap: (6 × 7) + (6 × 2) = 54 vs 20.
        {"signal_type": "config_drift", "sku": "SKU-HHD-0001", "severity": "critical"},
        # Over-cautious by 4 units × ₹41,000 = ₹164,000 idle. The rupee figure.
        {"signal_type": "config_drift", "sku": "SKU-ELC-0002", "severity": "warning"},
        # Over-cautious by 2 units × ₹22,000 = ₹44,000 idle.
        {"signal_type": "config_drift", "sku": "SKU-ELC-0001", "severity": "medium"},
        # The fifth row, and the audit's credibility: cannot derive.
        {"signal_type": "data_insufficient", "sku": "SKU-PRC-0001", "severity": "info"},
    ],
}

_D4 = {
    "scenario_key": "D4_refusal",
    "name": "D4 — The Refusal",
    "description": (
        "Colgate is out of stock and a 120-unit draft order worth ₹10,800 sits below the "
        "₹50,000 ceiling — the agent has the authority to place it. It declines anyway, "
        "because ninety days of history contain zero sales for this SKU. Colgate rather "
        "than the television because ₹10,800 isolates evidence as the only variable; a "
        "₹615,000 refusal would be indistinguishable from a threshold check."
    ),
    "clock_offset_days": DEFAULT_OFFSET,
    "seed_spec": {
        "backfill_days": 90,
        # Explicitly zero, and the reason the whole scenario works. Any nonzero
        # rate here makes the refusal unjustifiable.
        "demand": {"SKU-PRC-0001": 0.0},
        "stock": {"SKU-PRC-0001": 0},
        "preserve_pos": ["PO-2026-0004"],
        "autonomy": {"mode": "autonomous", "max_order_value": 50000},
    },
    "expected_signals": [
        # Out of stock: on hand 0 against a reorder point of 30.
        {"signal_type": "threshold_breach", "sku": "SKU-PRC-0001", "severity": "critical"},
        # And the refusal itself: no history, so no defensible order quantity.
        {"signal_type": "data_insufficient", "sku": "SKU-PRC-0001", "severity": "info"},
    ],
}

#: The four scenarios, in demo order.
SCENARIOS = (_D1, _D2, _D3, _D4)
SCENARIO_KEYS = tuple(spec["scenario_key"] for spec in SCENARIOS)


def normalise_severity(severity: str) -> str:
    """Translate doc 13's severity labels into the frozen vocabulary."""
    return SEVERITY_TRANSLATION.get(severity, severity)


def _normalise_expected(expected: list[dict]) -> list[dict]:
    return [dict(entry, severity=normalise_severity(entry["severity"])) for entry in expected]


def ensure_scenarios(db) -> dict:
    """Insert or refresh the four ``demo_scenarios`` rows. Idempotent on key.

    Definitions live in this module, so an existing row is *updated* rather than
    skipped: the file is the source of truth and a stale row in a developer's
    database must never outvote it. ``is_loaded`` and ``loaded_at`` are runtime
    state and are left alone.
    """
    created, updated = [], []
    for spec in SCENARIOS:
        seed_spec = json.dumps(spec["seed_spec"], sort_keys=True)
        expected = json.dumps(_normalise_expected(spec["expected_signals"]), sort_keys=True)

        row = (
            db.query(DemoScenario)
            .filter(DemoScenario.scenario_key == spec["scenario_key"])
            .first()
        )
        if row is None:
            db.add(
                DemoScenario(
                    scenario_key=spec["scenario_key"],
                    name=spec["name"],
                    description=spec["description"],
                    seed_spec=seed_spec,
                    clock_offset_days=spec["clock_offset_days"],
                    expected_signals=expected,
                    is_loaded=False,
                    loaded_at=None,
                )
            )
            created.append(spec["scenario_key"])
            continue

        if (
            row.name != spec["name"]
            or row.description != spec["description"]
            or row.seed_spec != seed_spec
            or row.clock_offset_days != spec["clock_offset_days"]
            or row.expected_signals != expected
        ):
            row.name = spec["name"]
            row.description = spec["description"]
            row.seed_spec = seed_spec
            row.clock_offset_days = spec["clock_offset_days"]
            row.expected_signals = expected
            updated.append(spec["scenario_key"])

    db.commit()
    return {"created": created, "updated": updated, "total": len(SCENARIOS)}


def _decode(value, fallback):
    if not value:
        return fallback
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return fallback


def get_scenario(db, key: str) -> DemoScenario | None:
    return db.query(DemoScenario).filter(DemoScenario.scenario_key == key).first()


def list_scenarios(db) -> list[dict]:
    """Every scenario, in demo order, with its spec and assertions decoded."""
    ensure_scenarios(db)
    order = {key: index for index, key in enumerate(SCENARIO_KEYS)}
    rows = db.query(DemoScenario).all()
    rows.sort(key=lambda row: (order.get(row.scenario_key, len(order)), row.scenario_key))
    return [
        {
            "key": row.scenario_key,
            "name": row.name,
            "description": row.description,
            "clock_offset_days": row.clock_offset_days or 0,
            "seed_spec": _decode(row.seed_spec, {}),
            "expected_signals": _decode(row.expected_signals, []),
            "is_loaded": bool(row.is_loaded),
            "loaded_at": row.loaded_at.isoformat() if row.loaded_at else None,
        }
        for row in rows
    ]


def load_scenario(db, key: str) -> dict:
    """Reset → seed → set the clock offset. Doc 13 §4. Idempotent.

    Loading the same scenario twice produces the same dataset, because the reset
    removes the previous load's history before the new one is written relative to
    the current ``clock.now()``.

    Raises ``KeyError`` for an unknown key. ``RuntimeError`` propagates from
    ``clock.set_offset`` if a nonzero offset is requested without DEMO_MODE — the
    caller must not be able to move the calendar in a real deployment.
    """
    ensure_scenarios(db)
    scenario = get_scenario(db, key)
    if scenario is None:
        raise KeyError(key)

    spec = _decode(scenario.seed_spec, {})
    offset = int(scenario.clock_offset_days or 0)

    reset_result = reset_simulation(db, reset_clock=True)

    # The offset is applied *before* seeding, so every ``recorded_at`` the backfill
    # writes is relative to the scenario's own calendar rather than to real now.
    # Ordering this the other way round would put the history ninety days behind
    # the wrong day, which is the same class of bug as omitting the timestamp.
    if offset:
        clock.set_offset(offset)

    seeded = seed_dataset(
        db,
        demand=spec.get("demand"),
        stock=spec.get("stock"),
        backfill_days=int(spec.get("backfill_days", 90)),
        autonomy=spec.get("autonomy"),
        supplier_products=spec.get("supplier_products"),
    )

    # ``is_loaded`` carries doc 13 §4's "exactly one active at a time".
    db.query(DemoScenario).filter(DemoScenario.scenario_key != key).update(
        {"is_loaded": False, "loaded_at": None}, synchronize_session=False
    )
    scenario.is_loaded = True
    scenario.loaded_at = clock.now()
    db.commit()

    logger.info(
        "simulation_scenario_loaded",
        poc_id="POC-07",
        scenario=key,
        clock_offset_days=offset,
        movements=seeded["history"]["movements_written"],
        distinct_dates=seeded["history"]["distinct_recorded_dates"],
    )
    return {
        "key": key,
        "name": scenario.name,
        "clock_offset_days": clock.offset_days(),
        "reset": reset_result,
        "seeded": seeded,
        "expected_signals": _decode(scenario.expected_signals, []),
    }


def _signal_identity(db, signal: Signal) -> tuple[str, str | None, str | None, str]:
    product_sku = None
    if signal.product_id:
        product = db.query(Product).filter(Product.id == signal.product_id).first()
        product_sku = product.sku if product else None
    supplier_code = None
    if signal.supplier_id:
        supplier = db.query(Supplier).filter(Supplier.id == signal.supplier_id).first()
        supplier_code = supplier.supplier_code if supplier else None
    return (signal.signal_type, product_sku, supplier_code, signal.severity)


def _expected_identity(db, entry: dict) -> tuple[str, str | None, str | None, str]:
    supplier_code = entry.get("supplier_code")
    if supplier_code is None and entry.get("supplier_id") is not None:
        supplier = db.query(Supplier).filter(Supplier.id == entry["supplier_id"]).first()
        supplier_code = supplier.supplier_code if supplier else None
    return (
        entry["signal_type"],
        entry.get("sku"),
        supplier_code,
        normalise_severity(entry["severity"]),
    )


def verify_scenario(db, key: str) -> dict:
    """Compare the signals actually raised against ``expected_signals``.

    Doc 13 §4: *"Returns pass/fail"*, and it is what CI calls instead of a human
    inspecting a screen.

    The comparison is a **subset** check — ``passed`` is true when nothing expected
    is missing. Extra signals are legitimate (a dense ninety-day history raises
    findings beyond the three a scenario is built to demonstrate), so they are
    reported under ``unexpected`` rather than failing the run: a verification that
    concealed them would be worse than one that failed on them.

    A signal of the right type on the right subject but at the wrong severity is
    reported separately as a ``severity_mismatch`` and still fails, because "we
    found it but called it low" is a different defect from "we did not find it" and
    a report that merged the two would send the reader to the wrong place.
    """
    ensure_scenarios(db)
    scenario = get_scenario(db, key)
    if scenario is None:
        raise KeyError(key)

    expected = _decode(scenario.expected_signals, [])
    actual_signals = db.query(Signal).filter(Signal.status == "open").all()
    actual = [_signal_identity(db, signal) for signal in actual_signals]

    # Severity-blind index, so a right-signal/wrong-severity case can be named.
    by_subject: dict[tuple[str, str | None, str | None], set[str]] = {}
    for signal_type, sku, supplier_code, severity in actual:
        by_subject.setdefault((signal_type, sku, supplier_code), set()).add(severity)

    matched, missing, mismatched = [], [], []
    for entry in expected:
        signal_type, sku, supplier_code, severity = _expected_identity(db, entry)
        found = by_subject.get((signal_type, sku, supplier_code))
        record = {
            "signal_type": signal_type,
            "sku": sku,
            "supplier_code": supplier_code,
            "severity": severity,
        }
        if found is None:
            missing.append(record)
        elif severity in found:
            matched.append(record)
        else:
            mismatched.append(dict(record, actual_severity=sorted(found)))

    expected_subjects = {
        _expected_identity(db, entry)[:3] for entry in expected
    }
    unexpected = [
        {
            "signal_type": signal_type,
            "sku": sku,
            "supplier_code": supplier_code,
            "severity": severity,
        }
        for signal_type, sku, supplier_code, severity in actual
        if (signal_type, sku, supplier_code) not in expected_subjects
    ]

    passed = not missing and not mismatched
    result = {
        "key": key,
        "passed": passed,
        "expected_count": len(expected),
        "matched": matched,
        "missing": missing,
        "severity_mismatch": mismatched,
        "unexpected": unexpected,
        "signals_examined": len(actual),
        "is_loaded": bool(scenario.is_loaded),
    }
    logger.info(
        "simulation_scenario_verified",
        poc_id="POC-07",
        scenario=key,
        passed=passed,
        matched=len(matched),
        missing=len(missing),
        severity_mismatch=len(mismatched),
    )
    return result
