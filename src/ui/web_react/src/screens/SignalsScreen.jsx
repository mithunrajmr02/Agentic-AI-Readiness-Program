import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Table, SeverityDot, Card, ProvenanceMark } from '../components';

/**
 * 07-UX-ARCHITECTURE.md §5.2 Signals Screen (/signals)
 * WS-12 Skeleton / Triage table
 */
export default function SignalsScreen() {
  const navigate = useNavigate();
  const [filterType, setFilterType] = useState('all');

  const demoSignals = [
    {
      signal_id: 'SIG-000047',
      signal_type: 'config_drift',
      subject: 'USB-C Cable (SKU-1004)',
      severity: 'critical',
      detected_from: 'Reorder point 20; measured velocity implies 47',
      raised_at: '2026-08-25T08:00:00',
      status: 'open',
    },
    {
      signal_id: 'SIG-000046',
      signal_type: 'po_overdue',
      subject: 'PO-2026-0038 · Sharma Electronics',
      severity: 'warn',
      detected_from: 'Expected 23 Aug; 2 days overdue',
      raised_at: '2026-08-25T08:00:00',
      status: 'open',
    },
    {
      signal_id: 'SIG-000045',
      signal_type: 'projected_breach',
      subject: 'Wireless Mouse (SKU-1001)',
      severity: 'good',
      detected_from: 'Projected breach in 4 days resolved by order',
      raised_at: '2026-08-25T08:00:00',
      status: 'resolved',
      decision_id: 'DEC-000123',
    },
  ];

  const filtered = demoSignals.filter(s => filterType === 'all' || s.status === filterType);

  const columns = [
    {
      key: 'severity',
      label: 'SEVERITY',
      width: '120px',
      render: (val) => <SeverityDot severity={val} />,
    },
    {
      key: 'signal_id',
      label: 'ID',
      width: '120px',
      render: (val) => <span className="t-mono" style={{ fontWeight: 600 }}>{val}</span>,
    },
    {
      key: 'signal_type',
      label: 'TYPE',
      width: '160px',
      render: (val) => <span className="badge badge-primary">{val}</span>,
    },
    {
      key: 'subject',
      label: 'SUBJECT & CONTEXT',
      render: (val, row) => (
        <div>
          <div style={{ fontWeight: 600, color: 'var(--ink-1)' }}>{val}</div>
          <div style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-3)' }}>{row.detected_from}</div>
        </div>
      ),
    },
    {
      key: 'status',
      label: 'STATUS',
      width: '130px',
      render: (val, row) => (
        <div>
          <span className={`badge ${val === 'resolved' ? 'badge-success' : 'badge-warning'}`}>
            {val}
          </span>
          {row.decision_id && (
            <div style={{ fontSize: '11px', marginTop: '0.2rem' }}>
              <Link to={`/decisions/${row.decision_id}`}>└ {row.decision_id} ↗</Link>
            </div>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="signals-screen">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h1 className="t-display" style={{ margin: 0 }}>Signals Inbox</h1>
          <p className="t-meta" style={{ marginTop: '0.25rem' }}>
            Telemetry and exception detectors running against inventory movements.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className="btn btn-outline" style={{ fontSize: 'var(--t-meta-size)' }}>
            Scan Telemetry Now
          </button>
          <select
            className="form-control"
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            style={{ width: '140px' }}
          >
            <option value="all">All Signals</option>
            <option value="open">Open Only</option>
            <option value="critical">Critical</option>
            <option value="config_drift">Config Drift</option>
            <option value="projected_breach">Projected Breach</option>
            <option value="po_overdue">PO Overdue</option>
            <option value="data_insufficient">Data Insufficient</option>
          </select>
        </div>
      </div>

      <Card>
        {filtered.length > 0 ? (
          <Table
            columns={columns}
            rows={filtered}
            onRowClick={(row) => navigate(`/signals/${row.signal_id}`)}
          />
        ) : (
          <div className="EmptyState">No signals found matching current filter.</div>
        )}
      </Card>
    </div>
  );
}
