"""Tests for metric snapshots persistence and historical retrieval (WS-17)."""
from src.backend.models_analytics import MetricSnapshot
from src.core import clock
from src.metrics.registry import compute_metric
from src.metrics.snapshots import get_snapshots, snapshot_all, snapshot_metric, take_snapshot


def test_take_snapshot_single(test_db):
    """Test snapshot creation for a single metric."""
    m = compute_metric(test_db, "M-14")
    snap = take_snapshot(test_db, m)

    assert snap.id is not None
    assert snap.metric_key == "M-14"
    assert snap.value == 0.0
    assert snap.tier == "T1"
    assert snap.data_disclosure == "synthetic"
    assert snap.computed_at is not None


def test_snapshot_all(test_db):
    """Test snapshot_all persists all 36 metrics."""
    snapshots = snapshot_all(test_db)
    assert len(snapshots) == 36

    count = test_db.query(MetricSnapshot).count()
    assert count == 36

    # Verify T3 metrics stored with null value
    t3_snaps = test_db.query(MetricSnapshot).filter(MetricSnapshot.tier == "T3").all()
    assert len(t3_snaps) == 8
    for s in t3_snaps:
        assert s.value is None


def test_get_snapshots_query(test_db):
    """Test historical snapshot querying with filters."""
    snapshot_all(test_db)

    m14_history = get_snapshots(test_db, metric_key="M-14")
    assert len(m14_history) == 1
    assert m14_history[0]["metric_key"] == "M-14"
    assert m14_history[0]["value"] == 0.0
    assert m14_history[0]["tier"] == "T1"
    assert "formula" in m14_history[0]


def test_snapshot_metric_helper(test_db):
    """Test snapshot_metric helper function."""
    snap = snapshot_metric(test_db, "M-1")
    assert snap.metric_key == "M-1"
    assert snap.id is not None
