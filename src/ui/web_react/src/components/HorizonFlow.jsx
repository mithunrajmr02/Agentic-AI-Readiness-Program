import React from 'react';
import { useNavigate } from 'react-router-dom';

/**
 * HorizonFlow Primitive (HORIZON VIEW)
 * Expresses system state and event lineage through flowing temporal and contextual wave bands.
 */
export default function HorizonFlow({
  events = [],
  activeTime = '08:00',
  height = 140,
  className = '',
}) {
  const navigate = useNavigate();

  const defaultEvents = [
    { id: 'SIG-000045', time: '08:00', x: 33, type: 'signal', label: 'SIG-000045', sub: 'Projected Breach', severity: 'good', path: '/signals/SIG-000045' },
    { id: 'APR-000012', time: '09:45', x: 45, type: 'approval', label: 'APR-000012', sub: '₹68,400 Review', severity: 'critical', path: '/approvals/APR-000012' },
    { id: 'SIG-000047', time: '11:20', x: 55, type: 'signal', label: 'SIG-000047', sub: 'Config Drift', severity: 'warn', path: '/signals/SIG-000047' },
    { id: 'DEC-000123', time: '13:10', x: 68, type: 'decision', label: 'DEC-000123', sub: 'Executed PO', severity: 'good', path: '/decisions/DEC-000123' },
  ];

  const items = events.length > 0 ? events : defaultEvents;

  return (
    <div className={`horizon-container ${className}`}>
      <div className="horizon-ambient-glow" />

      {/* Header bar of Horizon */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem', position: 'relative', zIndex: 5 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <span style={{ fontSize: 'var(--t-meta-size)', fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--ink-2)' }}>
            TEMPORAL CONTEXT & EVENT FLOW
          </span>
          <span className="badge badge-accent">24h Horizon</span>
        </div>
        <div style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-3)' }}>
          Current simulation tick: <strong style={{ color: 'var(--accent)' }}>{activeTime}</strong>
        </div>
      </div>

      {/* SVG Horizon Wave Curves */}
      <div style={{ position: 'relative', height: `${height}px`, width: '100%' }}>
        <svg
          viewBox="0 0 1000 140"
          preserveAspectRatio="none"
          style={{ width: '100%', height: '100%', overflow: 'visible' }}
        >
          <defs>
            <linearGradient id="horizonGrad1" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#3B82F6" stopOpacity="0.12" />
              <stop offset="50%" stopColor="#8B5CF6" stopOpacity="0.18" />
              <stop offset="100%" stopColor="#10B981" stopOpacity="0.10" />
            </linearGradient>
            <linearGradient id="horizonGrad2" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#60A5FA" stopOpacity="0.25" />
              <stop offset="50%" stopColor="#A78BFA" stopOpacity="0.30" />
              <stop offset="100%" stopColor="#34D399" stopOpacity="0.20" />
            </linearGradient>
          </defs>

          {/* Background Ambient Topographic Waves */}
          <path
            d="M 0,90 Q 250,40 500,85 T 1000,60 L 1000,140 L 0,140 Z"
            fill="url(#horizonGrad1)"
          />
          <path
            d="M 0,110 C 200,60 400,130 650,80 C 800,50 900,100 1000,90 L 1000,140 L 0,140 Z"
            fill="url(#horizonGrad2)"
          />
          <path
            d="M 0,90 Q 250,40 500,85 T 1000,60"
            fill="none"
            stroke="#93C5FD"
            strokeWidth="1.5"
            strokeDasharray="4 4"
            opacity="0.7"
          />

          {/* Time Marker Baseline */}
          <line x1="0" y1="135" x2="1000" y2="135" stroke="var(--border)" strokeWidth="1" />
        </svg>

        {/* Interactive Event Pins on Horizon */}
        {items.map((item) => {
          const badgeColor =
            item.severity === 'critical' ? 'var(--critical)' :
            item.severity === 'warn' ? 'var(--warn)' : 'var(--good)';

          return (
            <div
              key={item.id}
              onClick={() => item.path && navigate(item.path)}
              style={{
                position: 'absolute',
                left: `${item.x}%`,
                top: item.y || '30px',
                transform: 'translateX(-50%)',
                zIndex: 10,
                cursor: 'pointer',
                transition: 'transform 0.15s ease',
              }}
              title={`Click to view ${item.label}`}
              className="horizon-pin"
            >
              <div
                style={{
                  background: 'var(--surface-0)',
                  border: `1.5px solid ${badgeColor}`,
                  borderRadius: 'var(--radius-sm)',
                  padding: '0.35rem 0.65rem',
                  boxShadow: 'var(--shadow-card)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.1rem',
                  whiteSpace: 'nowrap',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                  <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: badgeColor }} />
                  <span className="t-mono" style={{ fontSize: '11px', fontWeight: 700, color: 'var(--ink-1)' }}>
                    {item.label}
                  </span>
                  <span style={{ fontSize: '10px', color: 'var(--ink-3)' }}>{item.time}</span>
                </div>
                <div style={{ fontSize: '11px', color: 'var(--ink-2)' }}>{item.sub}</div>
              </div>
              <div
                style={{
                  width: '1px',
                  height: '40px',
                  background: badgeColor,
                  margin: '0 auto',
                  opacity: 0.5,
                }}
              />
            </div>
          );
        })}
      </div>

      {/* Time Axis Legend */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          marginTop: '0.35rem',
          fontSize: '11px',
          color: 'var(--ink-3)',
          fontFamily: 'var(--font-mono)',
        }}
      >
        <span>00:00</span>
        <span>04:00</span>
        <span>08:00 (Tick)</span>
        <span>12:00</span>
        <span>16:00</span>
        <span>20:00</span>
        <span>24:00</span>
      </div>
    </div>
  );
}
