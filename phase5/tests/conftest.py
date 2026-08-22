import pytest
from unittest.mock import MagicMock, patch
from multi_agent.state import InventoryAnalysisState, initial_state


@pytest.fixture
def sample_product_data():
    return {
        "id": 1,
        "sku": "SKU-GRO-0001",
        "name": "Basmati Rice 5kg",
        "category": "grocery",
        "unit_price": 350.0,
        "cost_price": 280.0,
        "reorder_point": 20,
        "reorder_quantity": 100,
        "supplier_id": 1,
        "stock_level": {
            "quantity_on_hand": 12,
            "quantity_available": 12,
            "quantity_reserved": 0
        }
    }


@pytest.fixture
def state_with_data(sample_product_data):
    return {**initial_state(1), "product_data": sample_product_data}


@pytest.fixture
def state_after_forecast(state_with_data):
    return {
        **state_with_data,
        "demand_forecast": {
            "avg_daily_demand": 4.0,
            "demand_trend": "stable",
            "days_of_stock_remaining": 3,
            "stockout_risk": "high",
            "forecast_notes": "Will stock out in 3 days at current rate."
        }
    }


@pytest.fixture
def state_after_reorder(state_after_forecast):
    return {
        **state_after_forecast,
        "reorder_recommendation": {
            "reorder_required": True,
            "recommended_quantity": 100,
            "urgency": "within_3_days",
            "reason": "Stockout risk high."
        },
        "analysis_status": "reorder_required"
    }
