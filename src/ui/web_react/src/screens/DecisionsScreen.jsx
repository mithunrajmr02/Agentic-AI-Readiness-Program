import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Table, SeverityDot, Card, ProvenanceMark } from '../components';

/**
 * 07-UX-ARCHITECTURE.md §5.4 Decisions Timeline (/decisions)
 * WS-13 Skeleton / Audit log requested by Inventory Manual §4 Line 47
 * Shows autonomous, approved, rejected, and declined outcomes with equal prominence.
 */
export default function DecisionsScreen() {
  const navigate = useNavigate();
  const [filterOutcome, setFilterOutcome] = useState('all');

  const demoDecisions = [
    {
      decision_id: 'DEC-000125',
      time: '09:14',
      date: '25 Aug',
      action_type: 'raise_po',
      outcome: 'approved',
      subject: 'Ordered 240 × Bluetooth Speaker',
      amount: 68400,
      actor: 'user:1 (S. Iyer)',
      signal_id: 'SIG-000048',
      approval_id: 'APR-000012',
    },
    {
      decision_id: 'DEC-000124',
      time: '08:00',
      date: '25 Aug',
      action_type: 'no_action',
      outcome: 'declined',
      subject: 'No order — Laptop Stand (Insufficient history: 2 sales in 90d)',
      amount: null,
      actor: 'agent:replenishment',
      signal_id: 'SIG-000044',
      approval_id: null,
    },
    {
      decision_id: 'DEC-000123',
      time: '08:00',
      date: '25 Aug',
      action_type: 'raise_po',
      outcome: 'autonomous',
      subject: 'Ordered 120 × Wireless Mouse from Kumar Trading',
      amount: 14400,
      actor: 'agent:replenishment',
      signal_id: 'SIG-000045',
      approval_id: null,
    },
    {
      decision_id: 'DEC-000122',
      time: '14:22',
      date: '24 Aug',
      action_type: 'raise_po',
      outcome: 'rejected',
      subject: 'No order — Keyboard (Rejected by S. Iyer: "existing stock in back room")',
      amount: null,
      actor: 'user:1 (S. Iyer)',
      signal_id: 'SIG-000041',
      approval_id: 'APR-000011',
    },
  ];

  const filtered = demoDecisions.filter(d => filterOutcome === 'all' || d.outcome === filterOutcome);

  const columns = [
    {
      key: 'outcome',
      label: 'OUTCOME',
      width: '130px',
      render: (val) => {
        const sev = val === 'autonomous' || val === 'approved' ? 'good' : val === 'declined' ? 'warn' : 'critical';
        return <SeverityDot severity={sev} label={val} />;
      },
    },
    {
      key: 'decision_id',
      label: 'DECISION ID',
      width: '130px',
      render: (val) => <span className="t-mono" style={{ fontWeight: 600 }}>{val}</span>,
    },
    {
      key: 'subject',
      label: 'ACTION & SUBJECT',
      render: (val, row) => (
        <div>
          <div style={{ fontWeight: 600, color: 'var(--ink-1)' }}>{val}</div>
          <div style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-3)' }}>
            Actor: {row.actor} · {row.signal_id ? `Signal: ${row.signal_id}` : ''}
          </div>
        </div>
      ),
    },
    {
      key: 'amount',
      label: 'AMOUNT',
      width: '120px',
      align: 'right',
      render: (val) => val ? <span className="t-mono">₹{val.toLocaleString('en-IN')}</span> : '—',
    },
    {
      key: 'time',
      label: 'TIMESTAMP',
      width: '130px',
      render: (val, row) => <span className="t-meta">{row.date}, {val}</span>,
    },
  ];

  return (
    <div className="decisions-screen">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h1 className="t-display" style={{ margin: 0 }}>Decision Ledger</h1>
          <p className="t-meta" style={{ marginTop: '0.25rem' }}>
            Immutable governance audit trail of all autonomous, approved, rejected, and declined decisions.
          </p>
        </div>
        <select
          className="form-control"
          value={filterOutcome}
          onChange={(e) => setFilterOutcome(e.target.value)}
          style={{ width: '160px' }}
        >
          <option value="all">All Outcomes</option>
          <option value="autonomous">Autonomous Only</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
          <option value="declined">Declined (Refusals)</option>
        </select>
      </div>

      <Card>
        <Table
          columns={columns}
          rows={filtered}
          onRowClick={(row) => navigate(`/decisions/${row.decision_id}`)}
        />
      </Card>
    </div>
  );
}
