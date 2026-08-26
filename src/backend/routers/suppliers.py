"""Suppliers and Sourcing REST API router (WS-7).

15-SHARED-CONTRACTS.md §10, §12 / 12-DATA-AND-API-CHANGES.md §5.7.
Exposes supplier scorecard, catalog comparison, and lead-time drift endpoints.
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.backend.contracts import success_envelope
from src.backend.database import get_db
from src.backend.models import Product, Supplier
from src.backend.models_sourcing import SupplierProduct
from src.sourcing.drift import compute_supplier_drift, list_supplier_drifts
from src.sourcing.scorecard import scorecard
from src.sourcing.selection import select_supplier

router = APIRouter(prefix="/api/suppliers", tags=["suppliers"])


# --- Helpers -----------------------------------------------------------------

def format_supplier(s: Supplier) -> dict[str, Any]:
    """Format Supplier model into a standard JSON dictionary."""
    return {
        "id": s.id,
        "name": s.name,
        "supplier_code": s.supplier_code,
        "contact_email": s.contact_email,
        "payment_terms_days": s.payment_terms_days,
        "lead_time_days": s.lead_time_days,
        "is_active": s.is_active,
    }


# --- Endpoints ---------------------------------------------------------------

@router.get("", response_model=None)
def list_suppliers(
    active_only: bool = Query(False, description="Filter for active suppliers only"),
    db: Session = Depends(get_db),
):
    """List all registered suppliers with their configuration."""
    query = db.query(Supplier)
    if active_only:
        query = query.filter(Supplier.is_active.is_(True))
    suppliers = query.all()

    return success_envelope(
        data=[format_supplier(s) for s in suppliers],
        provenance={"suppliers": "retrieved"},
        data_disclosure="synthetic",
    )


@router.get("/drifts/all", response_model=None)
def get_all_supplier_drifts(
    tolerance_days: float = Query(0.0, description="Minimum days of drift to filter"),
    db: Session = Depends(get_db),
):
    """List all suppliers currently exhibiting delivery drift above tolerance."""
    drifts = list_supplier_drifts(db, tolerance_days=tolerance_days)
    return success_envelope(
        data=drifts,
        provenance={"drifts": "computed"},
        data_disclosure="synthetic",
    )


@router.get("/compare/{product_id}", response_model=None)
def compare_suppliers_for_product(
    product_id: int,
    quantity: int = Query(1, ge=1, description="Order quantity to evaluate MOQ and pricing"),
    db: Session = Depends(get_db),
):
    """Compare all available suppliers for a product with recommendations."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found",
        )

    # 1. Fetch catalog entries from supplier_products
    sp_entries = (
        db.query(SupplierProduct, Supplier)
        .join(Supplier, SupplierProduct.supplier_id == Supplier.id)
        .filter(SupplierProduct.product_id == product_id)
        .all()
    )

    catalog_comparison: list[dict[str, Any]] = []
    for sp, supp in sp_entries:
        catalog_comparison.append({
            "supplier_id": supp.id,
            "supplier_name": supp.name,
            "supplier_code": supp.supplier_code,
            "is_active": supp.is_active,
            "unit_price": sp.unit_price,
            "lead_time_days": sp.lead_time_days,
            "min_order_quantity": sp.min_order_quantity,
            "pack_size": sp.pack_size,
            "is_preferred": sp.is_preferred,
        })

    # If no supplier_products records, include default supplier
    if not catalog_comparison and product.supplier_id:
        supp = db.query(Supplier).filter(Supplier.id == product.supplier_id).first()
        if supp:
            catalog_comparison.append({
                "supplier_id": supp.id,
                "supplier_name": supp.name,
                "supplier_code": supp.supplier_code,
                "is_active": supp.is_active,
                "unit_price": product.cost_price,
                "lead_time_days": supp.lead_time_days,
                "min_order_quantity": 1,
                "pack_size": 1,
                "is_preferred": True,
            })

    # 2. Get recommendation if active supplier exists
    recommendation = None
    try:
        choice = select_supplier(db, product_id=product_id, quantity=quantity)
        recommendation = choice.to_dict()
    except Exception:
        recommendation = None

    return success_envelope(
        data={
            "product_id": product.id,
            "product_sku": product.sku,
            "product_name": product.name,
            "quantity": quantity,
            "comparison": catalog_comparison,
            "recommendation": recommendation,
        },
        provenance={"comparison": "retrieved", "recommendation": "computed"},
        data_disclosure="synthetic",
    )


@router.get("/{supplier_id}", response_model=None)
def get_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
):
    """Get single supplier details with performance summary."""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if supplier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with ID {supplier_id} not found",
        )

    sc = scorecard(db, supplier_id)
    supplier_data = format_supplier(supplier)
    supplier_data["scorecard"] = sc.to_dict()

    return success_envelope(
        data=supplier_data,
        provenance={"supplier": "retrieved", "scorecard": "computed"},
        data_disclosure="synthetic",
    )


@router.get("/{supplier_id}/scorecard", response_model=None)
def get_supplier_scorecard(
    supplier_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve measured reliability and lead-time scorecard for a supplier."""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if supplier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with ID {supplier_id} not found",
        )

    sc = scorecard(db, supplier_id)
    return success_envelope(
        data=sc.to_dict(),
        provenance={"scorecard": "computed"},
        data_disclosure="synthetic",
    )


@router.get("/{supplier_id}/products", response_model=None)
def get_supplier_products(
    supplier_id: int,
    db: Session = Depends(get_db),
):
    """List all products supplied by this supplier with pricing and lead times."""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if supplier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with ID {supplier_id} not found",
        )

    # 1. From supplier_products table
    sp_list = (
        db.query(SupplierProduct, Product)
        .join(Product, SupplierProduct.product_id == Product.id)
        .filter(SupplierProduct.supplier_id == supplier_id)
        .all()
    )

    products_data: list[dict[str, Any]] = []
    seen_product_ids = set()

    for sp, prod in sp_list:
        seen_product_ids.add(prod.id)
        products_data.append({
            "product_id": prod.id,
            "sku": prod.sku,
            "name": prod.name,
            "category": prod.category.value if hasattr(prod.category, "value") else str(prod.category),
            "unit_price": sp.unit_price,
            "lead_time_days": sp.lead_time_days,
            "min_order_quantity": sp.min_order_quantity,
            "pack_size": sp.pack_size,
            "is_preferred": sp.is_preferred,
        })

    # 2. From product.supplier_id default
    default_products = (
        db.query(Product)
        .filter(Product.supplier_id == supplier_id)
        .all()
    )
    for prod in default_products:
        if prod.id not in seen_product_ids:
            seen_product_ids.add(prod.id)
            products_data.append({
                "product_id": prod.id,
                "sku": prod.sku,
                "name": prod.name,
                "category": prod.category.value if hasattr(prod.category, "value") else str(prod.category),
                "unit_price": prod.cost_price,
                "lead_time_days": supplier.lead_time_days,
                "min_order_quantity": 1,
                "pack_size": 1,
                "is_preferred": True,
            })

    return success_envelope(
        data=products_data,
        provenance={"products": "retrieved"},
        data_disclosure="synthetic",
    )


@router.get("/{supplier_id}/drift", response_model=None)
def get_supplier_drift(
    supplier_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve detailed lead-time drift and PO evidence for a supplier."""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if supplier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with ID {supplier_id} not found",
        )

    drift_report = compute_supplier_drift(db, supplier_id)
    return success_envelope(
        data=drift_report,
        provenance={"drift": "computed"},
        data_disclosure="synthetic",
    )
