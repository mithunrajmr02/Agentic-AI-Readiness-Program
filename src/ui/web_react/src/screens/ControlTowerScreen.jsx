import React from 'react';
import { Link } from 'react-router-dom';
import { Card, SeverityDot, ProvenanceMark, MetricTile } from '../components';

/**
 * 07-UX-ARCHITECTURE.md §5.1 Control Tower Screen (/tower)
 * WS-11 Skeleton / Landing experience
 */
export default function ControlTowerScreen() {
  return (
    <div className="control-tower-screen">
      {/* Page Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h1 className="t-display" style={{ margin: 0 }}>Control Tower</h1>
          <p className="t-meta" style={{ marginTop: '0.25rem' }}>
            Autonomous replenishment status and active governance exceptions.
          </p>
        </div>
      </div>

      {/* ZONE 1: NEEDS YOU */}
      <div style={{ marginBottom: '2rem' }}>
        <div style={{
          fontSize: 'var(--t-meta-size)',
          fontWeight: 700,
          color: 'var(--ink-2)',
          letterSpacing: '0.05em',
          textTransform: 'uppercase',
          marginBottom: '0.75rem',
        }}>
          NEEDS YOU
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {/* Approval Item */}
          <div style={{
            background: 'var(--surface-0)',
            border: '1px solid var(--border)',
            borderLeft: '4px solid var(--critical)',
            borderRadius: 'var(--radius-md)',
            padding: '1rem 1.25rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.35rem' }}>
                <SeverityDot severity="critical" label="Approval Required" />
                <span className="t-mono" style={{ fontWeight: 700 }}>APR-000012</span>
                <span style={{ color: 'var(--ink-2)' }}>PO-2026-0051 · ₹68,400 · Bluetooth Speaker</span>
              </div>
              <div style={{ fontSize: 'var(--t-body-size)', color: 'var(--ink-2)' }}>
                Above ₹50,000 — §10 requires Store Manager approval before submission
              </div>
              <div style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-3)', marginTop: '0.25rem' }}>
                waiting 2h 14m of 24h SLA
              </div>
            </div>
            <Link to="/approvals/APR-000012" className="btn btn-primary" style={{ padding: '0.45rem 1rem' }}>
              Review →
            </Link>
          </div>

          {/* Overdue PO Item */}
          <div style={{
            background: 'var(--surface-0)',
            border: '1px solid var(--border)',
            borderLeft: '4px solid var(--warn)',
            borderRadius: 'var(--radius-md)',
            padding: '1rem 1.25rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.35rem' }}>
                <SeverityDot severity="warn" label="PO Overdue" />
                <span className="t-mono" style={{ fontWeight: 700 }}>SIG-000046</span>
                <span style={{ color: 'var(--ink-2)' }}>po_overdue · Sharma Electronics</span>
              </div>
              <div style={{ fontSize: 'var(--t-body-size)', color: 'var(--ink-2)' }}>
                PO-2026-0038 expected 23 Aug; 2 days overdue
              </div>
            </div>
            <Link to="/signals/SIG-000046" className="btn btn-outline" style={{ padding: '0.45rem 1rem' }}>
              Review →
            </Link>
          </div>

          {/* Config Drift Item */}
          <div style={{
            background: 'var(--surface-0)',
            border: '1px solid var(--border)',
            borderLeft: '4px solid var(--warn)',
            borderRadius: 'var(--radius-md)',
            padding: '1rem 1.25rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.35rem' }}>
                <SeverityDot severity="high" label="Config Drift" />
                <span className="t-mono" style={{ fontWeight: 700 }}>SIG-000047</span>
                <span style={{ color: 'var(--ink-2)' }}>config_drift · USB-C Cable</span>
              </div>
              <div style={{ fontSize: 'var(--t-body-size)', color: 'var(--ink-2)' }}>
                Stored reorder point 20; measured velocity implies 47 (threshold_breach and config_drift)
              </div>
              <div style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-3)', marginTop: '0.25rem' }}>
                detected at 08:00 tick
              </div>
            </div>
            <Link to="/signals/SIG-000047" className="btn btn-outline" style={{ padding: '0.45rem 1rem' }}>
              Review →
            </Link>
          </div>

          {/* Empty State message when nothing needs attention */}
          {false && <div>Nothing Needs You. 4 decisions handled autonomously since 08:00.</div>}
        </div>
      </div>

      {/* ZONE 2: HANDLED WHILE YOU WERE AWAY */}
      <div style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
          <div style={{
            fontSize: 'var(--t-meta-size)',
            fontWeight: 700,
            color: 'var(--ink-2)',
            letterSpacing: '0.05em',
            textTransform: 'uppercase',
          }}>
            HANDLED WHILE YOU WERE AWAY
          </div>
          <span className="t-meta">last 24 hours</span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {/* Autonomous Order */}
          <div style={{
            background: 'var(--surface-0)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-md)',
            padding: '1rem 1.25rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.25rem' }}>
                <SeverityDot severity="good" label="Executed" />
                <span className="t-meta">08:00</span>
                <span className="t-mono" style={{ fontWeight: 600 }}>DEC-000123</span>
                <span style={{ color: 'var(--ink-1)', fontWeight: 500 }}>
                  Ordered 120 × Wireless Mouse from Kumar Trading (₹14,400)
                </span>
                <ProvenanceMark kind="computed" />
              </div>
              <div style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-3)' }}>
                projected_breach — 8 days cover, 11-day lead time · within agent authority (≤ ₹50,000)
              </div>
            </div>
            <Link to="/decisions/DEC-000123" className="btn btn-outline" style={{ padding: '0.35rem 0.75rem', fontSize: 'var(--t-meta-size)' }}>
              Details ↗
            </Link>
          </div>

          {/* Refusal / Declined */}
          <div style={{
            background: 'var(--surface-0)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-md)',
            padding: '1rem 1.25rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.25rem' }}>
                <SeverityDot severity="warn" label="Declined" />
                <span className="t-meta">08:00</span>
                <span className="t-mono" style={{ fontWeight: 600 }}>DEC-000124</span>
                <span style={{ color: 'var(--ink-1)', fontWeight: 500 }}>
                  Declined to order Laptop Stand — Insufficient History
                </span>
                <ProvenanceMark kind="computed" citation="Inventory Manual §3" />
              </div>
              <div style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-3)' }}>
                Refusal: 2 sale events in 90 days is below the 14-event sufficiency threshold
              </div>
            </div>
            <Link to="/decisions/DEC-000124" className="btn btn-outline" style={{ padding: '0.35rem 0.75rem', fontSize: 'var(--t-meta-size)' }}>
              Details ↗
            </Link>
          </div>
        </div>
      </div>

      {/* ZONE 3: POSITION */}
      <div style={{ marginBottom: '2rem' }}>
        <div style={{
          fontSize: 'var(--t-meta-size)',
          fontWeight: 700,
          color: 'var(--ink-2)',
          letterSpacing: '0.05em',
          textTransform: 'uppercase',
          marginBottom: '0.75rem',
        }}>
          POSITION SUMMARY
        </div>

        <div className="stats-grid">
          <MetricTile
            label="Open Signals"
            value={3}
            tier="T1"
            disclosure="real"
            detail="1 critical, 1 warning, 1 info"
          />
          <MetricTile
            label="Pending Approvals"
            value={1}
            tier="T1"
            disclosure="real"
            detail="Store Manager queue"
          />
          <MetricTile
            label="POs in Transit"
            value={4}
            tier="T1"
            disclosure="real"
            detail="1 overdue by 2 days"
          />
          <MetricTile
            label="Total Inventory Value"
            value={203700}
            prefix="₹"
            tier="T1"
            disclosure="real"
            detail="Cost price valuation"
          />
        </div>
      </div>

      {/* Synthetic Data Caveat per 07-UX §5.1 */}
      <div style={{
        background: 'var(--surface-0)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-sm)',
        padding: '0.75rem 1rem',
        fontSize: 'var(--t-meta-size)',
        color: 'var(--ink-3)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '0.5rem',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span>ⓘ</span>
          <span>Demonstration Data Disclosure — 90-day history is simulated. Deterministic arithmetic and governance mechanism are real.</span>
        </div>
        <button className="btn btn-outline" style={{ padding: '0.35rem 0.75rem', fontSize: 'var(--t-meta-size)' }}>
          Scan Telemetry Now
        </button>
      </div>
    </div>
  );
}
