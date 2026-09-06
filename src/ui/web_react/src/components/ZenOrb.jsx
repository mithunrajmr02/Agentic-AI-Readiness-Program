import React from 'react';
import { ShieldCheck, AlertTriangle } from 'lucide-react';

/**
 * ZenOrb Primitive (ZEN FOCUS)
 * Ambient, distraction-free system health and decision-centric indicator.
 */
export default function ZenOrb({
  status = 'healthy', // 'healthy' | 'attention' | 'critical'
  title = 'All systems operational',
  subtitle = 'Steward autonomous agents are continuously monitoring inventory telemetry.',
  attentionCount = 0,
  onAction,
  actionLabel = 'Review Attention Items →',
  className = '',
}) {
  const isHealthy = status === 'healthy' && attentionCount === 0;

  return (
    <div className={`zen-focus-container ${className}`}>
      {/* Ambient Orb */}
      <div className="zen-orb-wrapper">
        <div className="zen-ripple" />
        <div
          className={`zen-orb ${
            isHealthy
              ? 'zen-orb-healthy'
              : status === 'critical'
              ? 'zen-orb-attention'
              : 'zen-orb-attention'
          }`}
        />
      </div>

      {/* System State Title & Subtitle */}
      <h2
        className="t-display"
        style={{
          margin: '0 0 0.5rem 0',
          fontWeight: 700,
          color: 'var(--ink-1)',
        }}
      >
        {isHealthy ? 'All Systems Operational' : `${attentionCount} Items Require Your Attention`}
      </h2>
      <p
        className="t-body"
        style={{
          maxWidth: '520px',
          margin: '0 auto 1.25rem auto',
          color: 'var(--ink-2)',
        }}
      >
        {subtitle}
      </p>

      {/* Action Trigger */}
      {attentionCount > 0 && onAction && (
        <button
          type="button"
          className="btn btn-primary"
          onClick={onAction}
          style={{ padding: '0.65rem 1.5rem', fontWeight: 700 }}
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}
