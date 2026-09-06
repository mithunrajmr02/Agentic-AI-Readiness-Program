import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, CheckCircle2, Circle, AlertCircle } from 'lucide-react';

/**
 * RailwayTrack Primitive (RAILWAY CONTROL)
 * Sequential operational timeline communicating:
 * "what happened -> what is happening -> what happens next"
 */
export default function RailwayTrack({
  steps = [
    { key: 'signals', label: 'Signals', count: 3, status: 'completed', path: '/signals' },
    { key: 'approvals', label: 'Approvals', count: 1, status: 'current', path: '/approvals' },
    { key: 'inprogress', label: 'In Progress', count: 0, status: 'upcoming', path: '/receiving' },
    { key: 'decisions', label: 'Decisions', count: 12, status: 'completed', path: '/decisions' },
    { key: 'impact', label: 'Impact Proof', count: null, status: 'upcoming', path: '/impact' },
  ],
  activeStepKey = 'approvals',
  nextStop = {
    id: 'APR-000012',
    label: 'High-Value Reorder Approval',
    detail: '₹68,400 · Bluetooth Speaker · Waiting Store Manager',
    path: '/approvals/APR-000012',
  },
  className = '',
}) {
  const navigate = useNavigate();

  return (
    <div
      className={`railway-container ${className}`}
      style={{
        background: 'var(--surface-0)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-lg)',
        padding: '1.25rem 1.5rem',
        boxShadow: 'var(--shadow-card)',
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '1rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <span
            style={{
              fontSize: 'var(--t-meta-size)',
              fontWeight: 700,
              letterSpacing: '0.06em',
              textTransform: 'uppercase',
              color: 'var(--ink-2)',
            }}
          >
            OPERATIONAL SEQUENCE & STAGES
          </span>
          <span className="badge badge-accent">Process Awareness</span>
        </div>
        <span className="t-meta">Autonomous Pipeline</span>
      </div>

      {/* Railway Track Flow */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: `repeat(${steps.length}, 1fr)`,
          position: 'relative',
          gap: '0.5rem',
          margin: '1.25rem 0',
        }}
      >
        {/* Track Line connecting nodes */}
        <div
          style={{
            position: 'absolute',
            top: '18px',
            left: '10%',
            right: '10%',
            height: '3px',
            background: 'var(--surface-3)',
            zIndex: 1,
          }}
        />

        {steps.map((step, idx) => {
          const isCurrent = step.key === activeStepKey;
          const isCompleted = step.status === 'completed';

          return (
            <div
              key={step.key}
              onClick={() => step.path && navigate(step.path)}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                textAlign: 'center',
                position: 'relative',
                zIndex: 2,
                cursor: 'pointer',
              }}
            >
              {/* Node Indicator */}
              <div
                style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '50%',
                  background: isCurrent
                    ? 'var(--accent)'
                    : isCompleted
                    ? 'var(--good)'
                    : 'var(--surface-0)',
                  border: isCurrent
                    ? '3px solid var(--accent-light)'
                    : isCompleted
                    ? '2px solid var(--good)'
                    : '2px solid var(--border)',
                  color: isCurrent || isCompleted ? '#ffffff' : 'var(--ink-3)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 700,
                  fontSize: '12px',
                  boxShadow: isCurrent ? '0 0 0 4px var(--accent-light)' : 'none',
                  transition: 'all 0.2s ease',
                  marginBottom: '0.5rem',
                }}
              >
                {isCompleted ? <CheckCircle2 size={18} /> : idx + 1}
              </div>

              {/* Node Label */}
              <div
                style={{
                  fontSize: 'var(--t-meta-size)',
                  fontWeight: isCurrent ? 700 : 600,
                  color: isCurrent ? 'var(--accent)' : 'var(--ink-1)',
                  marginBottom: '0.15rem',
                }}
              >
                {step.label}
              </div>

              {/* Node Count Badge */}
              {step.count !== null && (
                <span
                  className={`badge ${
                    isCurrent ? 'badge-warning' : isCompleted ? 'badge-success' : 'badge-neutral'
                  }`}
                  style={{ fontSize: '10px', padding: '0.1rem 0.4rem' }}
                >
                  {step.count} {isCurrent ? 'active' : ''}
                </span>
              )}
            </div>
          );
        })}
      </div>

      {/* Next Stop Highlight Bar */}
      {nextStop && (
        <div
          style={{
            background: 'var(--surface-1)',
            border: '1px solid var(--border)',
            borderLeft: '4px solid var(--accent)',
            borderRadius: 'var(--radius-sm)',
            padding: '0.75rem 1rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginTop: '1rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <span
              style={{
                fontSize: '11px',
                fontWeight: 700,
                color: 'var(--accent)',
                letterSpacing: '0.04em',
                textTransform: 'uppercase',
              }}
            >
              NEXT STOP
            </span>
            <span className="t-mono" style={{ fontWeight: 700, color: 'var(--ink-1)' }}>
              {nextStop.id}
            </span>
            <span style={{ fontSize: 'var(--t-body-size)', color: 'var(--ink-2)' }}>
              {nextStop.label} · {nextStop.detail}
            </span>
          </div>
          <button
            type="button"
            className="btn btn-primary btn-sm"
            onClick={() => navigate(nextStop.path)}
          >
            Intervene Now <ArrowRight size={14} />
          </button>
        </div>
      )}
    </div>
  );
}
