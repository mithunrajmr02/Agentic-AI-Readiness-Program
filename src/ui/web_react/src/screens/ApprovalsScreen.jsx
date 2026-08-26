import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Table, SeverityDot, Card } from '../components';

/**
 * 07-UX-ARCHITECTURE.md §5.3 Approvals Queue Screen (/approvals)
 * WS-13 Skeleton / Manager-only governance queue
 */
export default function ApprovalsScreen() {
  const navigate = useNavigate();

  const demoApprovals = [
    {
      approval_id: 'APR-000012',
      decision_id: 'DEC-000125',
      subject: 'PO-2026-0051 · Bluetooth Speaker',
      value: 68400,
      reason: 'Above ₹50,000 threshold — §10 requires Store Manager approval',
      requested_at: '2026-08-25T07:00:00',
      sla_status: '2h 14m / 24h',
      severity: 'critical',
    },
  ];

  const columns = [
    {
      key: 'severity',
      label: 'PRIORITY',
      width: '130px',
      render: (val) => <SeverityDot severity={val} label="Pending" />,
    },
    {
      key: 'approval_id',
      label: 'APPROVAL ID',
      width: '140px',
      render: (val) => <span className="t-mono" style={{ fontWeight: 600 }}>{val}</span>,
    },
    {
      key: 'subject',
      label: 'PROPOSED ACTION',
      render: (val, row) => (
        <div>
          <div style={{ fontWeight: 600, color: 'var(--ink-1)' }}>{val}</div>
          <div style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-3)' }}>{row.reason}</div>
        </div>
      ),
    },
    {
      key: 'value',
      label: 'AMOUNT',
      width: '130px',
      align: 'right',
      render: (val) => <span className="t-mono" style={{ fontWeight: 700 }}>₹{val.toLocaleString('en-IN')}</span>,
    },
    {
      key: 'sla_status',
      label: 'SLA CLOCK',
      width: '140px',
      render: (val) => <span className="t-meta" style={{ color: 'var(--warn)', fontWeight: 600 }}>{val}</span>,
    },
    {
      key: 'actions',
      label: '',
      width: '110px',
      render: (_, row) => (
        <Link to={`/approvals/${row.approval_id}`} className="btn btn-primary" style={{ padding: '0.35rem 0.75rem', fontSize: 'var(--t-meta-size)' }}>
          Review →
        </Link>
      ),
    },
  ];

  return (
    <div className="approvals-screen">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h1 className="t-display" style={{ margin: 0 }}>Approval Queue</h1>
          <p className="t-meta" style={{ marginTop: '0.25rem' }}>
            Store Manager governance queue for proposals exceeding autonomy thresholds.
          </p>
        </div>
      </div>

      <Card>
        <Table
          columns={columns}
          rows={demoApprovals}
          onRowClick={(row) => navigate(`/approvals/${row.approval_id}`)}
        />
      </Card>
    </div>
  );
}
