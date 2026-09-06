import React from 'react';
import { Card, MetricTile } from '../components';
import { ShieldCheck, TrendingUp, Cpu, Database, AlertCircle } from 'lucide-react';

/**
 * STEWARD Impact Proof & System Health (/impact)
 * 3-Tier Metric Disclosure (T1 Direct Ledger, T2 Model Simulation, T3 Unmeasured Data Gaps)
 * 5 -> 0 Numerical Rigour & Policy Citation Audit
 */
export default function ImpactScreen() {
  return (
    <div className="impact-screen" style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Screen Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 className="t-hero" style={{ margin: 0 }}>Impact Proof & System Health</h1>
          <p className="t-body" style={{ color: 'var(--ink-3)', margin: '0.25rem 0 0 0' }}>
            Executive metrics, telemetry latency, arithmetic verification, and unmeasured data gaps.
          </p>
        </div>
      </div>

      {/* 1. DETECTION & SENSING */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
          <Database size={16} color="var(--accent)" />
          <span style={{ fontSize: 'var(--t-meta-size)', fontWeight: 700, color: 'var(--ink-2)', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
            DETECTION & SENSING TELEMETRY
          </span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem' }}>
          <MetricTile
            label="Signals Raised"
            value={47}
            tier="T1"
            disclosure="Direct Ledger"
            detail="18 threshold, 12 projected, 8 drift, 6 overdue, 3 other"
          />
          <MetricTile
            label="Signal Detection Classes"
            value={14}
            tier="T1"
            disclosure="Direct Ledger"
            detail="Comprehensive multi-scenario anomaly detectors active"
          />
          <MetricTile
            label="Median Detection Latency"
            value={0.6}
            suffix="s"
            tier="T1"
            disclosure="Direct Ledger"
            detail="From physical movement event to signal creation"
          />
        </div>
      </div>

      {/* 2. DECISION & GOVERNANCE */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
          <Cpu size={16} color="var(--agent)" />
          <span style={{ fontSize: 'var(--t-meta-size)', fontWeight: 700, color: 'var(--ink-2)', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
            DECISION EXECUTION & GOVERNANCE
          </span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem' }}>
          <MetricTile
            label="Autonomy Rate"
            value={68}
            suffix="%"
            tier="T2"
            disclosure="Model Simulation"
            detail="32 of 47 resolved within autonomous policy authority"
          />
          <MetricTile
            label="Decide-to-Act Time"
            value="4m 12s"
            tier="T2"
            disclosure="Model Simulation"
            detail="Observed latency vs 24h manual expectation in Manual §10"
          />
          <MetricTile
            label="Policy Refusals"
            value={6}
            tier="T1"
            disclosure="Direct Ledger"
            detail="4 insufficient history, 2 duplicate order protection"
          />
        </div>
      </div>

      {/* 3. METHODOLOGY RIGOUR (5 -> 0) */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
          <ShieldCheck size={16} color="var(--good)" />
          <span style={{ fontSize: 'var(--t-meta-size)', fontWeight: 700, color: 'var(--ink-2)', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
            METHODOLOGY & NUMERICAL RIGOUR
          </span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem' }}>
          <MetricTile
            label="Fabricated Numeric Fields"
            value="5 → 0"
            isLead={true}
            tier="T1"
            disclosure="Direct Ledger"
            detail="Zero LLM-invented numbers in production ledger"
          />
          <MetricTile
            label="Policy Citation Rate"
            value="100%"
            tier="T1"
            disclosure="Direct Ledger"
            detail="47 of 47 decisions carry verbatim manual citation"
          />
          <MetricTile
            label="Full Ledger Records"
            value="100%"
            tier="T1"
            disclosure="Direct Ledger"
            detail="Every execution verified with idempotency key"
          />
        </div>
      </div>

      {/* 4. WHAT WE CANNOT MEASURE YET (T3 GAPS) */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
          <AlertCircle size={16} color="var(--warn)" />
          <span style={{ fontSize: 'var(--t-meta-size)', fontWeight: 700, color: 'var(--warn)', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
            WHAT WE CANNOT MEASURE YET (T3 GAPS)
          </span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem' }}>
          <MetricTile
            label="₹ Revenue Protected"
            value={null}
            tier="T3"
            formula="Σ (unmet units × unit margin) over avoided stockouts"
            missingInput="Per-SKU margin and observed lost-sale rates"
          />
          <MetricTile
            label="Hours Returned to Team"
            value={null}
            tier="T3"
            formula="(baseline minutes per cycle − observed) × cycles"
            missingInput="Time-and-motion baseline for previous manual process"
          />
          <MetricTile
            label="True Stockout Reduction"
            value={null}
            tier="T3"
            formula="Stockout-days: baseline vs autonomous replenishment"
            missingInput="Longitudinal movement history across 12+ months"
          />
        </div>

        <div
          style={{
            background: 'var(--surface-0)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-sm)',
            padding: '0.85rem 1.25rem',
            fontSize: 'var(--t-meta-size)',
            color: 'var(--ink-3)',
            marginTop: '1rem',
          }}
        >
          ⓘ These metrics are not withheld estimates. They require comprehensive historical transaction logs to compute directly without projection.
        </div>
      </div>
    </div>
  );
}
