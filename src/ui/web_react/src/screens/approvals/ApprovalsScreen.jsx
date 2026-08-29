import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { Table, SeverityDot, Card, EmptyState } from '../../components';
import { QUERY_KEYS } from '../../lib/query';
import { describeApiError } from '../../lib/api';

/**
 * 07-UX-ARCHITECTURE.md §5.3 & 15-SHARED-CONTRACTS.md §13 Approvals Queue Screen (/approvals)
 * Manager-only governance queue for proposals exceeding autonomy thresholds.
 */
export default function ApprovalsScreen() {
  const navigate = useNavigate();
  const [filterOutcome, setFilterOutcome] = useState('pending');

  // Fallback demo items for offline/demo reliability (13-DEMO-SCENARIOS.md §5)
  const fallbackApprovals = [
    {
      approval_id: 'APR-000012',
      decision_id: 'DEC-000125',
      subject: 'Order 240 × Bluetooth Speaker from Sharma Electronics',
      action_type: 'raise_po',
      value: 68400,
      reason: 'Above ₹50,000 threshold — §10 requires Store Manager approval',
      requested_at: '2026-08-25T07:00:00',
      outcome: null,
      sla_status: '2h 14m / 24h',
      sla_breached: false,
      severity: 'warn',
    },
  ];

  // Fetch approvals with React Query
  const { data: rawApprovals, isLoading, isError, error, refetch } = useQuery({
    queryKey: filterOutcome === 'pending'
      ? QUERY_KEYS.approvalsPending()
      : ['approvals', { outcome: filterOutcome }],
    queryFn: async () => {
      try {
        const params = {};
        if (filterOutcome === 'pending') {
          params.pending_only = true;
        } else if (filterOutcome !== 'all') {
          params.outcome = filterOutcome;
        }
        const res = await axios.get('/api/approvals', { params });
        return res.data?.data || [];
      } catch (err) {
        // In offline/demo mode, return fallback items matching the filter
        return fallbackApprovals.filter((a) => {
          if (filterOutcome === 'pending') return !a.outcome;
          if (filterOutcome === 'all') return true;
          return a.outcome === filterOutcome;
        });
      }
    },
    initialData: fallbackApprovals,
  });

  const approvalsList = rawApprovals && rawApprovals.length > 0 ? rawApprovals : [];

  // Map raw API records to table rows
  const rows = approvalsList.map((item) => {
    const dec = item.decision || {};
    const inputs = dec.inputs || {};
    const totalVal = inputs.total_value || (inputs.quantity && inputs.unit_price ? inputs.quantity * inputs.unit_price : item.value || 0);
    const prodName = inputs.product_name || dec.product_name || 'Item';
    const suppName = inputs.supplier_name || dec.supplier_name || 'Supplier';
    const qty = inputs.quantity || inputs.proposed_quantity || 240;

    let displaySubject = item.subject || `Order ${qty} × ${prodName} from ${suppName}`;
    let displayReason = item.reason || dec.policy_citation || 'Exceeds ₹50,000 autonomy threshold';

    const isPending = !item.outcome;
    const severity = item.severity || (item.sla_breached ? 'critical' : isPending ? 'warn' : 'good');

    return {
      approval_id: item.approval_id,
      decision_id: item.decision_id || dec.decision_id,
      subject: displaySubject,
      reason: displayReason,
      value: totalVal,
      requested_at: item.requested_at,
      outcome: item.outcome,
      sla_status: item.sla_status || (item.sla_breached ? 'SLA Breached' : '2h 14m / 24h'),
      severity,
      raw: item,
    };
  });

  const columns = [
    {
      key: 'severity',
      label: 'STATUS',
      width: '140px',
      render: (val, row) => (
        <SeverityDot
          severity={row.severity}
          label={row.outcome ? row.outcome.toUpperCase() : 'PENDING'}
        />
      ),
    },
    {
      key: 'approval_id',
      label: 'APPROVAL ID',
      width: '140px',
      render: (val) => <span className="t-mono" style={{ fontWeight: 600, color: 'var(--ink-1)' }}>{val}</span>,
    },
    {
      key: 'subject',
      label: 'PROPOSED ACTION & POLICY TRIGGER',
      render: (val, row) => (
        <div>
          <div style={{ fontWeight: 600, color: 'var(--ink-1)' }}>{val}</div>
          <div style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-3)', marginTop: '0.2rem' }}>
            {row.reason}
          </div>
        </div>
      ),
    },
    {
      key: 'value',
      label: 'AMOUNT',
      width: '130px',
      align: 'right',
      render: (val) => (
        <span className="t-mono" style={{ fontWeight: 700, color: 'var(--ink-1)' }}>
          {val ? `₹${val.toLocaleString('en-IN')}` : '—'}
        </span>
      ),
    },
    {
      key: 'sla_status',
      label: 'SLA TIMER',
      width: '140px',
      render: (val, row) => (
        <span
          className="t-meta"
          style={{
            color: row.raw?.sla_breached ? 'var(--critical)' : 'var(--warn)',
            fontWeight: 600,
          }}
        >
          {val}
        </span>
      ),
    },
    {
      key: 'actions',
      label: '',
      width: '110px',
      render: (_, row) => (
        <Link
          to={`/approvals/${row.approval_id}`}
          className="btn btn-primary"
          style={{ padding: '0.35rem 0.75rem', fontSize: 'var(--t-meta-size)' }}
          onClick={(e) => e.stopPropagation()}
        >
          Review →
        </Link>
      ),
    },
  ];

  return (
    <div className="approvals-screen">
      {/* Screen Title & Controls */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '1.5rem',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <h1 className="t-display" style={{ margin: 0 }}>Approval Queue</h1>
            <span
              className="badge badge-warning"
              style={{ fontSize: '0.85rem', padding: '0.25rem 0.55rem' }}
            >
              {rows.filter((r) => !r.outcome).length} Pending
            </span>
          </div>
          <p className="t-meta" style={{ marginTop: '0.35rem' }}>
            Store Manager governance queue for proposals exceeding autonomy thresholds (Inventory Manual §10).
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <select
            className="form-control"
            value={filterOutcome}
            onChange={(e) => setFilterOutcome(e.target.value)}
            style={{ width: '170px' }}
          >
            <option value="pending">Pending Only</option>
            <option value="all">All Approvals</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
            <option value="countered">Countered</option>
            <option value="expired">Expired</option>
          </select>

          <button
            type="button"
            className="btn btn-outline"
            onClick={() => refetch()}
            style={{ padding: '0.45rem 0.85rem', fontSize: 'var(--t-meta-size)' }}
            title="Refresh queue"
          >
            ⟳ Refresh
          </button>
        </div>
      </div>

      {/* Error state */}
      {isError && (
        <div
          style={{
            padding: '1rem',
            background: 'rgba(196, 38, 46, 0.08)',
            borderLeft: '4px solid var(--critical)',
            marginBottom: '1.25rem',
            borderRadius: 'var(--radius-sm)',
          }}
        >
          <div style={{ fontWeight: 600, color: 'var(--critical)', marginBottom: '0.25rem' }}>
            Failed to refresh approval queue
          </div>
          <div style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-2)' }}>
            {describeApiError(error)}
          </div>
        </div>
      )}

      {/* Main Table or Empty State */}
      <Card>
        {isLoading && !rows.length ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--ink-3)' }}>
            Loading approvals queue...
          </div>
        ) : rows.length === 0 ? (
          <EmptyState
            title="No Approvals Found"
            reason={
              filterOutcome === 'pending'
                ? 'The approval queue is clear. All current replenishment decisions are operating within autonomous policy thresholds.'
                : `No approval records match the filter '${filterOutcome}'.`
            }
            icon="✓"
          />
        ) : (
          <Table
            columns={columns}
            rows={rows}
            onRowClick={(row) => navigate(`/approvals/${row.approval_id}`)}
          />
        )}
      </Card>
    </div>
  );
}
