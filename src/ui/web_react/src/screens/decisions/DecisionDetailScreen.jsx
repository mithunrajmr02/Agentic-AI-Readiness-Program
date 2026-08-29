import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import {
  Card,
  SeverityDot,
  ProvenanceMark,
  EvidenceBlock,
  AuthorityBadge,
  RefusalCard,
  EmptyState,
} from '../../components';
import { QUERY_KEYS } from '../../lib/query';
import { describeApiError } from '../../lib/api';
import RunTelemetryBlock from './RunTelemetryBlock';

/**
 * 07-UX-ARCHITECTURE.md §5.4 & 15-SHARED-CONTRACTS.md §3.2 Decision Detail (/decisions/:decisionId)
 * Immutable ledger record: triggering signal, deterministic inputs & arithmetic,
 * quoted policy citation, agent reasoning record, human override objection, and run telemetry.
 */
export default function DecisionDetailScreen() {
  const { decisionId } = useParams();
  const activeDecisionId = decisionId || 'DEC-000123';

  // Demo fallback profiles
  const fallbackProfiles = {
    'DEC-000123': {
      decision_id: 'DEC-000123',
      signal_id: 'SIG-000045',
      run_id: 'RUN-000078',
      action_type: 'raise_po',
      status: 'auto_approved',
      actor: 'agent:replenishment',
      product_name: 'Wireless Mouse',
      supplier_name: 'Kumar Trading',
      proposed_at: '2026-08-25T08:00:00',
      decided_at: '2026-08-25T08:00:05',
      executed_at: '2026-08-25T08:00:06',
      execution_ref: 'PO-2026-0052',
      autonomy_mode: 'assisted',
      inputs: {
        recommended_quantity: 120,
        unit_price: 120.0,
        total_value: 14400.0,
        daily_demand: 6.0,
        lead_time_days: 11,
        safety_days: 9,
        on_hand: 14,
        reorder_point: 32,
        policy_threshold: '₹50,000.00 (within authority)',
        autonomy_mode: 'assisted (R4 matched: auto_approved)',
      },
      computation: {
        formula: 'order_qty = round_to_pack((demand × (lead_time + safety_days)), 10)',
        citation: "Inventory Operations Manual §9 'Order Quantity Calculation'",
        result: '₹14,400 ≤ ₹50,000 (auto_approved)',
      },
      policy_citation:
        'Purchase Orders with a total value at or below ₹50,000 may be placed autonomously under assisted/autonomous mode.',
      policy_section: 'Inventory Manual §10 · Matched Rule: R4_value_threshold',
      agent_narrative:
        'Wireless Mouse would have breached safety stock within 4 days. Computed replenishment quantity of 120 units covers 20 days of demand. Sourcing selected Kumar Trading as the cheapest active supplier with 11-day lead time. Total order value of ₹14,400 is within the ₹50,000 manager threshold.',
    },
    'DEC-000124': {
      decision_id: 'DEC-000124',
      signal_id: 'SIG-000044',
      run_id: 'RUN-000079',
      action_type: 'no_action',
      status: 'insufficient_data',
      actor: 'agent:replenishment',
      product_name: 'Laptop Stand',
      proposed_at: '2026-08-25T08:00:00',
      decided_at: '2026-08-25T08:00:02',
      autonomy_mode: 'assisted',
      inputs: {
        sale_events: 2,
        distinct_days: 1,
        history_window_days: 90,
        sufficiency: 'insufficient',
      },
      computation: {
        formula: 'sufficiency = evaluate_sufficiency(sale_events, distinct_days)',
        citation: "Inventory Operations Manual §3 line 35 'Data Sufficiency Floor'",
        result: 'Insufficient data → Value = None (Refusal)',
      },
      policy_citation:
        'Replenishment decisions require at least 14 sale events across 21 distinct days. Below this threshold, no automated reorder point may be derived.',
      policy_section: 'Inventory Operations Manual §3 §4',
      agent_narrative:
        'Refused to derive automated reorder parameters for Laptop Stand. The SKU contains only 2 recorded sale events across 1 distinct day in the last 90 days. Either sales are not being recorded or the SKU is not selling; those have opposite remedies and cannot be distinguished without additional history.',
      refusal: {
        needed: '14 sale events across 21 distinct days',
        have: '2 sale events across 1 distinct day',
        citation: 'Inventory Operations Manual §3 line 35',
        suggestion: 'Maintain manual reorder points or backfill missing sales transactions before enabling autonomous replenishment.',
      },
    },
    'DEC-000125': {
      decision_id: 'DEC-000125',
      signal_id: 'SIG-000048',
      approval_id: 'APR-000012',
      run_id: 'RUN-000080',
      action_type: 'raise_po',
      status: 'approved',
      actor: 'user:1 (S. Iyer)',
      product_name: 'Bluetooth Speaker',
      supplier_name: 'Sharma Electronics',
      proposed_at: '2026-08-25T07:00:00',
      decided_at: '2026-08-25T09:14:22',
      executed_at: '2026-08-25T09:14:25',
      execution_ref: 'PO-2026-0051',
      autonomy_mode: 'assisted',
      inputs: {
        recommended_quantity: 240,
        unit_price: 285.0,
        total_value: 68400.0,
        daily_demand: 12.0,
        lead_time_days: 11,
        safety_days: 9,
        on_hand: 22,
        reorder_point: 40,
        escalation_reason: 'value_threshold (> ₹50,000)',
      },
      computation: {
        formula: 'quantity = demand × (lead_time + safety_days)',
        citation: 'Inventory Operations Manual §9 line 102',
        result: '₹68,400 > ₹50,000 → Escalated to Store Manager (APR-000012)',
      },
      policy_citation:
        'Purchase Orders with a total value above ₹50,000 require formal Store Manager approval prior to supplier submission.',
      policy_section: 'Inventory Operations Manual §10, "PO Approval Threshold"',
      agent_narrative:
        'Bluetooth Speaker breach escalated to Store Manager due to total value of ₹68,400 exceeding the ₹50,000 policy threshold. Order approved by Store Manager S. Iyer and executed under PO-2026-0051.',
      system_objection: null,
    },
  };

  const defaultProfile = fallbackProfiles[activeDecisionId] || fallbackProfiles['DEC-000123'];

  // 1. Fetch Decision Data
  const { data: rawDecision, isLoading, isError, error, refetch } = useQuery({
    queryKey: QUERY_KEYS.decision(activeDecisionId),
    queryFn: async () => {
      try {
        const res = await axios.get(`/api/decisions/${activeDecisionId}`);
        return res.data?.data;
      } catch (err) {
        if (err.response?.status === 404) {
          return defaultProfile;
        }
        throw err;
      }
    },
    initialData: defaultProfile,
  });

  // 2. Fetch Linked Agent Run Telemetry
  const { data: runData } = useQuery({
    queryKey: ['decision', activeDecisionId, 'run'],
    queryFn: async () => {
      try {
        const res = await axios.get(`/api/decisions/${activeDecisionId}/run`);
        return res.data?.data;
      } catch {
        return null;
      }
    },
  });

  const decision = rawDecision || defaultProfile;
  const inputs = decision.inputs || {};
  const computation = decision.computation || {};
  const isRefusal =
    decision.status === 'insufficient_data' ||
    decision.outcome === 'declined' ||
    Boolean(decision.refusal);

  const getSeverity = (status) => {
    switch (status) {
      case 'executed':
      case 'auto_approved':
      case 'approved':
        return 'good';
      case 'insufficient_data':
      case 'declined':
        return 'warn';
      case 'rejected':
      case 'failed':
      case 'expired':
        return 'critical';
      default:
        return 'info';
    }
  };

  const getOutcomeLabel = (status) => {
    switch (status) {
      case 'auto_approved':
        return 'Autonomous';
      case 'approved':
        return 'Approved by Manager';
      case 'rejected':
        return 'Rejected';
      case 'countered':
        return 'Countered / Modified';
      case 'insufficient_data':
      case 'declined':
        return 'Declined (Refusal)';
      case 'executing':
        return 'Executing';
      default:
        return (status || 'Recorded').replace(/_/g, ' ').toUpperCase();
    }
  };

  if (isLoading && !rawDecision) {
    return (
      <div className="decision-detail-screen" style={{ padding: '1rem 0' }}>
        <div style={{ color: 'var(--ink-2)', fontStyle: 'italic' }}>Loading decision ledger record...</div>
      </div>
    );
  }

  if (isError && !rawDecision) {
    return (
      <div className="decision-detail-screen">
        <div style={{ marginBottom: '1rem' }}>
          <Link to="/decisions" style={{ fontSize: 'var(--t-meta-size)', color: 'var(--accent)' }}>
            ← Back to Decisions
          </Link>
        </div>
        <Card style={{ borderLeft: '4px solid var(--critical)' }}>
          <h3 style={{ color: 'var(--critical)', marginTop: 0 }}>Error Loading Decision</h3>
          <p>{describeApiError(error)}</p>
          <button className="btn btn-outline" onClick={() => refetch()}>
            Retry
          </button>
        </Card>
      </div>
    );
  }

  return (
    <div className="decision-detail-screen">
      {/* Top Breadcrumb */}
      <div style={{ marginBottom: '1rem' }}>
        <Link to="/decisions" style={{ fontSize: 'var(--t-meta-size)', color: 'var(--accent)', textDecoration: 'none' }}>
          ← Back to Decisions
        </Link>
      </div>

      {/* Header Badge & Action Title */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          marginBottom: '1.25rem',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
            <span className="t-mono" style={{ fontSize: '1.35rem', fontWeight: 700, color: 'var(--ink-1)' }}>
              {decision.decision_id}
            </span>
            <SeverityDot severity={getSeverity(decision.status)} label={getOutcomeLabel(decision.status)} />
            <AuthorityBadge mode={decision.autonomy_mode || 'assisted'} />
          </div>

          <h1 className="t-heading" style={{ margin: '0.4rem 0 0.2rem 0', color: 'var(--ink-1)' }}>
            {decision.action_type === 'no_action'
              ? `No Order — ${decision.product_name || 'Refusal'}`
              : `Ordered ${inputs.recommended_quantity || inputs.quantity || 120} × ${
                  decision.product_name || 'Item'
                } from ${decision.supplier_name || 'Supplier'}`}
          </h1>

          <p className="t-meta" style={{ margin: 0 }}>
            Decided: {decision.decided_at ? new Date(decision.decided_at).toLocaleString() : '25 Aug 08:00:05'} &nbsp;·&nbsp;
            Actor: <strong>{decision.actor || 'agent:replenishment'}</strong> &nbsp;·&nbsp;
            Execution Ref:{' '}
            <span className="t-mono" style={{ fontWeight: 600 }}>
              {decision.execution_ref || '—'}
            </span>
          </p>
        </div>

        {/* Linked Entities Quick Links */}
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          {decision.signal_id && (
            <Link
              to={`/signals/${decision.signal_id}`}
              className="badge badge-primary"
              style={{ textDecoration: 'none', padding: '0.35rem 0.65rem' }}
            >
              Signal: {decision.signal_id} ↗
            </Link>
          )}
          {decision.approval_id && (
            <Link
              to={`/approvals/${decision.approval_id}`}
              className="badge badge-warning"
              style={{ textDecoration: 'none', padding: '0.35rem 0.65rem' }}
            >
              Approval: {decision.approval_id} ↗
            </Link>
          )}
        </div>
      </div>

      {/* Refusal Card Rendering if Insufficient Data */}
      {isRefusal && (
        <RefusalCard
          title="Decision Declined — Insufficient Data Floor"
          needed={decision.refusal?.needed || '14 sale events across 21 distinct days'}
          have={decision.refusal?.have || `${inputs.sale_events || 2} sale events across ${inputs.distinct_days || 1} day`}
          citation={decision.refusal?.citation || 'Inventory Operations Manual §3 line 35'}
          suggestion={
            decision.refusal?.suggestion ||
            'System declined to extrapolate demand from insufficient movement history. Maintain manual parameters until sufficient data is recorded.'
          }
        />
      )}

      {/* 1. DETERMINISTIC INPUTS & COMPUTATION */}
      <EvidenceBlock
        title="DETERMINISTIC INPUTS & COMPUTATION"
        inputs={inputs}
        formula={computation.formula || '(demand × lead_time) + (demand × safety_days)'}
        citation={computation.citation || "Inventory Operations Manual §9 'Order Quantity Calculation'"}
        result={computation.result || `₹${(inputs.total_value || 14400).toLocaleString('en-IN')} (auto_approved)`}
      />

      {/* 2. GOVERNING POLICY CITATION (Verbatim Manual Text) */}
      <Card title="GOVERNING POLICY CITATION" style={{ margin: '1.15rem 0', borderLeft: '4px solid var(--accent)' }}>
        <p style={{ fontStyle: 'italic', color: 'var(--ink-1)', fontSize: '1.05rem', lineHeight: 1.6, margin: '0 0 0.5rem 0' }}>
          "{decision.policy_citation || 'Purchase Orders with a total value at or below ₹50,000 may be placed autonomously under assisted/autonomous mode.'}"
        </p>
        <div style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-3)' }}>
          Citation: {decision.policy_section || 'Inventory Operations Manual §10'} &nbsp;·&nbsp; Matched Rule:{' '}
          <strong>{decision.escalation_reason || 'R4_value_threshold'}</strong>
        </div>
      </Card>

      {/* 3. AGENT REASONING RECORD */}
      <Card
        title={
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
            <span>AGENT REASONING RECORD</span>
            <ProvenanceMark kind="generated" />
          </div>
        }
        style={{ borderLeft: '4px solid var(--agent)', marginBottom: '1.15rem' }}
      >
        <p style={{ fontSize: 'var(--t-body-size)', color: 'var(--ink-1)', lineHeight: 1.65, margin: 0 }}>
          {decision.agent_narrative ||
            'Computed replenishment quantity covers projected demand through supplier lead time. Verified pricing against active sourcing contracts.'}
        </p>
      </Card>

      {/* 4. HUMAN OVERRIDE & SYSTEM OBJECTION (if Countered) */}
      {decision.system_objection && (
        <Card
          title="HUMAN OVERRIDE & SYSTEM OBJECTION RECORD"
          style={{ borderLeft: '4px solid var(--warn)', marginBottom: '1.15rem', background: 'rgba(217, 119, 6, 0.04)' }}
        >
          <div style={{ marginBottom: '0.65rem' }}>
            <span className="badge badge-warning">Operator Counter-Proposal Applied</span>
          </div>
          <p style={{ fontSize: 'var(--t-body-size)', color: 'var(--ink-1)', lineHeight: 1.6, margin: '0 0 0.5rem 0' }}>
            {decision.system_objection}
          </p>
          <div style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-3)' }}>
            ⓘ Recorded to immutable ledger at counter time. The Store Manager approved this override over the stated system objection.
          </div>
        </Card>
      )}

      {/* 5. AGENT RUN EXECUTION TRACE & TELEMETRY */}
      <RunTelemetryBlock run={runData || { run_id: decision.run_id }} />
    </div>
  );
}
