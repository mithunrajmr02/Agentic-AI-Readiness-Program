"""Supplier selection logic and commercial trade-off evaluation (WS-7).

15-SHARED-CONTRACTS.md §10 / 14-PARALLEL-WORKSTREAMS.md §WS-7.
Selects optimal active supplier for a product and quantity, weighing price and lead time.
Enforces manual §6 line 74: Inactive suppliers are excluded by construction.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Optional

from sqlalchemy.orm import Session

from src.backend.models import Product, Supplier
from src.backend.models_sourcing import SupplierProduct
from src.core.errors import InsufficientData, StewardError


@dataclass(frozen=True)
class SupplierChoice:
    """Supplier selection recommendation contract (doc 15 §10)."""

    supplier_id: int
    unit_price: float
    lead_time_days: int
    is_cheapest: bool
    rejected_alternatives: list[dict]
    rationale: str

    def to_dict(self) -> dict:
        return asdict(self)


def select_supplier(
    db: Session,
    product_id: int,
    quantity: int = 1,
    prefer_supplier_id: Optional[int] = None,
) -> SupplierChoice:
    """Select the optimal active supplier for a given product and quantity.

    15-SHARED-CONTRACTS.md §10.
    1. Queries supplier_products for active suppliers offering the product.
    2. Fallback to product.supplier_id if no supplier_products records exist.
    3. Inactive suppliers are strictly excluded (§6 line 74).
    4. Evaluates pricing, lead time, and MOQ to produce SupplierChoice.
    """
    # 1. Query supplier_products joined with active suppliers
    sp_records = (
        db.query(SupplierProduct, Supplier)
        .join(Supplier, SupplierProduct.supplier_id == Supplier.id)
        .filter(
            SupplierProduct.product_id == product_id,
            Supplier.is_active.is_(True),
        )
        .all()
    )

    candidates: list[dict[str, Any]] = []

    for sp, supp in sp_records:
        candidates.append({
            "supplier_id": supp.id,
            "supplier_name": supp.name,
            "unit_price": float(sp.unit_price),
            "lead_time_days": int(sp.lead_time_days),
            "min_order_quantity": int(sp.min_order_quantity or 1),
            "is_preferred": bool(sp.is_preferred),
        })

    # 2. Fallback to Product default supplier if no supplier_products entries
    if not candidates:
        product = db.query(Product).filter(Product.id == product_id).first()
        if product is None:
            raise ValueError(f"Product with ID {product_id} not found")

        if product.supplier_id:
            supp = (
                db.query(Supplier)
                .filter(Supplier.id == product.supplier_id, Supplier.is_active.is_(True))
                .first()
            )
            if supp:
                candidates.append({
                    "supplier_id": supp.id,
                    "supplier_name": supp.name,
                    "unit_price": float(product.cost_price),
                    "lead_time_days": int(supp.lead_time_days or 7),
                    "min_order_quantity": 1,
                    "is_preferred": True,
                })

    # 3. If no active supplier exists, raise InsufficientData
    if not candidates:
        raise InsufficientData(
            what=f"supplier selection for product {product_id}",
            needed="at least 1 active supplier associated with the product",
            have="0 active suppliers",
        )

    # 4. Find the cheapest price among active candidates
    min_price = min(c["unit_price"] for c in candidates)

    # If caller specifically requested a preferred supplier that is active, check if present
    selected = None
    if prefer_supplier_id is not None:
        for c in candidates:
            if c["supplier_id"] == prefer_supplier_id:
                selected = c
                break

    # Otherwise sort: cheapest first, then shortest lead time, then preferred
    if selected is None:
        candidates_sorted = sorted(
            candidates,
            key=lambda c: (c["unit_price"], c["lead_time_days"], not c["is_preferred"]),
        )
        selected = candidates_sorted[0]

    is_cheapest = selected["unit_price"] == min_price

    # 5. Build rejected alternatives
    rejected_alternatives: list[dict[str, Any]] = []
    for c in candidates:
        if c["supplier_id"] == selected["supplier_id"]:
            continue
        reasons = []
        if c["unit_price"] > selected["unit_price"]:
            diff = c["unit_price"] - selected["unit_price"]
            reasons.append(f"Higher unit price (+₹{diff:.2f}/unit)")
        if c["lead_time_days"] > selected["lead_time_days"]:
            lt_diff = c["lead_time_days"] - selected["lead_time_days"]
            reasons.append(f"Longer lead time (+{lt_diff}d)")
        if not reasons:
            reasons.append("Alternative commercial option")

        rejected_alternatives.append({
            "supplier_id": c["supplier_id"],
            "supplier_name": c["supplier_name"],
            "unit_price": c["unit_price"],
            "lead_time_days": c["lead_time_days"],
            "min_order_quantity": c["min_order_quantity"],
            "reason": "; ".join(reasons),
        })

    # 6. Construct explicit rationale
    if is_cheapest:
        rationale = (
            f"Selected cheapest active supplier '{selected['supplier_name']}' "
            f"(₹{selected['unit_price']:.2f}/unit, {selected['lead_time_days']}d lead time)"
        )
        if rejected_alternatives:
            rationale += f"; rejected {len(rejected_alternatives)} higher-cost alternative(s)."
    else:
        rationale = (
            f"Selected active supplier '{selected['supplier_name']}' "
            f"(₹{selected['unit_price']:.2f}/unit, {selected['lead_time_days']}d lead time) "
            f"over cheapest active alternative (₹{min_price:.2f}/unit)."
        )

    return SupplierChoice(
        supplier_id=selected["supplier_id"],
        unit_price=selected["unit_price"],
        lead_time_days=selected["lead_time_days"],
        is_cheapest=is_cheapest,
        rejected_alternatives=rejected_alternatives,
        rationale=rationale,
    )
