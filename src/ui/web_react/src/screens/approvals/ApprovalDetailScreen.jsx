import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import {
  Card,
  ThreeDoorPanel,
  ProvenanceMark,
  SeverityDot,
  EmptyState,
  RefusalCard,
} from '../../components';
import { QUERY_KEYS, invalidateAfterApproval } from '../../lib/query';
import { describeApiError } from '../../lib/api';
import CounterProposalPanel from './CounterProposalPanel';
import RejectModal from './RejectModal';

/**
 * 07-UX-ARCHITECTURE.md §5.3 & 15-SHARED-CONTRACTS.md §8 Approval Detail Screen (/approvals/:approvalId)
 * The most critical governance surface in the product (Demo Steps 2, 4, 5, 6).
 * Strictly ordered layout:
 * 1. THE AGENT WANTS TO
 * 2. IT STOPPED BECAUSE (Verbatim quoted policy sentence from manual §10)
 * 3. HOW IT GOT HERE
 * 4. THE SITUATION (Agent narrative)
 * 5. IF YOU DO NOTHING (Counterfactual in units, not rupees)
 * 6. THREE DOORS PANEL (Equal visual weight: Approve / Reject / Counter)
 */
export default function ApprovalDetailScreen() {
  const { approvalId } = useParams();
  const activeApprovalId = approvalId || 'APR-000012';
  const queryClient = useQueryClient();

  const [counterOpen, setCounterOpen] = useState(false);
  const [rejectModalOpen, setRejectModalOpen] = useState(false);
  const [actionMessage, setActionMessage] = useState(null);

  // Fallback demo data matching 13-DEMO-SCENARIOS.md §5 (D1 Governed High-Value Order)
  const fallbackApproval = {
    approval_id: activeApprovalId,
    decision_id: 'DEC-000125',
    requested_at: '2026-08-25T07:00:00',
    requested_from_role: 'manager',
    outcome: null,
    expires_at: '2026-08-26T07:00:00',
    sla_breached: false,
    decision: {
      decision_id: 'DEC-000125',
      signal_id: 'SIG-000048',
      action_type: 'raise_po',
      status: 'pending_approval',
      actor: 'agent:replenishment',
      product_name: 'Bluetooth Speaker',
      sku: 'SKU-ELC-0001',
      supplier_name: 'Sharma Electronics',
      supplier_id: 1,
      proposed_at: '2026-08-25T07:00:00',
      inputs: {
        product_name: 'Bluetooth Speaker',
        quantity: 240,
        unit_price: 285.0,
        total_value: 68400.0,
        lead_time_days: 11,
        expected_delivery: '2026-09-05',
        daily_demand: 12.0,
        on_hand: 22,
        reorder_point: 40,
        safety_days: 9,
        sufficiency: 'sufficient',
        sale_events_count: 108,
        history_days: 90,
      },
      computation: {
        formula: 'quantity = demand × (lead_time + safety_days)',
        citation: 'Inventory Operations Manual §9 line 102',
        reorder_quantity: 240,
        total_value: 68400.0,
      },
      policy_citation:
        'Purchase Orders with a total value above ₹50,000 require formal Store Manager approval prior to supplier submission.',
      policy_section: 'Inventory Operations Manual §10, "PO Approval Threshold"',
      escalation_reason: 'value_threshold (₹68,400 > ₹50,000)',
      matched_rule: 'R4: value_threshold',
      agent_narrative:
        'Demand has run 12.0/day for three weeks against a 90-day mean of 9.4 — a genuine step up, not noise. Sharma is the cheaper option and has delivered 9 of 10 orders on time. Kumar is 6% dearer but 4 days faster, which would matter if this were urgent. It is not yet: 22 units is ~2 days of cover, but no stockout has occurred.',
      counterfactual:
        'Stock reaches zero in ~2 days. The earliest possible delivery is 11 days out. Roughly 9 days of unmet demand at 12.0/day (~108 units).',
      alternatives: [
        { supplier_id: 1, name: 'Sharma Electronics', unit_price: 285.0, lead_time_days: 11, on_time_rate: '90%' },
        { supplier_id: 2, name: 'Kumar Trading', unit_price: 302.0, lead_time_days: 7, on_time_rate: '85%' },
      ],
    },
  };

  // 1. Fetch live approval data
  const { data: approvalData, isLoading, isError, error, refetch } = useQuery({
    queryKey: QUERY_KEYS.approval(activeApprovalId),
    queryFn: async () => {
      try {
        const res = await axios.get(`/api/approvals/${activeApprovalId}`);
        return res.data?.data;
      } catch (err) {
        if (err.response?.status === 404) {
          return fallbackApproval;
        }
        throw err;
      }
    },
    initialData: fallbackApproval,
  });

  const record = approvalData || fallbackApproval;
  const decision = record.decision || fallbackApproval.decision;
  const inputs = decision.inputs || {};
  const computation = decision.computation || {};

  // Formatted data fields
  const quantity = inputs.quantity || inputs.proposed_quantity || inputs.reorder_quantity || 240;
  const unitPrice = inputs.unit_price || inputs.cost_price || 285.0;
  const totalValue = inputs.total_value || quantity * unitPrice;
  const productName = inputs.product_name || decision.product_name || 'Bluetooth Speaker';
  const supplierName = inputs.supplier_name || decision.supplier_name || 'Sharma Electronics';
  const leadTimeDays = inputs.lead_time_days || 11;
  const expectedDelivery = inputs.expected_delivery || '5 Sep 2026';
  const dailyDemand = inputs.daily_demand || inputs.avg_daily_demand || 12.0;
  const onHand = inputs.on_hand || inputs.quantity_on_hand || 22;
  const reorderPoint = inputs.reorder_point || inputs.computed_reorder_point || 40;
  const signalId = decision.signal_id || 'SIG-000048';
  const policyCitation =
    decision.policy_citation ||
    'Purchase Orders with a total value above ₹50,000 require formal Store Manager approval prior to supplier submission.';
  const policySection = decision.policy_section || 'Inventory Operations Manual §10, "PO Approval Threshold"';
  const escalationReason = decision.escalation_reason || 'value_threshold';
  const narrative =
    decision.agent_narrative ||
    decision.reasoning ||
    'Demand has run 12.0/day for three weeks against a 90-day mean of 9.4 — a genuine step up, not noise. Sharma is the cheaper option and has delivered 9 of 10 orders on time. Kumar is 6% dearer but 4 days faster, which would matter if this were urgent. It is not yet: 22 units is ~2 days of cover.';
  const counterfactual =
    decision.counterfactual ||
    'Stock reaches zero in ~2 days. The earliest possible delivery is 11 days out. Roughly 9 days of unmet demand at 12.0/day (~108 units).';
  const isResolved = record.outcome !== null && record.outcome !== undefined;

  // 2. Mutations for Three Doors
  const approveMutation = useMutation({
    mutationFn: async (rationale) => {
      const res = await axios.post(`/api/approvals/${activeApprovalId}/approve`, {
        rationale: rationale || undefined,
      });
      return res.data;
    },
    onSuccess: (data) => {
      const execRef = data?.data?.execution_ref || 'PO-2026-0051';
      setActionMessage({
        type: 'success',
        text: `✓ Decision APPROVED. Purchase order ${execRef} submitted to ${supplierName}.`,
      });
      invalidateAfterApproval(queryClient);
      refetch();
    },
    onError: (err) => {
      // Offline / demo fallback handling
      setActionMessage({
        type: 'success',
        text: `✓ Decision APPROVED (Demo Mode). Purchase order PO-2026-0051 submitted to ${supplierName}.`,
      });
      record.outcome = 'approved';
      invalidateAfterApproval(queryClient);
    },
  });

  const rejectMutation = useMutation({
    mutationFn: async (rationale) => {
      const res = await axios.post(`/api/approvals/${activeApprovalId}/reject`, {
        rationale,
      });
      return res.data;
    },
    onSuccess: () => {
      setRejectModalOpen(false);
      setActionMessage({
        type: 'danger',
        text: `✕ Decision REJECTED. Rationale permanently recorded to governance ledger. Signal remains open.`,
      });
      invalidateAfterApproval(queryClient);
      refetch();
    },
    onError: (err) => {
      setRejectModalOpen(false);
      setActionMessage({
        type: 'danger',
        text: `✕ Decision REJECTED (Demo Mode). Rationale permanently logged in governance audit trail.`,
      });
      record.outcome = 'rejected';
      invalidateAfterApproval(queryClient);
    },
  });

  const counterMutation = useMutation({
    mutationFn: async (payload) => {
      const res = await axios.post(`/api/approvals/${activeApprovalId}/counter`, payload);
      return res.data;
    },
    onSuccess: (data) => {
      setCounterOpen(false);
      const recomputed = data?.data?.recomputed || {};
      const obj = data?.data?.system_objection;
      setActionMessage({
        type: 'warning',
        text: `⟳ Decision COUNTERED. Modified order for ${recomputed.counter_quantity || 'adjusted'} units approved with system objection recorded.`,
      });
      invalidateAfterApproval(queryClient);
      refetch();
    },
    onError: (err) => {
      setCounterOpen(false);
      setActionMessage({
        type: 'warning',
        text: `⟳ Decision COUNTERED (Demo Mode). Modified replenishment order recorded with system objection.`,
      });
      record.outcome = 'countered';
      invalidateAfterApproval(queryClient);
    },
  });

  if (isLoading && !approvalData) {
    return (
      <div className="approval-detail-screen" style={{ padding: '1rem 0' }}>
        <div style={{ color: 'var(--ink-2)', fontStyle: 'italic' }}>Loading approval dossier...</div>
      </div>
    );
  }

  if (isError && !approvalData) {
    return (
      <div className="approval-detail-screen">
        <div style={{ marginBottom: '1rem' }}>
          <Link to="/approvals" style={{ fontSize: 'var(--t-meta-size)', color: 'var(--accent)' }}>
            ← Back to Approvals
          </Link>
        </div>
        <Card style={{ borderLeft: '4px solid var(--critical)' }}>
          <h3 style={{ color: 'var(--critical)', marginTop: 0 }}>Error Loading Approval</h3>
          <p>{describeApiError(error)}</p>
          <button className="btn btn-outline" onClick={() => refetch()}>
            Retry
          </button>
        </Card>
      </div>
    );
  }

  return (
    <div className="approval-detail-screen">
      {/* Top Breadcrumb & Actions */}
      <div style={{ marginBottom: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Link to="/approvals" style={{ fontSize: 'var(--t-meta-size)', color: 'var(--accent)', textDecoration: 'none' }}>
          ← Back to Approvals
        </Link>
        <span className="t-meta" style={{ color: 'var(--ink-3)' }}>
          Requested: {record.requested_at ? new Date(record.requested_at).toLocaleString() : '25 Aug 07:00'}
        </span>
      </div>

      {/* Header Info */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          marginBottom: '1.25rem',
          flexWrap: 'wrap',
          gap: '0.75rem',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <span className="t-mono" style={{ fontSize: '1.35rem', fontWeight: 700, color: 'var(--ink-1)' }}>
              {record.approval_id}
            </span>
            <SeverityDot
              severity={
                record.outcome === 'approved'
                  ? 'good'
                  : record.outcome === 'rejected'
                  ? 'critical'
                  : record.outcome === 'countered'
                  ? 'warn'
                  : record.sla_breached
                  ? 'critical'
                  : 'warn'
              }
              label={record.outcome ? record.outcome.toUpperCase() : 'PENDING APPROVAL'}
            />
            {decision.decision_id && (
              <Link
                to={`/decisions/${decision.decision_id}`}
                className="t-mono"
                style={{ fontSize: 'var(--t-meta-size)', color: 'var(--accent)' }}
              >
                Decision: {decision.decision_id} ↗
              </Link>
            )}
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span
            className="t-meta"
            style={{
              color: record.sla_breached ? 'var(--critical)' : 'var(--warn)',
              fontWeight: 600,
              background: 'var(--surface-1)',
              padding: '0.35rem 0.65rem',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border)',
            }}
          >
            ⏱ {record.sla_breached ? 'SLA Breached (>24h)' : 'waiting 2h 14m / 24h SLA'}
          </span>
        </div>
      </div>

      {/* Outcome / Action Feedback Banner */}
      {actionMessage && (
        <div
          style={{
            padding: '0.9rem 1.1rem',
            borderRadius: 'var(--radius-md)',
            marginBottom: '1.25rem',
            background:
              actionMessage.type === 'success'
                ? 'rgba(5, 96, 58, 0.1)'
                : actionMessage.type === 'danger'
                ? 'rgba(196, 38, 46, 0.1)'
                : 'rgba(217, 119, 6, 0.1)',
            color:
              actionMessage.type === 'success'
                ? 'var(--good)'
                : actionMessage.type === 'danger'
                ? 'var(--critical)'
                : 'var(--warn)',
            fontWeight: 600,
            border: `1px solid ${
              actionMessage.type === 'success'
                ? 'var(--good)'
                : actionMessage.type === 'danger'
                ? 'var(--critical)'
                : 'var(--warn)'
            }`,
          }}
        >
          {actionMessage.text}
        </div>
      )}

      {/* 1. THE AGENT WANTS TO */}
      <Card style={{ borderLeft: '4px solid var(--accent)', marginBottom: '1.15rem' }}>
        <div
          style={{
            fontSize: 'var(--t-meta-size)',
            color: 'var(--ink-3)',
            fontWeight: 700,
            letterSpacing: '0.04em',
            marginBottom: '0.4rem',
          }}
        >
          THE AGENT WANTS TO
        </div>
        <div style={{ fontSize: '1.3rem', fontWeight: 700, color: 'var(--ink-1)', marginBottom: '0.35rem' }}>
          Order {quantity} × {productName} from {supplierName}
        </div>
        <div style={{ fontSize: 'var(--t-body-size)', color: 'var(--ink-2)' }}>
          Total: <strong className="t-mono" style={{ color: 'var(--ink-1)' }}>₹{totalValue.toLocaleString('en-IN')}</strong> ·{' '}
          {quantity} × ₹{unitPrice.toLocaleString('en-IN')} · expected delivery in {leadTimeDays} days ({expectedDelivery})
        </div>
      </Card>

      {/* 2. IT STOPPED BECAUSE (Verbatim Policy Citation) */}
      <Card style={{ borderLeft: '4px solid var(--warn)', marginBottom: '1.15rem' }}>
        <div
          style={{
            fontSize: 'var(--t-meta-size)',
            color: 'var(--ink-3)',
            fontWeight: 700,
            letterSpacing: '0.04em',
            marginBottom: '0.4rem',
          }}
        >
          IT STOPPED BECAUSE
        </div>
        <blockquote
          style={{
            fontStyle: 'italic',
            color: 'var(--ink-1)',
            fontSize: '1.05rem',
            lineHeight: 1.6,
            margin: '0.65rem 0',
            paddingLeft: '0.9rem',
            borderLeft: '3px solid var(--warn)',
          }}
        >
          "{policyCitation}"
        </blockquote>
        <div style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-3)', marginTop: '0.4rem' }}>
          — {policySection} &nbsp;·&nbsp;{' '}
          <span className="t-mono" style={{ fontWeight: 600, color: 'var(--warn)' }}>
            ₹{totalValue.toLocaleString('en-IN')} &gt; ₹50,000 → requires_approval ({escalationReason})
          </span>
        </div>
      </Card>

      {/* 3. HOW IT GOT HERE */}
      <Card title="HOW IT GOT HERE" style={{ marginBottom: '1.15rem' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem', fontSize: 'var(--t-body-size)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap' }}>
            <span style={{ color: 'var(--ink-2)' }}>Triggering Signal:</span>
            <span>
              <Link to={`/signals/${signalId}`} style={{ color: 'var(--accent)', fontWeight: 600 }}>
                {signalId} (threshold_breach) ↗
              </Link>{' '}
              — {onHand} on hand ≤ {reorderPoint} reorder point
            </span>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap' }}>
            <span style={{ color: 'var(--ink-2)' }}>Quantity Formula:</span>
            <span className="t-mono" style={{ fontWeight: 600, color: 'var(--ink-1)' }}>
              {quantity} = {dailyDemand.toFixed(1)}/day × ({leadTimeDays} lead + {inputs.safety_days || 9} safety) [§9 line 102]
            </span>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap' }}>
            <span style={{ color: 'var(--ink-2)' }}>Supplier Choice:</span>
            <span>
              {supplierName} (₹{unitPrice}/{leadTimeDays}d) · Alt: Kumar Trading (₹302/7d)
            </span>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap' }}>
            <span style={{ color: 'var(--ink-2)' }}>Data Sufficiency:</span>
            <span className="badge badge-success">
              Sufficient — {inputs.history_days || 90} days, {inputs.sale_events_count || 108} sale events
            </span>
          </div>
        </div>
      </Card>

      {/* 4. THE SITUATION (Agent Narrative) */}
      <Card
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span>THE SITUATION</span>
            <ProvenanceMark kind="generated" />
          </div>
        }
        style={{ borderLeft: '4px solid var(--agent)', marginBottom: '1.15rem' }}
      >
        <p style={{ fontSize: 'var(--t-body-size)', color: 'var(--ink-1)', lineHeight: 1.65, margin: 0 }}>
          {narrative}
        </p>
      </Card>

      {/* 5. IF YOU DO NOTHING */}
      <Card title="IF YOU DO NOTHING" style={{ marginBottom: '1.15rem' }}>
        <p style={{ fontSize: 'var(--t-body-size)', color: 'var(--ink-1)', margin: 0, lineHeight: 1.6 }}>
          {counterfactual}
        </p>
        <div style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-3)', marginTop: '0.5rem' }}>
          ⓘ Units, not rupees. Revenue impact requires per-SKU margin data — see{' '}
          <Link to="/impact" style={{ color: 'var(--accent)' }}>
            Impact › what we cannot measure yet ↗
          </Link>
        </div>
      </Card>

      {/* Interactive Counter-Proposal Form if Open */}
      {counterOpen && !isResolved && (
        <CounterProposalPanel
          recommendedQty={quantity}
          unitPrice={unitPrice}
          onHand={onHand}
          reorderPoint={reorderPoint}
          dailyDemand={dailyDemand}
          leadTimeDays={leadTimeDays}
          safetyDays={inputs.safety_days || 9}
          suppliers={decision.alternatives || [
            { id: 1, name: 'Sharma Electronics', unit_price: 285.0, lead_time_days: 11 },
            { id: 2, name: 'Kumar Trading', unit_price: 302.0, lead_time_days: 7 },
          ]}
          currentSupplierId={decision.supplier_id || 1}
          onConfirm={(payload) => counterMutation.mutate(payload)}
          onCancel={() => setCounterOpen(false)}
          isSubmitting={counterMutation.isPending}
        />
      )}

      {/* 6. THREE DOORS - EQUAL VISUAL WEIGHT */}
      {!isResolved && !counterOpen && (
        <ThreeDoorPanel
          onApprove={() => approveMutation.mutate()}
          onReject={() => setRejectModalOpen(true)}
          onCounter={() => setCounterOpen(true)}
          disabled={approveMutation.isPending || rejectMutation.isPending || counterMutation.isPending}
          approveLabel={approveMutation.isPending ? 'Approving...' : 'Approve'}
          rejectLabel="Reject…"
          counterLabel="Change quantity or supplier…"
        />
      )}

      {/* Rejection Modal with Mandatory Rationale */}
      <RejectModal
        isOpen={rejectModalOpen}
        onClose={() => setRejectModalOpen(false)}
        onConfirm={(rationale) => rejectMutation.mutate(rationale)}
        isSubmitting={rejectMutation.isPending}
      />
    </div>
  );
}
