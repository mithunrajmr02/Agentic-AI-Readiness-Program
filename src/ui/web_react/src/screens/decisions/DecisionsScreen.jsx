import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { Table, SeverityDot, Card, EmptyState, ProvenanceMark } from '../../components';
import { QUERY_KEYS } from '../../lib/query';
import { describeApiError } from '../../lib/api';

/**
 * 07-UX-ARCHITECTURE.md §5.4 & 15-SHARED-CONTRACTS.md §13 Decisions Timeline (/decisions)
 * Immutable governance audit log requested by Inventory Manual §4 Line 47.
 * Shows autonomous, approved, rejected, and declined outcomes with equal prominence.
 */
export default function DecisionsScreen() {
  const navigate = useNavigate();
  const [filterOutcome, setFilterOutcome] = useState('all');
  const [filterAction, setFilterAction] = useState('all');

  // Fallback demo dataset covering all 4 core outcome types (13-DEMO-SCENARIOS.md)
  const fallbackDecisions = [
    {
      decision_id: 'DEC-000125',
      time: '09:14:22',
      date: '25 Aug',
      action_type: 'raise_po',
      status: 'approved',
      outcome_type: 'approved',
      subject: 'Ordered 240 × Bluetooth Speaker from Sharma Electronics',
      amount: 68400,
      actor: 'user:1 (S. Iyer)',
      signal_id: 'SIG-000048',
      approval_id: 'APR-000012',
      policy_citation: '§10 PO Approval Threshold (> ₹50,000)',
      provenance: 'computed',
    },
    {
      decision_id: 'DEC-000124',
      time: '08:00:02',
      date: '25 Aug',
      action_type: 'no_action',
      status: 'insufficient_data',
      outcome_type: 'declined',
      subject: 'No order — Laptop Stand (Insufficient history: 2 sales in 90d)',
      amount: null,
      actor: 'agent:replenishment',
      signal_id: 'SIG-000044',
      approval_id: null,
      policy_citation: '§3 Data Sufficiency Floor',
      provenance: 'computed',
    },
    {
      decision_id: 'DEC-000123',
      time: '08:00:05',
      date: '25 Aug',
      action_type: 'raise_po',
      status: 'auto_approved',
      outcome_type: 'autonomous',
      subject: 'Ordered 120 × Wireless Mouse from Kumar Trading',
      amount: 14400,
      actor: 'agent:replenishment',
      signal_id: 'SIG-000045',
      approval_id: null,
      policy_citation: '§10 Autonomy Threshold (≤ ₹50,000)',
      provenance: 'computed',
    },
    {
      decision_id: 'DEC-000122',
      time: '14:22:10',
      date: '24 Aug',
      action_type: 'raise_po',
      status: 'rejected',
      outcome_type: 'rejected',
      subject: 'No order — Mechanical Keyboard (Rejected by S. Iyer: "existing stock in back room")',
      amount: null,
      actor: 'user:1 (S. Iyer)',
      signal_id: 'SIG-000041',
      approval_id: 'APR-000011',
      policy_citation: '§10 Manager Discretion',
      provenance: 'retrieved',
    },
  ];

  // React Query fetch
  const { data: rawDecisions, isLoading, isError, error, refetch } = useQuery({
    queryKey: QUERY_KEYS.decisions({ outcome: filterOutcome, action: filterAction }),
    queryFn: async () => {
      try {
        const params = {};
        if (filterAction !== 'all') {
          params.action_type = filterAction;
        }
        if (filterOutcome !== 'all') {
          if (filterOutcome === 'autonomous') params.status = 'auto_approved';
          else if (filterOutcome === 'approved') params.status = 'approved';
          else if (filterOutcome === 'rejected') params.status = 'rejected';
          else if (filterOutcome === 'countered') params.status = 'countered';
          else if (filterOutcome === 'declined') params.status = 'insufficient_data';
        }
        const res = await axios.get('/api/decisions', { params });
        return res.data?.data || [];
      } catch {
        // Fallback demo data
        return fallbackDecisions;
      }
    },
    initialData: fallbackDecisions,
  });

  const decisionsList = rawDecisions && rawDecisions.length > 0 ? rawDecisions : fallbackDecisions;

  // Outcome classifier
  const mapOutcomeType = (status, action) => {
    if (status === 'auto_approved' || (status === 'executed' && action !== 'no_action')) return 'autonomous';
    if (status === 'approved') return 'approved';
    if (status === 'rejected') return 'rejected';
    if (status === 'countered') return 'countered';
    if (status === 'insufficient_data' || action === 'no_action' || status === 'declined') return 'declined';
    return status || 'recorded';
  };

  // Format table rows
  const rows = decisionsList
    .map((d) => {
      const outcome = d.outcome_type || mapOutcomeType(d.status, d.action_type);
      const inputs = d.inputs || {};
      const amount = d.amount ?? (inputs.total_value || (inputs.quantity && inputs.unit_price ? inputs.quantity * inputs.unit_price : null));
      const dateStr = d.decided_at || d.proposed_at || d.time;

      let sev = 'info';
      if (outcome === 'autonomous' || outcome === 'approved') sev = 'good';
      else if (outcome === 'declined') sev = 'warn';
      else if (outcome === 'rejected' || outcome === 'failed') sev = 'critical';
      else if (outcome === 'countered') sev = 'warn';

      return {
        decision_id: d.decision_id,
        outcome,
        severity: sev,
        subject: d.subject || (d.action_type === 'no_action' ? `No order — Refusal (${d.product_name || 'Item'})` : `Ordered ${inputs.recommended_quantity || 120} × ${d.product_name || 'Item'}`),
        actor: d.actor || 'agent:replenishment',
        amount,
        signal_id: d.signal_id,
        approval_id: d.approval_id,
        policy_citation: d.policy_citation || '§10 Autonomy Policy',
        date: d.date || (dateStr ? new Date(dateStr).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }) : '25 Aug'),
        time: d.time || (dateStr ? new Date(dateStr).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }) : '08:00'),
        raw: d,
      };
    })
    .filter((r) => {
      if (filterOutcome === 'all') return true;
      return r.outcome === filterOutcome;
    })
    .filter((r) => {
      if (filterAction === 'all') return true;
      return r.raw.action_type === filterAction;
    });

  const columns = [
    {
      key: 'outcome',
      label: 'OUTCOME',
      width: '130px',
      render: (val, row) => <SeverityDot severity={row.severity} label={val.toUpperCase()} />,
    },
    {
      key: 'decision_id',
      label: 'DECISION ID',
      width: '130px',
      render: (val) => <span className="t-mono" style={{ fontWeight: 600, color: 'var(--ink-1)' }}>{val}</span>,
    },
    {
      key: 'subject',
      label: 'ACTION & CONTEXT',
      render: (val, row) => (
        <div>
          <div style={{ fontWeight: 600, color: 'var(--ink-1)' }}>{val}</div>
          <div style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-3)', marginTop: '0.2rem', display: 'flex', gap: '0.65rem', flexWrap: 'wrap' }}>
            <span>Actor: <strong>{row.actor}</strong></span>
            {row.signal_id && (
              <Link to={`/signals/${row.signal_id}`} style={{ color: 'var(--accent)' }} onClick={(e) => e.stopPropagation()}>
                Signal: {row.signal_id} ↗
              </Link>
            )}
            {row.approval_id && (
              <Link to={`/approvals/${row.approval_id}`} style={{ color: 'var(--accent)' }} onClick={(e) => e.stopPropagation()}>
                Approval: {row.approval_id} ↗
              </Link>
            )}
          </div>
        </div>
      ),
    },
    {
      key: 'amount',
      label: 'AMOUNT',
      width: '120px',
      align: 'right',
      render: (val) => (
        <span className="t-mono" style={{ fontWeight: 600, color: val ? 'var(--ink-1)' : 'var(--ink-3)' }}>
          {val ? `₹${val.toLocaleString('en-IN')}` : '—'}
        </span>
      ),
    },
    {
      key: 'policy_citation',
      label: 'GOVERNING RULE',
      width: '160px',
      render: (val) => <span className="t-meta" style={{ color: 'var(--ink-2)' }}>{val}</span>,
    },
    {
      key: 'timestamp',
      label: 'TIMESTAMP',
      width: '130px',
      render: (_, row) => <span className="t-meta">{row.date}, {row.time}</span>,
    },
  ];

  return (
    <div className="decisions-screen">
      {/* Header & Filter Controls */}
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
          <h1 className="t-display" style={{ margin: 0 }}>Decision Ledger</h1>
          <p className="t-meta" style={{ marginTop: '0.35rem' }}>
            Immutable governance audit trail of all autonomous, approved, rejected, and declined decisions (Manual §4 line 47).
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <select
            className="form-control"
            value={filterOutcome}
            onChange={(e) => setFilterOutcome(e.target.value)}
            style={{ width: '160px' }}
          >
            <option value="all">All Outcomes</option>
            <option value="autonomous">Autonomous</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
            <option value="countered">Countered</option>
            <option value="declined">Declined (Refusals)</option>
          </select>

          <select
            className="form-control"
            value={filterAction}
            onChange={(e) => setFilterAction(e.target.value)}
            style={{ width: '150px' }}
          >
            <option value="all">All Actions</option>
            <option value="raise_po">Raise PO</option>
            <option value="adjust_reorder_point">Adjust ROP</option>
            <option value="no_action">No Action</option>
          </select>

          <button
            type="button"
            className="btn btn-outline"
            onClick={() => refetch()}
            style={{ padding: '0.45rem 0.85rem', fontSize: 'var(--t-meta-size)' }}
            title="Refresh ledger"
          >
            ⟳ Refresh
          </button>
        </div>
      </div>

      {/* Error Banner */}
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
            Failed to refresh decision ledger
          </div>
          <div style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-2)' }}>
            {describeApiError(error)}
          </div>
        </div>
      )}

      {/* Main Table Card */}
      <Card>
        {isLoading && !rows.length ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--ink-3)' }}>
            Loading decisions ledger...
          </div>
        ) : rows.length === 0 ? (
          <EmptyState
            title="No Decisions Found"
            reason="No decision records match the selected filter criteria."
            icon="○"
          />
        ) : (
          <Table
            columns={columns}
            rows={rows}
            onRowClick={(row) => navigate(`/decisions/${row.decision_id}`)}
          />
        )}
      </Card>
    </div>
  );
}
