import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, SeverityDot } from '../components';
import { PlayCircle, CheckCircle2, ArrowRight, ShieldCheck, Cpu } from 'lucide-react';

/**
 * STEWARD Operational Simulation & Scenarios Screen (/settings/scenarios)
 * Interactive environment to test autonomous replenishment agents under controlled edge cases.
 */
export default function ScenariosSettingsScreen() {
  const navigate = useNavigate();
  const [activeScenario, setActiveScenario] = useState(null);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);

  const scenarios = [
    {
      id: 'sc-1',
      number: '01',
      title: 'Deterministic Stockout Detection & Autonomous Order',
      tag: 'Autonomous Replenishment',
      severity: 'good',
      description: 'Simulates physical inventory depletion below reorder point for Wireless Mouse (SKU-1001). Agent computes formula and issues PO-2026-0052 under ₹50k cap.',
      targetRoute: '/decisions/DEC-000123',
      targetLabel: 'View Executed Decision DEC-000123 →',
    },
    {
      id: 'sc-2',
      number: '02',
      title: 'Supplier Delay & Dock Exception Signal',
      tag: 'Supplier Exception',
      severity: 'warn',
      description: 'Simulates Sharma Electronics delivery overdue by 2 days on PO-2026-0038. Detector fires SIG-000046 and updates measured supplier lead time.',
      targetRoute: '/signals/SIG-000046',
      targetLabel: 'Inspect Signal SIG-000046 →',
    },
    {
      id: 'sc-3',
      number: '03',
      title: 'High-Value Escalation & Store Manager Approval',
      tag: 'Human Governance',
      severity: 'critical',
      description: 'Calculates Bluetooth Speaker replenishment order total of ₹68,400. Exceeds ₹50k autonomy ceiling; halts auto-dispatch and creates approval APR-000012.',
      targetRoute: '/approvals/APR-000012',
      targetLabel: 'Open Approval APR-000012 →',
    },
    {
      id: 'sc-4',
      number: '04',
      title: 'Sales Velocity Step-Change & ROP Drift',
      tag: 'Config Drift',
      severity: 'warn',
      description: 'Customer demand surge jumps USB-C Cable sales to 4.2 units/day. Detector identifies +27 unit divergence between stored ROP (20) and implied ROP (47).',
      targetRoute: '/signals/SIG-000047',
      targetLabel: 'Inspect Drift Signal SIG-000047 →',
    },
    {
      id: 'sc-5',
      number: '05',
      title: 'Data Sufficiency Floor Policy Refusal',
      tag: 'Refusal Honesty',
      severity: 'good',
      description: 'Evaluates new product with only 2 sales events in 90 days. Replenishment agent refuses automated derivation per Manual §3 and logs audit refusal.',
      targetRoute: '/decisions/DEC-000124',
      targetLabel: 'View Policy Refusal DEC-000124 →',
    },
    {
      id: 'sc-6',
      number: '06',
      title: 'Multi-Item Simultaneous Stockout Burst',
      tag: 'Concurrent Telemetry',
      severity: 'warn',
      description: 'Triggers simultaneous inventory drops across 4 product categories to verify multi-agent concurrency, isolation, and SLA queue handling.',
      targetRoute: '/tower',
      targetLabel: 'Observe Control Tower Telemetry →',
    },
  ];

  const handleRunScenario = (sc) => {
    setActiveScenario(sc.id);
    setRunning(true);
    setResult(null);

    setTimeout(() => {
      setRunning(false);
      setResult({
        scenario: sc,
        message: `Simulation '${sc.title}' executed successfully. Telemetry event lineage generated.`,
      });
    }, 600);
  };

  return (
    <div className="scenarios-settings-screen" style={{ maxWidth: '1000px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
      {/* Header */}
      <div>
        <h1 className="t-hero" style={{ margin: 0 }}>Operational Simulation & Scenarios</h1>
        <p className="t-body" style={{ color: 'var(--ink-3)', margin: '0.25rem 0 0 0' }}>
          Execute and inspect deterministic autonomous agent behavior across realistic edge conditions.
        </p>
      </div>

      {result && (
        <div
          style={{
            padding: '1.25rem 1.5rem',
            background: 'var(--good-light)',
            color: 'var(--good)',
            border: '1px solid var(--good-border)',
            borderRadius: 'var(--radius-md)',
            boxShadow: 'var(--shadow-card)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: '1rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <CheckCircle2 size={20} color="var(--good)" />
            <div>
              <div style={{ fontWeight: 700, fontSize: '13px' }}>{result.message}</div>
              <div style={{ fontSize: '12px', color: 'var(--ink-2)', marginTop: '0.15rem' }}>
                All downstream data models and audit trails populated.
              </div>
            </div>
          </div>

          <button
            type="button"
            className="btn btn-primary btn-sm"
            onClick={() => navigate(result.scenario.targetRoute)}
          >
            {result.scenario.targetLabel}
          </button>
        </div>
      )}

      {/* Scenarios Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.25rem' }}>
        {scenarios.map((sc) => (
          <div
            key={sc.id}
            className="card"
            style={{
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              borderLeft: `4px solid ${
                sc.severity === 'critical'
                  ? 'var(--critical)'
                  : sc.severity === 'warn'
                  ? 'var(--warn)'
                  : 'var(--good)'
              }`,
            }}
          >
            <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="t-mono" style={{ fontSize: '11px', fontWeight: 800, color: 'var(--ink-3)' }}>
                  SCENARIO {sc.number}
                </span>
                <span className="badge badge-neutral" style={{ fontSize: '10px' }}>{sc.tag}</span>
              </div>

              <div style={{ fontWeight: 700, fontSize: '14px', color: 'var(--ink-1)', lineHeight: 1.4 }}>
                {sc.title}
              </div>

              <p style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-2)', lineHeight: 1.5, margin: 0 }}>
                {sc.description}
              </p>
            </div>

            <div
              style={{
                padding: '0.85rem 1.25rem',
                borderTop: '1px solid var(--border)',
                background: 'var(--surface-1)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <button
                type="button"
                className="btn btn-outline btn-sm"
                onClick={() => handleRunScenario(sc)}
                disabled={running && activeScenario === sc.id}
              >
                <PlayCircle size={14} />
                {running && activeScenario === sc.id ? 'Simulating…' : 'Trigger Scenario'}
              </button>

              <button
                type="button"
                className="btn btn-outline btn-sm"
                onClick={() => navigate(sc.targetRoute)}
                title="Direct link to surface"
              >
                Surface ↗
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
